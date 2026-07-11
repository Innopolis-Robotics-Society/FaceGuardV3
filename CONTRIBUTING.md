# Contributing to FaceGuardV3

Welcome, and thank you for your interest in contributing to FaceGuardV3! 
FaceGuardV3 is a secure, decoupled face recognition access control system deployed on edge hardware. We strictly adhere to a disciplined, issue-driven workflow to maintain the quality and reliability of the access control system.

## 1. Issue-Linked Workflow

**No product work is started without an issue.** 
All changes must trace back to a specific GitHub Issue.

1. **Find or Create an Issue:** Check the [Issues](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues) tab. If you find a bug or want to propose a feature, create an issue using one of the provided templates (`User Story`, `Bug Report`, or `Other PBI`).
2. **Assignment and Estimation:** Wait for the issue to be prioritized in the Sprint Backlog. An issue must be moved to the **Ready** column with an assigned owner and Story Points before work begins.
3. **Branching:** Create a branch for your issue. Use the naming convention: `<issue-number>-<short-description>` (e.g., `42-add-login-form`).

## 2. Pull Request (PR) Process

We use a trunk-based workflow adapted for GitHub Pull Requests. Direct pushes to `main` are disabled.

1. **Commit Often:** Make small, logical commits. Use meaningful commit messages.
2. **Open a Pull Request:** Once your work is ready, open a PR against the `main` branch. 
3. **Link the Issue:** Ensure your PR description links to the original issue (e.g., `Closes #42`). Use the provided PR template to document your changes and testing steps.
4. **Pass CI Quality Gates:** All PRs must pass the automated CI pipeline. This includes:
   - Formatting (`black`) and Linting (`flake8`)
   - Unit and Integration tests (`pytest`)
   - Quality Requirement Tests (QRT)
   - Minimum test coverage thresholds
   - Security vulnerability scans (`bandit`)
5. **Code Review:** Your PR requires at least **one approval** from a different team member.
6. **Merge:** Once approved and passing CI, the PR will be merged using a **Merge Commit** (Squash and Rebase are disabled to preserve exact commit history).

## 3. Configuration and Secrets

- **Never commit secrets:** Passwords, API keys, and environment-specific configs must never be committed.
- **Environment Variables:** Use `backend/.env`. A sanitized example is provided at `backend/.env.example`.
- If you add a new environment variable, make sure to add a placeholder for it in `backend/.env.example`.

## 4. Setting Up Your Development Environment

FaceGuardV3 relies on Docker to ensure a reproducible environment across all machines.

1. Copy the example environment variables:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Build and run the containers:
   ```bash
   docker compose -f docker/docker-compose.yml up --build
   ```
3. The frontend is available at `http://localhost:3000` and the backend API docs at `http://localhost:8000/docs`.

For detailed architecture and internal logic explanations, please refer to the [Architecture Documentation](docs/architecture/README.md) and [Development Process](docs/development-process.md).
