import streamlit as st
import sys
import os
import av
import threading
import time as time_module
from datetime import date, time, datetime
import streamlit.components.v1 as components
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.employees_db import add_employees, find_closest_embedding  # noqa: E402
import leds  # noqa: E402

from faceguard.recognize import (  # noqa: E402
    create_face_app,
    extract_embedding_from_frame,
    average_embeddings,
    LivenessDetector,
)
from faceguard.detect import draw_face_box  # noqa: E402

st.markdown(
    "<h1 style='text-align: center;'>Add an employee</h1>", unsafe_allow_html=True
)


class EnrollVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.app = create_face_app()
        self.liveness_detector = LivenessDetector()
        self.embeddings = []
        self.lock = threading.Lock()
        self.status = "Initializing camera..."

        self.current_frame = None
        self.last_frame_time = time_module.time()
        self.is_running = True

        self.last_face = None
        self.last_draw_text = ""
        self.last_draw_color = (0, 255, 0)

        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()

    def _process_loop(self):
        while self.is_running:
            time_module.sleep(0.3)

            with self.lock:
                if self.current_frame is None:
                    continue
                img = self.current_frame.copy()

            current_time = time_module.time()
            if current_time - self.last_frame_time > 5.0:
                self.is_running = False
                break

            with self.lock:
                if len(self.embeddings) >= 30:
                    self.status = "Finished! 30 embeddings collected."
                    self.last_face = None
                    continue

            try:
                embedding, face, status_code = extract_embedding_from_frame(
                    self.app, self.liveness_detector, img
                )
                if status_code == "spoof":
                    from faceguard.recognize import get_face_embedding

                    embedding = get_face_embedding(face)
                    status_code = "real"

                with self.lock:
                    if status_code == "real" and embedding is not None:
                        self.embeddings.append(embedding)
                        leds.registration_active()
                        self.status = (
                            f"Collecting embeddings: {len(self.embeddings)}/30"
                        )
                        self.last_face = face
                        self.last_draw_text = f"Collecting: {len(self.embeddings)}/30"
                        self.last_draw_color = (0, 255, 0)
                    elif status_code == "bad_face":
                        self.status = "Please look straight at the camera"
                        self.last_face = face
                        self.last_draw_text = "Look straight"
                        self.last_draw_color = (0, 255, 255)
                        leds.bad_frame()
                    else:
                        self.status = "No face detected"
                        self.last_face = None
                        leds.all_off()
            except Exception as e:
                print(f"Background thread error: {e}")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        with self.lock:
            self.current_frame = img
            self.last_frame_time = time_module.time()

            if self.last_face is not None:
                draw_face_box(
                    img, self.last_face, self.last_draw_text, color=self.last_draw_color
                )

        return av.VideoFrame.from_ndarray(img, format="bgr24")


if "enroll_embedding" not in st.session_state:
    st.session_state["enroll_embedding"] = None

ctx = webrtc_streamer(
    key="enroll",
    video_processor_factory=EnrollVideoProcessor,
    media_stream_constraints={
        "video": {
            "width": {"min": 640, "ideal": 1280},
            "height": {"min": 480, "ideal": 720},
            "frameRate": {"ideal": 3, "max": 5},
        },
        "audio": False,
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
)
success_placeholder = st.empty()
error_placeholder = st.empty()
try_placeholder = st.empty()
progress_bar = st.progress(0)
status_indicator = st.empty()
if ctx.video_processor:
    while ctx.state.playing:
        with ctx.video_processor.lock:
            embeddings_count = len(ctx.video_processor.embeddings)
            status = ctx.video_processor.status
            collected_embeddings = list(ctx.video_processor.embeddings)

        progress_bar.progress(min(embeddings_count / 30, 1.0))
        status_indicator.markdown(f"**Status:** {status}")

        if embeddings_count >= 30:
            st.session_state["enroll_embedding"] = average_embeddings(
                collected_embeddings
            )
            leds.registration_done()
            success_placeholder.success("Face data successfully collected!")
            break

        time_module.sleep(0.1)

embedding = st.session_state.get("enroll_embedding", None)
if embedding is not None:
    match = find_closest_embedding(embedding)
    if match:
        error_placeholder.error(f"Face already exists for {match[1]}")
        if try_placeholder.button("Try again"):
            with ctx.video_processor.lock:
                ctx.video_processor.embeddings = []
                ctx.video_processor.status = "Initializing camera..."
                ctx.video_processor.last_face = None
            st.session_state["enroll_embedding"] = None
            success_placeholder.empty()
            error_placeholder.empty()
            try_placeholder.empty()
            progress_bar.empty()
            status_indicator.empty()
            st.rerun()
    else:
        name = st.text_input("Enter a name:")

        access_type = st.radio("Access type:", ["Permanent", "Temporary"])

        start_date = None
        expiration_date = None
        start_time = None
        expiration_time = None

        if access_type == "Temporary":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start date:", value=date.today(), min_value=date.today()
                )
                start_time = st.time_input("Start time:", value=time(0, 0), step=60)
            with col2:
                expiration_date = st.date_input(
                    "Expiration date:", value=date.today(), min_value=date.today()
                )
                expiration_time = st.time_input("Expiration time:", value=time(23, 59), step=60)

            start_dt = datetime.combine(start_date, start_time)
            expiration_dt = datetime.combine(expiration_date, expiration_time)

            if expiration_dt <= start_dt:
                st.error("Expiration must be after start date and time.")

        if st.button("Save"):
            if embedding is None:
                st.error("No face detected. Please capture a face.")
            elif not name:
                st.error("Please enter a name.")
            elif access_type == "Temporary" and expiration_dt <= start_dt:
                st.error("Please fix the access dates before saving.")
            else:
                final_start = start_dt if access_type == "Temporary" else None
                final_expiration = expiration_dt if access_type == "Temporary" else None
                if add_employees(name, access_type, embedding, final_start, final_expiration):
                    st.success("Saved!")
                    st.session_state["enroll_embedding"] = None
                    st.switch_page("page_employees.py")
