import streamlit as st
import pandas as pd
from helpers.db_utils import (
    get_all_grants, get_grant_by_id, get_grant_summary_data, is_allocation_exceeding_total
)

st.set_page_config(page_title="📋 Grant Summary", layout="wide")

st.title("📋 Grant Summary Dashboard")

# -- Select a Grant
grant_options = get_all_grants()
grant_lookup = {f"{g[1]} ({g[2]})": g[0] for g in grant_options}
selected = st.selectbox("Select a Grant", list(grant_lookup.keys()))

if selected:
    grant_id = grant_lookup[selected]
    grant = get_grant_by_id(grant_id)

    # -- Overview Box
    with st.expander("🔍 Grant Details", expanded=True):
        st.write(f"**Funder:** {grant[2]} ({grant[3]})")
        st.write(f"**Status:** {grant[7]}")
        st.write(f"**Start – End:** {grant[4]} → {grant[5]}")
        st.write(f"**Total Award:** ${grant[6]:,.2f}")
        if grant[8]:
            st.markdown(f"**Notes:** {grant[8]}")

    # -- Allocation vs Total Check
    exceeds, allocated, total = is_allocation_exceeding_total(grant_id)
    st.markdown("---")
    st.subheader("💰 Allocation Summary")
    if exceeds:
        st.warning(f"⚠️ Allocated (${allocated:,.2f}) exceeds total award (${total:,.2f})")
    else:
        st.success(f"✅ Allocated: ${allocated:,.2f} of ${total:,.2f}")

    # -- Summary Table
    st.markdown("### 📊 Line Item Spending Summary")
    df_summary = get_grant_summary_data(grant_id)
    st.dataframe(df_summary, use_container_width=True)

    # -- Optional Chart
    st.markdown("### 📈 Allocation vs Actuals")
    st.bar_chart(df_summary.set_index("Line Item")[["Allocated", "Spent"]])
