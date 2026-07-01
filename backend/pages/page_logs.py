import streamlit as st
import pandas as pd
import sys
import os
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from db.logs_db import get_all_logs, delete_old_logs, init_db  # noqa: E402

init_db()
delete_old_logs()

st.markdown(
    "<h1 style='text-align: center;'>Access Logs History</h1>", unsafe_allow_html=True
)

logs = get_all_logs()
df = pd.DataFrame(logs)
filter_criteria = st.date_input(
    "Filter by the range of dates",
    (datetime.date.today() - datetime.timedelta(days=2), datetime.date.today()),
    min_value=datetime.date.today() - datetime.timedelta(days=2),
    max_value=datetime.date.today(),
    format="DD.MM.YYYY",
)
if not df.empty:
    df["time"] = (pd.to_datetime(df["time"]).dt.tz_localize("UTC").dt.tz_convert("Europe/Moscow").dt.tz_localize(None))
    if len(filter_criteria) == 2:
        df = df[(df["time"] > (pd.Timestamp(filter_criteria[0]) - datetime.timedelta(days=1))) & (df["time"] < (pd.Timestamp(filter_criteria[1] + datetime.timedelta(days=1))))]
st.dataframe(
    df,
    column_order=["id", "name", "time", "status"],
    use_container_width=True,
    hide_index=True,
)
