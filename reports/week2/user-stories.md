# User Stories for FaceGuard

## User Roles / Personas

1. **Admin**
2. **User**

---

## US-01: Add people to database

**Requirement status:** Active
**MoSCoW priority:** Must Have

As an Admin,
I want to be able to add people to the database,
so that I can give them access to the laboratory.

### Notes and constraints

Admin provides name and face image.

---

## US-02: Recognize face for entry

**Requirement status:** Active
**MoSCoW priority:** Must Have

As a User,
I want my face to be recognized by camera,
so that I can enter the laboratory.

### Notes and constraints

Recognition within 2–3 seconds.

---

## US-03: Remove people from database

**Requirement status:** Active
**MoSCoW priority:** Must Have

As an Admin,
I want to be able to remove people from the database,
so that they could not enter the laboratory.

### Notes and constraints

Removal is immediate.

---

## US-04: Database for about 40 people

**Requirement status:** Active
**MoSCoW priority:** Must Have

As an Admin,
I want to have a database for about 40 people,
so that I can give access to all laboratory workers.

### Notes and constraints

System handles at least 40 enrolled users.

---

## US-05: Accurate system

**Requirement status:** Active
**MoSCoW priority:** Must Have

As an Admin,
I want to have an accurate system,
so that unknown people would not enter the laboratory.

### Notes and constraints

False acceptance rate < 0.1%.

---

## US-06: Avoid loss of card

**Requirement status:** Removed
**Previous MoSCoW priority:** Must Have

As a User,
I want to avoid losing a physical access card,
so that I can enter the laboratory without it.

**Reason:** Duplicate of US-02.

---

## US-07: Temporary access

**Requirement status:** Active
**MoSCoW priority:** Should Have

As an Admin,
I want to be able to temporarily add a person,
so that I can give temporary access to someone.

### Notes and constraints

Access expires after set date.

---

## US-08: Notification about failed access

**Requirement status:** Active
**MoSCoW priority:** Should Have

As a User,
I want to get a notification about failed access,
so that I understand if I have access.

### Notes and constraints

Immediate sound or screen message.

---

## US-09: Logs of failed attempts

**Requirement status:** Active
**MoSCoW priority:** Could Have

As an Admin,
I want to receive logs of failed attempts to enter,
so that I will have a list of suspicious people.

### Notes and constraints

Logs include timestamps and images.

---

## US-10: Liveness detection

**Requirement status:** Active
**MoSCoW priority:** Could Have

As an Admin,
I want the camera to detect any attempt at deception (e.g., using a photo),
so that the system prevents unknown persons from entering.

### Notes and constraints

Requires blink or motion detection.

---

## US-11: Recognize in a crowd

**Requirement status:** Active
**MoSCoW priority:** Could Have

As an Admin,
I want the camera to recognize a worker in a crowd,
so that I can be sure that strangers did not enter legally.

### Notes and constraints

Focus on the person closest to the door.

---

## US-12: Recognition with accessories

**Requirement status:** Active
**MoSCoW priority:** Could Have

As a User,
I want to be recognized by the camera despite having accessories (glasses, hat, etc.),
so that I do not need to remove them.

### Notes and constraints

Works with typical glasses and hats.

---

## US-13: Prevent photo substitution

**Requirement status:** Active
**MoSCoW priority:** Could Have

As a User,
I want to be sure that the system will not mistake another person with a photo of my face for me,
so that my access cannot be stolen.

### Notes and constraints

Requires liveness or motion check.

---

## US-14: View list of people with access

**Requirement status:** Active
**MoSCoW priority:** Should Have

As an Admin,
I want to be able to see the whole list of people who have access,
so that I can review and revoke access when necessary.

### Notes and constraints

List shows names and access type.

---

## Initial proposed MVP v1 scope

- US-01
- US-02
- US-03
- US-04
- US-05