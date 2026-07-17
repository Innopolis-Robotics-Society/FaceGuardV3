# ADR-003: Keep Recognition In-Process and Direct

**ID:** ADR-003
**Status:** Accepted

## Context

FaceGuard targets one local entry point and a small employee database. Moving each frame through an external job queue or cloud inference service would add latency, an online dependency, and result-correlation complexity. Earlier UI-driven model loading also caused freezes. QR-001 requires a decision visible within 3 seconds under its stated hardware conditions.

## Decision

Keep model inference, liveness, similarity comparison, and access decision in the FastAPI backend process. A frame is handled as one direct, ordered operation; CPU/blocking functions run through FastAPI's worker-thread boundary so they do not block the event loop. Models are initialized once at application startup, and recognition/enrollment are serialized by one operation lock. No external queue or inference service is introduced for the current single-entry deployment.

## Considered alternatives

- An external/cloud inference service: rejected because offline operation and predictable local latency are required.
- A persistent background job queue: rejected because only one current decision is useful and queued stale frames conflict with the latest-frame policy.
- Running ML directly on the event loop: rejected because it would block WebSocket handling despite inference remaining in-process.

## Consequences

- The pipeline is simple and offline, and response correlation is explicit.
- A slow consumer skips old camera frames rather than building a backlog.
- The design intentionally does not support simultaneous recognition/enrollment or multiple backend cameras.
- Horizontal/multi-camera scaling would require revisiting process ownership, model concurrency, and similarity indexing.
- `tests/quality/test_recognition_performance.py` is only a deterministic software-overhead check because its fake detector returns immediately. It does not prove QR-001's camera + real model + Raspberry Pi + UI latency; QRT-001 remains only partially automated until that environment is measured.

## Quality requirements addressed

- [QR-001](../../quality-requirements.md#qr-001-recognition-response-time), together with ADR-005 and ADR-009.
