# helpers/helpers.py

from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit as st
import hashlib


# ---- Date Utils

def generate_month_range(start_date, end_date):
    """
    Returns a list of 'YYYY-MM' strings between two dates, inclusive.
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    months = []
    current = start_date
    while current <= end_date:
        months.append(current.strftime("%Y-%m"))
        current += relativedelta(months=1)
    return months



def validate_date_range(start_date, end_date):
    if isinstance(start_date, str): start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str): end_date = datetime.strptime(end_date, "%Y-%m-%d")
    if end_date < start_date:
        raise ValueError("End date must be after start date.")

# Financial Utilities

def distribute_amount_evenly(allocated_amount: float, months: list[str]) -> dict[str, float]:
    """Evenly distribute the allocated amount across the months without exceeding it."""
    monthly_base = round(allocated_amount / len(months), 2)
    distribution = {month: monthly_base for month in months}

    # Calculate how much was actually distributed
    total_distributed = round(monthly_base * len(months), 2)
    remainder = round(allocated_amount - total_distributed, 2)

    # Add the remainder to the final month to match total
    if remainder != 0:
        last_month = months[-1]
        distribution[last_month] = round(distribution[last_month] + remainder, 2)

    return distribution

# ----- String Utilities -----
def normalize_string(value, title_case=True):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    value = value.strip()
    return value.title() if title_case else value



def render_filter_sidebar(df):
    with st.sidebar:
        st.subheader("🔦 Filter Line Items")

        # 🎯 Create selectboxes with keys to enable clearing via session_state
        filter_li = st.selectbox(
            "Filter by Line Item",
            ["All"] + sorted(df["Line Item"].unique()),
            key="line_item_filter"
        )

        filter_qb_code = st.selectbox(
            "Filter by QB Code",
            ["All"] + sorted(map(str, df["QB Code"].unique())),
            key="qb_code_filter"
        )

        filter_qb_name = st.selectbox(
            "Filter by QB Name",
            ["All"] + sorted(df["QB Name"].unique()),
            key="qb_name_filter"
        )

        # 🧹 Clear filters button
        if st.button("🔄 Clear Filters"):
            st.session_state.pop("line_item_filter", None)
            st.session_state.pop("qb_code_filter", None)
            st.session_state.pop("qb_name_filter", None)
            st.rerun()

    return filter_li, filter_qb_code, filter_qb_name



def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login():
    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        hashed_pw_input = hash_password(password)
        stored_pw = st.secrets["auth"].get(username)

        if stored_pw and stored_pw == hashed_pw_input:
            st.session_state["authenticated"] = True
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("❌ Invalid credentials")

def logout_button():
    with st.sidebar:
        st.markdown("##")
        st.markdown(f"👤 `{st.session_state.get('user', 'Unknown')}`")
        if st.button("🚪 Log Out"):
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.rerun()