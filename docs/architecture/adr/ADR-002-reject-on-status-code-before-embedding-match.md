# ADR-002: Reject Access Based on Provider Status Code Before Embedding Comparison

**ID:** ADR-002

**Status:** Accepted

**Context:**

The customer requested protection against basic impersonation attempts,
such as presenting a printed photo or a phone screen showing an authorized
user's face to the camera (see customer feedback: "Registration via
video"). A recognition pipeline that only compares face embeddings for
similarity, without first checking whether the presented face passed a
liveness/validity check, is vulnerable to this kind of static 2D
presentation attack: a high-quality photo of an authorized user can produce
an embedding similar enough to be matched.

The team needed a way to reject spoofed or invalid inputs before they ever
reach the embedding-comparison step, so that a spoof attempt cannot be
granted access purely on embedding similarity.

**Decision:**

The `FaceProviderInterface.extract_embedding()` contract returns a
`status_code` alongside the embedding (e.g. `"real"`, `"spoof"`,
`"no_face"`). `process_access_attempt()` in the business-logic layer checks
this status_code first: if it is not `"real"`, the attempt is rejected
immediately (`access_granted = False`) and embedding comparison against the
database is skipped entirely. Only inputs that pass this initial check
proceed to similarity comparison against stored embeddings.

The current automated quality tests verify this behavior through provider
doubles that return controlled `status_code` values. Concrete production
providers must preserve the same contract when they classify an input as
real, spoofed, or invalid.

**Alternatives considered:**

- Compare embeddings first and apply spoof/no-face checks afterward. This
  was rejected because a spoofed input could still be granted access before
  the invalid status is considered.
- Treat spoof detection as UI-only feedback. This was rejected because the
  access decision must be enforced in the backend business-logic path, not
  only displayed in the interface.
- Store spoof/no-face attempts for later review but continue matching
  embeddings. This was rejected because logging alone would not prevent an
  access grant.

**Consequences and tradeoffs:**

- Positive: Provides a first line of defense against basic photo/screen
  presentation attacks, independent of how similar the resulting embedding
  might be to a legitimate user's embedding.
- Positive: The check is provider-agnostic — any provider that implements
  the interface can plug in its own liveness/spoof detection logic without
  business logic needing to change.
- Negative: The strength of this protection depends entirely on the quality
  of the liveness/spoof signal produced by the concrete provider. A weak or
  bypassable liveness check in the underlying provider would silently
  weaken this protection.
- Negative: This decision does not address more sophisticated attacks (e.g.
  video replay or 3D masks); QR-002 and QRT-002 are explicitly scoped to
  static 2D photo/screen presentation attacks only.

**Quality requirements addressed:**

- QR-002 (Resistance to Static Photo Spoofing) — directly addressed. The
  current supporting QRT-002 check verifies rejection of `"spoof"` and
  `"no_face"` statuses before access can be granted; it does not prove the
  requirement's 9/10 physical presentation-attack target. See
  [QR-002](../../quality-requirements.md#qr-002-resistance-to-static-photo-spoofing).
