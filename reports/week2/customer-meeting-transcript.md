I: Thank you for your time. May we record this interview?
C: Yes, no problem.
I: Let’s start. As an admin, I want to be able to add people to the database to give them access to the laboratory.
C: Yes.

I: As a user, I want my face to be recognized by camera so that I can enter the laboratory.
C: Yes.

I: As an admin, I want to be able to remove people from the database, so that they could not enter laboratory.
C: Yes

I: As an admin, I want to have a database for about 40 people so that I can give access for all laboratory workers
C: Uh-huh.

I: As an admin, I want to have an accurate system so that unknown people would not enter the laboratory
C: Yeah

I: As an admin, I want to be able to temporary add person so that I can give temporary access to someone.
C: Yes. What about another format? Do you have any use cases or user stories that you doubt?
I: Yes, there are some.
C: Well, let's get to those specifically, because everything else is there, yes.
I: Okay, for example: As a user, I'd like to receive access denied notifications if I'm not recognized. That way I can tell if I have access or not.
C: We don't have any feedback.
I: So there isn't any?
C: I was actually thinking about taking some simple LEDs and connecting them.
I: Well, because we're now using the cards, and they indicate whether they've been allowed through.
C: How good are you with simple electrical circuits?
I: Well, I have some. I do. Yes, I could, in principle, if necessary.
C: So, how about taking a couple of LEDs, a red and green one, and connecting them to the board? So there would be an indicator.

C: Uh-huh. Okay. Well, let's do it this way.
I: Okay.
I: As an admin, I want the camera to recognize a worker in a crowd and grant access, so I can be sure that strangers have entered the lab legally. Well, roughly speaking, the worker is taking strangers into the lab at their own risk.
C: Take that into account.
I: And if a crowd is passing, for example, who should we distinguish in that crowd? Should we not pay much attention to the crowd situation, or should we distinguish the person in front?
C: Only the person in front. So you don't need the crowd situation, yes. It's a complex case, and I don't know how to handle it myself.
I: Okay. As a user, would I like to be recognized by the camera despite the fact that I have accessories on (glasses, hat, etc.)?
C: Yeah, right. 
I: As a user, I want to be sure that the system won't mistake another person for me with a photo of my face.
C: Yes, that was the initial requirement.

I: As an admin, I want to be able to see the entire list of people who have access.
C: As an admin, yes.
I: Now, about the prototype. First, I want to create an administration panel that will require login and password access. This means that people who have access to the site, once they find out about it, can easily administer it. I want to implement this kind of mini-security. It will most likely be like a site hosted on a localhost. We'll have a small menu with a tab listing all employees. There will be "add" and "remove user" buttons. So, for example, we add an "add" button, and naturally, the person is recognized, and registration occurs. There's a "Remove Users" button, and there we select users to remove. It opens as a list, and we select users using the checkboxes. There's also a button to add temporary access, meaning if we accidentally added a permanent user, we need to give them temporary access. So, let's say we forgot to check the box for temporary users initially. And then we'll switch to another user. Another section, let's call it that, in the mini-menu, where all blocks will be considered—that is, whether an attempt should be considered, again. Logs of those who weren't recognized, meaning those who weren't employees.

C: Yes, yes.
I: Well, those cases will be taken into account, meaning a screenshot will be sent showing when it happened, that the person wasn't allowed into the lab. And only for us, in cases where they're recognized for some external factors, like lighting or accessories—wouldn't that be in the logs?
C: Well, yes, just for you.
I: Okay, so only for those who tried to get in but weren't allowed in. That's all I have for now regarding the prototype, or do you have any suggestions?
C: That's all for now.
I: Okay. Would you like access to all logs or just failed attempts?
C: All.
I: So, we'd need to add a third tab where everything would be.
C: You could just make one tab where it would be...
I: Yeah.
C: Or with filters.
I: Yes, I was just about to say that the default sorting would most likely be by date, and there would also be filters that would distinguish between successful and unsuccessful attempts. Now, regarding functionality.
I: So, the minimum functionality is admin login, new user registration, deletion of an old user, and viewing logs?
C: Yes.
I: We're just thinking about making it at least recognize a person, that is, somehow. Somehow, even if not with the highest accuracy, but compare it with our database? That's V1.
S: I just advised against focusing too much on the website, because the algorithm itself is trivial. We'll need to spend more time and not put it off until the last minute.
I: Okay. It's just a pretty late task, to be honest. Okay, now on to the questions. At what height will the cameras be installed? At eye level or a little higher?
C: Somewhere at eye level, yes. 1m60cm-1m70cm, probably somewhere around there.
Q: Should administrators be able to change a user's role? For example, promote someone to administrator or demote them?
C: No.
I: So, only one administrator?
C: Yes.
I: Okay. Should access results trigger any notifications, sounds, or color indicators?
S: No. That is, it lets the green light in, and if it doesn't, it's red. If, for example, there's active registration, the green light just blinks, ugh, both at once.
I: Okay. How long should the system continue to operate when the power goes out? And should it even operate automatically?
S: We don't have a UPS.
I: Uh-huh. Okay, so the power goes out, and so does the camera. Well, it doesn't allow anyone to disconnect. Okay. Should the system locally store login attempts when there's no internet connection, such as successful access, access denied, camera recognition errors... And sync these records after the connection is restored?
C: The entire system is offline; there are no online functions.
I: So, to some kind of cloud. Well, technically, we're not putting the cloud on any server?
C: No, everything is hardware-based, everything is hardware-based.
I: Okay. Then the question immediately becomes: how often, for example, can the logs be cleared? Because otherwise, the database would get clogged up every time.
S: Well, you could just look at the limitations, what the logs store over the last three days, something like that.
I: Okay. What should the system do if the camera is unavailable or stops sending frames?
C: Provide some kind of light indicator.
I: Yeah.
S: Since we now have such an indicator.
I: Are there any indicators that are colorful, meaning they can display green, red, and yellow in one indicator?
C: But there's this RGB LED. You could just use it.
I: It's like it could just flash yellow, as a warning.

I: Okay. A few questions, let's put it this way. How do you envision connecting to the camera through the board? So, is it wired or via a cable?
C: Wired. Only wired. It will most likely be USB.
I: Yeah. So, we'll connect to the board through a laptop, and the board will be connected to the camera?
C: Again.
I: So, how should we work with the board itself? Wired or something?
C: You can work directly on it. It has video outputs, all the ports, it's a regular computer. You can connect via SSH; if needed, I'll come over and consult. Usually, it's more convenient via SSH, so you don't have to transfer or do anything extra.
I: Okay. So, roughly speaking, the wire will go directly to the camera?
C: Yes
I: Everything's fine. Right. And. Should we deploy the database only on the board, or on the laptop as well? So, what's the approximate setup?
C: Everything is on the board.
I: So, we mostly use the laptop just to test how it works, but the main part will be on the board.
C: Well, yeah. So, on the laptop, you're like an admin. I connect to the board via SSH on the laptop and do things there. That's it. That's the case. But the entire working system itself is purely on the Raspberry Pi.
I: Okay. Thank you. Basically, no questions. If anyone has anything to add, let me know.
I: Can I clarify? We'll be making some kind of website. Will you use it to add users, or will you do it through...
C: No. Look, the entire application runs on the Raspberry Pi. I can connect to the Raspberry Pi via SSH Key and open the website there. The website's visualization can be transferred to my computer via SSH Key. From there, I can open it on my computer.
I: Okay, thank you very much.
