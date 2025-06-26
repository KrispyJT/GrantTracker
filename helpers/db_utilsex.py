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
# 
def insert_and_return_id(query, params=None):
    with engine.begin() as conn:
        result = conn.execute(text(query + " RETURNING id"), params or {})
        return result.scalar_one()


# -----------------
# Helper Functions
# ------------------

# Add Logic 
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


# Update Helper Function
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




#########################
### Other Misc functions
########################



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

# 7
def get_funder_id(funder_name):
    query = "SELECT id FROM funders WHERE LOWER(name) = LOWER(:name)"
    result = fetch_one(query, {"name": funder_name.strip()})
    return result["id"] if result else None

# 12
def get_all_funders():
    query = "SELECT id, name, type FROM funders ORDER BY name"
    return fetch_all(query)


# 14
def get_line_items_by_grant(grant_id):
    query = """
        SELECT id, name, description, allocated_amount
        FROM grant_line_items
        WHERE grant_id = :grant_id
        ORDER BY name
    """
    return fetch_all(query, {"grant_id": grant_id})

# 19
def get_parent_categories():
    query = "SELECT id, name FROM qb_parent_categories ORDER BY name"
    return fetch_all(query)


# 23
def get_subcategories(parent_id=None):
    if isinstance(parent_id, int):
        query = "SELECT id, name FROM qb_categories WHERE parent_id = :parent_id ORDER BY name"
        return fetch_all(query, {"parent_id": parent_id})
    else:
        query = "SELECT id, name FROM qb_categories ORDER BY name"
        return fetch_all(query)

# 27
def get_qb_codes(category_id=None):
    if category_id:
        query = "SELECT code, name FROM qb_accounts WHERE category_id = :category_id ORDER BY code"
        return fetch_all(query, {"category_id": category_id})
    else:
        query = "SELECT code, name FROM qb_accounts ORDER BY code"
        return fetch_all(query)
# --------------------------
# Adding Logic
# ------------------------
# 1a. Grant Information
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

# 1b. Funder Information
def add_funder_if_missing(funder_name, funder_type):
    return insert_if_not_exists(
        table="funders",
        fields=["name", "type"],
        values={"name": funder_name, "type": funder_type},
        conflict_fields=["name"],
        case_insensitive_fields=["name"]
    )

# 1c. Grant Line Item Information
def add_line_item(grant_id, name, description, allocated_amount=0.0):
    return insert_if_not_exists(
        table="grant_line_items",
        fields=["grant_id", "name", "description", "allocated_amount"],
        values={
            "grant_id": grant_id,
            "name": name,
            "description": description,
            "allocated_amount": allocated_amount
        },
        conflict_fields=["grant_id", "name"],
        case_insensitive_fields=["name"]
    )

# 1d. QuickBooks Parent Category Information
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
# 1e. QuickBooks Subcategory Information
def add_subcategory(name, parent_id):
    return insert_if_not_exists(
        table="qb_categories",
        fields=["name", "parent_id"],
        values={"name": name, "parent_id": parent_id},
        conflict_fields=["name", "parent_id"],
        case_insensitive_fields=["name"]
    )


# 1f. QuickBooks Code Information 
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

# M:M Custom 
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



# ------------
# Update Logic
# -------------

# A
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



# B
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

# C
def update_line_item_allocated(item_id, new_allocated_amount):
    return update_record(
        table="grant_line_items",
        id_column="id",
        id_value=item_id,
        update_fields={
            "allocated_amount": new_allocated_amount
        }
    )

# D
def update_parent_category(parent_id, new_name):
    return update_name_if_unique("qb_parent_categories", "id", parent_id, "name", new_name)

# E
def update_subcategory(subcat_id, new_name):
    return update_name_if_unique("qb_categories", "id", subcat_id, "name", new_name)
   
# F
def update_qb_code(code, new_name):
    return update_name_if_unique("qb_accounts", "code", code.strip(), "name", new_name)



