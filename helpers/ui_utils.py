# helpers/ui_utils.py
import streamlit as st
from helpers.db_utils import get_grant_summary_data
import pandas as pd

def build_grant_summary_table(grants: list[dict]) -> pd.DataFrame:
    from helpers.db_utils import get_grant_summary_data
    import pandas as pd

    summary_rows = []

    for grant in grants:
        grant_id = grant["id"]
        df = get_grant_summary_data(grant_id)

        # Safeguard: fill in zeros if DataFrame is empty
        if df.empty or "Allocated" not in df.columns:
            allocated = 0.0
            spent = 0.0
        else:
            allocated = df["Allocated"].sum()
            spent = df["Spent"].sum()

        percent_spent = round((spent / allocated) * 100, 1) if allocated else 0.0
        remaining = allocated - spent

        summary_rows.append({
            "Grant": grant["name"],
            "Funder": grant["funder"],
            "Start": grant["start_date"],
            "End": grant["end_date"],
            "Total Award": grant["total_award"],
            "Allocated": allocated,
            "Spent": spent,
            "% Spent": percent_spent,
            "Remaining": remaining,
            "Status": grant["status"]
        })

    return pd.DataFrame(summary_rows)

def inject_sidebar_css():
    """
    Hides the default Streamlit multipage sidebar nav label ("streamlit app").
    """
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)