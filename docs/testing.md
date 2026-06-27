# Testing and QA Checks

## Testing Strategy

FaceGuardV3 uses automated unit, integration, and quality requirement tests to
check the core recognition pipeline without depending on physical deployment
hardware. The test suite uses controlled fake frames, fake recognition
providers, mock recognizers, and deterministic embedding vectors so it can run
locally or in a CI/Docker test environment.

## Critical Modules

- `backend.faceguard.recognize`: embedding normalization, similarity scoring,
  verification, and embedding averaging.
- `backend.faceguard.detect`: face selection, bounding box clamping, cropping,
  and basic face quality checks.
- `backend.faceguard.business_logic`: access decision handling for valid,
  missing, spoofed, bad-quality, and low-similarity recognition results.
- `backend.faceguard.interfaces`: provider contract used to inject fake or real
  recognition implementations.

## Unit Tests

Unit tests are stored in `tests/unit/`.

- `tests/unit/test_recognize.py` covers `normalize_embedding()`,
  `cosine_similarity()`, `verify_embedding()`, `average_embeddings()`, and
  zero-vector handling.
- `tests/unit/test_detect.py` covers `select_closest_face()`, `clamp_bbox()`,
  `crop_face()`, and `is_good_face()`.
- `tests/unit/test_business_logic.py` covers `process_access_attempt()` for
  matching embeddings, rejected `no_face`, `spoof`, and `bad_face` statuses, and
  low-similarity embeddings.

Run unit tests:

```bash
PYTHONPATH=. pytest tests/unit/ -v
```

## Integration Tests

Integration tests are stored in `tests/integration/`.

`tests/integration/test_recognition_flow.py` verifies the recognition decision
flow using a fake frame, a fake recognition provider, the real
`process_access_attempt()` function, and the real embedding verification path
through business logic.

Run integration tests:

```bash
PYTHONPATH=. pytest tests/integration/ -v
```

## Full Test Suite

Run all tests, including quality requirement tests:

```bash
PYTHONPATH=. pytest tests/ -v
```

## Coverage

The project uses `pytest-cov` for line coverage. The Assignment 4 Part 7 target
is at least 30% line coverage for each of these modules:

- `backend/faceguard/recognize.py`
- `backend/faceguard/detect.py`
- `backend/faceguard/business_logic.py`

Run coverage:

```bash
PYTHONPATH=. pytest tests/ --cov=backend/faceguard --cov-report=term-missing
```

## Bandit Security Scan

Bandit is used as an additional static QA check for common Python security
issues in the backend code.

Run Bandit:

```bash
bandit -r backend
```

## Local Execution Commands

```bash
PYTHONPATH=. pytest tests/unit/ -v
PYTHONPATH=. pytest tests/integration/ -v
PYTHONPATH=. pytest tests/ -v
PYTHONPATH=. pytest tests/ --cov=backend/faceguard --cov-report=term-missing
bandit -r backend
```

## Limitations

These tests do not require a real camera, Raspberry Pi, GPIO pins, a real ONNX
liveness model, a real InsightFace model, private face images, or customer
data. Hardware behavior, live camera image quality, production model accuracy,
and real printed-photo presentation attacks must still be validated separately
on the target deployment setup.
