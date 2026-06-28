# Customer Review Transcript

**Date:** 2026-06-27  
**Participants:** Development team, Customer

**(00:00)**  
**Interviewer:** All permissions have been granted. I suggest we start checking what we have already done. I can say that we also tested it on the Raspberry Pi last night — everything worked and loaded correctly. For now we are testing locally. We have not reached the lab yet, as the Raspberry Pi is currently in use.

**(01:06)**  
**Interviewer:** I launched everything. We register, enter the password. We verify that everything loads correctly and the password matches. We now have the list of employees. I will delete myself right away.

**(01:32)**  
**Interviewer:** I will delete myself to demonstrate the registration flow.

**(01:57)**  
**Customer:** Okay.

**(01:58)**  
**Interviewer:** Okay. Let's start — does the employee page satisfy what you want, or not?

**(02:19)**  
**Customer:** Can I change names and status here?

**(02:46)**  
**Interviewer:** We cannot change names and status at the moment — to do that, the user would need to be re-registered. The username is set at registration and stays assigned to that entry.

**(03:28)**  
**Customer:** Ideally, you should be able to change the name after registration and also change the status — for example, from temporary to permanent and vice versa. Otherwise, it looks good.

**(03:35)**  
**Interviewer:** Noted, we will fix that. I suggest we move on to registration. Here we can select a camera — I only have one, a local one. We enter the username, for example, Maxim. We have already taken into account your feedback regarding temporary registration.

**(04:08)**  
**Interviewer:** Now it works with dates — a start date and an end date. Let's set the end to tomorrow. We are starting the registration session. We also took into account your feedback about using multiple frames. We collect 30 frames and generate an average embedding from them.

**(04:30)**  
**Interviewer:** The session will load now. During registration, we need to turn our head a little so the system captures as much variation as possible.

**(05:02)**  
**Interviewer:** Registration was successful. We are saving the user. How do you like the registration window? Is everything okay?

**(05:32)**  
**Customer:** Okay, but I would like date control down to minutes, not just days.

**(05:41)**  
**Interviewer:** Understood. I can also show permanent registration — it is not much different from temporary. If a user registers without glasses, they can still be recognized when wearing glasses.

**(06:29)**  
**Customer:** By the way, what happens if I try to register the same person twice?

**(06:53)**  
**Interviewer:** There will just be two entries for that person. For example, I have a temporary entry with glasses and a permanent one without. The system will most likely switch between recognizing one version of me and the other. We can actually test that now with face recognition. We start the session and select the camera.

**(07:22)**  
**Interviewer:** We start the recognition session. At first it may show access denied because the first frame is still being processed — after that everything works fine.

**(07:41)**  
**Interviewer:** So right now it recognizes me without glasses. If I put on glasses, it will probably recognize the other version of me.

**(07:53)**  
**Customer:** Nice to have in the future — a check that the person is already in the system. If you have time, it would be great to implement that.

**(07:58)**  
**Interviewer:** Good, we will add a check so that a person already in the system cannot be registered twice. I will also mention the frame rate — the system is under a lot of load, and we know the Raspberry Pi has limited performance. The video stream on the site has some stuttering. This is intentional, to reduce the load, since the recognition session runs in the background anyway. It is not important to see the stream in real time — running it at full quality would be too heavy for the Raspberry Pi.

**(08:46)**  
**Interviewer:** Right now it is optimized so that it can run for at least two hours. Let me show you Spoof Detection. I have a photo here.

**(09:05)**  
**Interviewer:** It displays a Spoof Detection notification and does not let the user in. All of this is also saved in the logs. What do you think about the recognition page? What would you like to change or improve?

**(09:41)**  
**Customer:** Great, you managed to implement anti-spoofing after all.

**(09:45)**  
**Interviewer:** We did, although it took quite a bit of time. We also implemented live recognition — you no longer need to press the Take Photo button manually.

**(09:57)**  
**Customer:** What FPS is planned for the Raspberry Pi?

**(10:02)**  
**Interviewer:** To reduce the load, the system is set to extract and analyze one frame per second. First it checks whether a face is present, then runs Spoof Detection. Only if a face is found and there is no spoofing does it compare against the database.

**(10:22)**  
**Customer:** So, 1 FPS?  
**Interviewer:** More or less, yes — 1 FPS, because it cannot handle more than that. At higher frame rates, the video quality drops significantly and the face can no longer be recognized reliably.

**(10:39)**  
**Customer:** Have you tested it?

**(10:42)**  
**Interviewer:** Yes, we have already tested it on the Raspberry Pi with an external camera.

**(11:00)**  
**Interviewer:** I suggest we look at the logs page.

**(11:15)**  
**Customer:** Okay, is it possible to raise it to 2 or 3 frames? Or is that too much?  
**Interviewer:** I tried, but at some point the system cannot handle it. It starts to freeze and after about a minute it can no longer recognize faces.

**(11:30)**  
**Interviewer:** We will try to find ways to optimize further.

**(11:54)**  
**Customer:** Try to find the upper bound. I would still like it to fit within 3 to 5 seconds, ideally less — but well done anyway.

**(11:57)**  
**Interviewer:** There is a significant delay when the request is sent from the backend. The recognition itself is a bit faster. We tried to reduce all possible load — we also removed the face bounding box overlay in recognition to reduce the processing load on the Raspberry Pi.

**(12:26)**  
**Interviewer:** We also switched to a lightweight recognition model, because the buffalo-l model was much slower — it used to take up to eight seconds. The analysis step was taking most of the time. We will keep trying to improve it so the Raspberry Pi does not overload.

**(13:03)**  
**Customer:** Okay, are there lighter models available? Are there any documented tests or comparisons?  
**Interviewer:** There is no lighter model than buffalo-S available. There is only SL, but it is almost identical in performance. The SL model lacks full embedding comparison capabilities, so it would not be suitable. We have installed the most lightweight model that still maintains acceptable recognition quality. Performance comparison results are recorded in the logs.

**(13:53)**  
**Interviewer:** I can go to the logs page. Here are the different statuses.

**(14:22)**  
**Interviewer:** We will clean this up later — it is still under development. Right now a log is created for every recognition event. By the end of development, we will remove the redundant ACCESS_GRANTED entries that appear when a person stands in front of the camera for a long time.

**(14:49)**  
**Customer:** Will there be search and filtering for the logs?  
**Interviewer:** There is already sorting and search — it is above the status column.

**(15:37)**  
**Interviewer:** I also suggest testing the case when the user is not registered. I will go to the employees tab and delete myself.

**(15:51)**  
**Customer:** Ideally, there should be good date filtering so you can select a range.

**(16:06)**  
**Interviewer:** We will add date range filtering. We were originally planning to keep logs only for the last 72 hours, after which they are automatically deleted.

**(16:27)**  
**Interviewer:** Yes, within 72 hours.

**(16:35)**  
**Interviewer:** Employees have sorting by registration status and search. Let us return to the recognition page and start the session.

**(17:03)**  
**Interviewer:** It shows Access Denied for me. If I try to spoof as well, it will also reject me.

**(17:47)**  
**Customer:** When the employee list is open, I would like to see the last time each user entered.  
**Interviewer:** Understood, we will add that.

**(18:02)**  
**Interviewer:** I think we have covered all the pages. Are there any other additions?

**(18:23)**  
**Customer:** Probably not for now — I have said everything I found.

**(18:30)**  
**Interviewer:** In that case, thank you. We have reviewed all the user-facing functionality.

**(18:58)**  
**Interviewer:** This week we achieved the Sprint Goal: we deployed the system on Raspberry Pi 5, switched to a lightweight model, implemented automatic recognition without a button press, and added Spoof Detection. I also want to highlight the quality improvements made this sprint. We set up the CI pipeline with automated tests — all 28 tests passed and coverage is at 41% for the faceguard package. CI also includes linting, formatting checks, and a Bandit security scan. These checks are now mandatory for every PR and will remain active in all following sprints.

**(19:23)**  
**Customer:** Hardware question: have you already worked with the Raspberry Pi GPIO?  
**Interviewer:** What do you mean exactly? Have we tested the full system on the Raspberry Pi?

**(20:10)**  
**Customer:** I mean, have you started developing the feature that signals the system state — access granted, denied, or registration — using an LED and a motor?  
**Interviewer:** Understood. We have started work on the LED integration and plan to work on it more thoroughly next week, along with the motor.

**(21:03)**  
**Interviewer:** This week we installed the lightweight model, connected the entire system to it, and fixed the issue where video recognition would crash after a minute due to dropped frames. We fixed that and worked on maintaining a consistent image quality. We also improved Spoof Detection — it was not working correctly before, but now it reliably detects when someone tries to deceive the system using a photo on a phone. We also addressed the registration feedback and generally sped up the process.

**(21:58)**  
**Interviewer:** We will continue to optimize so that the video stream does not lag too much and recognition runs a bit faster.

**(22:25)**  
**Interviewer:** One question: is it possible to come in this weekend to connect the LEDs in the lab?

**(22:49)**  
**Customer:** Yes, I can come to Innopolis on Sunday and help with that.  
**Interviewer:** Great, thank you. Is any additional lighting planned for where the camera will be placed?

**(23:04)**  
**Customer:** Write to me closer to 5 or 6 in the evening.  
**Interviewer:** Today or tomorrow?

**(23:14)**  
**Customer:** Tomorrow.  
**Interviewer:** Understood.

**(23:17)**  
**Interviewer:** Regarding the camera placement — is any additional lighting planned? There is a risk that the image could be too dark or grayish, which could reduce recognition quality.  
**Customer:** It depends on your tests. If the system needs it, I can provide a set of electronics to set it up.

**(24:03)**  
**Interviewer:** Okay, we will test that as well. The Raspberry Pi needs a constant power supply, so we will need to figure out how to route the wires to the door.

**(24:24)**  
**Interviewer:** To summarize what has been done: employee registration with both permanent and temporary access, employee removal, a logs page, an employees page, a recognition page, access denial for unregistered users, and recognition of registered employees. This is in addition to the feedback items you sent us.

**(24:53)**  
**Interviewer:** What still needs to be improved? Of the remaining risks: performance on the Raspberry Pi does not yet consistently meet the 3-second target, and LED and motor integration is planned for the next sprint. Are there any other suggestions?  
**Customer:** I like everything — I have already given more detailed comments. You are doing great!

**(25:01)**  
**Interviewer:** Thank you. I have no further questions. If any of the team members have questions, feel free to ask.

**(25:23)**  
**Team Member:** I have one question about the resistors for the LEDs. Is everything already available in the lab?

**(25:44)**  
**Customer:** Yes, everything is there — we will find what we need.  
**Team Member:** Perfect, thank you. No more questions from me.

**(25:51)**  
**Interviewer:** Thank you for the meeting. Goodbye.  
**Customer:** Good luck to everyone!ᅠ
