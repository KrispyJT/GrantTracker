import streamlit as st
import pandas as pd
from helpers.db_utils import (
    get_parent_categories,
    add_parent_category,
    update_parent_category,
    delete_parent_category,
    get_subcategories,
    add_subcategory,
    update_subcategory,
    delete_subcategory,
    get_qb_codes,
    add_qb_code,
    update_qb_code,
    delete_qb_code,
    get_filtered_qb_codes,
)

st.set_page_config(page_title="QuickBook Codes", page_icon="💼")
st.title("💼 Quickbook Mapping Tool")
st.write("The user can create a Quickbook code and edit existing codes.")

# -------------------
# PARENT CATEGORY
# -------------------
st.markdown("### 📁 Parent Category")
parent_cats = get_parent_categories()
parent_dict = {row["name"]: row["id"] for row in parent_cats}
parent_names = list(parent_dict.keys())

selected_parent = st.selectbox("Select Parent Category", parent_names or ["No Categories Yet"])

with st.expander("➕ Add New Parent Category"):
    with st.form("add_parent"):
        new_parent = st.text_input("New Parent Category Name")
        new_desc = st.text_input("Description")
        if st.form_submit_button("Add") and new_parent.strip():
            add_parent_category(new_parent.strip(), new_desc.strip())
            st.success("Parent category added.")
            st.rerun()

if selected_parent in parent_dict:
    with st.expander("✏️ Edit/Delete Parent Category"):
        with st.form("edit_parent"):
            new_name = st.text_input("Edit Name", value=selected_parent)
            col1, col2 = st.columns(2)
            if col1.form_submit_button("Update"):
                update_parent_category(parent_dict[selected_parent], new_name.strip())
                st.success("Updated.")
                st.rerun()
            if col2.form_submit_button("Delete"):
                deleted = delete_parent_category(parent_dict[selected_parent])
                if deleted:
                    st.success("Deleted.")
                    st.rerun()
                else:
                    st.warning("⚠️ Cannot delete: Subcategories exist.")

# -------------------
# SUBCATEGORY
# -------------------
st.markdown("### 📂 Subcategory")
selected_sub = "No Subcategories Yet"
cat_dict = {}
parent_id = parent_dict.get(selected_parent)
if not isinstance(parent_id, int):
    parent_id = None

if parent_id is not None:
    subcats = get_subcategories(parent_id)
    cat_dict = {row["name"]: row["id"] for row in subcats}
    sub_names = list(cat_dict.keys())
    selected_sub = st.selectbox("Select Subcategory", sub_names or ["No Subcategories Yet"])

    with st.expander("➕ Add New Subcategory"):
        with st.form("add_subcat"):
            new_sub = st.text_input("New Subcategory")
            if st.form_submit_button("Add") and new_sub.strip():
                add_subcategory(new_sub.strip(), parent_dict[selected_parent])
                st.success("Subcategory added.")
                st.rerun()

    if selected_sub in cat_dict:
        with st.expander("✏️ Edit/Delete Subcategory"):
            with st.form("edit_subcat"):
                new_subname = st.text_input("Edit Subcategory Name", value=selected_sub)
                col1, col2 = st.columns(2)
                if col1.form_submit_button("Update"):
                    update_subcategory(cat_dict[selected_sub], new_subname.strip())
                    st.success("Updated.")
                    st.rerun()
                if col2.form_submit_button("Delete"):
                    deleted = delete_subcategory(cat_dict[selected_sub])
                    if deleted:
                        st.success("Deleted.")
                        st.rerun()
                    else:
                        st.warning("⚠️ Cannot delete: QB codes exist under this subcategory.")

# -------------------
# QB CODES
# -------------------
st.markdown("### 📇 QB Codes")
if selected_sub in cat_dict:
    code = st.text_input("QB Code (numbers only, e.g., 8705)")
    desc = st.text_input("Description (e.g., Workshops)")
    if st.button("Add QB Code"):
        if not code.strip().isdigit():
            st.error("Code must be numeric.")
        elif not desc.strip():
            st.error("Description cannot be empty.")
        else:
            added = add_qb_code(code.strip(), desc.strip(), cat_dict[selected_sub])
            if added:
                st.success("Code added.")
                st.rerun()
            else:
                st.error("⚠️ That code already exists.")

    st.subheader("✏️ Edit/Delete QB Code")
    codes = get_qb_codes()
    if codes:
        label_map = {f"{row['code']} - {row['name']}": row['code'] for row in codes}
        selected_label = st.selectbox("Select Code to Edit", list(label_map.keys()))
        selected_code = label_map[selected_label]
        current_desc = next((row["name"] for row in codes if row["code"] == selected_code), "")
        new_desc = st.text_input("New Description", value=current_desc)
        col1, col2 = st.columns(2)
        if col1.button("Update Description"):
            update_qb_code(selected_code, new_desc.strip())
            st.success("Updated.")
            st.rerun()
        if col2.button("❌ Delete QB Code"):
            delete_qb_code(selected_code)
            st.warning(f"Code '{selected_code}' deleted.")
            st.rerun()

# -------------------
# FILTERS & DISPLAY
# -------------------
st.subheader("📂 Filter Accounts")
parent_filter = st.selectbox("Filter by Parent Category", ["All"] + parent_names)
sub_filter = []
if parent_filter != "All" and parent_filter in parent_dict:
    sub_filter = [name for name, _ in get_subcategories(parent_dict[parent_filter])]

sub_selected = st.selectbox("Filter by Subcategory", ["All"] + sub_filter if sub_filter else ["All"])
filtered_df = get_filtered_qb_codes(parent_filter, sub_selected)
st.dataframe(filtered_df, use_container_width=True)










#########################

# # pages/quickbooks.py
# import streamlit as st
# import pandas as pd
# from helpers.db_utils import (
#     get_parent_categories,
#     add_parent_category,
#     update_parent_category,
#     delete_parent_category,
#     get_subcategories,
#     add_subcategory,
#     update_subcategory,
#     delete_subcategory,
#     get_qb_codes,
#     add_qb_code,
#     update_qb_code,
#     delete_qb_code,
#     get_filtered_qb_codes,
# )
# st.set_page_config(page_title="QuickBook Codes", page_icon="💼")
# st.title("💼 Quickbook Mapping Tool")
# st.write(
#     """
#     The user can create a Quickbook code and edit 
#     existing codes.
#     """
# )

# # -------------------
# # PARENT CATEGORY
# # -------------------
# st.markdown("### 📁 Parent Category")
# parent_cats = get_parent_categories()
# parent_dict = {name: pid for pid, name in parent_cats}

# selected_parent = st.selectbox("Select Parent Category", list(parent_dict.keys()) or ["No Categories Yet"])

# with st.expander("➕ Add New Parent Category"):
#     with st.form("add_parent"):
#         new_parent = st.text_input("New Parent Category Name")
#         new_desc = st.text_input("Description")
#         if st.form_submit_button("Add") and new_parent.strip():
#             add_parent_category(new_parent.strip(), new_desc.strip())
#             st.success("Parent category added.")
#             st.rerun()

# if selected_parent != "No Categories Yet":
#     with st.expander("✏️ Edit/Delete Parent Category"):
#         with st.form("edit_parent"):
#             new_name = st.text_input("Edit Name", value=selected_parent)
#             col1, col2 = st.columns(2)
#             if col1.form_submit_button("Update"):
#                 update_parent_category(parent_dict[selected_parent], new_name.strip())
#                 st.success("Updated.")
#                 st.rerun()
#             if col2.form_submit_button("Delete"):
#                 deleted = delete_parent_category(parent_dict[selected_parent])
#                 if deleted:
#                     st.success("Deleted.")
#                     st.rerun()
#                 else:
#                     st.warning("⚠️ Cannot delete: Subcategories exist.")

# # -------------------
# # SUBCATEGORY
# # -------------------
# st.markdown("### 📂 Subcategory")
# selected_sub = "No Subcategories Yet"

# if selected_parent != "No Categories Yet":
#     subcats = get_subcategories(parent_dict[selected_parent])
#     cat_dict = {name: cid for cid, name in subcats}
#     selected_sub = st.selectbox("Select Subcategory", list(cat_dict.keys()) or ["No Subcategories Yet"])

#     with st.expander("➕ Add New Subcategory"):
#         with st.form("add_subcat"):
#             new_sub = st.text_input("New Subcategory")
#             if st.form_submit_button("Add") and new_sub.strip():
#                 add_subcategory(new_sub.strip(), parent_dict[selected_parent])
#                 st.success("Subcategory added.")
#                 st.rerun()

#     if selected_sub != "No Subcategories Yet":
#         with st.expander("✏️ Edit/Delete Subcategory"):
#             with st.form("edit_subcat"):
#                 new_subname = st.text_input("Edit Subcategory Name", value=selected_sub)
#                 col1, col2 = st.columns(2)
#                 if col1.form_submit_button("Update"):
#                     update_subcategory(cat_dict[selected_sub], new_subname.strip())
#                     st.success("Updated.")
#                     st.rerun()
#                 if col2.form_submit_button("Delete"):
#                     deleted = delete_subcategory(cat_dict[selected_sub])
#                     if deleted:
#                         st.success("Deleted.")
#                         st.rerun()
#                     else:
#                         st.warning("⚠️ Cannot delete: QB codes exist under this subcategory.")

# # -------------------
# # QB CODES
# # -------------------
# st.markdown("### 📇 QB Codes")
# if selected_sub != "No Subcategories Yet":
#     code = st.text_input("QB Code (numbers only, e.g., 8705)")
#     desc = st.text_input("Description (e.g., Workshops)")
#     if st.button("Add QB Code"):
#         if not code.strip().isdigit():
#             st.error("Code must be numeric.")
#         elif not desc.strip():
#             st.error("Description cannot be empty.")
#         else:
#             added = add_qb_code(code.strip(), desc.strip(), cat_dict[selected_sub])
#             if added:
#                 st.success("Code added.")
#                 st.rerun()
#             else:
#                 st.error("⚠️ That code already exists.")

#     st.subheader("✏️ Edit/Delete QB Code")
#     codes = get_qb_codes()
#     if codes:
#         label_map = {f"{code} - {name}": code for code, name in codes}
#         selected_label = st.selectbox("Select Code to Edit", list(label_map.keys()))
#         selected_code = label_map[selected_label]
#         current_desc = [n for c, n in codes if c == selected_code][0]

#         new_desc = st.text_input("New Description", value=current_desc)
#         col1, col2 = st.columns(2)
#         if col1.button("Update Description"):
#             update_qb_code(selected_code, new_desc.strip())
#             st.success("Updated.")
#             st.rerun()
#         if col2.button("❌ Delete QB Code"):
#             delete_qb_code(selected_code)
#             st.warning(f"Code '{selected_code}' deleted.")
#             st.rerun()

# # -------------------
# # FILTERS & DISPLAY
# # -------------------
# st.subheader("📂 Filter Accounts")
# parent_filter = st.selectbox("Filter by Parent Category", ["All"] + list(parent_dict.keys()))
# sub_filter = []
# if parent_filter != "All":
#     sub_filter = [name for _, name in get_subcategories(parent_dict[parent_filter])]
# sub_selected = st.selectbox("Filter by Subcategory", ["All"] + sub_filter if sub_filter else ["All"])

# filtered_df = get_filtered_qb_codes(parent_filter, sub_selected)
# st.dataframe(filtered_df, use_container_width=True)
