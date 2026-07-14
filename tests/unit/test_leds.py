import logging

import pytest

import leds


class FakeLed:
    def __init__(self, pin, pin_factory):
        self.pin = pin
        self.pin_factory = pin_factory
        self.calls = []
        self.close_calls = 0

    def on(self):
        self.calls.append("on")

    def off(self):
        self.calls.append("off")

    def close(self):
        self.close_calls += 1


class FakeFactory:
    def __init__(self, chip):
        self.chip = chip
        self._chip = chip
        self.close_calls = 0

    def close(self):
        self.close_calls += 1


class FakeEvent:
    def __init__(self, wait_results=None):
        self.set_value = False
        self.wait_results = list(wait_results or [])
        self.wait_calls = []

    def set(self):
        self.set_value = True

    def is_set(self):
        return self.set_value

    def wait(self, duration):
        self.wait_calls.append(duration)
        if self.wait_results:
            result = self.wait_results.pop(0)
            if result:
                self.set_value = True
            return result
        return self.set_value


@pytest.fixture(autouse=True)
def reset_led_module(monkeypatch):
    leds.cleanup()
    monkeypatch.setattr(leds, "GPIO_IMPORT_ERROR", None)
    yield
    leds.cleanup()


def initialize_fake_gpio(monkeypatch, chip="0"):
    factories = []
    devices = []

    def factory_class(chip):
        factory = FakeFactory(chip)
        factories.append(factory)
        return factory

    def led_class(pin, pin_factory):
        device = FakeLed(pin, pin_factory)
        devices.append(device)
        return device

    monkeypatch.setenv("GPIO_CHIP", chip)
    monkeypatch.setattr(leds, "LGPIOFactory", factory_class)
    monkeypatch.setattr(leds, "GPIOZeroLED", led_class)

    assert leds.initialize_gpio() is True
    return factories[0], devices


def clear_device_calls(devices):
    for device in devices:
        device.calls.clear()


def test_initialization_uses_configured_gpiochip_and_bcm_pins(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=leds.LOGGER.name)

    factory, devices = initialize_fake_gpio(monkeypatch, chip="0")

    assert leds.GPIO_AVAILABLE is True
    assert leds.GPIO_CHIP == 0
    assert leds.PIN_FACTORY is factory
    assert factory.chip == 0
    assert [device.pin for device in devices] == [17, 27, 22]
    assert all(device.pin_factory is factory for device in devices)
    assert "GPIO initialized successfully using gpiochip0" in caplog.text


def test_initialization_failure_is_logged_and_actions_are_skipped(monkeypatch, caplog):
    def failing_factory(chip):
        raise OSError(f"cannot open gpiochip{chip}")

    monkeypatch.setenv("GPIO_CHIP", "0")
    monkeypatch.setattr(leds, "LGPIOFactory", failing_factory)
    monkeypatch.setattr(leds, "GPIOZeroLED", FakeLed)
    caplog.set_level(logging.INFO, logger=leds.LOGGER.name)

    assert leds.initialize_gpio() is False
    assert leds.GPIO_AVAILABLE is False
    assert "GPIO initialization failed for gpiochip0" in caplog.text
    assert "cannot open gpiochip0" in caplog.text

    caplog.clear()
    leds.access_denied()

    assert "access_denied skipped: GPIO is unavailable" in caplog.text
    assert "solid red for 5 seconds" not in caplog.text


def test_partial_initialization_failure_closes_created_resources(monkeypatch, caplog):
    factory = FakeFactory(0)
    devices = []

    def led_class(pin, pin_factory):
        if pin == 27:
            raise RuntimeError("blue LED failed")
        device = FakeLed(pin, pin_factory)
        devices.append(device)
        return device

    monkeypatch.setattr(leds, "LGPIOFactory", lambda chip: factory)
    monkeypatch.setattr(leds, "GPIOZeroLED", led_class)
    caplog.set_level(logging.ERROR, logger=leds.LOGGER.name)

    assert leds.initialize_gpio() is False

    assert devices[0].pin == 17
    assert devices[0].close_calls == 1
    assert factory.close_calls == 1
    assert "blue LED failed" in caplog.text


def test_initialization_rejects_a_factory_using_the_wrong_gpiochip(monkeypatch, caplog):
    factory = FakeFactory(1)
    monkeypatch.setenv("GPIO_CHIP", "0")
    monkeypatch.setattr(leds, "LGPIOFactory", lambda chip: factory)
    monkeypatch.setattr(leds, "GPIOZeroLED", FakeLed)
    caplog.set_level(logging.ERROR, logger=leds.LOGGER.name)

    assert leds.initialize_gpio() is False

    assert leds.GPIO_AVAILABLE is False
    assert factory.close_calls == 1
    assert "opened gpiochip1, but GPIO_CHIP requested gpiochip0" in caplog.text


def test_all_leds_off_and_solid_sequence(monkeypatch):
    _, devices = initialize_fake_gpio(monkeypatch)
    yellow, blue, red = devices
    clear_device_calls(devices)

    leds.solid(blue, 0)

    assert yellow.calls == ["off"]
    assert blue.calls == ["off", "on", "off"]
    assert red.calls == ["off"]


def test_blink_runs_until_stop_event(monkeypatch):
    _, devices = initialize_fake_gpio(monkeypatch)
    yellow, blue, red = devices
    clear_device_calls(devices)
    stop_event = FakeEvent(wait_results=[False, True])

    leds.blink(yellow, stop_event, interval=0.25)

    assert yellow.calls == ["off", "on", "off"]
    assert blue.calls == ["off"]
    assert red.calls == ["off"]
    assert stop_event.wait_calls == [0.25, 0.25]


def test_start_recognizing_avoids_duplicate_blink_threads(monkeypatch):
    _, devices = initialize_fake_gpio(monkeypatch)
    yellow, blue, red = devices
    clear_device_calls(devices)
    threads = []
    events = []

    def event_class():
        event = FakeEvent(wait_results=[False, True])
        events.append(event)
        return event

    class DeferredThread:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args
            self.daemon = daemon
            self.started = False
            threads.append(self)

        def start(self):
            self.started = True

        def run(self):
            self.target(*self.args)

    monkeypatch.setattr(leds.threading, "Event", event_class)
    monkeypatch.setattr(leds.threading, "Thread", DeferredThread)

    leds.start_recognizing()
    leds.start_recognizing()

    assert len(threads) == 1
    assert threads[0].started is True
    assert threads[0].daemon is True

    threads[0].run()

    assert yellow.calls == ["off", "on", "off"]
    assert blue.calls == ["off"]
    assert red.calls == ["off"]
    assert events[0].wait_calls == [0.5, 0.5]


def test_access_statuses_drive_expected_leds(monkeypatch):
    _, devices = initialize_fake_gpio(monkeypatch)
    yellow, blue, red = devices
    clear_device_calls(devices)

    monkeypatch.setattr(leds.threading, "Event", FakeEvent)

    class ImmediateThread:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(leds.threading, "Thread", ImmediateThread)

    leds.access_granted()
    leds.access_denied()
    leds.bad_frame()

    assert "on" in blue.calls
    assert "on" in red.calls
    assert "on" in yellow.calls
    assert blue.calls[-1] == "off"
    assert red.calls[-1] == "off"
    assert yellow.calls[-1] == "off"


def test_stale_solid_thread_cannot_override_newer_status(monkeypatch):
    _, devices = initialize_fake_gpio(monkeypatch)
    _, blue, red = devices
    clear_device_calls(devices)
    threads = []

    monkeypatch.setattr(leds.threading, "Event", FakeEvent)

    class DeferredThread:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args
            threads.append(self)

        def start(self):
            return None

        def run(self):
            self.target(*self.args)

    monkeypatch.setattr(leds.threading, "Thread", DeferredThread)

    leds.access_granted()
    leds.access_denied()
    threads[0].run()
    threads[1].run()

    assert "on" not in blue.calls
    assert red.calls[-2:] == ["on", "off"]


def test_registration_indicators_drive_all_leds(monkeypatch):
    _, devices = initialize_fake_gpio(monkeypatch)
    clear_device_calls(devices)

    monkeypatch.setattr(leds.threading, "Event", FakeEvent)

    class ImmediateThread:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(leds.threading, "Thread", ImmediateThread)

    leds.registration_active()
    assert all(device.calls[-1] == "on" for device in devices)

    leds.registration_done()

    for device in devices:
        assert device.calls.count("on") == 2
        assert device.calls[-1] == "off"


def test_all_off_cancels_active_effect_and_clears_leds(monkeypatch):
    _, devices = initialize_fake_gpio(monkeypatch)
    clear_device_calls(devices)
    threads = []

    class DeferredThread:
        def __init__(self, target, args, daemon):
            threads.append(self)

        def start(self):
            return None

    monkeypatch.setattr(leds.threading, "Thread", DeferredThread)

    leds.start_recognizing()
    active_stop_event = leds.blink_stop
    leds.all_off()

    assert len(threads) == 1
    assert active_stop_event.is_set()
    assert all(device.calls[-1] == "off" for device in devices)


def test_stop_recognizing_cancels_blink_and_clears_leds(monkeypatch):
    _, devices = initialize_fake_gpio(monkeypatch)

    class DeferredThread:
        def __init__(self, target, args, daemon):
            return None

        def start(self):
            return None

    monkeypatch.setattr(leds.threading, "Thread", DeferredThread)

    leds.start_recognizing()
    active_stop_event = leds.blink_stop
    leds.stop_recognizing()

    assert active_stop_event.is_set()
    assert all(device.calls[-1] == "off" for device in devices)


def test_cleanup_closes_leds_and_factory_once(monkeypatch):
    factory, devices = initialize_fake_gpio(monkeypatch)

    leds.cleanup()
    leds.cleanup()

    assert leds.GPIO_AVAILABLE is False
    assert leds.PIN_FACTORY is None
    assert all(device.close_calls == 1 for device in devices)
    assert factory.close_calls == 1


def test_shutdown_uses_idempotent_gpio_cleanup(monkeypatch):
    factory, devices = initialize_fake_gpio(monkeypatch)

    leds.shutdown()
    leds.shutdown()

    assert leds.GPIO_AVAILABLE is False
    assert leds.PIN_FACTORY is None
    assert all(device.close_calls == 1 for device in devices)
    assert factory.close_calls == 1
