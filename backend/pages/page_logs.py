import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from db.logs_db import get_all_logs, delete_old_logs, init_db  # noqa: E402

init_db()
delete_old_logs()

st.markdown(
    "<h1 style='text-align: center;'>Access Logs History</h1>", unsafe_allow_html=True
)

logs = get_all_logs()
df = pd.DataFrame(logs)
if not df.empty:
    df["time"] = (pd.to_datetime(df["time"]).dt.tz_localize("UTC").dt.tz_convert("Europe/Moscow").dt.tz_localize(None))

st.dataframe(
    df,
    column_order=["id", "name", "time", "status"],
    use_container_width=True,
    hide_index=True,
)