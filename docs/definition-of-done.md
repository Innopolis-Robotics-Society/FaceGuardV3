# Definition of Done

A Product Backlog Item (PBI) may be marked Done only when all of the following are satisfied:

- [ ] All issue-specific acceptance criteria are satisfied
- [ ] The work is reviewed and approved by a different team member than the implementer
- [ ] For user stories, all linked supporting PBIs provide the required
      implementation, review, and verification evidence
- [ ] Automated unit tests pass and critical modules maintain ≥ 30% line
      coverage, verified via CI coverage report
- [ ] Automated integration tests pass for important component interactions
- [ ] All automated Quality Requirement Tests (QRTs) linked to affected
      quality requirements pass in CI, referenced by their stable IDs —
      currently QRT-001 (response time), QRT-002 (spoofing resistance),
      QRT-003 (modularity), QRT-004 (temporary access window enforcement),
      and any later-added QRTs (see `docs/quality-requirement-tests.md`)
- [ ] For critical product workflows that lack full automation (e.g. manual
      verification on the recognition test page), verification is
      performed and recorded as evidence in the PR/MR description, and
      linked to the relevant UAT scenario(s) where applicable
- [ ] If the change adds or changes user-facing functionality, the relevant
      scenario(s) in `docs/user-acceptance-tests.md` are added or updated,
      or the absence of UAT impact is explicitly stated
- [ ] CI pipeline passes, including linting, format check, unit tests,
      integration tests, coverage, QRTs, and the additional QA check (Bandit)
- [ ] If a Docker container is affected, it builds and runs successfully
      with the change included
- [ ] Relevant architecture documentation (`docs/architecture/README.md`,
      static/dynamic/deployment views) is updated to match the change, or
      the change is explicitly documented as not applicable to the current
      architecture
- [ ] For changes that introduce, change, or reverse an architecture
      decision, a new or updated ADR is created in `docs/architecture/adr/`
      with a stable `ADR-NNN` ID, and the ADR identifies which quality
      requirement(s) it addresses
- [ ] If the change affects or introduces a quality requirement in
      `docs/quality-requirements.md`, that requirement is linked to the
      relevant ADR(s)
- [ ] No secrets, credentials, or real/non-sanitized employee data are
      committed to the repository; only sanitized test/demo data is used
      in tests, fixtures, and public artifacts
- [ ] Verification evidence is preserved in the normal workflow artifacts
      (PR/MR description, linked issue, or `reports/`)
- [ ] `CHANGELOG.md` is updated with a user-visible entry, or explicitly
      marked not applicable
- [ ] Relevant documentation (README, docs/) is updated if the change
      affects setup, usage, or interfaces, including `docs/development-process.md`
      when the workflow, git process, configuration management, CI, or
      dev environment changed (update the Mermaid gitGraph diagram for
      material git-workflow changes)
- [ ] If the change affects any maintained documentation, the hosted
      documentation site is updated to reflect it, or explicitly documented
      as not affecting hosted content
- [ ] If the change affects deployment or runtime configuration,
      `.env.example` and configuration documentation are updated
- [ ] For supporting or implementation PBIs, the issue-linked PR/MR is
      merged into the protected default branch (main)
