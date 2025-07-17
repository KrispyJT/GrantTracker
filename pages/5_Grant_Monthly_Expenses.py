# pages/actual_expenses.py
# pages/actual_expenses.py
import streamlit as st
import pandas as pd
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from helpers.db_utils import (
    get_all_grants,
    get_line_items_by_grant,
    get_mappings_for_grant,
    get_actual_expenses_for_grant,
    save_actual_expense,
)
from helpers.helpers import generate_month_range, render_filter_sidebar, render_sidebar_navigation
from helpers.ui_utils import inject_sidebar_css

st.set_page_config(page_title="💵 Actual Expenses", layout="wide")

# Auth Check
if not st.session_state.get("authenticated"):
    st.warning("🔒 Please log in to access this page.")
    st.stop()

inject_sidebar_css()
render_sidebar_navigation()


st.title("Enter Monthly Actual Expenses")
# 1️⃣ Grant Selection
grants = get_all_grants()
if not grants:
    st.warning("No grants available.")
    st.stop()

grant_options = {f"{g['name']} ({g['funder']})": g['id'] for g in grants}
col1, col2 = st.columns(2)

with col1:
    selected_grant_label = st.selectbox("🌟 Select a Grant", list(grant_options.keys()))
    selected_grant_id = grant_options[selected_grant_label]

# 🆕 Submission History for that grant
from helpers.db_utils import get_submitted_months_for_grant  # make sure it's imported
submission_history = get_submitted_months_for_grant(selected_grant_id)

with st.expander("📅 Submission History for This Grant", expanded=False):
    if not submission_history:
        st.info("No expenses have been submitted yet.")
    else:
        for record in submission_history:
            raw_month = record["month"]  # 'YYYY-MM'
            formatted_month = datetime.strptime(raw_month, "%Y-%m").strftime("%b %Y")  # 'Jan 2024'
            last_saved = record["last_saved"]
            st.markdown(f"✅ **{formatted_month}** — Last saved: `{last_saved}`")


# 2️⃣ Month Selection
grant_row = next(g for g in grants if g['id'] == selected_grant_id)
month_range = generate_month_range(grant_row['start_date'], grant_row['end_date'])
if not month_range:
    st.warning("This grant has no valid month range.")
    st.stop()

month_label_map = {m: datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in month_range}
label_to_month = {v: k for k, v in month_label_map.items()}

with col2:
    selected_label = st.selectbox("📅 Select Reporting Month", list(label_to_month.keys()))
    selected_month = label_to_month[selected_label]

# 3️⃣ Retrieve Data
line_items = get_line_items_by_grant(selected_grant_id)
mappings = get_mappings_for_grant(selected_grant_id)
existing_expenses = get_actual_expenses_for_grant(selected_grant_id, selected_month)

expense_lookup = {(row['qb_code'], row['line_item_id']): row for row in existing_expenses}

# 4️⃣ Build Expense Records
def build_expense_records():
    records = []
    for _, row in mappings.iterrows():
        li_name = row["line_item"]
        qb_code = row["qb_code"]
        qb_name = row["qb_name"]
        line_item_id = next((li['id'] for li in line_items if li['name'] == li_name), None)
        expense_row = expense_lookup.get((qb_code, line_item_id))
        records.append({
            "Line Item": li_name,
            "QB Code": qb_code,
            "QB Name": qb_name,
            "Amount Spent": float(expense_row['amount']) if expense_row else 0.0,
            "Notes": expense_row['notes'] if expense_row else "",
            "line_item_id": line_item_id
        })
    return records

records = build_expense_records()
if not records:
    st.info("No line item mappings found for this grant.")
    st.stop()

df = pd.DataFrame(records)

# ✅ Filter Sidebar
filter_li, filter_qb_code, filter_qb_name = render_filter_sidebar(df)

# 🔍 Apply Filters
filtered_df = df.copy()
if filter_li != "All":
    filtered_df = filtered_df[filtered_df["Line Item"] == filter_li]
if filter_qb_code != "All":
    filtered_df = filtered_df[filtered_df["QB Code"].astype(str) == filter_qb_code]
if filter_qb_name != "All":
    filtered_df = filtered_df[filtered_df["QB Name"] == filter_qb_name]

# 5️⃣ Expense Table
st.subheader("📟 Monthly Expense Entry Table")

with st.expander("ℹ️ How to Use This Table"):
    st.markdown("""
    - 🔎 Use the sidebar to filter line items by name, QB code, or QB name.
    - ✏️ Edit the **Amount Spent** and **Notes** directly in the table.
    - 💾 Be sure to click **'Submit Monthly Expenses'** before changing months.
    - 📅 Submissions are saved **per month**. If you switch months without saving, changes will be lost.
    """)

st.caption("✅ *Edit only the Amount Spent and Notes columns. All other fields are read-only.*")

gb = GridOptionsBuilder.from_dataframe(filtered_df)
gb.configure_column("Amount Spent", editable=True, type=["numericColumn", "numberColumnFilter"],
    valueFormatter=JsCode("function(params) { return '$' + Number(params.value).toLocaleString(); }")
)
gb.configure_column("Notes", editable=True)
gb.configure_columns("line_item_id", hide=True)
grid_options = gb.build()

grid_response = AgGrid(
    filtered_df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
    theme="streamlit"
)

edited_df = grid_response["data"]

# 6️⃣ Display Totals
total_filtered = edited_df["Amount Spent"].sum()
total_all = df["Amount Spent"].sum()

col_total_1, col_total_2 = st.columns(2)
col_total_1.metric("💰 Total in Filtered View", f"${total_filtered:,.2f}")
col_total_2.metric("📊 Total Across All Line Items", f"${total_all:,.2f}")

# 7️⃣ Save Expenses Button + Reminder
with st.container():
    st.warning(
        "⚠️ Please submit your Monthly Expenses before switching months. "
        "If you enter amounts and change months without saving, your changes will be lost."
    )

    if st.button("📂 Submit Monthly Expenses", key="submit_expenses"):
        rows_to_save = edited_df[
            (edited_df["Amount Spent"] != 0) | (edited_df["Notes"].astype(str).str.strip() != "")
        ]

        if rows_to_save.empty:
            st.info("ℹ️ Nothing to save.")
        else:
            for _, row in rows_to_save.iterrows():
                amount = float(row["Amount Spent"])
                notes = row.get("Notes", "").strip()
                line_item_id = row["line_item_id"]
                qb_code = row["QB Code"]

                if line_item_id and (amount != 0 or notes):
                    save_actual_expense(
                        grant_id=selected_grant_id,
                        month=selected_month,
                        qb_code=qb_code,
                        line_item_id=line_item_id,
                        amount=amount,
                        notes=notes,
                        date_submitted=datetime.today().date()
                    )

            st.success("✅ Expenses saved.")
            st.rerun()


# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
# from helpers.db_utils import (
#     get_all_grants,
#     get_line_items_by_grant,
#     get_mappings_for_grant,
#     get_actual_expenses_for_grant,
#     save_actual_expense,
# )
# from helpers.helpers import generate_month_range, render_filter_sidebar

# st.set_page_config(page_title="💵 Actual Expenses", layout="wide")
# st.title("Enter Monthly Actual Expenses")

# # 1️⃣ Grant Selection
# grants = get_all_grants()
# if not grants:
#     st.warning("No grants available.")
#     st.stop()

# grant_options = {f"{g['name']} ({g['funder']})": g['id'] for g in grants}
# col1, col2 = st.columns(2)

# with col1:
#     selected_grant_label = st.selectbox("🌟 Select a Grant", list(grant_options.keys()))
#     selected_grant_id = grant_options[selected_grant_label]

# # 2️⃣ Month Selection
# grant_row = next(g for g in grants if g['id'] == selected_grant_id)
# month_range = generate_month_range(grant_row['start_date'], grant_row['end_date'])
# if not month_range:
#     st.warning("This grant has no valid month range.")
#     st.stop()

# month_label_map = {m: datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in month_range}
# label_to_month = {v: k for k, v in month_label_map.items()}

# with col2:
#     selected_label = st.selectbox("📅 Select Reporting Month", list(label_to_month.keys()))
#     selected_month = label_to_month[selected_label]

# # 3️⃣ Retrieve Data
# line_items = get_line_items_by_grant(selected_grant_id)
# mappings = get_mappings_for_grant(selected_grant_id)
# existing_expenses = get_actual_expenses_for_grant(selected_grant_id, selected_month)

# expense_lookup = {(row['qb_code'], row['line_item_id']): row for row in existing_expenses}

# # 4️⃣ Build Expense Records
# def build_expense_records():
#     records = []
#     for _, row in mappings.iterrows():
#         li_name = row["line_item"]
#         qb_code = row["qb_code"]
#         qb_name = row["qb_name"]
#         line_item_id = next((li['id'] for li in line_items if li['name'] == li_name), None)
#         expense_row = expense_lookup.get((qb_code, line_item_id))
#         records.append({
#             "Line Item": li_name,
#             "QB Code": qb_code,
#             "QB Name": qb_name,
#             "Amount Spent": float(expense_row['amount']) if expense_row else 0.0,
#             "Notes": expense_row['notes'] if expense_row else "",
#             "line_item_id": line_item_id
#         })
#     return records

# records = build_expense_records()
# if not records:
#     st.info("No line item mappings found for this grant.")
#     st.stop()

# df = pd.DataFrame(records)

# # ✅ Filter Sidebar
# filter_li, filter_qb_code, filter_qb_name = render_filter_sidebar(df)

# # 🔍 Apply Filters
# filtered_df = df.copy()
# if filter_li != "All":
#     filtered_df = filtered_df[filtered_df["Line Item"] == filter_li]
# if filter_qb_code != "All":
#     filtered_df = filtered_df[filtered_df["QB Code"].astype(str) == filter_qb_code]
# if filter_qb_name != "All":
#     filtered_df = filtered_df[filtered_df["QB Name"] == filter_qb_name]

# # 5️⃣ Expense Table
# st.subheader("📟 Monthly Expense Entry Table")

# with st.expander("ℹ️ How to Use This Table"):
#     st.markdown("""
#     - 🔎 Use the sidebar to filter line items by name, QB code, or QB name.
#     - ✏️ Enter the **Amount Spent** and any **Notes** for each row.
#     - 💾 Make sure to **click 'Submit Actual Expenses'** to save your entries.
#     - 📅 You must **submit expenses separately for each month**.
#     """)

# st.caption("✅ *Edit only the Amount Spent and Notes columns. All other fields are read-only.*")

# gb = GridOptionsBuilder.from_dataframe(filtered_df)
# gb.configure_column("Amount Spent", editable=True, type=["numericColumn", "numberColumnFilter"],
#     valueFormatter=JsCode("function(params) { return '$' + Number(params.value).toLocaleString(); }")
# )
# gb.configure_column("Notes", editable=True)
# gb.configure_columns("line_item_id", hide=True)
# grid_options = gb.build()

# grid_response = AgGrid(
#     filtered_df,
#     gridOptions=grid_options,
#     update_mode=GridUpdateMode.VALUE_CHANGED,
#     allow_unsafe_jscode=True,
#     fit_columns_on_grid_load=True,
#     theme="streamlit"
# )

# edited_df = grid_response["data"]

# # 6️⃣ Display Totals
# total_filtered = edited_df["Amount Spent"].sum()
# total_all = df["Amount Spent"].sum()

# col_total_1, col_total_2 = st.columns(2)
# col_total_1.metric("💰 Total in Filtered View", f"${total_filtered:,.2f}")
# col_total_2.metric("📊 Total Across All Line Items", f"${total_all:,.2f}")

# # 5️⃣ Expense Table
# st.subheader("📟 Monthly Expense Entry Table")

# with st.expander("ℹ️ How to Use This Table"):
#     st.markdown("""
#     - 🔎 Use the sidebar to filter line items by name, QB code, or QB name.
#     - ✏️ Edit the **Amount Spent** and **Notes** directly in the table.
#     - 💾 Be sure to click **'Submit Actual Expenses'** before changing months.
#     - 📅 Submissions are saved **per month**. If you switch months without saving, your changes will be lost.
#     """)

# st.caption("✅ *Edit only the Amount Spent and Notes columns. All other fields are read-only.*")

# gb = GridOptionsBuilder.from_dataframe(filtered_df)
# gb.configure_column("Amount Spent", editable=True, type=["numericColumn", "numberColumnFilter"],
#     valueFormatter=JsCode("function(params) { return '$' + Number(params.value).toLocaleString(); }")
# )
# gb.configure_column("Notes", editable=True)
# gb.configure_columns("line_item_id", hide=True)
# grid_options = gb.build()

# grid_response = AgGrid(
#     filtered_df,
#     gridOptions=grid_options,
#     update_mode=GridUpdateMode.VALUE_CHANGED,
#     allow_unsafe_jscode=True,
#     fit_columns_on_grid_load=True,
#     theme="streamlit"
# )

# edited_df = grid_response["data"]

# # 6️⃣ Display Totals
# total_filtered = edited_df["Amount Spent"].sum()
# total_all = df["Amount Spent"].sum()

# col_total_1, col_total_2 = st.columns(2)
# col_total_1.metric("💰 Total in Filtered View", f"${total_filtered:,.2f}")
# col_total_2.metric("📊 Total Across All Line Items", f"${total_all:,.2f}")


# # 7️⃣ Save Expenses
# st.warning("⚠️ Please click 'Submit Actual Expenses' before switching months. Unsaved entries will be lost.")
# if st.button("📂 Submit Actual Expenses"):
#     rows_to_save = edited_df[
#         (edited_df["Amount Spent"] != 0) | (edited_df["Notes"].astype(str).str.strip() != "")
#     ]

#     if rows_to_save.empty:
#         st.info("ℹ️ Nothing to save.")
#     else:
#         for _, row in rows_to_save.iterrows():
#             amount = float(row["Amount Spent"])
#             notes = row.get("Notes", "").strip()
#             line_item_id = row["line_item_id"]
#             qb_code = row["QB Code"]

#             if line_item_id and (amount != 0 or notes):
#                 save_actual_expense(
#                     grant_id=selected_grant_id,
#                     month=selected_month,
#                     qb_code=qb_code,
#                     line_item_id=line_item_id,
#                     amount=amount,
#                     notes=notes,
#                     date_submitted=datetime.today().date()
#                 )

#         st.success("✅ Expenses saved.")
#         st.rerun()



#################################
# pages/actual_expenses.py

# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
# from helpers.db_utils import (
#     get_all_grants,
#     get_line_items_by_grant,
#     get_mappings_for_grant,
#     get_actual_expenses_for_grant,
#     save_actual_expense,
# )
# from helpers.helpers import generate_month_range

# st.set_page_config(page_title="💵 Actual Expenses", layout="wide")
# st.title("Enter Monthly Actual Expenses")

# # -------------------
# # 1️⃣ Grant Selection
# # -------------------
# grants = get_all_grants()
# if not grants:
#     st.warning("No grants available.")
#     st.stop()

# grant_options = {f"{g['name']} ({g['funder']})": g['id'] for g in grants}
# col1, col2 = st.columns(2)

# with col1:
#     selected_grant_label = st.selectbox("🌟 Select a Grant", list(grant_options.keys()))
#     selected_grant_id = grant_options[selected_grant_label]

# # --------------------------
# # 2️⃣ Month Selection
# # --------------------------
# grant_row = next(g for g in grants if g['id'] == selected_grant_id)
# month_range = generate_month_range(grant_row['start_date'], grant_row['end_date'])

# if not month_range:
#     st.warning("This grant has no valid month range.")
#     st.stop()

# month_label_map = {m: datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in month_range}
# label_to_month = {v: k for k, v in month_label_map.items()}

# with col2:
#     selected_label = st.selectbox("📅 Select Reporting Month", list(label_to_month.keys()))
#     selected_month = label_to_month[selected_label]

# # --------------------------
# # 3️⃣ Retrieve Data
# # --------------------------
# line_items = get_line_items_by_grant(selected_grant_id)
# mappings = get_mappings_for_grant(selected_grant_id)
# existing_expenses = get_actual_expenses_for_grant(selected_grant_id, selected_month)

# expense_lookup = {
#     (row['qb_code'], row['line_item_id']): row for row in existing_expenses
# }

# # --------------------------
# # 4️⃣ Build Expense Records (Helper)
# # --------------------------
# def build_expense_records():
#     records = []
#     for _, row in mappings.iterrows():
#         li_name = row["line_item"]
#         qb_code = row["qb_code"]
#         qb_name = row["qb_name"]

#         line_item_id = next((li['id'] for li in line_items if li['name'] == li_name), None)
#         expense_row = expense_lookup.get((qb_code, line_item_id))

#         records.append({
#             "Line Item": li_name,
#             "QB Code": qb_code,
#             "QB Name": qb_name,
#             "Amount Spent": float(expense_row['amount']) if expense_row else 0.0,
#             "Notes": expense_row['notes'] if expense_row else "",
#             "line_item_id": line_item_id
#         })
#     return records

# records = build_expense_records()
# if not records:
#     st.info("No line item mappings found for this grant.")
#     st.stop()

# entry_df = pd.DataFrame(records).reset_index(drop=True)

# # --------------------------
# # 🔍 Sidebar Filters
# # --------------------------
# st.sidebar.markdown("### 🔎 Filter Line Items")

# line_item_options = ["All"] + sorted(entry_df["Line Item"].unique())
# qb_code_options = ["All"] + sorted(entry_df["QB Code"].astype(str).unique())
# qb_name_options = ["All"] + sorted(entry_df["QB Name"].unique())

# selected_line_item = st.sidebar.selectbox("Filter by Line Item", line_item_options)
# selected_qb_code = st.sidebar.selectbox("Filter by QB Code", qb_code_options)
# selected_qb_name = st.sidebar.selectbox("Filter by QB Name", qb_name_options)

# filtered_df = entry_df.copy()
# if selected_line_item != "All":
#     filtered_df = filtered_df[filtered_df["Line Item"] == selected_line_item]
# if selected_qb_code != "All":
#     filtered_df = filtered_df[filtered_df["QB Code"].astype(str) == selected_qb_code]
# if selected_qb_name != "All":
#     filtered_df = filtered_df[filtered_df["QB Name"] == selected_qb_name]

# # --------------------------
# # 5️⃣ Expense Table
# # --------------------------
# st.subheader("📟 Monthly Expense Entry Table")
# st.caption("✅ *Edit only the Amount Spent and Notes columns. All other fields are read-only.*")

# gb = GridOptionsBuilder.from_dataframe(filtered_df)
# gb.configure_column("Amount Spent", editable=True, type=["numericColumn", "numberColumnFilter"])
# gb.configure_column("Notes", editable=True)
# gb.configure_columns("line_item_id", hide=True)
# grid_options = gb.build()

# grid_response = AgGrid(
#     filtered_df,
#     gridOptions=grid_options,
#     update_mode=GridUpdateMode.VALUE_CHANGED,
#     allow_unsafe_jscode=True,
#     fit_columns_on_grid_load=True,
#     theme="streamlit"
# )

# edited_df = grid_response["data"]

# # --------------------------
# # 6️⃣ Show Total Spent
# # --------------------------
# total_spent = edited_df["Amount Spent"].sum()
# st.info(f"💰 **Total Entered:** ${total_spent:,.2f}")

# # --------------------------
# # 7️⃣ Save Expenses
# # --------------------------
# if st.button("📂 Submit Actual Expenses"):
#     rows_to_save = edited_df[
#         (edited_df["Amount Spent"] != 0) | (edited_df["Notes"].astype(str).str.strip() != "")
#     ]

#     if rows_to_save.empty:
#         st.info("ℹ️ Nothing to save.")
#     else:
#         for _, row in rows_to_save.iterrows():
#             amount = float(row["Amount Spent"])
#             raw_notes = row.get("Notes", "")
#             notes = raw_notes.strip() if isinstance(raw_notes, str) else ""
#             line_item_id = row["line_item_id"]
#             qb_code = row["QB Code"]

#             if line_item_id and (amount != 0 or notes):
#                 save_actual_expense(
#                     grant_id=selected_grant_id,
#                     month=selected_month,
#                     qb_code=qb_code,
#                     line_item_id=line_item_id,
#                     amount=amount,
#                     notes=notes,
#                     date_submitted=datetime.today().date()
#                 )

#         st.success("✅ Expenses saved.")
#         st.rerun()


#########################################

# ORGINAL
# # pages/actual_expenses.py

# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
# from helpers.db_utils import (
#     get_all_grants,
#     get_line_items_by_grant,
#     get_mappings_for_grant,
#     get_actual_expenses_for_grant,
#     save_actual_expense,
# )
# from helpers.helpers import generate_month_range

# st.set_page_config(page_title="💵 Actual Expenses", layout="wide")
# st.title("Enter Monthly Actual Expenses")

# # -------------------
# # 1️⃣ Grant Selection
# # -------------------
# grants = get_all_grants()
# if not grants:
#     st.warning("No grants available.")
#     st.stop()

# grant_options = {f"{g['name']} ({g['funder']})": g['id'] for g in grants}
# col1, col2 = st.columns(2)

# with col1:
#     selected_grant_label = st.selectbox("🌟 Select a Grant", list(grant_options.keys()))
#     selected_grant_id = grant_options[selected_grant_label]

# # --------------------------
# # 2️⃣ Month Selection
# # --------------------------
# grant_row = next(g for g in grants if g['id'] == selected_grant_id)
# month_range = generate_month_range(grant_row['start_date'], grant_row['end_date'])

# if not month_range:
#     st.warning("This grant has no valid month range.")
#     st.stop()

# month_label_map = {m: datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in month_range}
# label_to_month = {v: k for k, v in month_label_map.items()}

# with col2:
#     selected_label = st.selectbox("📅 Select Reporting Month", list(label_to_month.keys()))
#     selected_month = label_to_month[selected_label]

# # --------------------------
# # 3️⃣ Retrieve Data
# # --------------------------
# line_items = get_line_items_by_grant(selected_grant_id)
# mappings = get_mappings_for_grant(selected_grant_id)
# existing_expenses = get_actual_expenses_for_grant(selected_grant_id, selected_month)

# expense_lookup = {
#     (row['qb_code'], row['line_item_id']): row for row in existing_expenses
# }

# # --------------------------
# # 4️⃣ Build Expense Records (Helper)
# # --------------------------
# def build_expense_records():
#     records = []
#     for _, row in mappings.iterrows():
#         li_name = row["line_item"]
#         qb_code = row["qb_code"]
#         qb_name = row["qb_name"]

#         # Find line_item_id safely
#         line_item_id = next((li['id'] for li in line_items if li['name'] == li_name), None)

#         expense_row = expense_lookup.get((qb_code, line_item_id))

#         records.append({
#             "Line Item": li_name,
#             "QB Code": qb_code,
#             "QB Name": qb_name,
#             "Amount Spent": float(expense_row['amount']) if expense_row else 0.0,
#             "Notes": expense_row['notes'] if expense_row else "",
#             "line_item_id": line_item_id
#         })
#     return records

# records = build_expense_records()

# if not records:
#     st.info("No line item mappings found for this grant.")
#     st.stop()

# entry_df = pd.DataFrame(records).reset_index(drop=True)

# # --------------------------
# # 5️⃣ Expense Table & Context
# # --------------------------
# st.subheader("📟 Monthly Expense Entry Table")
# st.caption("✅ *Edit only the Amount Spent and Notes columns. All other fields are read-only.*")

# gb = GridOptionsBuilder.from_dataframe(entry_df)
# gb.configure_column("Amount Spent", editable=True, type=["numericColumn", "numberColumnFilter"])
# gb.configure_column("Notes", editable=True)
# gb.configure_columns("line_item_id", hide=True)
# grid_options = gb.build()

# grid_response = AgGrid(
#     entry_df,
#     gridOptions=grid_options,
#     update_mode=GridUpdateMode.VALUE_CHANGED,
#     allow_unsafe_jscode=True,
#     fit_columns_on_grid_load=True,
#     theme="streamlit"
# )

# edited_df = grid_response["data"]

# # Show running total
# total_spent = edited_df["Amount Spent"].sum()
# st.info(f"💰 **Total Entered:** ${total_spent:,.2f}")

# # --------------------------
# # 6️⃣ Save Expenses
# # --------------------------
# if st.button("📂 Submit Actual Expenses"):
#     rows_to_save = edited_df[
#         (edited_df["Amount Spent"] != 0) | (edited_df["Notes"].str.strip() != "")
#     ]

#     if rows_to_save.empty:
#         st.info("ℹ️ Nothing to save.")
#     else:
#         for _, row in rows_to_save.iterrows():
#             amount = float(row["Amount Spent"])
#             raw_notes = row.get("Notes", "")
#             notes = raw_notes.strip() if isinstance(raw_notes, str) else ""
#             line_item_id = row["line_item_id"]
#             qb_code = row["QB Code"]

#             # ✅ Safe fallback to skip if no line_item_id
#             if line_item_id and (amount != 0 or notes):
#                 save_actual_expense(
#                     grant_id=selected_grant_id,
#                     month=selected_month,
#                     qb_code=qb_code,
#                     line_item_id=line_item_id,
#                     amount=amount,
#                     notes=notes,
#                     date_submitted=datetime.today().date()
#                 )

#         st.success("✅ Expenses saved.")
#         st.rerun()














