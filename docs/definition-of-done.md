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
      from face detection to the UI access decision is ≤ 3 seconds,
      verified by the automated QRT linked to QR-001
      (Recognition Response Time — see `docs/quality-requirement-tests.md`)
- [ ] For changes affecting access control or recognition-decision logic,
      unauthorized or spoofed attempts are correctly rejected, verified by
      the automated QRT linked to QR-002 (Resistance to Static Photo Spoofing)
- [ ] For changes affecting the recognition pipeline or the recognition
      provider, business-logic test assertions, API route signatures, and
      UI templates remain unchanged, verified by the automated QRT linked
      to QR-003 (Recognition Model Modularity)
- [ ] All automated Quality Requirement Tests (QRTs) linked to affected
      quality requirements pass in CI. QRTs are defined in
      `docs/quality-requirement-tests.md` and referenced by their stable
      IDs — currently QRT-001 through QRT-003, and any later-added QRTs
- [ ] For critical product workflows that lack full automation (e.g. manual
      verification on the recognition test page), verification is
      performed and recorded as evidence in the PR/MR description, and
      linked to the relevant UAT scenario(s) where applicable
- [ ] If the change adds or changes user-facing functionality, the relevant
      scenario(s) in `docs/user-acceptance-tests.md` are added or updated,
      or the absence of UAT impact is explicitly stated
- [ ] If a Docker container is affected, the container builds and runs
      successfully with the change included
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
      relevant ADR(s) — whether the ADR already exists or is newly created
- [ ] No secrets, credentials, or real/non-sanitized employee data are
      committed to the repository; only sanitized test/demo data is used
      in tests, fixtures, and public artifacts
- [ ] Verification evidence is preserved in the normal workflow artifacts
      (PR/MR description, linked issue, or `reports/`)
- [ ] `CHANGELOG.md` is updated with a user-visible entry, or explicitly
      marked not applicable
- [ ] Relevant documentation (README, docs/) is updated if the change
      affects setup, usage, or interfaces
- [ ] `docs/development-process.md` is kept current with the team's actual
      development process — including board/workflow states, git and
      review workflow, configuration/secrets management, CI process, and
      dev-environment setup. For material git-workflow changes, the Mermaid
      gitGraph diagram is updated to match
- [ ] If the change affects any maintained documentation (process,
      architecture, quality, testing, or UAT docs), the hosted
      documentation site is updated to reflect it, or the change is
      explicitly documented as not affecting hosted content
- [ ] If the change affects deployment or runtime configuration,
      `.env.example` and configuration documentation are updated
- [ ] For supporting or implementation PBIs, the issue-linked PR/MR is
      merged into the protected default branch (main)
- [ ] CI pipeline passes, including linting, format check, unit tests,
      integration tests, coverage, QRTs, and the additional QA check (Bandit)
