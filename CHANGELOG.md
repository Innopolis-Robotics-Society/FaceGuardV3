# Changelog

All notable changes to FaceGuard will be documented in this file.

## [Unreleased]

### Added
- Dual browser/backend camera modes with a single latest-frame backend capture loop and no stale-frame queue
- Validated, retry-bounded InsightFace `buffalo_s` bootstrap into the persistent model cache
- Automated QRT-005 through the FastAPI boundary and isolated PostgreSQL, including concurrent duplicate-registration prevention
- Frontend behavior tests and per-critical-backend-module coverage gates in CI

### Changed
- WebSocket JWT authentication now uses subprotocols instead of URL query parameters
- Recognition/enrollment are serialized and frame responses correlate JPEG, bounding box, dimensions, and sequence
- Backend-camera streams record aggregate capture, frame-age, inference, encoding and send timings without logging frame or credential data
- GPIO feedback is generation-safe, configurable by gpiochip, tolerant of unavailable hardware, and cleaned up at shutdown
- Deployment, architecture, QRT, DoD, testing, and customer instructions now describe the implemented system and hardware-evidence limits

### Fixed
- Duplicate similarity check and insert now execute atomically and roll back without changing the existing employee
- Enrollment now maps spoof, bad-frame, no-face, valid-sample, and completion states to the documented LED feedback
- Database pool connections are rolled back after an exceptional context exit before being returned to the pool
- Frontend container builds now exclude host `node_modules`, build output, logs, and private environment files from the Docker context
- Camera, GPIO, background task, and database-pool resources are released during normal shutdown and error paths
- Docker Hub image now starts the FastAPI backend instead of the removed Streamlit application

## [3.0.0] - 2026-07-12  

### Added
- Decoupled React frontend and FastAPI backend communicating via WebSockets for real-time video streaming
- Recognition runs efficiently in the background without blocking the UI
- LED access indication (no physical door actuator is included)
- Recognition with accessories
- Extensive customer handover documentation and contributor guides

### Changed
- Sped up system response time by eliminating Streamlit UI polling bottlenecks
- Improved local database setup for enhanced offline reliability

### Fixed
- Stabilized Docker build process and image sizes

### Removed
- US-011: Recognize in a crowd (removed based on customer feedback; not needed for current scope)

## [2.1.0] - 2026-07-05  

### Added
- LEDs integration to show the system's response: yellow blinks during recognition, blue solid 5s on access granted, red solid 5s on access denied, yellow solid 5s on bad frame
- Edit employee name and status after registration
- Time of employee's last entry shown in the employees list
- Duplicate face check when registering a new employee
- Filtering by date range in access logs

### Changed
- Temporary access now uses exact start and expiration date+time pickers

### Fixed
- Incorrect access granting: expired temporary employees could still be granted access until admin reloaded the Employees page
- Incorrect blocking access was not blocked before start_date for temporary employees
- Moscow Time

## [2.0.0] - 2026-06-28  

### Added
- Liveness Detection to prevent spoofing via photos or videos
- Deployment to Raspberry Pi 5 and connection to the web-camera
- Camera selector on the Recognition page and Add Employee page

### Changed
- Replaced buffalo_l model with a lightweight alternative for faster recognition and improved UI responsiveness
- Temporary registration now uses start and expiration date pickers instead of a number-of-days input
- Recognition page and Add Employee page: switched from single photo capture to video frame extraction
- Recognition session now starts with a Start button on the Recognition page

## [1.0.0] - 2026-06-21  

### Added
- Face recognition using InsightFace (buffalo_l model)
- Camera integration using OpenCV
- Face embedding generation and storage in employee database
- Face recognition test page with live camera feed and confidence score
- Docker containerization for x86 and ARM deployment
- Authentication page for admin login with login and password
- Add Employee page with photo capture, name input, and access type selection
- Remove Employee functionality from the employees list
- Employees page showing all registered users with search and sort
- Access Logs page showing all access attempts with timestamp and status
- PostgreSQL database for employee storage
- PostgreSQL database for logs storage
- Automatic deletion of logs older than 3 days
- Local setup instructions in root README.md


[1.0.0]: https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/1.0.0  
[2.0.0]: https://github.com/Innopolis-Robotics-Society/FaceGuardV3/compare/1.0.0...v2.0.0  
[2.1.0]: https://github.com/Innopolis-Robotics-Society/FaceGuardV3/compare/v2.0.0...v2.1.0  
[3.0.0]: https://github.com/Innopolis-Robotics-Society/FaceGuardV3/compare/v2.1.0...v3.0.0
