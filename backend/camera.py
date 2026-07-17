"""Backend camera capture with a single latest-frame-only buffer."""

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
    """Base error raised by the backend camera pipeline."""


class CameraConfigurationError(CameraError):
    """Raised when camera environment settings are invalid."""


class CameraOpenError(CameraError):
    """Raised when OpenCV cannot open the configured camera."""


class CameraReadError(CameraError):
    """Raised when the capture worker cannot provide a usable frame."""


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

        try:
            index = int(values.get("CAMERA_INDEX", "0"))
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
    """Own one ``VideoCapture`` and retain only its newest successful frame."""

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
        self._lease_lock = threading.Lock()
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
        if property_id is None:
            return
        try:
            accepted = capture.set(property_id, value)
            if accepted is False:
                logger.warning("Camera rejected %s=%s", property_name, value)
        except Exception:
            logger.warning(
                "Unable to configure camera property %s=%s",
                property_name,
                value,
                exc_info=True,
            )

    def _configure_capture(self, capture) -> None:
        fourcc = getattr(cv2, "VideoWriter_fourcc", None)
        if fourcc is not None:
            self._set_property(capture, "CAP_PROP_FOURCC", fourcc(*"MJPG"))
        self._set_property(capture, "CAP_PROP_FRAME_WIDTH", self.settings.width)
        self._set_property(capture, "CAP_PROP_FRAME_HEIGHT", self.settings.height)
        self._set_property(capture, "CAP_PROP_FPS", self.settings.fps)
        self._set_property(capture, "CAP_PROP_BUFFERSIZE", self.settings.buffer_size)

    def start(self) -> None:
        if self.is_running:
            return

        self._stop_event.clear()
        self._latest = None
        self._terminal_error = None
        self._sequence = 0
        if not self._device_lease.acquire(blocking=False):
            raise CameraOpenError("Backend camera is already owned by another worker")
        with self._lease_lock:
            self._owns_device_lease = True

        try:
            capture = self._create_capture()
            if capture is None:
                raise CameraOpenError(
                    f"Cannot create camera capture for index {self.settings.index}"
                )
            self._capture = capture
            self._released = False
            if not capture.isOpened():
                raise CameraOpenError(f"Cannot open camera index {self.settings.index}")
            self._configure_capture(capture)
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
        failures = 0
        capture = self._capture
        try:
            while not self._stop_event.is_set():
                started_at = time.perf_counter()
                success, image = capture.read()
                captured_at = time.perf_counter()
                if not success or image is None:
                    failures += 1
                    if failures >= self.settings.max_read_failures:
                        with self._condition:
                            self._terminal_error = CameraReadError(
                                f"Camera read failed {failures} consecutive times"
                            )
                            self._condition.notify_all()
                        return
                    if self._stop_event.wait(self.settings.read_retry_delay):
                        return
                    continue

                failures = 0
                self._sequence += 1
                frame = CameraFrame(
                    sequence=self._sequence,
                    captured_at=captured_at,
                    image=image,
                    capture_ms=(captured_at - started_at) * 1000.0,
                )
                with self._condition:
                    # Replacement, never append: slow consumers skip stale frames.
                    self._latest = frame
                    self._condition.notify_all()
        except Exception as error:
            logger.exception("Unexpected camera capture failure")
            with self._condition:
                self._terminal_error = CameraReadError(
                    "Unexpected camera capture failure"
                )
                self._terminal_error.__cause__ = error
                self._condition.notify_all()
        finally:
            self._release_capture()
            self._release_device_lease()
            with self._condition:
                self._condition.notify_all()

    def wait_for_frame(
        self, after_sequence: int = 0, timeout: Optional[float] = None
    ) -> CameraFrame:
        wait_timeout = self.settings.frame_timeout if timeout is None else timeout

        def ready() -> bool:
            return (
                self._terminal_error is not None
                or (self._latest is not None and self._latest.sequence > after_sequence)
                or self._stop_event.is_set()
            )

        with self._condition:
            signalled = self._condition.wait_for(ready, timeout=wait_timeout)
            if self._terminal_error is not None:
                raise self._terminal_error
            if self._stop_event.is_set():
                raise CameraReadError("Camera capture has stopped")
            if not signalled or self._latest is None:
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
                        "Unable to release camera index=%s", self.settings.index
                    )

    def _release_device_lease(self) -> None:
        with self._lease_lock:
            if self._owns_device_lease:
                self._owns_device_lease = False
                self._device_lease.release()

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop_event.set()
        with self._condition:
            self._condition.notify_all()
        # Some V4L2 drivers unblock ``read`` only after release.
        self._release_capture()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(join_timeout)
            if thread.is_alive():
                logger.warning("Camera worker did not stop within %.1fs", join_timeout)
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
