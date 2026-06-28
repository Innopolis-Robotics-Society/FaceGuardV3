# Customer Review Summary: MVP v2 increment

## Meeting details

During the meeting, the video and audio were recorded. Due to unexpected problems, the audio recording was lost. But the transcript was prepared from notes and reflects the full discussion. So, the video without sound will be attached as a Meeting Recording.

**Date**: 27.06.2026  
**Participants**:  
| name | username | role |
| --- | --- | --- |
| Maksim Beketov | ixkci | interviewer |
| Sofia Sokolova | s0ftach | recorder |
| Varvara Orekhova | oebarbie | observer |
| Maksim Barannikov | Exckernels | note taker |
| Alexander Bondarenko | grex861 | note taker|
| Artyom Tuzov | artyomzifir | customer |

**Format:** Online. UAT was conducted during this online Sprint Review session. Because of the remote format, the customer was not able to perform the UAT, so the team demonstrated each UAT scenario to the customer and confirmed acceptance.

## Sprint Goal
**Sprint Goal** is to improve recognition speed and reliability by switching to a lightweight model, enabling video-based face enrollment, adding liveness detection, and deploying to Raspberry Pi 5. The **Sprint Goal** was presented and confirmed as achieved by the customer.

## Delivered Increment
The following changes were demonstrated and approved by the customer:

- Switched to a lightweight face recognition model for improved performance
- Temporary registration now uses start and expiration date pickers
- Deployed to Raspberry Pi 5 with web-camera connection
- Liveness detection added to prevent spoofing via photos
- Camera selector added on Recognition and Add Employee pages
- Switched from single photo capture to video frame extraction
- Recognition session now starts with a dedicated Start button

## UAT results
Because of the remote format, the customer was not able to make the UAT, so the team demonstrated each UAT scenario to the customer, who observed, provided feedback, and confirmed acceptance. All 7 UAT scenarios passed. No failures were recorded.

| UAT scenario ID | Scenario | Result |
|---|---|---|
| UAT-001 | Register a new employee with permanent access | Passed |
| UAT-002 | Add a new employee with temporary access | Passed |
| UAT-003 | Remove a registered employee | Passed |
| UAT-004 | View the list of all registered employees | Passed |
| UAT-005 | View the access logs | Passed |
| UAT-006 | Automatic recognition of a registered employee | Passed |
| UAT-007 | Rejection of an unregistered person | Passed |

## Quality Evidence
The team presented the CI pipeline with automated tests, coverage reporting, linting, formatting checks, and Bandit security scan. All 28 tests passed with 41% overall coverage across the `faceguard` package. Liveness detection and the lightweight model were demonstrated live. The customer was satisfied with the quality improvements made this Sprint.

## Customer's Feedback: Approvals & Requested changes
The customer approved the MVP v2 increment. The following changes were requested for the next Sprint:

- [#113](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113) - Add ability to edit employee name and status after registration 
- [#114](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114) - Add time of employee's last entry to the employees list
- [#115](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115) - Add a duplicate name check when registering a new employee
- [#116](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116) - Add filtering by date range in access logs 
- [#117](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117) - Change temporary access to use exact time in addition to date
  
## Risks & Gaps
- Raspberry Pi 5 performance is limited to approximately 1 FPS due to hardware constraints. Higher frame rates cause the system to freeze and fail to recognize faces. The team will continue testing to find the maximum sustainable FPS within a 3–5 second response target.
- Additional lighting may be needed at the camera installation point in the laboratory to maintain recognition quality.
- LED indicator and motor integration for access grant/deny signaling have been started and are planned for the next Sprints.

## Action Points
- Test LED indicators in the laboratory
- Find the upper bound FPS that keeps recognition within 3–5 seconds on Raspberry Pi 5
- Address Customer's feedback from this session

## Resulting Product Backlog Changes

New PBIs were added based on customer feedback: [#113](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113), [#114](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114), [#115](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115), [#116](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116), [#117](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117).  
Full Product Backlog: [Product Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/5)

