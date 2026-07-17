# ADR-007: Non-Blocking, Generation-Safe GPIO LED Feedback

**ID:** ADR-007
**Status:** Accepted

## Context

Recognition continues while an LED remains on for several seconds. Blocking sleeps would stop WebSocket work, while detached old blink/hold threads could later turn off a newer result. Raspberry Pi gpiochip numbering also varies, and development/CI usually has no GPIO device.

## Decision

Implement LED feedback in `backend/leds.py` with `gpiozero.LED` and `LGPIOFactory(chip=GPIO_CHIP)` using BCM pins 17 (yellow), 27 (blue), and 22 (red).

- The adapter `.on()` command is issued synchronously when feedback is selected.
- Only blink/hold duration waits run in daemon worker threads.
- Every action receives a generation and cancellation event. A stale worker may mutate LEDs only if it still owns the current generation.
- Recognition/enrollment orchestration invokes GPIO through FastAPI's worker-thread boundary.
- Initialization failure enters an explicit no-GPIO mode rather than failing the API.
- Shutdown cancels and joins the owned worker, turns all LEDs off, closes LED objects, and closes the pin factory.

The repository implements LEDs only; it has no motor or door-controller adapter.

## Considered alternatives

- Blocking `sleep` in the request/event-loop path: rejected because it stops frame processing.
- An unmanaged thread per signal: rejected because stale threads race newer states and leak resources.
- Hard-code a Raspberry Pi gpiochip: rejected because host/controller numbering differs.
- Treat a fake GPIO timing test as physical evidence: rejected because it cannot measure the electrical LED transition.

## Consequences

- Software dispatch is immediate and independently testable, and old workers cannot override a new result.
- The Pi Compose override must map the selected `/dev/gpiochipN` to the same container-visible number configured in `GPIO_CHIP`.
- GPIO absence is observable through logs and `/health`, while recognition remains usable.
- The software precheck in `tests/quality/test_hardware_feedback.py` proves call ordering only. QR-006 still needs automated Raspberry Pi hardware-in-the-loop measurement, so QRT-006 remains Planned.

## Quality requirements addressed

- [QR-006](../../quality-requirements.md#qr-006-hardware-feedback-latency).
