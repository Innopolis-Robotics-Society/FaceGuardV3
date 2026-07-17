# Quality Requirements

Statuses below distinguish implemented software from evidence that proves the complete measurable scenario. A CI double is not treated as camera, model, or physical-hardware evidence.

## QR-001: Recognition Response Time

**ISO/IEC 25010 sub-characteristic:** Time behaviour

**Scenario:** When an authorized person approaches the entry point and stands in the camera frame triggering automatic face detection under normal indoor lighting with a standard USB webcam and a local database of up to 20 users, the local recognition inference service shall capture the frame, preprocess the face, verify it against the database, and display the access decision in the UI within 3.0 seconds.

**Why this matters:** The MVP previously required manual triggering and could freeze because of heavy model loading. Recognition must feel immediate at an unattended access point.

**Linked quality requirement tests:** [QRT-001](quality-requirement-tests.md#qrt-001-recognition-pipeline-response-time)

**Linked ADR:**

- [ADR-003: Keep Recognition In-Process and Direct](architecture/adr/ADR-003-synchronous-recognition-pipeline-for-response-time.md)
- [ADR-005: Decouple React Presentation from FastAPI Processing](architecture/adr/ADR-005-decouple-frontend-backend-for-websocket-streaming.md)
- [ADR-009: Dual Camera Sources with a Latest-Frame Pipeline](architecture/adr/ADR-009-dual-camera-latest-frame-pipeline.md)

**Current status:** Software architecture implemented; complete requirement not yet automatically verified. The current CI performance test uses an instant fake face app and therefore does not establish camera + real InsightFace/MiniFASNet + PostgreSQL + WebSocket/UI latency on Raspberry Pi. The earlier “consistently ~1.1 seconds” statement had no maintained evidence and has been removed.

---

## QR-002: Resistance to Static Photo Spoofing

**ISO/IEC 25010 sub-characteristic:** Authenticity

**Scenario:** When an unauthorized person attempts to gain access by presenting a printed photo or a phone screen displaying an authorized user's face to the camera under normal deployment operation with a USB camera of at least 720p resolution and normal indoor lighting, the video preprocessing and face embedding comparator module shall reject the access attempt and log the event, successfully rejecting at least 9 out of 10 static 2D photo presentation attacks from the predefined test set.

**Why this matters:** Embedding matching without a liveness boundary is vulnerable to basic presentation attacks.

**Linked quality requirement tests:** [QRT-002](quality-requirement-tests.md#qrt-002-static-photo-spoofing-rejection)

**Linked ADR:** [ADR-002: Reject Access Based on Provider Status Code Before Embedding Comparison](architecture/adr/ADR-002-reject-on-status-code-before-embedding-match.md)

**Current status:** Liveness integration and mandatory rejection ordering are implemented. CI exercises the production `InsightFaceProvider` boundary with a controlled face result and a deterministic liveness rejection, then proves that the matching embedding still cannot grant access. It does not execute the predefined ten physical photo/screen presentations, so the 9/10 scenario is not yet fully automated.

---

## QR-003: Recognition Model Modularity

**ISO/IEC 25010 sub-characteristic:** Modularity

**Scenario:** When the development team swaps the underlying face recognition provider, such as changing from a heavy model to a lightweight ONNX-based model under the CI build and development environment, the Python backend modules responsible for recognition shall maintain API route contracts, React UI behavior, and business-logic test assertions unchanged, passing the full automated CI pipeline successfully after the provider replacement.

**Why this matters:** The application must not hard-wire access decisions to one recognition library.

**Linked quality requirement tests:** [QRT-003](quality-requirement-tests.md#qrt-003-inference-provider-contract-modularity)

**Linked ADR:** [ADR-001: Introduce a Face Recognition Provider Abstraction](architecture/adr/ADR-001-face-recognition-provider-abstraction.md)

**Current status:** Implemented and automatically verified at the provider/business-logic boundary.

---

## QR-004: Temporary Access Window Enforcement

**ISO/IEC 25010 sub-characteristic:** Functional correctness

**Scenario:** When a registered employee with Temporary access status attempts recognition under normal deployment operation, regardless of whether an admin has recently opened the Employees page, the access-control decision module shall grant access only when the current time is within the employee's configured `[start_date, expiration_date]` window (inclusive), and shall deny access outside that window in 100% of automated test cases.

**Why this matters:** Temporary access is a security boundary independent of admin page activity.

**Linked quality requirement tests:** [QRT-004](quality-requirement-tests.md#qrt-004-temporary-access-window-enforcement)

**Linked ADR:** [ADR-004: Enforce Temporary Access Window in Application Logic with TIMESTAMP Normalization](architecture/adr/ADR-004-temporary-access-window-enforcement.md)

**Current status:** Implemented. Deterministic tests cover inclusive datetime/date bounds, write normalization, migration SQL, and filtering in the embedding read path.

---

## QR-005: Duplicate Registration Prevention

**ISO/IEC 25010 sub-characteristic:** Functional correctness / integrity

**Scenario:** When an admin attempts to register a new employee using a face that already exists in the system's database, the backend registration module shall detect the high-similarity match, reject the registration request with an appropriate error message, and prevent duplicate entries in the database.

**Why this matters:** Multiple identities for one person create ambiguous recognition and integrity failures.

**Linked quality requirement tests:** [QRT-005](quality-requirement-tests.md#qrt-005-duplicate-registration-prevention)

**Linked ADR:** [ADR-008: Prevent Duplicate Registration Before Insert in One Transaction](architecture/adr/ADR-008-atomic-duplicate-registration-prevention.md)

**Current status:** Implemented. QRT-005 uses the FastAPI HTTP boundary, real PostgreSQL, deterministic embeddings, and concurrent requests. It proves rejection, HTTP `409`, unchanged existing data, one stored row, acceptance of a similar vector just below the `0.56` threshold, and serialized check/insert.

---

## QR-006: Hardware Feedback Latency

**ISO/IEC 25010 sub-characteristic:** Time behaviour

**Scenario:** When a recognition event (success or failure) is determined by the backend inference service, the physical LED indicators connected to the edge device's GPIO pins shall illuminate in the correct color (for example blue for success and red for failure) within 0.5 seconds of the software decision, without blocking subsequent video frames.

**Why this matters:** Access feedback must be immediate without stopping frame processing.

**Linked quality requirement tests:** [QRT-006](quality-requirement-tests.md#qrt-006-hardware-feedback-latency)

**Linked ADR:** [ADR-007: Non-Blocking, Generation-Safe GPIO LED Feedback](architecture/adr/ADR-007-gpio-hardware-integration.md)

**Current status:** Software adapter and generation safety implemented; full QRT Planned. `tests/quality/test_hardware_feedback.py` proves that the correct adapter `.on()` call occurs before the duration worker starts, but a fake LED cannot prove the physical transition or 0.5-second end-to-end latency. A self-hosted Raspberry Pi hardware-in-the-loop runner with an electrical/optical measurement is required.
