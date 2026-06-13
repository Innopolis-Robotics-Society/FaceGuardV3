**1. Purpose and description of the MVP v0 foundation**  
The current MVP v0 establishes the technical foundation for FaceGuard. It includes an authentication page, employees management page with add functionality, and employees management page with delete functionality. It also has access logs page and employees list page, which are backed by a PostgreSQL database. Face recognition and camera are not yet implemented and are replaced by placeholders.

**2. Deployment URL or runnable-artifact link**  
[TODO]  

**3. Public video demonstration link**  
[TODO]  

**4. Relationship to the prototype and proposed MVP v1 stories, where applicable**  
MVP v0 implements the prototype screens and reflects its features. It covers the following MVP v1 user stories:
- US-01: Add people to database  
- US-03: Remove people from database  
- US-04: Database for about 40 people  
- US-07: Temporary access
- US-09: Logs of failed attempts
- US-14: View list of people with access

**5. Current limitations, placeholders, and mocks**  
For now, this version has limitations, such as inability to connect to the camera or Raspberry Pi. Face recognisition is not implemented yet. Embeddings of employees's photos are not captured or stored.

**6. Link to local setup instructions**
**[link](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/a9553c790f8eff41e28cc19c6705d5d3e2f48315/README.md)**

**7. Repeatable smoke-check scenario**  
(in case app is running locally at `http://localhost:8501`)  

**Steps:**
1. Open `http://localhost:8501`, then Authentication Page appears
2. Enter valid admin credentials, then got redirected to the Employees Page
3. Navigate to "add an employee" in the sidebar, then the form appears
4. Make a photo, fill in the name, select access type, click Save, then you will redirected to Employees Page
5. Navigate to "logs", then the logs table appears loaded from the database
6. Navigate to "employees", then the employee table appears loaded from the database
7. Navigate to "Log out" button, you will be log out of the system
