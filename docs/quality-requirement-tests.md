# Quality Requirement Tests

## Status summary

| ID | Linked QR | Automated measurable QR scenario? | Runs in CI | Status |
|---|---|---|---|---|
| QRT-001 | QR-001 | No — software overhead only; no real camera/model/UI timing | Supporting check runs | Partially automated |
| QRT-002 | QR-002 | No — rejection contract only; no ten physical attacks | Supporting check runs | Partially automated |
| QRT-003 | QR-003 | Yes, at the provider contract boundary | Yes | Implemented |
| QRT-004 | QR-004 | Yes, deterministic access-window behavior | Yes | Implemented |
| QRT-005 | QR-005 | Yes, FastAPI + real PostgreSQL with deterministic embeddings | Yes | Implemented |
| QRT-006 | QR-006 | No — physical LED transition is not measured | Software precheck runs | Planned |

## QRT-001: Recognition Pipeline Response Time

**Linked quality requirement:** `QR-001`

**Current automated check:** `tests/quality/test_recognition_performance.py` times embedding/decision software paths using a controlled frame and a fake face app.

**Command:** `PYTHONPATH=backend:. .venv/bin/pytest tests/quality/test_recognition_performance.py -q`

**Observed/expected result:** The fake-backed calls complete within 3 seconds and return the expected decision shape.

**Evidence:** CI job `Backend tests, QRT and coverage`, quality-test step.

**Why this is not full QRT evidence:** Capture is not performed, the fake detector returns immediately, the real InsightFace and liveness sessions do not run, PostgreSQL is bypassed with a vector, and UI rendering is not timed. This is useful regression evidence for orchestration overhead but cannot measure QR-001's stated end-to-end deployment scenario.

**Required completion:** Run the released stack on representative Raspberry Pi/camera hardware with up to 20 database users, measure from captured-frame timestamp through visible UI decision for a defined sample size, and publish the raw measurements automatically.

**Status:** Partially automated (not Implemented end-to-end)

## QRT-002: Static Photo Spoofing Rejection

**Linked quality requirement:** `QR-002`

**Current automated check:** `tests/quality/test_photo_spoofing_rejection.py` proves the decision contract for `spoof` and `no_face`, and exercises the production `InsightFaceProvider` with a controlled face plus deterministic liveness rejection. A matching embedding still cannot grant access after that rejection.

**Command:** `PYTHONPATH=backend:. .venv/bin/pytest tests/quality/test_photo_spoofing_rejection.py -q`

**Observed/expected result:** All controlled invalid statuses are rejected before matching, including the production-provider path with an otherwise matching embedding.

**Evidence:** CI job `Backend tests, QRT and coverage`, quality-test step.

**Why this is not full QRT evidence:** A deterministic liveness result is not a printed-photo/phone-screen presentation attack. The check proves provider integration and decision ordering, not MiniFASNet attack-detection accuracy with a physical 720p camera.

**Required completion:** Version a permitted attack dataset/procedure and execute ten automated or hardware-runner presentations under the specified lighting/camera conditions, including event-log verification.

**Status:** Partially automated (not Implemented for the 9/10 physical scenario)

## QRT-003: Inference Provider Contract Modularity

**Linked quality requirement:** `QR-003`

**Test:** `tests/quality/test_inference_provider_contract.py`

**Command:** `PYTHONPATH=backend:. .venv/bin/pytest tests/quality/test_inference_provider_contract.py -q`

**Expected measurable result:** A different `FaceProviderInterface` implementation is injected without changing access-decision code; success and provider-failure results preserve the application contract.

**Evidence:** CI job `Backend tests, QRT and coverage`, quality-test step.

**Limit:** This proves the internal provider seam. A real replacement must still pass the complete frontend/backend CI pipeline.

**Status:** Implemented

## QRT-004: Temporary Access Window Enforcement

**Linked quality requirement:** `QR-004`

**Test:** Relevant behavior in `tests/unit/test_temporary_access.py`.

**Command:** `PYTHONPATH=backend:. .venv/bin/pytest tests/unit/test_temporary_access.py -q`

**Expected measurable result:** Every before-start and after-expiration case is excluded; inclusive in-window cases pass; legacy `date` and current `datetime` values normalize correctly; database-read results exclude inactive temporary identities without requiring an admin page load.

**Evidence:** CI job `Backend tests, QRT and coverage`, unit-test step and coverage artifact.

**Limit:** Migration SQL structure is asserted in unit tests; it is not currently executed in a dedicated migration QRT against a legacy production snapshot.

**Status:** Implemented

## QRT-005: Duplicate Registration Prevention

**Linked quality requirement:** `QR-005`

**Test:** `tests/quality/test_duplicate_registration.py`

**Environment:** An isolated PostgreSQL 15 database named exactly `faceguard_test`. The test refuses any other `POSTGRES_DB`. Embeddings are deterministic vectors, while duplicate comparison, transaction/advisory lock, insert/rollback, JWT dependency, HTTP routing, and PostgreSQL are real.

**Local command:**

```bash
docker compose -p faceguardv3-qrt -f docker/docker-compose.test.yml up -d --wait
PYTHONPATH=backend:. RUN_POSTGRES_INTEGRATION=1 \
  DB_HOST=127.0.0.1 DB_PORT=55432 \
  POSTGRES_DB=faceguard_test POSTGRES_USER=faceguard_test \
  POSTGRES_PASSWORD=faceguard_test \
  JWT_SECRET=faceguard-qrt-signing-secret-at-least-32-bytes \
  .venv/bin/pytest tests/quality/test_duplicate_registration.py -q
docker compose -p faceguardv3-qrt -f docker/docker-compose.test.yml down
```

**Expected measurable result:**

1. first registration returns HTTP `200` and inserts one employee;
2. a near-identical vector returns HTTP `409` naming the existing employee;
3. the database still contains exactly the unchanged original row;
4. a similar-but-distinct vector with cosine similarity `0.55`, just below the `0.56` threshold, returns `200` and creates a second row; and
5. two concurrent same-face requests yield one `200`, one `409`, and one row.

**Evidence:** CI PostgreSQL service, `Automated quality-requirement tests` step, and the uploaded `backend-coverage` JSON/XML artifact. Latest local audit result: `2 passed`.

**Limit:** Deterministic embeddings deliberately avoid testing InsightFace internals and physical enrollment capture. Those concerns belong to model/camera validation, not duplicate orchestration.

**Status:** Implemented

## QRT-006: Hardware Feedback Latency

**Linked quality requirement:** `QR-006`

**Current software precheck:** `tests/quality/test_hardware_feedback.py` uses an in-memory LED and records order through the public `access_granted()` command. It fails if the correct `.on()` call is not issued synchronously before the background hold worker starts. Unit tests also cover color mapping, recognition/enrollment dispatch, stale-worker protection, configured gpiochip selection, initialization failure, and shutdown cleanup.

**Software command:** `PYTHONPATH=backend:. .venv/bin/pytest tests/quality/test_hardware_feedback.py tests/unit/test_leds.py tests/unit/test_backend_main.py -q`

**Software expected result:** Adapter command ordering and lifecycle behavior pass without timing sleeps. This check runs in CI.

**Missing measurable result:** QR-006 requires the physical blue/red LED transition within `0.5 s` of the backend decision while subsequent frames continue. A GitHub-hosted runner and fake GPIO expose neither electrical nor optical transition time.

**Required completion:** A self-hosted Raspberry Pi runner with mapped gpiochip and a photodiode/logic-analyzer input must correlate a backend decision marker with the measured pin/LED transition, exercise success and failure repeatedly, assert `<= 0.5 s`, confirm a later frame is processed, and retain raw timestamp evidence.

**Evidence:** Software precheck is in normal CI. No automated physical evidence exists.

**Status:** Planned (software implementation present; full hardware QRT absent)
