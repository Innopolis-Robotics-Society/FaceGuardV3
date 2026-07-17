# Testing and QA

## Critical modules and line coverage

The critical list follows the paths that can grant/reject access, accept an enrollment, own camera/GPIO resources, or authenticate callers. Pure drawing/UI helpers, the legacy single-user CLI, and log presentation are tested but are not used as substitutes for these gates.

| Critical module | Risk covered | Required | Local audit coverage (2026-07-17) | Result |
|---|---|---:|---:|---|
| `backend/main.py` | Recognition/enrollment orchestration, operation lock, WebSocket/frame contract, lifecycle | 30% | 70.40% | Pass |
| `backend/camera.py` | One capture owner, latest-frame replacement, release/error paths | 30% | 89.90% | Pass |
| `backend/db/employees_db.py` | Employee writes, duplicate integrity, temporary access | 30% | 84.67% | Pass |
| `backend/db/connection.py` | Thread-safe pooled connection/close lifecycle | 30% | 100.00% | Pass |
| `backend/faceguard/business_logic.py` | Access decision and non-real rejection | 30% | 100.00% | Pass |
| `backend/faceguard/recognize.py` | InsightFace/liveness adapter, embeddings, thresholds | 30% | 100.00% | Pass |
| `backend/core/security.py` | JWT signing, expiry/signature/subject validation | 30% | 96.67% | Pass |
| `backend/leds.py` | Color mapping, stale-worker exclusion, chip selection, cleanup | 30% | 83.77% | Pass |

The complete audit run covered 1,366 backend statements at 85.07% and passed 139 tests. The policy is enforced from `reports/coverage.json` by `scripts/check_critical_coverage.py`; a high global percentage cannot hide a critical module below 30%.

## Test suites

| Suite | Behavior/risk focus | Latest local result |
|---|---|---:|
| `tests/unit` | Recognition math/orchestration, liveness integration, camera ownership/latest-frame/release, JWT/WS auth, bbox metadata, mutual exclusion, database rollback/timestamps, duplicate comparison, GPIO generations/cleanup | 121 passed |
| `tests/integration` | Provider-to-access-decision flows and real FastAPI WebSocket authentication boundary | 6 passed |
| `tests/quality` with PostgreSQL enabled | Supporting QRT-001/002, implemented QRT-003/005, QR-006 software precheck | 12 passed |
| Frontend Vitest | Runtime URLs/subprotocol, bbox projection, browser/backend modes, one browser frame in flight and exact response JPEG | 8 passed |

QRT-004 is deliberately co-located with the detailed temporary-access data-layer tests in `tests/unit/test_temporary_access.py`. Test location does not change its stable QRT ID. See [QRT status](quality-requirement-tests.md) for the evidence boundary: QRT-005 is Implemented, while QRT-001/002 are partial and physical QRT-006 remains Planned.

## Backend commands

```bash
PYTHONPATH=backend:. .venv/bin/pytest tests/unit -q
PYTHONPATH=backend:. .venv/bin/pytest tests/integration -q
PYTHONPATH=backend:. .venv/bin/pytest tests/quality -q
```

The last command skips two PostgreSQL QRT-005 cases unless the explicitly isolated database is enabled:

```bash
docker compose -p faceguardv3-qrt -f docker/docker-compose.test.yml up -d --wait
PYTHONPATH=backend:. RUN_POSTGRES_INTEGRATION=1 \
  DB_HOST=127.0.0.1 DB_PORT=55432 \
  POSTGRES_DB=faceguard_test POSTGRES_USER=faceguard_test \
  POSTGRES_PASSWORD=faceguard_test \
  JWT_SECRET=faceguard-qrt-signing-secret-at-least-32-bytes \
  .venv/bin/pytest tests/quality -q
```

The QRT fixture refuses to run unless the database name is exactly `faceguard_test` and truncates only that isolated employee table.

## Coverage and evidence

With the same PostgreSQL environment:

```bash
mkdir -p reports
PYTHONPATH=backend:. RUN_POSTGRES_INTEGRATION=1 \
  DB_HOST=127.0.0.1 DB_PORT=55432 \
  POSTGRES_DB=faceguard_test POSTGRES_USER=faceguard_test \
  POSTGRES_PASSWORD=faceguard_test \
  JWT_SECRET=faceguard-qrt-signing-secret-at-least-32-bytes \
  .venv/bin/pytest tests -q --cov=backend --cov-report=term-missing \
  --cov-report=json:reports/coverage.json \
  --cov-report=xml:reports/coverage.xml --cov-fail-under=30
.venv/bin/python scripts/check_critical_coverage.py \
  --coverage-file reports/coverage.json --threshold 30
```

Local evidence paths are `reports/coverage.json` and `reports/coverage.xml`; generated coverage is ignored by Git. CI uploads both as the `backend-coverage` artifact and prints every critical percentage in the gate log.

## Frontend and static checks

```bash
cd frontend
npm ci
npm test
npm run lint
npm run build
npm audit --audit-level=high
```

Backend source gates:

```bash
.venv/bin/black --check backend tests scripts/check_critical_coverage.py
.venv/bin/flake8 backend tests scripts/check_critical_coverage.py \
  --count --show-source --statistics --max-line-length=120
.venv/bin/bandit -q -r backend
```

Configuration/docs gates are the two Compose `config --quiet` commands in the root README, `mkdocs build --strict --site-dir /tmp/faceguardv3-site`, and the separate Lychee workflow.

The 2026-07-17 audit also built the ordinary backend, Docker Hub backend, and frontend Dockerfiles. Both backend images passed `pip check` and initialized the repository MiniFASNet and InsightFace `buffalo_s` assets; the ordinary image then started against the isolated PostgreSQL service and returned `/health` with `models_ready: true`. The frontend preview image also started and served HTTP. These are local container smoke checks, not ordinary PR CI or physical-camera/model-accuracy evidence; the reproducible build commands are in the root README.

## CI gates

`.github/workflows/ci.yml` has three mandatory jobs:

- **Backend tests, QRT and coverage:** PostgreSQL 15 service, Black, Flake8, Bandit, separate unit/integration/quality steps, full coverage, per-critical-module gate, XML/JSON artifact.
- **Frontend tests, lint and build:** Node 22, `npm ci`, Vitest, Oxlint, TypeScript/Vite production build, high-severity dependency audit.
- **Compose and documentation validation:** base and combined Pi Compose validation plus strict MkDocs build.

`.github/workflows/lychee.yml` remains the Markdown link gate. No required test uses `continue-on-error`.

## What CI does not prove

| Software logic automated in CI | Hardware/in-environment behavior still required |
|---|---|
| One capture factory/lease, replace-only frame slot, stop/release | V4L2 driver stability, Pi CSI exposure, camera quality/FPS |
| Liveness status is required before matching | 9/10 printed-photo/phone-screen attacks with real camera/model/lighting |
| Correct LED adapter mapping, generation ownership, chip selection, cleanup | Electrical wiring, visible color, physical transition within 0.5 seconds |
| Fake-backed recognition overhead | QR-001 end-to-end Raspberry Pi camera/model/database/WebSocket/UI latency |
| Base/Pi Compose schema and exact device mapping strings | The named devices exist and permissions work on the customer's Pi |

These limitations are not failures hidden by skips: QRT-001/002 remain partial and QRT-006 remains Planned until their stated measurable environments are automated.
