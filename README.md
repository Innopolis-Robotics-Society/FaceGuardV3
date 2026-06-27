# FaceGuardV3
Face recognition access control system for the university laboratory.

## Setup Instructions - Docker
The system supports both x86 (Laptops/PCs) and arm64 (Raspberry Pi 5) environments out of the box

**1. Clone the repository**
```bash
git clone [https://github.com/Innopolis-Robotics-Society/FaceGuardV3.git](https://github.com/Innopolis-Robotics-Society/FaceGuardV3.git)
cd FaceGuardV3
```

**2. Configure Secrets and Environment**
Copy the example secrets file:
```bash
cp backend/.streamlit/secrets.toml.example backend/.streamlit/secrets.toml
```
Open `backend/.streamlit/secrets.toml` and fill in your credentials:
- `admin_login` - your admin username
- `admin_password` - your admin password

**3. Make sure Docker is running**  
Open Docker Desktop (or start the Docker daemon on Linux) and wait until the engine is running.

**4. Build and run with Docker**
```bash
docker compose -f docker/docker-compose.yml up --build
```

**5. Access the application**  
Open your browser at `http://localhost:8501`
