# ADR-007: Asynchronous GPIO Hardware Integration for Edge Devices

## Status

Accepted

## Context

During the deployment on Raspberry Pi 5 for MVP v2 and MVP v3, the system needed to actuate physical hardware (LEDs and eventually a motor for the door) based on face recognition results. 
The FaceGuardV3 backend is built using FastAPI, which relies on an asynchronous event loop (asyncio) to efficiently handle multiple WebSocket connections (for video streaming) and REST API requests concurrently.

Using synchronous hardware control libraries or blocking `time.sleep()` calls to hold LED states (e.g., turning an LED on for 5 seconds) would block the main event loop. If the event loop is blocked, the backend cannot process incoming video frames, causing the video stream to lag or drop connections, completely degrading the core recognition performance.

## Decision

We decided to handle GPIO interactions asynchronously, decoupling them from the main recognition pipeline:

1. **Hardware Abstraction:** We will wrap GPIO interactions (using lightweight libraries like `gpiozero` or standard `RPi.GPIO`) in an abstraction layer (`LEDController` / `MotorController`). This allows us to mock the hardware during CI testing or when developing on non-ARM devices (like laptops).
2. **Asynchronous Execution:** 
   - State changes (e.g., "turn on blue LED") are triggered instantly.
   - Durations (e.g., "keep it on for 5 seconds") are managed either using `asyncio.sleep()` inside `async` tasks or through FastAPI's `BackgroundTasks`.
3. **Decoupled Invocation:** Hardware commands are fired asynchronously after the database transaction has been successfully committed, ensuring that hardware actuation does not delay the API response sent to the React frontend.

## Consequences

**Positive:**
- The FastAPI event loop remains unblocked, allowing seamless WebSocket streaming and high FPS throughput.
- Developers can run the backend locally using dummy/mock hardware classes without requiring a Raspberry Pi.
- System feedback (LEDs) accurately reflects the real-time processing state without degrading performance.

**Negative:**
- Managing asynchronous tasks for hardware means we must handle potential race conditions (e.g., a new recognition event comes in while the LED is still holding the state for the previous one). We will address this by resetting the task or maintaining a state lock per pin.
- Testing hardware interactions in CI requires robust mocking, which slightly complicates the test suite.
