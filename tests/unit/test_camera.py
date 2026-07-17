import threading

import numpy as np
import pytest

from camera import (
    CameraConfigurationError,
    CameraOpenError,
    CameraReadError,
    CameraSettings,
    LatestFrameCamera,
)


class ControlledCapture:
    def __init__(self, frames=(), opened=True):
        self.frames = list(frames)
        self.opened = opened
        self.release_calls = 0
        self.properties = []
        self.frames_consumed = threading.Event()
        self.released = threading.Event()

    def isOpened(self):
        return self.opened

    def set(self, property_id, value):
        self.properties.append((property_id, value))
        return True

    def read(self):
        if self.frames:
            frame = self.frames.pop(0)
            if not self.frames:
                self.frames_consumed.set()
            return True, frame
        self.frames_consumed.set()
        self.released.wait(1.0)
        return False, None

    def release(self):
        self.release_calls += 1
        self.released.set()


@pytest.mark.parametrize("source", ["browser", "backend", " BROWSER "])
def test_camera_settings_accept_supported_modes(source):
    settings = CameraSettings.from_env({"CAMERA_SOURCE": source, "CAMERA_INDEX": "2"})

    assert settings.source == source.strip().lower()
    assert settings.index == 2


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"CAMERA_SOURCE": "rtsp"}, "CAMERA_SOURCE"),
        ({"CAMERA_INDEX": "usb0"}, "CAMERA_INDEX"),
        ({"CAMERA_INDEX": "-1"}, "non-negative"),
    ],
)
def test_camera_settings_reject_invalid_configuration(values, message):
    with pytest.raises(CameraConfigurationError, match=message):
        CameraSettings.from_env(values)


def test_start_is_idempotent_and_only_one_capture_loop_owns_device():
    first_capture = ControlledCapture([np.zeros((2, 3, 3), dtype=np.uint8)])
    created = []

    def factory(*args):
        created.append(args)
        return first_capture

    first = LatestFrameCamera(CameraSettings(source="backend"), factory)
    second = LatestFrameCamera(
        CameraSettings(source="backend"),
        lambda *args: pytest.fail("second capture must not be constructed"),
    )
    try:
        first.start()
        first.start()
        with pytest.raises(CameraOpenError, match="already owned"):
            second.start()

        assert len(created) == 1
        assert first.is_running is True
    finally:
        first.stop()
        second.stop()


def test_latest_frame_replaces_older_frames_without_backlog():
    frames = [np.full((2, 3, 3), value, dtype=np.uint8) for value in (10, 20, 30)]
    capture = ControlledCapture(frames)
    camera = LatestFrameCamera(CameraSettings(source="backend"), lambda *args: capture)
    try:
        camera.start()
        assert capture.frames_consumed.wait(1.0), "capture loop did not consume frames"

        latest = camera.wait_for_frame(after_sequence=0, timeout=1.0)
        latest.image.fill(99)
        same_frame_again = camera.wait_for_frame(after_sequence=0, timeout=1.0)

        assert latest.sequence == 3
        assert np.all(same_frame_again.image == 30)
    finally:
        camera.stop()


def test_stop_unblocks_capture_and_releases_device_exactly_once():
    capture = ControlledCapture([np.zeros((2, 2, 3), dtype=np.uint8)])
    camera = LatestFrameCamera(CameraSettings(source="backend"), lambda *args: capture)

    camera.start()
    assert capture.frames_consumed.wait(1.0)
    camera.stop()
    camera.stop()

    assert capture.release_calls == 1
    assert camera.is_running is False


def test_unavailable_camera_is_released_and_does_not_keep_global_lease():
    unavailable = ControlledCapture(opened=False)
    camera = LatestFrameCamera(
        CameraSettings(source="backend"), lambda *args: unavailable
    )

    with pytest.raises(CameraOpenError, match="Cannot open camera"):
        camera.start()

    replacement_capture = ControlledCapture([np.zeros((2, 2, 3), dtype=np.uint8)])
    replacement = LatestFrameCamera(
        CameraSettings(source="backend"), lambda *args: replacement_capture
    )
    try:
        replacement.start()
        assert replacement_capture.frames_consumed.wait(1.0)
    finally:
        replacement.stop()

    assert unavailable.release_calls == 1


def test_consecutive_read_failures_are_reported_to_consumer():
    capture = ControlledCapture()
    settings = CameraSettings(
        source="backend",
        max_read_failures=2,
        read_retry_delay=0.0,
    )
    camera = LatestFrameCamera(settings, lambda *args: capture)
    try:
        camera.start()
        capture.released.set()
        with pytest.raises(CameraReadError, match="2 consecutive"):
            camera.wait_for_frame(timeout=1.0)
    finally:
        camera.stop()
