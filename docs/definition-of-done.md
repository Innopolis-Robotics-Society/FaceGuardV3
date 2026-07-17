# Definition of Done

A Product Backlog Item may be marked Done only when every applicable item below is satisfied and the evidence is linked from its issue/PR. A manual UAT does not silently substitute for a required automated QRT, and a fake hardware adapter does not prove a physical requirement.

## Product and review

- [ ] All issue acceptance criteria are satisfied; supporting PBIs required by a user story are also complete.
- [ ] The implementation is reviewed and approved by at least one participant other than the author.
- [ ] The issue-linked PR passes required checks and is merged into protected `main`; direct unreviewed delivery is not Done.
- [ ] User-facing behavior has updated/relevant UAT scenarios or the PR explicitly records why UAT is not applicable.

## Automated verification

- [ ] Backend unit and integration tests pass and verify behavior/risks rather than mock calls alone.
- [ ] Frontend tests pass when frontend behavior changes; frontend lint, TypeScript check, and production build pass.
- [ ] Every affected **Implemented** QRT passes in CI and is referenced by stable ID. Current implemented QRTs are QRT-003, QRT-004, and QRT-005. QRT-001/QRT-002 are only partially automated; QRT-006 is Planned—see `docs/quality-requirement-tests.md`.
- [ ] For a QR without complete automation, the PR states the evidence gap, preserves any applicable manual/HIL evidence, and does not claim the full QR is implemented merely because a supporting software check passed.
- [ ] Full backend line coverage is produced and `scripts/check_critical_coverage.py` confirms every listed critical module is at least 30%; global coverage alone is insufficient.
- [ ] All mandatory CI gates pass: Black, Flake8, Bandit, backend suites/QRT/coverage, frontend tests/lint/type-check/build/audit, Compose validation, strict documentation build, and Lychee link check.
- [ ] Verification evidence is retained in normal artifacts: CI logs/artifacts, PR description, linked issue, or maintained `reports/` evidence where appropriate.

## Architecture, deployment, and documentation

- [ ] Static, dynamic, and deployment views match any changed component, interaction, device mapping, port, network, or volume.
- [ ] A stable ADR is added/updated only for a durable decision with real alternatives and consequences; affected QRs link to it.
- [ ] Base and applicable Pi Compose configurations validate. Changed images build and the relevant stack starts/healthchecks successfully when the execution environment permits it.
- [ ] Software camera/GPIO cleanup is tested. Any required real Pi/camera/GPIO check is performed and recorded separately; unavailable hardware is stated as a limitation.
- [ ] README, customer handover, troubleshooting, `.env.example`, testing/QRT docs, and contributor instructions reflect changed setup or interfaces.
- [ ] `CHANGELOG.md` contains a user-visible Unreleased entry, or the PR explicitly marks it not applicable.
- [ ] Hosted documentation builds strictly. Publishing is confirmed after merge or explicitly tracked as a release action.

## Security and data

- [ ] No secrets, real credentials, private employee data, biometric samples, or non-sanitized evidence are committed.
- [ ] Authentication, authorization, database rollback/isolation, and log handling have relevant regression tests when affected.
- [ ] Tests that use PostgreSQL are guarded to use only an isolated test database and clean their data.
