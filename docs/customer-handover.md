# Customer Handover and Operations Guide

This document is the authoritative handover artifact for FaceGuard, final release (`MVP v3`, Sprint 5 / Week 7). It defines the current transition status, operational requirements, and essential knowledge required by the customer to independently deploy, operate, and maintain the system.

## 1. Product Status and Handover Scope

**Product Overview:** FaceGuard is a secure, decoupled face recognition access control system. It uses an edge-hosted FastAPI backend, a React SPA frontend, and local PostgreSQL storage to recognize registered employees in real time and log all access attempts.

**Scope of this release:** This is the final MVP v3 release. It includes a fully persistent local database, background recognition that runs while the admin navigates other pages, recognition with accessories (glasses, hats), temporary access date and time validation, brute-force login protection with a lockout after repeated failed attempts, and a documentation site with authentication, registration, recognition status, and deployment guidance. Physical door integration is not part of this release and is not planned; the LED indicators serve as the access signal in place of a physical door mechanism. Medical masks are intentionally not supported as a recognized accessory, for the security reasons explained in Section 5.

**Important customer requirement:** the system must not use any external database or cloud resource. All data must be stored locally on the device only. This was explicitly and firmly stated by the customer during the Week 6 session and remains in effect.

## 2. Handover Status and Ownership

### Transition Status

| Attribute | Value |
|:---|:---|
| **Transition Outcome** | `Ready for independent use` |
| **Customer Confirmation Status** | `Accepted` |
| **Deployment Responsibility** | Customer (Raspberry Pi 5) |
| **Repository Ownership** | Team (retained) |
| **Documentation Sufficiency** | Confirmed sufficient by the customer during the Week 7 final transition session |

Detailed confirmation evidence and the customer's exact answers are recorded in `reports/week7/sprint-review-summary.md` and the transcript. This file only reflects the resulting status.

### Final Transition Confirmation (Week 7, 2026-07-16)

The customer was asked directly and confirmed:
- Able to use the system independently, without the team's assistance: **Yes**
- System already deployed in the customer's own environment: **Not yet**
- Current version sufficient to manage the system independently going forward: **Yes**
- Anything preventing the customer from taking full control now: **No**
- Accepts this as the final delivered product: **Yes**

### Why the Highest Level Was Not Reached

**Current level:** `Ready for independent use`

**Why not `Deployed or operated on customer side`:**
- The customer confirmed the system is not yet deployed in their own environment; deployment on customer infrastructure has not been observed yet
- This is expected to happen after the course concludes and is not a blocker for this handover

**Remaining actions needed:** None blocking. The customer explicitly confirmed nothing prevents them from taking full control of the system.

### Ownership and Access Transfer

| Asset | Owner after handover | Notes |
|:---|:---|:---|
| Source code (GitHub) | Team (retained) | Customer has read access |
| Deployed product | Customer | Raspberry Pi 5, local deployment |
| Admin credentials | Customer | Managed in `.env` file; login and password hash can be changed at any time using the provided script |
| Hardware (camera, LEDs) | Customer | Pre-existing hardware |
| Database (PostgreSQL) | Customer | Local only, operated on Raspberry Pi. No external or cloud database is used |
| Documentation | Customer | Public repository and hosted docs, confirmed sufficient by the customer |
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
- `DB_HOST`: PostgreSQL hostname, usually `db` in Docker Compose

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
5. **Login lockout check:** attempt to log in with an incorrect password 5 times within a minute and confirm the system temporarily blocks further attempts.

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
- **Accessories:** glasses and hats are supported and reliably recognized. Medical masks are intentionally not supported: a mask significantly distorts the facial embedding, which would reduce the reliability of the identity match, so the system rejects recognition attempts made while wearing one. This is a deliberate security and reliability decision.
- **Anti-spoofing:** the system rejects recognition attempts made by presenting a photograph instead of a real face.
- **Rate limiting and authentication:** API endpoints are secured with JSON Web Tokens (JWT). The login page is protected against brute-force attacks: if an admin enters incorrect credentials 5 times within a minute, further attempts are temporarily blocked with a "Too many attempts. Please try again later." message for one minute.
- **Temporary access date and time validation:** the system only accepts a future date and time for temporary access; past dates are rejected. Employees with temporary access are validated against their start and expiration dates, and access is automatically denied outside this window without admin action.
- **Log management:** access logs are retained in the local database. The system automatically prunes logs older than 3 days to preserve storage on the Raspberry Pi.
- **Performance:** registration and recognition are slower on the Raspberry Pi than on a laptop. The system has been optimized as much as practical within the current hardware's limitations.

## 6. Documentation Entry Points

For normal customer use, operation, and troubleshooting, refer to:

- [Main README](../README.md): primary entry point and setup instructions
- [Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/): full project documentation, including authentication, registration, recognition status colors, and deployment steps, available in light and dark themes
- [Contributor Guide](../CONTRIBUTING.md) and [Agents Guide](../AGENTS.md): guidelines for team members and AI agents
- [System Roadmap](roadmap.md): product evolution up to `MVP v3`
- [User Acceptance Tests](user-acceptance-tests.md): step-by-step instructions for admin panel usage

The customer reviewed this documentation during the Week 7 session and confirmed it is sufficient.

## 7. Remaining Actions and Known Limitations

**Follow-up items (non-blocking):**

- Continue optimizing performance and stability on Raspberry Pi where practical, within current hardware limitations

**Known limitations and customer-side responsibilities:**

- **Lighting sensitivity:** the recognition model's accuracy degrades in low lighting. The deployment area must be well lit.
- **Thermal management:** running the system continuously on the Raspberry Pi without active cooling may cause thermal throttling.
- **Hardware performance:** registration and recognition are slower on the Raspberry Pi than on more powerful hardware such as a laptop, due to hardware constraints rather than a software defect.
- **Medical masks not supported:** intentionally excluded from recognized accessories for reliability and security reasons; see Section 5.
- **Not yet deployed on customer infrastructure:** the customer confirmed the current version is sufficient to do so, but deployment on their own environment had not yet taken place as of the Week 7 session.
