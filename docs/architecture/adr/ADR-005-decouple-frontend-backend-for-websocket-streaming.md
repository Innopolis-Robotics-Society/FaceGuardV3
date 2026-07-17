# ADR-005: Decouple React Presentation from FastAPI Processing

**ID:** ADR-005
**Status:** Accepted
**Date:** 2026-07-09

## Context

The previous Streamlit UI reran server-side presentation code during frame processing and coupled page state to inference. FaceGuard needs a responsive SPA, an explicit authenticated API, and the ability to use either a client-attached camera or a camera attached to a remote Raspberry Pi.

## Decision

Use a React/Vite SPA for presentation and FastAPI for REST, WebSocket, recognition, persistence, and GPIO orchestration.

- REST requests carry a Bearer JWT.
- Recognition/enrollment WebSockets carry `faceguard.jwt` plus `bearer.<JWT>` subprotocols; tokens are not URL query parameters.
- In `browser` mode the SPA captures JPEGs and permits only one outstanding frame.
- In `backend` mode FastAPI owns the Pi V4L2 camera and returns the processed JPEG.
- Both modes return bbox, dimensions, and sequence for the exact processed frame.
- Service URL and camera mode `VITE_*` settings are compiled at frontend build time.

## Considered alternatives

- Continue with Streamlit: rejected because it couples UI reruns and inference state.
- Browser-only capture: rejected because a remote administration browser cannot access the camera physically attached to the Pi.
- Put JWTs in WebSocket query strings: rejected because URLs are commonly logged.
- A single HTTP request per frame: rejected due to repeated request setup and poorer stream lifecycle semantics.

## Consequences

- UI, data APIs, and ML logic have clear boundaries and independent tests.
- Two technology stacks and compatible runtime URL configuration must be maintained.
- A reverse proxy must forward WebSocket upgrades and subprotocol headers.
- This decision removes the old UI bottleneck but does not itself prove the real-hardware 3-second QR-001 target; no unsupported 1.1-second claim is made.

## Quality requirements addressed

- [QR-001](../../quality-requirements.md#qr-001-recognition-response-time).
