# --- streamlit_app.py ---
import streamlit as st
import pandas as pd
from helpers.db_utils import get_all_grants

st.set_page_config(page_title="Grant Tracker Home", page_icon="🏠")
st.title("🏠 Welcome to the Grant Tracker")

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
    df = pd.DataFrame(grants, columns=["ID", "Grant Name", "Funder", "Start", "End", "Status", "Total Award", "Notes"])
    st.dataframe(df.drop(columns=["ID"]), use_container_width=True)
else:
    st.info("No grants found. Use the sidebar to navigate to ➕ Grants and add your first one!")

# --- Quick Page Links (Optional, for dev or MVP phase only) ---
st.markdown("---")
st.markdown("### 🔗 Quick Links")
st.page_link('streamlit_app.py', label="Home", icon="🏠")
st.page_link('pages/grants.py', label="Grants", icon="➕")
st.page_link('pages/funders.py', label="Funders", disabled=True)
st.page_link('pages/quickbooks.py', label="QB Codes")
st.page_link('pages/lineitem_maps.py', label="Line Item Mapping", icon="🧩")
st.page_link('pages/monthy_planning.py', label='Month Planning')
