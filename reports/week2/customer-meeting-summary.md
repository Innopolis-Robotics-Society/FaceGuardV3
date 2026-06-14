Date: 12.06.26.  
Participants: ixkci (interviewer), oebarbie (note taker), s0ftach (observer), ns3dx (note taker), grex861 (recorder).  
Artifacts demonstrated: [user-stories.md](user-stories.md), initial proposed MVP v1 scope (US-01–US-05).  
Discussion points: 
  1. LED indicators;
  2. Facial recognition in crowds;
  3. Camera height and distance;
  4. Facial recognition in accessories;
  5. Deployment and running locally on the customer's device;
  6. System based on a Raspberry Pi;
  7. Backup power supply (UPS);
  8. Wired system (camera via USB, admin via SSH);
  9. Single administrator, roles cannot be changed;
  10. Logging of all actions;
  11. Log storage period (to avoid overflow).  

Decisions: It was decided to add LED indicators, recommended not to consider facial recognition in crowds (but the system could have such feature), clarified the camera height and distance, approved the need for facial recognition in accessories, clarified that the entire system should be deployed and run locally on the customer's device. A backup power supply (UPS) is not an option (if the power goes out, the system simply stops). The entire system is wired (the camera is connected via USB, the admin is connected via SSH). There is only one administrator; roles cannot be changed. All actions must be logged. To avoid storage overflow issues, we decided to only store logs for three days.  

Action points: 
  1. Implement LED indicators;
  2. Remove/ignore facial recognition in crowds from scope;
  3. Implement facial recognition with accessories;
  4. Ensure entire system runs locally on customer's device;
  5. Set up system on Raspberry Pi;
  6. Enforce single administrator with fixed role;
  7. Implement logging of all actions;
  8. Configure log retention to 3 days.  

Risks: storage overflow, power loss causes system to stop.  
Feedback: the customer answered all questions, listened to the initial idea, made some adjustments, for example, recommended not to consider facial recognition in crowds, clarified the camera height and distance, approved the need for facial recognition in accessories, clarified that the entire system should be deployed and run locally on the customer's device, notified about the absence of an uninterruptible power supply.  
Customer approvals: [user-stories.md](user-stories.md), initial proposed MVP v1 scope (US-01–US-05).  
Resulting changes: added LED indicators to the design, removed facial recognition in crowds from scope, updated camera placement parameters, decided that logs will be stored only for 3 days.
