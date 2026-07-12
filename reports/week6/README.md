# Week 6 Report - Assignment 6

## 1. Project Description

**Project name:** FaceGuard  
**FaceGuard** is a face recognition access control system for a university laboratory. The system replaces physical access cards by identifying users through a camera and allowing administrators to manage employees through a web interface.

## 2. Product Backlog  
[Product Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/5)

## 3. Sprint 4 Backlog
[Sprint Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/15)

## 4. Assignment 6 Sprint 4 milestone
[Sprint 4 milestone](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/milestone/4)

## 5. Sprint Goal 

**Sprint Goal:** Deploy a stable, containerized, and secure Trial Release of the system that reliably recognizes a registered employee even if they wear accessories while maintaining background processing efficiency, optimized system response time, and protected administrative data access.

**Sprint dates:** 06.07.2026 - 12.07.2026

**Short scope summary:**  
- Speed up the system response time by decoupling frontend and backend via WebSockets
- Recognize registered employees with accessories (glasses, masks)
- Run recognition in the background without blocking the UI
- Set up a local PostgreSQL database for offline reliability
- Optimize Docker build process and stabilize image sizes
- Implement security for protected administrative data access
- Update customer-facing documentation (README, CONTRIBUTING, AGENTS, customer-handover)
- Deliver trial release v3.0.0 for customer testing

## 6. Total Sprint size
104 Story Points  

## 7. Trial-release Changes
- Decoupled React frontend and FastAPI backend communicating via WebSockets for real-time video streaming, eliminating Streamlit UI polling latency
- System response time improved from ~3s+ to ~1.1s end-to-end
- Recognition runs efficiently in the background without blocking the UI
- Recognition with accessories (glasses, masks) through lowered liveness threshold
- Connection of the recognition system to the physical door
- Local PostgreSQL database setup for enhanced offline reliability
- Stabilized Docker build process and reduced image sizes
- Created customer handover documentation, contributor guide (CONTRIBUTING.md), and agent guidance (AGENTS.md)
- Added two new quality requirements (QR-005: Duplicate Registration, QR-006: Hardware Feedback Latency) with QRT stubs
- Documented asynchronous GPIO hardware integration (ADR-007)

## 8. Product Access Artifact
[Runnable Product](https://github.com/Innopolis-Robotics-Society/FaceGuardV3)  
[FaceGuardV3 v3.0.0 Release](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v3.0.0)  

The application is deployed on a Raspberry Pi 5 with a connected USB webcam and leds.  
For local evaluation, start with Docker and open at: `http://localhost:3000`

## 9. Run Instructions
[Run instructions](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/main/README.md)

## 10-14. Links
- [README.md](../../README.md)  
- [CONTRIBUTING.md](../../CONTRIBUTING.md)  
- [AGENTS.md](../../AGENTS.md)  
- [docs/customer-handover.md](../../docs/customer-handover.md)  
- [Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/)  

## 15. Customer-facing Documentation Review
The customer reviewed the customer-facing documentation (README.md, CONTRIBUTING.md, AGENTS.md, customer-handover.md) during the Sprint Review. The customer did not confirm the current documentation as sufficient; instead, the customer requested additional documentation describing the system's functions, such as a static documentation page or site.

## 16. Transition-readiness Summary
The system reached the 'Ready for independent use' handover level. The customer confirmed the system works overall and expressed clear approval, noting that background recognition works effectively. However, the following must still happen in Week 7:
1. Add validation to the temporary access date and time field so past dates cannot be selected (minimum value must be current date and time).
2. Fix occasional page freezes under load and improve camera stream capture stability on weaker hardware.
3. Provide the requested dedicated documentation page/site detailing system functions.
4. Ensure no external databases or cloud resources are used (all data must remain local, as strictly required by the customer).
Note: Physical door integration is not planned; LED indicators serve as the access signal.

## 17. Customer Feedback Response

| Feedback point | Resulting PBI or issue | Status | Response |
|---|---|---|---|
| Recognize in a crowd not needed | [#50](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/50) | Removed | Customer confirmed during Sprint 4 Review (2026-07-10), see `reports/week6/sprint-review-summary.md` |
| Speed up the system response | [#171](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/171) | Done | Decoupled frontend and backend via WebSockets |
| Make the recognition run in the background | [#172](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/172) | Done | Recognition now runs continuously via WebSocket without blocking the UI |
| Temporary access should use explicit start and end date fields | [#57](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/57) | Done | Replaced number-of-days input with start and expiration date pickers |
| Recognition should use 5–10 captured frames and averaged embeddings | [#59](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/59) | Done | Switched from single photo capture to video frame extraction |
| Test a lighter recognition model suitable for Raspberry Pi 5 | [#86](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/86) | Done | Replaced buffalo_l with a lightweight alternative for faster recognition |
| Continue Raspberry Pi 5 setup and real webcam connection | [#58](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/58) | Done | Deployed to Raspberry Pi 5 with web-camera connected |
| Add check if employee is already registered | [#115](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115) | Done | Added duplicate name check on registration |
| Change temporary access to use exact time in addition to date | [#117](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117) | Done | Temporary access now uses exact start and expiration date+time pickers |
| Add ability to edit employee name and status after registration | [#113](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113) | Done | Edit employee dialog added to the Employees page |
| Add time of employee's last entry to the employees list | [#114](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114) | Done | Last entry column added to the Employees table |
| Add filtering by date range in access logs | [#116](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116) | Done | Date range filter added to the Logs page |
| Apply OpenCV face cropping before embedding extraction | — | Done | Applied during video frame extraction implementation as part of the recognition pipeline improvements |
| Separate model confidence score from overall system success rate | — | Done | Addressed during lightweight model integration, as confidence score is now tracked separately in access logs |

## 18. Feedback Not Addressed
All feedback from the Week 5 Sprint Review was addressed in this Sprint. Feedback received during the Week 6 UAT session has been added to the Product Backlog and is planned for the next Sprint.

## 19-20. Links to the Documentation
- [docs/roadmap.md](../../docs/roadmap.md)
- [docs/definition-of-done.md](../../docs/definition-of-done.md)
- [docs/quality-requirements.md](../../docs/quality-requirements.md)
- [docs/quality-requirement-tests.md](../../docs/quality-requirement-tests.md)
- [docs/testing.md](../../docs/testing.md)
- [docs/user-acceptance-tests.md](../../docs/user-acceptance-tests.md)
- [docs/development-process.md](../../docs/development-process.md)
- [docs/architecture/README.md](../../docs/architecture/README.md)

## 21. Summary of relevant UAT or customer-trial results.

User acceptance testing was conducted during an offline Sprint Review session on July 10, 2026.

| UAT scenario ID | Scenario | Result |
|---|---|---|
| UAT-001 | Register a new employee with permanent access | Passed |
| UAT-002 | Add a new employee with temporary access | Passed |
| UAT-006 | Automatic recognition of a registered employee | Passed |
| UAT-008 | Edit the name or status of an employee | Passed |

All four scenarios passed. No failures were recorded.

**Most important feedback received:**
- No external databases and no cloud resources of any kind must be used (strictly local).
- Temporary access needs date and time validation to prevent past dates from being selected.
- The system requires dedicated documentation detailing its functions.
- The camera stream occasionally does not capture properly on the board, and loading can be slow on weaker hardware.

## 22-23. Links
- [3.0.0 - towards MVP v3](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v3.0.0)  
- [CHANGELOG.md](../../CHANGELOG.md)

## 24. Customer Review Transcript
The public publication was permitted.  
[Customer Review Transcript.md](sprint-review-transcript.md)

## 25-28. Links
- [sprint-review-summary.md](sprint-review-summary.md)
- [reflection.md](reflection.md)
- [retrospective.md](retrospective.md)
- [llm-report.md](llm-report.md)

## 29. Current Product Status
- Trial release `v3.0.0` is available on GitHub
- The system runs on Raspberry Pi 5 with a connected web-camera
- Face recognition uses a lightweight InsightFace model (buffalo_s)
- Face recognition processes video frames instead of a single photo
- Liveness detection is implemented to prevent spoofing via photos or videos
- LED indicators show system state: yellow blinks during recognition, blue on access granted, red on access denied
- Temporary access uses exact start and expiration date+time pickers
- Duplicate name check prevents registering the same employee twice
- Edit employee dialog allows updating name and status after registration
- Last entry time is shown in the employees list
- Date range filter is available on the Logs page
- CI pipeline runs linting, formatting, security check, tests, and coverage on every PR
- All 38 tests pass with coverage exceeding 30% on all critical modules
- All four UAT scenarios passed during the Sprint Review session with the customer
- Hosted documentation site is live at `https://innopolis-robotics-society.github.io/FaceGuardV3/`

## 29. Next Steps
1. Improve recognition accuracy with accessories such as glasses and masks
2. Integrate a smart lock controlled by the recognition result
3. Increase the speed of the system's response

## 30. Contribution Traceability

| GitHub username | Issues | PRs/MRs | Review activity | Contribution |
|---|---|---|---|---|
| @s0ftach | [#199](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/199), [#205](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/205), [#218](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/218), [#230](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/230), [#237](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/237), [#239](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/239)| [#206](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/206), [#217](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/217), [#234](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/234), [#236](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/236), [#238](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/238), [#239](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/239), [#240](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/240) | [#206](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/206), [#207](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/207), [#222](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/222), [#228](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/228), [#233](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/233) | Tests, Documentation, Project Management |
| @oebarbie | [#200](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/200), [#202](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/202), [#203](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/203), [#209](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/209) | [#201](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/201), [#221](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/221), [#228](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/228), [#233](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/233) | [#217](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/217), [#221](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/221), [#234](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/234), [#236](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/236), [#238](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/238), [#240](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/241), [#239](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/239), [#240](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/241) | Documentation, Project Management |
| @Exckernels | [#226](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/226) | [#227](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/227) | [#227](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/227) | Backend, Tests CI, System's Optimization |
| @ixkci | [#171](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/171), [#172](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/172), [#196](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/196), [#197](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/197), [#213](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/213), [#215](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/215), [#241](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/241) | [#198](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/198), [#207](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/207), [#211](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/211), [#212](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/212), [#214](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/214), [#220](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/220) | [#198](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/198), [#201](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/201), [#211](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/211), [#212](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/212), [#214](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/214), [#220](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/220) | Backend, System's Optimization, Architecture |
| @grex861 | - | [#222](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/222) | - | Documentation |
| @tyajhelo | - | - | - | - |

## 31. Screenshots
Screenshots are stored in:

```text
reports/week6/images/
```
- ![Sprint milestone](images/sprint_milestone.png)
- ![SemVer release](images/release.png)
- ![PR example](images/pr_example.png)
- ![Board or project workflow view](images/board.png)
