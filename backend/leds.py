import logging
import os
import threading

# Uvicorn configures this logger before importing the FastAPI application, so
# GPIO initialization and runtime state changes are visible in container logs.
LOGGER = logging.getLogger("uvicorn.error.leds")

try:
    from gpiozero import LED as GPIOZeroLED
    from gpiozero.pins.lgpio import LGPIOFactory

    GPIO_IMPORT_ERROR = None
except Exception as exc:  # GPIO dependencies are optional outside Raspberry Pi
    GPIOZeroLED = None
    LGPIOFactory = None
    GPIO_IMPORT_ERROR = exc


YELLOW = None
BLUE = None
RED = None
PIN_FACTORY = None
GPIO_CHIP = 0
GPIO_AVAILABLE = False

_state_lock = threading.RLock()
_action_generation = 0
_action_stop = threading.Event()
_action_kind = None
_action_thread = None

# Retained as module attributes for compatibility and observability.
blink_stop = _action_stop
blink_thread = None


def _read_gpio_chip():
    raw_value = os.environ.get("GPIO_CHIP", "0")
    try:
        return int(raw_value)
    except ValueError:
        LOGGER.error("[LED] Invalid GPIO_CHIP=%r; using gpiochip0", raw_value)
        return 0


def _log_skipped(action):
    LOGGER.warning("[LED] %s skipped: GPIO is unavailable", action)


def _call_led_locked(led, method):
    try:
        getattr(led, method)()
        return True
    except Exception as exc:
        LOGGER.exception("[LED] Failed to turn LED %s: %s", method, exc)
        return False


def _all_leds_off_locked():
    if not GPIO_AVAILABLE:
        return
    for led in (YELLOW, BLUE, RED):
        if led is not None:
            _call_led_locked(led, "off")


def _cancel_action_locked():
    global _action_generation, _action_kind, _action_thread, blink_thread

    _action_generation += 1
    _action_stop.set()
    _action_kind = None
    _action_thread = None
    blink_thread = None


def _begin_action_locked(kind, stop_event=None):
    global _action_stop, _action_kind, blink_stop

    _cancel_action_locked()
    _action_stop = stop_event if stop_event is not None else threading.Event()
    _action_kind = kind
    if kind == "blink":
        blink_stop = _action_stop
    _all_leds_off_locked()
    return _action_generation, _action_stop


def _action_owns_state_locked(generation, stop_event):
    return (
        GPIO_AVAILABLE
        and generation == _action_generation
        and stop_event is _action_stop
    )


def _action_is_current_locked(generation, stop_event):
    return _action_owns_state_locked(generation, stop_event) and not stop_event.is_set()


def _finish_action(generation, stop_event):
    global _action_kind, _action_thread, blink_thread

    with _state_lock:
        if generation == _action_generation and stop_event is _action_stop:
            _action_kind = None
            _action_thread = None
            blink_thread = None


def _close_resources(leds, factory):
    for led in leds:
        try:
            led.close()
        except Exception as exc:
            LOGGER.exception("[LED] Failed to close LED device: %s", exc)
    if factory is not None:
        try:
            factory.close()
        except Exception as exc:
            LOGGER.exception("[LED] Failed to close GPIO pin factory: %s", exc)


def initialize_gpio():
    global BLUE, GPIO_AVAILABLE, GPIO_CHIP, PIN_FACTORY, RED, YELLOW

    cleanup()
    GPIO_CHIP = _read_gpio_chip()
    factory = None
    created_leds = []

    try:
        if GPIO_IMPORT_ERROR is not None:
            raise RuntimeError(
                f"GPIO dependencies are unavailable: {GPIO_IMPORT_ERROR}"
            ) from GPIO_IMPORT_ERROR
        factory = LGPIOFactory(chip=GPIO_CHIP)
        actual_chip = getattr(factory, "_chip", GPIO_CHIP)
        if actual_chip != GPIO_CHIP:
            raise RuntimeError(
                f"LGPIOFactory opened gpiochip{actual_chip}, "
                f"but GPIO_CHIP requested gpiochip{GPIO_CHIP}"
            )
        yellow = GPIOZeroLED(17, pin_factory=factory)
        created_leds.append(yellow)
        blue = GPIOZeroLED(27, pin_factory=factory)
        created_leds.append(blue)
        red = GPIOZeroLED(22, pin_factory=factory)
        created_leds.append(red)
    except Exception as exc:
        _close_resources(created_leds, factory)
        LOGGER.exception(
            "[LED] GPIO initialization failed for gpiochip%d: %s", GPIO_CHIP, exc
        )
        return False

    with _state_lock:
        PIN_FACTORY = factory
        YELLOW = yellow
        BLUE = blue
        RED = red
        GPIO_AVAILABLE = True
        _all_leds_off_locked()

    LOGGER.info(
        "[LED] GPIO initialized successfully using gpiochip%d (BCM pins 17, 27, 22)",
        GPIO_CHIP,
    )
    return True


def all_leds_off():
    with _state_lock:
        if not GPIO_AVAILABLE:
            _log_skipped("all_leds_off")
            return
        _cancel_action_locked()
        _all_leds_off_locked()
    LOGGER.info("[LED] all_leds_off: all physical LEDs are off")


def solid(led, duration, _generation=None, _stop_event=None):
    if _generation is None:
        with _state_lock:
            if not GPIO_AVAILABLE:
                _log_skipped("solid")
                return
            generation, stop_event = _begin_action_locked("solid")
    else:
        generation = _generation
        stop_event = _stop_event

    try:
        with _state_lock:
            if not _action_is_current_locked(generation, stop_event):
                return
            if not _call_led_locked(led, "on"):
                return

        stop_event.wait(duration)
    finally:
        with _state_lock:
            if _action_owns_state_locked(generation, stop_event):
                _call_led_locked(led, "off")
        _finish_action(generation, stop_event)


def blink(led, stop_event, interval=0.5, _generation=None):
    if _generation is None:
        with _state_lock:
            if not GPIO_AVAILABLE:
                _log_skipped("blink")
                return
            generation, stop_event = _begin_action_locked("blink", stop_event)
    else:
        generation = _generation

    led_is_on = False
    try:
        while not stop_event.is_set():
            with _state_lock:
                if not _action_is_current_locked(generation, stop_event):
                    return
                if not _call_led_locked(led, "on"):
                    return
                led_is_on = True

            if stop_event.wait(interval):
                return

            with _state_lock:
                if not _action_is_current_locked(generation, stop_event):
                    return
                if not _call_led_locked(led, "off"):
                    return
                led_is_on = False

            if stop_event.wait(interval):
                return
    finally:
        with _state_lock:
            if led_is_on and _action_owns_state_locked(generation, stop_event):
                _call_led_locked(led, "off")
        _finish_action(generation, stop_event)


def _start_background_action(action, kind, target, args):
    global _action_thread

    with _state_lock:
        if not GPIO_AVAILABLE:
            _log_skipped(action)
            return False
        generation, stop_event = _begin_action_locked(kind)
        thread = threading.Thread(
            target=target,
            args=(*args, generation, stop_event),
            daemon=True,
        )
        _action_thread = thread
        try:
            thread.start()
        except Exception as exc:
            _cancel_action_locked()
            _all_leds_off_locked()
            LOGGER.exception("[LED] Failed to start %s worker: %s", action, exc)
            return False
        return True


# Blink yellow while recognition is in progress.
def start_recognizing():
    global _action_thread, blink_thread

    with _state_lock:
        if not GPIO_AVAILABLE:
            _log_skipped("start_recognizing")
            return
        if _action_kind == "blink" and not _action_stop.is_set():
            LOGGER.info("[LED] start_recognizing: yellow blink is already active")
            return

        generation, stop_event = _begin_action_locked("blink")
        thread = threading.Thread(
            target=blink,
            args=(YELLOW, stop_event, 0.5, generation),
            daemon=True,
        )
        _action_thread = thread
        blink_thread = thread
        try:
            thread.start()
        except Exception as exc:
            _cancel_action_locked()
            _all_leds_off_locked()
            LOGGER.exception("[LED] Failed to start recognition blink worker: %s", exc)
            return

    LOGGER.info("[LED] start_recognizing: yellow blinking")


# Stop recognition feedback and turn every LED off.
def stop_recognizing():
    with _state_lock:
        if not GPIO_AVAILABLE:
            _log_skipped("stop_recognizing")
            return
        _cancel_action_locked()
        _all_leds_off_locked()
    LOGGER.info("[LED] stop_recognizing: all physical LEDs are off")


def access_granted():
    if _start_background_action("access_granted", "solid", solid, (BLUE, 5)):
        LOGGER.info("[LED] access_granted: solid blue for 5 seconds")


def access_denied():
    if _start_background_action("access_denied", "solid", solid, (RED, 5)):
        LOGGER.info("[LED] access_denied: solid red for 5 seconds")


def bad_frame():
    if _start_background_action("bad_frame", "solid", solid, (YELLOW, 5)):
        LOGGER.info("[LED] bad_frame: solid yellow for 5 seconds")


def registration_active():
    with _state_lock:
        if not GPIO_AVAILABLE:
            _log_skipped("registration_active")
            return
        _begin_action_locked("registration_active")
        for led in (YELLOW, BLUE, RED):
            _call_led_locked(led, "on")
    LOGGER.info("[LED] registration_active: all physical LEDs are on")


def _finish_registration(generation, stop_event):
    try:
        if stop_event.wait(3):
            return
        with _state_lock:
            if _action_is_current_locked(generation, stop_event):
                _all_leds_off_locked()
    finally:
        _finish_action(generation, stop_event)


def registration_done():
    global _action_thread

    with _state_lock:
        if not GPIO_AVAILABLE:
            _log_skipped("registration_done")
            return
        generation, stop_event = _begin_action_locked("registration_done")
        for led in (YELLOW, BLUE, RED):
            _call_led_locked(led, "on")
        thread = threading.Thread(
            target=_finish_registration,
            args=(generation, stop_event),
            daemon=True,
        )
        _action_thread = thread
        try:
            thread.start()
        except Exception as exc:
            _cancel_action_locked()
            _all_leds_off_locked()
            LOGGER.exception(
                "[LED] Failed to start registration completion worker: %s", exc
            )
            return

    LOGGER.info("[LED] registration_done: all LEDs on for 3 seconds")


def all_off():
    with _state_lock:
        if not GPIO_AVAILABLE:
            _log_skipped("all_off")
            return
        _cancel_action_locked()
        _all_leds_off_locked()
    LOGGER.info("[LED] all_off: all physical LEDs are off")


def cleanup():
    global BLUE, GPIO_AVAILABLE, PIN_FACTORY, RED, YELLOW

    with _state_lock:
        leds_to_close = [led for led in (YELLOW, BLUE, RED) if led is not None]
        factory_to_close = PIN_FACTORY
        had_resources = bool(leds_to_close or factory_to_close is not None)

        _cancel_action_locked()
        _all_leds_off_locked()
        GPIO_AVAILABLE = False
        YELLOW = None
        BLUE = None
        RED = None
        PIN_FACTORY = None

    _close_resources(leds_to_close, factory_to_close)
    if had_resources:
        LOGGER.info("[LED] GPIO resources closed")


def shutdown():
    """Release GPIO resources during the FastAPI shutdown lifecycle."""
    cleanup()


initialize_gpio()
