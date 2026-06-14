During the discussion, the customer answered all questions.
Listened to the initial idea.
Made some adjustments, for example:
It was decided to add LED indicators.
Recommended not to consider facial recognition in crowds.
Clarified the camera height and distance.
Approved the need for facial recognition in accessories.
Clarified that the entire system should be deployed and run locally on the customer's device.
The system is based on a Raspberry Pi.
A backup power supply (UPS) is not an option—if the power goes out, the system simply stops.
The entire system is wired (the camera is connected via USB, the admin is connected via SSH).
There is only one administrator; roles cannot be changed.
All actions are logged.
To avoid storage overflow issues, we decided to only store logs for three days.
