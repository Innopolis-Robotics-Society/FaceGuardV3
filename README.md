# FaceGuardV3

Face recognition access control for university laboratories.

FaceGuardV3 replaces physical access cards with a camera-based face recognition system. When a registered employee approaches the entrance, the system identifies them in seconds, unlocks the door, and logs the event. This all happens without any manual action. The system runs on a Raspberry Pi 5 at the edge, works fully offline, and integrates with LED indicators for immediate visual feedback.

| Quick links | |
|---|---|
| **Hosted documentation** | [docs.faceguard.dev](https://innopolis-robotics-society.github.io/FaceGuardV3/) |
| **Current release** | [v3.0.0 - Trial release](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v3.0.0) |
| **Customer handover** | [docs/customer-handover.md](docs/customer-handover.md) |
| **Contributing** | [CONTRIBUTING.md](CONTRIBUTING.md) |
| **Agent guidance** | [AGENTS.md](AGENTS.md) |

## Product goal

Laboratory access control must be secure, fast, and effortless. FaceGuardV3 removes the problem of lost or forgotten access cards by recognising employees solely by their face. The system is designed for unattended operation on a Raspberry Pi, with automatic recognition, liveness-based spoofing protection.

## Current features

- **Decoupled architecture**: React frontend + FastAPI backend, communicating via WebSockets for real-time video streaming
- **Automatic face recognition**: captures video frames and recognises registered employees
- **Accessories support**: recognises employees wearing glasses, masks, or other accessories
- **Liveness detection**: resists static photo spoofing attacks using a MiniFASNet model
- **Temporary access**: grant time-limited access with exact start and expiration date+time
- **Employee management**: add, edit, remove, and search employees through a web interface
- **Access logs**: view all attempts with date-range filtering
- **LED indicators**: yellow during recognition, blue on access granted, red on access denied
- **Background recognition**: runs continuously without blocking the UI
- **Local database**: fully offline operation with PostgreSQL on the edge device
- **Full Docker deployment**: reproducible environment for development and production
- **Sprint 4 trial release v3.0.0**: see the [release page](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v3.0.0) for a complete changelog

## Screenshots

| Admin login | Recognition in action |
|---|---|
| ![Admin login](docs/screenshots/login.png) | ![Recognition](docs/screenshots/recognition.png) |

| Employee management | Access logs |
|---|---|
| ![Employees page](docs/screenshots/employees.png) | ![Access logs](docs/screenshots/logs.png) |

## Maintained documentation

| Document | What it covers |
|---|---|
| [Roadmap](docs/roadmap.md) | Sprint-by-Sprint delivery plan |
| [Architecture](docs/architecture/README.md) | Static, dynamic, and deployment views with ADRs |
| [Testing status](docs/testing.md) | Coverage, QRTs, CI gates, and QA checks |
| [Quality requirements](docs/quality-requirements.md) | Measurable non-functional requirements |
| [User acceptance tests](docs/user-acceptance-tests.md) | Maintained UAT scenarios with execution history |

## Setup Instructions - Docker

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

### 5. Make sure Docker is running
**Windows:** Open Docker Desktop and wait until it shows "Engine running" in the bottom left corner.
**Mac:** Open the Docker app and wait until the Docker icon appears in the menu bar.
**Linux:**
  ```bash
  sudo systemctl start docker
  ```

### 6. Build and run the containers

Return to the project root directory and start Docker:
```bash
cd ..
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up
```

### 7. Access the application
Once the containers are running, open your browser and navigate to:
```
http://localhost:3000
```

## Hosted Documentation

See the [Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/).