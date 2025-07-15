import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from helpers.helpers import generate_month_range
from helpers.db_utils import (
    get_all_grants, get_grant_by_id, get_grant_summary_data, is_allocation_exceeding_total, get_actual_expenses_by_line_item
)

st.set_page_config(page_title="📋 Grant Summary", layout="wide")

st.title("📋 Grant Summary Dashboard")

# -- Select a Grant
grant_options = get_all_grants()
grant_lookup = {f"{g['name']} ({g['funder']})": g['id'] for g in grant_options}
selected = st.selectbox("Select a Grant", list(grant_lookup.keys()))

if selected:
    grant_id = grant_lookup[selected]
    grant = get_grant_by_id(grant_id)

    # ----------------------
    # 📅 Month Range Filter
    # ----------------------
    month_range = generate_month_range(grant['start_date'], grant['end_date'])
    if not month_range:
        st.warning("This grant has no valid month range.")
        st.stop()

    month_label_map = {m: datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in month_range}
    label_to_month = {v: k for k, v in month_label_map.items()}

    with st.sidebar:
        st.markdown("### 📅 Filter by Month Range")
        selected_start_label = st.selectbox("Start Month", list(label_to_month.keys()), index=0)
        selected_end_label = st.selectbox("End Month", list(label_to_month.keys()), index=len(label_to_month)-1)

    start_month = label_to_month[selected_start_label]
    end_month = label_to_month[selected_end_label]

    # ----------------------
    # 📊 Get Summary Data
    # ----------------------
    df_summary = get_grant_summary_data(grant_id, start_month, end_month)
    total_spent = df_summary["Spent"].sum()
    exceeds, allocated, total = is_allocation_exceeding_total(grant_id)

    # ✅ New Metrics
    allocated_remaining = total - allocated
    spending_remaining = total - total_spent
    percent_allocated = (allocated / total * 100) if total else 0
    percent_spent = (total_spent / total * 100) if total else 0

    # Optional: Filter by Line Item
    line_items = ["All"] + df_summary["Line Item"].unique().tolist()
    with st.sidebar:
        selected_item = st.selectbox("🔍 Filter by Line Item", line_items)
    if selected_item != "All":
        df_summary = df_summary[df_summary["Line Item"] == selected_item]

    # Reorder & Format Table Columns
    df_summary = df_summary[["Line Item ID","Line Item", "Spent", "Allocated", "Remaining", "% Spent"]]
    df_summary["Spent"] = df_summary["Spent"].apply(lambda x: f"{x:,.0f}")
    df_summary["Allocated"] = df_summary["Allocated"].apply(lambda x: f"{x:,.0f}")
    df_summary["Remaining"] = df_summary["Remaining"].apply(lambda x: f"{x:,.0f}")

    # ----------------------
    # 💡 Allocation vs Spending (Tabs)
    # ----------------------
    st.markdown("### 📊 Grant Financial Overview")
    tab2, tab1 = st.tabs(["🧾 Spending Progress", "💰 Allocation Overview"])

    with tab2:
        st.subheader("🧾 Spending Progress")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Total Award", f"${total:,.2f}")
        with col2:
            st.metric("💸 Actual Spent", f"${total_spent:,.2f}")
        with col3:
            st.metric("💼 Remaining", f"${spending_remaining:,.2f}")
        with col4:
            st.metric("📊 % Spent", f"{percent_spent:.1f}%")

        st.progress(min(total_spent / total, 1.0) if total else 0)

    with tab1:
        st.subheader("💰 Allocation Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Total Award", f"${total:,.2f}")
        with col2:
            st.metric("💵 Allocated", f"${allocated:,.2f}")
        with col3:
            st.metric("💼 Remaining", f"${allocated_remaining:,.2f}")
        with col4:
            st.metric("📊 % Allocated", f"{percent_allocated:.1f}%")

        st.progress(min(allocated / total, 1.0) if total else 0)

        if exceeds:
            st.warning("⚠️ Allocated amount exceeds the total award!")
        else:
            st.success("✅ Allocation is within the total award.")

    # ----------------------
    # 📋 Line Item Summary Table
    # ----------------------
    st.markdown("### 📋 Line Item Spending Summary")
    st.dataframe(df_summary, use_container_width=True, column_config={"Line Item ID": None})
    st.caption(f"🗓️ Showing actual expenses between **{selected_start_label}** and **{selected_end_label}**.")

    # ----------------------
    # 📈 Bar Chart
    # ----------------------
    st.markdown("### 📈 Allocation vs Actuals")
    st.bar_chart(df_summary.set_index("Line Item")[["Allocated", "Spent"]])

     # 📈 Allocation vs Actuals (Bar Chart)
    st.markdown("### 📈 Allocation vs Actuals")
    st.bar_chart(df_summary.set_index("Line Item")[["Allocated", "Spent"]])

    # 🟢 Donut Chart for Total Spent vs Remaining
    st.markdown("### 🧮 Total Spending Breakdown")
    

    donut_df = pd.DataFrame({
        "Status": ["Spent", "Remaining"],
        "Amount": [total_spent, total - total_spent]
    })

    fig = px.pie(
        donut_df, 
        names="Status", 
        values="Amount", 
        hole=0.4, 
        title="Total Grant Spending"
    )
    st.plotly_chart(fig, use_container_width=True)



    # ----------------------
    # 🔍 Actual Expenses by Line Item (Drilldown)
    # ----------------------
    if selected_item != "All":
        st.markdown(f"### 🧾 Detailed Expenses for: **{selected_item}**")

        try:
            if "Line Item ID" not in df_summary.columns:
                st.warning("⚠️ Line Item ID is missing from summary data.")
            else:
                # Get the line item ID for the selected item
                line_item_id_row = df_summary[df_summary["Line Item"] == selected_item]

                if line_item_id_row.empty:
                    st.warning("⚠️ Could not find a matching Line Item in the summary data.")
                else:
                    line_item_id = int(line_item_id_row["Line Item ID"].iloc[0])

                    df_actuals_raw = get_actual_expenses_by_line_item(grant_id, line_item_id)
                    df_actuals = pd.DataFrame(df_actuals_raw)

                    if df_actuals.empty:
                        st.info("No actual expenses recorded yet for this line item.")
                    else:
                        df_actuals['Month'] = pd.to_datetime(df_actuals['month'], format="%Y-%m")
                        df_actuals['Month Label'] = df_actuals['Month'].dt.strftime('%b %Y')
                        df_actuals = df_actuals.sort_values(by='Month')

                        df_actuals['Amount'] = df_actuals['amount'].apply(lambda x: f"${x:,.2f}")
                        df_actuals['QB Code'] = df_actuals['qb_code']
                        df_actuals['Notes'] = df_actuals['notes']

                        display_cols = ['Month Label', 'Amount', 'QB Code', 'Notes']
                        st.dataframe(df_actuals[display_cols], use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ Error loading detailed expenses: {e}")











#########################
# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from helpers.helpers import generate_month_range
# from helpers.db_utils import (
#     get_all_grants, get_grant_by_id, get_grant_summary_data, is_allocation_exceeding_total
# )

# st.set_page_config(page_title="📋 Grant Summary", layout="wide")

# st.title("📋 Grant Summary Dashboard")

# # -- Select a Grant
# grant_options = get_all_grants()
# grant_lookup = {f"{g['name']} ({g['funder']})": g['id'] for g in grant_options}
# selected = st.selectbox("Select a Grant", list(grant_lookup.keys()))

# if selected:
#     grant_id = grant_lookup[selected]
#     grant = get_grant_by_id(grant_id)

#     # ----------------------
#     # 📅 Month Range Filter
#     # ----------------------
#     month_range = generate_month_range(grant['start_date'], grant['end_date'])
#     if not month_range:
#         st.warning("This grant has no valid month range.")
#         st.stop()

#     month_label_map = {m: datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in month_range}
#     label_to_month = {v: k for k, v in month_label_map.items()}

#     with st.sidebar:
#         st.markdown("### 📅 Filter by Month Range")
#         selected_start_label = st.selectbox("Start Month", list(label_to_month.keys()), index=0)
#         selected_end_label = st.selectbox("End Month", list(label_to_month.keys()), index=len(label_to_month)-1)

#     start_month = label_to_month[selected_start_label]
#     end_month = label_to_month[selected_end_label]

#     # ----------------------
#     # 📊 Get Summary Data
#     # ----------------------
#     df_summary = get_grant_summary_data(grant_id, start_month, end_month)
#     total_spent = df_summary["Spent"].sum()
#     exceeds, allocated, total = is_allocation_exceeding_total(grant_id)
    

#     # Optional: Filter by Line Item
#     line_items = ["All"] + df_summary["Line Item"].unique().tolist()
#     with st.sidebar:
#         selected_item = st.selectbox("🔍 Filter by Line Item", line_items)
#     if selected_item != "All":
#         df_summary = df_summary[df_summary["Line Item"] == selected_item]

#     # Reorder & Format Table Columns
#     df_summary = df_summary[["Line Item", "Spent", "Allocated", "Remaining", "% Spent"]]
#     df_summary["Spent"] = df_summary["Spent"].apply(lambda x: f"{x:,.0f}")
#     df_summary["Allocated"] = df_summary["Allocated"].apply(lambda x: f"{x:,.0f}")
#     df_summary["Remaining"] = df_summary["Remaining"].apply(lambda x: f"{x:,.0f}")

#     # ----------------------
#     # 💡 Allocation vs Spending (Tabs)
#     # ----------------------
#     st.markdown("### 📊 Grant Financial Overview")
#     tab2, tab1 = st.tabs(["🧾 Spending Progress", "💰 Allocation Overview"])

#     # with tab2:
#     #     st.subheader("🧾 Spending Progress")
#     #     col1, col2, col3, col4 = st.columns(4)
#     #     with col1:
#     #         st.metric("🎯 Total Award", f"${total:,.2f}")
#     #     with col2:
#     #         st.metric("💸 Actual Spent", f"${total_spent:,.2f}")
#     #     with col3:
#     #         st.metric("💼 Remaining", f"${spending_remaining:,.2f}")
#     #     with col4:
#     #         st.metric("📊 % Spent", f"{percent_spent:.1f}%")

#     #     st.progress(min(total_spent / total, 1.0) if total else 0)


#     with tab2:
#         st.subheader("🧾 Spending Progress")
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("💸 Actual Spent", f"${total_spent:,.2f}")
#         with col2:
#             st.metric("🎯 Total Award", f"${total:,.2f}")
#         with col3:
#             percent_spent = (total_spent / total * 100) if total else 0
#             st.metric("📊 % Spent", f"{percent_spent:.1f}%")

#         st.progress(min(total_spent / total, 1.0) if total else 0)

#     # with tab1:
#     #     st.subheader("💰 Allocation Summary")
#     #     col1, col2, col3, col4 = st.columns(4)
#     #     with col1:
#     #         st.metric("🎯 Total Award", f"${total:,.2f}")
#     #     with col2:
#     #         st.metric("💵 Allocated", f"${allocated:,.2f}")
#     #     with col3:
#     #         st.metric("💼 Remaining", f"${allocated_remaining:,.2f}")
#     #     with col4:
#     #         st.metric("📊 % Allocated", f"{percent_allocated:.1f}%")

#     #     st.progress(min(allocated / total, 1.0) if total else 0)

#     #     if exceeds:
#     #         st.warning("⚠️ Allocated amount exceeds the total award!")
#     #     else:
#     #         st.success("✅ Allocation is within the total award.")


#     with tab1:
#         st.subheader("💰 Allocation Summary")
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("💵 Allocated", f"${allocated:,.2f}")
#         with col2:
#             st.metric("🎯 Total Award", f"${total:,.2f}")
#         with col3:
#             percent_allocated = (allocated / total * 100) if total else 0
#             st.metric("📊 % Allocated", f"{percent_allocated:.1f}%")

#         st.progress(min(allocated / total, 1.0) if total else 0)

#         if exceeds:
#             st.warning("⚠️ Allocated amount exceeds the total award!")
#         else:
#             st.success("✅ Allocation is within the total award.")

    

#     # ----------------------
#     # 📋 Line Item Summary Table
#     # ----------------------
#     st.markdown("### 📋 Line Item Spending Summary")
#     st.dataframe(df_summary, use_container_width=True)
#     st.caption(f"🗓️ Showing actual expenses between **{selected_start_label}** and **{selected_end_label}**.")

#     # ----------------------
#     # 📈 Bar Chart
#     # ----------------------
#     st.markdown("### 📈 Allocation vs Actuals")
#     st.bar_chart(df_summary.set_index("Line Item")[["Allocated", "Spent"]])




########################################
# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from helpers.helpers import generate_month_range
# from helpers.db_utils import (
#     get_all_grants, get_grant_by_id, get_grant_summary_data, is_allocation_exceeding_total
# )

# st.set_page_config(page_title="📋 Grant Summary", layout="wide")

# st.title("📋 Grant Summary Dashboard")

# # -- Select a Grant
# grant_options = get_all_grants()
# grant_lookup = {f"{g['name']} ({g['funder']})": g['id'] for g in grant_options}
# selected = st.selectbox("Select a Grant", list(grant_lookup.keys()))

# if selected:
#     grant_id = grant_lookup[selected]
#     grant = get_grant_by_id(grant_id)

#     # ----------------------
#     # 📅 Month Range Filter
#     # ----------------------
#     month_range = generate_month_range(grant['start_date'], grant['end_date'])
#     if not month_range:
#         st.warning("This grant has no valid month range.")
#         st.stop()

#     month_label_map = {m: datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in month_range}
#     label_to_month = {v: k for k, v in month_label_map.items()}

#     with st.expander("📅 Filter by Month Range", expanded=True):
#         col1, col2 = st.columns(2)
#         with col1:
#             selected_start_label = st.selectbox("Start Month", list(label_to_month.keys()), index=0)
#         with col2:
#             selected_end_label = st.selectbox("End Month", list(label_to_month.keys()), index=len(label_to_month)-1)

#     start_month = label_to_month[selected_start_label]
#     end_month = label_to_month[selected_end_label]

#     # ----------------------
#     # 🔍 Grant Details
#     # ----------------------
#     with st.expander("🔍 Grant Details", expanded=True):
#         st.markdown(f"""
#         **Funder:** {grant['funder_name']} ({grant['funder_type']})  
#         **Status:** {grant['status']}  
#         **Start – End:** {grant['start_date']} → {grant['end_date']}  
#         **Total Award:** ${grant['total_award']:,.2f}
#         """)
#         if grant['notes']:
#             st.markdown(f"**Notes:** {grant['notes']}")

#     # ----------------------
#     # 📊 Get Summary Data
#     # ----------------------
#     df_summary = get_grant_summary_data(grant_id, start_month, end_month)
#     total_spent = df_summary["Spent"].sum()
#     exceeds, allocated, total = is_allocation_exceeding_total(grant_id)

#     # ----------------------
#     # 💡 Allocation vs Spending (Tabs)
#     # ----------------------
#     st.markdown("### 📊 Grant Financial Overview")
#     tab1, tab2 = st.tabs(["💰 Allocation Overview", "🧾 Spending Progress"])

#     with tab1:
#         st.subheader("💰 Allocation Summary")
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("💵 Allocated", f"${allocated:,.2f}")
#         with col2:
#             st.metric("🎯 Total Award", f"${total:,.2f}")
#         with col3:
#             percent_allocated = (allocated / total * 100) if total else 0
#             st.metric("📊 % Allocated", f"{percent_allocated:.1f}%")

#         st.progress(min(allocated / total, 1.0) if total else 0)

#         if exceeds:
#             st.warning("⚠️ Allocated amount exceeds the total award!")
#         else:
#             st.success("✅ Allocation is within the total award.")

#     with tab2:
#         st.subheader("🧾 Spending Progress")
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("💸 Actual Spent", f"${total_spent:,.2f}")
#         with col2:
#             st.metric("🎯 Total Award", f"${total:,.2f}")
#         with col3:
#             percent_spent = (total_spent / total * 100) if total else 0
#             st.metric("📊 % Spent", f"{percent_spent:.1f}%")

#         st.progress(min(total_spent / total, 1.0) if total else 0)

#     # ----------------------
#     # 📋 Line Item Summary Table
#     # ----------------------
#     st.markdown("### 📋 Line Item Spending Summary")
#     st.dataframe(df_summary, use_container_width=True)
#     st.caption(f"🗓️ Showing actual expenses between **{selected_start_label}** and **{selected_end_label}**.")

#     # ----------------------
#     # 📈 Bar Chart
#     # ----------------------
#     st.markdown("### 📈 Allocation vs Actuals")
#     st.bar_chart(df_summary.set_index("Line Item")[["Allocated", "Spent"]])


#############################################
# ORIGINAL
# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from dateutil.relativedelta import relativedelta
# from helpers.helpers import generate_month_range
# from helpers.db_utils import (
#     get_all_grants, get_grant_by_id, get_grant_summary_data, is_allocation_exceeding_total
# )

# st.set_page_config(page_title="📋 Grant Summary", layout="wide")



# st.title("📋 Grant Summary Dashboard")

# # -- Select a Grant
# grant_options = get_all_grants()
# grant_lookup = {f"{g['name']} ({g['funder']})": g['id'] for g in grant_options}
# selected = st.selectbox("Select a Grant", list(grant_lookup.keys()))

# if selected:
#     grant_id = grant_lookup[selected]
#     grant = get_grant_by_id(grant_id)

#     # ----------------------
#     # 📅 Month Range Filter
#     # ----------------------
#     month_range = generate_month_range(grant['start_date'], grant['end_date'])
#     if not month_range:
#         st.warning("This grant has no valid month range.")
#         st.stop()

#     # Human-friendly month labels
#     month_label_map = {m: datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in month_range}
#     label_to_month = {v: k for k, v in month_label_map.items()}

#     st.markdown("### 📅 Filter by Month Range")
#     col_start, col_end = st.columns(2)
#     with col_start:
#         selected_start_label = st.selectbox("Start Month", list(label_to_month.keys()), index=0)
#     with col_end:
#         selected_end_label = st.selectbox("End Month", list(label_to_month.keys()), index=len(label_to_month)-1)

#     start_month = label_to_month[selected_start_label]
#     end_month = label_to_month[selected_end_label]


#     # -- Overview Box
#     with st.expander("🔍 Grant Details", expanded=True):
#         st.write(f"**Funder:** {grant['funder_name']} ({grant['funder_type']})")
#         st.write(f"**Status:** {grant['status']}")
#         st.write(f"**Start – End:** {grant['start_date']} → {grant['end_date']}")
#         st.write(f"**Total Award:** ${grant['total_award']:,.2f}")
#         if grant['notes']:
#             st.markdown(f"**Notes:** {grant['notes']}")

#     # -- Allocation vs Total Check
#     exceeds, allocated, total = is_allocation_exceeding_total(grant_id)
#     st.markdown("---")
#     st.subheader("💰 Allocation Summary")

#     # -- Use columns for a clean layout
#     col1, col2, col3 = st.columns([1.5, 1.5, 1])

#     with col1:
#         st.markdown("**💵 Allocated**")
#         st.markdown(f"${allocated:,.2f}")

#     with col2:
#         st.markdown("**🎯 Total Award**")
#         st.markdown(f"${total:,.2f}")

#     with col3:
#         percent = (allocated / total * 100) if total else 0
#         st.markdown("**📊 % Allocated**")
#         st.markdown(f"{percent:.1f}%")

# # -- Visual feedback
#     if exceeds:
#         st.warning("⚠️ Allocated amount exceeds the total award!")
#     else:
#         st.success("✅ Allocation is within the total award.")

# # -- Add progress bar (always shows)
#     if total and total > 0:
#         st.progress(min(allocated / total, 1.0))

   
#     # -- Summary Table
#     st.markdown("### 📊 Line Item Spending Summary")
#     df_summary = get_grant_summary_data(grant_id, start_month, end_month)
#     total_spent = df_summary["Spent"].sum()

#     st.dataframe(df_summary, use_container_width=True)
#     st.caption(f"🗓️ Showing actual expenses between **{selected_start_label}** and **{selected_end_label}**.")


#     # -- Actual Spending Progress Bar
#     st.markdown("### 🧾 Spending Progress")

#     col_spent, col_total, col_percent = st.columns([1.5, 1.5, 1])
#     with col_spent:
#         st.markdown("**💸 Actual Spent**")
#         st.markdown(f"${total_spent:,.2f}")
#     with col_total:
#         st.markdown("**🎯 Total Award**")
#         st.markdown(f"${total:,.2f}")
#     with col_percent:
#         spent_pct = (total_spent / total * 100) if total else 0
#         st.markdown("**📊 % Spent**")
#         st.markdown(f"{spent_pct:.1f}%")

#     st.progress(min(total_spent / total, 1.0) if total else 0)



#     # -- Optional Chart
#     st.markdown("### 📈 Allocation vs Actuals")
#     st.bar_chart(df_summary.set_index("Line Item")[["Allocated", "Spent"]])
