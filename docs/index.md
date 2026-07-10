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
cp backend/secrets.toml.example backend/secrets.toml
```
Open `backend/secrets.toml` and fill in your credentials:
- `admin_login` — your admin username
- `admin_password` — your admin password
- `host`, `database`, `user`, `password` — your PostgreSQL database connection details

> [!WARNING]
> Never commit your `backend/secrets.toml` file to version control. It is already included in `.gitignore`.

**3. Make sure Docker is running**

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
Open your browser at `http://localhost:3000` for the Web UI.
*(The backend API and WebSockets are automatically served at `http://localhost:8000`)*
