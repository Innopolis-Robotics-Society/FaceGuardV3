# AI Agent Guidance

## Current system

- React/Vite SPA in `frontend/`; FastAPI REST/WebSockets in `backend/main.py`; local PostgreSQL; optional Raspberry Pi GPIO LEDs.
- The deployed FastAPI camera source is `browser` (one JPEG in flight) or `backend` (`LatestFrameCamera`: one V4L2 capture loop, one replace-only latest slot). The maintenance CLI modules under `backend/faceguard/` still open OpenCV directly and must not run beside the service against the same device.
- Recognition/enrollment share an operation lock. Responses correlate exact JPEG/bbox/dimensions/sequence.
- JWT is mandatory. REST uses Bearer auth; WebSockets use `faceguard.jwt` and `bearer.<JWT>` subprotocols, never a query token.
- Duplicate check and insert are one PostgreSQL transaction under an advisory lock (ADR-008). GPIO workers are generation-safe and cleaned up (ADR-007).
- There is no Streamlit runtime, motor, door controller, native libcamera adapter, or physical-hardware CI runner.

## Rules

1. Never read into output, change, or commit real `.env`, credentials, biometric data, or customer employee records. Use only sanitized examples/test databases.
2. Read the relevant view and ADR before structural changes. Preserve the provider boundary, latest-frame/no-backlog semantics, operation lock, transactional duplicate boundary, and cleanup lifecycle unless an explicit superseding ADR is justified.
3. Do not block the FastAPI event loop with inference, database, GPIO duration waits, or camera reads. Immediate adapter commands may be synchronous; blocking work uses the worker boundary.
4. Do not add unrelated refactors or tests created only for quantity/coverage. Tests must assert a behavior or risk and fail for a real regression.
5. Never describe fake GPIO as physical latency, fake face status as 9/10 photo-attack accuracy, or instant fake inference as Raspberry Pi response-time evidence.
6. Keep base and Pi Compose roles distinct. Pi mode uses both Compose files and maps the configured `/dev/videoN` and `/dev/gpiochipN` only into the backend.

## Required checks

```bash
PYTHONPATH=backend:. .venv/bin/pytest tests/unit -q
PYTHONPATH=backend:. .venv/bin/pytest tests/integration -q
PYTHONPATH=backend:. .venv/bin/pytest tests/quality -q
.venv/bin/black --check backend tests scripts/check_critical_coverage.py
.venv/bin/flake8 backend tests scripts/check_critical_coverage.py --max-line-length=120
.venv/bin/bandit -q -r backend
```

For QRT-005/full coverage, use only `docker/docker-compose.test.yml` and `POSTGRES_DB=faceguard_test` as documented in `docs/testing.md`. Run frontend `npm ci`, `npm test`, `npm run lint`, `npm run build`, and `npm audit --audit-level=high` after frontend changes. Validate base and combined Pi Compose and run `mkdocs build --strict --site-dir /tmp/faceguardv3-site` after configuration/documentation changes.

Report commands and limitations honestly; do not commit or push unless explicitly requested.
