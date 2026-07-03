# Architecture Documentation

## Architecture Decision Records

The ADRs capture the main architectural decisions that connect the current
FaceGuardV3 implementation to the quality requirements:

- [ADR-001: Introduce a Face Recognition Provider Abstraction](adr/ADR-001-face-recognition-provider-abstraction.md) supports the Static View by defining the `FaceProviderInterface` boundary between business logic and the recognition provider. It supports QR-003 by allowing provider swaps to be tested without changing the access-decision flow.
- [ADR-002: Reject Access Based on Provider Status Code Before Embedding Comparison](adr/ADR-002-reject-on-status-code-before-embedding-match.md) supports the Dynamic View by fixing the order of the recognition flow: provider status is checked before embedding comparison. It supports QR-002 by making spoof/no-face rejection part of the backend access decision.
- [ADR-003: Keep the Recognition Pipeline Synchronous and In-Process for Sub-3-Second Response](adr/ADR-003-synchronous-recognition-pipeline-for-response-time.md) supports the Dynamic and Deployment Views by keeping recognition in the local FaceGuard application process for the current single-entry-point deployment. It supports QR-001 by keeping response-time measurement focused on the direct capture, extraction, comparison, and decision path.

Together, these decisions match the current architecture shown below: Streamlit application runs in a local application container and coordinates camera input, recognition, PostgreSQL-backed embedding lookup, logging, and hardware outputs. The ADRs document why recognition is behind a provider contract, why non-real provider statuses are rejected before identity matching, and why the current response-time target is handled in-process rather than through external queues or inference services.

## Static View

[Component Diagram Source (PlantUML)](static-view/component-diagram.puml)

**What the diagram shows:**
The diagram illustrates the core client-server architecture of FaceGuardV3. The `Streamlit Application` acts as a monolithic orchestrator. It receives a `Video Stream` from the physical `Camera`, coordinates face recognition by calling the internal `Face Recognition Module` (based on InsightFace), and handles persistent state by requiring the `SQL Interface` from the `PostgreSQL` database. Finally, it issues commands to the `Door & LED Controller` to manage physical access.

**Coupling and Cohesion:**
*   **Coupling:** The system exhibits low coupling between the physical hardware, the database, and the ML subsystem. By logically separating the `Face Recognition Module` behind an `Internal Python Interface`, the `Streamlit Application` is decoupled from the specific ML implementation details. The UI orchestrates the flow without containing ML logic.
*   **Cohesion:** The `Face Recognition Module` has high functional cohesion, dedicated entirely to extracting embeddings and anti-spoofing. The `Streamlit Application` maintains cohesion by focusing on orchestrating the access control flow and serving the UI.

**Maintainability implications:**
The monolithic approach simplifies current deployment for a localized laboratory setup. The extraction of the `SQL Interface` (via `psycopg2`) and the face recognition logic into separate modules allows them to be mocked during unit testing. However, the lack of a decoupled REST API means that scaling to multiple independent frontends (e.g., mobile apps) would require significant refactoring.

**Quality requirements:**
*   **Supports:** *Testability* (internal components can be mocked), *Time-to-market/Modifiability* (Streamlit allows rapid UI iterations).
*   **Constrains:** *Scalability* (tight coupling of UI and backend logic limits distributed scaling) and *Performance* (running ML inference and UI rendering in the same monolithic process might create bottlenecks under high load).

## Dynamic View

[Sequence Diagram Source (PlantUML)](dynamic-view/sequence-diagram.puml)

**What the diagram shows:**
The diagram maps a successful "happy path" access attempt. The `Camera` initiates the interaction by capturing and sending a frame. The `FaceGuard Application` orchestrates the request by first delegating face extraction to the `Recognition Module` (which interacts with the ML `Model`), and then explicitly calling the `Storage` database layer to find the closest matching identity. Upon a successful match, the application sequentially records the event in `Logs`, turns on the `LED Indicator` (blue), and triggers the `Door Lock` to open.

**What scenario the diagram represents:**
The diagram represents the primary access control workflow: a user attempting to enter the lab. It traces the sequence of events from the physical approach of the user to the camera, through the extraction and verification of face embeddings, down to the final physical response (opening the door, illuminating LEDs) and database logging.

**Why that scenario is important to the product:**
This scenario is the core value proposition of FaceGuardV3. It demonstrates how the system combines hardware inputs (Camera), heavy machine learning tasks (InsightFace models), and hardware outputs (LEDs, Door Relays) within a single coordinated flow to ensure secure, automated access.

**Architecture decisions, integration boundaries, and quality requirements:**
*   **Architecture Decisions:** The diagram clarifies the decision to perform face embedding matching *in memory* (the `FaceGuard Application` requests the database layer to fetch all known embeddings and compare them internally via cosine similarity), rather than performing vector similarity search directly inside the database using extensions.
*   **Integration Boundaries:** It highlights the critical boundaries between the physical edge hardware (Camera, LEDs, Door) and the software monolith (`FaceGuard Application`), showing exactly when and where the software triggers physical state changes.
*   **Quality Requirements:** It helps reason about *Performance* (latency from frame capture to door opening depends heavily on the ML model execution and database retrieval times) and *Security/Reliability* (ensuring the door only opens and logs are written strictly after a successful database match).


## Deployment View

[Deployment Diagram Source (PlantUML)](deployment-view/deployment-diagram.puml)

**What the diagram shows:**
The deployment view illustrates how the FaceGuardV3 system is deployed at the edge. The core application runs as a single Docker container (`faceguard:latest`) directly on a `Raspberry Pi` located at the lab entrance. The hardware peripherals (Camera, LEDs, Door Relay) are physically connected to this Raspberry Pi via USB/CSI and GPIO pins. The container exposes port 8501 for the `Admin Workstation` to connect over the local network to view the UI. State management is offloaded to the cloud, with the application connecting to `Neon.tech` PostgreSQL hosted on AWS.

**Why the selected deployment model was chosen:**
*   **Docker Containerization:** Machine learning libraries (like OpenCV and InsightFace) often have complex system-level dependencies. Packaging the application in Docker ensures that it runs reliably and reproducibly on any host machine without dependency conflicts. Volume mounts are used to persist `secrets.toml` and downloaded `insightface_models`, preventing the need to re-download heavy models on every container restart.
*   **Serverless Cloud Database (Neon):** Using a managed, serverless PostgreSQL database removes the burden of local database administration, backups, and storage management, while providing easy access across environments.

**How the current deployment supports or constrains the product:**
*   **Supports:** *Portability* and *Ease of Installation* are highly supported. Deploying the system in a new lab only requires Docker and an internet connection.
*   **Constrains:** *Reliability* is constrained by internet connectivity. Because the database is hosted externally on AWS, the system requires a persistent, stable internet connection to function. If the lab loses external network access, the monolithic container cannot authenticate users.

**What must be considered when deploying or operating:**
Administrators must ensure that the `secrets.toml` file is correctly populated with Neon DB credentials and mounted as a read-only volume. Furthermore, the `insightface_models` directory must be mounted to cache the ONNX models; otherwise, startup times will be severely impacted by large network downloads.
