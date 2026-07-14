# FaceGuard
Face recognition access control system for a university laboratory.

## Project description
FaceGuard replaces physical access cards with a camera-based face recognition system. When a registered employee approaches the entrance, the system identifies them, gives visual feedback with LED indicators, and logs the event. This all happens without any manual action. The system runs on a Raspberry Pi, works fully offline, detects liveness to prevent photo spoofing, recognises employees even with glasses or masks, and integrates with LED indicators for immediate visual feedback.

## Product goal
Laboratory access control must be secure and fast. FaceGuard removes the problem of lost or forgotten access cards by recognising employees solely by their face. The system is designed for unattended operation on a Raspberry Pi, with automatic recognition, liveness-based spoofing protection.

## Current features
- **Automatic face recognition**: captures video frames and recognises registered employees.
- **Accessories support**: recognises employees wearing glasses, masks, or other accessories.
- **Liveness detection**: resists static photo spoofing attacks using a MiniFASNet model.
- **Employee management**: add, edit, remove, and search employees through a web interface.
- **LED indicators**: yellow during recognition, blue on access granted, red on access denied.
- **Background recognition**: runs continuously without blocking the UI.
- **Local database**: fully offline operation with PostgreSQL on the edge device.

## Maintained documentation
| Document | What it covers |
|---|---|
| [Roadmap](docs/roadmap.md) | Sprint-by-Sprint delivery plan |
| [Architecture](docs/architecture/README.md) | Static, dynamic, and deployment views with ADRs |
| [Testing status](docs/testing.md) | Coverage, QRTs, CI gates, and QA checks |
| [Quality requirements](docs/quality-requirements.md) | Measurable non-functional requirements |
| [User acceptance tests](docs/user-acceptance-tests.md) | Maintained UAT scenarios with execution history |

## Documentation Links
| Documentation | Link |
|---|---|
| Hosted documentation | [docs.faceguard.dev](https://innopolis-robotics-society.github.io/FaceGuardV3/) |
| Current release | [v3.0.0 - Trial release](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v3.0.0) |
| Customer handover | [docs/customer-handover.md](docs/customer-handover.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Agent guidance | [AGENTS.md](AGENTS.md) |

## Setup Instructions

### 1. Clone the repository

```bash
git clone git@github.com:Innopolis-Robotics-Society/FaceGuardV3.git
cd FaceGuardV3
```
If the above does not work, use HTTPS instead:
```bash
git clone https://github.com/Innopolis-Robotics-Society/FaceGuardV3.git
cd FaceGuardV3
```

### 2. Configure environment variables

Navigate to the backend directory and copy the environment example file:
```bash
cd backend
cp .env.example .env
```

### 3. Generate an admin password hash

Run the hash generation script to securely hash your password:
```bash
python3 scripts/generate_hash.py
```
Enter your desired password when prompted, and copy the generated bcrypt hash.

### 4. Fill in the `.env` file

Open `backend/.env` and fill in all the required data.
For the admin credentials, paste your login and the generated hash without any quotes:
```
ADMIN_LOGIN=myadmin
ADMIN_PASSWORD_HASH=<your_copied_bcrypt_hash>
```

Generate a distinct JWT signing secret and paste it as `JWT_SECRET`:

```bash
openssl rand -hex 32
```

If the UI is opened directly by Pi hostname/IP instead of through localhost
SSH forwarding, add that exact origin to the comma-separated `CORS_ORIGINS`
allow-list. Do not use `*`.

### 5. Make sure Docker is running
**Windows:** Open Docker Desktop and wait until it shows "Engine running" in the bottom left corner.  
**Mac:** Open the Docker app and wait until the Docker icon appears in the menu bar.  
**Linux:**
  ```bash
  sudo systemctl start docker
  ```

### 6. Build and run the containers

Return to the project root directory. For laptop development, where the
browser supplies camera frames with `getUserMedia`, use the base Compose file:

```bash
cd ..
docker compose --env-file backend/.env -f docker/docker-compose.yml config
docker compose --env-file backend/.env -f docker/docker-compose.yml up -d --build
```

For Raspberry Pi 5, use the hardware override as well. It maps only
`/dev/video0` and `/dev/gpiochip0`, builds the frontend in backend-camera mode,
and makes the FastAPI container own camera index 0:

```bash
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml \
  -f docker/docker-compose.pi.yml config
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml \
  -f docker/docker-compose.pi.yml up -d --build
```

`backend/.env` is a required local file and must not be committed. The database
and backend read the same file, which prevents credential drift. Vite embeds
`VITE_CAMERA_SOURCE` at build time, so changing camera mode requires rebuilding
the frontend image. Optional `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` values
are also passed as frontend build arguments; leave them unset for the default
current-hostname/port-8000 routing used by SSH forwarding.

On the first backend start, the pinned InsightFace `buffalo_s` archive
(approximately 122 MiB) is downloaded into `docker/insightface_models`, checked
as a ZIP, and then extracted. Keep this cache to make later starts fully
offline. A corrupt ZIP or storage error is reported explicitly and must be
investigated rather than bypassed.

### 7. Access the application
Once the containers are running, open your browser and navigate to:
```
http://localhost:3000
```

When accessing the Pi over SSH port forwarding, forward both application ports,
for example `ssh -L 3000:localhost:3000 -L 8000:localhost:8000 pi@<pi-host>`.

## Hosted Documentation

See the [Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/).
