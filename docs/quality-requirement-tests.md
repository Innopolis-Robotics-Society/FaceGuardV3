# Quality Requirements Test

## QRT-1
**Stable ID**: `QRT-PERF-001`
**Linked quality requirement ID**: `QR-PERF-001`  
**ISO/IEC 25010 Characteristic**: Performance Efficiency
**ISO/IEC 25010 Sub-characteristic**: Time Behavior
**Test Type**: Automated performance
**Test Location**: `tests/quality/test_recognition_performance.py`
**CI Job**: Not configured yet
**Status**: Implemented

### Purpose

This test verifies that the recognition pipeline produces an access decision within the required response time.

### Test Procedure

1. Load a prepared face image or prerecorded frame from `tests/fixtures/`.
2. Pass the input to the recognition pipeline.
3. Measure the time from recognition start to access decision.
4. Verify that the decision is produced within the required time limit.

### Pass Condition

The recognition decision must be produced in **≤ 3.0 seconds** for a local database of up to 20 registered users.

### Failure Condition

The test fails if:

* recognition takes more than 3.0 seconds;
* no access decision is produced;
* the recognition pipeline crashes;
* the result format is invalid.

### Evidence

The test result will be preserved through the CI pipeline and linked from `reports/week4/README.md`.

### Limitations

This QRT uses prepared image or frame fixtures instead of a live USB camera. Real camera behavior is verified separately through demo, UAT, or Sprint Review evidence.

## QRT-2
**Stable ID**: `QRT-SEC-002`
**Linked quality requirement ID**: `QR-SEC-002`  
**ISO/IEC 25010 Characteristic**: Security
**ISO/IEC 25010 Sub-characteristic**: Authenticity
**Test Type**: Automated security
**Test Location**: `tests/quality/test_photo_spoofing_rejection.py`
**CI Job**: Not configured yet
**Status**: Implemented

### Purpose

This test verifies that the system rejects unauthorized or low-confidence face inputs instead of granting access.

### Test Procedure

1. Load static photo or unauthorized face samples from `tests/fixtures/`.
2. Pass each sample through the recognition or validation pipeline.
3. Check whether the system rejects access.
4. Count the number of rejected attempts.
5. Compare the result with the required rejection threshold.

### Pass Condition

The system rejects at least 9 out of 10 static 2D photo presentation attempts or unauthorized low-confidence inputs.

### Failure Condition

The test fails if:

* fewer than 9 out of 10 attempts are rejected;
* access is granted for a low-confidence or unauthorized input;
* the validation pipeline crashes;
* the system does not return a verifiable rejection result.

### Evidence

The test result will be preserved through the CI pipeline and linked from `reports/week4/README.md`.

### Limitations

If full liveness detection is not implemented during Assignment 4, this QRT validates threshold-based rejection. Full anti-spoofing or liveness detection remains deferred work.





## QRT-3
**Stable ID**: `QRT-MAIN-003`
**Linked quality requirement ID**: `QR-MAIN-003`  
**ISO/IEC 25010 Characteristic**: Maintainability 
**ISO/IEC 25010 Sub-characteristic**: Modularity
**Test Type**: Automated integration / architecture 
**Test Location**: `tests/quality/test_inference_provider_contract.py`
**CI Job**: Not configured yet
**Status**: Implemented


### Purpose

This test verifies that the recognition model can be replaced through a provider abstraction without changing API routes, UI templates, or unrelated business logic.

### Test Procedure

1. Create or load a fake recognition provider.
2. Inject the fake provider into the recognition flow.
3. Execute the recognition flow through the normal service layer or application interface.
4. Verify that the application receives a valid recognition result.
5. Verify that the recognition flow does not directly depend on a specific recognition library.

### Pass Condition

The recognition provider can be replaced with a mock or substitute provider while the application-level recognition flow continues to work.

### Failure Condition

The test fails if:

* the recognition flow directly depends on one specific model library;
* replacing the provider requires API route changes;
* replacing the provider breaks the recognition flow;
* the fake provider cannot produce a valid application-level access decision.

### Evidence

The test result will be preserved through the CI pipeline and linked from `reports/week4/README.md`.

### Limitations

This QRT verifies software modularity through provider substitution. It does not measure recognition accuracy of a real production model.
