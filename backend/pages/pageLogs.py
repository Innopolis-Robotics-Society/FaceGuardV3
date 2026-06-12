import streamlit as st
import numpy as np
import pandas as pd

st.title("Logs")
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col2:
    if st.button("+"):
        st.write("Add a user")
with col4:
    if st.button("-"):
        st.write("Remove the user")