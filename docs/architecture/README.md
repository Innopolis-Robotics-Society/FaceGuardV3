# Architecture

FaceGuardV3 is a three-service edge application: a React SPA, a FastAPI backend, and local PostgreSQL. The frontend owns presentation and, in browser-camera mode, capture. The backend owns authentication, operation serialization, frame processing, liveness/recognition orchestration, persistence, and optional GPIO feedback.

## Static view

[Component diagram source](static-view/component-diagram.puml)

The implemented components are:

- React/Vite UI with authenticated REST calls, authenticated WebSockets, browser/backend camera modes, and exact-frame bounding-box projection.
- FastAPI REST and WebSocket boundary. Recognition and enrollment share one `asyncio.Lock`, so model state and a backend camera cannot be used concurrently.
- `LatestFrameCamera`, which owns at most one OpenCV `VideoCapture` worker process-wide and replaces a single latest-frame slot. There is no frame queue.
- `FaceProviderInterface` and the InsightFace/MiniFASNet implementation. Liveness status is evaluated before identity similarity matching.
- PostgreSQL access through a `ThreadedConnectionPool`. Employee writes, duplicate checks, temporary-access validation, and logs remain in the backend data-access layer.
- Generation-safe `leds.py` GPIO control using `gpiozero`/`LGPIOFactory`. GPIO absence disables feedback without disabling the API.

The deployed FastAPI camera source is deliberately an adapter boundary. `browser` mode sends one JPEG at a time and waits for its response. `backend` mode reads a V4L2 device in one capture loop and gives slow consumers only the newest frame. Legacy maintenance CLIs under `backend/faceguard/` predate this runtime and open OpenCV directly; they are not container entry points and must not share a device with the service.

## Dynamic view

[Sequence diagram source](dynamic-view/sequence-diagram.puml)

The sequence source covers the maintained runtime scenarios rather than only a happy path:

- REST login and JWT-authenticated WebSocket opening;
- normal recognition, temporary-access-aware matching, and exact frame/bbox response;
- enrollment and duplicate registration through the REST/database boundary;
- liveness rejection before matching;
- LED mapping and generation replacement;
- operation-busy handling; and
- disconnect/shutdown cleanup of camera, GPIO, task, lock, and database pool.

The JPEG/bbox contract is important: `frame_width`, `frame_height`, `frame_sequence`, and `box` describe the same image. In backend mode that image is returned by the server; in browser mode the client retains the one in-flight JPEG until its response arrives.

## Deployment view

[Deployment diagram source](deployment-view/deployment-diagram.puml)

The base Compose file exposes frontend `3000`, backend `8000`, and PostgreSQL `5432` for development. All services share the `faceguard` bridge network; `pgdata` persists database state and `docker/insightface_models` is mounted into the backend.

The Raspberry Pi override must be applied together with the base file. It removes the PostgreSQL host port, selects backend camera mode, and maps exactly the configured `/dev/videoN` and `/dev/gpiochipN` devices. The current adapter requires a V4L2-visible camera; native libcamera capture is outside the implementation. Browser mode instead uses the client device camera and maps no camera into the backend.

There is no motor or physical door actuator in this repository. GPIO controls only the three documented LEDs. Ordinary GitHub-hosted CI validates the software adapters but has neither Raspberry Pi device mappings nor physical latency evidence.

## Architecture decision records

- [ADR-001 — Face recognition provider abstraction](adr/ADR-001-face-recognition-provider-abstraction.md) (`QR-003`).
- [ADR-002 — Reject non-real provider status before matching](adr/ADR-002-reject-on-status-code-before-embedding-match.md) (`QR-002`).
- [ADR-003 — In-process recognition pipeline](adr/ADR-003-synchronous-recognition-pipeline-for-response-time.md) (`QR-001`).
- [ADR-004 — Temporary-access timestamps and application enforcement](adr/ADR-004-temporary-access-window-enforcement.md) (`QR-004`).
- [ADR-005 — React/FastAPI WebSocket separation](adr/ADR-005-decouple-frontend-backend-for-websocket-streaming.md) (`QR-001`).
- [ADR-006 — Local PostgreSQL](adr/ADR-006-local-database-for-offline-reliability.md).
- [ADR-007 — Non-blocking, generation-safe GPIO feedback](adr/ADR-007-gpio-hardware-integration.md) (`QR-006`).
- [ADR-008 — Atomic duplicate registration prevention](adr/ADR-008-atomic-duplicate-registration-prevention.md) (`QR-005`).
- [ADR-009 — Dual camera sources with a latest-frame pipeline](adr/ADR-009-dual-camera-latest-frame-pipeline.md) (`QR-001`).

ADRs describe durable choices and their consequences. Passing a software adapter test does not, by itself, prove camera/liveness accuracy or physical GPIO latency; those limitations remain explicit in the QRT documentation.
