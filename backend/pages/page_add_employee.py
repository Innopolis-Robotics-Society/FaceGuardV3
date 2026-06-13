import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.employees_db import add_employees

st.markdown("<h1 style='text-align: center;'>Add an employee</h1>", unsafe_allow_html=True)

camera_picture = st.camera_input("Look into the camera:")
if camera_picture is not None:
    st.image(camera_picture)

name = st.text_input("Enter name:")

access_type = st.radio("Access type:", ["Permanent", "Temporary"])
if access_type == "Temporary":
    access_days = st.number_input("Number of days:", min_value=1, step=1)

if st.button("Save"):
    add_employees(name, access_type)
    st.success("Saved!")
    st.switch_page("page_employees.py")
