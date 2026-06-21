# Transcript
(00:00)
I: Thank you for taking the time to spend with us. May we audio record our interview again?
C: Yes, of course

(00:06)
I: Thank you! Let's get started, the first thing we want to discuss is the implemented MVP v1 increment. We have implemented sections: “Employee”, here “Add an employee”, and here “Logs” so that access attempts can be seen. And for now, we made a separate “Face Recognition” page - essentially, it won't be in the final version. It's just for testing. Right now, we can take a photo for registration, and it is saved as an embedding into the table. And for recognition, we take a photo again, the system creates an embedding and it compares with the database. The team has already tested it, but this is also a temporary measure - the project will use live speech recognition.
C: Can you demonstrate how it will work?

(00:54)
I: Yes. It gets saved to the table, and then it is compared and recognized with a certain accuracy about 80.
C: Is that the model's confidence? Don't confuse model confidence with success rate. The success rate must be 95%, while confidence is whatever it turns out to be.

(01:23)
I: Uh-huh. Good. But for now, this all runs on the built-in webcam. And I want to discuss the planned MVP v1 scope. Our plans for the MVP v1 scope include figuring out the hardware and connecting a webcam so that the entire system works with an external camera. So it can also recognize, save embeddings, and compare. We also plan to implement deletion from the database. And overall, that's it for now.
C: Okay, good. By the way, which model did you choose?

(01:57)
I: The ONNX Runtime Buffalo-L model, InsightFace.
C: Got it. Okay. How many frames does it output?

(02:14)
I: Well, it lags heavily with the L-version. But the lighter one runs fine.
C: Later on, you will need to test this thoroughly on the Raspberry Pi. The processing power there is severely limited.

(02:37)
I: Okay. I just wanted to move on to questions regarding our plans for MVP v1. First, do you accept the planned goals, is everything okay?
C: Yes, yes

(03:16)
I: So, the next question. Do we even need to use a virtual machine?
C: In my opinion, it doesn't really apply to us. I don't know where to use it here, so no, you don't need it.

(03:43)
I: All right. The third question: did we understand correctly that we need to pack this entire project into Docker? So it should run on different operating systems?
C: Yes, pack it all into Docker so that the entire required environment and all system utilities are strictly inside Docker, not on the host system. Because the host system might have various other processes that you shouldn't interfere with. Usually, a starter Docker package should be there from the very beginning so you can develop within it right away. Please get this done as soon as possible, otherwise, it will hinder synchronizing the whole team.

(06:28)
I: We'll take it into account. We also have another question. We have an “Add an employee” page. So here is the camera, and you can select temporary access by the number of days. Is it comfortable?
C: It would probably be better to do it this way: we have an access start time and an access end time so that it can be specified precisely.

(06:52)
I: So make it date-based? Date, start time, and end of access.
C: Yes

(07:02)
I: Okay, thank you. Do you have any questions for us?
C: Yes. Please describe how your full pipeline for processing face data is structured? You have a camera, and you have the model module. What do you do next?

(07:27)
I: So, OpenCV acts as the camera itself, and InsightFace handles detection, recognition, and embedding generation.
C: In detail?

(07:42)
I: I used the ONNX Runtime model. Embedding generation is already built into InsightFace; it has ready-to-use methods.
C: Do I understand correctly that you take one photo and process it?

(08:31)
I: For now, yes, based on a single image.
C: Will you be changing that somehow?

(08:36)
I: Yes, most likely. The camera will be internally taking multiple photos.
C: As a hint: comparing embeddings using just a single frame is bad. A frame could accidentally be noisy or blurry. It's important to capture several frames at once (five to ten) and then compare. The idea is to obtain an average embedding over several frames because noise from the model and the camera can ruin everything. And if you ruin the registration, it'll ruin all the subsequent recognition. Saving based purely on one frame is a very poor solution. I just want you to know this for the future.

(10:20)
I: As we understood, we take several face photos, save them as vectors, calculate the average embedding, and use that for comparison.
C: Yes

(10:34)
I: And how many photos? And should they be in different lighting conditions?
C: Figure it out experimentally. You know how Face ID data is collected on a phone. It's done that way for a reason. And another question, are you detecting the face in the frame?

(11:36)
I: InsightFace handles all of that. It can even detect multiple faces.
C: And how will that be handled? Say you have a frame, and two faces accidentally get in: one in the front, one in the back. How is it processed?

(12:21)
I: The face in the back is ignored. It takes the first captured face in the frame, the one closest to the camera.
C: So you feed the image directly into the model, and then from the vector representations you check the face sizes and pick the large one?

(12:46)
I: Yes
C: There are probably algorithms in OpenCV that can locate faces in photos, so you can crop the frame and extract only the intended face. That's another idea for your future reference.

(14:00)
I: All right, thanks. And one question to clarify. Do we understand correctly that we have one Raspberry Pi for three teams?
C: Yes

(17:13)
I: Okay. We don’t have any questions. Do you have any?
C: No

(17:19)
I: Good. So, thank you for meeting! See you!
C: Good luck!

  
