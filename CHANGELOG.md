# Changelog

## [0.2.0](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v1) - 15.06.2026 - MVP v1

### Added
- Face recognition using InsightFace (buffalo_l model)
- Camera integration using OpenCV
- Face embedding generation and storage in employee database
- Face recognition test page with live camera feed and confidence score
- Docker containerization for x86 and ARM deployment
- Temporary access with start and end date selection

## [0.1.0](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/releases/tag/v0) - 08.06.2026 - MVP v0

### Added
- Authentication page for admin login with login and password
- Add Employee page with photo capture, name input, and access type selection
- Remove Employee functionality from the employees list
- Employees page showing all registered users with search and sort
- Access Logs page showing all access attempts with timestamp and status
- PostgreSQL database for employee storage (ID, name, registration date, access type)
- PostgreSQL database for logs storage (ID, name, timestamp, status)
- Automatic deletion of logs older than 3 days
- Local setup instructions in root README.md

### Changed
- Temporary access input changed from number of days to date range picker
