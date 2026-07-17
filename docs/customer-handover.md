# Customer Handover and Operations Guide

This is the maintained operational handover for the current FaceGuardV3 repository. It describes what the software actually implements and separates CI evidence from checks that require the customer's Raspberry Pi and physical hardware.

## Scope and current assurance

FaceGuardV3 consists of a React SPA, a FastAPI/InsightFace/MiniFASNet backend, local PostgreSQL, a browser or Raspberry Pi camera adapter, and optional yellow/blue/red GPIO LEDs. It stores data locally and can operate without cloud services after model assets have been populated.

The repository does **not** contain a motor or physical door actuator. LEDs are indicators only. This audit verified software tests, PostgreSQL QRT, frontend build/tests, configuration validation, and CI definitions. It did not have access to the customer's Pi camera, gpiochip wiring, physical LEDs, lighting, or door environment; therefore physical deployment readiness and QR-006 latency are not claimed by this document.

## Customer-owned assets

| Asset | Operational responsibility |
|---|---|
| Raspberry Pi 5, camera, LED wiring/resistors | Customer administrator |
| `backend/.env`, admin password, JWT secret, database password | Customer administrator; never commit or share |
| PostgreSQL `pgdata` volume and backups | Customer administrator |
| InsightFace/liveness model directory | Customer administrator; keep available locally |
| Source and maintained documentation | Repository maintainers |

## Prerequisites

- Raspberry Pi 5 with a 64-bit OS, active cooling for continuous inference, Docker Engine, and recent Docker Compose v2.
- A camera visible as `/dev/videoN` through V4L2. USB webcams are supported. A CSI/Pi camera is supported only if it is deliberately exposed through a working V4L2 interface; there is no native libcamera adapter.
- For LEDs: a usable `/dev/gpiochipN`, `gpioinfo`, and correctly protected BCM 17/27/22 wiring.
- Initial access to model assets. The tracked MiniFASNet model is mounted from `docker/insightface_models`; when `buffalo_s` is absent, the backend downloads it with bounded retries, validates the archive and required ONNX files, then retains it in the mounted cache.

## Secure configuration

From the repository root:

```bash
cp backend/.env.example backend/.env
python3 backend/scripts/generate_hash.py
openssl rand -hex 32
```

Set at least:

- `ADMIN_LOGIN` and the generated bcrypt `ADMIN_PASSWORD_HASH`;
- a new, independent `JWT_SECRET` (mandatory at startup);
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DB_HOST=db`, and `DB_PORT=5432`;
- the real browser origin in `CORS_ORIGINS`, for example `http://faceguard-pi:3000` in addition to any local origins;
- camera and GPIO variables described below.

Restrict file permissions and never put the JWT or plaintext admin password in documentation. Use `--env-file backend/.env` in Compose commands; otherwise Compose interpolation can create database credentials that differ from those received by the backend.

## Camera modes

| Mode | Capture owner | Deployment use | Backlog behavior |
|---|---|---|---|
| `browser` | Browser `getUserMedia` | Local development or a client-attached camera | One JPEG may await a response; no client-side queue |
| `backend` | Pi backend OpenCV worker | Camera physically attached to the Pi | One replace-only latest frame; no FIFO queue |

The base Compose file builds browser mode. The Pi override builds backend mode and maps the selected device. `VITE_*` settings are build-time values, so rebuild the frontend after changing them. A remote browser camera needs HTTPS and camera permission; a remote browser cannot access a camera attached to the Pi, which is why backend mode exists.

The single capture-owner guarantee applies to the deployed FastAPI service. Legacy maintenance CLIs under `backend/faceguard/` open OpenCV directly and must only be used while the service is stopped if they target the same camera.

## Deployment

### Ordinary local deployment

```bash
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml up --build -d
```

### Raspberry Pi deployment

Find devices:

```bash
ls -l /dev/video* /dev/gpiochip*
v4l2-ctl --list-devices
gpioinfo
```

Example `backend/.env` values:

```dotenv
CAMERA_SOURCE=backend
CAMERA_DEVICE=/dev/video0
CAMERA_INDEX=0
GPIO_CHIP_DEVICE=/dev/gpiochip0
GPIO_CHIP=0
```

The host and container gpiochip numbers must agree. For `/dev/gpiochip4`, use `GPIO_CHIP_DEVICE=/dev/gpiochip4` and `GPIO_CHIP=4`.

```bash
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml \
  -f docker/docker-compose.pi.yml \
  up --build -d
```

The Pi override removes the database host port and maps only the configured camera/gpiochip into the backend. PostgreSQL remains on the internal `faceguard` bridge network. `pgdata` is persistent; schema creation and the legacy access-date migration run automatically during backend startup.

## Startup verification

1. Run `docker compose ... ps`; all three services should become healthy.
2. Open `http://<pi-host>:8000/health`. Confirm `models_ready: true`, the expected `camera_source`, and the expected `gpio_available` value.
3. Open `http://<pi-host>:3000`, sign in, and confirm authenticated Employees and Logs requests work.
4. Start recognition. In backend mode, confirm only one camera operation starts; trying enrollment concurrently should receive a busy result.
5. Register a dedicated test person, try the same face again, and confirm HTTP/UI duplicate rejection without a second employee row.
6. Verify temporary access before, within, and after its configured timestamp window.

## LED operation and manual check

| Backend result | Physical command |
|---|---|
| Recognizing | Yellow begins on and blinks |
| Bad frame/angle | Yellow solid, 5 seconds |
| Granted | Blue solid, 5 seconds |
| Denied or spoof | Red solid, 5 seconds |
| Enrollment valid sample/completion | All on; completion holds 3 seconds |
| Enrollment spoof / bad frame / no face | Red / yellow / all off |
| Stop/shutdown | All off and resources closed |

The preferred check is an actual controlled recognition/enrollment attempt. A maintenance-only blue test is:

```bash
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml -f docker/docker-compose.pi.yml \
  exec backend python -c "import time, leds; leds.access_granted(); time.sleep(6); leds.shutdown()"
```

This confirms visible behavior manually but is not automated QR-006 evidence. CI fake GPIO proves software command ordering, stale-thread protection, chip selection, and cleanup only. Physical latency still needs a self-hosted Pi hardware-in-the-loop runner with a photodiode or logic analyzer.

## Authentication and data behavior

- Login is bcrypt-checked and limited to five attempts per minute per remote address.
- REST uses a Bearer JWT. WebSockets use subprotocols and never require a JWT query string.
- Recognition/enrollment are serialized to protect model and camera state.
- Liveness failure is rejected before embedding comparison and logged as a spoof attempt.
- Duplicate registration compares stored embeddings at threshold `0.56` under a PostgreSQL advisory transaction lock. A duplicate returns `409`, rolls back, and preserves existing data.
- Temporary employee embeddings are available for recognition only within inclusive start/expiration timestamps.
- Logs older than three days are pruned by a tracked background task.

## Shutdown and recovery

Use normal Compose shutdown so FastAPI can cancel the cleanup task, release the camera, turn off/close GPIO, and close the database pool:

```bash
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml -f docker/docker-compose.pi.yml \
  down --timeout 10
```

Do not use `kill -9` as a normal stop procedure. If the backend was forcibly killed, verify no process still owns `/dev/videoN`, inspect LED state, and restart the stack before use.

Useful diagnostics:

```bash
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml -f docker/docker-compose.pi.yml ps
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml -f docker/docker-compose.pi.yml logs --tail 200 db backend frontend
```

## Test and evidence commands

The exact backend, QRT-005, coverage, frontend, Compose, and documentation commands are maintained in the [root README](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/main/README.md#tests-and-verification) and [Testing and QA](testing.md). The key evidence split is:

- GitHub-hosted CI: unit/integration/software QRT, real PostgreSQL QRT-005, per-critical-module coverage, frontend tests/lint/type-check/build, Bandit, Compose configuration, docs build, and Lychee links.
- Raspberry Pi/manual or HIL: real V4L2 stability, physical liveness attacks, real model/UI response latency, correct wiring, electrical/visible LED latency, thermal behavior, and forced-failure recovery.

## Troubleshooting

- **Camera:** validate `v4l2-ctl --list-devices`, `CAMERA_DEVICE`, `CAMERA_INDEX`, container mapping/permissions, and that no other process owns it. For browser mode, check HTTPS and browser permission.
- **WebSocket 403 or close 1008:** sign out/in, verify Pi time and unchanged `JWT_SECRET`, and ensure any reverse proxy forwards WebSocket subprotocol headers. Never move the JWT into the URL.
- **GPIO unavailable:** compare `gpioinfo` with `GPIO_CHIP_DEVICE`/`GPIO_CHIP`, verify BCM 17/27/22 wiring, and inspect backend initialization logs. The software deliberately continues without LEDs.
- **PostgreSQL unhealthy/authentication failed:** include `--env-file backend/.env`, inspect `db` logs, and remember that changing credentials does not rewrite credentials inside an existing initialized `pgdata` volume.
- **Frontend wrong backend URL/mode:** update `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`, or the selected Compose mode and rebuild the frontend.
- **Models not ready:** verify the bind-mounted MiniFASNet file, `LIVENESS_MODEL_PATH`, `buffalo_s` files, permissions, disk space, and first-start network availability.

## Remaining limitations

- No physical door actuator.
- No native libcamera adapter; backend capture is V4L2/OpenCV.
- QR-001 and QR-002 have supporting CI checks but no complete real-hardware automated evidence.
- QRT-006 is Planned because no physical-latency runner exists.
- Model thresholds and real-world accuracy still require customer-environment calibration and acceptance testing.
- The Logs backend accepts a date range, but the current Logs page has no date-range controls.
- Employee registration is stored/displayed as a date, not a registration timestamp; temporary access bounds remain full timestamps.
