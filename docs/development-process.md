# Development Process and Configuration Management

This document outlines the actual development process, Git workflow, and configuration management practices used by the FaceGuardV3 team.

## 1. Task Management and Issue Tracking

We use **GitHub Projects** and **GitHub Milestones** to manage our workflows:
- **Product Backlog:** Managed in a dedicated GitHub Project (e.g., `FaceGuardV3-Product-Backlog`).
- **Sprint Backlog:** Managed in separate, sprint-specific GitHub Projects (e.g., `FaceGuardV3-Sprint-3-Backlog`).
- **Sprint Container:** We use GitHub Milestones (e.g., `Sprint 3`) to track sprint dates, store the Sprint Goal, and containerize the selected issues.

### Issue Types & Templates
**No product work is started without first creating a tracked Issue.** Issues are created and used as the primary source of truth for all tasks, utilizing predefined templates located in `.github/ISSUE_TEMPLATE/`:
- **User Story:** Defines the user role, desired action, expected value, and acceptance criteria.
- **Bug Report:** Captures problem description, reproduction steps, expected/actual behavior, and environment.
- **Other PBI:** For technical or infrastructure work.
- **Course Task:** For assignments and reporting (does not count toward product scope).

### Board Statuses (Work Status)
The team uses the following board statuses (columns) and explicit **entry criteria** for moving work into each state:
- **To Do:** (Entry criteria: The Product Backlog Item (PBI) is refined and prioritized, but not yet selected for the current Sprint.)
- **Ready:** (Entry criteria: The PBI is selected for the current Sprint, assigned, estimated, has clear acceptance criteria, and can be started without major unanswered questions.)
- **In Progress:** (Entry criteria: A developer is actively assigned and a feature branch has been created to start the work.)
- **Review:** (Entry criteria: The implementation is complete, and the associated Pull Request (PR) has been opened and linked to the issue.)
- **Done:** (Entry criteria: The PR is approved and merged into the protected default branch, all acceptance criteria are met, and the Definition of Done (DoD) is satisfied.)

## 2. Git and Review Workflow

The team follows a trunk-based workflow adapted for GitHub Pull Requests.

### GitGraph Diagram

```mermaid
gitGraph
    commit id: "Initial Setup"
    branch "42-add-login-form"
    checkout "42-add-login-form"
    commit id: "Add login UI"
    commit id: "Integrate with DB"
    checkout main
    commit id: "Update README (by teammate)"
    checkout "42-add-login-form"
    commit id: "Fix PR review comments" type: HIGHLIGHT
    checkout main
    merge "42-add-login-form" tag: "v0.2.0"
```

**What the diagram shows:**
The diagram illustrates our standard workflow in a collaborative environment. While a developer works on a feature branch (e.g., `42-add-login-form`), other teammates might push changes to `main`. Once the initial feature work is pushed and a Pull Request is opened, the review process begins. The developer pushes additional commits (highlighted) to address PR review feedback. Finally, after approval and passing CI, the branch is merged into `main` using a merge commit.

### Workflow Rules
1. **Branch Creation & Naming:** Branches are created from the issue page where possible. The naming convention is `<issue-number>-<short-description>` (e.g., `42-add-login-form`).
2. **Pull Requests:** All changes are submitted via PRs. A PR template (`.github/pull_request_template.md`) prompts the author for a summary, testing performed, and a reviewer checklist.
3. **Review Process:** 
   - Direct pushes to `main` are disabled.
   - PR authors cannot approve their own changes.
   - At least **one approval** from a different team member is required before merging.
4. **Merging:** Changes are merged using **Merge Commits** (Squash and Rebase are disabled).
5. **Issue Resolution:** Issues are linked to the PR and are automatically closed when the PR is merged, provided all acceptance criteria and the DoD are satisfied.

## 3. Configuration and Secrets Management

We prioritize security and portability by keeping sensitive data out of version control.

- **Secret Storage & Runtime Configuration:** All runtime secrets and environment variables are stored securely in `backend/.env`. During runtime, this configuration is supplied to the backend container natively through the `env_file` directive in `docker-compose.yml`.
- **Ignored Files:** Our `.gitignore` strictly ignores sensitive and environment-specific files, including `backend/.env`, `.coverage`, and large binaries/models (unless Git LFS is used).
- **Sanitized Examples:** To onboard new developers, we commit a sanitized example file: `backend/.env.example`. Developers copy this file to `backend/.env` and fill in the actual local credentials.
- **CI Configuration:** When CI pipelines need access to secrets (e.g., for integration testing), they are securely supplied via **GitHub Actions Repository Secrets**, never hardcoded in the YAML files.
- **Deployment Configuration:** For edge deployment (e.g., on the Raspberry Pi), deployment configuration is handled manually by an administrator who securely sets up the `.env` file on the production device. CI does not deploy secrets directly to the edge.

## 4. Reproducible Development Environment

To eliminate "it works on my machine" issues, especially given our dependencies on native machine learning libraries (OpenCV, InsightFace), we use a containerized setup.

- **Docker & Docker Compose:** The product is defined in `docker/docker-compose.yml`. Developers simply run `docker compose up --build` (or the equivalent target in a Makefile/run script) to launch the application. This ensures that the Node.js (React) and Python (FastAPI) environments, system libraries, and configurations are identical across all developer machines.

## 5. Continuous Integration (CI) Process

Our repository relies on GitHub Actions for Continuous Integration. The CI pipeline runs automatically on all PRs and pushes to the `main` branch.

- **Quality Gates & Testing:** The `ci.yml` workflow enforces code quality and behavior by running:
  - Formatting checks (Black) and source-code linting (Flake8).
  - Automated tests (Unit and Integration) covering critical logic.
  - Automated Quality Requirement Tests (QRT).
  - Line coverage reporting with a strict gate (e.g., `--cov-fail-under=30` for critical modules).
  - **Additional QA Check:** A security vulnerability scan using **Bandit**.
- **Link Checking:** The `lychee.yml` workflow checks all Markdown files across the repository to ensure no broken links are committed.
- **Deployment Automation:** Currently, we rely on CI for testing and validation (Continuous Integration). Automated deployment (Continuous Delivery) is handled manually or via external scripts after a SemVer release tag is pushed.
