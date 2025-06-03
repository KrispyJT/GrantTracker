# --- streamlit_app.py ---
import streamlit as st
import pandas as pd
from helpers.db_utils import get_all_grants

st.set_page_config(page_title="Grant Tracker Home", page_icon="📊")
st.title("📊 Grant Tracker Dashboard")

# --- Grant Overview ---
st.header("All Grants")

grants = get_all_grants()

if not grants:
    st.warning("No grants found. Please add one in the Grants section.")
else:
    import pandas as pd
    df = pd.DataFrame(grants, columns=[
        "ID", "Grant Name", "Funder", "Start Date", "End Date", "Status", "Total Award", "Notes"
    ])
    df_display = df.drop(columns=["ID"])  # Don't show ID to users
    st.dataframe(df_display, use_container_width=True)

# --- Navigation Links ---
st.markdown("---")
st.subheader("Navigation")
st.markdown("""
- 📝 [Manage Grants](grants.py)
- 🧩 [Map Line Items & QB Codes](lineitems_maps.py)
- 💸 [Track Monthly Expenses](expenses.py) *(Coming Soon)*
""")

