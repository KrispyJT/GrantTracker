import streamlit as st
import pandas as pd
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

    # -- Overview Box
    with st.expander("🔍 Grant Details", expanded=True):
        st.write(f"**Funder:** {grant['funder_name']} ({grant['funder_type']})")
        st.write(f"**Status:** {grant['status']}")
        st.write(f"**Start – End:** {grant['start_date']} → {grant['end_date']}")
        st.write(f"**Total Award:** ${grant['total_award']:,.2f}")
        if grant['notes']:
            st.markdown(f"**Notes:** {grant['notes']}")

    # -- Allocation vs Total Check
    exceeds, allocated, total = is_allocation_exceeding_total(grant_id)
    st.markdown("---")
    st.subheader("💰 Allocation Summary")

    # -- Use columns for a clean layout
    col1, col2, col3 = st.columns([1.5, 1.5, 1])

    with col1:
        st.markdown("**💵 Allocated**")
        st.markdown(f"${allocated:,.2f}")

    with col2:
        st.markdown("**🎯 Total Award**")
        st.markdown(f"${total:,.2f}")

    with col3:
        percent = (allocated / total * 100) if total else 0
        st.markdown("**📊 % Allocated**")
        st.markdown(f"{percent:.1f}%")

# -- Visual feedback
    if exceeds:
        st.warning("⚠️ Allocated amount exceeds the total award!")
    else:
        st.success("✅ Allocation is within the total award.")

# -- Add progress bar (always shows)
    if total and total > 0:
        st.progress(min(allocated / total, 1.0))




    # exceeds, allocated, total = is_allocation_exceeding_total(grant_id)
    # st.markdown("---")
    # st.subheader("💰 Allocation Summary")
    # if exceeds:
    #     st.warning(f"⚠️ Allocated (${allocated:,.2f}) exceeds total award (${total:,.2f})")
    # else:
    #     st.success(f"✅ Allocated: ${allocated:,.2f}  of  ${total:,.2f}")

    # -- Summary Table
    st.markdown("### 📊 Line Item Spending Summary")
    df_summary = get_grant_summary_data(grant_id)
    st.dataframe(df_summary, use_container_width=True)

    # -- Optional Chart
    st.markdown("### 📈 Allocation vs Actuals")
    st.bar_chart(df_summary.set_index("Line Item")[["Allocated", "Spent"]])
