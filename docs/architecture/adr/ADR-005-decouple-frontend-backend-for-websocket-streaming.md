# ADR-005: Decouple Frontend and Backend for WebSocket Streaming

**Date:** 2026-07-09

## Status
Accepted

## Context
The FaceGuardV3 MVP was initially built as a monolithic Streamlit application. While Streamlit allowed rapid UI prototyping, it suffered from severe performance issues when applied to real-time face recognition. Streamlit's architecture requires re-executing the entire Python script and reloading the page state on every frame processed (via `st.rerun()`). This resulted in a bottleneck where the UI could not keep up with the backend model, causing significant lag, flickering, and end-to-end response times frequently exceeding the 3.0-second limit defined in **QR-001**. Furthermore, capturing video server-side via OpenCV tied the UI rendering and the ML inference to the same process loop, exacerbating the performance issues.

## Decision
We decided to completely decouple the presentation layer from the backend application logic. The architecture now consists of:
1. **React Frontend (Vite)**: A lightweight Single Page Application that handles presentation and captures video natively in the browser via WebRTC.
2. **FastAPI Backend**: A high-performance asynchronous Python server that exposes REST endpoints for data management and a WebSocket endpoint for real-time video streaming.

Instead of processing video server-side, the React client captures frames and streams them as base64-encoded strings over WebSockets to the FastAPI server. The server performs the face extraction and matching asynchronously and immediately returns the result JSON over the same WebSocket.

## Consequences

**Positive:**
- **Response Time (QR-001)**: Solves the UI rendering bottleneck. Warm recognition inference now takes ~1.1s and UI updates happen instantly (~1ms transmission over local network) without page reloads.
- **Scalability**: Decoupling the frontend allows the system to easily support multiple remote clients or edge displays in the future.
- **Maintainability**: The separation of concerns is much clearer. ML logic and database access are strictly isolated from UI rendering.

**Negative:**
- **Complexity**: The development team now has to maintain two distinct codebases with two different technology stacks (Python/FastAPI and Node.js/React).
- **Deployment Overhead**: Requires orchestrating multiple Docker containers (`docker-frontend` and `docker-backend`) instead of a single monolith.

## Quality Requirements Addressed
- **QR-001: Recognition Response Time**: Sub-3-second end-to-end latency achieved by eliminating Streamlit's polling constraints.
