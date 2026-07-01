# Week 5 Report - Assignment 5

## 1. Project Description

**Project name:** FaceGuard  
**FaceGuard** is a face recognition access control system for a university laboratory. The system replaces physical access cards by identifying users through a camera and allowing administrators to manage employees through a web interface.

## 2. Product Backlog  
[Product Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/5)

## 3. Sprint 3 Backlog
[Sprint Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/14/views/1)

## 4. Assignment 5 Sprint 3 milestone
[Sprint 3 milestone](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/milestone/3)

## 5. Sprint Goal: 

**Sprint Goal** is to set up the LED indicators to see the system's state and address customer's feedback from the last sprint review.

**Sprint dates:** 29.06.2026 - 05.07.2026

**Short scope summary:** The sprint 3 is focused on connecting the LED indicators to see the system's state and address customer's feedback from the last sprint review, such as:  
- #113 - Add ability to edit employee name and status after registration
- #114 - Add time of employee's last entry to the employees list
- #115 - Add a duplicate name check when registering a new employee
- #116 - Add filtering by date range in access logs
- #117 - Change temporary access to use exact time in addition to date

## 6. Total Sprint size:
[TODO] Story Points  

## 7. Delivered Product Changes
[TODO]

- Added the ability to edit employee name and status after registration
- Added time of employee's last entry to the employees list
- Added a duplicate name check when registering a new employee
- Added filtering by date range in access logs
- Changed temporary access to use exact time in addition to date

## 8. Runnable Product

[Runnable Product](https://github.com/Innopolis-Robotics-Society/FaceGuardV3)  

The application can be started with Docker and opened at: `http://localhost:8501`

## 9. Run Instructions

[Run instructions](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/main/README.md)

## 10. Customer Feedback Response
[TODO]

| Feedback point | Resulting PBI or issue | Status | Response |
|---|---|---|---|
| Temporary access should use explicit start and end date fields | [#57](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/57) | Done | Replaced number-of-days input with start and expiration date pickers |
| Recognition should use 5–10 captured frames and averaged embeddings | [#59](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/59) | Done | Switched from single photo capture to video frame extraction |
| Test a lighter recognition model suitable for Raspberry Pi 5 | [#86](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/86) | Done | Replaced buffalo_l with a lightweight alternative for faster recognition |
| Continue Raspberry Pi 5 setup and real webcam connection | [#58](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/58) | Done | Deployed to Raspberry Pi 5 with web-camera connected |
| Add check if employee is already registered | [#115](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115) | To Do | Added to backlog for next Sprint |
| Change temporary access to use exact time in addition to date | [#117](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117) | To Do | Will be added to backlog for next Sprint |
| Add ability to edit employee name and status after registration | [#113](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113) | To Do| Will be added to backlog for next Sprint |
| Add time of employee's last entry to the employees list | [#114](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114) | To Do | Will be added to backlog for next Sprint |
| Add filtering by date range in access logs | [#116](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116) | To Do | Will be added to backlog for next Sprint |
| Apply OpenCV face cropping before embedding extraction | — | Done | Applied during video frame extraction implementation as part of the recognition pipeline improvements |
| Separate model confidence score from overall system success rate | — | Done | Addressed during lightweight model integration, as confidence score is now tracked separately in access logs |

## 11. Feedback Not Addressed
[TODO]

All feedback from the Week 3 Sprint Review was addressed in this Sprint. Feedback received during the Week 4 UAT session has been added to the Product Backlog and is planned for the next Sprint.

## 12-19. Links to the Documentation

- [docs/roadmap.md](../../docs/roadmap.md)
- [docs/definition-of-done.md](../../docs/definition-of-done.md)
- [docs/quality-requirements.md](../../docs/quality-requirements.md)
- [docs/quality-requirement-tests.md](../../docs/quality-requirement-tests.md)
- [docs/testing.md](../../docs/testing.md)
- [docs/user-acceptance-tests.md](../../docs/user-acceptance-tests.md)
- [docs/development-process.md](../../docs/development-process.md)
- [docs/docs/architecture/README.md](../../docs/architecture/README.md)

## 20. Links to the static, dynamic, and deployment view artifacts.
[TODO]

## 21. Link to the ADR directory or ADR index.
[TODO]

## 22. Architecture
[TODO]  
Summary of the architecture and how it supports the current product.

## 23. QRs and Architecture decisions
[TODO]
Short explanation of how quality requirements are linked to the architecture decisions.

## 24. Testing and CI
[TODO]
Testing and CI status summary for the delivered increment.

## 25-27. CI Pipeline

- [CI pipeline](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/actions)
- [Latest protected-default-branch CI run] [TODO]
- [Release 2.1.0 - MVP v2](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v2.1.0) [TODO]

## 28. Changelog
[CHANGELOG.md](../../CHANGELOG.md)

## 29. Demo Video
[TODO]
[MVP v2 demo video]

## 30. UAT Results Summary
[TODO]
User acceptance testing was conducted during an online Sprint Review session on June 27, 2026. 
Due to the remote format, the team demonstrated each UAT scenario to the customer, 
who observed, provided feedback, and confirmed acceptance. All 7 UAT scenarios passed.

| UAT scenario ID | Scenario | Result |
|---|---|---|
| UAT-001 | Register a new employee with permanent access | Passed |
| UAT-002 | Add a new employee with temporary access | Passed |
| UAT-003 | Remove a registered employee | Passed |
| UAT-004 | View the list of all registered employees | Passed |
| UAT-005 | View the access logs | Passed |
| UAT-006 | Automatic recognition of a registered employee | Passed |
| UAT-007 | Rejection of an unregistered person | Passed |

All seven scenarios passed. No failures were recorded.

**Most important feedback received:**
- Add a duplicate name check when registering a new employee
- Change temporary access to use exact time in addition to date
- Add ability to edit employee name and status after registration
- Add time of employee's last entry to the employees list
- Add filtering by date range in access logs

## 31. Link to the hosted documentation site
[TODO]
Our project does not require to be hosted, as the customer wants to have it on the localhost.

## 32. Customer Review Transcript

The public publication was permitted.  
[Customer Review Transcript.md](customer-review-transcript.md)

## 33. Explicit of deviations
[TODO]
Our project does not require to be hosted or deployes, as the customer wants to have it on the localhost. Therefore, our runnable artifact is a repository with setup instructions.

## 34-37. Links

- [sprint-review-summary.md](sprint-review-summary.md)
- [reflection.md](reflection.md)
- [retrospective.md](retrospective.md)
- [llm-report.md](llm-report.md)

## 38. Current Product Status
[TODO]
- MVP v2 release is available as release `v2.1.0`.
- The system runs on Raspberry Pi 5 with a connected web-camera.
- Face recognition uses a lightweight model.
- Face recognition processes video frames instead of a single photo.
- Liveness detection is implemented to prevent spoofing via photos or videos.
- Automatic recognition works without a button press on the Recognition page.
- Temporary registration uses start and expiration date pickers.
- CI pipeline is configured with automated tests, coverage reporting, linting, formatting, and Bandit security check.
- All 28 tests pass with 41% overall coverage across the `faceguard` package.
- All seven UAT scenarios passed during the Sprint Review session with the customer.
- Add duplicate name check when registering a new employee - [#115](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115)
- Change temporary access to use exact time in addition to date - [#117](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117)
- Add ability to edit employee name and status after registration - [#113](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113)
- Add time of employee's last entry to the employees list - [#114](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114)
- Add filtering by date range in access logs - [#116](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116)
- Add failure notifications for unrecognized attempts or system errors.


## 39. Next Steps
[TODO]
1. Improve recognition accuracy with accessories such as glasses and masks.
2. Integrate a smart lock controlled by the recognition result.

## 40. Contribution Traceability
[TODO]

| GitHub username | Issues | PRs/MRs | Review activity | Contribution |
|---|---|---|---|---|
| @s0ftach | [#57](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/57) | [#89](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/89) | [#98](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/98) | Backend, Testing, Documentation, Presentation |
| @oebarbie |  |  |  | Backend, Documentation, H/W setup |
| @Exckernels |  |  |  | Backend, Testing, Documentation, LEDs setup |
| @ixkci |  |  |  | Backend, Testing |
| @grex861 |  |  |  | LEDs setup, Documentation |
| @tyajhelo |  |  |  | Documentation |

## 41. Screenshots
[TODO]
Screenshots are stored in:

```text
reports/week4/images/
```
- ![Sprint milestone](images/sprint_milestone.png)
- ![Board or project workflow view]((images/board.png))
- ![Latest CI run](images/ci_run.png)
- ![SemVer release](images/semver_release.png)
- ![PR example](images/pr_example.png)
- ![Hosted docs site](images/hosted_site.png)

- ![Branch protection](images/branch_protection.png)
- ![Coverage](images/coverage.png)
- ![QA check](images/qa_check.png)
- ![Release](images/release.png)
- ![Product Backlog](images/product_backlog.png)
- ![Sprint Backlog](images/sprint_backlog.png)  
 **Face is blurred for privacy reasons.**
- ![Recognition page](images/recognition.png)
- ![Add Employee page](images/add_employee.png)

