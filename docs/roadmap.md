# Roadmap

## Sprint 1 (MVP v1) — June 15–21, 2026
- **Milestone:** [Sprint 1](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/milestone/1)
- **Sprint Goal:** Deliver a working face recognition system with temporary registration and full Docker deployment, ready to run without manual setup
- **Focus:** Face recognition, Docker, admin panel, database
- **Items:**
  - [#PBI: Add OpenCV for image processing and InsightFace](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/62),
  - [#PBI: Implement embedding adding](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/63),
  - [#PBI: Add a page for testing face recognition](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/55),
  - [#PBI: Containerize the application](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/56)

## Sprint 2 (MVP v1) — June 22–28, 2026
- **Milestone:** [Sprint 2](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/milestone/2)
- **Sprint Goal:** Improve recognition speed and reliability by switching to a lightweight model, enabling video-based face enrollment, adding liveness detection, and deploying to Raspberry Pi 5.  
- **Focus:** Hardware integration, Raspberry Pi, camera, liveness detection, recognition speed
- **Items:**
  - [#PBI: Switch to a lightweight recognition model](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/86),
  - [#PBI: Add automatic face recognition without button press](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/87),
  - [#US-010: Liveness detection](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/49),
  - [#US-007: Add temporary access](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/46),
  - [#PBI: Improve face adding using video instead of single photo](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/59),
  - [#PBI: Set up Raspberry Pi 5 environment and connect it to web-camera](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/58),
  - [#PBI: Change design for temporary registration](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/57)

## Sprint 3 (MVP v2) — June 29 – July 5, 2026
- **Milestone:** [Sprint 3](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/milestone/3)  
- **Sprint Goal:** Improve system visibility through status LED indicators and deliver customer-requested improvements from the last review.  
- **Focus:** LEDs connection, employee management improvements from customer feedback  
- **Items:**
  - [#Bug: excessive addition of logs](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/144)
  - [#PBI: Add a check to see if a person is already registered in the system](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115),
  - [#PBI: Remove test section from the recognition page](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/152),
  - [#US-008: Notification](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/47),
  - [#PBI: Set up LEDs](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/60),
  - [#PBI: Change employee's name and status after registration](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113),
  - [#PBI: Add the time of the employee's last entry](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114),
  - [#PBI: Add filtering logs by date range](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116),
  - [#PBI: Change the provision of temporary access](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117),

## Sprint 4 (MVP v2) — July 6-12, 2026
- **Milestone:** TBD
- **Sprint Goal:** Finalize local deployment stability and improve recognition accuracy.
- **Focus:** Accessories, recognition accuracy, offline capabilities
- **Items:**
  - [#PBI: Migrate from cloud NeonDB to local PostgreSQL Docker database for offline stability](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/196)
