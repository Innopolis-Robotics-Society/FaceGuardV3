# Testing and QA Checks

## Critical Modules and Coverage

| Critical module | Why critical | Required line coverage | Current line coverage | Evidence |
|---|---|---:|---:|---|
| `backend/faceguard/recognize.py` | Core facial recognition mathematical logic, embedding comparison, and spoof detection thresholding. | 30% | 49% | Local `pytest --cov` run |
| `backend/faceguard/detect.py` | Bounding box clamping, face geometry validation, and closest face selection. | 30% | 85% | Local `pytest --cov` run |
| `backend/faceguard/business_logic.py` | Access control decision making, routing statuses (`spoof`, `no_face`, `real`). | 30% | 67% | Local `pytest --cov` run |

## Automated Test Status

| Test type | Scope | Command or CI check | Latest result | Evidence |
|---|---|---|---|---|
| Unit tests | Mathematical logic and business rules | `PYTHONPATH=. pytest tests/unit/ -v` | 17 passed | Local run |
| Integration tests | Provider mocking and pipeline flow | `PYTHONPATH=. pytest tests/integration/ -v` | 3 passed | Local run |
| Automated QRTs | QR-001, QR-002, QR-003 | `PYTHONPATH=. pytest tests/quality/ -v` | 8 passed | Local run |

## CI and QA Check Status

| Gate or check | Required for Done? | Latest protected-branch status | Evidence |
|---|---|---|---|
| Linting | Yes | Pending CI setup | Pending CI setup |
| Formatting or type checking | Yes | Pending CI setup | Pending CI setup |
| Additional QA check | Yes | Passing | Local `bandit -r backend` run |

## Additional QA Check Rationale

| QA objective or risk | Additional QA check | Scope | Latest result | Evidence | Limitations or follow-up |
|---|---|---|---|---|---|
| Silent exception swallowing and insecure code patterns can mask critical failures or expose the system to exploits. | Static Application Security Testing (SAST) with Bandit. | `backend/` source code. | Passing: 0 issues identified | Local `bandit -r backend` run | Bandit only analyzes Python source code. It does not scan Docker image vulnerabilities or C-level dependency flaws. |

## Manual Evidence That Does Not Count as QRT

| Evidence | Scope | Result | Follow-up PBI or issue |
|---|---|---|---|
| Live USB Camera UAT | Physical presentation of printed photos and real camera recognition behavior | Pending hardware test | N/A |
