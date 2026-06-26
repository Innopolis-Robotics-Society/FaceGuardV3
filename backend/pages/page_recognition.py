import streamlit as st
import numpy as np
import cv2
import sys
import os
import av
import threading
import time
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from faceguard.recognize import create_face_app, extract_embedding_from_frame, LivenessDetector
from faceguard.detect import draw_face_box
from db.employees_db import find_closest_embedding
from db.logs_db import add_log

st.markdown("<h1 style='text-align: center;'>Face Recognition Access Control</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    status_indicator = st.empty()
    status_indicator.markdown("### Status\nReady")
with col2:
    match_info = st.empty()
    match_info.markdown("### Name\nWaiting for face.")
with col3:
    similarity_display = st.empty()
    similarity_display.markdown("### Similarity\n-")

class RecognitionVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.app = create_face_app()
        self.liveness_detector = LivenessDetector()
        self.lock = threading.Lock()
        
        self.status = "No face detected"
        self.name = "Unknown"
        self.similarity = 0.0
        
        self.last_log_time = 0
        self.last_logged_name = None
        self.last_logged_status = None
        self.log_cooldown = 5.0
        
        self.last_face = None
        self.last_draw_text = ""
        self.last_draw_color = (0, 255, 0)

        self.current_frame = None
        self.last_frame_time = time.time()
        self.is_running = True
        
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()

    def _process_loop(self):
        while self.is_running:
            time.sleep(1.0)
            
            with self.lock:
                if self.current_frame is None:
                    continue
                img = self.current_frame.copy()
                
            current_time = time.time()
            
            if current_time - self.last_frame_time > 5.0:
                self.is_running = False
                break
                
            try:
                embedding, face, status_code = extract_embedding_from_frame(self.app, self.liveness_detector, img)
                
                with self.lock:
                    if status_code == "real" and embedding is not None:
                        match = find_closest_embedding(embedding)
                        if match:
                            emp_id, name, similarity = match
                            self.status = "Access Granted"
                            self.name = name
                            self.similarity = similarity * 100
                            self.last_face = face
                            self.last_draw_text = f"{name} ({similarity * 100:.1f}%)"
                            self.last_draw_color = (0, 255, 0)
                            
                            if (current_time - self.last_log_time > self.log_cooldown or 
                                self.last_logged_name != name or 
                                self.last_logged_status != "ACCESS_GRANTED"):
                                try:
                                    add_log(name, "ACCESS_GRANTED")
                                    self.last_log_time = current_time
                                    self.last_logged_name = name
                                    self.last_logged_status = "ACCESS_GRANTED"
                                except Exception:
                                    pass
                        else:
                            self.status = "Access Denied"
                            self.name = "Unknown"
                            self.similarity = 0.0
                            self.last_face = face
                            self.last_draw_text = "Access Denied"
                            self.last_draw_color = (0, 0, 255)
                            
                            if (current_time - self.last_log_time > self.log_cooldown or 
                                self.last_logged_name != "UNKNOWN" or 
                                self.last_logged_status != "ACCESS_DENIED"):
                                try:
                                    add_log("UNKNOWN", "ACCESS_DENIED")
                                    self.last_log_time = current_time
                                    self.last_logged_name = "UNKNOWN"
                                    self.last_logged_status = "ACCESS_DENIED"
                                except Exception:
                                    pass
                                    
                    elif status_code == "spoof":
                        self.status = "SPOOF DETECTED"
                        self.name = "Unknown"
                        self.similarity = 0.0
                        self.last_face = face
                        self.last_draw_text = "SPOOF DETECTED"
                        self.last_draw_color = (0, 0, 255)
                        
                        if (current_time - self.last_log_time > self.log_cooldown or 
                            self.last_logged_status != "SPOOF_ATTEMPT"):
                            try:
                                add_log("UNKNOWN", "SPOOF_ATTEMPT")
                                self.last_log_time = current_time
                                self.last_logged_name = "UNKNOWN"
                                self.last_logged_status = "SPOOF_ATTEMPT"
                            except Exception:
                                pass
                                
                    elif status_code == "bad_face":
                        self.status = "Please look straight at the camera"
                        self.name = "Unknown"
                        self.similarity = 0.0
                        self.last_face = face
                        self.last_draw_text = "Look straight"
                        self.last_draw_color = (0, 255, 255)
                    else:
                        self.status = "No face detected"
                        self.name = "Unknown"
                        self.similarity = 0.0
                        self.last_face = None
            except Exception as e:
                print(f"Error in background processing: {e}")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        
        with self.lock:
            self.current_frame = img
            self.last_frame_time = time.time()
            
            if self.last_face is not None:
                draw_face_box(img, self.last_face, self.last_draw_text, color=self.last_draw_color)
                
        return av.VideoFrame.from_ndarray(img, format="bgr24")

ctx = webrtc_streamer(
    key="recognize",
    video_processor_factory=RecognitionVideoProcessor,
    media_stream_constraints={
        "video": {
            "width": {"min": 640, "ideal": 1280},
            "height": {"min": 480, "ideal": 720},
            "frameRate": {"ideal": 1, "max": 2} 
        }, 
        "audio": False
    },
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
)

if ctx.state.playing:
    while ctx.state.playing:
        if ctx.video_processor:
            with ctx.video_processor.lock:
                status = ctx.video_processor.status
                name = ctx.video_processor.name
                similarity = ctx.video_processor.similarity
                
            if status == "Access Granted":
                status_indicator.markdown(f"### Status\n<span style='color:green; font-weight:bold'>{status}</span>", unsafe_allow_html=True)
                match_info.markdown(f"### Name\n{name}")
                similarity_display.markdown(f"### Similarity\n{similarity:.1f}%")
            elif status in ["Access Denied", "SPOOF DETECTED"]:
                status_indicator.markdown(f"### Status\n<span style='color:red; font-weight:bold'>{status}</span>", unsafe_allow_html=True)
                match_info.markdown(f"### Name\n{name}")
                similarity_display.markdown("### Similarity\n-")
            else:
                status_indicator.markdown(f"### Status\n{status}")
                match_info.markdown("### Name\n-")
                similarity_display.markdown("### Similarity\n-")
                
        time.sleep(0.1)

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
