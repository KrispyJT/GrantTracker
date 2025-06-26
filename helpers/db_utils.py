# --- db_utils.py (Supabase version)
from sqlalchemy import create_engine, text
import pandas as pd
import streamlit as st
from datetime import date
from helpers.date_helpers import generate_month_range, distribute_amount_evenly

# Connect using secrets
engine = create_engine(st.secrets["database"]["url"])


# -------------------------
# 🔍 Read Functions
# -------------------------
# 1
def fetch_all(query, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row._mapping) for row in result]

# 2
def fetch_one(query, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        row = result.fetchone()
        return dict(row._mapping) if row else None

# -------------------------
# 💾 Write Functions
# -------------------------
# 3
def execute_query(query, params=None):
    with engine.begin() as conn:
        conn.execute(text(query), params or {})
# 4
def insert_and_return_id(query, params=None):
    with engine.begin() as conn:
        result = conn.execute(text(query + " RETURNING id"), params or {})
        return result.scalar_one()

# -------------------------
# Grant Logic
# -------------------------
# 5
def get_all_grants():
    query = """
        SELECT g.id, g.name, f.name AS funder, g.start_date, g.end_date,
               g.status, g.total_award, g.notes
        FROM grants g
        JOIN funders f ON g.funder_id = f.id
        ORDER BY g.start_date DESC
    """
    return fetch_all(query)

# 6
def grant_exists(grant_name):
    query = "SELECT 1 FROM grants WHERE LOWER(name) = LOWER(:name) LIMIT 1"
    return fetch_one(query, {"name": grant_name.strip()})



# 9 
def add_grant(grant_name, funder_id, start_date, end_date, total_award, status, notes):
    query = """
        INSERT INTO grants (name, funder_id, start_date, end_date, total_award, status, notes)
        VALUES (:name, :funder_id, :start_date, :end_date, :total_award, :status, :notes)
    """
    params = {
        "name": grant_name.strip(),
        "funder_id": funder_id,
        "start_date": start_date.isoformat() if isinstance(start_date, date) else start_date,
        "end_date": end_date.isoformat() if isinstance(end_date, date) else end_date,
        "total_award": total_award,
        "status": status.strip(),
        "notes": notes.strip() if notes else None
    }
    execute_query(query, params)


# 10
def update_grant(grant_id, grant_name, funder_id, start_date, end_date, total_award, status, notes):
    query = """
        UPDATE grants
        SET name = :name,
            funder_id = :funder_id,
            start_date = :start_date,
            end_date = :end_date,
            total_award = :total_award,
            status = :status,
            notes = :notes
        WHERE id = :grant_id
    """
    params = {
        "name": grant_name.strip(),
        "funder_id": funder_id,
        "start_date": start_date.isoformat() if isinstance(start_date, date) else start_date,
        "end_date": end_date.isoformat() if isinstance(end_date, date) else end_date,
        "total_award": total_award,
        "status": status.strip(),
        "notes": notes.strip() if notes else None,
        "grant_id": grant_id
    }
    execute_query(query, params)


# 11
def delete_grant(grant_id):
    query = "DELETE FROM grants WHERE id = :grant_id"
    execute_query(query, {"grant_id": grant_id})


# 13
def get_grant_by_id(grant_id):
    query = """
        SELECT g.id, g.name, f.name AS funder_name, f.type AS funder_type,
               g.start_date, g.end_date, g.total_award, g.status, g.notes
        FROM grants g
        LEFT JOIN funders f ON g.funder_id = f.id
        WHERE g.id = :grant_id
    """
    return fetch_one(query, {"grant_id": grant_id})




# -------------------------
# Funder Logic
# -------------------------
# 7
def get_funder_id(funder_name):
    query = "SELECT id FROM funders WHERE LOWER(name) = LOWER(:name)"
    result = fetch_one(query, {"name": funder_name.strip()})
    return result["id"] if result else None


# 8
def add_funder_if_missing(funder_name, funder_type):
    existing = fetch_one("SELECT id FROM funders WHERE LOWER(name) = LOWER(:name)", {"name": funder_name.strip()})
    if not existing:
        query = "INSERT INTO funders (name, type) VALUES (:name, :type)"
        execute_query(query, {
            "name": funder_name.strip(),
            "type": funder_type.strip()
        })


# 12
def get_all_funders():
    query = "SELECT id, name, type FROM funders ORDER BY name"
    return fetch_all(query)


# -------------------------
# Grant Line Item Logic
# -------------------------
# 14
def get_line_items_by_grant(grant_id):
    query = """
        SELECT id, name, description, allocated_amount
        FROM grant_line_items
        WHERE grant_id = :grant_id
        ORDER BY name
    """
    return fetch_all(query, {"grant_id": grant_id})

# 15
def add_line_item(grant_id, name, description, allocated_amount=0.0):
    query = """
        INSERT INTO grant_line_items (grant_id, name, description, allocated_amount)
        VALUES (:grant_id, :name, :description, :allocated_amount)
    """
    params = {
        "grant_id": grant_id,
        "name": name.strip(),
        "description": description.strip(),
        "allocated_amount": allocated_amount
    }
    execute_query(query, params)

# 16
def update_line_item(line_item_id, name, description, allocated_amount):
    query = """
        UPDATE grant_line_items
        SET name = :name, description = :description, allocated_amount = :allocated_amount
        WHERE id = :id
    """
    params = {
        "name": name.strip(),
        "description": description.strip() if description else None,
        "allocated_amount": allocated_amount,
        "id": line_item_id
    }
    execute_query(query, params)


# 17
def update_line_item_allocated(item_id, new_allocated_amount):
    query = """
        UPDATE grant_line_items
        SET allocated_amount = :allocated_amount
        WHERE id = :id
    """
    params = {
        "allocated_amount": new_allocated_amount,
        "id": item_id
    }
    execute_query(query, params)

# 18
def delete_line_item(item_id):
    query = "DELETE FROM grant_line_items WHERE id = :id"
    execute_query(query, {"id": item_id})



# -------------------------
# QuickBooks Logic
# -------------------------
# 19
def get_parent_categories():
    query = "SELECT id, name FROM qb_parent_categories ORDER BY name"
    return fetch_all(query)

# 20
def add_parent_category(name, desc):
    query = """
        INSERT INTO qb_parent_categories (name, description)
        VALUES (:name, :description)
        ON CONFLICT (name) DO NOTHING
    """
    cleaned_desc = desc.strip() if desc and isinstance(desc, str) else None
    execute_query(query, {"name": name.strip(), "description": cleaned_desc})

# 21
def update_parent_category(parent_id, new_name):
    query = """
        UPDATE qb_parent_categories
        SET name = :name
        WHERE id = :id
    """
    execute_query(query, {"name": new_name.strip(), "id": parent_id})

# 22
def delete_parent_category(parent_id):
    # Check for dependencies first
    query_check = "SELECT 1 FROM qb_categories WHERE parent_id = :parent_id LIMIT 1"
    if fetch_one(query_check, {"parent_id": parent_id}):
        return False

    # Proceed to delete
    query_delete = "DELETE FROM qb_parent_categories WHERE id = :parent_id"
    execute_query(query_delete, {"parent_id": parent_id})
    return True

# 23
def get_subcategories(parent_id=None):
    if isinstance(parent_id, int):
        query = "SELECT id, name FROM qb_categories WHERE parent_id = :parent_id ORDER BY name"
        return fetch_all(query, {"parent_id": parent_id})
    else:
        query = "SELECT id, name FROM qb_categories ORDER BY name"
        return fetch_all(query)

# def get_subcategories(parent_id=None):
#     if parent_id is not None:
#         query = "SELECT id, name FROM qb_categories WHERE parent_id = :parent_id ORDER BY name"
#         return fetch_all(query, {"parent_id": parent_id})
#     else:
#         query = "SELECT id, name FROM qb_categories ORDER BY name"
#         return fetch_all(query)
# 24
def add_subcategory(name, parent_id):
    query = """
        INSERT INTO qb_categories (name, parent_id)
        VALUES (:name, :parent_id)
        ON CONFLICT DO NOTHING
    """
    execute_query(query, {"name": name.strip(), "parent_id": parent_id})

# 25
def update_subcategory(subcat_id, new_name):
    query = "UPDATE qb_categories SET name = :new_name WHERE id = :subcat_id"
    execute_query(query, {"new_name": new_name.strip(), "subcat_id": subcat_id})

# 26
def delete_subcategory(subcat_id):
    # Check if any QB accounts are linked to this subcategory
    query_check = "SELECT 1 FROM qb_accounts WHERE category_id = :subcat_id LIMIT 1"
    if fetch_one(query_check, {"subcat_id": subcat_id}):
        return False

    # Safe to delete
    query_delete = "DELETE FROM qb_categories WHERE id = :subcat_id"
    execute_query(query_delete, {"subcat_id": subcat_id})
    return True

# 27
def get_qb_codes(category_id=None):
    if category_id:
        query = "SELECT code, name FROM qb_accounts WHERE category_id = :category_id ORDER BY code"
        return fetch_all(query, {"category_id": category_id})
    else:
        query = "SELECT code, name FROM qb_accounts ORDER BY code"
        return fetch_all(query)


# 28
def add_qb_code(code, name, category_id):
    # Check for existing code to simulate "INSERT OR IGNORE"
    check_query = "SELECT 1 FROM qb_accounts WHERE code = :code"
    exists = fetch_one(check_query, {"code": code})

    if exists:
        return False  # Already exists

    insert_query = """
        INSERT INTO qb_accounts (code, name, category_id)
        VALUES (:code, :name, :category_id)
    """
    execute_query(insert_query, {
        "code": code,
        "name": name.strip(),
        "category_id": category_id
    })
    return True

# 29 
def update_qb_code(code, new_name):
    query = """
        UPDATE qb_accounts
        SET name = :name
        WHERE code = :code
    """
    execute_query(query, {
        "name": new_name.strip(),
        "code": code.strip()
    })

# 30
def delete_qb_code(code):
    query = "DELETE FROM qb_accounts WHERE code = :code"
    execute_query(query, {"code": code.strip()})

# 31
def get_filtered_qb_codes(parent_filter="All", sub_filter="All"):
    base_query = """
        SELECT a.code, a.name, c.name AS subcategory, p.name AS parent_category
        FROM qb_accounts a
        JOIN qb_categories c ON a.category_id = c.id
        JOIN qb_parent_categories p ON c.parent_id = p.id
    """
    filters = []
    params = {}

    if parent_filter != "All":
        filters.append("p.name = :parent_name")
        params["parent_name"] = parent_filter.strip()

    if sub_filter != "All":
        filters.append("c.name = :sub_name")
        params["sub_name"] = sub_filter.strip()

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    base_query += " ORDER BY p.name, c.name, a.code"

    results = fetch_all(base_query, params)
    return pd.DataFrame(results)




# ---------------------
# --- Mapping Logic ---
# ---------------------
# 32
def get_mappings_for_grant(grant_id):
    query = """
        SELECT li.name AS line_item, a.code AS qb_code, a.name AS qb_name,
               c.name AS subcategory, p.name AS parent_category
        FROM grant_line_items_maps m
        JOIN grant_line_items li ON m.line_item_id = li.id
        JOIN qb_accounts a ON m.qb_code = a.code
        JOIN qb_categories c ON a.category_id = c.id
        JOIN qb_parent_categories p ON c.parent_id = p.id
        WHERE m.grant_id = :grant_id
        ORDER BY li.name, p.name, c.name, a.code
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"grant_id": grant_id})
        return pd.DataFrame(result.fetchall(), columns=result.keys())

# 33
def add_qb_mapping(grant_id, qb_code, line_item_id):
    check_query = """
        SELECT 1 FROM qb_to_grant_mapping
        WHERE grant_id = :grant_id AND qb_code = :qb_code AND grant_line_item_id = :line_item_id
        LIMIT 1
    """
    existing = fetch_one(check_query, {
        "grant_id": grant_id,
        "qb_code": qb_code,
        "line_item_id": line_item_id,
    })

    if existing:
        return False  # Mapping already exists

    insert_query = """
        INSERT INTO qb_to_grant_mapping (grant_id, qb_code, grant_line_item_id)
        VALUES (:grant_id, :qb_code, :line_item_id)
    """
    execute_query(insert_query, {
        "grant_id": grant_id,
        "qb_code": qb_code,
        "line_item_id": line_item_id,
    })

    return True


# 34
def delete_qb_mapping(mapping_id):
    query = "DELETE FROM qb_to_grant_mapping WHERE id = :id"
    execute_query(query, {"id": mapping_id})



# -----------------------------
#   Anticipated Expenses Logic
# ----------------------------
# 37
def get_anticipated_expenses_for_grant(grant_id):
    query = """
        SELECT month, expected_amount, line_item_id
        FROM anticipated_expenses
        WHERE grant_id = :grant_id
        ORDER BY month
    """
    return fetch_all(query, {"grant_id": grant_id})

# 38
def save_anticipated_expense(grant_id, line_item_id, month, expected_amount):
    # Check if it already exists
    check_query = """
        SELECT id FROM anticipated_expenses
        WHERE grant_id = :grant_id AND line_item_id = :line_item_id AND month = :month
    """
    existing = fetch_one(check_query, {
        "grant_id": grant_id,
        "line_item_id": line_item_id,
        "month": month
    })

    if existing:
        # Update
        update_query = """
            UPDATE anticipated_expenses
            SET expected_amount = :expected_amount
            WHERE id = :id
        """
        execute_query(update_query, {
            "expected_amount": expected_amount,
            "id": existing["id"]
        })
    else:
        # Insert
        insert_query = """
            INSERT INTO anticipated_expenses (grant_id, line_item_id, month, expected_amount)
            VALUES (:grant_id, :line_item_id, :month, :expected_amount)
        """
        execute_query(insert_query, {
            "grant_id": grant_id,
            "line_item_id": line_item_id,
            "month": month,
            "expected_amount": expected_amount
        })

# 39
def initialize_anticipated_expenses(grant_id, line_item_id, start_date, end_date, allocated_amount=0.0):
    months = generate_month_range(start_date, end_date)
    distribution = distribute_amount_evenly(allocated_amount, months)

    for month, expected_amount in distribution.items():
        save_anticipated_expense(grant_id, line_item_id, month, expected_amount)


# 40
def delete_anticipated_expenses_for_grant(grant_id):
    query = "DELETE FROM anticipated_expenses WHERE grant_id = :grant_id"
    execute_query(query, {"grant_id": grant_id})



# -----------------------
#  Actual Expenses Logic
# -----------------------
# 35
def get_actual_expenses_for_grant(grant_id, month):
    query = """
        SELECT month, qb_code, amount, notes, date_submitted, line_item_id
        FROM actual_expenses
        WHERE grant_id = :grant_id AND month = :month
    """
    return fetch_all(query, {"grant_id": grant_id, "month": month})


# 36
def save_actual_expense(grant_id, month, qb_code, line_item_id, amount, notes, date_submitted):
    # Check for an existing record
    check_query = """
        SELECT id FROM actual_expenses
        WHERE grant_id = :grant_id AND month = :month AND qb_code = :qb_code AND line_item_id = :line_item_id
    """
    existing = fetch_one(check_query, {
        "grant_id": grant_id,
        "month": month,
        "qb_code": qb_code,
        "line_item_id": line_item_id
    })

    if existing:
        # Update the record
        update_query = """
            UPDATE actual_expenses
            SET amount = :amount, notes = :notes, date_submitted = :date_submitted
            WHERE id = :id
        """
        execute_query(update_query, {
            "amount": amount,
            "notes": notes,
            "date_submitted": date_submitted,
            "id": existing["id"]
        })
    else:
        # Insert a new record
        insert_query = """
            INSERT INTO actual_expenses (grant_id, month, qb_code, amount, notes, line_item_id, date_submitted)
            VALUES (:grant_id, :month, :qb_code, :amount, :notes, :line_item_id, :date_submitted)
        """
        execute_query(insert_query, {
            "grant_id": grant_id,
            "month": month,
            "qb_code": qb_code,
            "amount": amount,
            "notes": notes,
            "line_item_id": line_item_id,
            "date_submitted": date_submitted
        })



# ---------------------------
# Summary + Validation Logic 
# ----------------------------


# 41
def is_allocation_exceeding_total(grant_id):
    query = """
        SELECT g.total_award, COALESCE(SUM(li.allocated_amount), 0) AS total_allocated
        FROM grants g
        LEFT JOIN grant_line_items li ON g.id = li.grant_id
        WHERE g.id = :grant_id
        GROUP BY g.id
    """
    result = fetch_one(query, {"grant_id": grant_id})
    if result:
        total_award, total_allocated = result
        return total_allocated > total_award, total_allocated, total_award
    return False, 0, 0



# exceeds, allocated, total = is_allocation_exceeding_total(grant_id)
# if exceeds:
#     st.warning(f"⚠️ Total allocated (${allocated}) exceeds total award (${total}).")

# 42
def get_total_allocated_for_grant(grant_id):
    query = """
        SELECT COALESCE(SUM(allocated_amount), 0.0) AS total_allocated
        FROM grant_line_items
        WHERE grant_id = :grant_id
    """
    result = fetch_one(query, {"grant_id": grant_id})
    return result[0] if result else 0.0


# 43
def get_line_item_allocations(grant_id):
    query = """
        SELECT id, name, allocated_amount
        FROM grant_line_items
        WHERE grant_id = :grant_id
    """
    return fetch_all(query, {"grant_id": grant_id})

# 44
def get_actual_expense_totals(grant_id):
    query = """
        SELECT line_item_id, SUM(amount) AS total_spent
        FROM actual_expenses
        WHERE grant_id = :grant_id
        GROUP BY line_item_id
    """
    return fetch_all(query, {"grant_id": grant_id})

# 45
def get_grant_summary_data(grant_id):
    # Fetch allocations and actuals (both use SQLAlchemy under the hood now)
    line_items = get_line_item_allocations(grant_id)
    actuals = dict(get_actual_expense_totals(grant_id))  # line_item_id → total_spent

    data = []
    for item_id, name, allocated in line_items:
        spent = actuals.get(item_id, 0.0)
        percent_spent = round((spent / allocated) * 100, 1) if allocated else 0.0
        remaining = allocated - spent
        data.append({
            "Line Item": name,
            "Allocated": allocated,
            "Spent": spent,
            "% Spent": f"{percent_spent}%",
            "Remaining": remaining
        })

    return pd.DataFrame(data)
