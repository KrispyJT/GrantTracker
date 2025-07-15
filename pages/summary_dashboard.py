import streamlit as st
import pandas as pd
from datetime import datetime
from helpers.helpers import generate_month_range
from helpers.db_utils import (
    get_all_grants, get_grant_by_id, get_grant_summary_data, is_allocation_exceeding_total
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

    with st.expander("📅 Filter by Month Range", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_start_label = st.selectbox("Start Month", list(label_to_month.keys()), index=0)
        with col2:
            selected_end_label = st.selectbox("End Month", list(label_to_month.keys()), index=len(label_to_month)-1)

    start_month = label_to_month[selected_start_label]
    end_month = label_to_month[selected_end_label]

    # ----------------------
    # 🔍 Grant Details
    # ----------------------
    with st.expander("🔍 Grant Details", expanded=True):
        st.markdown(f"""
        **Funder:** {grant['funder_name']} ({grant['funder_type']})  
        **Status:** {grant['status']}  
        **Start – End:** {grant['start_date']} → {grant['end_date']}  
        **Total Award:** ${grant['total_award']:,.2f}
        """)
        if grant['notes']:
            st.markdown(f"**Notes:** {grant['notes']}")

    # ----------------------
    # 📊 Get Summary Data
    # ----------------------
    df_summary = get_grant_summary_data(grant_id, start_month, end_month)
    total_spent = df_summary["Spent"].sum()
    exceeds, allocated, total = is_allocation_exceeding_total(grant_id)

    # ----------------------
    # 💡 Allocation vs Spending (Tabs)
    # ----------------------
    st.markdown("### 📊 Grant Financial Overview")
    tab1, tab2 = st.tabs(["💰 Allocation Overview", "🧾 Spending Progress"])

    with tab1:
        st.subheader("💰 Allocation Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💵 Allocated", f"${allocated:,.2f}")
        with col2:
            st.metric("🎯 Total Award", f"${total:,.2f}")
        with col3:
            percent_allocated = (allocated / total * 100) if total else 0
            st.metric("📊 % Allocated", f"{percent_allocated:.1f}%")

        st.progress(min(allocated / total, 1.0) if total else 0)

        if exceeds:
            st.warning("⚠️ Allocated amount exceeds the total award!")
        else:
            st.success("✅ Allocation is within the total award.")

    with tab2:
        st.subheader("🧾 Spending Progress")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💸 Actual Spent", f"${total_spent:,.2f}")
        with col2:
            st.metric("🎯 Total Award", f"${total:,.2f}")
        with col3:
            percent_spent = (total_spent / total * 100) if total else 0
            st.metric("📊 % Spent", f"{percent_spent:.1f}%")

        st.progress(min(total_spent / total, 1.0) if total else 0)

    # ----------------------
    # 📋 Line Item Summary Table
    # ----------------------
    st.markdown("### 📋 Line Item Spending Summary")
    st.dataframe(df_summary, use_container_width=True)
    st.caption(f"🗓️ Showing actual expenses between **{selected_start_label}** and **{selected_end_label}**.")

    # ----------------------
    # 📈 Bar Chart
    # ----------------------
    st.markdown("### 📈 Allocation vs Actuals")
    st.bar_chart(df_summary.set_index("Line Item")[["Allocated", "Spent"]])



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
