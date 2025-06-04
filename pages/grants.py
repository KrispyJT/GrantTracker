import streamlit as st
import pandas as pd
from datetime import date
from helpers.db_utils import (
    get_all_grants,
    add_funder_if_missing,
    get_funder_id,
    add_grant,
    update_grant,
    delete_grant
)

st.set_page_config(page_title="Grants", page_icon="📈")
st.title("🌟 Grant Mapping Tool")

# ----------------------------
# Show session status messages
# ----------------------------
if st.session_state.get("grant_added"):
    st.success("✅ Grant added.")
    st.session_state["grant_added"] = False
    st.rerun()

if st.session_state.get("grant_updated"):
    st.success("✅ Grant updated.")
    st.session_state["grant_updated"] = False
    st.rerun()

if st.session_state.get("grant_deleted"):
    st.warning("🗑️ Grant deleted.")
    st.session_state["grant_deleted"] = False
    st.rerun()

# -------------------
# Add New Grant
# -------------------
with st.expander("➕ Add a New Grant", expanded=False):
    with st.form("grant_form"):
        grant_name = st.text_input("Grant Name").strip()
        funder_name = st.text_input("Funder Name").strip()
        funder_type = st.selectbox("Funder Type", ["Private", "Federal", "State", "Other"])
        start_date = st.date_input("Start Date (MM/DD/YYYY)", value=date.today())
        end_date = st.date_input("End Date (MM/DD/YYYY)", value=date.today())

        try:
            total_award = st.number_input(
                "Award Amount",
                value=None,
                step=0.01,
                format="%.2f",
                placeholder="Enter award (e.g., 15000)"
            )
        except TypeError:
            award_input = st.text_input("Award Amount (e.g., 15000)")
            try:
                total_award = float(award_input) if award_input else None
            except ValueError:
                total_award = None

        status = st.selectbox("Status", ["Pending", "Active", "Closed"])
        notes = st.text_area("Additional Notes").strip()

        submitted = st.form_submit_button("Add Grant")

    if submitted:
        if not grant_name or not funder_name or total_award is None:
            st.warning("⚠️ Please fill out all required fields correctly.")
        else:
            try:
                add_funder_if_missing(funder_name, funder_type)
                funder_id = get_funder_id(funder_name)
                add_grant(grant_name, funder_id, start_date, end_date, total_award, status, notes)
                st.session_state["grant_added"] = True
                st.rerun()
            except Exception as e:
                if "UNIQUE constraint failed: grants.name" in str(e):
                    st.error(f"❌ A grant named '{grant_name}' already exists. Please choose a unique name.")
                else:
                    st.error(f"❌ Failed to add grant: {e}")

# -------------------
# Edit/Delete a Grant
# -------------------
with st.expander("✏️ Edit or Delete a Grant", expanded=False):
    grants = get_all_grants()
    if grants:
        df = pd.DataFrame(grants, columns=["ID", "Grant Name", "Funder", "Start", "End", "Status", "Total Award", "Notes"])
        selected = st.selectbox("Select a Grant to Edit/Delete", options=df["Grant Name"].tolist())
        row = df[df["Grant Name"] == selected].iloc[0]

        with st.form("edit_grant"):
            new_name = st.text_input("Grant Name", value=row["Grant Name"]).strip()
            new_funder = st.text_input("Funder Name", value=row["Funder"]).strip()
            new_funder_type = st.selectbox("Funder Type", ["Private", "Federal", "State", "Other"])
            new_start = st.date_input("Start Date (MM/DD/YYYY)", value=pd.to_datetime(row["Start"]).date())
            new_end = st.date_input("End Date (MM/DD/YYYY)", value=pd.to_datetime(row["End"]).date())

            try:
                new_award = st.number_input(
                    "Total Award",
                    value=float(row["Total Award"]) if row["Total Award"] else None,
                    step=0.01,
                    format="%.2f"
                )
            except TypeError:
                new_award_input = st.text_input("Total Award (e.g., 15000)", value=str(row["Total Award"] or ""))
                try:
                    new_award = float(new_award_input) if new_award_input else None
                except ValueError:
                    new_award = None

            new_status = st.selectbox("Status", ["Pending", "Active", "Closed"],
                                      index=["Pending", "Active", "Closed"].index(row["Status"]))
            new_notes = st.text_area("Additional Notes", value=row["Notes"] or "").strip()

            col1, col2 = st.columns(2)
            if col1.form_submit_button("Update Grant"):
                if new_award is None:
                    st.warning("❗ Please enter a valid award amount.")
                else:
                    add_funder_if_missing(new_funder, new_funder_type)
                    funder_id = get_funder_id(new_funder)
                    update_grant(row["ID"], new_name, funder_id, new_start, new_end, new_award, new_status, new_notes)
                    st.session_state["grant_updated"] = True
                    st.rerun()

            if col2.form_submit_button("❌ Delete Grant"):
                delete_grant(row["ID"])
                st.session_state["grant_deleted"] = True
                st.rerun()
    else:
        st.info("No grants available to edit or delete.")

# -------------------
# Display All Grants
# -------------------
st.header("📋 All Grants")
grants = get_all_grants()
if grants:
    df = pd.DataFrame(grants, columns=["ID", "Grant Name", "Funder", "Start", "End", "Status", "Total Award", "Notes"])
    df["Total Award"] = df["Total Award"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
    st.dataframe(df.drop(columns=["ID"]), use_container_width=True)
else:
    st.info("No grants found.")
