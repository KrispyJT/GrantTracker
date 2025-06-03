import streamlit as st
import pandas as pd
from helpers.db_utils import (
    get_all_grants,
    get_line_items_by_grant,
    add_line_item,
    delete_line_item,
    get_filtered_qb_codes,
    get_mappings_for_grant,
    add_qb_mapping,
    delete_qb_mapping
)

st.set_page_config(page_title="Line Item Mapping", page_icon="🧩")
st.title("🧩 Map QB Codes to Grant Line Items")

# ----------------------------------
# 1. Select Grant
# ----------------------------------
grants = get_all_grants()
grant_options = {f"{g[1]} ({g[2]})": g[0] for g in grants}  # g[1]=name, g[2]=funder, g[0]=id

selected_label = st.selectbox("Select a Grant", options=list(grant_options.keys()))
selected_grant_id = grant_options[selected_label]

# ----------------------------------
# 2. View/Add/Delete Grant Line Items
# ----------------------------------
st.subheader("📋 Grant Line Items")
line_items = get_line_items_by_grant(selected_grant_id)

if line_items:
    df_line_items = pd.DataFrame(line_items, columns=["ID", "Name", "Description"])
    st.dataframe(df_line_items.drop(columns=["ID"]), use_container_width=True)

    with st.expander("➖ Delete Line Item"):
        item_to_delete = st.selectbox("Choose Line Item to Delete", options=df_line_items["Name"].tolist())
        if st.button("Confirm Deletion"):
            line_item_id = df_line_items[df_line_items["Name"] == item_to_delete]["ID"].values[0]
            delete_line_item(line_item_id)
            st.success("✅ Line item deleted.")
            st.rerun()
else:
    st.info("ℹ️ No line items yet for this grant.")

# Add line item form
with st.form("add_line_item"):
    st.markdown("### ➕ Add New Line Item")
    new_name = st.text_input("Line Item Name").strip()
    new_desc = st.text_area("Description (optional)").strip()
    submitted = st.form_submit_button("Add Line Item")
    if submitted:
        if new_name:
            add_line_item(selected_grant_id, new_name, new_desc)
            st.success(f"✅ Added line item '{new_name}'")
            st.rerun()
        else:
            st.warning("⚠️ Line Item name is required.")

# ----------------------------------
# 3. Map QB Codes to Line Items
# ----------------------------------
st.markdown("---")
st.subheader("🔗 Map QuickBooks Code to a Line Item")

qb_data = get_filtered_qb_codes("All", "All")
lineitem_options = [li[1] for li in line_items]  # li[1] = line item name

with st.form("map_qb_code_form"):
    qb_code_label = st.selectbox("QB Code", [f"{r['code']} – {r['name']}" for _, r in qb_data.iterrows()])
    selected_li = st.selectbox("Grant Line Item", options=lineitem_options)
    if st.form_submit_button("Map Code"):
        code = qb_code_label.split("–")[0].strip()
        line_item_id = next((li[0] for li in line_items if li[1] == selected_li), None)
        add_qb_mapping(selected_grant_id, code, line_item_id)
        st.success(f"✅ Mapped QB Code {code} to '{selected_li}'")
        st.rerun()

# ----------------------------------
# 4. View/Delete Existing Mappings
# ----------------------------------
st.markdown("---")
st.subheader("📎 Existing QB Mappings")

mappings = get_mappings_for_grant(selected_grant_id)
if mappings:
    df_map = pd.DataFrame(mappings, columns=["ID", "QB Code", "QB Name", "Line Item"])
    st.dataframe(df_map.drop(columns=["ID"]), use_container_width=True)

    with st.expander("🗑️ Remove Mapping"):
        to_remove = st.selectbox("Select QB Code to Remove", df_map["QB Code"].tolist())
        if st.button("Remove Mapping"):
            mapping_id = df_map[df_map["QB Code"] == to_remove]["ID"].values[0]
            delete_qb_mapping(mapping_id)
            st.success("🧹 Mapping removed.")
            st.rerun()
else:
    st.info("ℹ️ No mappings found.")
