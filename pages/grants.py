# --- grants.py (Streamlit Page) ---
import streamlit as st
import pandas as pd
from datetime import date
from helpers.db_utils import (
    get_all_grants,
    add_funder_if_not_exists,
    add_grant,
    get_funder_id,
    update_grant,
    delete_grant
)

st.set_page_config(page_title="Grants", page_icon="📈")
st.title("🌟 Grant Mapping Tool")

# -------------------
# Add New Grant
# -------------------
st.header("➕ Add a New Grant")
with st.form("grant_form"):
    grant_name = st.text_input("Grant Name").strip()
    funder_name = st.text_input("Funder Name").strip()
    funder_type = st.selectbox("Funder Type", ["Private", "Federal", "State", "Other"])
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())
    total_award = st.text_input("Award Amount").strip()
    status = st.selectbox("Status", ["Pending", "Active", "Closed"])
    notes = st.text_area("Additional Notes").strip()

    submitted = st.form_submit_button("Add Grant")

if submitted:
    if not grant_name or not funder_name:
        st.warning("⚠️ Please fill out required fields.")
    else:
        funder_id = add_funder_if_not_exists(funder_name, funder_type)
        success = add_grant(grant_name, funder_id, start_date, end_date, status, notes)
        if success:
            st.success(f"✅ Grant '{grant_name}' added!")
            st.rerun()
        else:
            st.error("❌ Grant name already exists.")

# -------------------
# Show Existing Grants
# -------------------
st.header("📋 Existing Grants")
grants = get_all_grants()

if grants:
    df = pd.DataFrame(grants, columns=["ID", "Grant Name", "Funder", "Start", "End", "Status"])
    st.dataframe(df, use_container_width=True)

    st.subheader("✏️ Edit/Delete a Grant")
    selected = st.selectbox("Select a Grant to Edit/Delete", options=df["Grant Name"].tolist())
    row = df[df["Grant Name"] == selected].iloc[0]

    with st.form("edit_grant"):
        new_name = st.text_input("Grant Name", value=row["Grant Name"]).strip()
        new_funder = st.text_input("Funder Name", value=row["Funder"]).strip()
        new_start = st.date_input("Start Date", value=pd.to_datetime(row["Start"]).date())
        new_end = st.date_input("End Date", value=pd.to_datetime(row["End"]).date())
        new_status = st.selectbox("Status", ["Pending", "Active", "Closed"], index=["Pending", "Active", "Closed"].index(row["Status"]))
        new_notes = st.text_area("Additional Notes").strip()

        col1, col2 = st.columns(2)
        if col1.form_submit_button("Update Grant"):
            funder_id = add_funder_if_not_exists(new_funder, "Private")
            update_grant(row["ID"], new_name, funder_id, new_start, new_end, new_status, new_notes)
            st.success("Grant updated.")
            st.rerun()

        if col2.form_submit_button("❌ Delete Grant"):
            delete_grant(row["ID"])
            st.warning("Grant deleted.")
            st.rerun()
else:
    st.info("No grants found.")