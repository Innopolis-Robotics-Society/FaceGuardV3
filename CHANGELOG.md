# Changelog

All notable changes to FaceGuard will be documented in this file.

## [Unreleased]

## [2.2.0] - 2026-07-12  

### Added
- Connection of the system and the door
- Recognition with accessories
- Permanent login and password for the admin
- Running recognition in the background

### Changed
- The speed of the system's response

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
[2.2.0]: https://github.com/Innopolis-Robotics-Society/FaceGuardV3/compare/v2.2.0...v2.1.0  
