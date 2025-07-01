# --- db_utils.py (Supabase version)
from sqlalchemy import create_engine, text
import pandas as pd
import streamlit as st
from datetime import date
from helpers.helpers import generate_month_range, distribute_amount_evenly, normalize_string

# Connect using secrets
engine = create_engine(st.secrets["database"]["url"])


# -------------------------
# Read Functions
# -------------------------

def fetch_all(query, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row._mapping) for row in result]

def fetch_one(query, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        row = result.fetchone()
        return dict(row._mapping) if row else None

# -------------------------
# Write Functions
# -------------------------

def execute_query(query, params=None):
    with engine.begin() as conn:
        conn.execute(text(query), params or {})

def insert_and_return_id(query, params=None):
    with engine.begin() as conn:
        result = conn.execute(text(query + " RETURNING id"), params or {})
        return result.scalar_one()

########################
### HELPER FUNCTIONS ###
########################

# ---------------
# Get Helpers
# --------------

def get_all_from_table(table, fields="*", order_by=None):
    """
    Fetch all rows from a table.

    Args:
        table (str): Table name.
        fields (str): Fields to select (default '*').
        order_by (str): Column to order by.

    Returns:
        list of dicts
    """
    query = f"SELECT {fields} FROM {table}"
    if order_by:
        query += f" ORDER BY {order_by}"
    return fetch_all(query)


def get_record_by_id(table, id_column, id_value, fields="*"):
    """
    Fetch a single record by ID.

    Args:
        table (str): Table name.
        id_column (str): ID column (e.g., 'id').
        id_value (Any): Value of the ID.
        fields (str): Fields to select (default '*').

    Returns:
        dict or None
    """
    query = f"SELECT {fields} FROM {table} WHERE {id_column} = :id_value"
    return fetch_one(query, {"id_value": id_value})

# ------------------
# Insert/Add Helpers
# ------------------

def insert_if_not_exists(table, fields, values, conflict_fields, case_insensitive_fields=None, normalize_case=True):
    """
    Inserts a new record into the specified table if a matching row does not already exist.

    Args:
        table (str): The name of the table to insert into.
        fields (list[str]): List of column names to insert.
        values (dict): Dictionary of values to insert, keyed by column name.
        conflict_fields (list[str]): Fields used to check if the row already exists.
        case_insensitive_fields (list[str], optional): Fields to compare in a case-insensitive way.
        normalize_case (bool, optional): If True, strings are normalized (trimmed and title-cased). Default is True.

    Returns:
        bool: True if a new record was inserted, False if it already existed.
    """
    # normalize and sanitize input values
    clean_values = {
        k: normalize_string(v) if normalize_case else v
        for k, v in values.items()
    }

    # WHERE clause to check for duplicates
    where_clauses = []
    params = {}
    for field in conflict_fields:
        if case_insensitive_fields and field in case_insensitive_fields:
            where_clauses.append(f"LOWER({field}) = LOWER(:{field})")
        else:
            where_clauses.append(f"{field} = :{field}")
        params[field] = clean_values[field]

    # Checks if record already exists
    check_query = f"SELECT 1 FROM {table} WHERE {' AND '.join(where_clauses)}"
    if fetch_one(check_query, params):
        return False    # Skip insert if already present

    # build and execute INSERT statement
    insert_fields = ", ".join(fields)
    placeholders = ", ".join(f":{f}" for f in fields)
    insert_query = f"INSERT INTO {table} ({insert_fields}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
    execute_query(insert_query, clean_values)

    return True # insert succeeded 

# ---------------
# Update Helpers
# ---------------
def update_name_if_unique(table, id_column, id_value, name_column, new_name, normalize_case=True):
    """
    Updates the name field of a record if the new name is unique across the table.

    Args:
        table (str): The name of the table.
        id_column (str): The name of the primary key column.
        id_value (Any): The value of the ID for the record being updated.
        name_column (str): The column to update (e.g., 'name').
        new_name (str): The proposed new name value.
        normalize_case (bool): If True, normalize the name string (strip + title case).

    Returns:
        bool: True if the update was successful, False if the name already exists in another record.
    """
     
    formatted_name = normalize_string(new_name) if normalize_case else new_name.strip()

    query_check = f"""
        SELECT 1 FROM {table}
        WHERE LOWER({name_column}) = LOWER(:name)
        AND {id_column} != :id_value
    """
    if fetch_one(query_check, {"name": formatted_name, "id_value": id_value}):
        return False

    query_update = f"""
        UPDATE {table}
        SET {name_column} = :name
        WHERE {id_column} = :id_value
    """
    execute_query(query_update, {"name": formatted_name, "id_value": id_value})
    return True


def update_record(table, id_column, id_value, update_fields: dict, normalize=True):
    """
    Generic update function to modify fields of a record by ID

    Args:
        table (str): The name of the table to update
        id_column (str): The primary key column name e.g. 'id'
        id_value: The value of the row's ID to identify the record
        update_fields (dict): Dictionary of {field_name: new_value} to update
        normalize (bool): If True, normalize string fields (Strip + title case)
    Returns:
        None
    """
    # Prepare clean values
    clean_values = {
        key: normalize_string(value) if normalize and isinstance(value, str) else value
        for key, value in update_fields.items()
    }
    clean_values[id_column] = id_value

    # generate the SET clause
    assignments = ", ".join([f"{key} = :{key}" for key in update_fields.keys()])
    query = f"""
        UPDATE {table}
        SET {assignments}
        WHERE {id_column} = :{id_column}
    """
    execute_query(query, clean_values)

# --------------
# Delete Helper
# --------------

def delete_record(table, id_column, id_value):
    """
    Deletes a single record from the specified table using its ID.

    Args:
        table (str): The name of the table.
        id_column (str): The name of the ID column (e.g., 'id', 'code', etc.).
        id_value (Any): The value of the ID to match.

    Returns:
        None
    """
    query = f"DELETE FROM {table} WHERE {id_column} = :{id_column}"
    execute_query(query, {id_column: id_value})

###################
#### END OF HELPERS
###################

# ---------------------
# GRANTS TABLE & LOGIC
# --------------------


def grant_exists(grant_name):
    normalized = grant_name.strip().lower()
    query = "SELECT 1 FROM grants WHERE LOWER(TRIM(name)) = :normalized_name LIMIT 1"
    return fetch_one(query, {"normalized_name": normalized})

def get_all_grants():
    fields = "g.id, g.name, f.name AS funder, g.start_date, g.end_date, g.total_award, g.status, g.notes"
    query = f"""
    SELECT {fields} 
    FROM grants g 
    JOIN funders f ON g.funder_id = f.id
    ORDER BY g.name DESC
    """
    return fetch_all(query)

def get_grant_by_id(grant_id):
    query = """
        SELECT g.id, g.name, f.name AS funder_name, f.type AS funder_type,
               g.start_date, g.end_date, g.total_award, g.status, g.notes
        FROM grants g
        LEFT JOIN funders f ON g.funder_id = f.id
        WHERE g.id = :grant_id
    """
    return fetch_one(query, {"grant_id": grant_id})

# Add Grant
def add_grant(grant_name, funder_id, start_date, end_date, total_award, status, notes):
    return insert_if_not_exists(
        table="grants",
        fields=["name", "funder_id", "start_date", "end_date", "total_award", "status", "notes"],
        values={
            "name": grant_name,
            "funder_id": funder_id,
            "start_date": start_date.isoformat() if isinstance(start_date, date) else start_date,
            "end_date": end_date.isoformat() if isinstance(end_date, date) else end_date,
            "total_award": total_award,
            "status": status,
            "notes": notes if isinstance(notes, str) and notes.strip() else None
        },
        conflict_fields=["name"],
        case_insensitive_fields=["name"]
    )

# Update Grant
def update_grant(grant_id, grant_name, funder_id, start_date, end_date, total_award, status, notes):
    return update_record(
        table="grants",
        id_column="id",
        id_value=grant_id,
        update_fields={
            "name": grant_name,
            "funder_id": funder_id,
            "start_date": start_date.isoformat() if isinstance(start_date, date) else start_date,
            "end_date": end_date.isoformat() if isinstance(end_date, date) else end_date,
            "total_award": total_award,
            "status": status,
            "notes": notes if isinstance(notes, str) and notes.strip() else None
        }
    )

# Delete Grant
def delete_grant(grant_id):
    delete_record("grants", "id", grant_id)
    return True

# -----------------------
# GRANT LINE ITEMS TABLE
# ---------------------- 
def get_line_items_by_grant(grant_id):
    query = """
        SELECT id, name, description, allocated_amount
        FROM grant_line_items
        WHERE grant_id = :grant_id
        ORDER BY name
    """
    return fetch_all(query, {"grant_id": grant_id})

# ------ Financials 
def get_total_allocated_for_grant(grant_id):
    query = """
        SELECT COALESCE(SUM(allocated_amount), 0.0) AS total_allocated
        FROM grant_line_items
        WHERE grant_id = :grant_id
    """
    result = fetch_one(query, {"grant_id": grant_id})
    return result[0] if result else 0.0



def add_line_item(grant_id, name, description, allocated_amount=0.0):
    clean_desc = description.strip() if isinstance(description, str) and description.strip() else None
    return insert_if_not_exists(
        table="grant_line_items",
        fields=["grant_id", "name", "description", "allocated_amount"],
        values={
            "grant_id": grant_id,
            "name": name,
            "description": clean_desc,
            "allocated_amount": allocated_amount
        },
        conflict_fields=["grant_id", "name"],
        case_insensitive_fields=["name"]
    )


def update_line_item(line_item_id, name, description, allocated_amount):
    return update_record(
        table="grant_line_items",
        id_column="id",
        id_value=line_item_id,
        update_fields={
            "name": name,
            "description": description,
            "allocated_amount": allocated_amount,
        }
    )

def delete_line_item(item_id):
    delete_record("grant_line_items", "id", item_id)
    return True


def get_line_item_allocations(grant_id):
    query = """
        SELECT id, name, allocated_amount
        FROM grant_line_items
        WHERE grant_id = :grant_id
    """
    return fetch_all(query, {"grant_id": grant_id})

# U3. Update Line Item Logic
def update_line_item_allocated(item_id, new_allocated_amount):
    return update_record(
        table="grant_line_items",
        id_column="id",
        id_value=item_id,
        update_fields={
            "allocated_amount": new_allocated_amount
        }
    )




# -----------------------
# FUNDERS TABLE & LOGIC
# -----------------------

def get_all_funders():
    return get_all_from_table("funders", "id, name, type", order_by="name")

# Add Funder Information
def add_funder_if_missing(funder_name, funder_type):
    return insert_if_not_exists(
        table="funders",
        fields=["name", "type"],
        values={"name": funder_name, "type": funder_type},
        conflict_fields=["name"],
        case_insensitive_fields=["name"]
    )

def get_funder_id(funder_name):
    query = "SELECT id FROM funders WHERE LOWER(name) = LOWER(:name)"
    result = fetch_one(query, {"name": funder_name.strip()})
    return result["id"] if result else None

def delete_funder(funder_id):
    delete_record("funders", "id", funder_id)
    return True


# ----------------------------
# QuickBooks Logic + Tables
# ---------------------------

def get_parent_categories():
    return get_all_from_table("qb_parent_categories", "id, name", order_by="name")

def get_subcategories(parent_id=None):
    if parent_id is not None:
        return fetch_all(
            "SELECT id, name FROM qb_categories WHERE parent_id = :parent_id ORDER BY name",
            {"parent_id":parent_id}
        )
    return get_all_from_table("qb_categories", "id, name", order_by="name")

def get_qb_codes(category_id=None):
    if category_id is not None:
        return fetch_all(
            "SELECT code, name FROM qb_accounts WHERE category_id - :category_id ORDER BY code",
            {"category_id": category_id}
        )
    return get_all_from_table("qb_accounts", "code, name", order_by="code")


# A4. QuickBooks Parent Category Information
def add_parent_category(name, desc):
    return insert_if_not_exists(
        table="qb_parent_categories",
        fields=["name", "description"],
        values={
            "name": name,
            "description": desc if isinstance(desc, str) and desc.strip() else None
        },
        conflict_fields=["name"],
        case_insensitive_fields=["name"]
    )
# A5. QuickBooks Subcategory Information
def add_subcategory(name, parent_id):
    return insert_if_not_exists(
        table="qb_categories",
        fields=["name", "parent_id"],
        values={"name": name, "parent_id": parent_id},
        conflict_fields=["name", "parent_id"],
        case_insensitive_fields=["name"]
    )


# A6. QuickBooks Code Information 
def add_qb_code(code, name, category_id):
    return insert_if_not_exists(
        table="qb_accounts",
        fields=["code", "name", "category_id"],
        values={
            "code": code,
            "name": name,
            "category_id": category_id
        },
        conflict_fields=["code"],
        case_insensitive_fields=["code"]
    )

# U4. Update Parent Category Logic
def update_parent_category(parent_id, new_name):
    return update_name_if_unique("qb_parent_categories", "id", parent_id, "name", new_name)

# U5. Update Subcategory Logic
def update_subcategory(subcat_id, new_name):
    return update_name_if_unique("qb_categories", "id", subcat_id, "name", new_name)
   
# U6. Update QB Code Logic
def update_qb_code(code, new_name):
    return update_name_if_unique("qb_accounts", "code", code.strip(), "name", new_name)


# Delete Parent Category
def delete_parent_category(parent_id):
    """
    Deletes a parent category if no subcategories are linked to it.

    Returns:
        bool: True if deleted, False if dependency found
    """
    query_check = "SELECT 1 FROM qb_categories WHERE parent_id = :parent_id LIMIT 1"
    if fetch_one(query_check, {"parent_id": parent_id}):
        return False
    
    delete_record("qb_parent_categories", "id", parent_id)
    return True

# Delete Subcategory
def delete_subcategory(subcat_id):
    """
    Deletes a subcategory if no QB codes are linked to it.

    Returns:
        bool: True if deleted, False if dependency found.
    """
    query_check = "SELECT 1 FROM qb_accounts WHERE category_id = :subcat_id LIMIT 1"
    if fetch_one(query_check, {"subcat_id": subcat_id}):
        return False
    
    delete_record("qb_categories", "id", subcat_id)
    return True

# Delete QB Code
def delete_qb_code(code):
    delete_record("qb_accounts", "code", code)
    return True

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




#----------
# QB MAPPING
# ------------
def get_mappings_for_grant(grant_id):
    """
    Returns a mapping of line items to QuickBooks codes for a specific grant,
    including subcategory and parent category info.

    Args:
        grant_id (int): The ID of the grant.

    Returns:
        pd.DataFrame: Line item to QB code mappings.
    """
    query = """
        SELECT
            m.id,
            li.name AS line_item,
            a.code AS qb_code,
            a.name AS qb_name,
            c.name AS subcategory,
            p.name AS parent_category
        FROM qb_to_grant_mapping m
        JOIN grant_line_items li ON m.grant_line_item_id = li.id
        JOIN qb_accounts a ON m.qb_code = a.code
        JOIN qb_categories c ON a.category_id = c.id
        JOIN qb_parent_categories p ON c.parent_id = p.id
        WHERE m.grant_id = :grant_id
        ORDER BY li.name, p.name, c.name, a.code
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"grant_id": grant_id})
        return pd.DataFrame(result.fetchall(), columns=result.keys())

# A7. Many to Many Mapping - Custom 
def add_qb_mapping(grant_id, qb_code, line_item_id):
    return insert_if_not_exists(
        table="qb_to_grant_mapping",
        fields=["grant_id", "qb_code", "grant_line_item_id"],
        values={
            "grant_id": grant_id,
            "qb_code": qb_code,
            "grant_line_item_id": line_item_id
        },
        conflict_fields=["grant_id", "qb_code", "grant_line_item_id"]
    )


# Delete QB to Grant Mapping ID
def delete_qb_mapping(mapping_id):
    delete_record("qb_to_grant_mapping", "id", mapping_id)
    return True


# -------------------
# ACTUAL EXPENSES TABLE
# -------------------
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

def get_actual_expense_totals(grant_id):
    query = """
        SELECT line_item_id, SUM(amount) AS total_spent
        FROM actual_expenses
        WHERE grant_id = :grant_id
        GROUP BY line_item_id
    """
    return fetch_all(query, {"grant_id": grant_id})


def get_grant_summary_data(grant_id):
    # Fetch allocations and actuals (both use SQLAlchemy under the hood now)
    line_items = get_line_item_allocations(grant_id)
    actuals = dict(get_actual_expense_totals(grant_id))  # line_item_id → total_spent

    data = []
    for item_id, name, allocated in line_items:
        allocated = float(allocated)  # 💡 convert here!
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

def delete_anticipated_expenses_for_grant(grant_id):
    delete_record("anticipated_expenses", "grant_id", grant_id)
    return True


# --------------
# Summary + Validation Logic
# ------------------------

# 41
# def is_allocation_exceeding_total(grant_id):
#     query = """
#         SELECT g.total_award, COALESCE(SUM(li.allocated_amount), 0) AS total_allocated
#         FROM grants g
#         LEFT JOIN grant_line_items li ON g.id = li.grant_id
#         WHERE g.id = :grant_id
#         GROUP BY g.id
#     """
#     result = fetch_one(query, {"grant_id": grant_id})
#     if result:
#         total_award, total_allocated = result
#         return float(total_allocated) > float(total_award), float(total_allocated), float(total_award)
#     return False, 0.0, 0.0

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
        total_award = result["total_award"]
        total_allocated = result["total_allocated"]
        return float(total_allocated) > float(total_award), float(total_allocated), float(total_award)
    return False, 0.0, 0.0
