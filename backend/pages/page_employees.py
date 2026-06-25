import streamlit as st
import base64
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db.employees_db import connect_to_db, init_db, load_employees, delete_employee, add_employees
st.markdown("<h1 style='text-align: center;'>Employees</h1>", unsafe_allow_html=True)
init_db()
df = load_employees()
statuses = ["All"] + df["status"].unique().tolist()
selected_status = st.selectbox("Filter by status", statuses)

if selected_status != "All":
    df = df[df["status"] == selected_status]

if "table_version" not in st.session_state:
    st.session_state["table_version"] = 0

def reset_table():
    old_key = f"employees_table_{st.session_state['table_version']}"
    if old_key in st.session_state:
        del st.session_state[old_key]
    st.session_state["table_version"] += 1

@st.dialog("Confirm deletion")
def confirm_delete():
    st.write("Are you sure you want to delete selected employees?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            for id in selected_rows["id"]:
                delete_employee(id)
            reset_table()
            st.rerun()
    with col2:
        if st.button("No"):
            reset_table()
            st.rerun()
            
if df is not None:
    df.insert(0, "Select", False)
    table_key = f"employees_table_{st.session_state['table_version']}"
    edited_df = st.data_editor(
        df,
        hide_index=True,
        disabled=["id", "name", "registration_date", "status"],
        column_config={
            "id": None,
            "status": st.column_config.SelectboxColumn("Status", options=["Permanent", "Temporary"]),
            "name": "Employee's name",
            "registration_date": "Registration date",
            "start_date": "Start date",
            "expiration_date": "Expiration date"
        },
        key=table_key
    )
    selected_rows = edited_df[edited_df["Select"] == True]
    if not selected_rows.empty:
        col_cancel, col_delete, _ = st.columns([1, 1, 4])
        with col_cancel:
            if st.button("Cancel"):
                reset_table()
                st.rerun()
        with col_delete:
            if st.button("Delete"):
                confirm_delete()
