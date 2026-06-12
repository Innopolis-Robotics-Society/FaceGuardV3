import streamlit as st

st.title("Add an Employee")

camera_picture = st.camera_input("Look into the camera:")
if camera_picture is not None:
    st.image(camera_picture)

name = st.text_input("Enter name:")
time = st.text

access_type = st.radio("Access type:", ["Forever", "Temporary"])
if access_type == "Temporary":
    access_days = st.number_input("Number of days:", min_value=1, step=1)

if st.button("Save"):
    st.success("Saved!")
