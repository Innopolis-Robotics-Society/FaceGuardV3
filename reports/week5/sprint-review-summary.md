# Customer Review Summary: MVP v2 increment (Sprint 3)

## Meeting details

During the meeting, the video was recorded. Before recording started, the team requested permission to record the meeting and to publish a sanitized English transcript in the public repository. The customer agreed to both. UAT was conducted during this same online session.

**Date**: 04.07.2026  
**Participants**:  
| GitHub username | role |
| --- | --- |
| ixkci | interviewer |
| s0ftach | recorder |
| oebarbie | observer |
| Exckernels | note taker |

**Format:** Ofline.

## Sprint Goal

**Sprint Goal** was to improve system visibility through status LED indicators, add a duplicate registration check, and address customer-requested improvements from the previous Sprint Review (27.06.2026). The **Sprint Goal** was presented and confirmed as achieved by the customer, with performance still flagged as an open concern.

## Delivered Increment

The following changes were demonstrated and approved by the customer:

- LED status indicators added: blue (access granted), red (access denied / spoof detected), yellow (face detected but poor quality / registration in progress); all three colors light up together during registration
- Duplicate registration prevention: a face cannot be registered repeatedly
- Temporary access registration now includes exact time in addition to date
- Access log deduplication: repeating logs from the same recognition session are no longer registered
- Employee's last entry/last capture time added to the employee list
- Filtering of access logs by date range
- Ability to edit an employee's name and status after registration
- Test section removed from the recognition page

## UAT results

8 active UAT scenarios were executed and passed during this session, including the two new MVP v2 scenarios (UAT-008: Edit the name or status of an employee; UAT-009: Register an already registered employee). No failures were recorded. Full detail: `docs/user-acceptance-tests.md`.

## Quality Evidence

CI gates (linting, formatting, Bandit, automated unit/integration/QRT tests) remained active and passing throughout the sprint. Quality metrics were not walked through in detail with the customer during this session; detailed evidence is maintained in `docs/testing.md`.

## Architecture Evidence Discussed

Architecture documentation and ADRs were not a discussion focus with the customer in this session; the demo centered on user-facing behavior (LEDs, registration flow, logs). Architecture and ADR work (ADR-001 through ADR-004) is tracked and reviewed internally in `docs/architecture/`.

## Customer's Feedback: Approvals & Requested changes

The customer approved the MVP v2 increment. The following concerns and changes were raised for the next Sprint:

- Recognition and overall website response time remains too slow; the customer classified this as a **Must have** priority for Sprint 4 — [#171](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/171)
- Recognition should run in the background instead of requiring the admin to stay on the page, including an asynchronous camera-start mode — [#172](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/172)
- The customer suggested investigating memory usage and repeated embedding copying as a possible cause of the performance issues, as a lead for the team's own investigation rather than a separate backlog item

## Risks & Gaps

- Raspberry Pi 5 performance remains a bottleneck; the customer observed a much faster response on a laptop demo and suggested the board itself, plus running two models simultaneously, may be the limiting factor
- LED indicators work but are not fully reliable yet; connecting peripherals to the Raspberry Pi as external devices sometimes requires separate elevated (sudo) access, adding operational overhead
- Access-denied response time is also slow and needs further optimization
- The customer offered to provide better hardware to test for a possible performance gain if the team determines the current board is the limiting factor

## Action Points

- Prioritize recognition and website response-time optimization for Sprint 4 (Must have)
- Investigate background/asynchronous recognition mode (camera stays active without blocking navigation)
- Investigate memory usage and embedding-copy overhead as a possible performance cause
- Continue stabilizing LED behavior and Raspberry Pi peripheral access permissions
- Evaluate whether alternate/upgraded hardware is needed if software-side optimization is insufficient

## Resulting Product Backlog Changes

New PBIs were added based on customer feedback from this session: [#171](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/171), [#172](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/172).  
All Sprint 3 PBIs from the previous review (#113–#117, #60, #152) were completed and are visible as Done on the Product Backlog board.  
Full Product Backlog: [Product Backlog board](https://github.com/orgs/Innopolis-Robotics-Society/projects/5)
