# Week 3 Sprint Retrospective

## What went well

1. The team delivered visible progress on the MVP v1 face recognition workflow. The implemented increment included employee-related pages, employee registration, basic log storage, face comparison logic, and a temporary recognition test interface using a built-in webcam.

2. The team improved the repository workflow during Week 3. Issue-linked pull requests, approvals, meaningful review comments, Definition of Done, roadmap updates, changelog workflow, and the extended pull request template made the development process more structured and easier to verify.

3. The team clarified the technical direction of the recognition pipeline. Work on OpenCV, InsightFace, embeddings, Dockerization, and the test page helped separate dependency setup, recognition logic, deployment, and verification into more understandable backlog items.

## What did not go well

1. Some workflow requirements were clarified late. Branch naming, issue-linking, pull request descriptions, review comments, approval rules, and changelog checklist usage had to be corrected after part of the work had already started.

2. Evidence collection was not organized from the beginning. Pull request links, approvals, review comments, issue status updates, screenshots, changelog decisions, and verification notes had to be checked and collected after implementation instead of being recorded continuously.

3. The recognition pipeline still has technical risks and unfinished improvements. The customer pointed out that model confidence must not be confused with overall system success rate, that the system should use 5–10 frames with an averaged embedding, and that face cropping and lighter model testing are still needed.

## Action points

1. In the next Sprint, the team should create or confirm the GitHub issue first, then create the branch using the required `<issue-number>-short-description` format, assign a reviewer, define acceptance criteria, and only then start implementation.

2. The team should maintain a shared evidence and technical follow-up checklist during the Sprint. It should track issue links, pull request links, review comments, approvals, screenshots, changelog decisions, Docker/run verification, release links, final Work Status updates, and the customer’s requested technical changes such as 5–10 frame averaging, OpenCV face cropping, temporary access time fields, and lighter model testing.
