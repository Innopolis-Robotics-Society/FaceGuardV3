import streamlit as st
import numpy as np
import cv2
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from faceguard.recognize import create_face_app, extract_embedding_from_frame, cosine_similarity
from db.employees_db import find_closest_embedding
from db.logs_db import add_log

st.markdown("<h1 style='text-align: center;'>Face Recognition Access Control</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    status_indicator = st.empty()
    status_indicator.markdown("Ready")
with col2:
    match_info = st.empty()
    match_info.markdown("Waiting for face.")
with col3:
    similarity_display = st.empty()
    similarity_display.markdown("Similarity.")


img_file_buffer = st.camera_input("Look at the camera for recognition")
if img_file_buffer is not None:

    # convert to opencv format
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    app = create_face_app()
    embedding, face = extract_embedding_from_frame(app, cv2_img)
    
    if embedding is not None:
        match = find_closest_embedding(embedding)
        
        if match:
            emp_id, name, similarity = match
            similarity_percent = similarity * 100
            
            status_indicator.markdown("Access Granted")
            match_info.markdown("name")
            similarity_display.markdown(f"{similarity_percent:.1f}%")
            
            add_log(name, "ACCESS_GRANTED")
            st.success(f"Access Granted for {name} (ID: {emp_id}, Similarity: {similarity_percent:.1f}%)")            
        else:
            status_indicator.markdown("Access Denied")
            match_info.markdown("unknown")

            add_log("UNKNOWN", "ACCESS_DENIED")
            st.error("Access Denied.")
    else:
        st.warning("No face detected.")

# test button (delete later)
st.divider()
st.subheader("Test")

col_a, col_b = st.columns(2)
with col_a:
    if st.button("Test Status"):
        st.info("Trigger a test recognition.")

with col_b:
    if st.button("Reset Status"):
        st.rerun()