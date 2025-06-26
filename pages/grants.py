# pages/grants.py
import streamlit as st
from datetime import date
from helpers.db_utils import get_all_grants
from helpers.grant_controller import (
    handle_add_grant,
    handle_update_grant,
    handle_delete_grant,
)

st.set_page_config(page_title="Grant Management", page_icon="📑")
st.title("📑 Grant Management")

st.markdown("Manage grants and related information below. Add new grants, edit existing ones, or delete obsolete entries.")

# Fetch all grants and build dropdown dictionary
grants = get_all_grants()
grant_dict = {f"{g['name']} ({g['funder']})": g['id'] for g in grants}

# -------------------
# ➕ Add New Grant
# -------------------
st.markdown("### ➕ Add New Grant")
with st.expander("Add a new grant entry"):
    with st.form("add_grant_form"):
        new_grant_name = st.text_input("Grant Name")
        new_funder_name = st.text_input("Funder Name")
        new_funder_type = st.selectbox("Funder Type", ["Government", "Foundation", "Corporate", "Other"])
        col1, col2 = st.columns(2)
        new_start_date = col1.date_input("Start Date", value=date.today())
        new_end_date = col2.date_input("End Date")
        new_total_award = st.number_input("Total Award ($)", step=1000.0, min_value=0.0)
        new_status = st.selectbox("Status", ["Active", "Closed", "Pending"])
        new_notes = st.text_area("Notes (Optional)")
        if st.form_submit_button("Add Grant"):
            try:
                handle_add_grant(
                    new_grant_name,
                    new_funder_name,
                    new_funder_type,
                    new_start_date,
                    new_end_date,
                    new_total_award,
                    new_status,
                    new_notes,
                )
                st.success("✅ Grant added successfully.")
                st.rerun()
            except ValueError as ve:
                st.error(f"⚠️ {ve}")

# -------------------
# ✏️ Edit/Delete Grant
# -------------------
st.markdown("### ✏️ Edit or Delete Grant")
if grants:
    selected_label = st.selectbox("Select Grant to Edit/Delete", list(grant_dict.keys()))
    selected_grant_id = grant_dict[selected_label]
    selected_row = next((row for row in grants if row["id"] == selected_grant_id), None)

    if selected_row:
        existing_name = selected_row["name"]
        existing_funder = selected_row["funder"]
        existing_start = selected_row["start_date"]
        existing_end = selected_row["end_date"]
        existing_status = selected_row["status"]
        existing_award = selected_row["total_award"]
        existing_notes = selected_row.get("notes", "")

        with st.expander("Edit/Delete Selected Grant"):
            with st.form("edit_grant_form"):
                edited_grant_name = st.text_input("Grant Name", value=existing_name)
                edited_funder_name = st.text_input("Funder Name", value=existing_funder)
                edited_funder_type = st.selectbox("Funder Type", ["Government", "Foundation", "Corporate", "Other"])
                col1, col2 = st.columns(2)
                edited_start_date = col1.date_input("Start Date", value=existing_start)
                edited_end_date = col2.date_input("End Date", value=existing_end)
                edited_total_award = st.number_input("Total Award ($)", value=existing_award or 0.0, step=1000.0)
                edited_status = st.selectbox("Status", ["Active", "Closed", "Pending"], index=["Active", "Closed", "Pending"].index(existing_status))
                edited_notes = st.text_area("Notes", value=existing_notes)
                col1, col2 = st.columns(2)

                if col1.form_submit_button("Update Grant"):
                    handle_update_grant(
                        selected_grant_id,
                        edited_grant_name,
                        edited_funder_name,
                        edited_funder_type,
                        edited_start_date,
                        edited_end_date,
                        edited_total_award,
                        edited_status,
                        edited_notes,
                    )
                    st.success("✅ Grant updated successfully.")
                    st.rerun()

                if col2.form_submit_button("❌ Delete Grant"):
                    handle_delete_grant(selected_grant_id)
                    st.warning("⚠️ Grant deleted.")
                    st.rerun()
else:
    st.info("No grants available yet. Please add one above.")

# -------------------
# 📋 Display All Grants
# -------------------
st.markdown("### 📋 All Grants")
if grants:
    st.dataframe(
        {
            "Name": [g["name"] for g in grants],
            "Funder": [g["funder"] for g in grants],
            "Start Date": [g["start_date"] for g in grants],
            "End Date": [g["end_date"] for g in grants],
            "Status": [g["status"] for g in grants],
            "Total Award": [g["total_award"] for g in grants],
            "Notes": [g.get("notes", "") for g in grants],
        },
        use_container_width=True,
    )
else:
    st.info("No grants to show.")
