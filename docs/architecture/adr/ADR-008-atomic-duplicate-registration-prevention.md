# ADR-008: Prevent Duplicate Registration Before Insert in One Transaction

**ID:** ADR-008
**Status:** Accepted

## Context

Two employee rows for the same physical face make recognition identity ambiguous. A cached pre-check outside a transaction can be stale, and two concurrent registration requests can both observe “no duplicate” and then insert. Duplicate responsibility must sit at the authoritative write boundary, while tests need deterministic embeddings without running InsightFace.

## Decision

`add_employees()` owns duplicate validation and insert as one PostgreSQL transaction:

1. acquire transaction-scoped advisory lock `1178682181` for registration;
2. read every stored non-null embedding directly from PostgreSQL, bypassing the recognition cache and regardless of current temporary-access activity;
3. calculate cosine similarity in the data-access/orchestration code using the same normalized-vector helper;
4. reject a best match at or above `0.56` with `DuplicateEmployeeError` before the name check or insert;
5. check duplicate name, insert only if both checks pass, then commit; and
6. roll back on every error and invalidate the embedding cache only after success.

FastAPI maps `DuplicateEmployeeError` to HTTP `409` and preserves the existing employee row.

## Considered alternatives

- Check only after insert and delete a duplicate: rejected because an invalid row becomes externally visible and cleanup can fail.
- Use the 60-second recognition cache: rejected because it can miss a recent registration.
- Rely only on a name uniqueness rule: rejected because the same face can be submitted with a different name.
- PostgreSQL vector extension/nearest-neighbour index: deferred; the target database is small and the added extension/deployment complexity is not justified.
- Process-local lock only: rejected because it does not serialize multiple backend processes.

## Consequences

- Check and insert are race-safe across backend processes sharing PostgreSQL.
- Registration transactions are serialized; this is acceptable for low-frequency administrative enrollment.
- Threshold calibration remains a product/model responsibility and can produce false positives or false negatives.
- QRT-005 uses deterministic embeddings through the real FastAPI boundary and real PostgreSQL, including a concurrent attempt; it does not test InsightFace internals or physical capture quality.

## Quality requirements addressed

- [QR-005](../../quality-requirements.md#qr-005-duplicate-registration-prevention).
