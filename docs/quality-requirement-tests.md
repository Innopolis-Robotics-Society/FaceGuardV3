# Quality Requirement Tests

## Quality Requirements Covered

- QR-001: Recognition Response Time

- QR-002: Resistance to Static Photo Spoofing

- QR-003: Recognition Model Modularity

- QR-004: Temporary Access Window Enforcement

## QRT-001: Recognition Pipeline Response Time

**Linked quality requirement**: `QR-001`

**Verification method**: Automated performance CI check.

**Test data, setup, or environment**: Standard CI/Docker test environment. The test uses a controlled fake frame, fake face app, and fake face result instead of live hardware.

**Automated command or CI check**: `pytest tests/quality/test_recognition_performance.py`

**Expected measurable result**: The test verifies two levels of the pipeline:
1. Embedding extraction from a detected face completes in `<= 3.0` seconds.
2. The full access-decision pipeline (capture -> extract -> compare against the database -> decision), as described in the QR-001 scenario, also completes in `<= 3.0` seconds and produces a valid access decision.

The test fails if either step exceeds 3.0 seconds, crashes, or fails to produce a decision.

**Evidence link**: Latest protected default-branch CI run after CI integration.

**Limitation**: Uses controlled fake inputs instead of a live USB camera; the fake face-detection app returns instantly, so this measures pipeline/business-logic overhead rather than actual ML model inference latency.

**CI Job**: `pytest tests/quality/` runs automatically on every PR and push to main

**Status**: Implemented

## QRT-002: Static Photo Spoofing Rejection

**Linked quality requirement**: `QR-002`

**Verification method**: Automated security integration CI check.

**Test data, setup, or environment**: Standard CI/Docker test environment. The test uses mock recognizers and controlled embedding vectors to simulate spoof, no-face, and low-similarity attempts.

**Automated command or CI check**: `pytest tests/quality/test_photo_spoofing_rejection.py`

**Expected measurable result**: The test passes only if the validation pipeline correctly rejects spoof or invalid recognition attempts, including at least 9 out of 10 low-similarity attempts. It fails if fewer than 9 attempts are rejected or if access is erroneously granted.

**Evidence link**: Latest protected default-branch CI run after CI integration.

**Limitation**: Uses controlled mock recognizers and embeddings instead of physical printed-photo attacks with a live camera.

**CI Job**: pytest tests/quality/ runs automatically on every PR and push to main

**Status**: Implemented

## QRT-003: Inference Provider Contract Modularity

**Linked quality requirement**: `QR-003`

**Verification method**: Automated architecture integration CI check.

**Test data, setup, or environment**: Standard CI/Docker test environment. A fake recognition provider is injected into the standard application flow instead of the real ML library.

**Automated command or CI check**: `pytest tests/quality/test_inference_provider_contract.py`

**Expected measurable result**: The test passes if the application successfully receives a valid access decision from the mock provider without raising dependency errors, proving the pipeline does not directly depend on a specific recognition library.

**Evidence link**: Latest protected default-branch CI run after CI integration.

**Limitation**: Uses a mock provider instead of executing the real InsightFace model, ONNX liveness detector, camera input, or GPIO hardware.

**CI Job**: pytest tests/quality/ runs automatically on every PR and push to main

**Status**: Implemented

## QRT-004: Temporary Access Window Enforcement

**Linked quality requirement:** `QR-004`

**Verification method:** Automated unit test on the pure business-rule
function, plus a mocked-DB test on the data-access layer.

**Test data, setup, or environment:** Standard CI test environment. No real
database is used — connect_to_db() is mocked; test fixtures provide rows
representing permanent, active-temporary, expired-temporary, and
not-yet-started-temporary employees with a fixed now timestamp for
determinism.

**Automated command or CI check:** pytest tests/unit/test_employees_db.py

**Expected measurable result:** is_temporary_access_valid() returns True
only for permanent employees and temporary employees within their
[start_date, expiration_date] window; get_all_embeddings() excludes any
temporary employee outside that window from the results used for
recognition matching.

**Evidence link:** Latest protected default-branch CI run.

**Limitation:** Uses a mocked cursor rather than a real PostgreSQL instance,
so it verifies the Python-level filtering logic but not PostgreSQL-specific
behavior (e.g. timezone handling at the DB driver level). No live-DB
integration test exists yet for this path.

**CI Job:** pytest tests/ runs automatically on every PR and push to main

**Status:** Implemented

---

## QRT-004: Temporary Access Window Enforcement

**Linked quality requirement**: `QR-004`

**Verification method**: Automated unit test on the pure business-rule
functions, plus a mocked-DB test on the data-access layer.

**Test data, setup, or environment**: Standard CI test environment. No real
database is used — `connect_to_db()` is mocked; test fixtures provide rows
representing permanent, active-temporary, expired-temporary, and
not-yet-started-temporary employees with a fixed `now` timestamp for
determinism. Legacy `date`-typed (pre-migration) values are also covered.

**Automated command or CI check**: `pytest tests/unit/test_temporary_access.py`

**Expected measurable result**: `_temporary_access_is_active()` returns
`True` only when the current time is within `[start_date, expiration_date]`
inclusive (or for non-Temporary status), correctly handling both
`datetime` and legacy `date` inputs. `_normalize_access_window()` converts
`date` inputs to full-day `datetime` bounds before writes.
`get_all_embeddings()` excludes any temporary employee outside the active
window from the results used for recognition matching. `add_employees()`
returns `False` and skips the INSERT when a duplicate name exists.

**Evidence link**: Latest protected default-branch CI run.

**Limitation**: Uses a mocked cursor rather than a real PostgreSQL instance,
so it verifies the Python-level filtering and normalization logic but not
PostgreSQL-specific behavior (e.g. the `DATE`→`TIMESTAMP` migration SQL is
checked for the expected substrings, not executed against a real database).

**CI Job**: `pytest tests/` runs automatically on every PR and push to main

**Status**: Implemented
