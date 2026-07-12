# Sprint Review Transcript — Sprint 4, Week 6

**Date:** 10.07.2026
**Participants:** Development team, Customer

Before recording started, the team requested permission to record the meeting and to publish a sanitized English transcript in the public repository. The customer agreed to both. Since UAT and transition discussion were conducted during the same session, the recording permission covers the Sprint Review, UAT execution, and transition discussion.

(00:00)  
**Interviewer:** Here is the instruction. What needs to be done? Login and password. Login is admin, all lowercase. The password is the same as the username. Further down is the registration instruction.

**Customer:** Okay.

(00:36)  
**Interviewer:** Here I am. [inaudible]

(00:57)   
**Customer:** Better through the calendar. I specifically took it so that... Seriously? Yes. You could have returned to the previous state. [inaudible]

(01:28)  
**Interviewer:** It is running for 60 seconds. Wait, no. I gave myself temporary access. I set it for tomorrow. There is a moment where it might deny access, so it needs to be time-based. Okay, I have a large availability window.

(02:17)  
**Customer:** What is the face recognition threshold? The threshold for minimum recognition is 56. That is what the system generally recognizes. Why that number? Because it takes the average embedding and we tried to combine embeddings together, so several registrations are under one profile. And it recognizes approximately.

(02:44)  
**Interviewer:** You can try to enter the conditional page without stopping. Now I can enter the frame. What do you mean? This is super. What else needs to be done?

(03:11)  
**Customer:** Please register without stopping.

(03:35)  
**Customer:** Okay, good, thank you.

(04:18)  
**Interviewer:** Sometimes the load is too high. We need to not consume too much memory. Yes. There will be a next page.

(04:51)  
**Customer:** [inaudible]

(05:19)  
**Customer:** Yes. Most likely this is because parallel processing is already running. But it should stop. When recognition is running, it stops the first process and starts the second. Okay, write it down then.

(06:10)  
**Interviewer:** How clear were the interfaces? Could you figure it out? You can delete someone right away. Yes. Sorting works well. What could be improved? What did you like?

(06:35)  
**Interviewer:** What did you not like? Sometimes the stream does not capture properly. Loading on Raspberry Pi can be slow, but this is rather a minor issue. If you can fix it, that would be great. Otherwise everything is fine.

(07:06)  
**Customer:** What is the overall project stage? Is it ready to transfer? Not yet fully. If running locally, yes, it is ready. The system works, right? How much does the application and database weigh in total?

(07:43)  
**Interviewer:** We have not measured it. By estimation, as far as I remember, the models weigh about a gigabyte, maybe one and a half. I cannot say exactly. There is an interesting improvement for vector compression.

(08:13)  
**Customer:** But that is probably unnecessary. Anyway, I like it, it works. I see and believe. Tomorrow or Sunday evening. Good. Overall, you are doing well.

(08:46)  
**Interviewer:** This week we implemented speeding up the site overall. We rewrote the streaming part to a separate frontend. We added background recognition, so when a session starts, you can freely navigate between pages and everything continues to work. We also added...

(09:20)  
**Interviewer:** We migrated the database from the cloud to local storage, which also improved site performance. Now everything runs locally. Did you have a cloud database? Yes, we used to send it there. Do not do that. No external databases. No cloud resources. Everything must be stored only on the hardware. Now everything is stored locally, we cleaned everything up. Good. This week we accelerated the site, rewrote it, and added background recognition. We were ready to add a door, but the door is essentially the LEDs.
 
(10:18)  
**Customer:** Yes. No further requirements are needed. What will you work on next? You mentioned a bug. Yes, I will try to fix the occasional page freeze.

(10:40)  
**Interviewer:** I will also add a form with validation so that past dates cannot be set. For example, you cannot give temporary access starting from July 8. Only today's date and time will be allowed as the minimum threshold.

**Customer:** Okay.

(11:08)  
**Interviewer:** We will continue optimizing everything to ensure it works well on the Raspberry Pi. Next week we want everything to work reliably. An additional task from me is to clean up the repository, add documentation, and if possible build static documentation with all the ideas, that would be great.

(12:07)  
**Interviewer:** The main register is there, it will be updated. We have instructions there. We will add all the information.

(12:14)  
**Interviewer:** Should I log into it?

(12:24)  
**Interviewer:** Now it will load. Strange that this link points to the repository and the organization itself. You can log in and see. It turned out interesting.

(12:52)  
**Interviewer:** Ah, yes. Below my...

(13:11)  
**Interviewer:** I want a wiki page to appear that describes the functions and everything. You can look.

(13:30)  
**Interviewer:** Okay. Then go back. Can we? Yes, of course.

(14:03)  
**Interviewer:** I will not take it. A couple of pages describing the main functions and how everything works. Essentially supporting documentation. If you take it on, that would be great.

(14:30)  
**Customer:** For the rest, finish everything so that it works. That would be great. Thank you very much. If you want to keep working until next year. Some others also wanted to.
