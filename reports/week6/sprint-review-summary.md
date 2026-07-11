# Customer Review Summary: MVP v3 increment (Sprint 5) / Week 7

## Meeting details
During the meeting, the video was recorded. Before recording started, the team requested permission to record the meeting and to publish a sanitized English transcript in the public repository. The customer agreed to both. Final UAT and transition discussion included.
**Date**: 18.07.2026
**Participants**:
| GitHub username | role |
| --- | --- |
| ixkci | interviewer |
| s0ftach | recorder |
| oebarbie | observer |
| Exckernels | note taker |
**Format:** Online.

## Sprint Goal
**Sprint Goal** was to deliver final MVP v3 with full handover readiness, resolve remaining performance and stability issues, complete documentation, and ensure operational usefulness. The **Sprint Goal** was achieved.

## Delivered Increment
The following changes were demonstrated and approved by the customer:
- Recognition runs efficiently in the background without blocking the UI (WebSocket-based real-time streaming)
- Decoupled React frontend and FastAPI backend
- Sped up system response time by eliminating previous bottlenecks
- Connection of the system to the door
- Recognition with accessories support
- Improved local database setup for enhanced offline reliability
- Stabilized Docker build process and image sizes
- LEDs integration stabilized
- Edit employee name/status, last entry time, duplicate prevention, date-range filtering, and temporary access improvements (from prior increments)
- Extensive customer handover documentation and contributor guides

## UAT results
All UAT scenarios (including previous + new final ones) were executed and passed. No failures recorded. Full details: `docs/user-acceptance-tests.md`.

## Quality Evidence
CI gates (linting, formatting, Bandit, automated tests) remained active and passing. Detailed evidence in `docs/testing.md`.

## Architecture Evidence Discussed
WebSocket decoupling, background processing, and overall architecture reviewed positively.

## Customer's Feedback: Approvals & Requested changes
The customer fully approved the MVP v3 increment and the final product. No major new changes requested.

## Risks & Gaps
- Raspberry Pi 5 performance remains a potential bottleneck in high-load scenarios (hardware upgrade recommended if needed).
- Post-course team support ends; customer responsible for ongoing maintenance.

## Action Points
- Customer to proceed with deployment on target hardware.
- Monitor real-world performance and provide feedback if needed.
- Archive project artifacts.

## Resulting Product Backlog Changes
All major PBIs closed (including #196, #197, #213, #215 and performance-related items). Remaining risks documented for the customer. Full Product Backlog: [link to board].
