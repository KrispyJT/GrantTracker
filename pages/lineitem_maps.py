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
    delete_qb_mapping,
    update_line_item_allocated
)


st.set_page_config(page_title="Line Item Mapping", page_icon="🧩")
st.title("🧩 Map QB Codes to Grant Line Items")

# ----------------------------------
# 1. Select Grant
# ----------------------------------
grants = get_all_grants()
grant_options = {f"{g[1]} ({g[2]})": g[0] for g in grants}
selected_label = st.selectbox("🎯 Select a Grant", list(grant_options.keys()))
selected_grant_id = grant_options[selected_label]

# Optional Grant Info Display
selected_grant = next(g for g in grants if g[0] == selected_grant_id)
with st.expander("📄 Grant Overview", expanded=False):
    st.markdown(f"**Grant Name:** {selected_grant[1]}")
    st.markdown(f"**Funder:** {selected_grant[2]}")
    st.markdown(f"**Status** {selected_grant[5]}")
    st.markdown(f"**Total Award Amount:** ${selected_grant[6]:,.2f}")
    st.markdown(f"**Start Date:** {selected_grant[3]} **End Date:** {selected_grant[4]}")
    if selected_grant[7]:
        st.info(f"**Notes:** {selected_grant[7]}")


# ----------------------------------
# 2. Manage Line Items
# ----------------------------------
st.divider()
st.header("📋 Manage Line Items")

line_items = get_line_items_by_grant(selected_grant_id)

with st.expander("➕ Add New Line Item"):
    with st.form("add_line_item_form"):
        name = st.text_input("Name").strip()
        desc = st.text_area("Description").strip()
        alloc = st.number_input("Allocated Amount ($)", min_value=0.0, step=100.0)
        if st.form_submit_button("Add Line Item"):
            if name:
                add_line_item(selected_grant_id, name, desc, alloc)
                st.success(f"✅ '{name}' added.")
                st.rerun()
            else:
                st.warning("Name is required.")

if line_items:
    df = pd.DataFrame(line_items, columns=["ID", "Name", "Description", "Allocated"])
    with st.expander("📝 Edit or Delete Line Items"):
        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"#### ✏️ {row['Name']} (${row['Allocated']:,.2f})")
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Edit Name", value=row["Name"], key=f"name_{row['ID']}")
                    new_desc = st.text_area("Edit Description", value=row["Description"], key=f"desc_{row['ID']}")
                    new_amt = st.number_input("Allocated $", value=float(row["Allocated"]), key=f"alloc_{row['ID']}")
                    if st.button("Save Changes", key=f"save_{row['ID']}"):
                        update_line_item_allocated(row["ID"], new_amt)
                        st.success("Updated.")
                        st.rerun()
                with col2:
                    if st.button("❌ Delete", key=f"del_{row['ID']}"):
                        delete_line_item(row["ID"])
                        st.warning(f"Deleted {row['Name']}")
                        st.rerun()
else:
    st.info("ℹ️ No line items for this grant.")

# ----------------------------------
# 3. Map QB Codes to Line Items
# ----------------------------------
st.divider()
st.header("🔗 Map QB Codes")

qb_data = get_filtered_qb_codes("All", "All")
lineitem_labels = {li[1]: li[0] for li in line_items}

with st.form("map_qb_form"):
    li_name = st.selectbox("Line Item", options=list(lineitem_labels.keys()))
    qb_choice = st.selectbox("QB Code", [f"{r['code']} – {r['name']}" for _, r in qb_data.iterrows()])
    if st.form_submit_button("Map Code"):
        li_id = lineitem_labels[li_name]
        code = qb_choice.split("–")[0].strip()
        add_qb_mapping(selected_grant_id, code, li_id)
        st.success(f"✅ Mapped {code} to '{li_name}'")
        st.rerun()

# ----------------------------------
# 4. View & Delete Mappings
# ----------------------------------


st.divider()
st.header("📎 Existing Mappings")

mappings = get_mappings_for_grant(selected_grant_id)
if mappings:
    df_map = pd.DataFrame(mappings, columns=["ID", "QB Code", "QB Name", "Line Item"])

    # 🧮 Mapping Tracker
    mapped_ids = df_map["Line Item"].unique().tolist()
    total_items = len(line_items)
    mapped_count = len(mapped_ids)
    unmapped_count = total_items - mapped_count

    if total_items == 0:
        st.warning("⚠️ No line items created for this grant.")
    elif mapped_count == total_items:
        st.success(f"✅ All {total_items} line items have been mapped.")
    else:
        st.info(f"🔄 {mapped_count} of {total_items} line items mapped. {unmapped_count} remaining.")

        # 🚫 Show which ones are still unmapped
        unmapped_names = [li[1] for li in line_items if li[1] not in mapped_ids]
        if unmapped_names:
            st.warning("🚫 The following line items are not yet mapped:")
            for name in unmapped_names:
                st.markdown(f"- {name}")

    # 📦 Group mappings by line item
    grouped = df_map.groupby("Line Item")
    for li, group in grouped:
        with st.expander(f"🧾 {li}", expanded=False):
            for _, row in group.iterrows():
                st.markdown(f"• `{row['QB Code']}` – {row['QB Name']}")
                if st.button("🗑️ Remove", key=f"rm_{row['ID']}"):
                    delete_qb_mapping(row["ID"])
                    st.success("Mapping removed.")
                    st.rerun()
else:
    st.info("ℹ️ No QuickBooks codes have been mapped to any line items yet. Use the form above to begin.")



# st.divider()
# st.header("📎 Existing Mappings")

# mappings = get_mappings_for_grant(selected_grant_id)

# if mappings:
#     df_map = pd.DataFrame(mappings, columns=["ID", "QB Code", "QB Name", "Line Item"])

#     # 🧮 Mapping Tracker
#     mapped_ids = df_map["Line Item"].unique().tolist()
#     total_items = len(line_items)
#     mapped_count = len(mapped_ids)
#     unmapped_count = total_items - mapped_count

#     if total_items == 0:
#         st.warning("⚠️ No line items created for this grant.")
#     elif mapped_count == total_items:
#         st.success(f"✅ All {total_items} line items have been mapped.")
#     else:
#         st.info(f"🔄 {mapped_count} of {total_items} line items mapped. {unmapped_count} remaining.")

#     # 📦 Group mappings by line item
#     grouped = df_map.groupby("Line Item")
#     for li, group in grouped:
#         with st.expander(f"🧾 {li}", expanded=False):
#             for _, row in group.iterrows():
#                 st.markdown(f"• `{row['QB Code']}` – {row['QB Name']}")
#                 if st.button("🗑️ Remove", key=f"rm_{row['ID']}"):
#                     delete_qb_mapping(row["ID"])
#                     st.success("Mapping removed.")
#                     st.rerun()
# else:
#     st.info("ℹ️ No QB mappings yet.")



# OLD CODE BELOW

# import streamlit as st
# import pandas as pd
# from helpers.db_utils import (
#     get_all_grants,
#     get_line_items_by_grant,
#     add_line_item,
#     delete_line_item,
#     get_filtered_qb_codes,
#     get_mappings_for_grant,
#     add_qb_mapping,
#     delete_qb_mapping,
#     update_line_item_allocated
# )

# st.set_page_config(page_title="Line Item Mapping", page_icon="🧩")
# st.title("🧩 Map QB Codes to Grant Line Items")

# # ----------------------------------
# # 1. Select Grant
# # ----------------------------------
# grants = get_all_grants()
# grant_options = {f"{g[1]} ({g[2]})": g[0] for g in grants}  # g[1]=name, g[2]=funder, g[0]=id

# selected_label = st.selectbox("Select a Grant", options=list(grant_options.keys()))
# selected_grant_id = grant_options[selected_label]

# # ----------------------------------
# # 2. View/Add/Delete Grant Line Items
# # ----------------------------------
# st.subheader("📋 Grant Line Items")
# line_items = get_line_items_by_grant(selected_grant_id)

# # Add line item form
# with st.form("add_line_item"):
#     st.markdown("### ➕ Add New Line Item")
#     new_name = st.text_input("Line Item Name").strip()
#     new_desc = st.text_area("Description (optional)").strip()
#     allocated = st.number_input("Allocated Amount $", min_value=0.0)
#     submitted = st.form_submit_button("Add Line Item")
#     if submitted:
#         if new_name:
#             add_line_item(selected_grant_id, new_name, new_desc, allocated)
#             st.success(f"✅ Added line item '{new_name}' with ${allocated:,.2f}")
#             st.rerun()
#         else:
#             st.warning("⚠️ Line Item name is required.")


# if line_items:
#     df_line_items = pd.DataFrame(line_items, columns=["ID", "Name", "Description", "Allocated Amount"])
#     st.dataframe(df_line_items.drop(columns=["ID"]), use_container_width=True)

#     with st.expander("➖ Delete Line Item"):
#         item_to_delete = st.selectbox("Choose Line Item to Delete", options=df_line_items["Name"].tolist())
#         if st.button("Confirm Deletion"):
#             line_item_id = df_line_items[df_line_items["Name"] == item_to_delete]["ID"].values[0]
#             delete_line_item(line_item_id)
#             st.success("✅ Line item deleted.")
#             st.rerun()
# else:
#     st.info("ℹ️ No line items yet for this grant.")



# with st.expander("✏️ Update Allocated Amount"):
#     selected_item = st.selectbox("Select Line Item to Update", df_line_items["Name"].tolist())
#     current_amt = df_line_items[df_line_items["Name"] == selected_item]["Allocated Amount"].values[0]
#     new_amt = st.number_input("New Allocated Amount ($)", value=float(current_amt), min_value=0.0, step=100.0)
    
#     if st.button("Update Amount"):
#         item_id = df_line_items[df_line_items["Name"] == selected_item]["ID"].values[0]
#         update_line_item_allocated(item_id, new_amt)
#         st.success(f"✅ Updated '{selected_item}' to ${new_amt:,.2f}")
#         st.rerun()


# # ----------------------------------
# # 3. Map QB Codes to Line Items
# # ----------------------------------
# st.markdown("---")
# st.subheader("🔗 Map QuickBooks Code to a Line Item")

# qb_data = get_filtered_qb_codes("All", "All")
# lineitem_options = [li[1] for li in line_items]  # li[1] = line item name

# with st.form("map_qb_code_form"):
#     qb_code_label = st.selectbox("QB Code", [f"{r['code']} – {r['name']}" for _, r in qb_data.iterrows()])
#     selected_li = st.selectbox("Grant Line Item", options=lineitem_options)
#     if st.form_submit_button("Map Code"):
#         code = qb_code_label.split("–")[0].strip()
#         line_item_id = next((li[0] for li in line_items if li[1] == selected_li), None)
#         add_qb_mapping(selected_grant_id, code, line_item_id)
#         st.success(f"✅ Mapped QB Code {code} to '{selected_li}'")
#         st.rerun()

# # ----------------------------------
# # 4. View/Delete Existing Mappings
# # ----------------------------------
# st.markdown("---")
# st.subheader("📎 Existing QB Mappings")

# mappings = get_mappings_for_grant(selected_grant_id)
# if mappings:
#     df_map = pd.DataFrame(mappings, columns=["ID", "QB Code", "QB Name", "Line Item"])
#     st.dataframe(df_map.drop(columns=["ID"]), use_container_width=True)

#     with st.expander("🗑️ Remove Mapping"):
#         to_remove = st.selectbox("Select QB Code to Remove", df_map["QB Code"].tolist())
#         if st.button("Remove Mapping"):
#             mapping_id = df_map[df_map["QB Code"] == to_remove]["ID"].values[0]
#             delete_qb_mapping(mapping_id)
#             st.success("🧹 Mapping removed.")
#             st.rerun()
# else:
#     st.info("ℹ️ No mappings found.")
