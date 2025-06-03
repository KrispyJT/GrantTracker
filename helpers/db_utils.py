# db_utils.py
import sqlite3
import os

# --- Constants ---
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "grant_tracker.db")

# --- Helper: Connect to DB ---
def get_connection():
    return sqlite3.connect(DB_PATH)

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



# -- HELPERS FOR QUICKBOOKS
def get_parent_categories(conn):
    query = "SELECT id, name FROM qb_parent_categories ORDER BY name"
    return fetch_all(conn, query)

def get_subcategories(conn, parent_id=None):
    if parent_id:
        query = "SELECT id, name FROM qb_categories WHERE parent_id = ? ORDER BY name"
        return fetch_all(conn, query, (parent_id,))
    else:
        query = "SELECT id, name FROM qb_categories ORDER BY name"
        return fetch_all(conn, query)

def get_qb_codes(conn, category_id=None):
    if category_id:
        query = "SELECT code, name FROM qb_accounts WHERE category_id = ? ORDER BY code"
        return fetch_all(conn, query, (category_id,))
    else:
        query = "SELECT code, name FROM qb_accounts ORDER BY code"
        return fetch_all(conn, query)

def insert_qb_code(conn, code, name, category_id):
    query = "INSERT INTO qb_accounts (code, name, category_id) VALUES (?, ?, ?)"
    execute_query(conn, query, (code, name, category_id))

def update_qb_code(conn, code, new_name):
    query = "UPDATE qb_accounts SET name = ? WHERE code = ?"
    execute_query(conn, query, (new_name, code))

def delete_qb_code(conn, code):
    query = "DELETE FROM qb_accounts WHERE code = ?"
    execute_query(conn, query, (code,))
