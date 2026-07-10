# ADR-006: Local PostgreSQL Database for Offline Reliability

## Context

Originally, the FaceGuardV3 system utilized a serverless cloud PostgreSQL database (Neon.tech on AWS) to store employee data, embeddings, and access logs. While this simplified local setup and removed the need for database administration, it introduced a significant deployment constraint: the system required a continuous, stable internet connection to function. If the edge device (Raspberry Pi) lost internet connectivity, it could not authenticate users, resulting in total system failure at the physical entry point.

Furthermore, relying on a cloud database meant storing sensitive access logs and biometric embedding representations in an external system, which could raise privacy concerns. 

## Decision

We have decided to migrate from a cloud-hosted database to a **local PostgreSQL database** running as a Docker container directly on the edge device. 

Specifically:
- We added a `db` service (`postgres:15-alpine`) to the `docker-compose.yml` file.
- We replaced hardcoded credential files (`secrets.toml`) with standard Docker environment variables (`.env`).
- State is now persisted locally via a named Docker volume (`pgdata`).

## Consequences

### Positive
- **Full Offline Capability:** The system can now operate 100% locally. Internet outages at the lab will no longer prevent employees from entering.
- **Improved Latency:** Database queries (especially fetching embeddings and writing logs) are now executed over the local Docker network rather than over the public internet, reducing the overall access-decision response time.
- **Increased Privacy:** All biometric representations and access logs remain on the edge device.

### Negative
- **Local Storage Management:** The system now consumes local storage on the Raspberry Pi for the database volume. Administrators must ensure the SD card or attached storage has sufficient space and is backed up properly.
- **Data Synchronization:** If multiple FaceGuard instances are deployed in the future, they will each have their own isolated local database, requiring an additional synchronization mechanism if central management is needed.
