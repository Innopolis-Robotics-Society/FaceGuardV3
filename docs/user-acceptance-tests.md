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
- If the lighting is poor or the frame is blurry, the system asks you to look straight ahead and the LEDs light up yellow for 5 seconds
- The LEDs lit up yellow, red, and blue (all LEDs) during the registration and 3 seconds after it 
- The employee was registered
- The system recognizes them
- The name, registration date, the type of the access (status) are displayed in the list of all registered employees on the 'Employees' page; the fields start date and time and expiration date and time are filled with 'None'

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:** Add a check if the employee was already registered. Try to define the upper bound on FPS number to fit in 3-5 seconds for backend response.  
**Resulting PBIs:** [#115](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115)

---
### Execution: Sprint Review & UAT Session (2026-07-03)  

**Result:** Passed
**Executed by:** Customer (role: admin)  
**Comments:**  The system shall be faster.  
**Resulting PBIs:** [#171](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/171)  


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
5. Enter the valid start and expiration dates and time
6. Press the button 'Save'

**Expected outcome:**
- If the lighting is poor or the frame is blurry, the system asks you to look straight ahead and the LEDs light up yellow for 5 seconds
- The LEDs lit up yellow, red, and blue (all LEDs) during the registration and 3 seconds after its
- The employee was registered
- The system recognizes them during the allowed period
- The name, registration date, the type of the access (status), start date and time, and expiration date and time are displayed in the list of all registered employees on the page 'Employees'
- After the expiration date and time, the access for that employee is automatically removed, and the system rejects the attempt
---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.   
**Comments:** Change the way of specifying the temporary access duration from selecting dates to selecting dates with exact time.  
**Resulting PBIs:** [#117](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117)

---
### Execution: Sprint Review & UAT Session (2026-07-03)

**Result:** Passed
**Executed by:** Customer (role: admin)  
**Comments:** The system shall be faster.  
**Resulting PBIs:** [#171](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/171)  


---


## UAT-003: Remove a registered employee

**Status:** Active  
**User goal:** Remove the registered employee so they do not have the access to enter the laboratory

**Preconditions:**
- The admin is on the 'Employees' page

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
- The admin is on the 'Employees' page

**Steps:**
1. Scroll down to see the entire table with registered employees

**Expected outcome:**
- All registered employees are displayed on the list
- Each row with employee has the following filled fields: employee's name, registration date and time, the type of the access (status), start date and time, expiration date and time, and time of the last access (or with empty, None, or Never if the employee had not made any attempts to enter the laboratory) 
- Each row with employee has a tick box in the left side so it can be selected
- The admin is able to sort, search, filter the items

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:** Add the ability to change employee's name and status after registration, add the time of the employee's last entry  
**Resulting PBIs:** [#113](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113), [#114](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114)

---
### Execution: Sprint Review & UAT Session (2026-07-03)

**Result:** Passed
**Executed by:** Customer (role: admin)
**Comments:** All good.
**Resulting PBIs:** -  


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
- Each recognition session adds only one log at a time (with one-minute-period)
- The admin can select the date range to filter the logs (within the period of 3 days because it is the maximum period the system keeps)

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:** Add filtering by date range  
**Resulting PBIs:** [#116](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116)

---
### Execution: Sprint Review & UAT Session (2026-07-03)

**Result:** Passed
**Executed by:** Customer (role: admin)  
**Comments:** Works well.  
**Resulting PBIs:** -  


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
- If the lighting is poor or the frame is blurry, the system asks you to look straight ahead and the LEDs light up yellow for 5 seconds
- During recognition, the LEDs glow yellow; after successful recognition, the LEDs stop blinking yellow and turn solid blue for 5 seconds
- If there's no one in front of the camera, nothing lights up
- There is no test section on the recognition page
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
### Execution: Sprint Review & UAT Session (2026-07-03)

**Result:** Passed  
**Executed by:** Customer (role: admin)  
**Comments:** The recognition shall run in the background.  
**Resulting PBIs:** [#172](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/172)  


---


## UAT-007: Rejection of an unregistered person

**Status:** Active  
**User goal:** The system shall deny the access to an unregistered person so they cannot enter the laboratory

**Preconditions:**
- The person is not registered

**Steps:**
1. The unregistered person stands in front of the camera in its view

**Expected outcome:**
- If the lighting is poor or the frame is blurry, the system asks you to look straight ahead and the LEDs light up yellow for 5 seconds
- During recognition, the LEDs glow yellow; after failed recognition, the LEDs stop blinking yellow and turn solid red for 5 seconds
- There is no test section on the recognition page
- If there's no one in front of the camera, nothing lights up 
- The system identifies the presence of a face
- The system denies the access
- The system logs the attempt

---

### Execution: Sprint Review & UAT Session (2026-06-27)

**Result:** Passed  
**Executed by:** Customer (role: admin). Tests were demonstrated by the team during an online session; the customer observed, asked questions, and confirmed acceptance.  
**Comments:**  Very good!  
**Resulting PBIs:** -

---
### Execution: Sprint Review & UAT Session (2026-07-03)

**Result:** Passed  
**Executed by:** Customer (role: admin)  
**Comments:** The recognition shall run in the background.  
**Resulting PBIs:** [#172](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/172)  


---


## UAT-008: Edit the name or status of an employee

**Status:** Active  
**User goal:** Change the name or status of an already registered employee in the employees' table

**Preconditions:**
- The admin is on the 'Employees' page

**Steps:**
1. Scroll down to see the entire table with registered employees
2. Find the employee whose name or status need to be changed
3. Select the checkbox next to the employee's name
4. Click "Edit"
5. In a dialog, fill in the fields with the new name/status information
6. Click "Save"

**Expected outcome:**
- All registered employees are displayed on the list
- When the admin clicks "Edit", a dialog opens pre-filled with the employee's current name and status. If "Temporary" is selected, date and time pickers appear pre-filled with existing dates (or defaults if none)
- After the admin clicks "Save", the database gets updated, and table refreshes
- The table with updated fields is displayed

---
### Execution: Sprint Review & UAT Session (2026-07-03)

**Result:** Passed
**Executed by:** Customer (role: admin)
**Comments:** -  
**Resulting PBIs:** -  

---
## UAT-009: Register an already registered employee

**Status:** Active
**User goal:** Prevent duplication of registered employees

**Preconditions:**
- The system is active, powered on
- The admin is on the page 'Add a new employee'

**Steps:**
1. Place employee with clearly visible face in front of the camera in its view
2. Capture employee's face

**Expected outcome:**
- If the lighting is poor or the frame is blurry, the system asks you to look straight ahead and the LEDs light up yellow for 5 seconds
- The LEDs lit up yellow, red, and blue (all LEDs) during the registration
- The system shows a message about duplicate and does not register the employee again
- The button "Try again" is displayed and after pressing, resets the registration

---
### Execution: Sprint Review & UAT Session (2026-07-03)

**Result:** Passed  
**Executed by:** Customer (role: admin)
**Comments:**  Works correctly.  
**Resulting PBIs:**  -  

---
