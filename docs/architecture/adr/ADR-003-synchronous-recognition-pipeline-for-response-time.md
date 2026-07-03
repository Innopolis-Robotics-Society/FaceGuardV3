# ADR-003: Keep the Recognition Pipeline Synchronous and In-Process for Sub-3-Second Response

**ID:** ADR-003

**Status:** Accepted

**Context:**

MVP v1 required manual triggering of recognition and could freeze because
heavy model loading blocked the rest of the application. The customer
explicitly reported this as a usability problem ("Site freezes; make
recognition faster"). For the deployment scenario the product targets — a
single local access point with a small database of up to ~20 registered users
— the team needed to guarantee that a full access attempt (capture,
preprocess, extract embedding, compare against the database, and display a
decision) completes within a bounded, predictable time.

**Decision:**

Keep the recognition pipeline synchronous and in-process (no background job
queue, no async worker, no external inference service) for this scale of
deployment, but require that:

- The face-recognition provider used in production is lightweight enough
  (e.g. ONNX-based) to keep per-frame inference fast, decoupled from
  business logic via the `FaceProviderInterface` (ADR-001).
- The database comparison step remains a simple, low-overhead operation
  appropriate for a database of this size (tens of users), avoiding
  unnecessary work in the critical path between frame capture and decision.

This decision is verified by QRT-001, which times both the embedding
extraction step and the full `process_access_attempt` path against the
3.0-second budget defined in QR-001 using deterministic test providers.

**Alternatives considered:**

- Move recognition to a background job queue. This was rejected for the
  current access-control flow because the user needs an immediate allow/deny
  decision at the entry point.
- Use an external inference service. This was rejected for the current
  local deployment model because it would add network latency and another
  runtime dependency to a small, single-entry-point installation.
- Introduce asynchronous orchestration in the UI/backend path. This was
  rejected because the current repository uses a simple Streamlit-based
  monolithic flow, and the measured quality requirement can be exercised
  without adding async infrastructure.

**Consequences and tradeoffs:**

- Positive: A synchronous pipeline is simple to reason about, simple to
  test deterministically (see `tests/quality/test_recognition_performance.py`),
  and avoids the added complexity of async orchestration for a
  small-scale local deployment.
- Positive: Directly addresses the customer-reported freezing/performance
  problem by making response time an explicit, tested, measurable
  requirement instead of an incidental property of whichever model happens
  to be loaded.
- Negative: A synchronous, in-process design does not scale to a much
  larger user database or to concurrent multi-camera access points without
  revisiting this decision (e.g. introducing indexed similarity search or
  async processing). This is a known scaling risk that should be
  reconsidered if the product's target deployment scale grows materially.
- Negative: The 3.0-second budget in QR-001 and this ADR assumes a single
  local webcam and CPU-bound inference; it does not account for GPU
  acceleration or multi-tenant load, which would require a different
  architectural approach.

**Quality requirements addressed:**

- QR-001 (Recognition Response Time) — directly addressed. This ADR is the
  architectural rationale for why a synchronous, lightweight-provider
  pipeline is expected to meet the ≤3.0-second response-time scenario that
  QR-001 defines and QRT-001 verifies. See
  [QR-001](../../quality-requirements.md#qr-001-recognition-response-time).
