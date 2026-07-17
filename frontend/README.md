# FaceGuardV3 frontend

React/Vite SPA for FaceGuardV3. Runtime API/WebSocket helpers use the page hostname and backend port `8000` by default. `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`, and `VITE_CAMERA_SOURCE` are build-time settings; copy `.env.example` to `.env.local` for standalone development.

```bash
npm ci
npm run dev
npm test
npm run lint
npm run build
npm audit --audit-level=high
```

`browser` mode uses `getUserMedia` and sends at most one JPEG while awaiting a response. `backend` mode requests no browser camera and displays JPEGs returned by FastAPI. WebSockets authenticate with subprotocols; do not add a JWT query parameter.
