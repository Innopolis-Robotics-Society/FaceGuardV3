# User Acceptance Tests

## UAT-001: Register a new employee with permanent access

**Status:** Active  
**User goal:** Grant permanent access to a new employee so the system recognizes them any time they approach the camera.

**Preconditions:**
- The system is active, powered on
- The admin is on the page 'Add a new employee'

**Steps:**
1. Place employee with clearly visible face in front of the camera in its view
2. Capture employee's face
3. Enter the name of the employee
4. Choose access type 'Permanent'
5. Press the button 'Save'

**Expected outcome:**
- The employee was registered
- The system recognizes them
- The name, registration date, the type of the access (status) are displayed in the list of all registered employees on the page 'Employees'; the fields start date and expiration date are filled with 'None'

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:** Add a check if the employee was already registered. Try to define the upper bound on FPS number to fit in 3-5 seconds for backend response.  
**Resulting PBIs:** [#115](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115)

---

## UAT-002: Add a new employee with temporary access

**Status:** Active  
**User goal:**  Grant temporary access to a new employee so the system recognizes them if they approach the camera during the allowed period.

**Preconditions:**
- The system is active, powered on
- The admin is on the page 'Add a new employee'

**Steps:**
1. Place employee with clearly visible face in front of the camera in its view
2. Capture employee's face
3. Enter the name of the employee
4. Choose access type 'Temporary'
5. Enter the valid start and expiration dates.
6. Press the button 'Save'

**Expected outcome:**
- The employee was registered
- The system recognizes them during the allowed period
- The name, registration date, the type of the access (status), start date, and expiration date are displayed in the list of all registered employees on the page 'Employees'
- After the expiration date, the access for that employee is automatically removed, and the system rejects the attempt
---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.   
**Comments:** Change the way of specifying the temporary access duration from selecting dates to selecting dates with exact time.  
**Resulting PBIs:** [#117](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117)

---

## UAT-003: Remove a registered employee

**Status:** Active  
**User goal:** Remove the registered employee so they do not have the access to enter the laboratory

**Preconditions:**
- The admin is on the page 'Employees'

**Steps:**
1. Tick the boxes on the left side of the rows with the employees that the admin wants to remove
2. Press the button 'Delete'
3. Confirm deletion by pressing 'Yes' in the pop-up window

**Expected outcome:**
- The employee is not displayed in the list of all employees
- The access for this employee is denied

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:** All good.
**Resulting PBIs:** -

---

## UAT-004: View the list of all registered employees

**Status:** Active  
**User goal:** View the list with information of all registered employees so the admin can monitor registered employees

**Preconditions:**
- The admin is on the 'Employee' page

**Steps:**
1. Scroll down to see the entire table with registered employees

**Expected outcome:**
- All registered employees are displayed on the list
- Each row with employee has the following filled fields: employee's name, registration date, the type of the access (status), start date, and expiration date
- Each row with employee has a tick box in the left side so it can be selected
- The admin is able to sort, search, filter the items

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:** Add the ability to change employee's name and status after registration, add the time of the employee's last entry  
**Resulting PBIs:** [#113](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113), [#114](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114)

---

## UAT-005: View the access logs

**Status:** Active  
**User goal:** View logs of all attempts so the admin can monitor access attempts

**Preconditions:**
- The admin is on the 'Access Logs History' page

**Steps:**
1. Scroll down to see the entire table with logs

**Expected outcome:**
- All access logs are displayed in the table
- The ID of a log, name of the employee or 'UNKNOWN', attempt time, and status are correctly displayed

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:** Add filtering by date range  
**Resulting PBIs:** [#116](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116)

---

## UAT-006: Automatic recognition of a registered employee

**Status:** Active  
**User goal:** The system shall grant the access to a registered employee so they can enter the laboratory

**Preconditions:**
- The employee was registered
- If the employee has temporary access, the date when the attempt is happening shall be between the start and expiration dates (including the boundaries)

**Steps:**
1. The employee stands in front of the camera in its view with clearly visible face

**Expected outcome:**
- The system recognized the employee within 3 seconds automatically
- The system grants the access
- The system logs the attempt

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:** Very good!  
**Resulting PBIs:** -

---

## UAT-007: Rejection of an unregistered person

**Status:** Active  
**User goal:** The system shall deny the access to an unregistered person so they cannot enter the laboratory

**Preconditions:**
- The person is not registered

**Steps:**
1. The unregistered person stands in front of the camera in its view

**Expected outcome:**
- The system identifies the presence of a face
- The system denies the access
- The system logs the attempt

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:**  Very good!  
**Resulting PBIs:** -
