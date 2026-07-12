from types import SimpleNamespace

import leds


class FakeLed:
    def __init__(self):
        self.calls = []

    def on(self):
        self.calls.append("on")

    def off(self):
        self.calls.append("off")


def configure_leds(monkeypatch):
    yellow = FakeLed()
    blue = FakeLed()
    red = FakeLed()
    monkeypatch.setattr(leds, "GPIO_AVAILABLE", True)
    monkeypatch.setattr(leds, "YELLOW", yellow)
    monkeypatch.setattr(leds, "BLUE", blue)
    monkeypatch.setattr(leds, "RED", red)
    return yellow, blue, red


def test_all_leds_off_and_solid_sequence(monkeypatch):
    yellow, blue, red = configure_leds(monkeypatch)
    sleeps = []
    monkeypatch.setattr(leds.time, "sleep", lambda duration: sleeps.append(duration))

    leds.solid(blue, 2.5)

    assert yellow.calls == ["off"]
    assert blue.calls == ["off", "on", "off"]
    assert red.calls == ["off"]
    assert sleeps == [2.5]


def test_gpio_operations_are_noops_when_hardware_is_unavailable(monkeypatch):
    led = FakeLed()
    monkeypatch.setattr(leds, "GPIO_AVAILABLE", False)
    monkeypatch.setattr(
        leds.time,
        "sleep",
        lambda duration: (_ for _ in ()).throw(AssertionError("must not sleep")),
    )

    leds.all_leds_off()
    leds.solid(led, 5)
    leds.blink(led, SimpleNamespace(is_set=lambda: False))

    assert led.calls == []


def test_blink_runs_until_stop_event(monkeypatch):
    led = FakeLed()
    checks = iter([False, True])
    sleeps = []
    monkeypatch.setattr(leds, "GPIO_AVAILABLE", True)
    monkeypatch.setattr(leds.time, "sleep", lambda duration: sleeps.append(duration))
    stop_event = SimpleNamespace(is_set=lambda: next(checks))

    leds.blink(led, stop_event, interval=0.25)

    assert led.calls == ["on", "off"]
    assert sleeps == [0.25, 0.25]


def test_start_and_stop_recognizing_manage_background_thread(monkeypatch):
    yellow, blue, red = configure_leds(monkeypatch)
    threads = []

    class FakeThread:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args
            self.daemon = daemon
            self.started = False
            threads.append(self)

        def start(self):
            self.started = True

    monkeypatch.setattr(leds.threading, "Thread", FakeThread)

    leds.start_recognizing()

    assert len(threads) == 1
    assert threads[0].target is leds.blink
    assert threads[0].args[0] is yellow
    assert threads[0].daemon is True
    assert threads[0].started is True
    assert yellow.calls == ["off"]
    assert blue.calls == ["off"]
    assert red.calls == ["off"]

    leds.stop_recognizing()

    assert leds.blink_stop.is_set()
    assert yellow.calls[-1] == "off"
    assert blue.calls[-1] == "off"
    assert red.calls[-1] == "off"


def test_access_indicators_schedule_expected_led(monkeypatch):
    yellow, blue, red = configure_leds(monkeypatch)
    scheduled = []
    stops = []

    class FakeThread:
        def __init__(self, target, args, daemon):
            scheduled.append((target, args, daemon))

        def start(self):
            return None

    monkeypatch.setattr(leds.threading, "Thread", FakeThread)
    monkeypatch.setattr(leds, "stop_recognizing", lambda: stops.append(True))

    leds.access_granted()
    leds.access_denied()
    leds.bad_frame()

    assert stops == [True, True, True]
    assert scheduled == [
        (leds.solid, (blue, 5), True),
        (leds.solid, (red, 5), True),
        (leds.solid, (yellow, 5), True),
    ]


def test_registration_indicators_do_not_require_background_timing(monkeypatch):
    yellow, blue, red = configure_leds(monkeypatch)
    sleeps = []

    class ImmediateThread:
        def __init__(self, target, daemon):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(leds.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(leds.time, "sleep", lambda duration: sleeps.append(duration))

    leds.registration_active()
    leds.registration_done()

    assert sleeps == [3]
    assert yellow.calls.count("on") == 2
    assert blue.calls.count("on") == 2
    assert red.calls.count("on") == 2
    assert yellow.calls[-1] == "off"
    assert blue.calls[-1] == "off"
    assert red.calls[-1] == "off"


def test_all_off_stops_recognition_and_clears_leds(monkeypatch):
    yellow, blue, red = configure_leds(monkeypatch)
    stops = []
    monkeypatch.setattr(leds, "stop_recognizing", lambda: stops.append(True))

    leds.all_off()

    assert stops == [True]
    assert yellow.calls == ["off"]
    assert blue.calls == ["off"]
    assert red.calls == ["off"]
