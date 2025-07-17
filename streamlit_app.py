# --- streamlit_app.py ---
import pandas as pd
import streamlit as st 
from streamlit import column_config
from helpers.db_utils import get_all_grants
from helpers.ui_utils import build_grant_summary_table, inject_sidebar_css
from helpers.helpers import login, render_sidebar_navigation

st.set_page_config(page_title="Grant Tracker Home", page_icon="🏠", layout="wide", initial_sidebar_state="auto")

# --- LOGIN CHECK ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    login()
    st.stop()

inject_sidebar_css()
render_sidebar_navigation()

# ========================
# 👋 Intro Section
# ========================
st.markdown("# Grant Tracker Dashboard")
with st.expander("ℹ️ What is this?"):
    st.info("**The Grant Tracker Prototype** is a lightweight internal tool to simplify your grant workflow.")

    st.markdown("""
    ### ✨ Key Purposes:
    - **Manage** grants, line items, and funders in one place  
    -   **Map** QuickBooks codes to your line items  
    - **Track** monthly expenses and visualize progress  
    """)

    st.markdown("### Core Features:")
    st.markdown("""
    - 📑 **Grants** – Create and organize grant records  
    - 🧑‍💼 **Funders** – _(Coming soon?)_ Manage your grant funding sources  
    - 💼 **QuickBooks Codes** – Set up internal QB chart of accounts  
    - 🧩 **Line Item Mapping** – Link QB codes to each grant’s line items  
    - 💵 **Monthly Expenses** – Track actuals and reconcile with accounting  
    - 📆 **Monthly Planning** – _(Coming soon?)_ Allocate monthly expected spending by line item  
    - 🔗 **Visit** [First Steps Kent](https://www.firststepskent.org/) for more program information.
    """)

# ========================
# 📂 Load + Process Grants
# ========================
grants = get_all_grants()
if not grants:
    st.warning("No grants available. Use the ➕ Grants page to add one.")
    st.stop()

summary_df = build_grant_summary_table(grants)


# Column configuration for all grant overview tables
grant_column_config = {
    "Start": column_config.DateColumn("Start Date", format="MM/DD/YYYY"),
    "End": column_config.DateColumn("End Date", format="MM/DD/YYYY"),
    "Total Award": column_config.NumberColumn("Total Award", format="$%d"),
    "Allocated": column_config.NumberColumn("Allocated", format="$%d"),
    "Spent": column_config.NumberColumn("Spent", format="$%d"),
    "Remaining": column_config.NumberColumn("Remaining", format="$%d"),
    "% Spent": column_config.NumberColumn("% Spent", format="%.1f%%"),
    "Status": column_config.TextColumn("Status"),
}





# ----------------------------
# 📊 Portfolio Summary + Filtered Table
# ----------------------------
st.markdown("### 📊 Portfolio Summary")

# Unique statuses (e.g., Active, Closed)
statuses = summary_df["Status"].unique().tolist()
tab_all, *tabs_by_status = st.tabs(["📊 All Grants"] + [f"🔎 {s} Grants" for s in statuses])

with tab_all:
    filtered_df = summary_df  # All grants
    column_order = ["Grant", "Total Award", "Allocated", "Spent", "Remaining", "% Spent", "Status", "Funder"]
    filtered_df = filtered_df[column_order]


    # Shrink metrics using columns + custom CSS
    st.markdown("<div class='metric-row'>", unsafe_allow_html=True)
    cols = st.columns(5)
    cols[0].metric("Total Grants", len(filtered_df))
    cols[1].metric("Total Awarded", f"${filtered_df['Total Award'].sum():,.0f}")
    cols[2].metric("Allocated", f"${filtered_df['Allocated'].sum():,.0f}")
    cols[3].metric("Spent", f"${filtered_df['Spent'].sum():,.0f}")
    pct = round(filtered_df['Spent'].sum() / filtered_df['Allocated'].sum() * 100, 1) if filtered_df['Allocated'].sum() else 0
    cols[4].metric("% Spent", f"{pct}%")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 📋 Grant-Level Overview")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True, column_config=grant_column_config)
    # st.dataframe(filtered_df, use_container_width=True, hide_index=True)

for i, status in enumerate(statuses):
    with tabs_by_status[i]:
        filtered_df = summary_df[summary_df["Status"] == status]

        st.markdown("<div class='metric-row'>", unsafe_allow_html=True)
        cols = st.columns(5)
        cols[0].metric("Grants", len(filtered_df))
        cols[1].metric("Awarded", f"${filtered_df['Total Award'].sum():,.0f}")
        cols[2].metric("Allocated", f"${filtered_df['Allocated'].sum():,.0f}")
        cols[3].metric("Spent", f"${filtered_df['Spent'].sum():,.0f}")
        pct = round(filtered_df['Spent'].sum() / filtered_df['Allocated'].sum() * 100, 1) if filtered_df['Allocated'].sum() else 0
        cols[4].metric("% Spent", f"{pct}%")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"### 📋 {status} Grant Overview")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True, column_config=grant_column_config)
        # st.dataframe(filtered_df, use_container_width=True, hide_index=True)



# import streamlit as st
# from streamlit import column_config

# st.markdown("### 📄 Grant-Level Overview")

# st.dataframe(
#     summary_df,
#     use_container_width=True,
#     column_config={
#         "Start": column_config.DateColumn("Start Date", format="MM/DD/YYYY"),
#         "End": column_config.DateColumn("End Date", format="MM/DD/YYYY"),
#         "Total Award": column_config.NumberColumn("Total Award", format="$%d"),
#         "Allocated": column_config.NumberColumn("Allocated", format="$%d"),
#         "Spent": column_config.NumberColumn("Spent", format="$%d"),
#         "Remaining": column_config.NumberColumn("Remaining", format="$%d"),
#         "% Spent": column_config.NumberColumn("% Spent", format="%.1f%%"),
#         "Status": column_config.TextColumn("Grant Status"),
#     }
# )


################################

# # ========================
# # 📋 Grant-Level Table
# # ========================
# st.markdown("## 📋 Grant-Level Overview")
# st.dataframe(
#     summary_df[["Grant", "Funder", "Start", "End", "Total Award", "Allocated", "Spent", "% Spent", "Remaining", "Status"]],
#     use_container_width=True,
#     hide_index=True
# )



# st.markdown("### 📊 Portfolio Summary")

# # Get unique statuses (e.g. Active, Closed, Pending)
# statuses = summary_df["Status"].unique().tolist()

# tab_all, *tabs_by_status = st.tabs(["📊 All Grants"] + [f"🔎 {s} Grants" for s in statuses])

# # --- ALL GRANTS TAB ---
# with tab_all:
#     cols = st.columns(5)
#     cols[0].metric("Total Grants", len(summary_df), border=True)
#     cols[1].metric("Total Awarded", f"${summary_df['Total Award'].sum():,.0f}", border=True)
#     cols[2].metric("Allocated", f"${summary_df['Allocated'].sum():,.0f}", border=True)
#     cols[3].metric("Spent", f"${summary_df['Spent'].sum():,.0f}", border=True)
#     overall_pct = round(summary_df['Spent'].sum() / summary_df['Allocated'].sum() * 100, 1) if summary_df['Allocated'].sum() else 0
#     cols[4].metric("% Spent", f"{overall_pct}%", border=True)

# # --- PER STATUS TABS ---
# for i, status in enumerate(statuses):
#     with tabs_by_status[i]:
#         filtered = summary_df[summary_df["Status"] == status]
#         cols = st.columns(5)
#         cols[0].metric("Grants", len(filtered))
#         cols[1].metric("Awarded", f"${filtered['Total Award'].sum():,.0f}")
#         cols[2].metric("Allocated", f"${filtered['Allocated'].sum():,.0f}")
#         cols[3].metric("Spent", f"${filtered['Spent'].sum():,.0f}")
#         pct = round(filtered['Spent'].sum() / filtered['Allocated'].sum() * 100, 1) if filtered['Allocated'].sum() else 0
#         cols[4].metric("% Spent", f"{pct}%")

















# # --- streamlit_app.py ---
# import streamlit as st
# import pandas as pd
# from helpers.db_utils import get_all_grants
# from helpers.helpers import login, logout_button

# st.set_page_config(page_title="Grant Tracker Home", page_icon="🏠")
# st.title("🏠 Welcome to the Grant Tracker")

# # --- LOGIN CHECK ---
# if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
#     login()
#     st.stop()

# logout_button()

# # --- Intro Section ---
# st.markdown("""
# Welcome to the **Grant Tracker Prototype** – a lightweight app designed to help you:

# - 🎯 Manage grants and funders
# - 📋 Define grant-specific line items
# - 🧩 Map QuickBooks (QB) account codes to grant line items
# - 📊 Generate structured, auditable monthly reports

# This tool is built to reduce manual Excel tracking and help you create a more scalable, consistent workflow.
# """)

# st.markdown("### 📂 Navigation Overview")
# st.markdown("- **Grants** – Create and organize grant records")
# st.markdown("- **Funders** – (Coming soon) Manage organizations funding your grants")
# st.markdown("- **QuickBooks Codes** – Set up internal QB account codes")
# st.markdown("- **Line Item Mapping** – Link QB codes to your grant’s line items")
# st.markdown("- Monthly Planning")
# st.markdown("- 🌎 [First Steps Kent](https://www.firststepskent.org/) – Program information")

# # --- Grant Overview Table ---
# st.markdown("---")
# grants = get_all_grants()

# st.markdown("### 📋 Your Grants")
# if grants:
#     df = pd.DataFrame(grants)
#     st.dataframe(df.drop(columns=["id"]), use_container_width=True)

#     grant_dict = {f"{row['name']} ({row['funder']})": row['id'] for row in grants}
# else:
#     st.info("No grants found. Use the sidebar to navigate to ➕ Grants and add your first one!")

# # --- Quick Page Links (Optional, for dev or MVP phase only) ---
# st.markdown("---")
# st.markdown("### 🔗 Quick Links")
# st.page_link('streamlit_app.py', label="Home", icon="🏠")
# st.page_link('pages/1_Grants.py', label="Grants", icon="➕")
# st.page_link('pages/_2_Funders.py', label="Funders", disabled=True)
# st.page_link('pages/3_QuickBook_Codes.py', label="QB Codes", icon="💼")
# st.page_link('pages/4_Grant_Line_Item_Mapping.py', label="Line Item Mapping", icon="🧩")
# st.page_link('pages/_6_Grant_Monthly_Planning.py', label='Month Planning', disabled=True)
# st.page_link('pages/5_Grant_Monthly_Expenses.py', label="Monthly Expenses", icon="💵")
# st.page_link('pages/7_Grant_Summary_Dashboard.py', label="Summary", icon="📊")


