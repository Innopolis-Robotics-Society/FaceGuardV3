import pytest

import leds


class FakeLed:
    def __init__(self, pin=None, pin_factory=None):
        self.pin = pin
        self.pin_factory = pin_factory
        self.calls = []

    def on(self):
        self.calls.append("on")

    def off(self):
        self.calls.append("off")

    def close(self):
        self.calls.append("close")


class CapturedThread:
    created = []

    def __init__(self, target, args=(), daemon=None):
        self.target = target
        self.args = args
        self.daemon = daemon
        self.started = False
        self.join_calls = []
        self.__class__.created.append(self)

    def start(self):
        self.started = True

    def join(self, timeout=None):
        self.join_calls.append(timeout)


class FakeFactory:
    instances = []

    def __init__(self, chip):
        self.chip = chip
        self.closed = False
        self.__class__.instances.append(self)

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def reset_led_state(monkeypatch):
    leds.cleanup()
    CapturedThread.created = []
    FakeFactory.instances = []
    monkeypatch.setattr(leds.threading, "Thread", CapturedThread)
    yield
    leds.cleanup()


def configure_leds(monkeypatch):
    yellow = FakeLed()
    blue = FakeLed()
    red = FakeLed()
    monkeypatch.setattr(leds, "GPIO_AVAILABLE", True)
    monkeypatch.setattr(leds, "YELLOW", yellow)
    monkeypatch.setattr(leds, "BLUE", blue)
    monkeypatch.setattr(leds, "RED", red)
    return yellow, blue, red


@pytest.mark.parametrize(
    ("action", "expected_colour", "expected_duration"),
    [
        ("access_granted", "blue", 5.0),
        ("access_denied", "red", 5.0),
        ("bad_frame", "yellow", 5.0),
    ],
)
def test_access_feedback_dispatches_the_expected_led_immediately(
    monkeypatch, action, expected_colour, expected_duration
):
    yellow, blue, red = configure_leds(monkeypatch)
    by_colour = {"yellow": yellow, "blue": blue, "red": red}

    getattr(leds, action)()

    selected = by_colour[expected_colour]
    assert selected.calls[-1] == "on"
    assert len(CapturedThread.created) == 1
    worker = CapturedThread.created[0]
    assert worker.started is True
    assert worker.target is leds._hold_then_off
    assert worker.args[0:2] == (selected, expected_duration)


def test_latest_feedback_owns_the_leds_when_older_worker_finishes(monkeypatch):
    yellow, blue, red = configure_leds(monkeypatch)

    leds.access_granted()
    old_worker = CapturedThread.created[-1]
    leds.access_denied()
    calls_before_old_worker_finishes = list(red.calls)

    # The second action sets the old generation's event. A late worker must not
    # switch off or otherwise mutate the newer red signal.
    old_worker.target(*old_worker.args)

    assert old_worker.args[-1].is_set()
    assert red.calls == calls_before_old_worker_finishes
    assert red.calls[-1] == "on"
    assert blue.calls[-1] == "off"
    assert yellow.calls[-1] == "off"


def test_stale_recognition_blink_cannot_override_access_result(monkeypatch):
    yellow, blue, red = configure_leds(monkeypatch)

    leds.start_recognizing()
    blink_worker = CapturedThread.created[-1]
    leds.access_granted()
    blue_calls = list(blue.calls)

    blink_worker.target(*blink_worker.args)

    assert blink_worker.args[-1].is_set()
    assert blue.calls == blue_calls
    assert blue.calls[-1] == "on"


def test_start_recognizing_is_idempotent_until_stopped(monkeypatch):
    yellow, blue, red = configure_leds(monkeypatch)

    leds.start_recognizing()
    leds.start_recognizing()

    assert len(CapturedThread.created) == 1
    assert yellow.calls[-1] == "on"
    assert blue.calls[-1] == "off"
    assert red.calls[-1] == "off"

    leds.stop_recognizing()
    assert leds.blink_stop.is_set()
    assert all(led.calls[-1] == "off" for led in (yellow, blue, red))


def test_registration_feedback_maps_all_leds_and_has_generation_safe_timeout(
    monkeypatch,
):
    yellow, blue, red = configure_leds(monkeypatch)

    leds.registration_active()
    assert all(led.calls[-1] == "on" for led in (yellow, blue, red))

    leds.registration_done()
    worker = CapturedThread.created[-1]
    assert all(led.calls[-1] == "on" for led in (yellow, blue, red))
    assert worker.target is leds._registration_timeout
    assert worker.started is True


def test_cleanup_cancels_worker_turns_off_and_closes_all_resources(monkeypatch):
    yellow, blue, red = configure_leds(monkeypatch)
    factory = FakeFactory(4)
    monkeypatch.setattr(leds, "PIN_FACTORY", factory)
    leds.access_granted()
    worker = CapturedThread.created[-1]

    leds.cleanup()

    assert worker.args[-1].is_set()
    assert worker.join_calls == [1.0]
    assert all(led.calls[-2:] == ["off", "close"] for led in (yellow, blue, red))
    assert factory.closed is True
    assert leds.GPIO_AVAILABLE is False
    assert leds.PIN_FACTORY is None


def test_initialize_gpio_uses_configured_gpiochip_and_bcm_pins(monkeypatch):
    monkeypatch.setenv("GPIO_CHIP", "4")
    monkeypatch.setattr(leds, "GPIO_IMPORT_ERROR", None)
    monkeypatch.setattr(leds, "LGPIOFactory", FakeFactory)
    created_leds = []

    def create_led(pin, pin_factory):
        led = FakeLed(pin, pin_factory)
        created_leds.append(led)
        return led

    monkeypatch.setattr(leds, "GPIOZeroLED", create_led)

    assert leds.initialize_gpio() is True

    assert FakeFactory.instances[-1].chip == 4
    assert [led.pin for led in created_leds] == [17, 27, 22]
    assert all(led.pin_factory is FakeFactory.instances[-1] for led in created_leds)
    assert all(led.calls == ["off"] for led in created_leds)


def test_initialize_gpio_closes_partial_resources_after_failure(monkeypatch):
    monkeypatch.setattr(leds, "GPIO_IMPORT_ERROR", None)
    monkeypatch.setattr(leds, "LGPIOFactory", FakeFactory)
    first_led = FakeLed(17)
    calls = 0

    def fail_on_second_led(pin, pin_factory):
        nonlocal calls
        calls += 1
        if calls == 1:
            first_led.pin_factory = pin_factory
            return first_led
        raise RuntimeError("GPIO line is busy")

    monkeypatch.setattr(leds, "GPIOZeroLED", fail_on_second_led)

    assert leds.initialize_gpio() is False

    assert first_led.calls == ["close"]
    assert FakeFactory.instances[-1].closed is True
    assert leds.GPIO_AVAILABLE is False


@pytest.mark.parametrize("chip", ["not-a-number", "-1"])
def test_invalid_gpiochip_disables_gpio_without_starting_workers(monkeypatch, chip):
    monkeypatch.setenv("GPIO_CHIP", chip)
    monkeypatch.setattr(leds, "GPIO_IMPORT_ERROR", None)
    monkeypatch.setattr(leds, "LGPIOFactory", FakeFactory)

    assert leds.initialize_gpio() is False
    leds.access_granted()

    assert FakeFactory.instances == []
    assert CapturedThread.created == []


def test_feedback_is_a_safe_noop_without_gpio(monkeypatch):
    monkeypatch.setattr(leds, "GPIO_AVAILABLE", False)

    leds.start_recognizing()
    leds.access_granted()
    leds.access_denied()
    leds.bad_frame()
    leds.registration_active()
    leds.registration_done()

    assert CapturedThread.created == []
    assert leds._action_kind is None


def test_public_blink_stops_with_its_event_and_leaves_led_off(monkeypatch):
    led = FakeLed()
    monkeypatch.setattr(leds, "GPIO_AVAILABLE", True)

    class TwoWaitsThenStop:
        def __init__(self):
            self.waits = 0

        def is_set(self):
            return False

        def wait(self, timeout):
            self.waits += 1
            return self.waits == 2

    leds.blink(led, TwoWaitsThenStop(), interval=0.01)

    assert led.calls == ["on", "off"]
