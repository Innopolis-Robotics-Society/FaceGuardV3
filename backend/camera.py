"""USB camera capture with latest-frame-only buffering.

The capture worker is deliberately independent from FastAPI.  OpenCV camera
operations are blocking, so the worker owns ``VideoCapture`` and publishes a
single replaceable frame instead of allowing an unbounded queue to build up.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
import sys
import threading
import time
from typing import Callable, Mapping, Optional

import cv2
import numpy as np


logger = logging.getLogger(__name__)


class CameraError(RuntimeError):
    """Base error raised by the backend camera stream."""


class CameraConfigurationError(CameraError):
    """Raised when camera environment settings are invalid."""


class CameraOpenError(CameraError):
    """Raised when OpenCV cannot open the configured camera."""


class CameraReadError(CameraError):
    """Raised when the capture worker cannot obtain a usable frame."""


@dataclass(frozen=True)
class CameraSettings:
    source: str = "browser"
    index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    jpeg_quality: int = 60
    buffer_size: int = 1
    read_retry_delay: float = 0.05
    max_read_failures: int = 5
    frame_timeout: float = 2.0

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "CameraSettings":
        values = os.environ if environ is None else environ
        source = values.get("CAMERA_SOURCE", "browser").strip().lower()
        if source not in {"browser", "backend"}:
            raise CameraConfigurationError(
                "CAMERA_SOURCE must be either 'browser' or 'backend'"
            )

        raw_index = values.get("CAMERA_INDEX", "0").strip()
        try:
            index = int(raw_index)
        except ValueError as error:
            raise CameraConfigurationError("CAMERA_INDEX must be an integer") from error
        if index < 0:
            raise CameraConfigurationError("CAMERA_INDEX must be non-negative")

        return cls(source=source, index=index)


@dataclass(frozen=True)
class CameraFrame:
    sequence: int
    captured_at: float
    image: np.ndarray
    capture_ms: float


class LatestFrameCamera:
    """Own a VideoCapture and retain only its newest successful frame."""

    # A stuck native V4L2 read must fail closed. The worker releases this
    # process-wide lease only after it has actually exited.
    _device_lease = threading.Lock()

    def __init__(
        self,
        settings: CameraSettings,
        capture_factory: Optional[Callable[..., object]] = None,
    ):
        self.settings = settings
        self._capture_factory = capture_factory
        self._capture = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._condition = threading.Condition()
        self._release_lock = threading.Lock()
        self._lease_state_lock = threading.Lock()
        self._owns_device_lease = False
        self._released = True
        self._latest: Optional[CameraFrame] = None
        self._sequence = 0
        self._terminal_error: Optional[CameraError] = None

    def _create_capture(self):
        factory = self._capture_factory or cv2.VideoCapture
        v4l2 = getattr(cv2, "CAP_V4L2", None)
        if sys.platform.startswith("linux") and v4l2 is not None:
            return factory(self.settings.index, v4l2)
        return factory(self.settings.index)

    @staticmethod
    def _set_property(capture, property_name: str, value) -> None:
        property_id = getattr(cv2, property_name, None)
        if property_id is not None:
            try:
                configured = capture.set(property_id, value)
                if configured is False:
                    logger.warning(
                        "Camera did not accept property %s=%s",
                        property_name,
                        value,
                    )
            except Exception:
                logger.warning(
                    "Unable to configure camera property %s=%s",
                    property_name,
                    value,
                    exc_info=True,
                )

    def _configure_capture(self, capture) -> None:
        fourcc_factory = getattr(cv2, "VideoWriter_fourcc", None)
        if fourcc_factory is not None:
            self._set_property(capture, "CAP_PROP_FOURCC", fourcc_factory(*"MJPG"))
        self._set_property(capture, "CAP_PROP_FRAME_WIDTH", self.settings.width)
        self._set_property(capture, "CAP_PROP_FRAME_HEIGHT", self.settings.height)
        self._set_property(capture, "CAP_PROP_FPS", self.settings.fps)
        self._set_property(capture, "CAP_PROP_BUFFERSIZE", self.settings.buffer_size)

    @staticmethod
    def _capture_value(capture, property_name: str):
        property_id = getattr(cv2, property_name, None)
        getter = getattr(capture, "get", None)
        if property_id is None or getter is None:
            return None
        try:
            return getter(property_id)
        except Exception:
            logger.debug("Unable to read negotiated camera property", exc_info=True)
            return None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._latest = None
        self._terminal_error = None
        self._sequence = 0
        if not self._device_lease.acquire(blocking=False):
            raise CameraOpenError("Backend camera is already owned by another worker")
        with self._lease_state_lock:
            self._owns_device_lease = True

        try:
            capture = self._create_capture()
        except Exception:
            self._release_device_lease()
            raise
        if capture is None:
            self._release_device_lease()
            raise CameraOpenError(
                f"Cannot create camera capture for index {self.settings.index}"
            )
        self._capture = capture
        self._released = False

        try:
            if not capture.isOpened():
                raise CameraOpenError(f"Cannot open camera index {self.settings.index}")
            self._configure_capture(capture)
        except Exception:
            self._release_capture()
            self._release_device_lease()
            raise

        logger.info(
            "Opened backend camera index=%s width=%s height=%s fps=%s",
            self.settings.index,
            self._capture_value(capture, "CAP_PROP_FRAME_WIDTH"),
            self._capture_value(capture, "CAP_PROP_FRAME_HEIGHT"),
            self._capture_value(capture, "CAP_PROP_FPS"),
        )
        try:
            self._thread = threading.Thread(
                target=self._capture_loop,
                name="faceguard-camera-capture",
                daemon=True,
            )
            self._thread.start()
        except Exception:
            self._release_capture()
            self._release_device_lease()
            self._thread = None
            raise

    def _capture_loop(self) -> None:
        consecutive_failures = 0
        capture = self._capture
        try:
            while not self._stop_event.is_set():
                started_at = time.perf_counter()
                success, frame = capture.read()
                captured_at = time.perf_counter()

                if not success or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures >= self.settings.max_read_failures:
                        error = CameraReadError(
                            "Camera read failed "
                            f"{consecutive_failures} consecutive times"
                        )
                        with self._condition:
                            self._terminal_error = error
                            self._condition.notify_all()
                        return
                    if self._stop_event.wait(self.settings.read_retry_delay):
                        return
                    continue

                consecutive_failures = 0
                self._sequence += 1
                item = CameraFrame(
                    sequence=self._sequence,
                    captured_at=captured_at,
                    image=frame,
                    capture_ms=(captured_at - started_at) * 1000.0,
                )
                with self._condition:
                    self._latest = item
                    self._condition.notify_all()
        except Exception as error:
            logger.exception("Unexpected camera capture failure")
            with self._condition:
                self._terminal_error = CameraReadError(
                    "Unexpected camera capture failure"
                )
                self._condition.notify_all()
            self._terminal_error.__cause__ = error
        finally:
            self._release_capture()
            self._release_device_lease()
            with self._condition:
                self._condition.notify_all()

    def wait_for_frame(
        self, after_sequence: int = 0, timeout: Optional[float] = None
    ) -> CameraFrame:
        wait_timeout = self.settings.frame_timeout if timeout is None else timeout

        def frame_ready() -> bool:
            return (
                self._terminal_error is not None
                or (self._latest is not None and self._latest.sequence > after_sequence)
                or self._stop_event.is_set()
            )

        with self._condition:
            ready = self._condition.wait_for(frame_ready, timeout=wait_timeout)
            if self._terminal_error is not None:
                raise self._terminal_error
            if self._stop_event.is_set():
                raise CameraReadError("Camera capture has stopped")
            if not ready or self._latest is None:
                raise CameraReadError("Timed out waiting for a camera frame")
            latest = self._latest

        return CameraFrame(
            sequence=latest.sequence,
            captured_at=latest.captured_at,
            image=latest.image.copy(),
            capture_ms=latest.capture_ms,
        )

    def _release_capture(self) -> None:
        with self._release_lock:
            if self._released:
                return
            self._released = True
            capture = self._capture
            self._capture = None
            if capture is not None:
                try:
                    capture.release()
                except Exception:
                    logger.exception(
                        "Unable to release backend camera index=%s",
                        self.settings.index,
                    )
                else:
                    logger.info("Released backend camera index=%s", self.settings.index)

    def _release_device_lease(self) -> None:
        with self._lease_state_lock:
            if not self._owns_device_lease:
                return
            self._owns_device_lease = False
            self._device_lease.release()

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop_event.set()
        with self._condition:
            self._condition.notify_all()

        thread = self._thread
        # Releasing first is necessary to unblock a V4L2 read when a device is
        # disconnected or stops producing frames.  Release is idempotent here.
        self._release_capture()
        if thread is not None and thread is not threading.current_thread():
            thread.join(join_timeout)
            if thread.is_alive():
                logger.warning("Camera capture worker did not stop in time")
            else:
                self._thread = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def __enter__(self) -> "LatestFrameCamera":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()
