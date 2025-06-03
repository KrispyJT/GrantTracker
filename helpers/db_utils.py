# db_utils.py
import sqlite3
import pandas as pd
from datetime import date
import os

# --- Constants ---
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "grant_tracker.db")

# --- Helper: Connect to DB ---
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# --- Query Helpers ---
def fetch_all(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def fetch_one(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return result

def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

# --- Convenience Insert/Update Wrappers ---
def insert_and_return_id(query, params):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id



# ---------------
# GRANT LOGIC HELPER
# ---------------

# --- Grant Logic ---
def get_all_grants():
    query = """
        SELECT g.id, g.name, f.name AS funder, g.start_date, g.end_date, g.status, g.total_award, g.notes
        FROM grants g
        LEFT JOIN funders f ON g.funder_id = f.id
        ORDER BY g.start_date DESC
    """
    with get_connection() as conn:
        return conn.execute(query).fetchall()

def grant_exists(grant_name):
    query = "SELECT 1 FROM grants WHERE name = ?"
    with get_connection() as conn:
        return conn.execute(query, (grant_name.strip(),)).fetchone() is not None

def get_funder_id(funder_name):
    query = "SELECT id FROM funders WHERE name = ?"
    with get_connection() as conn:
        row = conn.execute(query, (funder_name.strip(),)).fetchone()
        return row[0] if row else None

def add_funder_if_missing(funder_name, funder_type):
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO funders (name, type) VALUES (?, ?)",
                     (funder_name.strip(), funder_type.strip()))

def add_grant(grant_name, funder_id, start_date, end_date, total_award, status, notes):
    query = """
        INSERT INTO grants (name, funder_id, start_date, end_date, total_award, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        conn.execute(query, (
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
    with get_connection() as conn:
        conn.execute(query, (
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
    with get_connection() as conn:
        conn.execute("DELETE FROM grants WHERE id = ?", (grant_id,))

def get_all_funders():
    with get_connection() as conn:
        return conn.execute("SELECT id, name, type FROM funders ORDER BY name").fetchall()

def get_grant_by_id(grant_id):
    query = """
        SELECT g.id, g.name, f.name AS funder_name, f.type AS funder_type, g.start_date, g.end_date, g.total_award, g.status, g.notes
        FROM grants g
        LEFT JOIN funders f ON g.funder_id = f.id
        WHERE g.id = ?
    """
    with get_connection() as conn:
        return conn.execute(query, (grant_id,)).fetchone()











# ------------------------
# -- QUICKBOOKS.PY LOGIC HELPER
# ------------------------
# PARENT CATEGORIES
# Fetch Parent Categories
def get_parent_categories(conn):
    query = "SELECT id, name FROM qb_parent_categories ORDER BY name"
    return fetch_all(conn, query)

# Add Parent Category
def add_parent_category(name, desc):
    query = "INSERT INTO qb_parent_categories (name, description) VALUES (?, ?)"
    execute_query(query, (name, desc))

# UPDATE PARENT
def update_parent_category(parent_id, new_name):
    query = "UPDATE qb_parent_categories SET name = ? WHERE id = ?"
    execute_query(query, (new_name, parent_id))

# DELETE PARENT
def delete_parent_category(parent_id):
    # Only allow deletion if no subcategories exist
    subcats = fetch_all("SELECT 1 FROM qb_categories WHERE parent_id = ?", (parent_id,))
    if subcats:
        return False
    execute_query("DELETE FROM qb_parent_categories WHERE id = ?", (parent_id,))
    return True

# SUBCATEGORIES - MID LEVEL of QB 
# FETCH SUB
def get_subcategories(conn, parent_id=None):
    if parent_id:
        query = "SELECT id, name FROM qb_categories WHERE parent_id = ? ORDER BY name"
        return fetch_all(conn, query, (parent_id,))
    else:
        query = "SELECT id, name FROM qb_categories ORDER BY name"
        return fetch_all(conn, query)
    
# ADD SUB
def add_subcategory(name, parent_id):
    query = "INSERT INTO qb_categories (name, parent_id) VALUES (?, ?)"
    execute_query(query, (name, parent_id))

# UPDATE SUB
def update_subcategory(subcat_id, new_name):
    query = "UPDATE qb_categories SET name = ? WHERE id = ?"
    execute_query(query, (new_name, subcat_id))
    
# DELETE SUB
def delete_subcategory(subcat_id):
    # Only allow deletion if no QB codes exist under it
    codes = fetch_all("SELECT 1 FROM qb_accounts WHERE category_id = ?", (subcat_id,))
    if codes:
        return False
    execute_query("DELETE FROM qb_categories WHERE id = ?", (subcat_id,))
    return True



# QB CODES - SMALLEST LAYER 
# GET CODES
def get_qb_codes(conn, category_id=None):
    if category_id:
        query = "SELECT code, name FROM qb_accounts WHERE category_id = ? ORDER BY code"
        return fetch_all(conn, query, (category_id,))
    else:
        query = "SELECT code, name FROM qb_accounts ORDER BY code"
        return fetch_all(conn, query)
    
# ADD QB CODE
def add_qb_code(code, name, category_id):
    try:
        query = "INSERT INTO qb_accounts (code, name, category_id) VALUES (?, ?, ?)"
        execute_query(query, (code, name, category_id))
        return True
    except sqlite3.IntegrityError:
        return False

# ADD QB CODE
# def insert_qb_code(conn, code, name, category_id):
#     query = "INSERT INTO qb_accounts (code, name, category_id) VALUES (?, ?, ?)"
#     execute_query(conn, query, (code, name, category_id))
# UPDATE QB CODE
def update_qb_code(conn, code, new_name):
    query = "UPDATE qb_accounts SET name = ? WHERE code = ?"
    execute_query(conn, query, (new_name, code))
# DELETE QB CODE
def delete_qb_code(conn, code):
    query = "DELETE FROM qb_accounts WHERE code = ?"
    execute_query(conn, query, (code,))


def get_filtered_qb_codes(parent_filter, sub_filter):
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
