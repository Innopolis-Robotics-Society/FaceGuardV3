import streamlit as st
import numpy as np
import sys
import cv2
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.employees_db import add_employees
from faceguard.recognize import create_face_app, extract_embedding_from_frame, get_face_embedding
from faceguard.detect import select_closest_face, is_good_face

st.markdown("<h1 style='text-align: center;'>Add an employee</h1>", unsafe_allow_html=True)

camera_picture = st.camera_input("Look into the camera:")
embedding = None

if camera_picture is not None:
    img_bytes = np.frombuffer(camera_picture.getvalue(), np.uint8)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    
    app = create_face_app()
    faces = app.get(img)
    face = select_closest_face(faces)

    if face is None:
        st.warning("No face detected.")
    elif len(faces) > 1:
        st.warning("Multiple faces detected. Please show only one face.")
    elif not is_good_face(face, img):
        st.warning("Face quality too low. Please ensure your face is clearly visible.")
    else:
        embedding = get_face_embedding(face)
        st.success("Face detected.")
        st.image(camera_picture)

name = st.text_input("Enter a name:")

access_type = st.radio("Access type:", ["Permanent", "Temporary"])
if access_type == "Temporary":
    access_days = st.number_input("Number of days:", min_value=1, step=1)

if st.button("Save"):
    if embedding is None:
        st.error("No face detected. Please capture a face.")
    elif not name:
        st.error("Please enter a name.")
    else:
        if access_type == "Temporary": days = access_days
        else: days = None
        add_employees(name, access_type, embedding, days)
        st.success("Saved!")
        st.switch_page("page_employees.py")
