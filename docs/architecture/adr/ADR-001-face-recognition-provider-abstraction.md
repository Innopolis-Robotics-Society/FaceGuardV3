# ADR-001: Introduce a Face Recognition Provider Abstraction

**ID:** ADR-001

**Status:** Accepted

**Context:**

During MVP v1, the recognition pipeline called a specific, heavy recognition
library directly from the application and business-logic layer. This caused
two problems observed by the customer: the system could freeze during model
loading/inference, and any change to the recognition approach (e.g. swapping
to a lighter or faster model) risked touching business logic, API routes,
and UI code that had no reason to depend on the internals of a specific
recognition library.

The team needed a way to change the underlying face-recognition provider
(e.g. move to a lightweight ONNX-based model) without rewriting or
re-testing unrelated application logic, and to make the recognition step
independently testable without real ML models or camera hardware.

**Decision:**

Introduce a `FaceProviderInterface` that defines a single contract method,
`extract_embedding(frame) -> (embedding, face_metadata, status_code)`.
The business-logic layer (`backend/faceguard/business_logic.py`,
`process_access_attempt`) depends only on this interface, never on a
concrete recognition library. Concrete providers (the real ML-based
recognizer, and test doubles such as `MockFaceRecognizer` and
`FakePipelineRecognizer`) implement the interface and can be swapped freely.

**Alternatives considered:**

- Keep direct calls to the recognition library in the Streamlit pages and
  business logic. This was rejected because it would keep UI flow, access
  decisions, and ML implementation details tightly coupled.
- Use separate interfaces for embedding extraction, face detection, and
  liveness checks. This was rejected for the current scope because the
  access decision needs one combined result from the recognition step, and
  a larger interface hierarchy would add complexity without improving the
  current tests or deployment model.

**Consequences and tradeoffs:**

- Positive: The recognition provider can be replaced (e.g. heavy model to
  ONNX-based model) without modifying business logic or API route contracts,
  reducing regression risk.
- Positive: Business logic can be unit- and quality-tested with fast,
  deterministic fake/mock providers instead of requiring real models or
  camera hardware in CI (see `tests/quality/test_inference_provider_contract.py`,
  `tests/mocks.py`).
- Negative: Adds one additional abstraction layer that must be understood
  and kept in sync when the interface contract changes (e.g. if a future
  provider needs to return additional metadata).
- Negative: Any behavior that is provider-specific (e.g. provider-specific
  confidence calibration) must still be normalized to the shared interface
  contract, which can hide provider-specific nuance from callers.

**Quality requirements addressed:**

- QR-003 (Recognition Model Modularity) — directly addressed. The interface
  is the mechanism that allows swapping recognition providers while keeping
  backend entry points and business-logic test assertions
  unchanged, which is the scenario QR-003 measures and QRT-003 verifies.
  See [QR-003](../../quality-requirements.md#qr-003-recognition-model-modularity).
