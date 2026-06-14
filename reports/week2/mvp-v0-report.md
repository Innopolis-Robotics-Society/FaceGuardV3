# Faceguard. MVP v0

## **1. Purpose and description of the MVP v0 foundation**  
The current MVP v0 establishes the technical foundation for FaceGuard. It includes an authentication page, and employees management page with add and delete functionalities. It also has access logs page and employees list page, which are backed by a PostgreSQL database. Face recognition and camera are not yet implemented and are replaced by placeholders.

## **2. Deployment URL**  
[URL](https://faceguardv3.streamlit.app)   

## **3. Public video demonstration link**  
[Link](https://drive.google.com/file/d/1H3z0uBsEWGSThQTx3_miLo73aQnXwOgz/view?usp=sharing)  

## **4. Relationship to the prototype and proposed MVP v1 stories, where applicable**  
MVP v0 implements the prototype screens and reflects its features. It covers the following MVP v1 user stories:
- US-01: Add people to database  
- US-03: Remove people from database  
- US-04: Database for about 40 people  
- US-07: Temporary access
- US-09: Logs of failed attempts
- US-14: View list of people with access

## **5. Current limitations, placeholders, and mocks**  
For now, this version has limitations, such as inability to connect to the camera or Raspberry Pi. Face recognition is not implemented yet. Employee face embeddings are not captured or stored.

## **6. Link to local setup instructions**  
[Link](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/a9553c790f8eff41e28cc19c6705d5d3e2f48315/README.md)

## **7. Repeatable smoke-check scenario**  

### **Access Instructions:**  
  
**1 Way. Localhost**
1. Clone the repository and follow [README](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/blob/13771ed35270511821926d20d7aa6b6339e9ec7f/README.md).
2. Fill in the credentials.  

**2 Way. Deployment URL**
1. Open the [URL](https://faceguardv3.streamlit.app).
2. Fill in the dedicated limited-permission test credentials:  
   login: `your_admin_login`  
   password: `your_admin_password`  
   _(For now, we will use test credentials for testing and accessing database on the deployed version, but later we will remove them. For the localhost you don't need them.)_
  
### **Steps:**
1. Open localhost or [URL](https://faceguardv3.streamlit.app), then Authentication Page appears
2. Enter valid admin credentials, then you are redirected to the Employees Page
3. Navigate to "Add an employee" in the sidebar, then the form appears
4. Take a photo, fill in the name, select access type, and click Save, then you are redirected to the Employees Page
5. Navigate to "Employees", then the employee table appears loaded from the database. There you can see different filters
6. Navigate to "Access Logs History", then the logs table appears loaded from the database. There you can see different filters
7. Navigate to "Log out" button, you are logged out of the system

### **Expected Results:**  
All steps complete without errors. Employee data and logs are correctly stored and retrieved from the database.
