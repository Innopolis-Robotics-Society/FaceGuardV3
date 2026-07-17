# Week 7 Report - Assignment 6

## 1. Previous Report
[Week 6 Report](../week6/README.md)

## 2. Product Backlog
[Product Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/5)

## 3. Sprint 5 Backlog
[Sprint 5 Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/17)

## 4. Sprint 5 Milestone
[Sprint 5 milestone](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/milestone/5)

## 5. Sprint Goal
**Sprint Goal:** Resolve Week 6 customer feedback (page freeze, temporary access date validation, function-description documentation), deliver the final MVP v3 release, and confirm the final transition outcome and handover status with the customer.

**Sprint dates:**
Start date: Jul 13, 2026
Finish date: Jul 19, 2026

**Short scope summary:**
- Added password hashing and login credential management
- Implemented login lockout after 5 failed attempts within one minute
- Added validation for temporary access dates; past dates are now rejected
- Created the System Functions documentation page for non-technical users
- Improved documentation site styling with pastel purple theme and dark mode
- Added SSH connection support for remote camera selection
- Performance improvements on Raspberry Pi and reduction of registration black-screen issue
- Extended customer handover documentation

## 6. Total Sprint Size
13 Story Points

## 7. Follow-up Maintenance and Final MVP v3 Changes
- Implemented password hashing; admin credentials can be changed at any time via documented commands
- Login lockout activates after 5 failed attempts within one minute; even the correct password is rejected during the lockout period
- Added future-only validation for temporary access date and time fields; past dates are now rejected
- Created the [System Functions](../../docs/system-functions.md) page describing all key system features for non-technical users, as requested by the customer in Week 6
- Overhauled documentation site styling to a custom pastel purple theme with light and dark mode toggles
- Integrated CHANGELOG natively into the documentation site
- Added SSH connection support; camera selection now happens remotely via SSH
- Improved registration performance on Raspberry Pi and reduced the black-screen issue during registration
- Updated [Customer Handover](../../docs/customer-handover.md) to reflect completed documentation

## 8. Final Product Access Artifact
[Runnable Product (Repository)](https://github.com/Innopolis-Robotics-Society/FaceGuardV3)
[FaceGuard Final MVP v3 Release](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v3.1.0)

The application is deployed on a Raspberry Pi 5 with a connected USB webcam and LEDs.
For local evaluation, start with Docker and open at: `http://localhost:3000`

## 9. Run Instructions
[Current run instructions](../../README.md)

## 10. README.md
[README.md](../../README.md)

## 11. CONTRIBUTING.md
[CONTRIBUTING.md](../../CONTRIBUTING.md)

## 12. AGENTS.md
[AGENTS.md](../../AGENTS.md)

## 13. Customer Handover Documentation
[docs/customer-handover.md](../../docs/customer-handover.md)

## 14. Hosted Documentation Site
[Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/)

## 15. Final Transition Outcome Summary
**Handover Level Reached:** Ready for independent use
**Customer Confirmation Status:** Accepted

The customer confirmed during the Sprint 5 Review session on 16.07.2026 that they are able to use the system independently, that the current version is sufficient to manage the system going forward, and that they accept this as the final delivered product. No further changes were requested. Documentation was explicitly confirmed as sufficient after the System Functions page was added.

## 16. What Was Transferred and Delegated
As detailed in [docs/customer-handover.md](../../docs/customer-handover.md):

- **Transferred to customer:** The deployed system on the customer's Raspberry Pi 5, the local PostgreSQL database, admin credentials via `.env`, and all physical hardware including the camera and LEDs
- **Delegated:** Admin credential management, now the customer can change login and password at any time using the documented commands
- **Made available:** Full source code via the public GitHub repository (read access); hosted documentation site with setup, usage, authentication, registration, and deployment instructions
- **Retained by team:** GitHub repository ownership

## 17. Remaining Transition Blockers, Limitations, and Follow-up Items
No critical transition blockers remain. The following known limitations were communicated to the customer:

- The system has not yet been deployed on the customer's own independent infrastructure; it currently runs on the Raspberry Pi provided during the course
- Recognition accuracy is affected by lighting conditions; stable indoor lighting is required
- Raspberry Pi 5 thermal management without active cooling may affect performance under sustained load
- Occasional camera stream capture instability may occur on weaker hardware
- Medical masks are intentionally not supported for recognition due to embedding distortion; this is a security and reliability decision, not a defect
- No further team support is planned after course completion; the customer confirmed they can operate the system independently

## 18. Customer-Independent Use and Deployment Evidence
During the Sprint Review session on 16.07.2026, the customer confirmed:

- Able to use the system independently without the team's assistance: **Yes**
- System already deployed in the customer's own environment: **Not yet**
- Current version sufficient to manage the system independently going forward: **Yes**
- Anything preventing the customer from taking full control now: **No**
- Accepts this as the final delivered product: **Yes**

The system is currently deployed on the Raspberry Pi 5 used during the course. Independent customer-side deployment has not yet taken place, but the customer confirmed no blockers prevent them from doing so.

## 19. Customer Feedback Response for Sprint 5

| Feedback point | Resulting PBI or issue | Status | Response |
|---|---|---|---|
| Add validation so past dates cannot be selected for temporary access | [#219](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/219) | Done | Future-only validation added to temporary access date and time fields |
| Provide dedicated documentation page describing system functions | [#235](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/235) | Done | System Functions page created at docs/system-functions.md and published on the hosted documentation site |
| Fix occasional page freezes and improve camera stream stability | [#224](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/224) | Done | Performance improved on Raspberry Pi; registration black-screen issue reduced |

## 20. Summary of Relevant Week 7 UAT and Customer-Trial Results
UAT was conducted during the offline Sprint Review and Final Transition Confirmation session on 16.07.2026. All active UAT scenarios were executed.

| UAT scenario | Result | Comments |
|---|---|---|
| UAT-001: Register a new employee with permanent access | Passed | Registration demonstrated live. Slower on Raspberry Pi than on a laptop, otherwise works as expected |
| UAT-002: Add a new employee with temporary access | Passed | Date validation confirmed working; past dates are rejected |
| UAT-003: Remove a registered employee | Passed | — |
| UAT-004: View the list of all registered employees | Passed | All demonstrated and confirmed working |
| UAT-005: View the access logs | Passed | — |
| UAT-006: Automatic recognition of a registered employee | Passed | — |
| UAT-007: Rejection of an unregistered person | Passed | Anti-spoofing tested specifically: a photograph presented to the camera was correctly rejected |
| UAT-008: Edit the name or status of an employee | Passed | — |
| UAT-009: Register an already registered employee | Passed | — |
| UAT-010: Face recognition with accessories | Passed | Glasses recognized correctly, confirmed twice. Masks intentionally rejected for security reasons; documented as expected behavior |
| UAT-011: Admin authentication | Passed | Login lockout after 5 failed attempts confirmed working |
| UAT-012: Background recognition | Passed | — |

All 12 active UAT scenarios passed. No failures were recorded. The customer confirmed the system works and accepted it as the final delivered product. 
Documentation was reviewed live and no further changes were requested.

## 21. Final SemVer Release
[v3.1.0 - MVP v3](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v3.1.0)

## 22. CHANGELOG.md
[CHANGELOG.md](../../CHANGELOG.md)

## 23. Public Sanitized Demo Video
[Public demo video]()

## 24. Demo Day Preparation Summary
The required Week 7 rehearsal was completed. The team prepared a pre-recorded demo under 2 minutes for the Demo Day presentation. All team members will attend the Week 8 Demo Day presentation. Each team member will present at least one slide. The slide deck covers project context, delivered requirements, customer usefulness, engineering evidence, remaining limitations, and team reflection.

## 25. Sprint Review Transcript
The public publication was permitted.
[Sprint Review Transcript](sprint-review-transcript.md)

## 26. Sprint Review Summary
[sprint-review-summary.md](sprint-review-summary.md)

## 27. Reflection
[reflection.md](reflection.md)

## 28. Retrospective
[retrospective.md](retrospective.md)

## 29. LLM Report
[llm-report.md](llm-report.md)

## 30. Final Product Status
- MVP v3 is completed and available on GitHub at release [v3.1.0](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v3.1.0)
- The system is deployed on the customer's Raspberry Pi 5 with a connected USB webcam and LEDs
- Password authentication with hashing is implemented; credentials can be changed at any time via documented commands
- Login lockout activates after 5 failed attempts within one minute
- Face recognition uses a lightweight InsightFace model processing video frames with averaged embeddings
- Liveness detection prevents spoofing via photographs
- Glasses are recognized correctly; medical masks are intentionally rejected for security reasons
- LED indicators show system state: yellow blinks during recognition, blue for access granted, red for access denied
- Temporary access uses exact start and expiration date and time pickers with future-only validation
- Duplicate name check prevents registering the same employee twice
- Edit employee dialog allows updating name and status after registration
- Last entry time is shown in the employees list
- Date range filter is available on the Logs page
- SSH connection support added; camera selection happens remotely via SSH
- CI pipeline runs linting, formatting, security checks, tests, and coverage on every PR
- All tests pass with coverage exceeding 30% on all critical modules
- Hosted documentation site is live at `https://innopolis-robotics-society.github.io/FaceGuardV3/`
- Customer confirmed the system is ready for independent use and accepted it as the final delivered product
- Handover documentation confirmed sufficient by the customer after the System Functions page was added

## 31. Contribution Traceability

| GitHub username | Issues | PRs/MRs | Review activity | Contribution |
|---|---|---|---|---|
| @s0ftach | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_CONTRIBUTION] |
| @oebarbie | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_LINKS] | Documentation, [INSERT_CONTRIBUTION] |
| @Exckernels | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_CONTRIBUTION] |
| @ixkci | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_CONTRIBUTION] |
| @grex861 | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_CONTRIBUTION] |
| @tyajhelo | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_LINKS] | [INSERT_CONTRIBUTION] |

## 32. Screenshots
Screenshots are stored in `reports/week7/images/`:

- ![Sprint 5 milestone](images/sprint_milestone.png)
- ![Final MVP v3 release](images/release.png)
- ![PR example](images/pr_example.png)
- ![Final product access or deployment evidence](images/deployment_evidence.png)
