# AI Agent Guidance

This document outlines the rules and context for AI coding assistants and agents operating within the FaceGuardV3 repository.

## System Context
- **Product:** FaceGuardV3 is a decoupled face recognition access control system designed to run on a Raspberry Pi 5 at the edge.
- **Architecture:** 
  - **Frontend:** React SPA (runs in `docker-frontend`)
  - **Backend:** FastAPI with WebSockets for real-time video streaming (runs in `docker-backend`)
  - **Database:** PostgreSQL (runs in `docker-db-1`)
  - **Hardware:** Integrates with Raspberry Pi GPIO (LEDs/Motor) via asynchronous tasks.

## Rules for Agents

1. **Secrets Management:** 
   - Never commit sensitive information (passwords, tokens, database credentials).
   - Use `backend/.env.example` as a reference for environment variables. Do not modify `.gitignore` to track `.env` files.

2. **Architectural Constraints:**
   - Refer to `docs/architecture/README.md` and `docs/architecture/adr/` before making structural changes. 
   - The frontend and backend must remain strictly decoupled.
   - Hardware GPIO operations must be asynchronous to prevent blocking the FastAPI event loop (ADR-007).

3. **Development Workflow:**
   - Always run the test suite (`pytest tests/`) after modifying backend logic.
   - Run formatting (`black`) and linting (`flake8`) before finalizing your changes.
   - Do not bypass the `FaceRecognitionProvider` abstraction when modifying recognition logic (ADR-001).

4. **Quality Gates:**
   - Verify that your changes do not violate existing Quality Requirements (`docs/quality-requirements.md`).
   - If adding a new substantial feature, ensure corresponding tests are written or updated in `tests/quality/` or `tests/unit/`.

5. **Tool Usage:**
   - Use standard Docker commands (`docker compose up --build`) to verify the environment.
   - Do not make changes to `.streamlit/` files, as the project has migrated away from Streamlit.
