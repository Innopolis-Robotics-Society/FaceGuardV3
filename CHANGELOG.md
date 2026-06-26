# Changelog

All notable changes to FaceGuard will be documented in this file.

## [Unreleased]

## [2.0.0] - 2026-06-28  

### Added
- Liveness Detection to prevent spoofing via photos or videos
- Automatic face recognition without button press on the "Recognition" page
- Deployment to Raspberry Pi 5 and connection to the web-camera

### Changed
- Replaced buffalo_l model with a lightweight alternative for faster recognition and improved UI responsiveness
- Temporary registration now uses start and expiration date pickers instead of a number-of-days input
- Design for Recognition page and Add Employee page: added camera selector and switched from single photo capture to video frame extraction

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
/* [2.0.0]: https://github.com/Innopolis-Robotics-Society/FaceGuardV3/compare/v1.0.0...v2.0.0? */
