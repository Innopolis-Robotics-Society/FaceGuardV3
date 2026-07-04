import threading
import time

YELLOW = None
BLUE = None
RED = None
GPIO_AVAILABLE = False

try:
    import gpiozero

    YELLOW = gpiozero.LED(17)
    BLUE = gpiozero.LED(27)
    RED = gpiozero.LED(22)
    GPIO_AVAILABLE = True
except Exception:
    pass


def all_leds_off():
    if not GPIO_AVAILABLE:
        return
    YELLOW.off()
    BLUE.off()
    RED.off()


def solid(led, duration):
    if not GPIO_AVAILABLE:
        return
    all_leds_off()
    led.on()
    time.sleep(duration)
    led.off()


def blink(led, stop_event, interval=0.5):
    if not GPIO_AVAILABLE:
        return
    while not stop_event.is_set():
        led.on()
        time.sleep(interval)
        led.off()
        time.sleep(interval)


blink_stop = threading.Event()
blink_thread = None


# Blink yellow while recognition is in progress
def start_recognizing():
    print("[LED] start_recognizing: yellow blinking")
    global blink_thread, blink_stop
    if not GPIO_AVAILABLE:
        return
    all_leds_off()
    blink_stop = threading.Event()
    blink_thread = threading.Thread(
        target=blink, args=(YELLOW, blink_stop), daemon=True
    )
    blink_thread.start()


# Stop yellow blinking when recognition stops
def stop_recognizing():
    print("[LED] stop_recognizing")
    if not GPIO_AVAILABLE:
        return
    blink_stop.set()
    all_leds_off()


# ACCESS GRANTED
# Stop yellow blinking, turn solid blue for 5 seconds
def access_granted():
    print("[LED] access_granted: solid blue 5s")
    stop_recognizing()
    threading.Thread(target=solid, args=(BLUE, 5), daemon=True).start()


# ACCESS DENIED
# Stop yellow blinking, turn solid red for 5 seconds
def access_denied():
    print("[LED] access_denied: solid red 5s")
    stop_recognizing()
    threading.Thread(target=solid, args=(RED, 5), daemon=True).start()


# Turn solid yellow for 5 seconds (poor lighting or blurry frame)
def bad_frame():
    print("[LED] bad_frame: solid yellow 5s")
    stop_recognizing()
    threading.Thread(target=solid, args=(YELLOW, 5), daemon=True).start()


# All LEDs are on during registration
def registration_active():
    print("[LED] registration_active: all LEDs on")
    if not GPIO_AVAILABLE:
        return
    all_leds_off()
    YELLOW.on()
    BLUE.on()
    RED.on()


# All LEDs on for 3 seconds after registration, then off
def registration_done():
    print("[LED] registration_done: all LEDs 3s then off")

    def run():
        if not GPIO_AVAILABLE:
            return
        all_leds_off()
        YELLOW.on()
        BLUE.on()
        RED.on()
        time.sleep(3)
        all_leds_off()

    threading.Thread(target=run, daemon=True).start()


# Turn all LEDs off (no face detected)
def all_off():
    print("[LED] all_off")
    stop_recognizing()
    if not GPIO_AVAILABLE:
        return
    all_leds_off()
