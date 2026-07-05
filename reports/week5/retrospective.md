# Sprint Retrospective — Sprint 3 (MVP v2)

## What went well

- **Daily Scrum attendance improved:** unlike Sprint 2, attendance was stable throughout the sprint, keeping the team aligned on progress.
- **Hardware integration:** successfully connected and integrated the LED indicators with the hardware backend, the team's first real hardware-facing milestone.
- **Successful Sprint Review demo:** the MVP v2 increment was demonstrated successfully, and all planned functionality met the customer's acceptance criteria.
- **Consistent code review practice:** code reviews and baseline quality checks (linting, formatting, Bandit) remained consistent throughout the sprint and did not become a bottleneck.

## What did not go well

- **Performance bottlenecks persisted:** system response time is still high on target hardware (Raspberry Pi 5); optimization goals were not fully achieved, and the customer raised this again at the Sprint Review.
- **CI pipeline friction:** formatting and linting checks (Black, Flake8) failed in CI multiple times during the sprint because local environments were not consistently checked before pushing, creating avoidable delays.
- **Task underestimation continued:** several tasks, especially around integration and optimization, took noticeably longer than estimated during planning.
- **Schedule disruption:** a critical technical issue forced the team to postpone a key meeting by a full day, which cascaded into shifted internal deadlines and delayed final delivery.

## What the team changed based on the previous Sprint Retrospective, and what results they observed

- **Daily Scrum attendance:** the team fully followed through on this action point; attendance was consistent and communication improved as a result.
- **Splitting large/uncertain tasks into smaller pieces:** attempted, but only partially successful. Some tasks (particularly performance optimization and hardware integration) were still underestimated despite being broken down.
- **Starting riskier work earlier (e.g. performance optimization):** this did not fully take hold. Optimization work was again pushed later in the sprint, and the same performance risk flagged in the Sprint 2 retrospective resurfaced as new customer feedback in the Sprint 3 review.

## Action points

1. **Fix local/CI formatting parity:** ensure Black and Flake8 run locally (e.g. via a pre-commit hook) before pushing, so formatting issues are caught before CI instead of blocking PRs after the fact.
2. **Front-load performance optimization with a time buffer:** dedicate focused effort on system response time at the start of the next sprint, and add a planning buffer for volatile tasks (optimization, hardware integration) so a single technical blocker does not cascade into delivery delays.
