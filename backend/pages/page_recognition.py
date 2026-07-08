import streamlit as st
import sys
import os
import av
import threading
import time
import logging
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from faceguard.recognize import (  # noqa: E402
    create_face_app,
    extract_embedding_from_frame,
    LivenessDetector,
)
import leds  # noqa: E402
from db.employees_db import find_closest_embedding  # noqa: E402
from db.logs_db import add_log  # noqa: E402

logger = logging.getLogger(__name__)

st.markdown(
    "<h1 style='text-align: center;'>Face Recognition Access Control</h1>",
    unsafe_allow_html=True,
)

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


@st.cache_resource
def get_models():
    return create_face_app(), LivenessDetector(threshold=0.40)


class RecognitionVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.app, self.liveness_detector = get_models()
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

        self.unrecognized_frames = 0
        self.access_granted_until = 0

        self.current_frame = None
        self.last_frame_time = time.time()
        self.is_running = True

        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()

    def _process_loop(self):
        while self.is_running:
            time.sleep(1)

            with self.lock:
                if self.current_frame is None:
                    continue
                img = self.current_frame.copy()

            current_time = time.time()

            if current_time - self.last_frame_time > 30.0:
                self.is_running = False
                break

            try:
                embedding, face, status_code = extract_embedding_from_frame(
                    self.app, self.liveness_detector, img
                )

                with self.lock:
                    if status_code == "real" and embedding is not None:
                        if self.last_logged_status != "RECOGNIZING":
                            leds.start_recognizing()
                            self.last_logged_status = "RECOGNIZING"
                        match = find_closest_embedding(embedding)
                        if match:
                            self.unrecognized_frames = 0
                            self.access_granted_until = current_time + 3.0
                            emp_id, name, similarity = match
                            self.status = "Access Granted"
                            self.name = name
                            self.similarity = similarity * 100
                            self.last_face = face
                            self.last_draw_text = f"{name} ({similarity * 100:.1f}%)"
                            self.last_draw_color = (0, 255, 0)
                            if (
                                current_time - self.last_log_time > self.log_cooldown
                                or self.last_logged_name != name
                                or self.last_logged_status != "ACCESS_GRANTED"
                            ):
                                leds.access_granted()
                                try:
                                    add_log(name, "ACCESS_GRANTED")
                                    self.last_log_time = current_time
                                    self.last_logged_name = name
                                    self.last_logged_status = "ACCESS_GRANTED"
                                except Exception:
                                    logger.warning(
                                        "Failed to write access granted log",
                                        exc_info=True,
                                    )
                        else:
                            if current_time < self.access_granted_until:
                                pass
                            else:
                                self.unrecognized_frames += 1
                                if self.unrecognized_frames >= 2:
                                    self.status = "Access Denied"
                                    self.name = "Unknown"
                                    self.similarity = 0.0
                                    self.last_face = face
                                    self.last_draw_text = "Access Denied"
                                    self.last_draw_color = (0, 0, 255)
                                    if (
                                        current_time - self.last_log_time > self.log_cooldown
                                        or self.last_logged_name != "UNKNOWN"
                                        or self.last_logged_status != "ACCESS_DENIED"
                                    ):
                                        leds.access_denied()
                                        try:
                                            add_log("UNKNOWN", "ACCESS_DENIED")
                                            self.last_log_time = current_time
                                            self.last_logged_name = "UNKNOWN"
                                            self.last_logged_status = "ACCESS_DENIED"
                                        except Exception:
                                            logger.warning(
                                                "Failed to write access denied log",
                                                exc_info=True,
                                            )
                                else:
                                    self.status = "Recognizing..."
                                    self.name = "..."
                                    self.similarity = 0.0
                                    self.last_face = face
                                    self.last_draw_text = "Recognizing..."
                                    self.last_draw_color = (255, 255, 0)

                    elif status_code == "spoof":
                        if current_time < self.access_granted_until:
                            pass
                        else:
                            self.unrecognized_frames = 0
                            self.status = "SPOOF DETECTED"
                            self.name = "Unknown"
                            self.similarity = 0.0
                            self.last_face = face
                            self.last_draw_text = "SPOOF DETECTED"
                            self.last_draw_color = (0, 0, 255)
                            if (
                                current_time - self.last_log_time > self.log_cooldown
                                or self.last_logged_status != "SPOOF_ATTEMPT"
                            ):
                                leds.access_denied()
                                try:
                                    add_log("UNKNOWN", "SPOOF_ATTEMPT")
                                    self.last_log_time = current_time
                                    self.last_logged_name = "UNKNOWN"
                                    self.last_logged_status = "SPOOF_ATTEMPT"
                                except Exception:
                                    logger.warning(
                                        "Failed to write spoof attempt log", exc_info=True
                                    )

                    elif status_code == "bad_face":
                        if current_time < self.access_granted_until:
                            pass
                        else:
                            self.unrecognized_frames = 0
                            self.status = "Please look straight at the camera"
                            self.name = "Unknown"
                            self.similarity = 0.0
                            self.last_face = face
                            self.last_draw_text = "Look straight"
                            self.last_draw_color = (0, 255, 255)
                            if self.last_logged_status != "BAD_FACE":
                                leds.bad_frame()
                                self.last_logged_status = "BAD_FACE"
                    else:
                        if current_time < self.access_granted_until:
                            pass
                        else:
                            self.unrecognized_frames = 0
                            self.status = "No face detected"
                            self.name = "Unknown"
                            self.similarity = 0.0
                            self.last_face = None
                            if self.last_logged_status != "NO_FACE":
                                leds.all_off()
                                self.last_logged_status = "NO_FACE"
            except Exception as e:
                print(f"Error in background processing: {e}")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        with self.lock:
            self.current_frame = img
            self.last_frame_time = time.time()

        return av.VideoFrame.from_ndarray(img, format="bgr24")


ctx = webrtc_streamer(
    key="recognize",
    video_processor_factory=RecognitionVideoProcessor,
    media_stream_constraints={
        "video": {
            "width": {"min": 640, "ideal": 1280},
            "height": {"min": 480, "ideal": 720},
            "frameRate": {"ideal": 1, "max": 1},
        },
        "audio": False,
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

if ctx.state.playing:
    while ctx.state.playing:
        vp = ctx.video_processor
        if vp:
            with vp.lock:
                status = vp.status
                name = vp.name
                similarity = vp.similarity

            if status == "Access Granted":
                status_indicator.markdown(
                    f"### Status\n<span style='color:green; font-weight:bold'>{status}</span>",
                    unsafe_allow_html=True,
                )
                match_info.markdown(f"### Name\n{name}")
                similarity_display.markdown(f"### Similarity\n{similarity:.1f}%")
            elif status in ["Access Denied", "SPOOF DETECTED"]:
                status_indicator.markdown(
                    f"### Status\n<span style='color:red; font-weight:bold'>{status}</span>",
                    unsafe_allow_html=True,
                )
                match_info.markdown(f"### Name\n{name}")
                similarity_display.markdown("### Similarity\n-")
            else:
                status_indicator.markdown(f"### Status\n{status}")
                match_info.markdown("### Name\n-")
                similarity_display.markdown("### Similarity\n-")

        time.sleep(0.1)
