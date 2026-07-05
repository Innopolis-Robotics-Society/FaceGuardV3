# ADR-004: Enforce Temporary Access Window in Application Logic with TIMESTAMP Normalization
**ID:** ADR-004  

**Status:** Accepted

**Context:**

Temporary access was originally stored as `DATE` columns (`start_date`,
`expiration_date`). This caused two real defects: (1) recognition never
checked expiration or start date at all, so expired or not-yet-started
temporary employees could still be granted access (QR-004 gap), and (2)
even after adding a check, comparing a `DATE` against `NOW()` in
PostgreSQL implicitly casts the date to midnight, so "valid through July
4th" would actually expire at the start of July 4th instead of its end.

**Decision:**

1. Store `start_date`/`expiration_date` as `TIMESTAMP`, with a one-time
   migration (`TEMPORARY_ACCESS_DATETIME_MIGRATION`, run inside `init_db()`)
   that converts any legacy `DATE` columns, expanding a bare expiration
   date to the end of that day (`+ INTERVAL '1 day' - INTERVAL '1
   microsecond'`) so existing data keeps its intended meaning.
2. Normalize all temporary-access bounds through `_normalize_access_window()`
   at write time (`add_employees`, `update_employee`), so a `date` input is
   always converted to a full-day `datetime` window before it reaches the
   database.
3. Enforce the access window in application code via
   `_temporary_access_is_active()`, called from `get_all_embeddings()`
   before any embedding is returned for recognition matching, rather than
   relying only on the scheduled `delete_expired_employees()` cleanup.

**Consequences and tradeoffs:**

- Positive: Fixes both the expiration-not-enforced and
  start-date-not-enforced defects, and the DATE/TIMESTAMP boundary bug, in
  one consistent place.
- Positive: `_temporary_access_is_active()` is a pure function, testable
  without a real database (see `tests/unit/test_temporary_access.py`),
  including legacy `date` inputs for backward compatibility.
- Negative: Correctness now depends on every code path that reads
  employee embeddings calling `_temporary_access_is_active()` — this is
  currently centralized in `get_all_embeddings()`, but any future new read
  path must remember to reuse it, or the same class of bug (expired access
  still granted) can reappear.
- Negative: The check relies on the application server's local clock
  (`_current_access_time()` uses naive local time), not the database
  clock; multi-server deployments with clock drift are not addressed by
  this decision.

**Quality requirements addressed:**

- QR-004 (Temporary Access Window Enforcement) directly addressed. This
  ADR documents the decision to enforce the access window in application
  logic with explicit datetime normalization, which QRT-004 verifies.
