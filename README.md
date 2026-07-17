# FaceGuardV3

FaceGuardV3 is a local face-recognition access indicator for a laboratory. A React SPA talks to a FastAPI backend over authenticated REST and WebSocket interfaces; InsightFace and MiniFASNet perform recognition and liveness checks; PostgreSQL stores employees and access logs; and three Raspberry Pi GPIO LEDs provide feedback. The repository does not implement a physical door actuator.

## Current behavior

- Recognition and enrollment are mutually exclusive and use one frame-processing operation at a time.
- `browser` camera mode captures in the browser and allows at most one JPEG to be awaiting a backend response.
- `backend` camera mode owns one OpenCV `VideoCapture` loop and retains only the latest frame; it is intended for a V4L2 device attached to the Raspberry Pi.
- This single-owner guarantee applies to the deployed FastAPI runtime. Legacy maintenance CLIs in `backend/faceguard/` open OpenCV directly; stop the service before using one against the same camera.
- WebSockets authenticate with the `faceguard.jwt` and `bearer.<JWT>` subprotocols. JWTs are not put in query strings.
- Every response carries the bounding box, processed-frame dimensions, and sequence; the UI overlays the box on the exact JPEG associated with the response.
- Enrollment uses liveness-accepted embeddings. Duplicate detection runs before insert, under a PostgreSQL transaction advisory lock, and returns HTTP `409` without changing the existing employee.
- Temporary access uses inclusive timestamp bounds. Schema creation and the legacy `DATE` to `TIMESTAMP` migration run automatically at backend startup.
- GPIO uses BCM 17 (yellow), 27 (blue), and 22 (red) on the configured `GPIO_CHIP`. Feedback workers are generation-safe and camera, GPIO, background tasks, and the database pool are cleaned up during normal shutdown.

## Requirements

- Docker Engine with a recent Docker Compose v2 implementation. The Raspberry Pi override uses the Compose `!reset` tag.
- For host-side development: Python 3.10 or 3.11 and Node.js 22.
- For edge deployment: Raspberry Pi 5 with a 64-bit OS, a V4L2-visible USB webcam (or a camera deliberately exposed as a V4L2 device), and optional LEDs wired through suitable resistors.
- Enough local storage for the PostgreSQL volume and InsightFace models. On first initialization, the backend downloads a missing `buffalo_s` archive with bounded retries, validates the ZIP and required ONNX files, and populates the persistent `docker/insightface_models` cache. Later starts are local while that cache remains intact.

## Configuration

Create the private backend environment file:

```bash
cp backend/.env.example backend/.env
```

Generate a bcrypt admin password hash (the script requires Python `bcrypt`):

```bash
python3 backend/scripts/generate_hash.py
```

Generate an independent JWT signing secret:

```bash
openssl rand -hex 32
```

Put the generated values and local PostgreSQL credentials in `backend/.env`. Never commit this file. `JWT_SECRET` is mandatory; the backend intentionally refuses to start without it. When Compose variables are read from `backend/.env`, always include `--env-file backend/.env` in the command so that the database and backend receive matching credentials.

Frontend service URLs are Vite build-time settings. Empty `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` values mean “use the browser hostname on port 8000”; changing a `VITE_*` value requires rebuilding the frontend image. See `frontend/.env.example` for standalone frontend development.

## Local Docker deployment (browser camera)

The base Compose file uses `CAMERA_SOURCE=browser` from the example configuration:

```bash
docker compose --env-file backend/.env -f docker/docker-compose.yml up --build -d
docker compose --env-file backend/.env -f docker/docker-compose.yml ps
```

Open `http://localhost:3000`; the backend and health endpoint are at `http://localhost:8000` and `http://localhost:8000/health`. A remote browser normally needs HTTPS for `getUserMedia`; `localhost` is the standard development exception.

## Raspberry Pi deployment (backend camera and GPIO)

Identify the actual host devices first:

```bash
ls -l /dev/video* /dev/gpiochip*
v4l2-ctl --list-devices
gpioinfo
```

Set these values in `backend/.env` to match the host. This example maps `/dev/video0` and `/dev/gpiochip0` to the same device numbers inside the backend container:

```dotenv
CAMERA_SOURCE=backend
CAMERA_DEVICE=/dev/video0
CAMERA_INDEX=0
GPIO_CHIP_DEVICE=/dev/gpiochip0
GPIO_CHIP=0
```

If the usable controller is `/dev/gpiochip4`, set both `GPIO_CHIP_DEVICE=/dev/gpiochip4` and `GPIO_CHIP=4`. Then use the base file plus the Pi override:

```bash
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml \
  -f docker/docker-compose.pi.yml \
  up --build -d
```

The override removes the public PostgreSQL port, maps the selected camera and gpiochip devices only into the backend, and builds the frontend for backend-camera mode. Native libcamera/CSI capture is not implemented; a Pi camera must appear through a working V4L2 interface for the current OpenCV adapter.

## Normal operation and shutdown

Use the Recognition page to start or stop recognition. Starting enrollment while recognition owns the operation returns a busy result rather than opening a second camera loop. LED meanings are:

| State | Feedback |
|---|---|
| Recognizing | Yellow starts on and blinks |
| Bad angle/frame | Yellow solid for 5 seconds |
| Access granted | Blue solid for 5 seconds |
| Access denied or spoof | Red solid for 5 seconds |
| Enrollment: valid sample/completed | All LEDs on; completion holds for 3 seconds |
| Enrollment: spoof / bad frame / no face | Red / yellow / all off |
| Idle/shutdown | All LEDs off |

Stop with Compose so FastAPI receives its shutdown lifecycle event:

```bash
docker compose --env-file backend/.env -f docker/docker-compose.yml down --timeout 10
```

For Pi mode, include both Compose files in the `down` command as in the startup command. Avoid `kill -9` unless recovering a hung host: it prevents the application from proving camera/GPIO cleanup.

## Tests and verification

Backend environment and ordinary software tests:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r backend/requirements.txt
PYTHONPATH=backend:. .venv/bin/pytest tests/unit -q
PYTHONPATH=backend:. .venv/bin/pytest tests/integration -q
PYTHONPATH=backend:. .venv/bin/pytest tests/quality -q
```

QRT-005 needs only the isolated test database, which is protected by the test itself against a non-test database name:

```bash
docker compose -p faceguardv3-qrt -f docker/docker-compose.test.yml up -d --wait
PYTHONPATH=backend:. RUN_POSTGRES_INTEGRATION=1 \
  DB_HOST=127.0.0.1 DB_PORT=55432 \
  POSTGRES_DB=faceguard_test POSTGRES_USER=faceguard_test \
  POSTGRES_PASSWORD=faceguard_test \
  JWT_SECRET=faceguard-qrt-signing-secret-at-least-32-bytes \
  .venv/bin/pytest tests/quality/test_duplicate_registration.py -q
docker compose -p faceguardv3-qrt -f docker/docker-compose.test.yml down
```

Run the complete coverage and per-critical-module gate with the same database variables:

```bash
mkdir -p reports
PYTHONPATH=backend:. RUN_POSTGRES_INTEGRATION=1 \
  DB_HOST=127.0.0.1 DB_PORT=55432 \
  POSTGRES_DB=faceguard_test POSTGRES_USER=faceguard_test \
  POSTGRES_PASSWORD=faceguard_test \
  JWT_SECRET=faceguard-qrt-signing-secret-at-least-32-bytes \
  .venv/bin/pytest tests -q --cov=backend --cov-report=term-missing \
  --cov-report=json:reports/coverage.json --cov-report=xml:reports/coverage.xml
.venv/bin/python scripts/check_critical_coverage.py \
  --coverage-file reports/coverage.json --threshold 30
```

Frontend checks:

```bash
cd frontend
npm ci
npm test
npm run lint
npm run build
npm audit --audit-level=high
```

Compose and documentation checks:

```bash
BACKEND_ENV_FILE=../backend/.env.example docker compose \
  --env-file backend/.env.example -f docker/docker-compose.yml config --quiet
BACKEND_ENV_FILE=../backend/.env.example docker compose \
  --env-file backend/.env.example -f docker/docker-compose.yml \
  -f docker/docker-compose.pi.yml config --quiet
mkdocs build --strict --site-dir /tmp/faceguardv3-site
```

Container build smoke checks used by maintainers are:

```bash
docker build -f docker/Dockerfile -t faceguardv3-backend-audit .
docker build -f docker/Dockerfile.hub -t faceguardv3-backend-hub-audit .
docker build -f frontend/Dockerfile -t faceguardv3-frontend-audit frontend
```

See [Testing and QA](docs/testing.md) for the critical-module list and QRT evidence. GitHub-hosted CI does not validate a real camera, real liveness attacks, gpiochip electrical behavior, or physical LED latency.

## Raspberry Pi LED check

First inspect `http://<pi-host>:8000/health` and backend logs for `gpio_available`. The preferred check is a controlled recognition attempt. For a maintenance-only blue LED check inside the Pi backend container:

```bash
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml -f docker/docker-compose.pi.yml \
  exec backend python -c "import time, leds; leds.access_granted(); time.sleep(6); leds.shutdown()"
```

This is a manual hardware check, not QRT-006 evidence. Full QR-006 verification needs an automated Raspberry Pi hardware-in-the-loop setup that measures the physical LED transition.

## Troubleshooting

- **Camera cannot open:** confirm the host device with `v4l2-ctl`, verify `CAMERA_DEVICE`/`CAMERA_INDEX`, check container permissions and `docker compose ... logs backend`, and ensure no other process owns the device. Browser mode instead requires camera permission and a secure browser context.
- **WebSocket 403/close 1008:** sign out and back in, confirm the device clock is correct, and verify `JWT_SECRET` was not changed while the token was active. A proxy must forward WebSocket upgrades and subprotocol headers. Do not add the token to a URL as a workaround.
- **GPIO unavailable:** compare `GPIO_CHIP_DEVICE` with `gpioinfo`, ensure the mapped target and `GPIO_CHIP` number match, check BCM wiring (17/27/22), and inspect backend logs. The application remains usable without GPIO but reports `gpio_available: false`.
- **PostgreSQL authentication/health failure:** use `--env-file backend/.env`, keep the backend and database credentials identical, inspect `docker compose ... logs db backend`, and remember that changing credentials does not rewrite an existing `pgdata` volume.
- **Frontend uses the wrong host or camera mode:** correct the `VITE_*` build arguments and rebuild `frontend`; these values are compiled into the SPA rather than read dynamically after container startup.
- **Model startup failure:** verify `docker/insightface_models/minifasnet.onnx`, the configured `LIVENESS_MODEL_PATH`, storage permissions and free space. A corrupt/incomplete `buffalo_s` archive is discarded and retried up to the bounded limit; persistent failure is reported rather than bypassed.

## Maintained documentation

- [Architecture](docs/architecture/README.md)
- [Quality requirements](docs/quality-requirements.md)
- [Quality requirement tests](docs/quality-requirement-tests.md)
- [Testing and QA](docs/testing.md)
- [Definition of Done](docs/definition-of-done.md)
- [Customer handover](docs/customer-handover.md)
- [Contributing](CONTRIBUTING.md)
- [Agent Guidance](AGENTS.md)
- [Hosted documentation](https://innopolis-robotics-society.github.io/FaceGuardV3/)
