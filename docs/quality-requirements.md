## QR-001: Recognition Response Time

**ISO/IEC 25010 sub-characteristic:** Time behaviour

**Scenario:** When an authorized person approaches the entry point and stands in the camera frame triggering automatic face detection under normal indoor lighting with a standard USB webcam and a local database of up to 20 users, the local recognition inference service shall capture the frame, preprocess the face, verify it against the database, and display the access decision in the UI within 3.0 seconds.

**Why this matters:** The MVP previously required manual triggering and could freeze because of heavy model loading. In an access control scenario, recognition must feel immediate and must not require unnecessary user interaction (Customer feedback: "Site freezes; make recognition faster").

**Linked quality requirement tests:** [QRT-001](quality-requirement-tests.md#qrt-001-recognition-pipeline-response-time)

**Linked ADR:** 
- [ADR-003: Keep the Recognition Pipeline Synchronous and In-Process for Sub-3-Second Response](architecture/adr/ADR-003-synchronous-recognition-pipeline-for-response-time.md)
- [ADR-005: Decouple Frontend and Backend for WebSocket Streaming](architecture/adr/ADR-005-decouple-frontend-backend-for-websocket-streaming.md)

**Current status:** Resolved. The transition to a decoupled React+FastAPI architecture with WebSockets (implemented in [#171](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/171)) eliminated UI polling latency. End-to-end response time is now consistently ~1.1 seconds.

---

## QR-002: Resistance to Static Photo Spoofing

**ISO/IEC 25010 sub-characteristic:** Authenticity

**Scenario:** When an unauthorized person attempts to gain access by presenting a printed photo or a phone screen displaying an authorized user's face to the camera under normal deployment operation with a USB camera of at least 720p resolution and normal indoor lighting, the video preprocessing and face embedding comparator module shall reject the access attempt and log the event, successfully rejecting at least 9 out of 10 static 2D photo presentation attacks from the predefined test set.

**Why this matters:** Access control requires protection against basic impersonation attempts. A system that only compares face embeddings without checking whether the input comes from a live person is vulnerable to simple photo-based spoofing (Customer feedback: "Registration via video").

**Linked quality requirement tests:** [QRT-002](quality-requirement-tests.md#qrt-002-static-photo-spoofing-rejection)

**Linked ADR:** [ADR-002: Reject Access Based on Provider Status Code Before Embedding Comparison](architecture/adr/ADR-002-reject-on-status-code-before-embedding-match.md)

---

## QR-003: Recognition Model Modularity

**ISO/IEC 25010 sub-characteristic:** Modularity

**Scenario:** When the development team swaps the underlying face recognition provider, such as changing from a heavy model to a lightweight ONNX-based model under the CI build and development environment, the Python backend modules responsible for recognition shall maintain API route signatures, UI templates, and business-logic test assertions unchanged, passing the full automated CI pipeline successfully after the provider replacement.

**Why this matters:** The MVP showed that a heavy recognition model can freeze the system. The architecture must avoid hard-wiring the application to one specific recognition library. A provider abstraction reduces regression risk and allows future speed or accuracy improvements without rewriting unrelated application logic.

**Linked quality requirement tests:** [QRT-003](quality-requirement-tests.md#qrt-003-inference-provider-contract-modularity)

**Linked ADR:** [ADR-001: Introduce a Face Recognition Provider Abstraction](architecture/adr/ADR-001-face-recognition-provider-abstraction.md)

---

## QR-004: Temporary Access Window Enforcement

**ISO/IEC 25010 sub-characteristic:** Functional Correctness

**Scenario:** When a registered employee with Temporary access status attempts
recognition under normal deployment operation, regardless of whether an
admin has recently opened the Employees page, the access-control decision
module shall grant access only when the current time is within the
employee's configured [start_date, expiration_date] window (inclusive), and
shall deny access outside that window in 100% of automated test cases.

**Why this matters:** Temporary access is a security boundary, not a
convenience feature — an employee whose access has expired (or has not yet
started) must not be recognized, independent of unrelated admin activity
such as viewing the Employees page. This was found to be a real defect:
`get_all_embeddings()` did not filter by expiration/start date, so expired
temporary employees could still be granted access until an admin happened
to reload the Employees page.

**Linked quality requirement tests:** [QRT-004](quality-requirement-tests.md#qrt-004-temporary-access-window-enforcement)

**Linked ADR:** [ADR-004: Enforce Temporary Access Window in Application Logic with TIMESTAMP Normalization](architecture/adr/ADR-004-temporary-access-window-enforcement.md)
