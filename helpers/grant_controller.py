# helpers/grant_controller.py

from .db_utils import (
    add_funder_if_missing,
    get_funder_id,
    add_grant,
    update_grant,
    delete_grant,
    grant_exists,
    get_grant_by_id
)

def handle_add_grant(grant_name, funder_name, funder_type, start_date, end_date, total_award, status, notes):
    if grant_exists(grant_name):
        raise ValueError("Grant with this name already exists.")

    add_funder_if_missing(funder_name, funder_type)
    funder_id = get_funder_id(funder_name)
    add_grant(grant_name, funder_id, start_date, end_date, total_award, status, notes)

def handle_update_grant(grant_id, grant_name, funder_name, funder_type, start_date, end_date, total_award, status, notes):
    add_funder_if_missing(funder_name, funder_type)
    funder_id = get_funder_id(funder_name)
    update_grant(grant_id, grant_name, funder_id, start_date, end_date, total_award, status, notes)

def handle_delete_grant(grant_id):
    delete_grant(grant_id)

def get_grant_details(grant_id):
    return get_grant_by_id(grant_id)














# # helpers/grant_controller.py
# import streamlit as st
# import pandas as pd
# from .db_utils import (
#     add_funder_if_missing,
#     get_funder_id,
#     add_grant,
#     update_grant,
#     delete_grant,
#     grant_exists
# )


# def add_new_grant(grant_name, funder_name, funder_type, start_date, end_date, total_award, status, notes):
#     if grant_exists(grant_name):
#         raise ValueError("Grant with this name already exists.")

#     add_funder_if_missing(funder_name, funder_type)
#     funder_id = get_funder_id(funder_name)

#     add_grant(grant_name, funder_id, start_date, end_date, total_award, status, notes)

# def update_existing_grant(grant_id, grant_name, funder_name, funder_type, start_date, end_date, total_award, status, notes):
#     add_funder_if_missing(funder_name, funder_type)
#     funder_id = get_funder_id(funder_name)

#     update_grant(grant_id, grant_name, funder_id, start_date, end_date, total_award, status, notes)

# def remove_grant(grant_id):
#     delete_grant(grant_id)
