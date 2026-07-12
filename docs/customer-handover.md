# Customer Handover and Operations Guide

This document is the authoritative handover artifact for FaceGuard, Week 6 Trial Release (`v3.0.0`, MVP v2). It defines the current transition status, operational requirements, and essential knowledge required by the customer to independently deploy, operate, and maintain the system.

## 1. Product Status and Handover Scope

**Product Overview:** FaceGuard is a secure, decoupled face recognition access control system. It uses an edge-hosted FastAPI backend, a React SPA frontend, and local PostgreSQL storage to recognize registered employees in real time and log all access attempts.

**Scope of this release:** This handover covers the Week 6 Trial Release (MVP v2 progress, towards MVP v3). It includes a fully persistent local database, background recognition that runs while the admin navigates other pages, and recognition with accessories. Physical door integration is not part of this release and is not planned; the LED indicators serve as the access signal in place of a physical door mechanism.

**Important customer requirement:** the system must not use any external database or cloud resource. All data must be stored locally on the device only. This was explicitly and firmly stated by the customer during the Week 6 session, after the team had briefly used cloud storage before migrating to fully local storage.

## 2. Handover Status and Ownership

### Transition Status

| Attribute | Value |
|:---|:---|
| **Transition Outcome** | `Ready for independent use` |
| **Customer Confirmation Status** | `Accepted` |
| **Deployment Responsibility** | Customer (Raspberry Pi 5) |
| **Repository Ownership** | Team (retained) |
| **Documentation Sufficiency** | Not confirmed as sufficient; the customer requested a dedicated documentation page or site describing the system's functions |

Detailed confirmation evidence, the meeting date, and the customer's exact feedback are recorded in `reports/week6/sprint-review-summary.md` and, if recorded, the transcript. This file only reflects the resulting status.

### Why Full Transition Was Not Reached

**Current level:** `Ready for independent use`

**Why not `Independently used by customer` or `Deployed or operated on customer side`:**
- The system is deployed on customer hardware, but formal independent use has not yet been observed
- Actual production usage will begin after handover
- This is acceptable for the current course scope

**Remaining actions needed:** None blocking for the current handover level. Follow-up items are non-blocking enhancements, see Section 7.

### Ownership and Access Transfer

| Asset | Owner after handover | Notes |
|:---|:---|:---|
| Source code (GitHub) | Team (retained) | Customer has read access |
| Deployed product | Customer | Raspberry Pi 5, local deployment |
| Admin credentials | Customer | Managed in `.env` file |
| Hardware (camera, LEDs) | Customer | Pre-existing hardware |
| Database (PostgreSQL) | Customer | Local only, operated on Raspberry Pi. No external or cloud database is used |
| Documentation | Customer | Public repository and hosted docs |
| Future support | Team | Critical fixes only, until course completion |

## 3. Configuration and Secrets Management

To operate the system, the customer must manage the runtime environment variables securely. No secrets are committed to the repository.

### Required Environment Variables

Create a `.env` file in the `backend/` directory (copy `backend/.env.example` as a starting point). At minimum:

- `ADMIN_LOGIN`: the login required to access the React admin panel
- `ADMIN_PASSWORD_HASH`: a bcrypt hash of the admin password. Generate it with `python3 scripts/generate_hash.py` from the `backend/` directory, then paste the resulting hash here. Do not store the plain password anywhere.
- `POSTGRES_USER`: PostgreSQL user
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name
- `DB_HOST`: PostgreSQL hostname (usually `db` in Docker Compose)
These must point only to the local PostgreSQL container, never to an external or cloud database.

Ensure the `.env` file has restricted read permissions on the Raspberry Pi so that unauthorized users cannot extract the admin credentials or password hash.

## 4. Setup, Deployment, and Verification

Full setup instructions and troubleshooting are also maintained in the root [README.md](../README.md). The steps below reflect the current actual process.

### Initial Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:Innopolis-Robotics-Society/FaceGuardV3.git
   cd FaceGuardV3
   ```
   If SSH does not work, use HTTPS instead:
   ```bash
   git clone https://github.com/Innopolis-Robotics-Society/FaceGuardV3.git
   cd FaceGuardV3
   ```
2. Configure environment variables:
   ```bash
   cd backend
   cp .env.example .env
   ```
3. Generate an admin password hash:
   ```bash
   python3 scripts/generate_hash.py
   ```
   Enter your chosen password when prompted and copy the generated bcrypt hash.
4. Open `backend/.env` and fill in the required values, including the database credentials and the admin credentials, without quotes:
   ```
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=faceguard
   DB_HOST=db
   ADMIN_LOGIN=myadmin
   ADMIN_PASSWORD_HASH=your_copied_bcrypt_hash
   ```
5. Make sure Docker is running:
   - Windows: open Docker Desktop and wait for "Engine running"
   - Mac: open the Docker app and wait for the Docker icon in the menu bar
   - Linux: `sudo systemctl start docker`
6. From the project root, build and start the containers:
   ```bash
   cd ..
   docker compose -f docker/docker-compose.yml build
   docker compose -f docker/docker-compose.yml up
   ```
7. Once the containers are running, open `http://localhost:3000` in a browser.

### Verification Steps

1. **Access the UI:** confirm `http://localhost:3000` loads without errors.
2. **Login:** enter the `ADMIN_LOGIN` and the password you hashed in step 3 above.
3. **Hardware check:** register a test user and confirm the connected LEDs respond as described in Section 5.
4. **Background recognition check:** while a recognition is running, navigate to another page in the admin panel and confirm recognition continues without interruption.

### System Recovery

- Restart services: `docker compose -f docker/docker-compose.yml restart`
- View logs: `docker compose -f docker/docker-compose.yml logs --tail 100`

## 5. Operational Notes for Normal Use

- **LED feedback during recognition:**
  - Yellow, blinking: the system is actively attempting to recognize a face
  - Yellow, solid for 5 seconds: poor lighting or a blurry frame, the person should look straight ahead
  - Blue, solid for 5 seconds: access granted, the person was recognized
  - Red, solid for 5 seconds: access denied, the face was not recognized
  - No LEDs lit: no one is currently in front of the camera
- **LED feedback during employee registration:** all three LEDs (yellow, red, blue) light up together during registration and for 3 seconds afterward.
- **Background recognition:** recognition keeps running while the admin uses other pages in the panel; the admin does not need to stay on the recognition page.
- **Rate limiting and Authentication:** API endpoints are secured with JSON Web Tokens (JWT). The login page is protected against brute-force attacks via SlowAPI: if an admin inputs incorrect credentials 5 times within a minute, access is temporarily blocked with a "Too Many Requests" (429) status.
- **Temporary access auto-expiry:** employees with temporary access are validated against their start and expiration dates. Access is automatically denied outside this window, no admin action needed. Date and time validation to prevent past dates is a planned improvement, see Section 7.
- **Log management:** access logs are retained in the local database. The system automatically prunes logs older than 3 days to preserve storage on the Raspberry Pi.

## 6. Documentation Entry Points

For normal customer use, operation, and troubleshooting, refer to:

- [Main README](../README.md): primary entry point and setup instructions
- [Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/): full project documentation
- [Contributor Guide](../CONTRIBUTING.md) and [Agents Guide](../AGENTS.md): guidelines for team members and AI agents
- [System Roadmap](roadmap.md): product evolution up to `MVP v2`
- [User Acceptance Tests](user-acceptance-tests.md): step-by-step instructions for admin panel usage

A dedicated function-description documentation page was requested by the customer during the Week 6 session and is planned, see Section 7.

## 7. Remaining Actions and Known Limitations

**Follow-up items (non-blocking):**

- Fix the occasional page freeze under load
- Add date and time validation for temporary access, minimum value is the current date and time
- Continue optimizing performance and stability on Raspberry Pi, particularly for the camera stream on weaker hardware
- Add a dedicated documentation page or site describing the system's functions, explicitly requested by the customer

**Known limitations and customer-side responsibilities:**

- **Lighting sensitivity:** the recognition model's accuracy degrades in low lighting. The deployment area must be well lit.
- **Thermal management:** running the system continuously on the Raspberry Pi without active cooling may cause thermal throttling.
- **Camera stream stability:** the camera stream occasionally does not capture correctly on weaker hardware; the customer described this as a minor issue.
