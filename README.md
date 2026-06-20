# FaceGuardV3
Face recognition access control system for the university laboratory.

## Requirements

### For Docker 
- Docker
- Docker Compose

### For Local Development
- Python 3.10+
- PostgreSQL  

## Setup Instructions

### Option 1: Docker  

**1. Clone the repository**
```bash
git clone git@github.com:Innopolis-Robotics-Society/FaceGuardV3.git
cd FaceGuardV3
```

**2. Create your secrets file**
```bash
cp backend/.streamlit/secrets.toml.example backend/.streamlit/secrets.toml
```
Open `backend/.streamlit/secrets.toml` and fill in your credentials:
- `admin_login` - your admin username
- `admin_password` - your admin password

**3. Build and run with Docker**
```bash
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up
```

**4. Access the application**
Open your browser at `http://localhost:8501`

**To stop the application:**
```bash
docker compose -f docker/docker-compose.yml down
```

---

### Option 2: Local Development

**1. Clone the repository**
```bash
git clone git@github.com:Innopolis-Robotics-Society/FaceGuardV3.git
cd FaceGuardV3
```

**2. Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  
```

**3. Install dependencies**
```bash
cd backend
pip install streamlit psycopg2-binary opencv-python insightface onnxruntime numpy pandas
```

**4. Create your secrets file**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Open `.streamlit/secrets.toml` and fill in your credentials.

**5. Run the app**
```bash
streamlit run pages/page_authentication.py
```

**6. Access the application**
Open your browser at `http://localhost:8501`

## Reports
1. [Week 2 Report](reports/week2/README.md)  
2. [MVP v0 Report](reports/week2/mvp-v0-report.md)  
