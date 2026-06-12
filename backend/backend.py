import streamlit as st
import pandas as pd
import numpy as np

st.title('Faceguard')

col1, col2 = st.columns(2)

with col1:
    if st.button("+", use_container_width=True):
        st.write("add the user")
    
with col2:
    if st.button("-", use_container_width=True):
        st.write("delete the user")
        
