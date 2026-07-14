# Architecture Documentation

## Architecture Decision Records

The ADRs capture the main architectural decisions that connect the current
FaceGuardV3 implementation to the quality requirements:

- [ADR-001: Introduce a Face Recognition Provider Abstraction](adr/ADR-001-face-recognition-provider-abstraction.md) supports the Static View by defining the `FaceProviderInterface` boundary between business logic and the recognition provider. It supports QR-003 by allowing provider swaps to be tested without changing the access-decision flow.
- [ADR-002: Reject Access Based on Provider Status Code Before Embedding Comparison](adr/ADR-002-reject-on-status-code-before-embedding-match.md) supports the Dynamic View by fixing the order of the recognition flow: provider status is checked before embedding comparison. It supports QR-002 by making spoof/no-face rejection part of the backend access decision.
- [ADR-003: Keep the Recognition Pipeline Synchronous and In-Process for Sub-3-Second Response](adr/ADR-003-synchronous-recognition-pipeline-for-response-time.md) supports the Dynamic and Deployment Views by keeping recognition in the local FaceGuard application process for the current single-entry-point deployment. It supports QR-001 by keeping response-time measurement focused on the direct capture, extraction, comparison, and decision path.
- [ADR-004: Enforce Temporary Access Window in Application Logic with TIMESTAMP Normalization](adr/ADR-004-temporary-access-window-enforcement.md) supports the Dynamic View by fixing the identity-verification step to exclude expired or not-yet-started temporary access before comparison. It supports QR-004 by ensuring access decisions respect the configured time window regardless of admin activity.
- [ADR-005: Decouple Frontend and Backend for WebSocket Streaming](adr/ADR-005-decouple-frontend-backend-for-websocket-streaming.md) supports all views by documenting the shift from a Streamlit monolith to a decoupled React and FastAPI architecture. It supports QR-001 by introducing WebSockets to eliminate UI rendering bottlenecks and achieve sub-3-second end-to-end response times.
- [ADR-006: Local PostgreSQL Database for Offline Reliability](adr/ADR-006-local-database-for-offline-reliability.md) supports all views by transitioning state management from the cloud to the local edge device. It supports reliability and performance by ensuring the system operates fully offline without internet dependency.
- [ADR-007: Asynchronous GPIO Hardware Integration for Edge Devices](adr/ADR-007-gpio-hardware-integration.md) supports the Deployment View by defining how the application integrates with physical edge hardware. It supports QR-006 by ensuring that hardware feedback is instantaneous without blocking the asynchronous recognition pipeline.

Together, these decisions match the current architecture shown below: the system is divided into a React frontend for the UI and a FastAPI backend that coordinates camera input via WebSockets, recognition, PostgreSQL-backed embedding lookup, logging, and hardware outputs. The ADRs document why recognition is behind a provider contract, why non-real provider statuses are rejected before identity matching, why the current response-time target is handled in-process, why the database is hosted locally for offline operation, and how hardware outputs are managed asynchronously.

## Static View

[Component Diagram Source (PlantUML)](static-view/component-diagram.puml)

**What the diagram shows:**
The diagram illustrates the core decoupled client-server architecture of FaceGuardV3. The `React Frontend` handles the presentation layer and, in browser mode, WebRTC camera capture. In Raspberry Pi backend mode the `FastAPI Backend` owns `/dev/video0` and the frontend only renders JPEG frames and metadata returned over WebSockets. The Backend coordinates face recognition by calling the internal `Face Recognition Module` (based on InsightFace), handles persistent state by requiring the `SQL Interface` from the `PostgreSQL` database, and enforces rate-limiting to prevent brute-force attacks. API endpoints and WebSockets are secured via JWT authentication. Finally, it issues commands to the `LED Controller` to manage physical access indication.

**Coupling and Cohesion:**
*   **Coupling:** The system exhibits low coupling across all layers. The UI is completely decoupled from the ML logic and database via a clean REST/WebSocket API. By logically separating the `Face Recognition Module` behind an `Internal Python Interface`, the `FastAPI Backend` is decoupled from the specific ML implementation details.
*   **Cohesion:** The `Face Recognition Module` has high functional cohesion, dedicated entirely to extracting embeddings and anti-spoofing. The `FastAPI Backend` maintains cohesion by focusing on orchestrating the access control flow and API serving.

**Maintainability implications:**
The decoupled approach simplifies scaling. The extraction of the UI into a React SPA means multiple independent frontends (e.g., mobile apps) can now easily consume the FastAPI endpoints. The `SQL Interface` (via `psycopg2`) and the face recognition logic can be mocked during unit testing.

**Quality requirements:**
*   **Supports:** *Testability* (internal components can be mocked), *Scalability* (separated frontend and backend), and *Performance* (WebSockets drastically reduce UI latency).
*   **Constrains:** *Complexity* (maintaining two separate tech stacks: Node.js and Python).

## Dynamic View

[Sequence Diagram Source (PlantUML)](dynamic-view/sequence-diagram.puml)

**What the diagram shows:**
The diagram maps a successful "happy path" access attempt in either camera mode. Browser mode captures and sends a frame from the `React Client`; backend mode captures the latest frame directly in the `FastAPI Server`. The server delegates face extraction to the `Recognition Module` (which interacts with the ML `Model`), and then explicitly calls the `Storage` database layer to find the closest matching identity. Upon a successful match, the server records the event in `Logs`, turns on the `LED Indicator` (blue), and returns the result plus preview metadata to the client.

**What scenario the diagram represents:**
The diagram represents the primary access control workflow: a user attempting to enter the lab. It traces the sequence of events from the physical approach of the user to the camera, through the extraction and verification of face embeddings, down to the final physical response (illuminating LEDs) and database logging.

**Why that scenario is important to the product:**
This scenario is the core value proposition of FaceGuardV3. It demonstrates how the system combines hardware inputs (Camera), heavy machine learning tasks (InsightFace models), and hardware outputs (LEDs) within a single coordinated flow to ensure secure, automated access.

**Architecture decisions, integration boundaries, and quality requirements:**
*   **Architecture Decisions:** The diagram clarifies the decision to perform face embedding matching *in memory* (the `FastAPI Server` requests the database layer to fetch all known embeddings and compare them internally via cosine similarity), rather than performing vector similarity search directly inside the database using extensions.
*   **Integration Boundaries:** It highlights the critical boundaries between the presentation layer (`React Client`), the software backend (`FastAPI Server`), and the physical edge hardware (Camera, LEDs), showing exactly when and where the software triggers physical state changes.
*   **Quality Requirements:** It helps reason about *Performance* (latency from frame capture to LED illumination depends heavily on the ML model execution, database retrieval times, and WebSocket transmission) and *Security/Reliability* (ensuring the LED only signals success and logs are written strictly after a successful database match).


## Deployment View

[Deployment Diagram Source (PlantUML)](deployment-view/deployment-diagram.puml)

**What the diagram shows:**
The deployment view illustrates how the FaceGuardV3 system is deployed at the edge. The application runs as separate Docker containers (`docker-frontend`, `docker-backend`, and `docker-db-1`) orchestrated by Docker Compose on a `Raspberry Pi` located at the lab entrance. The backend container receives only the required host devices: USB camera `/dev/video0` and GPIO character device `/dev/gpiochip0`. The frontend container exposes port 3000 for the `Admin Workstation`, while the backend exposes port 8000 for API and WebSocket traffic. State management is handled locally by PostgreSQL using the persistent `pgdata` volume.

**Why the selected deployment model was chosen:**
*   **Docker Containerization:** Machine learning libraries (like OpenCV and InsightFace) often have complex system-level dependencies. Packaging the application in Docker ensures that it runs reliably and reproducibly on any host machine without dependency conflicts. Volume mounts are used to persist `.env` and downloaded `insightface_models`, preventing the need to re-download heavy models on every container restart.
*   **Local Database Container:** Using a local PostgreSQL database removes the dependency on an external internet connection, which is critical for edge deployments where network stability is not guaranteed.

**How the current deployment supports or constrains the product:**
*   **Supports:** *Portability* and *Ease of Installation* are highly supported. Deploying the system in a new lab only requires Docker Compose and an initial internet connection. *Reliability* is strongly supported since the system can function completely offline.
*   **Constrains:** *Local Storage Management* is constrained, as the database data now consumes space on the edge device itself.

**What must be considered when deploying or operating:**
Administrators must populate `backend/.env` before running Compose and use both `docker-compose.yml` and `docker-compose.pi.yml` for Pi hardware deployments. The database and backend consume the same env file. The `insightface_models` directory must remain mounted for ONNX models, and the `pgdata` volume must be preserved on rebuilds and restarts. On Raspberry Pi 5, current Raspberry Pi OS exposes the header GPIO controller as `gpiochip0`, so the LED controller constructs gpiozero's `LGPIOFactory` explicitly with `GPIO_CHIP=0`; the legacy `RPi.GPIO` package and privileged containers are not required.
