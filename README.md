# FaceGuardV3

FaceGuardV3 is a robust, decoupled face recognition access control system designed for the university laboratory. 
It uses a React frontend, a FastAPI backend, an InsightFace recognition model, and integrates with Raspberry Pi GPIO for physical access control feedback (LEDs).

## Key Links

- **[Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/)**: Comprehensive documentation including architecture, development process, and quality testing.
- **[Customer Handover Guide](docs/customer-handover.md)**: Transition details, known limitations, and operational guidance for the customer.
- **[Contribution Guidelines](CONTRIBUTING.md)**: Workflow for contributing to this project.
- **[Agent Guidance](AGENTS.md)**: Guidance for AI agents and automation bots operating in this repository.

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
