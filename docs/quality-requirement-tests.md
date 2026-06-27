# Quality Requirements Test

## QRT-001: Recognition Pipeline Response Time

**Status**: Implemented
**Linked quality requirement**: `QR-001`
**Verification method**: Automated performance CI check.
**Test data, setup, or environment**: Standard CI build environment. A prepared face image fixture from `tests/fixtures/` and a local mock database containing up to 20 registered users.
**Automated command or CI check**: `pytest tests/quality/test_recognition_performance.py`
**CI status**: Not configured yet
**Expected measurable result**: The test executes the recognition pipeline and passes only if a valid access decision is produced in `<= 3.0` seconds. It fails if the execution time exceeds 3.0 seconds, crashes, or produces no decision.
**Evidence link**: Latest protected default-branch CI run.
**Limitation**: Uses prepared fixtures instead of a live USB camera.

## QRT-002: Static Photo Spoofing Rejection

**Status**: Implemented
**Linked quality requirement**: `QR-002`
**Verification method**: Automated security integration CI check.
**Test data, setup, or environment**: Standard CI build environment. A test dataset containing 10 distinct static 2D photo presentation attacks loaded from `tests/fixtures/`.
**Automated command or CI check**: `pytest tests/quality/test_photo_spoofing_rejection.py`
**CI status**: Not configured yet
**Expected measurable result**: The test passes only if the validation pipeline correctly rejects at least 9 out of 10 static 2D photo presentation attempts. It fails if fewer than 9 attempts are rejected or if access is erroneously granted.
**Evidence link**: Latest protected default-branch CI run.

## QRT-003: Inference Provider Contract Modularity

**Status**: Implemented
**Linked quality requirement**: `QR-003`
**Verification method**: Automated architecture integration CI check.
**Test data, setup, or environment**: Standard CI build environment. A fake recognition provider mock is injected into the standard application flow instead of the real ML library.
**Automated command or CI check**: `pytest tests/quality/test_inference_provider_contract.py`
**CI status**: Not configured yet
**Expected measurable result**: The test passes if the application successfully receives a valid access decision from the mock provider without raising dependency errors, proving the pipeline does not directly depend on a specific recognition library.
**Evidence link**: Latest protected default-branch CI run.
**Limitation**: Uses a mock provider to verify software modularity. It does not measure recognition accuracy of a real production model or exercise physical hardware.
