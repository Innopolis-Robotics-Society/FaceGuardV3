# ADR-009: Support Dual Camera Sources with a Latest-Frame Pipeline

**ID:** ADR-009
**Status:** Accepted

## Context

A browser may have its own camera, but a remote administration browser cannot access the webcam attached to the Raspberry Pi. Sending/capturing faster than inference creates stale-frame latency if frames are queued. Multiple capture loops or concurrent enrollment/recognition can also contend for a single device and non-thread-safe model state.

## Decision

Support two configured camera sources behind one frame contract:

- `browser`: capture in the SPA, send only when no response is outstanding, and have the backend drain already-queued WebSocket messages before decoding the newest one;
- `backend`: one `LatestFrameCamera` worker owns one V4L2 `VideoCapture`; successful captures replace one latest slot and consumers request a sequence newer than the one just processed.

`LatestFrameCamera` uses a process-wide non-blocking device lease, configures a one-frame OpenCV/V4L2 buffer where supported, copies a delivered frame, and releases capture in all stop/error paths. FastAPI's shared operation lock serializes recognition and enrollment. Each response correlates `box`, `frame_width`, `frame_height`, `frame_sequence`, and (in backend mode) the exact JPEG.

This decision governs the deployed FastAPI runtime. The older maintenance CLIs under `backend/faceguard/` retain direct `VideoCapture` calls and therefore must be run only while the service is stopped; they are not a second production capture path.

## Considered alternatives

- FIFO frame queue: rejected because increasing backlog increases decision age rather than usefulness.
- One capture loop per WebSocket: rejected because a physical camera has one owner and model operations are not intended to overlap.
- Browser-only capture: rejected for remote Pi-camera use.
- Backend-only capture: rejected because browser mode is useful for local development and client cameras.
- Native libcamera adapter: not selected in the current implementation; the backend adapter requires V4L2.

## Consequences

- Slow inference drops intermediate frames by design and acts on current input.
- There is one backend camera capture loop in the FastAPI runtime and bounded memory rather than a backlog.
- A busy second operation receives a bounded `operation_busy` result.
- Camera cleanup is part of WebSocket `finally` handling and application shutdown.
- CI can prove software ownership/replacement/cleanup with fake captures, but camera-driver behavior and Raspberry Pi image quality still require hardware verification.

## Quality requirements addressed

- [QR-001](../../quality-requirements.md#qr-001-recognition-response-time), alongside ADR-003 and ADR-005.
