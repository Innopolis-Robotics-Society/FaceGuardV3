# Contributing to FaceGuardV3
FaceGuardV3 uses issue-linked pull requests and mandatory behavior, quality, security, deployment, and documentation gates. Read the [architecture](architecture/README.md), [Definition of Done](definition-of-done.md), and affected QR/QRT before changing a critical path.
## Workflow
1. Start from a refined, assigned issue with acceptance criteria and create `<issue-number>-<short-description>` from current `main`.
2. Keep changes scoped. Do not commit `.env`, credentials, real employee data, biometric samples, generated model data, or coverage output.
3. Add tests for the behavior/risk being changed. Do not add mock-call-only tests, trivial construction tests, sleeps for timing assertions, or tests that merely inflate coverage.
4. Update code, architecture views/ADR where applicable, `.env.example`, operational docs, QRT status/evidence, and `CHANGELOG.md` as required by the DoD.
5. Open an issue-linked PR (`Closes #...`), record exact commands/results and hardware limitations, obtain another participant's approval, and merge only after required CI checks pass.
## Configuration and local stack
```bash
cp backend/.env.example backend/.env
python3 backend/scripts/generate_hash.py
openssl rand -hex 32
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml up --build -d --wait
```
Use the base file plus `docker/docker-compose.pi.yml` only for Raspberry Pi backend-camera/GPIO deployment. See the root [README](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/main/README.md) before mapping `/dev/videoN` or `/dev/gpiochipN`. Frontend `VITE_*` settings are compiled at build time.
## Backend verification
Use Python 3.10/3.11:
```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r backend/requirements.txt
PYTHONPATH=backend:. .venv/bin/pytest tests/unit -q
PYTHONPATH=backend:. .venv/bin/pytest tests/integration -q
PYTHONPATH=backend:. .venv/bin/pytest tests/quality -q
.venv/bin/black --check backend tests scripts/check_critical_coverage.py
.venv/bin/flake8 backend tests scripts/check_critical_coverage.py \
  --max-line-length=120
.venv/bin/bandit -q -r backend
```
QRT-005 and complete coverage require the isolated `faceguard_test` PostgreSQL service. Use the exact commands in [Testing and QA](testing.md); never point QRT-005 at a development or customer database. CI uploads JSON/XML coverage and enforces at least 30% for every documented critical module.
## Frontend verification
```bash
cd frontend
npm ci
npm test
npm run lint
npm run build
npm audit --audit-level=high
```
Frontend tests should cover observable UI/network/camera behavior. Browser/backend camera mode and bbox/frame correlation are security/latency-sensitive boundaries, not implementation details to bypass.
## Configuration and documentation verification
```bash
BACKEND_ENV_FILE=../backend/.env.example docker compose \
  --env-file backend/.env.example -f docker/docker-compose.yml config --quiet
BACKEND_ENV_FILE=../backend/.env.example docker compose \
  --env-file backend/.env.example -f docker/docker-compose.yml \
  -f docker/docker-compose.pi.yml config --quiet
mkdocs build --strict --site-dir /tmp/faceguardv3-site
```
Lychee runs separately on every PR. Do not mark a physical-camera, liveness-attack, or LED-latency requirement Implemented based on fakes; preserve the limitation and plan/attach hardware evidence.
