# --- db_utils.py (Refactored) ---
import sqlite3
import pandas as pd
from datetime import date
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "grant_tracker.db")

# --- DB Connection ---
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# --- Shared DB Ops ---
def fetch_all(query, params=()):
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()

def fetch_one(query, params=()):
    with get_connection() as conn:
        return conn.execute(query, params).fetchone()

def execute_query(query, params=()):
    with get_connection() as conn:
        conn.execute(query, params)
        conn.commit()

def insert_and_return_id(query, params):
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid

# --- Grant Logic ---
def get_all_grants():
    query = """
        SELECT g.id, g.name, f.name AS funder, g.start_date, g.end_date, g.status, g.total_award, g.notes
        FROM grants g
        LEFT JOIN funders f ON g.funder_id = f.id
        ORDER BY g.start_date DESC
    """
    return fetch_all(query)

def grant_exists(grant_name):
    query = "SELECT 1 FROM grants WHERE name = ?"
    return fetch_one(query, (grant_name.strip(),)) is not None

def get_funder_id(funder_name):
    query = "SELECT id FROM funders WHERE name = ?"
    result = fetch_one(query, (funder_name.strip(),))
    return result[0] if result else None

def add_funder_if_missing(funder_name, funder_type):
    query = "INSERT OR IGNORE INTO funders (name, type) VALUES (?, ?)"
    execute_query(query, (funder_name.strip(), funder_type.strip()))

def add_grant(grant_name, funder_id, start_date, end_date, total_award, status, notes):
    query = """
        INSERT INTO grants (name, funder_id, start_date, end_date, total_award, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(query, (
        grant_name.strip(),
        funder_id,
        start_date.isoformat() if isinstance(start_date, date) else start_date,
        end_date.isoformat() if isinstance(end_date, date) else end_date,
        total_award,
        status.strip(),
        notes.strip() if notes else None
    ))

def update_grant(grant_id, grant_name, funder_id, start_date, end_date, total_award, status, notes):
    query = """
        UPDATE grants
        SET name = ?, funder_id = ?, start_date = ?, end_date = ?, total_award = ?, status = ?, notes = ?
        WHERE id = ?
    """
    execute_query(query, (
        grant_name.strip(),
        funder_id,
        start_date.isoformat() if isinstance(start_date, date) else start_date,
        end_date.isoformat() if isinstance(end_date, date) else end_date,
        total_award,
        status.strip(),
        notes.strip() if notes else None,
        grant_id
    ))

def delete_grant(grant_id):
    query = "DELETE FROM grants WHERE id = ?"
    execute_query(query, (grant_id,))

def get_all_funders():
    query = "SELECT id, name, type FROM funders ORDER BY name"
    return fetch_all(query)

def get_grant_by_id(grant_id):
    query = """
        SELECT g.id, g.name, f.name AS funder_name, f.type AS funder_type, g.start_date, g.end_date, g.total_award, g.status, g.notes
        FROM grants g
        LEFT JOIN funders f ON g.funder_id = f.id
        WHERE g.id = ?
    """
    return fetch_one(query, (grant_id,))

# --- Line Item Logic ---
def get_line_items_by_grant(grant_id):
    query = """
        SELECT id, name, description
        FROM grant_line_items
        WHERE grant_id = ?
        ORDER BY name
    """
    return fetch_all(query, (grant_id,))

def add_line_item(grant_id, name, description):
    query = "INSERT INTO grant_line_items (grant_id, name, description) VALUES (?, ?, ?)"
    execute_query(query, (grant_id, name.strip(), description.strip()))

def delete_line_item(item_id):
    query = "DELETE FROM grant_line_items WHERE id = ?"
    execute_query(query, (item_id,))

# --- QuickBooks Logic ---
def get_parent_categories():
    query = "SELECT id, name FROM qb_parent_categories ORDER BY name"
    return fetch_all(query)

def add_parent_category(name, desc):
    query = "INSERT INTO qb_parent_categories (name, description) VALUES (?, ?)"
    execute_query(query, (name, desc))

def update_parent_category(parent_id, new_name):
    query = "UPDATE qb_parent_categories SET name = ? WHERE id = ?"
    execute_query(query, (new_name, parent_id))

def delete_parent_category(parent_id):
    query_check = "SELECT 1 FROM qb_categories WHERE parent_id = ?"
    if fetch_one(query_check, (parent_id,)):
        return False
    query_delete = "DELETE FROM qb_parent_categories WHERE id = ?"
    execute_query(query_delete, (parent_id,))
    return True

def get_subcategories(parent_id=None):
    if parent_id:
        query = "SELECT id, name FROM qb_categories WHERE parent_id = ? ORDER BY name"
        return fetch_all(query, (parent_id,))
    query = "SELECT id, name FROM qb_categories ORDER BY name"
    return fetch_all(query)

def add_subcategory(name, parent_id):
    query = "INSERT INTO qb_categories (name, parent_id) VALUES (?, ?)"
    execute_query(query, (name, parent_id))

def update_subcategory(subcat_id, new_name):
    query = "UPDATE qb_categories SET name = ? WHERE id = ?"
    execute_query(query, (new_name, subcat_id))

def delete_subcategory(subcat_id):
    query_check = "SELECT 1 FROM qb_accounts WHERE category_id = ?"
    if fetch_one(query_check, (subcat_id,)):
        return False
    query_delete = "DELETE FROM qb_categories WHERE id = ?"
    execute_query(query_delete, (subcat_id,))
    return True

def get_qb_codes(category_id=None):
    if category_id:
        query = "SELECT code, name FROM qb_accounts WHERE category_id = ? ORDER BY code"
        return fetch_all(query, (category_id,))
    query = "SELECT code, name FROM qb_accounts ORDER BY code"
    return fetch_all(query)

def add_qb_code(code, name, category_id):
    try:
        query = "INSERT INTO qb_accounts (code, name, category_id) VALUES (?, ?, ?)"
        execute_query(query, (code, name, category_id))
        return True
    except sqlite3.IntegrityError:
        return False

def update_qb_code(code, new_name):
    query = "UPDATE qb_accounts SET name = ? WHERE code = ?"
    execute_query(query, (new_name, code))

def delete_qb_code(code):
    query = "DELETE FROM qb_accounts WHERE code = ?"
    execute_query(query, (code,))

def get_filtered_qb_codes(parent_filter="All", sub_filter="All"):
    base_query = """
        SELECT a.code, a.name, c.name AS subcategory, p.name AS parent_category
        FROM qb_accounts a
        JOIN qb_categories c ON a.category_id = c.id
        JOIN qb_parent_categories p ON c.parent_id = p.id
    """
    filters = []
    params = []
    if parent_filter != "All":
        filters.append("p.name = ?")
        params.append(parent_filter)
    if sub_filter != "All":
        filters.append("c.name = ?")
        params.append(sub_filter)
    if filters:
        base_query += " WHERE " + " AND ".join(filters)
    base_query += " ORDER BY p.name, c.name, a.code"
    return pd.read_sql_query(base_query, get_connection(), params=params)

# --- Mapping Logic ---
def get_mappings_for_grant(grant_id):
    query = """
        SELECT m.id, a.code, a.name, l.name
        FROM qb_to_grant_mapping m
        JOIN qb_accounts a ON m.qb_code = a.code
        JOIN grant_line_items l ON m.grant_line_item_id = l.id
        WHERE m.grant_id = ?
        ORDER BY a.code
    """
    return fetch_all(query, (grant_id,))

def add_qb_mapping(grant_id, qb_code, line_item_id):
    query = "INSERT INTO qb_to_grant_mapping (grant_id, qb_code, grant_line_item_id) VALUES (?, ?, ?)"
    execute_query(query, (grant_id, qb_code, line_item_id))

def delete_qb_mapping(mapping_id):
    query = "DELETE FROM qb_to_grant_mapping WHERE id = ?"
    execute_query(query, (mapping_id,))
