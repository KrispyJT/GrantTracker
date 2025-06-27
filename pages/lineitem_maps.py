import streamlit as st
import pandas as pd
from helpers.db_utils import (
    get_all_grants,
    get_line_items_by_grant,
    add_line_item,
    update_line_item,
    delete_line_item,
    get_filtered_qb_codes,
    get_mappings_for_grant,
    add_qb_mapping,
    delete_qb_mapping,
)

st.set_page_config(page_title="Line Item Mapping", page_icon="🧩")
st.title("🧩 Map QB Codes to Line Items")


st.markdown("""
### Line Item Mapping Overview

This page allows you to manage the financial structure of each grant by defining **line items** and linking them to **QuickBooks (QB) codes** for accurate tracking and reporting.

You can:
- 📋 **Create and manage line items** for the selected grant, including descriptions and allocated amounts.  
- 📝 **Edit descriptions and budgets** for each line item (names must be managed through deletion and re-entry).  
- 🔗 **Map QB codes** to line items to align financial records with your accounting system.  
- 📎 **Review and remove mappings**, with visual summaries showing which items are still unmapped.
""")


# ----------------------------------
# 1. Select Grant
# ----------------------------------
grants = get_all_grants()

if not grants:
    st.warning("⚠️ No grants found. Please add a grant first.")
    st.stop()

grant_options = {f"{g['name']} ({g['funder']})": g['id'] for g in grants}
selected_label = st.selectbox("🎯 Select a Grant", list(grant_options.keys()))
selected_grant_id = grant_options.get(selected_label)

# Grant Info Display
selected_grant = next(g for g in grants if g["id"] == selected_grant_id)
with st.expander("📄 Grant Overview", expanded=False):
    st.markdown(f"**Grant Name:** {selected_grant['name']}")
    st.markdown(f"**Funder:** {selected_grant['funder']}")
    st.markdown(f"**Status** {selected_grant['status']}")
    st.markdown(f"**Total Award Amount:** ${selected_grant['total_award']:,.2f}")
    st.markdown(f"**Start Date:** {selected_grant['start_date']} **End Date:** {selected_grant['end_date']}")
    if selected_grant['notes']:
        st.info(f"**Notes:** {selected_grant['notes']}")

# ----------------------------------
# 2. Manage Line Items
# ----------------------------------
st.divider()
st.header("📋 Manage Line Items")

# Fetch current line items
line_items = get_line_items_by_grant(selected_grant_id)
df_line_items = pd.DataFrame(line_items, columns=["ID", "Name", "Description", "Allocated Amount"])

# Add New Line Item
with st.expander("➕ Add New Line Item"):
    with st.form("add_line_item_form"):
        raw_name = st.text_input("Name")
        raw_desc = st.text_area("Description")
        li_alloc = st.number_input("Allocated Amount ($)", min_value=0.0, step=100.0)

        if st.form_submit_button("Add Line Item"):
            li_name = raw_name.strip().title()
            li_desc = raw_desc.strip()

            existing_names = [name.strip().title() for _, name, *_ in line_items]

            if not li_name:
                st.warning("⚠️ Name is required.")
            elif li_name in existing_names:
                st.error("⚠️ A line item with this name already exists for this grant.")
            else:
                add_line_item(selected_grant_id, li_name, li_desc, li_alloc)
                st.success(f"✅ '{li_name}' added.")
                st.rerun()

### WORLKING ON THIS RN
# --- Edit Line Items ---
with st.expander("📝 Edit Line Items"):
    st.caption("You can only edit *Description* and *Allocated Amount*. To rename a line item, please delete and re-add it.")

    # Create copy without ID for display/editing
    df_editable = df_line_items[["Name", "Description", "Allocated Amount"]]

    edited_df = st.data_editor(
    df_editable,
    use_container_width=True,
    num_rows="fixed",
    disabled={"Name": True},
    hide_index=True,
    key="line_editor"
    )


    # edited_df = st.data_editor(
    #     df_editable,
    #     use_container_width=True,
    #     num_rows="fixed",
    #     disabled=["Name"],  # Only Description + Allocated Amount are editable
    #     key="line_editor"
    # )

    if st.button("💾 Save Changes to Line Items"):
        updates_made = False
        for i, row in edited_df.iterrows():
            original = df_line_items.iloc[i]
            if (
                row["Description"].strip() != original["Description"]
                or float(row["Allocated Amount"]) != original["Allocated Amount"]
            ):
                update_line_item(
                    original["ID"],
                    original["Name"],  # still useful in case your function needs it
                    row["Description"].strip(),
                    float(row["Allocated Amount"])
                )
                updates_made = True

        if updates_made:
            st.success("✅ Changes saved successfully.")
            st.rerun()
        else:
            st.info("ℹ️ No changes to save.")


    # if st.button("💾 Save Changes to Line Items"):
    #     updates_made = False
    #     for i, row in edited_df.iterrows():
    #         original = df_line_items.iloc[i]
    #         if (
    #             row["Description"].strip() != original["Description"]
    #             or float(row["Allocated Amount"]) != original["Allocated Amount"]
    #         ):
    #             update_line_item(
    #                 original["ID"],
    #                 original["Name"],
    #                 row["Description"].strip(),
    #                 float(row["Allocated Amount"])
    #             )
    #             updates_made = True

    #     if updates_made:
    #         st.success("✅ Changes saved successfully.")
    #         st.rerun()
    #     else:
    #         st.info("ℹ️ No changes to save.")


# --- Delete Line Item ---
with st.expander("❌ Delete Line Item"):
    updated_line_items = get_line_items_by_grant(selected_grant_id)
    id_to_name = {item['id']: item['name'] for item in updated_line_items}

    if id_to_name:
        selected_del_id = st.selectbox(
            "Select a line item to delete",
            options=list(id_to_name.keys()),
            format_func=lambda x: f"{id_to_name[x]}"
        )
        if st.button("Delete Selected Line Item"):
            delete_line_item(selected_del_id)
            st.warning("🗑️ Line item deleted.")
            st.rerun()
    else:
        st.info("No line items available to delete.")


# ----------------------------------
# 3. Map QB Codes to Line Items
# ----------------------------------

st.divider()
st.header("🔗 Map QuickBooks Codes to Line Items")

qb_data = get_filtered_qb_codes("All", "All")
lineitem_labels = {li['name']: li['id'] for li in line_items}

with st.form("map_qb_code_form"):
    li_name = st.selectbox("Grant Line Item", options=list(lineitem_labels.keys()))
    qb_choice = st.selectbox("QB Code", [f"{r['code']} – {r['name']}" for _, r in qb_data.iterrows()])
    
    if st.form_submit_button("Map Code"):
        li_id = lineitem_labels[li_name]
        code = qb_choice.split("–")[0].strip()
        success = add_qb_mapping(selected_grant_id, code, li_id)

        
        if success:
            st.success(f"✅ Mapped QB Code {code} to '{li_name}'")
            st.rerun()
        else:
            st.warning(f"Mapping already exists between '{code}' and '{li_name}'")


# ----------------------------------
# 4. View/Delete Existing Mappings
# ----------------------------------
st.header("📎 Existing QB Mappings")
mappings = get_mappings_for_grant(selected_grant_id)

if not mappings.empty:
    # Rename and reorder columns
    df_map = mappings.rename(columns={
        "id": "ID",
        "qb_code": "QB Code",
        "qb_name": "QB Name",
        "line_item": "Line Item"
    })[["ID", "QB Code", "QB Name", "Line Item"]]

    # Group by line item
    grouped = df_map.groupby("Line Item")

    # Determine which line items are not yet mapped
    mapped_items = df_map["Line Item"].unique().tolist()
    total_items = len(line_items)
    unmapped_items = [li['name'] for li in line_items if li['name'] not in mapped_items]

    # Summary Section
    if total_items == 0:
        st.warning("⚠️ No line items created for this grant.")
    elif len(mapped_items) == total_items:
        st.success(f"✅ All {total_items} line items are mapped.")
    else:
        st.info(f"🔄 {len(mapped_items)} of {total_items} line items mapped. {len(unmapped_items)} remaining.")
        st.warning("The following line items are not yet mapped:")
        for name in unmapped_items:
            st.markdown(f"- {name}")

    # Show grouped mappings and delete buttons
    for li_name, group in grouped:
        with st.expander(f"🧾 {li_name}", expanded=False):
            for _, row in group.iterrows():
                st.markdown(f"• `{row['QB Code']}` – {row['QB Name']}")
                if st.button("🗑️ Remove", key=f"del_map_{row['ID']}"):
                    delete_qb_mapping(row["ID"])
                    st.success("Mapping removed.")
                    st.rerun()
else:
    st.info("ℹ️ No QuickBooks codes have been mapped yet.")




### OLD
# st.header("📎 Existing QB Mappings")
# mappings = get_mappings_for_grant(selected_grant_id)

# if mappings:
#     df_map = pd.DataFrame(mappings, columns=["ID", "QB Code", "QB Name", "Line Item"])
#     grouped = df_map.groupby("Line Item")

#     mapped_items = df_map["Line Item"].unique().tolist()
#     total_items = len(line_items)
#     unmapped_items = [li[1] for li in line_items if li[1] not in mapped_items]

#     # Summary
#     if total_items == 0:
#         st.warning("⚠️ No line items created for this grant.")
#     elif len(mapped_items) == total_items:
#         st.success(f"✅ All {total_items} line items are mapped.")
#     else:
#         st.info(f"🔄 {len(mapped_items)} of {total_items} line items mapped. {len(unmapped_items)} remaining.")
#         # st.warning("**Unmapped items**: " + ", ".join(unmapped_items))
#         st.warning("The following line items are not yet mapped:")
#         for name in unmapped_items:
#             st.markdown(f"- {name}")

#     # Show grouped mappings
#     for li_name, group in grouped:
#         with st.expander(f"🧾 {li_name}", expanded=False):
#             for _, row in group.iterrows():
#                 st.markdown(f"• `{row['QB Code']}` – {row['QB Name']}")
#                 if st.button("🗑️ Remove", key=f"del_map_{row['ID']}"):
#                     delete_qb_mapping(row["ID"])
#                     st.success("Mapping removed.")
#                     st.rerun()
# else:
#     st.info("ℹ️ No QuickBooks codes have been mapped yet.")
## END OF OLD


#########
# 2nd working 
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
# grant_options = {f"{g[1]} ({g[2]})": g[0] for g in grants}
# selected_label = st.selectbox("🎯 Select a Grant", list(grant_options.keys()))
# selected_grant_id = grant_options[selected_label]

# # Optional Grant Info Display
# selected_grant = next(g for g in grants if g[0] == selected_grant_id)
# with st.expander("📄 Grant Overview", expanded=False):
#     st.markdown(f"**Grant Name:** {selected_grant[1]}")
#     st.markdown(f"**Funder:** {selected_grant[2]}")
#     st.markdown(f"**Status** {selected_grant[5]}")
#     st.markdown(f"**Total Award Amount:** ${selected_grant[6]:,.2f}")
#     st.markdown(f"**Start Date:** {selected_grant[3]} **End Date:** {selected_grant[4]}")
#     if selected_grant[7]:
#         st.info(f"**Notes:** {selected_grant[7]}")


# # ----------------------------------
# # 2. Manage Line Items
# # ----------------------------------
# st.divider()
# st.header("📋 Manage Line Items")

# line_items = get_line_items_by_grant(selected_grant_id)

# with st.expander("➕ Add New Line Item"):
#     with st.form("add_line_item_form"):
#         name = st.text_input("Name").strip()
#         desc = st.text_area("Description").strip()
#         alloc = st.number_input("Allocated Amount ($)", min_value=0.0, step=100.0)
#         if st.form_submit_button("Add Line Item"):
#             if name:
#                 add_line_item(selected_grant_id, name, desc, alloc)
#                 st.success(f"✅ '{name}' added.")
#                 st.rerun()
#             else:
#                 st.warning("Name is required.")

# if line_items:
#     df = pd.DataFrame(line_items, columns=["ID", "Name", "Description", "Allocated"])
#     with st.expander("📝 Edit or Delete Line Items"):
#         for _, row in df.iterrows():
#             with st.container():
#                 st.markdown(f"#### ✏️ {row['Name']} (${row['Allocated']:,.2f})")
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     new_name = st.text_input("Edit Name", value=row["Name"], key=f"name_{row['ID']}")
#                     new_desc = st.text_area("Edit Description", value=row["Description"], key=f"desc_{row['ID']}")
#                     new_amt = st.number_input("Allocated $", value=float(row["Allocated"]), key=f"alloc_{row['ID']}")
#                     if st.button("Save Changes", key=f"save_{row['ID']}"):
#                         update_line_item_allocated(row["ID"], new_amt)
#                         st.success("Updated.")
#                         st.rerun()
#                 with col2:
#                     if st.button("❌ Delete", key=f"del_{row['ID']}"):
#                         delete_line_item(row["ID"])
#                         st.warning(f"Deleted {row['Name']}")
#                         st.rerun()
# else:
#     st.info("ℹ️ No line items for this grant.")

# # ----------------------------------
# # 3. Map QB Codes to Line Items
# # ----------------------------------
# st.divider()
# st.header("🔗 Map QB Codes")

# qb_data = get_filtered_qb_codes("All", "All")
# lineitem_labels = {li[1]: li[0] for li in line_items}

# with st.form("map_qb_form"):
#     li_name = st.selectbox("Line Item", options=list(lineitem_labels.keys()))
#     qb_choice = st.selectbox("QB Code", [f"{r['code']} – {r['name']}" for _, r in qb_data.iterrows()])
#     if st.form_submit_button("Map Code"):
#         li_id = lineitem_labels[li_name]
#         code = qb_choice.split("–")[0].strip()
#         add_qb_mapping(selected_grant_id, code, li_id)
#         st.success(f"✅ Mapped {code} to '{li_name}'")
#         st.rerun()

# # ----------------------------------
# # 4. View & Delete Mappings
# # ----------------------------------


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

#         # 🚫 Show which ones are still unmapped
#         unmapped_names = [li[1] for li in line_items if li[1] not in mapped_ids]
#         if unmapped_names:
#             st.warning("🚫 The following line items are not yet mapped:")
#             for name in unmapped_names:
#                 st.markdown(f"- {name}")

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
#     st.info("ℹ️ No QuickBooks codes have been mapped to any line items yet. Use the form above to begin.")

# END OF 2nd 











