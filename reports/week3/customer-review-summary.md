# Customer Review Summary: MVP v1 increment

## Meeting details:
*Date*: 18.06.2026
*Participants*: ixkci(interviewer), s0ftach(recorder), oebarbie(observer), ns3dx (note taker), Customer

## Artifacts demonstrated:
1. Planned MVP v1 scope
2. Implemented MVP v1: Web page featuring the “Employees”, “Add an employee”, “Logs” modules. 
3. Face Recognition Test module: A temporary testing interface using the built-in webcam

## Scope Reviewed & Implemented Increment

### 1. Planned Scope for MVP v1
- Implement employee addition and deletion from the database
- Realize face recognition for entry (comparing in real-time face with face embeddings from database) with false acceptance rate < 0,1%
- Implement database with list of employees
- Integration of physical hardware components (move to external USB camera and Raspberry Pi)
### 2. Implemented MVP v1 increment
- Implemented user registration pipeline (capturing a photo, extracting embeddings, and saving them locally)
- Setup basic log storage for tracking entries and access history(outputs “unknown” if the system has not recognized the person)
- Implemented a comparison logic displaying matching results against database entries with an initial threshold (0,56)
- Verification was temporarily demonstrated via a built-in webcam

## Customer Feedback
*Status*: Approved with requested changes

The customer validated the demonstrated software increment, under the condition that the following technical feedback are implemented:
- Success Rate ≠ Model Confidence (the model confidence score (currently around 80%) must not be confused with the overall system success rate; the functional requirement for the final system success rate remains at 95%)
- Temporary Access Interface (the interface must specify explicit access "start time" and access "end time" parameters)
- Biometric Pipeline Organization (the system must capture 5 to 10 frames at registration/recognition, compute an average embedding vector, and match against that averaged baseline)
- Face Cropping (the customer suggested incorporating OpenCV pre-processing algorithms to locate and crop faces out of cluttered frames)
- Dockerization (the customer issued a high-priority mandate to encapsulate the environment and system inside a Docker container)
  
## Risks, Gaps, Decisions

- Virtual Machine Usage: deleted from requirements
- Hardware & Resource Constraints: the current ONNX Runtime Buffalo-L model lags on regular machines. Given that the technical capabilities of the Raspberry Pi 5 are limited, such a model may cause a technical risk and team should test the system on the lighter model

## Action Points

- Urgent make repository Dockerization (Issue #56)
- Modify form for Temporary Access (Isuue #57)
- Re-engineer pipeline to extract 5-10 frames and make an average embedding vector (Issue #59)
- Test lighter model to recognize face than ONNX Runtime Buffalo-L model (Issue #58)
- Do a face cropping before making an embedding (Issue #61)

## Scope Changes  
Up to this moment, no changes have occurred in the scope of the project, only minor technical details.  
  
## Resulting Product Backlog
[Link] (https://github.com/orgs/Innopolis-Robotics-Society/projects/5)

