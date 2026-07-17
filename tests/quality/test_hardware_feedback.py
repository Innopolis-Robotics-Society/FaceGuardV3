"""Software-side precheck for QR-006; this is not physical LED evidence."""

import leds


class RecordingLed:
    def __init__(self, colour, events):
        self.colour = colour
        self.events = events

    def on(self):
        self.events.append(f"{self.colour}:on")

    def off(self):
        self.events.append(f"{self.colour}:off")

    def close(self):
        self.events.append(f"{self.colour}:close")


class RecordingThread:
    def __init__(self, target, args, daemon):
        self.target = target
        self.args = args
        self.events = args[0].events

    def start(self):
        self.events.append("hold-worker:start")

    def join(self, timeout=None):
        self.events.append("hold-worker:join")


def test_qr_006_software_precheck_dispatches_gpio_before_background_hold(
    monkeypatch,
):
    events = []
    leds.cleanup()
    monkeypatch.setattr(leds, "YELLOW", RecordingLed("yellow", events))
    monkeypatch.setattr(leds, "BLUE", RecordingLed("blue", events))
    monkeypatch.setattr(leds, "RED", RecordingLed("red", events))
    monkeypatch.setattr(leds, "GPIO_AVAILABLE", True)
    monkeypatch.setattr(leds.threading, "Thread", RecordingThread)

    leds.access_granted()

    assert events == [
        "yellow:off",
        "blue:off",
        "red:off",
        "blue:on",
        "hold-worker:start",
    ]
    leds.cleanup()
