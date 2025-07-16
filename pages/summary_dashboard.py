
######### 4th 
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from helpers.helpers import generate_month_range
from helpers.db_utils import (
    get_all_grants, get_grant_by_id, get_grant_summary_data,
    is_allocation_exceeding_total, get_actual_expenses_by_line_item
)

if not st.session_state.get("authenticated"):
    st.warning("🔒 Please log in to access this page.")
    st.stop()

st.set_page_config(page_title="📋 Grant Summary", layout="wide")
st.title("📋 Grant Summary Dashboard")

# 1. Select Grant
grants = get_all_grants()
grant_lookup = {f"{g['name']} ({g['funder']})": g['id'] for g in grants}
selected_grant_name = st.selectbox("Select a Grant", list(grant_lookup.keys()))

granted_id = grant_lookup[selected_grant_name]
grant = get_grant_by_id(granted_id)

# 2. Sidebar Month Filter
month_range = generate_month_range(grant['start_date'], grant['end_date'])
month_label_map = {m: datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in month_range}
label_to_month = {v: k for k, v in month_label_map.items()}

with st.sidebar:
    st.markdown("### 📅 Filter by Month Range")
    start_label = st.selectbox("Start Month", list(label_to_month.keys()), index=0)
    end_label = st.selectbox("End Month", list(label_to_month.keys()), index=len(label_to_month)-1)

start_month, end_month = label_to_month[start_label], label_to_month[end_label]

# 3. Summary Data + Allocation Checks
df_summary = get_grant_summary_data(granted_id, start_month, end_month)
total_spent = df_summary["Spent"].sum()
exceeds, allocated, total_award = is_allocation_exceeding_total(granted_id)

remaining_allocation = total_award - allocated
remaining_spending = total_award - total_spent

percent_allocated = (allocated / total_award) * 100 if total_award else 0
percent_spent = (total_spent / total_award) * 100 if total_award else 0

# 4. 📊 Spending Metrics
st.markdown("## 🧾 Spending Metrics")
c1, c2, c3, c4 = st.columns(4)
c1.metric("🎯 Total Award", f"${total_award:,.2f}")
c2.metric("🪙 Actual Spent", f"${total_spent:,.2f}")
c3.metric("💼 Remaining", f"${remaining_spending:,.2f}")
c4.metric("📈 % Spent", f"{percent_spent:.1f}%")

st.progress(min(percent_spent / 100, 1.0))

# 5. 💰 Allocation Metrics
st.markdown("## 💰 Allocation Metrics")
a1, a2, a3, a4 = st.columns(4)
a1.metric("🎯 Total Award", f"${total_award:,.2f}")
a2.metric("💵 Allocated", f"${allocated:,.2f}")
a3.metric("💼 Remaining", f"${remaining_allocation:,.2f}")
a4.metric("📊 % Allocated", f"{percent_allocated:.1f}%")

st.progress(min(percent_allocated / 100, 1.0))

if exceeds:
    st.error("⚠️ Allocation exceeds total award amount.")
else:
    st.success("✅ Allocation is within the total award.")

# 6. 📋 Line Item Summary
st.markdown("## 📋 Line Item Spending Summary")

with st.sidebar:
    line_items_all = ["All"] + df_summary["Line Item"].unique().tolist()
    selected_item = st.selectbox("🔍 Filter by Line Item", line_items_all)

if selected_item != "All":
    df_summary = df_summary[df_summary["Line Item"] == selected_item]

# Format table fields
df_summary_fmt = df_summary.copy()
df_summary_fmt["Spent"] = df_summary_fmt["Spent"].apply(lambda x: f"{x:,.0f}")
df_summary_fmt["Allocated"] = df_summary_fmt["Allocated"].apply(lambda x: f"{x:,.0f}")
df_summary_fmt["Remaining"] = df_summary_fmt["Remaining"].apply(lambda x: f"{x:,.0f}")

st.dataframe(df_summary_fmt[["Line Item", "Spent", "Allocated", "Remaining", "% Spent"]], use_container_width=True)
st.caption(f"📆 Showing actual expenses between **{start_label}** and **{end_label}**.")

# 7. Tabs for Drilldown and Visuals
st.markdown("## 🔎 Drilldown & Visuals")
tab1, tab2 = st.tabs(["🧾 Detailed Expenses", "📊 Visuals"])

with tab1:
    if selected_item != "All":
        st.markdown(f"#### 🧾 Detailed Expenses for: **{selected_item}**")
        try:
            line_item_id_row = df_summary[df_summary["Line Item"] == selected_item]
            if not line_item_id_row.empty:
                line_item_id = int(line_item_id_row["Line Item ID"].iloc[0])
                df_actuals = pd.DataFrame(get_actual_expenses_by_line_item(granted_id, line_item_id))

                if not df_actuals.empty:
                    df_actuals["Month"] = pd.to_datetime(df_actuals["month"], format="%Y-%m")
                    df_actuals["Month Label"] = df_actuals["Month"].dt.strftime('%b %Y')
                    df_actuals["Amount"] = df_actuals["amount"].apply(lambda x: f"${x:,.2f}")
                    df_actuals = df_actuals.sort_values("Month")
                    st.dataframe(df_actuals[["Month Label", "Amount", "qb_code", "notes"]], use_container_width=True)
                else:
                    st.info("No actual expenses recorded yet for this line item.")
        except Exception as e:
            st.error(f"⚠️ Error loading detailed expenses: {e}")
    else:
        st.info("Please select a line item to drill down.")

with tab2:
    st.markdown("#### 📊 Allocation vs Actuals")
    try:
        df_viz = df_summary.copy()
        df_viz["Allocated"] = df_viz["Allocated"].astype(str).str.replace(",", "").astype(float)
        df_viz["Spent"] = df_viz["Spent"].astype(str).str.replace(",", "").astype(float)

        fig_bar = go.Figure(data=[
            go.Bar(name="Allocated", x=df_viz["Allocated"], y=df_viz["Line Item"], orientation='h'),
            go.Bar(name="Spent", x=df_viz["Spent"], y=df_viz["Line Item"], orientation='h')
        ])
        fig_bar.update_layout(
            barmode='group', xaxis_title="Amount ($)", yaxis_title="Line Item",
            height=400, template="plotly_dark", legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("#### 🥯 Spending Breakdown (Donut)")
        fig_donut = go.Figure(data=[go.Pie(
            labels=["Spent", "Remaining"],
            values=[total_spent, remaining_spending],
            hole=0.6,
            marker=dict(colors=["#636EFA", "#E5ECF6"])
        )])
        fig_donut.update_layout(showlegend=True, height=350, margin=dict(t=10, b=10))
        st.plotly_chart(fig_donut, use_container_width=True)

    except Exception as e:
        st.error(f"Error rendering visuals: {e}")



#############################8888888888888888888888888888888888
###### 3rd almost there
# import streamlit as st
# import plotly.graph_objects as go
# import plotly.express as px
# import pandas as pd
# from datetime import datetime
# from helpers.helpers import generate_month_range
# from helpers.db_utils import (
#     get_all_grants, get_grant_by_id, get_grant_summary_data,
#     is_allocation_exceeding_total, get_actual_expenses_by_line_item
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

#     df_summary = get_grant_summary_data(grant_id, start_month, end_month)
#     total_spent = df_summary["Spent"].sum()
#     exceeds, allocated, total = is_allocation_exceeding_total(grant_id)

#     allocated_remaining = total - allocated
#     spending_remaining = total - total_spent
#     percent_allocated = (allocated / total * 100) if total else 0
#     percent_spent = (total_spent / total * 100) if total else 0

#     # ----------------------
#     # 📊 Metrics Overview
#     # ----------------------
#     st.markdown("### 📊 Grant Financial Overview")
#     col1, col2, col3, col4 = st.columns(4)
#     col1.metric("🎯 Total Award", f"${total:,.2f}")
#     col2.metric("💵 Allocated", f"${allocated:,.2f}")
#     col3.metric("💸 Spent", f"${total_spent:,.2f}")
#     col4.metric("📊 % Spent", f"{percent_spent:.1f}%")

#     st.progress(min(total_spent / total, 1.0) if total else 0)

#     # ----------------------
#     # 📋 Line Item Spending Summary
#     # ----------------------
#     st.markdown("### 📋 Line Item Spending Summary")

#     line_items = ["All"] + df_summary["Line Item"].unique().tolist()
#     with st.sidebar:
#         selected_item = st.selectbox("🔍 Filter by Line Item", line_items)

#     if selected_item != "All":
#         df_summary = df_summary[df_summary["Line Item"] == selected_item]

#     df_summary = df_summary[["Line Item ID", "Line Item", "Spent", "Allocated", "Remaining", "% Spent"]]
#     df_summary["Spent"] = df_summary["Spent"].apply(lambda x: f"{x:,.0f}")
#     df_summary["Allocated"] = df_summary["Allocated"].apply(lambda x: f"{x:,.0f}")
#     df_summary["Remaining"] = df_summary["Remaining"].apply(lambda x: f"{x:,.0f}")

#     st.dataframe(df_summary, use_container_width=True, column_config={"Line Item ID": None})
#     st.caption(f"🗓️ Showing actual expenses between **{selected_start_label}** and **{selected_end_label}**.")

#     # ----------------------
#     # 📊 Drilldown + Visuals Tabs
#     # ----------------------
#     st.markdown("### 🔍 Drilldown & Visuals")
#     tab1, tab2 = st.tabs(["🧾 Detailed Expenses", "📊 Visuals"])

#     with tab1:
#         if selected_item != "All":
#             st.markdown(f"### 🧾 Detailed Expenses for: **{selected_item}**")
#             try:
#                 line_item_id_row = df_summary[df_summary["Line Item"] == selected_item]
#                 if line_item_id_row.empty:
#                     st.warning("⚠️ Could not find a matching Line Item in the summary data.")
#                 else:
#                     line_item_id = int(line_item_id_row["Line Item ID"].iloc[0])
#                     df_actuals_raw = get_actual_expenses_by_line_item(grant_id, line_item_id)
#                     df_actuals = pd.DataFrame(df_actuals_raw)

#                     if df_actuals.empty:
#                         st.info("No actual expenses recorded yet for this line item.")
#                     else:
#                         df_actuals['Month'] = pd.to_datetime(df_actuals['month'], format="%Y-%m")
#                         df_actuals['Month Label'] = df_actuals['Month'].dt.strftime('%b %Y')
#                         df_actuals = df_actuals.sort_values(by='Month')
#                         df_actuals['Amount'] = df_actuals['amount'].apply(lambda x: f"${x:,.2f}")
#                         df_actuals['QB Code'] = df_actuals['qb_code']
#                         df_actuals['Notes'] = df_actuals['notes']
#                         display_cols = ['Month Label', 'Amount', 'QB Code', 'Notes']
#                         st.dataframe(df_actuals[display_cols], use_container_width=True)
#             except Exception as e:
#                 st.error(f"⚠️ Error loading detailed expenses: {e}")
#         else:
#             st.info("Select a specific line item to view detailed expenses.")

#     with tab2:
#         st.markdown("#### 📈 Allocation vs Actuals")
#         allocated_vals = df_summary["Allocated"].str.replace(",", "").astype(float)
#         spent_vals = df_summary["Spent"].str.replace(",", "").astype(float)

#         fig_bar = go.Figure(data=[
#             go.Bar(name="Allocated", x=allocated_vals, y=df_summary["Line Item"], orientation='h'),
#             go.Bar(name="Spent", x=spent_vals, y=df_summary["Line Item"], orientation='h')
#         ])
#         fig_bar.update_layout(
#             barmode='group',
#             xaxis_title="Amount ($)",
#             yaxis_title="Line Item",
#             height=400,
#             margin=dict(t=30, b=30),
#             template="plotly_dark",
#             legend=dict(orientation="h", y=-0.2)
#         )
#         st.plotly_chart(fig_bar, use_container_width=True)

#         st.markdown("#### 🥯 Spending Breakdown (Donut)")
#         fig = go.Figure(data=[go.Pie(
#             labels=["Spent", "Remaining"],
#             values=[total_spent, spending_remaining],
#             hole=0.6,
#             marker=dict(colors=["#636EFA", "#E5ECF6"])
#         )])
#         fig.update_layout(showlegend=True, height=350, margin=dict(t=10, b=10, l=0, r=0))
#         st.plotly_chart(fig, use_container_width=True)






################### 2nd iteration not the best
# import streamlit as st
# import plotly.graph_objects as go
# import plotly.express as px
# import pandas as pd
# from datetime import datetime
# from helpers.helpers import generate_month_range
# from helpers.db_utils import (
#     get_all_grants, get_grant_by_id, get_grant_summary_data, is_allocation_exceeding_total, get_actual_expenses_by_line_item
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

#     # 📅 Month Range Filter
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

#     # 📊 Get Summary Data
#     df_summary = get_grant_summary_data(grant_id, start_month, end_month)
#     total_spent = df_summary["Spent"].sum()
#     exceeds, allocated, total = is_allocation_exceeding_total(grant_id)

#     # ✅ Metric Calculations
#     allocated_remaining = total - allocated
#     spending_remaining = total - total_spent
#     percent_allocated = (allocated / total * 100) if total else 0
#     percent_spent = (total_spent / total * 100) if total else 0

#     # Line Item Filter
#     line_items = ["All"] + df_summary["Line Item"].unique().tolist()
#     with st.sidebar:
#         selected_item = st.selectbox("🔍 Filter by Line Item", line_items)
#     if selected_item != "All":
#         df_summary = df_summary[df_summary["Line Item"] == selected_item]

#     # Format for visuals and table
#     df_summary = df_summary[["Line Item ID", "Line Item", "Spent", "Allocated", "Remaining", "% Spent"]]
#     df_summary["Spent"] = df_summary["Spent"].apply(lambda x: f"{x:,.0f}")
#     df_summary["Allocated"] = df_summary["Allocated"].apply(lambda x: f"{x:,.0f}")
#     df_summary["Remaining"] = df_summary["Remaining"].apply(lambda x: f"{x:,.0f}")

#     # ----------------------------------------
#     # 🔖 Main Tabs: Overview | Summary | Visuals
#     # ----------------------------------------
#     tab_overview, tab_summary, tab_visuals = st.tabs(["📊 Overview", "📋 Line Item Summary", "📈 Visuals"])

#     # --------------------
#     # 📊 Overview Tab
#     # --------------------
#     with tab_overview:
#         st.subheader("🧾 Spending Metrics")
#         col1, col2, col3, col4 = st.columns(4)
#         with col1:
#             st.metric("🎯 Total Award", f"${total:,.2f}")
#         with col2:
#             st.metric("💸 Actual Spent", f"${total_spent:,.2f}")
#         with col3:
#             st.metric("💼 Remaining", f"${spending_remaining:,.2f}")
#         with col4:
#             st.metric("📊 % Spent", f"{percent_spent:.1f}%")
#         st.progress(min(total_spent / total, 1.0) if total else 0)

#         st.subheader("💰 Allocation Metrics")
#         col1, col2, col3, col4 = st.columns(4)
#         with col1:
#             st.metric("🎯 Total Award", f"${total:,.2f}")
#         with col2:
#             st.metric("💵 Allocated", f"${allocated:,.2f}")
#         with col3:
#             st.metric("💼 Remaining", f"${allocated_remaining:,.2f}")
#         with col4:
#             st.metric("📊 % Allocated", f"{percent_allocated:.1f}%")
#         st.progress(min(allocated / total, 1.0) if total else 0)

#         if exceeds:
#             st.warning("⚠️ Allocated amount exceeds the total award!")
#         else:
#             st.success("✅ Allocation is within the total award.")

#     # --------------------
#     # 📋 Line Item Summary Tab
#     # --------------------
#     with tab_summary:
#         st.markdown("### 📋 Line Item Spending Summary")
#         st.dataframe(df_summary, use_container_width=True, column_config={"Line Item ID": None})
#         st.caption(f"🗓️ Showing actual expenses between **{selected_start_label}** and **{selected_end_label}**.")

#         # Drilldown
#         if selected_item != "All":
#             st.markdown(f"### 🧾 Detailed Expenses for: **{selected_item}**")

#             try:
#                 if "Line Item ID" not in df_summary.columns:
#                     st.warning("⚠️ Line Item ID is missing from summary data.")
#                 else:
#                     line_item_id_row = df_summary[df_summary["Line Item"] == selected_item]
#                     if line_item_id_row.empty:
#                         st.warning("⚠️ Could not find a matching Line Item in the summary data.")
#                     else:
#                         line_item_id = int(line_item_id_row["Line Item ID"].iloc[0])
#                         df_actuals_raw = get_actual_expenses_by_line_item(grant_id, line_item_id)
#                         df_actuals = pd.DataFrame(df_actuals_raw)

#                         if df_actuals.empty:
#                             st.info("No actual expenses recorded yet for this line item.")
#                         else:
#                             df_actuals['Month'] = pd.to_datetime(df_actuals['month'], format="%Y-%m")
#                             df_actuals['Month Label'] = df_actuals['Month'].dt.strftime('%b %Y')
#                             df_actuals = df_actuals.sort_values(by='Month')
#                             df_actuals['Amount'] = df_actuals['amount'].apply(lambda x: f"${x:,.2f}")
#                             df_actuals['QB Code'] = df_actuals['qb_code']
#                             df_actuals['Notes'] = df_actuals['notes']
#                             display_cols = ['Month Label', 'Amount', 'QB Code', 'Notes']
#                             st.dataframe(df_actuals[display_cols], use_container_width=True)
#             except Exception as e:
#                 st.error(f"⚠️ Error loading detailed expenses: {e}")

#     # --------------------
#     # 📈 Visuals Tab
#     # --------------------
#     with tab_visuals:
#         st.markdown("### 📈 Allocation vs Actuals (Bar Chart)")
#         allocated_vals = df_summary["Allocated"].str.replace(",", "").astype(float)
#         spent_vals = df_summary["Spent"].str.replace(",", "").astype(float)

#         fig_bar = go.Figure(data=[
#             go.Bar(name="Allocated", x=allocated_vals, y=df_summary["Line Item"], orientation='h'),
#             go.Bar(name="Spent", x=spent_vals, y=df_summary["Line Item"], orientation='h')
#         ])
#         fig_bar.update_layout(
#             barmode='group',
#             xaxis_title="Amount ($)",
#             yaxis_title="Line Item",
#             height=400,
#             margin=dict(t=30, b=30),
#             template="plotly_dark",
#             legend=dict(orientation="h", y=-0.2)
#         )
#         st.plotly_chart(fig_bar, use_container_width=True)

#         st.markdown("### 🧮 Total Spending Breakdown")
#         donut_df = pd.DataFrame({
#             "Status": ["Spent", "Remaining"],
#             "Amount": [total_spent, total - total_spent]
#         })
#         fig_donut = px.pie(
#             donut_df,
#             names="Status",
#             values="Amount",
#             hole=0.4,
#             title="Total Grant Spending"
#         )
#         st.plotly_chart(fig_donut, use_container_width=True)

#         st.markdown("### 🥯 Spending Distribution")
#         fig_dist = go.Figure(data=[go.Pie(
#             labels=["Spent", "Remaining"],
#             values=[total_spent, spending_remaining],
#             hole=0.6,
#             marker=dict(colors=["#636EFA", "#E5ECF6"])
#         )])
#         fig_dist.update_layout(
#             showlegend=True,
#             margin=dict(t=10, b=10, l=0, r=0),
#             height=350,
#         )
#         st.plotly_chart(fig_dist, use_container_width=True)

# ORGINAL - working mode 
###############################
# import streamlit as st
# import plotly.graph_objects as go
# import plotly.express as px
# import pandas as pd
# from datetime import datetime
# from helpers.helpers import generate_month_range
# from helpers.db_utils import (
#     get_all_grants, get_grant_by_id, get_grant_summary_data, is_allocation_exceeding_total, get_actual_expenses_by_line_item
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

#     # ✅ New Metrics
#     allocated_remaining = total - allocated
#     spending_remaining = total - total_spent
#     percent_allocated = (allocated / total * 100) if total else 0
#     percent_spent = (total_spent / total * 100) if total else 0

#     # Optional: Filter by Line Item
#     line_items = ["All"] + df_summary["Line Item"].unique().tolist()
#     with st.sidebar:
#         selected_item = st.selectbox("🔍 Filter by Line Item", line_items)
#     if selected_item != "All":
#         df_summary = df_summary[df_summary["Line Item"] == selected_item]

#     # Reorder & Format Table Columns
#     df_summary = df_summary[["Line Item ID","Line Item", "Spent", "Allocated", "Remaining", "% Spent"]]
#     df_summary["Spent"] = df_summary["Spent"].apply(lambda x: f"{x:,.0f}")
#     df_summary["Allocated"] = df_summary["Allocated"].apply(lambda x: f"{x:,.0f}")
#     df_summary["Remaining"] = df_summary["Remaining"].apply(lambda x: f"{x:,.0f}")

#     # ----------------------
#     # 💡 Allocation vs Spending (Tabs)
#     # ----------------------
#     st.markdown("### 📊 Grant Financial Overview")
#     tab2, tab1 = st.tabs(["🧾 Spending Progress", "💰 Allocation Overview"])

#     with tab2:
#         st.subheader("🧾 Spending Progress")
#         col1, col2, col3, col4 = st.columns(4)
#         with col1:
#             st.metric("🎯 Total Award", f"${total:,.2f}")
#         with col2:
#             st.metric("💸 Actual Spent", f"${total_spent:,.2f}")
#         with col3:
#             st.metric("💼 Remaining", f"${spending_remaining:,.2f}")
#         with col4:
#             st.metric("📊 % Spent", f"{percent_spent:.1f}%")

#         st.progress(min(total_spent / total, 1.0) if total else 0)

#     with tab1:
#         st.subheader("💰 Allocation Summary")
#         col1, col2, col3, col4 = st.columns(4)
#         with col1:
#             st.metric("🎯 Total Award", f"${total:,.2f}")
#         with col2:
#             st.metric("💵 Allocated", f"${allocated:,.2f}")
#         with col3:
#             st.metric("💼 Remaining", f"${allocated_remaining:,.2f}")
#         with col4:
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
#     st.dataframe(df_summary, use_container_width=True, column_config={"Line Item ID": None})
#     st.caption(f"🗓️ Showing actual expenses between **{selected_start_label}** and **{selected_end_label}**.")

#     # ----------------------
#     # 📈 Bar Chart
#     # ----------------------
#     st.markdown("### 📈 Allocation vs Actuals")


#     # Clean numeric columns by removing commas and converting to float
#     allocated_vals = df_summary["Allocated"].str.replace(",", "").astype(float)
#     spent_vals = df_summary["Spent"].str.replace(",", "").astype(float)

#     fig_bar = go.Figure(data=[
#         go.Bar(name="Allocated", x=allocated_vals, y=df_summary["Line Item"], orientation='h'),
#         go.Bar(name="Spent", x=spent_vals, y=df_summary["Line Item"], orientation='h')
#     ])

#     fig_bar.update_layout(
#         barmode='group',
#         xaxis_title="Amount ($)",
#         yaxis_title="Line Item",
#         height=400,
#         margin=dict(t=30, b=30),
#         template="plotly_dark",
#         legend=dict(orientation="h", y=-0.2)
#     )

#     st.plotly_chart(fig_bar, use_container_width=True)


#     # 🟢 Donut Chart for Total Spent vs Remaining
#     st.markdown("### 🧮 Total Spending Breakdown")
    

#     donut_df = pd.DataFrame({
#         "Status": ["Spent", "Remaining"],
#         "Amount": [total_spent, total - total_spent]
#     })

#     fig = px.pie(
#         donut_df, 
#         names="Status", 
#         values="Amount", 
#         hole=0.4, 
#         title="Total Grant Spending"
#     )
#     st.plotly_chart(fig, use_container_width=True)

#     # ----------------------
#     # 🥯 Donut Chart: Spending Distribution
#     # ----------------------
#     st.markdown("### 🥯 Spending Distribution")

#     fig = go.Figure(data=[go.Pie(
#         labels=["Spent", "Remaining"],
#         values=[total_spent, spending_remaining],
#         hole=0.6,
#         marker=dict(colors=["#636EFA", "#E5ECF6"])
#     )])
#     fig.update_layout(
#         showlegend=True,
#         margin=dict(t=10, b=10, l=0, r=0),
#         height=350,
#     )

#     st.plotly_chart(fig, use_container_width=True)




#     # ----------------------
#     # 🔍 Actual Expenses by Line Item (Drilldown)
#     # ----------------------
#     if selected_item != "All":
#         st.markdown(f"### 🧾 Detailed Expenses for: **{selected_item}**")

#         try:
#             if "Line Item ID" not in df_summary.columns:
#                 st.warning("⚠️ Line Item ID is missing from summary data.")
#             else:
#                 # Get the line item ID for the selected item
#                 line_item_id_row = df_summary[df_summary["Line Item"] == selected_item]

#                 if line_item_id_row.empty:
#                     st.warning("⚠️ Could not find a matching Line Item in the summary data.")
#                 else:
#                     line_item_id = int(line_item_id_row["Line Item ID"].iloc[0])

#                     df_actuals_raw = get_actual_expenses_by_line_item(grant_id, line_item_id)
#                     df_actuals = pd.DataFrame(df_actuals_raw)

#                     if df_actuals.empty:
#                         st.info("No actual expenses recorded yet for this line item.")
#                     else:
#                         df_actuals['Month'] = pd.to_datetime(df_actuals['month'], format="%Y-%m")
#                         df_actuals['Month Label'] = df_actuals['Month'].dt.strftime('%b %Y')
#                         df_actuals = df_actuals.sort_values(by='Month')

#                         df_actuals['Amount'] = df_actuals['amount'].apply(lambda x: f"${x:,.2f}")
#                         df_actuals['QB Code'] = df_actuals['qb_code']
#                         df_actuals['Notes'] = df_actuals['notes']

#                         display_cols = ['Month Label', 'Amount', 'QB Code', 'Notes']
#                         st.dataframe(df_actuals[display_cols], use_container_width=True)

#         except Exception as e:
#             st.error(f"⚠️ Error loading detailed expenses: {e}")











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


