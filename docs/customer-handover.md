# Customer Handover and Operations Guide

This document is the authoritative handover artifact for MVP v3. It defines the current transition status, operational requirements, and essential knowledge required by the customer to independently deploy, operate, and maintain the system.

## 1. Product Status and Handover Scope

**Product Overview:** FaceGuardV3 is a secure, decoupled face recognition access control system. It uses an edge-hosted FastAPI backend, a React SPA frontend, and local PostgreSQL storage to recognize registered employees in real time, automatically trigger door unlocking mechanisms, and log all access attempts.

**Scope of this release:** This handover covers the MVP v3 release. It includes background video processing, physical door and LED integration via GPIO, duplicate registration prevention, and a fully persistent local database.

## 2. Handover Status and Ownership

### Transition Status

| Attribute | Value |
|:---|:---|
| **Transition Outcome** | `Ready for independent use` |
| **Customer Confirmation Status** | `Accepted` |
| **Deployment Responsibility** | Customer (Raspberry Pi 5) |
| **Repository Ownership** | Team (retained) |
| **Documentation Sufficiency** | Confirmed sufficient by customer |

Detailed confirmation evidence, the meeting date, and the customer's exact feedback are recorded in `reports/week6/sprint-review-summary.md` and, if recorded, the transcript. This file only reflects the resulting status.

### Why Full Transition Was Not Reached

**Current level:** `Ready for independent use`

**Why not `Independently used by customer` or `Deployed or operated on customer side`:**
- The system is deployed on customer hardware, but formal independent use has not yet been observed
- Actual production usage will begin after handover
- This is acceptable for the current course scope

**Remaining actions needed:** None blocking. Follow-up items are non-blocking enhancements, see Section 7.

### Ownership and Access Transfer

| Asset | Owner after handover | Notes |
|:---|:---|:---|
| Source code (GitHub) | Team (retained) | Customer has read access |
| Deployed product | Customer | Raspberry Pi 5, local deployment |
| Admin credentials | Customer | Managed in `.env` file |
| Hardware (camera, door, LEDs) | Customer | Pre-existing hardware |
| Database (PostgreSQL) | Customer | Local, operated on Raspberry Pi |
| Documentation | Customer | Public repository and hosted docs |
| Future support | Team | Critical fixes only, until course completion |

## 3. Configuration and Secrets Management

To operate the system, the customer must manage the runtime environment variables securely. No secrets are committed to the repository.

### Required Environment Variables

Create a `.env` file in the `backend/` directory (copy `backend/.env.example` as a starting point). The following keys are required:

- `ADMIN_USERNAME`: the username required to log into the React admin panel
- `ADMIN_PASSWORD`: the password for the admin account
- `DATABASE_URL`: connection string for the local PostgreSQL instance, for example `postgresql://postgres:postgres@db:5432/faceguard`

Ensure the `.env` file has restricted read permissions on the Raspberry Pi so that unauthorized users cannot extract the admin credentials.

## 4. Setup, Deployment, and Verification

FaceGuardV3 relies entirely on Docker, simplifying the deployment process.

### Initial Setup on Raspberry Pi 5

1. Install Docker and Docker Compose on the Raspberry Pi.
2. Clone the repository: `git clone https://github.com/Innopolis-Robotics-Society/FaceGuardV3.git`
3. Configure your secrets: `cp backend/.env.example backend/.env` and edit it.
4. Start the system: `docker compose -f docker/docker-compose.yml up -d --build`

### Verification Steps

1. **Access the UI:** open a web browser on a device connected to the same local network and navigate to `http://<RASPBERRY_PI_IP>:3000`.
2. **Login:** enter the credentials specified in your `.env` file.
3. **Hardware check:** register a test user. The connected LEDs should cycle colors (yellow, red, blue), confirming the GPIO module is functioning.

### System Recovery

- Restart services: `docker compose -f docker/docker-compose.yml restart`
- View logs: `docker compose -f docker/docker-compose.yml logs --tail 100`

## 5. Operational Notes for Normal Use

- **LED feedback logic:**
  - Yellow, blinking: system is actively attempting to recognize a face
  - Yellow, solid 5s: bad frame or poor lighting, user must look straight ahead
  - Blue, solid 5s: access granted, door unlock signal sent
  - Red, solid 5s: access denied, face not recognized
- **Temporary access auto-expiry:** employees with temporary access are validated against their start and expiration dates. Access is automatically denied outside this window, no admin action needed.
- **Log management:** access logs are retained in the local database. The system automatically prunes logs older than 3 days to preserve storage on the Raspberry Pi.

## 6. Documentation Entry Points

For normal customer use, operation, and troubleshooting, refer to:

- [Main README](../README.md): primary entry point and setup instructions
- [Hosted Documentation Site](https://innopolis-robotics-society.github.io/FaceGuardV3/): full project documentation
- [Contributor Guide](../CONTRIBUTING.md) and [Agents Guide](../AGENTS.md): guidelines for team members and AI agents
- [System Roadmap](roadmap.md): product evolution up to `MVP v3`
- [User Acceptance Tests](user-acceptance-tests.md): step-by-step instructions for admin panel usage

## 7. Remaining Actions and Known Limitations

**Follow-up items (non-blocking):**

- Fix occasional page freeze during recognition
- Add form validation for temporary access dates, prevent past dates
- Continue performance optimization for Raspberry Pi
- Add a dedicated documentation page with function descriptions (nice to have)

**Known limitations and customer-side responsibilities:**

- **Physical door wiring:** the software fully supports and sends the automated door unlocking signal via Raspberry Pi GPIO 14. The customer must physically wire the laboratory's electronic door relay to this pin.
- **Lighting sensitivity:** the recognition model's accuracy degrades in low lighting. The deployment area must be well lit.
- **Thermal management:** running the system continuously on the Raspberry Pi without active cooling may cause thermal throttling.
