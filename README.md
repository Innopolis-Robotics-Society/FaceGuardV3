# FaceGuardV3
Face recognition access control system for the university laboratory.

## Setup Instructions - Docker

**1. Clone the repository**
```bash
git clone git@github.com:Innopolis-Robotics-Society/FaceGuardV3.git
cd FaceGuardV3
```
If the above does not work, use HTTPS instead:
```bash
git clone https://github.com/Innopolis-Robotics-Society/FaceGuardV3.git
cd FaceGuardV3
```

**2. Create your secrets file**
```bash
cp backend/.streamlit/secrets.toml.example backend/.streamlit/secrets.toml
```
Open `backend/.streamlit/secrets.toml` and fill in your credentials:
- `admin_login` — your admin username
- `admin_password` — your admin password

**3. Make sure Docker is running**

**Windows:** Open Docker Desktop and wait until it shows "Engine running" in the bottom left corner.

**Mac:** Run `open -a Docker` and wait until the Docker icon appears in the menu bar.

**Linux:**
```bash
sudo systemctl start docker
```

**4. Build and run with Docker**
```bash
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up
```

**5. Access the application**
Open your browser at `http://localhost:8501`

## Hosted Documentation
See the [Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/).
