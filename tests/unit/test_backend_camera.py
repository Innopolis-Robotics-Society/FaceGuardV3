import threading
import time

import cv2
import numpy as np
import pytest

import camera
from camera import (
    CameraConfigurationError,
    CameraOpenError,
    CameraReadError,
    CameraSettings,
    LatestFrameCamera,
)


class FakeCapture:
    def __init__(self, *, opened=True, read_result=(False, None)):
        self.opened = opened
        self.read_result = read_result
        self.properties = []
        self.release_count = 0

    def isOpened(self):
        return self.opened

    def set(self, property_id, value):
        self.properties.append((property_id, value))
        return True

    def get(self, property_id):
        values = {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30,
        }
        return values.get(property_id, 0)

    def read(self):
        return self.read_result

    def release(self):
        self.release_count += 1


class CountingCapture(FakeCapture):
    def __init__(self):
        super().__init__(opened=True)
        self.counter = 0

    def read(self):
        time.sleep(0.002)
        self.counter += 1
        frame = np.full((4, 6, 3), self.counter % 255, dtype=np.uint8)
        return True, frame


def test_camera_settings_support_browser_and_backend_sources():
    assert CameraSettings.from_env({}).source == "browser"
    backend = CameraSettings.from_env(
        {"CAMERA_SOURCE": " BACKEND ", "CAMERA_INDEX": "3"}
    )

    assert backend.source == "backend"
    assert backend.index == 3
    assert (backend.width, backend.height, backend.fps) == (640, 480, 30)
    assert backend.jpeg_quality == 60
    assert backend.buffer_size == 1


@pytest.mark.parametrize(
    "environment",
    [
        {"CAMERA_SOURCE": "remote"},
        {"CAMERA_SOURCE": "backend", "CAMERA_INDEX": "not-an-int"},
        {"CAMERA_SOURCE": "backend", "CAMERA_INDEX": "-1"},
    ],
)
def test_camera_settings_reject_invalid_environment(environment):
    with pytest.raises(CameraConfigurationError):
        CameraSettings.from_env(environment)


def test_camera_uses_index_v4l2_and_low_latency_properties(monkeypatch):
    capture = CountingCapture()
    calls = []

    def factory(*args):
        calls.append(args)
        return capture

    monkeypatch.setattr(camera.sys, "platform", "linux")
    settings = CameraSettings(source="backend", index=4)
    stream = LatestFrameCamera(settings, capture_factory=factory)

    stream.start()
    frame = stream.wait_for_frame(timeout=1)
    stream.stop(join_timeout=0.01)

    if hasattr(cv2, "CAP_V4L2"):
        assert calls == [(4, cv2.CAP_V4L2)]
    else:
        assert calls == [(4,)]
    assert frame.image.shape == (4, 6, 3)
    configured = dict(capture.properties)
    assert configured[cv2.CAP_PROP_FRAME_WIDTH] == 640
    assert configured[cv2.CAP_PROP_FRAME_HEIGHT] == 480
    assert configured[cv2.CAP_PROP_FPS] == 30
    assert configured[cv2.CAP_PROP_BUFFERSIZE] == 1
    assert configured[cv2.CAP_PROP_FOURCC] == cv2.VideoWriter_fourcc(*"MJPG")
    assert capture.release_count == 1


def test_camera_releases_capture_when_open_fails():
    capture = FakeCapture(opened=False)
    stream = LatestFrameCamera(
        CameraSettings(source="backend"), capture_factory=lambda *args: capture
    )

    with pytest.raises(CameraOpenError, match="Cannot open camera index 0"):
        stream.start()

    assert capture.release_count == 1


def test_camera_read_failures_back_off_and_release():
    capture = FakeCapture(opened=True, read_result=(False, None))
    settings = CameraSettings(
        source="backend",
        read_retry_delay=0.02,
        max_read_failures=3,
        frame_timeout=1,
    )
    stream = LatestFrameCamera(settings, capture_factory=lambda *args: capture)
    started_at = time.perf_counter()

    stream.start()
    with pytest.raises(CameraReadError, match="3 consecutive times"):
        stream.wait_for_frame(timeout=1)
    elapsed = time.perf_counter() - started_at
    stream.stop(join_timeout=0.01)

    assert elapsed >= 0.035
    assert capture.release_count == 1


def test_camera_returns_latest_frame_without_a_queue():
    capture = CountingCapture()
    stream = LatestFrameCamera(
        CameraSettings(source="backend"), capture_factory=lambda *args: capture
    )

    stream.start()
    first = stream.wait_for_frame(timeout=1)
    time.sleep(0.025)
    latest = stream.wait_for_frame(after_sequence=first.sequence, timeout=1)
    stream.stop(join_timeout=0.01)

    assert latest.sequence > first.sequence + 1
    assert int(latest.image[0, 0, 0]) == latest.sequence % 255
    assert capture.release_count == 1


def test_camera_does_not_return_a_stale_frame_after_stop():
    capture = CountingCapture()
    stream = LatestFrameCamera(
        CameraSettings(source="backend"), capture_factory=lambda *args: capture
    )

    stream.start()
    stream.wait_for_frame(timeout=1)
    stream.stop(join_timeout=0.01)

    with pytest.raises(CameraReadError, match="stopped"):
        stream.wait_for_frame(timeout=0.01)
    assert capture.release_count == 1


def test_stuck_capture_worker_keeps_exclusive_device_lease():
    read_started = threading.Event()
    allow_read_to_finish = threading.Event()

    class BlockingCapture(FakeCapture):
        def read(self):
            read_started.set()
            allow_read_to_finish.wait()
            return False, None

    first_capture = BlockingCapture(opened=True)
    first = LatestFrameCamera(
        CameraSettings(source="backend"),
        capture_factory=lambda *args: first_capture,
    )
    second_capture = CountingCapture()
    second = LatestFrameCamera(
        CameraSettings(source="backend"),
        capture_factory=lambda *args: second_capture,
    )

    first.start()
    assert read_started.wait(timeout=1)
    first.stop(join_timeout=0.01)
    assert first.is_running is True

    with pytest.raises(CameraOpenError, match="already owned"):
        second.start()

    allow_read_to_finish.set()
    first.stop(join_timeout=1)
    assert first.is_running is False

    second.start()
    second.wait_for_frame(timeout=1)
    second.stop(join_timeout=0.1)
    assert first_capture.release_count == 1
    assert second_capture.release_count == 1


def test_unexpected_read_exception_is_reported_and_released():
    class BrokenCapture(FakeCapture):
        def read(self):
            raise OSError("device disappeared")

    capture = BrokenCapture(opened=True)
    stream = LatestFrameCamera(
        CameraSettings(source="backend"), capture_factory=lambda *args: capture
    )

    stream.start()
    with pytest.raises(CameraReadError, match="Unexpected camera capture failure"):
        stream.wait_for_frame(timeout=1)
    stream.stop(join_timeout=0.01)

    assert capture.release_count == 1
