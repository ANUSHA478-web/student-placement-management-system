

import mysql.connector

import os

try:
    from config import DB_CONFIG
except ImportError:
    DB_CONFIG = {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "database": os.environ["DB_NAME"]
    }

from flask import Flask, render_template,request,redirect
def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as error:
        print("Database connection error:", error)
        return None



# ================= HELPER FUNCTIONS =================

def read_id(prompt):
    value = input(prompt).strip()
    if not value.isdigit() or int(value) <= 0:
        print("Please enter a valid positive ID.")
        return None
    return int(value)


def read_cgpa():
    try:
        value = float(input("Enter CGPA (0-10): ").strip())
        if not 0 <= value <= 10:
            print("CGPA must be between 0 and 10.")
            return None
        return value
    except ValueError:
        print("Enter a valid numeric CGPA.")
        return None


def show_rows(title, rows):
    print(f"\n--- {title} ---")
    if not rows:
        print("No records found.")
        return
    for row in rows:
        print(row)


# ================= 1. VIEW STUDENTS =================

def view_students():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT student_id, name, email, branch,
                   cgpa, backlogs, skills
            FROM students ORDER BY student_id
        """)
        show_rows("STUDENTS", cur.fetchall())
    finally:
        cur.close()
        conn.close()


# ================= 2. VIEW COMPANIES =================

def view_companies():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT company_id, company_name, location
            FROM companies ORDER BY company_id
        """)
        show_rows("COMPANIES", cur.fetchall())
    finally:
        cur.close()
        conn.close()


# ================= 3. VIEW JOBS =================

def view_jobs():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT j.job_id, c.company_name, j.job_role,
                   j.package_lpa, j.min_cgpa, j.max_backlogs
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY j.job_id
        """)
        show_rows(
            "AVAILABLE JOBS (ID, Company, Role, Package LPA, "
            "Minimum CGPA, Maximum Backlogs)",
            cur.fetchall()
        )
    finally:
        cur.close()
        conn.close()


# ================= 4. CHECK ELIGIBLE STUDENTS =================

def check_eligible_students():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT job_id, job_role, min_cgpa, max_backlogs
            FROM jobs ORDER BY job_id
        """)
        jobs = cur.fetchall()
        show_rows("JOB REQUIREMENTS", jobs)

        if not jobs:
            return

        job_id = read_id("Enter Job ID: ")
        if job_id is None:
            return

        cur.execute("""
            SELECT job_role, min_cgpa, max_backlogs
            FROM jobs WHERE job_id = %s
        """, (job_id,))
        job = cur.fetchone()

        if job is None:
            print("Job ID not found.")
            return

        cur.execute("""
            SELECT student_id, name, branch, cgpa, backlogs
            FROM students
            WHERE cgpa >= %s AND backlogs <= %s
            ORDER BY cgpa DESC
        """, (job[1], job[2]))

        print(f"\nEligible students for {job[0]}:")
        show_rows(
            "STUDENT ID, NAME, BRANCH, CGPA, BACKLOGS",
            cur.fetchall()
        )
    finally:
        cur.close()
        conn.close()


# ================= 5. APPLY FOR A JOB =================

def apply_for_job():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT student_id, name FROM students")
        show_rows("STUDENTS (ID, NAME)", cur.fetchall())

        student_id = read_id("Enter Student ID: ")
        if student_id is None:
            return

        cur.execute("""
            SELECT name, cgpa, backlogs
            FROM students WHERE student_id = %s
        """, (student_id,))
        student = cur.fetchone()

        if student is None:
            print("Student not found.")
            return

        cur.execute("""
            SELECT j.job_id, c.company_name, j.job_role,
                   j.min_cgpa, j.max_backlogs
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY j.job_id
        """)
        jobs = cur.fetchall()
        show_rows("AVAILABLE JOBS", jobs)

        job_id = read_id("Enter Job ID: ")
        if job_id is None:
            return

        cur.execute("""
            SELECT job_role, min_cgpa, max_backlogs
            FROM jobs WHERE job_id = %s
        """, (job_id,))
        job = cur.fetchone()

        if job is None:
            print("Job not found.")
            return

        # Check eligibility before accepting an application.
        if student[1] < job[1] or student[2] > job[2]:
            print("Application rejected: eligibility criteria not met.")
            print(f"Your CGPA: {student[1]} | Required: {job[1]}")
            print(
                f"Your backlogs: {student[2]} | "
                f"Maximum allowed: {job[2]}"
            )
            return

        # Check duplicates before inserting.
        cur.execute("""
            SELECT application_id FROM applications
            WHERE student_id = %s AND job_id = %s
        """, (student_id, job_id))

        if cur.fetchone():
            print("This student has already applied for this job.")
            return

        cur.execute("""
            INSERT INTO applications
                (student_id, job_id, application_date, status)
            VALUES (%s, %s, %s, %s)
        """, (student_id, job_id, date.today(), "Applied"))

        conn.commit()
        print("Application submitted successfully!")

    except mysql.connector.IntegrityError:
        conn.rollback()
        print("Duplicate application or database constraint error.")
    finally:
        cur.close()
        conn.close()


# ================= 6. VIEW APPLICATIONS =================

def view_applications():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT a.application_id, s.name, c.company_name,
                   j.job_role, a.application_date, a.status
            FROM applications a
            JOIN students s ON a.student_id = s.student_id
            JOIN jobs j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY a.application_id
        """)
        show_rows(
            "APPLICATIONS (ID, STUDENT, COMPANY, ROLE, DATE, STATUS)",
            cur.fetchall()
        )
    finally:
        cur.close()
        conn.close()


# ================= 7. UPDATE APPLICATION STATUS =================

def update_application_status():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT application_id, student_id, job_id, status
            FROM applications ORDER BY application_id
        """)
        show_rows("APPLICATIONS (ID, STUDENT ID, JOB ID, STATUS)",
                  cur.fetchall())

        app_id = read_id("Enter Application ID: ")
        if app_id is None:
            return

        status = input(
            "New status (Applied/Shortlisted/Selected/Rejected): "
        ).strip().title()

        allowed = {"Applied", "Shortlisted", "Selected", "Rejected"}
        if status not in allowed:
            print("Invalid status.")
            return

        cur.execute("""
            UPDATE applications
            SET status = %s
            WHERE application_id = %s
        """, (status, app_id))

        if cur.rowcount == 0:
            print("Application not found or status unchanged.")
        else:
            conn.commit()
            print("Application status updated successfully.")
    finally:
        cur.close()
        conn.close()


# ================= 8. SEARCH STUDENT =================

def search_student():
    name = input("Enter all or part of the student's name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT student_id, name, email, branch,
                   cgpa, backlogs, skills
            FROM students
            WHERE name LIKE %s
            ORDER BY name
        """, ("%" + name + "%",))
        show_rows("SEARCH RESULTS", cur.fetchall())
    finally:
        cur.close()
        conn.close()


# ================= 9. ADD STUDENT =================

def add_student():
    name = input("Student name: ").strip()
    email = input("Email: ").strip()
    branch = input("Branch: ").strip()
    cgpa = read_cgpa()
    if cgpa is None:
        return

    backlogs = read_id("Number of backlogs (0 or more): ")
    if backlogs is None:
        return

    skills = input("Skills: ").strip()

    if not name or not email or not branch:
        print("Name, email, and branch are required.")
        return

    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO students
                (name, email, branch, cgpa, backlogs, skills)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, branch, cgpa, backlogs, skills))
        conn.commit()
        print("Student added successfully.")
    except mysql.connector.IntegrityError:
        conn.rollback()
        print("Could not add student. That email may already exist.")
    finally:
        cur.close()
        conn.close()


# ================= 10. DELETE STUDENT =================

def delete_student():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT student_id, name FROM students")
        show_rows("STUDENTS (ID, NAME)", cur.fetchall())

        student_id = read_id("Student ID to delete: ")
        if student_id is None:
            return

        cur.execute(
            "SELECT name FROM students WHERE student_id = %s",
            (student_id,)
        )
        student = cur.fetchone()

        if student is None:
            print("Student not found.")
            return

        cur.execute("""
            SELECT application_id FROM applications
            WHERE student_id = %s
        """, (student_id,))

        if cur.fetchone():
            print(
                "Cannot delete: this student has applications. "
                "Keep the records to preserve application history."
            )
            return

        confirm = input(
            f"Type YES to delete {student[0]}: "
        ).strip()

        if confirm != "YES":
            print("Deletion cancelled.")
            return

        cur.execute(
            "DELETE FROM students WHERE student_id = %s",
            (student_id,)
        )
        conn.commit()
        print("Student deleted successfully.")
    finally:
        cur.close()
        conn.close()


# ================= 11. UPDATE STUDENT DETAILS =================

def update_student():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT student_id, name FROM students")
        show_rows("STUDENTS (ID, NAME)", cur.fetchall())

        student_id = read_id("Student ID to update: ")
        if student_id is None:
            return

        cur.execute(
            "SELECT student_id FROM students WHERE student_id = %s",
            (student_id,)
        )
        if cur.fetchone() is None:
            print("Student not found.")
            return

        name = input("New name: ").strip()
        email = input("New email: ").strip()
        branch = input("New branch: ").strip()
        cgpa = read_cgpa()
        if cgpa is None:
            return

        backlogs = read_id("New number of backlogs: ")
        if backlogs is None:
            return

        skills = input("New skills: ").strip()

        if not name or not email or not branch:
            print("Name, email, and branch are required.")
            return

        cur.execute("""
            UPDATE students
            SET name = %s, email = %s, branch = %s,
                cgpa = %s, backlogs = %s, skills = %s
            WHERE student_id = %s
        """, (
            name, email, branch, cgpa,
            backlogs, skills, student_id
        ))
        conn.commit()
        print("Student details updated successfully.")
    except mysql.connector.IntegrityError:
        conn.rollback()
        print("Update failed. The email may already belong to another student.")
    finally:
        cur.close()
        conn.close()


# ================= 12. ADD COMPANY =================

def add_company():
    name = input("Company name: ").strip()
    location = input("Company location: ").strip()

    if not name:
        print("Company name is required.")
        return

    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO companies (company_name, location)
            VALUES (%s, %s)
        """, (name, location))
        conn.commit()
        print("Company added successfully.")
    finally:
        cur.close()
        conn.close()


# ================= 13. ADD JOB =================

def add_job():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT company_id, company_name
            FROM companies ORDER BY company_id
        """)
        show_rows("COMPANIES (ID, NAME)", cur.fetchall())

        company_id = read_id("Company ID: ")
        if company_id is None:
            return

        cur.execute(
            "SELECT company_id FROM companies WHERE company_id = %s",
            (company_id,)
        )
        if cur.fetchone() is None:
            print("Company not found.")
            return

        role = input("Job role: ").strip()

        try:
            package = float(input("Package in LPA: ").strip())
            if package < 0:
                print("Package cannot be negative.")
                return
        except ValueError:
            print("Enter a valid package amount.")
            return

        min_cgpa = read_cgpa()
        if min_cgpa is None:
            return

        max_backlogs = read_id("Maximum allowed backlogs: ")
        if max_backlogs is None:
            return

        if not role:
            print("Job role is required.")
            return

        cur.execute("""
            INSERT INTO jobs
                (company_id, job_role, package_lpa,
                 min_cgpa, max_backlogs)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            company_id, role, package, min_cgpa, max_backlogs
        ))
        conn.commit()
        print("Job added successfully.")
    finally:
        cur.close()
        conn.close()


# ================= 14. CHECK DUPLICATE APPLICATION =================

def check_duplicate_application():
    conn = connect_db()
    cur = conn.cursor()
    try:
        student_id = read_id("Student ID: ")
        if student_id is None:
            return

        job_id = read_id("Job ID: ")
        if job_id is None:
            return

        cur.execute("""
            SELECT application_id, application_date, status
            FROM applications
            WHERE student_id = %s AND job_id = %s
        """, (student_id, job_id))

        application = cur.fetchone()

        if application:
            print("An application already exists.")
            print(
                f"Application ID: {application[0]} | "
                f"Date: {application[1]} | Status: {application[2]}"
            )
        else:
            print("No existing application found for this student and job.")
            print("The student may apply if they meet the eligibility criteria.")
    finally:
        cur.close()
        conn.close()


# ================= 15. PLACEMENT REPORT =================

def placement_report():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM students")
        total_students = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM companies")
        total_companies = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM applications")
        total_applications = cur.fetchone()[0]

        cur.execute("""
            SELECT status, COUNT(*)
            FROM applications
            GROUP BY status
            ORDER BY status
        """)
        statuses = cur.fetchall()

        cur.execute("""
            SELECT s.name, c.company_name, j.job_role,
                   a.application_date, a.status
            FROM applications a
            JOIN students s ON a.student_id = s.student_id
            JOIN jobs j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY a.application_id
        """)
        records = cur.fetchall()

        print("\n========== PLACEMENT REPORT ==========")
        print("Total students:", total_students)
        print("Total companies:", total_companies)
        print("Total jobs:", total_jobs)
        print("Total applications:", total_applications)
        print("\nApplication status summary:")
        show_rows("STATUS, COUNT", statuses)

        save = input(
            "\nExport detailed applications to placement_report.csv? (yes/no): "
        ).strip().lower()

        if save == "yes":
            # CSV is created in the folder from which Python is run.
            with open(
                "placement_report.csv",
                "w",
                newline="",
                encoding="utf-8"
            ) as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Student", "Company", "Job Role",
                    "Application Date", "Status"
                ])
                writer.writerows(records)

            print("Report saved as placement_report.csv")

    finally:
        cur.close()
        conn.close()

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
)
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/students")

@app.route("/students")
def view_students():
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
            

        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()

        print("Students fetched:", len(students))

        return render_template(
            "students.html",
            students=students
        )

    except mysql.connector.Error as error:
        return f"Database error: {error}", 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()



@app.route("/add-student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        branch = request.form["branch"].strip()
        cgpa = request.form["cgpa"].strip()
        backlogs = request.form["backlogs"].strip()
        skills = request.form["skills"].strip()

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(**DB_CONFIG)

            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO students
                    (name, email, branch, cgpa, backlogs, skills)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, email, branch, float(cgpa),
                  int(backlogs), skills))

            connection.commit()
            return redirect("/students")

        except (mysql.connector.Error, ValueError) as error:
            return f"Could not add student: {error}", 400

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("add_student.html")

@app.route("/search-student", methods=["GET", "POST"])
def search_student():
    students = []

    if request.method == "POST":
        search_term = request.form["search_term"].strip()

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT *
                FROM students
                WHERE name LIKE %s OR email LIKE %s
                """,
                (f"%{search_term}%", f"%{search_term}%")
            )

            students = cursor.fetchall()

        except mysql.connector.Error as error:
            return f"Database error: {error}", 500

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("search_student.html", students=students)

@app.route("/update-student/<int:student_id>", methods=["GET", "POST"])
def update_student(student_id):
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":
            name = request.form["name"].strip()
            email = request.form["email"].strip()
            branch = request.form["branch"].strip()
            cgpa = float(request.form["cgpa"])
            backlogs = int(request.form["backlogs"])
            skills = request.form["skills"].strip()

            cursor.execute(
                """
                UPDATE students
                SET name=%s, email=%s, branch=%s, cgpa=%s,
                    backlogs=%s, skills=%s
                WHERE student_id=%s
                """,
                (name, email, branch, cgpa, backlogs, skills, student_id)
            )

            connection.commit()
            return redirect("/students")

        cursor.execute(
            "SELECT * FROM students WHERE student_id = %s",
            (student_id,)
        )
        student = cursor.fetchone()

        if student is None:
            return "Student not found", 404

        return render_template("update_student.html", student=student)

    except (mysql.connector.Error, ValueError) as error:
        return f"Could not update student: {error}", 400

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

@app.route("/delete-student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM students WHERE student_id = %s",
            (student_id,)
        )
        connection.commit()

        return redirect("/students")

    except mysql.connector.Error as error:
        return f"Could not delete student: {error}", 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

# ---------------- COMPANY MANAGEMENT ----------------

@app.route("/companies")
def view_companies():
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT company_id, company_name, location "
            "FROM companies ORDER BY company_id"
        )
        companies = cursor.fetchall()

        return render_template(
            "companies.html",
            companies=companies
        )

    except mysql.connector.Error as error:
        return f"Database error: {error}", 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/add-company", methods=["GET", "POST"])
def add_company():
    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        location = request.form.get("location", "").strip()

        if not company_name or not location:
            return "Company name and location are required.", 400

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO companies (company_name, location) "
                "VALUES (%s, %s)",
                (company_name, location)
            )
            connection.commit()

            return redirect("/companies")

        except mysql.connector.Error as error:
            return f"Could not add company: {error}", 500

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("add_company.html")


@app.route(
    "/update-company/<int:company_id>",
    methods=["GET", "POST"]
)
def update_company(company_id):
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":
            company_name = request.form.get(
                "company_name", ""
            ).strip()
            location = request.form.get("location", "").strip()

            if not company_name or not location:
                return "Company name and location are required.", 400

            cursor.execute(
                "UPDATE companies "
                "SET company_name = %s, location = %s "
                "WHERE company_id = %s",
                (company_name, location, company_id)
            )
            connection.commit()

            return redirect("/companies")

        cursor.execute(
            "SELECT company_id, company_name, location "
            "FROM companies WHERE company_id = %s",
            (company_id,)
        )
        company = cursor.fetchone()

        if company is None:
            return "Company not found.", 404

        return render_template(
            "update_company.html",
            company=company
        )

    except mysql.connector.Error as error:
        return f"Company update error: {error}", 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route(
    "/delete-company/<int:company_id>",
    methods=["POST"]
)
def delete_company(company_id):
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM companies WHERE company_id = %s",
            (company_id,)
        )
        connection.commit()

        return redirect("/companies")

    except mysql.connector.Error as error:
        return (
            "Could not delete company. It may be linked to existing "
            f"jobs. Database error: {error}"
        ), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

# ---------------- END COMPANY MANAGEMENT ----------------
@app.route("/jobs")
def jobs():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT jobs.job_id, companies.company_name,
               jobs.job_role, jobs.package_lpa,
               jobs.min_cgpa, jobs.max_backlogs
        FROM jobs
        JOIN companies
        ON jobs.company_id = companies.company_id
    """)

    job_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("jobs.html", jobs=job_list)

@app.route("/applications")
def applications():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT applications.application_id,
               students.name,
               jobs.job_role,
               applications.application_date,
               applications.status
        FROM applications
        JOIN students
            ON applications.student_id = students.student_id
        JOIN jobs
            ON applications.job_id = jobs.job_id
    """)

    application_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "applications.html",
        applications=application_list
    )

@app.route("/apply-job", methods=["GET", "POST"])
def apply_job():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        student_id = request.form["student_id"]
        job_id = request.form["job_id"]

        cursor.execute(
            "SELECT * FROM applications WHERE student_id = %s AND job_id = %s",
            (student_id, job_id)
        )

        if cursor.fetchone():
            cursor.close()
            connection.close()
            return "You have already applied for this job."

        cursor.close()
        cursor = connection.cursor()

        cursor.execute(
            """INSERT INTO applications
               (student_id, job_id, application_date, status)
               VALUES (%s, %s, CURDATE(), %s)""",
            (student_id, job_id, "Applied")
        )

        connection.commit()
        cursor.close()
        connection.close()

        return redirect("/applications")

    cursor.execute("SELECT student_id, name FROM students")
    students = cursor.fetchall()

    cursor.execute("SELECT job_id, job_role FROM jobs")
    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "apply_job.html",
        students=students,
        jobs=jobs
    )


@app.route("/dashboard")
def dashboard():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications")
    total_applications = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM applications
        WHERE status = 'Selected'
    """)
    total_selected = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM applications
        WHERE status = 'Shortlisted'
    """)
    total_shortlisted = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_companies=total_companies,
        total_jobs=total_jobs,
        total_applications=total_applications,
        total_selected=total_selected,
        total_shortlisted=total_shortlisted
    )


@app.route("/search-job", methods=["GET", "POST"])
def search_job():
    results = []

    if request.method == "POST":
        search_term = request.form["search_term"]

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT jobs.job_id, companies.company_name,
                   jobs.job_role, jobs.package_lpa,
                   jobs.min_cgpa, jobs.max_backlogs
            FROM jobs
            JOIN companies
                ON jobs.company_id = companies.company_id
            WHERE jobs.job_role LIKE %s
               OR companies.company_name LIKE %s
        """, (f"%{search_term}%", f"%{search_term}%"))

        results = cursor.fetchall()
        cursor.close()
        connection.close()

    return render_template("search_job.html", jobs=results)

@app.route("/eligible-jobs", methods=["GET", "POST"])
def eligible_jobs():
    eligible = []
    students = []

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT student_id, name, cgpa, backlogs FROM students")
    students = cursor.fetchall()

    if request.method == "POST":
        student_id = request.form["student_id"]

        cursor.execute(
            "SELECT cgpa, backlogs FROM students WHERE student_id = %s",
            (student_id,)
        )
        student = cursor.fetchone()

        if student:
            cursor.execute("""
                SELECT jobs.job_id, companies.company_name,
                       jobs.job_role, jobs.package_lpa,
                       jobs.min_cgpa, jobs.max_backlogs
                FROM jobs
                JOIN companies
                    ON jobs.company_id = companies.company_id
                WHERE jobs.min_cgpa <= %s
                  AND jobs.max_backlogs >= %s
            """, (student["cgpa"], student["backlogs"]))

            eligible = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "eligible_jobs.html",
        students=students,
        jobs=eligible
    )

@app.route("/update-application/<int:application_id>", methods=["GET", "POST"])
def update_application(application_id):
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        status = request.form["status"]

        cursor.execute(
            "UPDATE applications SET status = %s WHERE application_id = %s",
            (status, application_id)
        )

        connection.commit()
        cursor.close()
        connection.close()

        return redirect("/applications")

    cursor.execute(
        "SELECT * FROM applications WHERE application_id = %s",
        (application_id,)
    )
    application = cursor.fetchone()

    cursor.close()
    connection.close()

    if application is None:
        return "Application not found", 404

    return render_template(
        "update_application.html",
        application=application
    )

@app.route("/delete-application/<int:application_id>", methods=["POST"])
def delete_application(application_id):
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM applications WHERE application_id = %s",
        (application_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

    return redirect("/applications")

@app.route("/student-profile/<int:student_id>")
def student_profile(student_id):
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE student_id = %s",
        (student_id,)
    )

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    if student is None:
        return "Student not found", 404

    return render_template("student_profile.html", student=student)

import csv
import io
from flask import Response

@app.route("/export-students")
def export_students():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT student_id, name, email, branch,
               cgpa, backlogs, skills
        FROM students
    """)

    students = cursor.fetchall()
    cursor.close()
    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Student ID", "Name", "Email", "Branch",
        "CGPA", "Backlogs", "Skills"
    ])
    writer.writerows(students)

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=students.csv"
        }
    )

@app.route("/export-applications")
def export_applications():
    import csv
    import io
    from flask import Response

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT application_id, student_id, job_id,
               application_date, status
        FROM applications
    """)

    records = cursor.fetchall()
    cursor.close()
    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Application ID", "Student ID", "Job ID",
        "Application Date", "Status"
    ])
    writer.writerows(records)

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=applications.csv"
        }
    )


@app.route("/export-jobs")
def export_jobs():
    import csv
    import io
    from flask import Response

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT job_id, company_id, job_role,
               package_lpa, min_cgpa, max_backlogs
        FROM jobs
    """)

    records = cursor.fetchall()
    cursor.close()
    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Job ID", "Company ID", "Job Role",
        "Package LPA", "Minimum CGPA", "Maximum Backlogs"
    ])
    writer.writerows(records)

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=jobs.csv"
        }
    )

@app.route("/export-companies")
def export_companies():
    import csv
    import io
    from flask import Response

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT company_id, company_name, location
        FROM companies
    """)

    records = cursor.fetchall()
    cursor.close()
    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Company ID", "Company Name", "Location"])
    writer.writerows(records)

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=companies.csv"
        }
    )

@app.route("/placement-report")
def placement_report():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT students.student_id,
               students.name,
               companies.company_name,
               jobs.job_role,
               applications.application_date,
               applications.status
        FROM applications
        JOIN students
            ON applications.student_id = students.student_id
        JOIN jobs
            ON applications.job_id = jobs.job_id
        JOIN companies
            ON jobs.company_id = companies.company_id
        ORDER BY students.name
    """)

    reports = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("placement_report.html", reports=reports)
@app.route("/export-placement-report")
def export_placement_report():
    import csv
    from flask import make_response

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT s.student_id, s.name, c.company_name,
               j.job_role, a.application_date, a.status
        FROM applications a
        JOIN students s ON a.student_id = s.student_id
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY s.name
    """)

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    output = make_response()
    output.headers["Content-Type"] = "text/csv"
    output.headers["Content-Disposition"] = (
        "attachment; filename=placement_report.csv"
    )

    import io
    file_data = io.StringIO()
    writer = csv.writer(file_data)

    writer.writerow([
        "Student ID", "Student Name", "Company",
        "Job Role", "Application Date", "Status"
    ])
    writer.writerows(rows)

    output.set_data(file_data.getvalue())
    return output






# ================= MAIN MENU =================

def main():
    while True:
        print("\n===== STUDENT PLACEMENT MANAGEMENT SYSTEM =====")
        print("1. View All Students")
        print("2. View All Companies")
        print("3. View All Jobs")
        print("4. Check Eligible Students")
        print("5. Apply for a Job")
        print("6. View Applications")
        print("7. Update Application Status")
        print("8. Search Student")
        print("9. Add a New Student")
        print("10. Delete a Student")
        print("11. Update Student Details")
        print("12. Add a New Company")
        print("13. Add a New Job")
        print("14. Check Duplicate Application")
        print("15. Generate Placement Report")
        print("16. Exit")

        choice = input("Enter your choice: ").strip()

        actions = {
            "1": view_students,
            "2": view_companies,
            "3": view_jobs,
            "4": check_eligible_students,
            "5": apply_for_job,
            "6": view_applications,
            "7": update_application_status,
            "8": search_student,
            "9": add_student,
            "10": delete_student,
            "11": update_student,
            "12": add_company,
            "13": add_job,
            "14": check_duplicate_application,
            "15": placement_report
        }

        if choice == "16":
            print("Thank you for using the system!")
            break

        action = actions.get(choice)

        if action is None:
            print("Invalid choice. Enter a number from 1 to 16.")
            continue

        try:
            action()
        except mysql.connector.Error as error:
            print("Database error:", error)
        except OSError as error:
            print("File error:", error)



if __name__ == "__main__":
    print("Starting Student Placement System website...")
    app.run(debug=True)
