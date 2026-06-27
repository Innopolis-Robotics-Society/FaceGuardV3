# Quality Requirement Tests

## Quality Requirements Covered

- QR-001: Recognition Response Time
- QR-002: Resistance to Static Photo Spoofing
- QR-003: Recognition Model Modularity

## QRT-001: Recognition Pipeline Response Time

**Linked quality requirement**: `QR-001`
**Verification method**: Automated performance CI check.
**Test data, setup, or environment**: Standard CI/Docker test environment. The test uses controlled fake frame, fake face app, fake face result, and fake liveness detector instead of live hardware.
**Automated command or CI check**: `pytest tests/quality/test_recognition_performance.py`
**Expected measurable result**: The test executes the recognition pipeline and passes only if a valid access decision is produced in `<= 3.0` seconds. It fails if the execution time exceeds 3.0 seconds, crashes, or produces no decision.
**Evidence link**: Latest protected default-branch CI run after CI integration.
**Limitation**: Uses controlled fake inputs instead of a live USB camera.
**CI Job**: Not configured yet
**Status**: Implemented

## QRT-002: Static Photo Spoofing Rejection

**Linked quality requirement**: `QR-002`
**Verification method**: Automated security integration CI check.
**Test data, setup, or environment**: Standard CI/Docker test environment. The test uses mock recognizers and controlled embedding vectors to simulate spoof, no-face, and low-similarity attempts.
**Automated command or CI check**: `pytest tests/quality/test_photo_spoofing_rejection.py`
**Expected measurable result**: The test passes only if the validation pipeline correctly rejects spoof or invalid recognition attempts, including at least 9 out of 10 low-similarity attempts. It fails if fewer than 9 attempts are rejected or if access is erroneously granted.
**Evidence link**: Latest protected default-branch CI run after CI integration.
**Limitation**: Uses controlled mock recognizers and embeddings instead of physical printed-photo attacks with a live camera.
**CI Job**: Not configured yet
**Status**: Implemented

## QRT-003: Inference Provider Contract Modularity

**Linked quality requirement**: `QR-003`
**Verification method**: Automated architecture integration CI check.
**Test data, setup, or environment**: Standard CI/Docker test environment. A fake recognition provider is injected into the standard application flow instead of the real ML library.
**Automated command or CI check**: `pytest tests/quality/test_inference_provider_contract.py`
**Expected measurable result**: The test passes if the application successfully receives a valid access decision from the mock provider without raising dependency errors, proving the pipeline does not directly depend on a specific recognition library.
**Evidence link**: Latest protected default-branch CI run after CI integration.
**Limitation**: Uses a mock provider instead of executing the real InsightFace model, ONNX liveness detector, camera input, or GPIO hardware.
**CI Job**: Not configured yet
**Status**: Implemented
