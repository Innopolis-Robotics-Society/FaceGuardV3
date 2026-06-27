import streamlit as st
import sys
import os
from datetime import date
import av
import threading
import time
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.employees_db import add_employees  # noqa: E402

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
        self.last_frame_time = time.time()
        self.is_running = True

        self.last_face = None
        self.last_draw_text = ""
        self.last_draw_color = (0, 255, 0)

        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()

    def _process_loop(self):
        while self.is_running:
            time.sleep(0.3)

            with self.lock:
                if self.current_frame is None:
                    continue
                img = self.current_frame.copy()

            current_time = time.time()
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
                    else:
                        self.status = "No face detected"
                        self.last_face = None
            except Exception as e:
                print(f"Background thread error: {e}")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        with self.lock:
            self.current_frame = img
            self.last_frame_time = time.time()

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

if ctx.video_processor:
    progress_bar = st.progress(0)
    status_indicator = st.empty()

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
            st.success("Face data successfully collected!")
            break

        time.sleep(0.1)

embedding = st.session_state.get("enroll_embedding", None)


name = st.text_input("Enter a name:")

access_type = st.radio("Access type:", ["Permanent", "Temporary"])

start_date = None
expiration_date = None

if access_type == "Temporary":
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date:", value=date.today(), min_value=date.today()
        )
    with col2:
        expiration_date = st.date_input(
            "Expiration date:", value=date.today(), min_value=date.today()
        )

    if expiration_date < start_date:
        st.error("Expiration date must be after start date.")

if st.button("Save"):
    if embedding is None:
        st.error("No face detected. Please capture a face.")
    elif not name:
        st.error("Please enter a name.")
    elif access_type == "Temporary" and (not start_date or not expiration_date):
        st.error("Please set both start and expiration dates for temporary access.")
    else:
        add_employees(name, access_type, embedding, start_date, expiration_date)
        st.success("Saved!")
        st.session_state["enroll_embedding"] = None
        st.switch_page("page_employees.py")
