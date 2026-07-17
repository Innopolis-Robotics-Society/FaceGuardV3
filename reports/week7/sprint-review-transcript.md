# Sprint Review Transcript — Sprint 5, Week 7  

**Date:** 16.07.2026  
**Participants:** Development team, Customer  

Before recording started, the team requested permission to record the meeting and to publish a sanitized English transcript in the public repository. The customer agreed to both. Since UAT and transition discussion were conducted during the same session, the recording permission covers the Sprint Review, UAT execution, and transition discussion.  

(00:00)  
**Interviewer:** The login and password can be changed at any time. If you want, we can change them now. The instructions explain the required command.  
**Customer:** Okay.  

(00:35)  
**Interviewer:** We generate the password hash and place it in the backend. The password is always stored as a hash.  
**Customer:** Great. Well done.  

(01:05)   
**Interviewer:** The login can also be changed easily. For now, we will keep the default credentials.  

(01:35)  
**Interviewer:** After restarting the website, five incorrect password attempts trigger a one minute lockout. During that time, even the correct password will not work.  

(02:15)  
**Interviewer:** There are currently no employees registered, so we will create the first one.   
**Customer:** Go ahead.  

(03:05)  
**Interviewer:** Registration is slower on the Raspberry Pi. On a laptop it takes only a few seconds. The camera resolution is 640 by 480 because lower values reduce recognition accuracy.  

(04:20)   
**Customer:** Can these parameters be changed?  
**Interviewer:** Yes, they can be adjusted.  

(05:10)  
**Interviewer:** Temporary access can only be assigned for the future. Past dates are rejected by validation.  

(06:05)  
**Interviewer:** During recognition, the blue light indicates face detection. If the user is not looking directly at the camera, the system may fail to create a high quality face embedding.  

(07:15)  
**Interviewer:** We can also test accessories. Glasses are recognized correctly, but masks are intentionally rejected for security reasons.  

(08:25)  
**Interviewer:** If someone presents a photograph instead of a real face, the system will not register it.  

(09:15)  
**Interviewer:** Temporary access can also be granted for a specific future date and time.  

(10:05)  
**Interviewer:** Here is the employee list. Sorting, search, and activity logs are available. The last access time is also displayed.  

(11:10)  
**Interviewer:** Recognition with glasses works correctly. Masks are not supported because they significantly distort the facial embedding.  

(12:15)  
**Interviewer:** Let us demonstrate the login protection. After five failed attempts, the system blocks authentication for one minute.  

(13:20)  
**Interviewer:** Here is the documentation. It explains authentication, registration, recognition status colors, and deployment steps. Both light and dark themes are available.   

(14:25)  
**Interviewer:** Overall, the requested improvements have been completed. The date validation works, and the black screen issue during registration has been reduced. Performance on the Raspberry Pi is better.  

(15:30)  
**Interviewer:** We optimized the system as much as possible within the hardware limitations.  

(16:00)  
**Interviewer:** Are you already able to use the system independently without our team's assistance?  
**Customer:** Yes.  

(16:18)  
**Interviewer:** Is the system already deployed in your own environment?  
**Customer:** Not yet.  

(16:35)  
**Interviewer:** Do you consider the current version sufficient to manage the system independently in the future?  
**Customer:** Yes.  

(16:55)  
**Interviewer:** Is there anything preventing you from taking full control of the system now?  
**Customer:** No.  

(17:10)  
**Interviewer:** Do you accept this as the final delivered product?  
**Customer:** Yes.  

(17:25)  
**Interviewer:** Is there anything else that should be added or changed?  
**Customer:** No, everything is as expected.  
**Interviewer:** Thank you very much. [inaudible]  
