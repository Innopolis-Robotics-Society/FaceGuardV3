# ADR-005: Decouple Frontend and Backend for WebSocket Streaming

**Date:** 2026-07-09

## Status
Accepted

## Context
The FaceGuardV3 MVP was initially built as a monolithic Streamlit application. While Streamlit allowed rapid UI prototyping, it suffered from severe performance issues when applied to real-time face recognition. Streamlit's architecture requires re-executing the entire Python script and reloading the page state on every frame processed (via `st.rerun()`). This resulted in a bottleneck where the UI could not keep up with the backend model, causing significant lag, flickering, and end-to-end response times frequently exceeding the 3.0-second limit defined in **QR-001**. Furthermore, capturing video server-side via OpenCV tied the UI rendering and the ML inference to the same process loop, exacerbating the performance issues.

## Decision
We decided to completely decouple the presentation layer from the backend application logic. The architecture now consists of:

1. **React Frontend (Vite)**: A lightweight Single Page Application that handles presentation. In `browser` mode it captures video natively through WebRTC; in `backend` mode it only renders JPEG preview frames and recognition metadata received from the server.
2. **FastAPI Backend**: An asynchronous Python server that exposes REST endpoints and authenticated WebSocket endpoints. In `backend` mode it is the sole owner of the Raspberry Pi USB camera and captures `/dev/video0` through V4L2.

The selected mode is explicit at deployment time (`CAMERA_SOURCE` for FastAPI and the build-time `VITE_CAMERA_SOURCE` for Vite). In browser mode, the client sends captured JPEG frames over the WebSocket. In backend mode, the client does not call `getUserMedia`; the server keeps only the latest captured frame, performs inference without building a frame queue, and returns the JPEG preview, `[x1, y1, x2, y2]` bounding box, and source frame dimensions over the same WebSocket.

## Consequences

**Positive:**
- **Response Time (QR-001)**: Removes Streamlit page reruns and permits latest-frame-only buffering so stale camera frames are discarded instead of accumulating.
- **Scalability**: Decoupling the frontend allows the system to easily support multiple remote clients or edge displays in the future.
- **Maintainability**: The separation of concerns is much clearer. ML logic and database access are strictly isolated from UI rendering.
- **Remote operation**: Backend camera mode always uses the camera attached to the Pi, even when the UI is opened from a workstation through SSH forwarding.

**Negative:**
- **Complexity**: The development team now has to maintain two distinct codebases with two different technology stacks (Python/FastAPI and Node.js/React).
- **Deployment Overhead**: Requires orchestrating multiple Docker containers (`docker-frontend` and `docker-backend`) instead of a single monolith.
- **Hardware mapping**: Backend camera mode requires explicit access to `/dev/video0`; GPIO access on current Raspberry Pi OS requires `/dev/gpiochip0`. Neither mapping requires a privileged container.

## Quality Requirements Addressed
- **QR-001: Recognition Response Time**: Sub-3-second end-to-end latency achieved by eliminating Streamlit's polling constraints.
