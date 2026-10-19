
CREATE DATABASE IF NOT EXISTS student_placement_db;

USE student_placement_db;

CREATE TABLE IF NOT EXISTS students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    branch VARCHAR(100),
    cgpa DECIMAL(4,2),
    backlogs INT DEFAULT 0,
    skills TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    location VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    job_role VARCHAR(100) NOT NULL,
    package_lpa DECIMAL(5,2),
    min_cgpa DECIMAL(4,2) DEFAULT 0,
    max_backlogs INT DEFAULT 0,
    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    job_id INT NOT NULL,
    application_date DATE,
    status VARCHAR(30) DEFAULT 'Applied',
    UNIQUE (student_id, job_id),
    FOREIGN KEY (student_id)
        REFERENCES students(student_id),
    FOREIGN KEY (job_id)
        REFERENCES jobs(job_id)
);
