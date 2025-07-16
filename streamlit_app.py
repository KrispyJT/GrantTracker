# --- streamlit_app.py ---
import streamlit as st
import pandas as pd
from helpers.db_utils import get_all_grants
from helpers.helpers import login, logout_button
import hashlib

st.set_page_config(page_title="Grant Tracker Home", page_icon="🏠")
st.title("🏠 Welcome to the Grant Tracker")

# --- LOGIN CHECK ---
# Only show login screen if not authenticated
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    login()
    st.stop()

logout_button()

# --- Intro Section ---
st.markdown("""
Welcome to the **Grant Tracker Prototype** – a lightweight app designed to help you:

- 🎯 Manage grants and funders
- 📋 Define grant-specific line items
- 🧩 Map QuickBooks (QB) account codes to grant line items
- 📊 Generate structured, auditable monthly reports

This tool is built to reduce manual Excel tracking and help you create a more scalable, consistent workflow.
""")

st.markdown("### 📂 Navigation Overview")
st.markdown("- **Grants** – Create and organize grant records")
st.markdown("- **Funders** – (Coming soon) Manage organizations funding your grants")
st.markdown("- **QuickBooks Codes** – Set up internal QB account codes")
st.markdown("- **Line Item Mapping** – Link QB codes to your grant’s line items")
st.markdown("- Monthly Planning")
st.markdown("- 🌎 [First Steps Kent](https://www.firststepskent.org/) – Program information")

# --- Grant Overview Table ---
st.markdown("---")
grants = get_all_grants()

st.markdown("### 📋 Your Grants")
if grants:
    df = pd.DataFrame(grants)
    st.dataframe(df.drop(columns=["id"]), use_container_width=True)

    grant_dict = {f"{row['name']} ({row['funder']})": row['id'] for row in grants}
else:
    st.info("No grants found. Use the sidebar to navigate to ➕ Grants and add your first one!")

# --- Quick Page Links (Optional, for dev or MVP phase only) ---
st.markdown("---")
st.markdown("### 🔗 Quick Links")
st.page_link('streamlit_app.py', label="Home", icon="🏠")
st.page_link('pages/1_Grants.py', label="Grants", icon="➕")
st.page_link('pages/_2_Funders.py', label="Funders", disabled=True)
st.page_link('pages/3_QuickBook_Codes.py', label="QB Codes")
st.page_link('pages/4_Grant_Line_Item_Mapping.py', label="Line Item Mapping", icon="🧩")
st.page_link('pages/_6_Grant_Monthly_Planning.py', label='Month Planning', disabled=True)
st.page_link('pages/5_Grant_Monthly_Expenses.py', label="💵 Actual Expenses")
st.page_link('pages/7_Grant_Summary_Dashboard.py', label="Summary Dashboard")
