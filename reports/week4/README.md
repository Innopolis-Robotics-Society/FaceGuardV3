ᅠ
# Week 4 Report - Assignment 4

## 1. Project Description

**Project name:** FaceGuard  
**FaceGuard** is a face recognition access control system for a university laboratory. The system replaces physical access cards by identifying users through a camera and allowing administrators to manage employees through a web interface.

## 2. Product Backlog  
[Product Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/5)

## 3. Sprint Backlog
[Sprint Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/10/views/1)

## 4. Assignment 4 Sprint milestone
[Sprint 2 milestone](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/milestone/2)

## 5. Sprint Goal: 

**Sprint Goal** is to improve recognition speed and reliability by switching to a lightweight model, enabling video-based face enrollment, adding liveness detection, and deploying to Raspberry Pi 5.

**Sprint dates:** 22.06.2026 - 28.06.2026

**Short scope summary:** The sprint 2 is focused on making the recognition faster and more reliable by replacing the heavy buffalo_l model with a lightweight model, switching from single-photo-enrollment to the video-based enrollment for more accurate embeddings, adding liveness detection for anti-spoofing, and deploying the system to Raspberry Pi 5 with a web-camera. Temporary registration was also changed to explicit date range pickers. The UI was updated with a camera selector.

## 6. Total Sprint size:
46 Story Points  

## 7. Delivered Product Changes

- Switched to a lightweight face recognition model for improved performance
- Implemented temporary registration with start and expiration date pickers
- Deployed the system to Raspberry Pi 5 with web-camera connection
- Added liveness detection to prevent spoofing
- Added camera selector on Recognition and Add Employee pages
- Switched from single photo capture to video frame extraction
- Recognition session now starts with a Start button on the Recognition page

## 8. Runnable Product

[Runnable Product](https://github.com/Innopolis-Robotics-Society/FaceGuardV3)  

The application can be started with Docker and opened at: `http://localhost:8501`

## 9. Run Instructions

[Run instructions](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/main/README.md)

## 10. Customer Feedback Response

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

All the feedback received on the previous meeting was addressed in this Sprint.

## 12-17. Links to the Documentation

- [docs/roadmap.md](../../docs/roadmap.md)
- [docs/definition-of-done.md](../../docs/definition-of-done.md)
- [docs/quality-requirements.md](../../docs/quality-requirements.md)
- [docs/quality-requirement-tests.md](../../docs/quality-requirement-tests.md)
- [docs/testing.md](../../docs/testing.md)
- [docs/user-acceptance-tests.md](../../docs/user-acceptance-tests.md)

## 18. Quality Model  

| Quality requirement ID | Name | ISO/IEC 25010 sub-characteristic | Description |
|---|---|---|---|
| QR-001 | Recognition Response Time | Performance efficiency - time behaviour | Recognition pipeline must produce an access decision within 3.0 seconds |
| QR-002 | Resistance to Static Photo Spoofing | Security - authenticity | System must reject at least 9 out of 10 static photo spoofing attempts |
| QR-003 | Recognition Model Modularity | Maintainability - modularity | Recognition model must be replaceable without changing the application pipeline |

## 19. Testing Status

All 28 tests pass. Overall line coverage across the `faceguard` package is **41%**, above the 30% target.

| Module | Stmts | Miss | Cover | Status |
|---|---|---|---|---|
| backend/faceguard/business_logic.py | 18 | 6 | 67% | Above threshold |
| backend/faceguard/detect.py | 46 | 7 | 85% | Above threshold |
| backend/faceguard/recognize.py | 123 | 63 | 49% | Above threshold |
| backend/faceguard/interfaces.py | 6 | 1 | 83% | Above threshold |
| backend/faceguard/enroll.py | 37 | 37 | 0% | Not covered |
| backend/faceguard/main.py | 51 | 51 | 0% | Not covered |
| backend/faceguard/dataset.py | 3 | 3 | 0% | Not covered |
| **TOTAL** | **284** | **168** | **41%** | Above threshold |

**Critical modules**: `business_logic.py`, `detect.py`, and `recognize.py` are identified as critical modules and all exceed the 30% coverage threshold. `enroll.py`, `main.py`, and `dataset.py` have 0% coverage. `main.py` is the Streamlit UI entry point which is not unit-testable directly.

## 20-22. Test Links

- [Unit tests](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/tree/main/tests/unit)
- [Integration tests](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/tree/main/tests/integration)
- [Automated quality requirement tests](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/tree/main/tests/quality)

## 23-25. CI Pipeline

- [CI pipeline](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/actions)
- [Latest protected-default-branch CI run](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/actions/runs/28308225264)
- ![Branch protection](images/branch_protection.png)

## 26. QA Check Screenshots

| Check | Screenshot |
|---|---|
| Linting | ![Linting](images/linting.png) |
| Coverage report | ![Coverage](images/coverage.png) |
| Test report | ![Tests](images/tests.png) |
| Additional QA check | ![QA check](images/qa_check.png) |

## 27. Short explanation of how the Assignment 4 tests, CI checks, quality requirement tests, and Definition of Done will continue to govern later project work.   

The Assignment 4 tests, CI checks, quality requirement tests, and Definition of Done defined are maintained actively and apply to all later project work. All later PBIs must pass the same CI checks, keep automated tests passing, maintain critical module coverage at or above 30%, and satisfy the updated Definition of Done before being marked Done.

## 28. SemVer release 
[Release 2.0.0 - MVP v2](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v2.0.0)

## 29. Changelog
[CHANGELOG.md](../../CHANGELOG.md)

## 30. Demo Video
[MVP v2 demo video](https://drive.google.com/file/d/1WeqOz5-CdQawEzLJqm_BUHD-Plo9eSof/view?usp=drive_link)

## 31. Presentation
[Presentation](https://drive.google.com/file/d/1rYBW_qT74htfvdqdye2SOPuVrmqIiQJ8/view?usp=drive_link)

## 32. UAT Results Summary
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

## 33. Customer Review Transcript

The public publication was permitted.  
[Customer Review Transcript.md](customer-review-transcript.md)

## 34-37. Links. Customer Review Transcript

- [customer-review-summary.md](customer-review-summary.md)
- [reflection.md](reflection.md)
- [retrospective.md](retrospective.md)
- [llm-report.md](llm-report.md)

## 38. Current Product Status

- MVP v2 release is available as release `v2.0.0`.
- The system runs on Raspberry Pi 5 with a connected web-camera.
- Face recognition uses a lightweight model.
- Face recognition processes video frames instead of a single photo.
- Liveness detection is implemented to prevent spoofing via photos or videos.
- Automatic recognition works without a button press on the Recognition page.
- Temporary registration uses start and expiration date pickers.
- CI pipeline is configured with automated tests, coverage reporting, linting, formatting, and Bandit security check.
- All 28 tests pass with 41% overall coverage across the `faceguard` package.
- All seven UAT scenarios passed during the Sprint Review session with the customer.

## 39. Next Steps

1. Add LED indicators for access grant and deny feedback on the hardware side.
2. Improve recognition accuracy with accessories such as glasses and masks.
3. Integrate a smart lock controlled by the recognition result.
4. Add failure notifications for unrecognized attempts or system errors.
5. Add duplicate name check when registering a new employee - [#115](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115)
6. Change temporary access to use exact time in addition to date - [#117](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117)
7. Add ability to edit employee name and status after registration - [#113](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113)
8. Add time of employee's last entry to the employees list - [#114](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114)
9. Add filtering by date range in access logs - [#116](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116)

## 40. Contribution Traceability

| Team member | GitHub username | Issues | PRs/MRs | Review activity | Contribution |
|---|---|---|---|---|---|
| Sofia Sokolova | @s0ftach | [#57](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/57), [#128](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/128) | [#89](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/89), [#97](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/97), [#101](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/101), [#103](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/103), [#112](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/112), [#119](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/119), [#120](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/120), [#121](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/121), [#122](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/122), [#123](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/123), [#124](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/124), [#129](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/129), [#130](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/130), [#131](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/131) | [#98](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/98), [#99](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/99), [#102](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/102), [#108](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/108), [#118](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/118) | Backend, Testing, Documentation, Presentation |
| Varvara Orekhova | @oebarbie | [#46](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/46) | [#89](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/89), [#108](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/108), [#110](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/110) | [#98](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/98), [#103](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/103), [#119](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/119), [#120](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/120), [#122](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/122), [#123](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/123), [#124](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/124), [#125](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/125), [#129](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/129), [#130](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/130), [#131](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/131) | Backend, Documentation, H/W setup |
| Maksim Barannikov | @Exckernels | [#93](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/93), [#94](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/94), [#96](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/96), [#100](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/100), [#104](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/104), [#106](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/106) | [#90](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/90), [#92](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/92), [#99](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/99), [#107](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/107) | [#110](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/110) | Backend, Testing, Documentation, H/W setup |
| Maksim Beketov | @ixkci | [#49](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/49), [#58](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/58), [#59](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/59), [#86](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/86), [#87](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/87), [#96](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/96) | [#98](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/98), [#102](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/102) | [#90](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/90), [#92](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/92), [#97](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/97), [#101](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/101) | Backend, Testing, H/W setup |
| Alexander Bondarenko | @grex861 | [#126](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/126) | [#118](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/118) | [#107](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/107) | Documentation |
| Pavel Dudinov | @tyajhelo | [#127](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/127), | [#125](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/125) | [#112](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/112), [#121](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/pull/121) | Documentation |

## 41. Screenshots
Screenshots are stored in:

```text
reports/week4/images/
```
![Sprint milestone](images/sprint_milestone.png)
![Latest CI run](images/ci_run.png)
![Branch protection](images/branch_protection.png)
![Coverage](images/coverage.png)
![QA check](images/qa_check.png)
![Release](images/release.png)
![PR example](images/pr_example.png)

## 42. Additional Screenshots
![Product Backlog](images/product_backlog.png)
Direct link: [Product Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/5)
![Sprint Backlog](images/sprint_backlog.png)
Direct link: [Sprint Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/6)
![Recognition page](images/recognition.png)
![Add Employee page](images/add_employee.png)
