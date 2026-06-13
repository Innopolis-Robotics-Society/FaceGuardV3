# FaceGuardV3
Face recognition access control system for the university laboratory.

## Requirements
1. Python 3.10+
2. PostgreSQL

## Local Setup Instructions

**1. Clone the repository**  
   `git clone git@github.com:Innopolis-Robotics-Society/FaceGuardV3.git`  
   `cd FaceGuardV3/backend`
   
**2. Install dependencies**  
   `pip install -r requirements.txt`  
   
**3. Create your secrets file**  
   `cp .streamlit/secrets.toml.example .streamlit/secrets.toml`  
   Open the file and fill in your credentials.
   
**4. Run the app**  
   `streamlit run pages/page_authentication.py`

## Reports
1. [Week 2 Report](reports/week2/README.md)  
2. [MVP v0 Report](reports/week2/mvp-v0-report.md)  
