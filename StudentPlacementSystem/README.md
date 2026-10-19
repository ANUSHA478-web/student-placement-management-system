
# Student Placement Management System

A web-based Student Placement Management System developed using Python, Flask, MySQL, HTML, and CSS. This project helps manage student records, companies, job opportunities, applications, and placement reports in one place.

## Features

- Student Management: Add, view, search, update, and delete student records.
- Company Management: Manage company details.
- Job Management: View and search job opportunities.
- Job Applications: Allow students to apply for jobs and view applications.
- Eligibility Checking: Find jobs based on student CGPA and backlogs.
- Application Status: Update application statuses such as Applied, Shortlisted, and Selected.
- Student Profiles: View individual student details.
- Dashboard: View statistics about students, companies, jobs, and applications.
- Placement Reports: View placement application details.
- CSV Export: Export student, company, job, application, and placement report data.

## Technologies Used

- Python
- Flask
- MySQL
- HTML
- CSS
- CSV

## Project Structure

```text
StudentPlacementSystem/
├── app.py
├── config.py
├── .gitignore
├── README.md
├── templates/
├── static/
│   └── style.css
└── ...
```

## Database Setup

1. Install MySQL and create a database named `student_placement_db`.
2. Create the required tables for students, companies, jobs, and applications.
3. Configure the database connection in your local `config.py` file.
4. Keep your database password private. Do not upload `config.py` or credentials to GitHub.

## How to Run Locally

1. Install Python and MySQL.
2. Install the required Python packages:

   ```bash
   pip install flask mysql-connector-python
   ```

3. Configure your MySQL connection locally.
4. Start the Flask application:

   ```bash
   python app.py
   ```

5. Open your browser and visit:

   http://127.0.0.1:5000/

## Project Purpose

This project demonstrates practical skills in Python web development, database connectivity, CRUD operations, job application management, and report generation.

## Author

Developed as a Student Placement Management System project.
