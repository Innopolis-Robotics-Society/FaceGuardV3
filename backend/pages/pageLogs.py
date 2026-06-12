import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(__file__))

from logs_db import get_all_logs, delete_old_logs
delete_old_logs()

st.markdown("<h1 style='text-align: center;'>Access Logs History</h1>", unsafe_allow_html=True)

logs = get_all_logs()
if not logs:
    st.markdown("<h5 style='text-align: center;'>No logs found</h5>", unsafe_allow_html=True)
else:
    st.dataframe(
        logs,
        column_order=["id", "name", "time", "status"],
        use_container_width=True,
        hide_index=True
    )