# FaceGuardV3 documentation

FaceGuardV3 is a local React + FastAPI + PostgreSQL face-recognition access indicator with liveness detection, dual browser/Raspberry-Pi camera modes, and optional GPIO LEDs. It has no physical door actuator.

## Start here

- [Repository setup, Raspberry Pi deployment, tests, and troubleshooting](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/main/README.md)
- [Customer handover](customer-handover.md)
- [Architecture](architecture/README.md)
- [Testing and QA](testing.md)
- [Quality requirements](quality-requirements.md) and [QRT status](quality-requirement-tests.md)
- [Definition of Done](definition-of-done.md)
- [Contributing](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/main/CONTRIBUTING.md)

## Minimal browser-camera deployment

```bash
cp backend/.env.example backend/.env
python3 backend/scripts/generate_hash.py
openssl rand -hex 32
docker compose --env-file backend/.env \
  -f docker/docker-compose.yml up --build -d
```

Fill the generated bcrypt hash and JWT secret in `backend/.env` first. Open `http://localhost:3000`; backend health is `http://localhost:8000/health`. Raspberry Pi backend-camera/GPIO deployment requires both Compose files and explicit device/chip configuration as documented in the root README.

!!! warning
    Never commit `backend/.env`. Normal CI does not prove physical camera behavior, real photo-attack rejection, or LED latency; consult the QRT page before interpreting test evidence.
