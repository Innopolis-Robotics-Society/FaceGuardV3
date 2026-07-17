# Sprint Retrospective — Sprint 5
## What went well
System response time improved by 40% via caching and query optimization; customer confirmed it meets baseline requirements.
CI failures dropped to zero after implementing pre-commit hooks, saving 3–4 hours of debugging time.
Performance work was front-loaded with a buffer, allowing the team to absorb an unexpected hardware issue without delays.
Final integration and end-to-end testing succeeded; all acceptance criteria were met in the Sprint Review demo.
## What did not go well
Integration and end-to-end tests were written too late, leaving little time for regression testing; one edge-case bug appeared during demo but was fixed quickly.
Documentation formatting remained inconsistent across sections, complicating setup for new readers.
Final polish was rushed, causing minor UI glitchesvisible in the demo.
Deployment instructions were not tested on a clean environment, leading to confusion about environment variables during handover.
## What the team changed or attempted to change based on the previous Sprint Retrospective, and what results they observed
Pre-commit hook for formatting (Sprint 3 action): fully adopted; CI formatting failures dropped from 3–4 per sprint to zero, speeding up PR reviews.
Front-loaded performance optimization with buffer (Sprint 3
 action): implemented from day 2; the buffer handled both planned work and an unexpected hardware issue without delaying delivery. Customer praised the improved response time.
## Action points
Test deployment on a clean Raspberry Pi using only the documentation, then fix any gaps to ensure reproducible handover instructions