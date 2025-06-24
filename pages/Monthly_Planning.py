import streamlit as st
import pandas as pd
from helpers.db_utils import (
    get_all_grants,
    get_line_items_by_grant,
    get_anticipated_expenses_for_grant,
    update_anticipated_expense,
    initialize_anticipated_expenses
)
from helpers.date_helpers import generate_month_range

st.set_page_config(page_title="📆 Monthly Planning", page_icon="📆")
st.title("📆 Monthly Expense Planning")

st.markdown("""
This page allows you to plan **anticipated monthly expenses** for each line item in a grant.
You can review allocations, edit expected monthly amounts, and ensure your budget is distributed across the grant period.
""")

# ----------------------------------
# 🎯 Select a Grant
# ----------------------------------
grants = get_all_grants()
grant_options = {f"{g[1]} ({g[2]})": g[0] for g in grants}
selected_label = st.selectbox("Select a Grant", list(grant_options.keys()))
selected_grant_id = grant_options[selected_label]
selected_grant = next(g for g in grants if g[0] == selected_grant_id)

start_date, end_date = selected_grant[3], selected_grant[4]
months = generate_month_range(start_date, end_date)



# Get line items for the selected grant
line_items = get_line_items_by_grant(selected_grant_id)

# Initialize anticipated expenses for each line item
for li in line_items:
    li_id = li[0]
    initialize_anticipated_expenses(
        grant_id=selected_grant_id,
        line_item_id=li_id,
        start_date=selected_grant[3],  # start_date from grant
        end_date=selected_grant[4]     # end_date from grant
    )


# ----------------------------------
# 📋 Load Anticipated Expenses
# ----------------------------------
line_items = get_line_items_by_grant(selected_grant_id)
anticipated_raw = get_anticipated_expenses_for_grant(selected_grant_id)

if not anticipated_raw:
    st.warning("⚠️ No anticipated expenses found. Please initialize them first.")
    st.stop()

# Create DataFrame
anticipated_df = pd.DataFrame(anticipated_raw, columns=["Month", "Expected Amount", "Line Item ID"])
li_map = {li[0]: li[1] for li in line_items}  # ID to Name
anticipated_df["Line Item"] = anticipated_df["Line Item ID"].map(li_map)

# Pivot for display
pivot_df = anticipated_df.pivot_table(index="Line Item", columns="Month", values="Expected Amount", fill_value=0.0)
pivot_df = pivot_df[[m for m in months if m in pivot_df.columns]]  # Ensure proper order

st.data_editor(pivot_df, use_container_width=True, key="forecast_editor")

if st.button("💾 Save Forecast Changes"):
    updated_df = st.session_state.forecast_editor
    updates_made = 0
    for line_item_name, row in updated_df.iterrows():
        line_item_id = next((li[0] for li in line_items if li[1] == line_item_name), None)
        for month, val in row.items():
            update_anticipated_expense(selected_grant_id, line_item_id, month, float(val))
            updates_made += 1
    st.success(f"✅ {updates_made} monthly values updated.")
