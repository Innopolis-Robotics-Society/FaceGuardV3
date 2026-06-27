# Definition of Done

A Product Backlog Item (PBI) may be marked Done only when all of the following are satisfied:

- [ ] All issue-specific acceptance criteria are satisfied
- [ ] The work is reviewed and approved by a different team member than the implementer
- [ ] For user stories, all linked supporting PBIs provide the required
      implementation, review, and verification evidence
- [ ] Required automated tests and/or manual verification checks pass
- [ ] Automated unit tests pass and critical modules maintain ≥ 30% line
      coverage, verified via CI coverage report
- [ ] Automated integration tests pass for important component interactions
- [ ] For changes affecting the recognition pipeline, total processing time
      from face detection to UI decision is ≤ 3 seconds,
      verified by the linked automated QRT for QR-PERF-001
- [ ] For changes affecting access control logic, unauthorized users are
      correctly rejected, verified by the linked automated QRT for QR-SEC-002
- [ ] For changes affecting the recognition pipeline or model, the
      application logic remains unchanged and CI passes without
      modifying business logic test assertions,
      verified by the linked automated QRT for QR-MAIN-003
- [ ] All automated Quality Requirement Tests (QRTs) linked to affected
      quality requirements pass in CI
- [ ] For changes affecting the recognition pipeline (OpenCV/InsightFace),
      manual verification on the test page is performed and recorded
- [ ] If a Docker container is affected, the container builds and runs
      successfully with the change included
- [ ] No secrets, credentials, or real/non-sanitized employee data are
      committed to the repository; only sanitized test/demo data is used
      in tests, fixtures, and public artifacts
- [ ] Verification evidence is preserved in the normal workflow artifacts
      (PR/MR description, linked issue, or reports/)
- [ ] CHANGELOG.md is updated with a user-visible entry, or explicitly
      marked not applicable
- [ ] Relevant documentation (README, docs/) is updated if the change
      affects setup, usage, or interfaces
- [ ] For supporting or implementation PBIs, the issue-linked PR/MR is
      merged into the protected default branch (main)
- [ ] CI pipeline passes, including linting, type/format check, unit tests,
      integration tests, coverage, QRTs, and the additional QA check
