"""Generation-safe GPIO/LED feedback for Raspberry Pi deployments."""

import logging
import os
import threading

logger = logging.getLogger(__name__)

try:
    from gpiozero import LED as GPIOZeroLED
    from gpiozero.pins.lgpio import LGPIOFactory

    GPIO_IMPORT_ERROR = None
except Exception as error:  # GPIO dependencies are optional off-device.
    GPIOZeroLED = None
    LGPIOFactory = None
    GPIO_IMPORT_ERROR = error


YELLOW = None
BLUE = None
RED = None
PIN_FACTORY = None
GPIO_CHIP = 0
GPIO_AVAILABLE = False

_state_lock = threading.RLock()
_generation = 0
_stop_event = threading.Event()
_action_kind = None
_action_thread = None

# Kept public for operational visibility and compatibility with existing callers.
blink_stop = _stop_event
blink_thread = None


def _configured_chip() -> int:
    raw_value = os.environ.get("GPIO_CHIP", "0")
    try:
        chip = int(raw_value)
    except ValueError:
        logger.error("Invalid GPIO_CHIP=%r; GPIO will remain unavailable", raw_value)
        raise ValueError("GPIO_CHIP must be an integer")
    if chip < 0:
        raise ValueError("GPIO_CHIP must be non-negative")
    return chip


def _call_led(led, method: str) -> bool:
    try:
        getattr(led, method)()
        return True
    except Exception:
        logger.exception("GPIO LED operation %s failed", method)
        return False


def _all_off_locked() -> None:
    if not GPIO_AVAILABLE:
        return
    for led in (YELLOW, BLUE, RED):
        if led is not None:
            _call_led(led, "off")


def _cancel_locked() -> None:
    global _generation, _action_kind, _action_thread, blink_thread
    _generation += 1
    _stop_event.set()
    _action_kind = None
    _action_thread = None
    blink_thread = None


def _begin_locked(kind: str):
    global _stop_event, _action_kind, blink_stop
    _cancel_locked()
    _stop_event = threading.Event()
    blink_stop = _stop_event
    _action_kind = kind
    _all_off_locked()
    return _generation, _stop_event


def _is_owner_locked(generation: int, stop_event: threading.Event) -> bool:
    return GPIO_AVAILABLE and generation == _generation and stop_event is _stop_event


def _finish_worker(generation: int, stop_event: threading.Event) -> None:
    global _action_kind, _action_thread, blink_thread
    with _state_lock:
        if generation == _generation and stop_event is _stop_event:
            _action_kind = None
            _action_thread = None
            blink_thread = None


def _hold_then_off(
    led,
    duration: float,
    generation: int,
    stop_event: threading.Event,
) -> None:
    try:
        stop_event.wait(duration)
        with _state_lock:
            if _is_owner_locked(generation, stop_event) and not stop_event.is_set():
                _call_led(led, "off")
    finally:
        _finish_worker(generation, stop_event)


def _blink_worker(
    led,
    interval: float,
    generation: int,
    stop_event: threading.Event,
) -> None:
    led_is_on = True
    try:
        while True:
            if stop_event.wait(interval):
                return
            with _state_lock:
                if not _is_owner_locked(generation, stop_event):
                    return
                _call_led(led, "off" if led_is_on else "on")
                led_is_on = not led_is_on
    finally:
        _finish_worker(generation, stop_event)


def _start_worker_locked(target, args, generation, stop_event):
    global _action_thread
    thread = threading.Thread(
        target=target,
        args=(*args, generation, stop_event),
        daemon=True,
    )
    _action_thread = thread
    try:
        thread.start()
    except Exception:
        _cancel_locked()
        _all_off_locked()
        logger.exception("Unable to start LED feedback worker")
        return None
    return thread


def _solid_feedback(led, duration: float, kind: str) -> bool:
    with _state_lock:
        if not GPIO_AVAILABLE:
            return False
        generation, stop_event = _begin_locked(kind)
        # The adapter command is synchronous; only the hold duration is offloaded.
        if not _call_led(led, "on"):
            return False
        _start_worker_locked(
            _hold_then_off,
            (led, duration),
            generation,
            stop_event,
        )
    return True


def _close_resources(leds_to_close, factory) -> None:
    for led in leds_to_close:
        try:
            led.close()
        except Exception:
            logger.exception("Unable to close GPIO LED")
    if factory is not None:
        try:
            factory.close()
        except Exception:
            logger.exception("Unable to close GPIO pin factory")


def initialize_gpio() -> bool:
    """Initialize the configured gpiochip, falling back to software-only mode."""

    global BLUE, GPIO_AVAILABLE, GPIO_CHIP, PIN_FACTORY, RED, YELLOW
    cleanup()
    factory = None
    initialized_leds = []
    try:
        GPIO_CHIP = _configured_chip()
        if GPIO_IMPORT_ERROR is not None:
            raise RuntimeError(
                f"GPIO dependencies are unavailable: {GPIO_IMPORT_ERROR}"
            ) from GPIO_IMPORT_ERROR
        factory = LGPIOFactory(chip=GPIO_CHIP)
        yellow = GPIOZeroLED(17, pin_factory=factory)
        initialized_leds.append(yellow)
        blue = GPIOZeroLED(27, pin_factory=factory)
        initialized_leds.append(blue)
        red = GPIOZeroLED(22, pin_factory=factory)
        initialized_leds.append(red)
    except Exception:
        _close_resources(initialized_leds, factory)
        logger.warning(
            "GPIO initialization failed; LED feedback is disabled",
            exc_info=True,
        )
        return False

    with _state_lock:
        PIN_FACTORY = factory
        YELLOW = yellow
        BLUE = blue
        RED = red
        GPIO_AVAILABLE = True
        _all_off_locked()
    logger.info("GPIO initialized on gpiochip%s (BCM 17/27/22)", GPIO_CHIP)
    return True


def all_leds_off() -> None:
    with _state_lock:
        if not GPIO_AVAILABLE:
            return
        _cancel_locked()
        _all_off_locked()


def solid(led, duration: float) -> None:
    """Public compatibility helper for one generation-safe solid signal."""

    _solid_feedback(led, duration, "solid")


def blink(led, stop_event, interval: float = 0.5) -> None:
    """Blocking compatibility helper used by low-level tests and diagnostics."""

    led_is_on = False
    while GPIO_AVAILABLE and not stop_event.is_set():
        _call_led(led, "on")
        led_is_on = True
        if stop_event.wait(interval):
            break
        _call_led(led, "off")
        led_is_on = False
        if stop_event.wait(interval):
            break
    if GPIO_AVAILABLE and led_is_on:
        _call_led(led, "off")


def start_recognizing() -> None:
    global blink_thread
    with _state_lock:
        if not GPIO_AVAILABLE:
            return
        if _action_kind == "recognizing" and not _stop_event.is_set():
            return
        generation, stop_event = _begin_locked("recognizing")
        if not _call_led(YELLOW, "on"):
            return
        blink_thread = _start_worker_locked(
            _blink_worker,
            (YELLOW, 0.5),
            generation,
            stop_event,
        )


def stop_recognizing() -> None:
    all_leds_off()


def access_granted() -> None:
    _solid_feedback(BLUE, 5.0, "access_granted")


def access_denied() -> None:
    _solid_feedback(RED, 5.0, "access_denied")


def bad_frame() -> None:
    _solid_feedback(YELLOW, 5.0, "bad_frame")


def registration_active() -> None:
    with _state_lock:
        if not GPIO_AVAILABLE:
            return
        _begin_locked("registration_active")
        for led in (YELLOW, BLUE, RED):
            _call_led(led, "on")


def _registration_timeout(
    generation: int,
    stop_event: threading.Event,
) -> None:
    try:
        stop_event.wait(3.0)
        with _state_lock:
            if _is_owner_locked(generation, stop_event) and not stop_event.is_set():
                _all_off_locked()
    finally:
        _finish_worker(generation, stop_event)


def registration_done() -> None:
    with _state_lock:
        if not GPIO_AVAILABLE:
            return
        generation, stop_event = _begin_locked("registration_done")
        for led in (YELLOW, BLUE, RED):
            _call_led(led, "on")
        _start_worker_locked(
            _registration_timeout,
            (),
            generation,
            stop_event,
        )


def all_off() -> None:
    all_leds_off()


def cleanup() -> None:
    """Cancel workers, turn LEDs off, and close every GPIO resource."""

    global BLUE, GPIO_AVAILABLE, PIN_FACTORY, RED, YELLOW
    with _state_lock:
        thread = _action_thread
        _cancel_locked()
        _all_off_locked()
        leds_to_close = [led for led in (YELLOW, BLUE, RED) if led is not None]
        factory = PIN_FACTORY
        GPIO_AVAILABLE = False
        YELLOW = None
        BLUE = None
        RED = None
        PIN_FACTORY = None

    if thread is not None and thread is not threading.current_thread():
        thread.join(timeout=1.0)
    _close_resources(leds_to_close, factory)


def shutdown() -> None:
    cleanup()


initialize_gpio()
