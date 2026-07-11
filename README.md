# FaceGuardV3
Face recognition access control system for the university laboratory.

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

Docker is supported on Mac, Windows, and Linux.

- **Windows:** Open Docker Desktop and wait until it shows "Engine running" in the bottom left corner.
- **Mac:** Open the Docker app and wait until the Docker icon appears in the menu bar.
- **Linux:**
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
