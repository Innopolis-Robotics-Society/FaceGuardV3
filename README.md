# FaceGuardV3

Face recognition access control system for the university laboratory.
The system uses a React frontend, a FastAPI backend, InsightFace for recognition, and Raspberry Pi GPIO for physical door control and LED feedback.

## Product Access

The system is deployed on a Raspberry Pi 5 with a connected USB webcam and electronic door lock.
Access the frontend at the Pi's address on port `3000` (e.g. `http://<raspberry-pi-ip>:3000`).

For local development or evaluation, build and run via Docker (see below).

## Key Links

- **[Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/)** — browsable architecture, process, quality, and testing docs
- **[Customer Handover Guide](docs/customer-handover.md)** — transition details, known limitations, and operational guidance
- **[Contribution Guidelines](CONTRIBUTING.md)** — workflow for human contributors
- **[Agent Guidance](AGENTS.md)** — setup and workflow guidance for AI coding agents

### Maintained Documentation

- [Roadmap](docs/roadmap.md) — Sprint-by-Sprint delivery plan
- [Architecture](docs/architecture/README.md) — static, dynamic, and deployment views with ADRs
- [Testing Status](docs/testing.md) — coverage, QRTs, CI gates, and QA checks
- [Quality Requirements](docs/quality-requirements.md) — measurable non-functional requirements
- [User Acceptance Tests](docs/user-acceptance-tests.md) — maintained UAT scenarios

## Setup Instructions

### 1. Clone the repository

```bash
git clone git@github.com:Innopolis-Robotics-Society/FaceGuardV3.git
cd FaceGuardV3
```
*(If the above does not work, use HTTPS: `git clone https://github.com/Innopolis-Robotics-Society/FaceGuardV3.git`)*

### 2. Configure the environment

FaceGuardV3 uses a `.env` file for secrets.
```bash
cp backend/.env.example backend/.env
```
Open `backend/.env` and specify your required configuration variables (e.g., admin credentials, database settings).

### 3. Build and Run with Docker

Make sure Docker and Docker Compose are installed and running on your machine.

```bash
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d
```

### 4. Access the Application

- **Frontend (UI)**: Open your browser at `http://localhost:3000`
- **Backend (API Docs)**: Open your browser at `http://localhost:8000/docs`

*For edge deployment on Raspberry Pi, please refer to the deployment section in our hosted documentation or the [Customer Handover Guide](docs/customer-handover.md).*
