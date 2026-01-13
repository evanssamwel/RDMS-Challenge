"""
Populate School ERP System with Sample Data
Generates realistic school data for demonstration
"""

import sys
import os
import random
from datetime import datetime, timedelta
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import QueryEngine
from core.storage import Storage

# Sample data
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
               "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
               "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra",
               "Donald", "Ashley", "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

KENYAN_STREETS = ["Kenyatta Avenue", "Moi Avenue", "University Way", "Ngong Road", "Thika Road", 
                  "Waiyaki Way", "Jogoo Road", "Lang'ata Road", "Kiambu Road", "Limuru Road"]

COURSE_TITLES = [
    ("Introduction to Computer Science", "CS101", "Fundamentals of programming and algorithms"),
    ("Data Structures & Algorithms", "CS201", "Advanced data structures and algorithmic techniques"),
    ("Database Systems", "CS301", "Relational databases and SQL"),
    ("Web Development", "CS202", "HTML, CSS, JavaScript, and frameworks"),
    ("Calculus I", "MATH101", "Limits, derivatives, and integrals"),
    ("Linear Algebra", "MATH201", "Vectors, matrices, and transformations"),
    ("Physics I", "PHY101", "Classical mechanics and thermodynamics"),
    ("Chemistry I", "CHEM101", "Atomic structure and chemical reactions"),
    ("English Composition", "ENG101", "Academic writing and critical thinking"),
    ("Business Management", "BUS201", "Principles of management and organization"),
    ("Marketing Fundamentals", "BUS301", "Marketing strategies and consumer behavior"),
    ("Financial Accounting", "ACC101", "Principles of accounting and financial statements"),
    ("Microeconomics", "ECON201", "Supply, demand, and market structures"),
    ("Psychology 101", "PSY101", "Introduction to psychological concepts"),
    ("Sociology", "SOC101", "Social structures and cultural dynamics")
]

BOOK_TITLES = [
    ("Introduction to Algorithms", "Cormen et al.", "Computer Science"),
    ("Clean Code", "Robert Martin", "Programming"),
    ("Design Patterns", "Gang of Four", "Software Engineering"),
    ("The Pragmatic Programmer", "Hunt & Thomas", "Programming"),
    ("Calculus Early Transcendentals", "James Stewart", "Mathematics"),
    ("Linear Algebra Done Right", "Sheldon Axler", "Mathematics"),
    ("Physics for Scientists", "Serway & Jewett", "Physics"),
    ("Chemistry: The Central Science", "Brown et al.", "Chemistry"),
    ("Principles of Economics", "Mankiw", "Economics"),
    ("Psychology", "David Myers", "Psychology")
]

def populate_school_data():
    """Populate the school database with sample data"""
    
    print("\n" + "="*60)
    print("📊 Populating School ERP with Sample Data")
    print("="*60 + "\n")
    
    # "Database" folder (MariaDB-like): databases/school_erp
    # This generator assumes full control over demo schema. If the web app already
    # created tables with different columns, INSERTs can fail, so we reset the folder.
    db_dir = os.path.join('databases', 'school_erp')
    if os.path.isdir(db_dir):
        print(f"🧹 Resetting demo database folder: {db_dir}")
        shutil.rmtree(db_dir, ignore_errors=True)

    storage = Storage(data_dir=db_dir)
    engine = QueryEngine(storage)

    def exec_sql(sql: str):
        res = engine.execute(sql)
        if isinstance(res, dict) and res.get('success') is False:
            raise ValueError(res.get('error') or 'SQL failed')
        return res

    def sql_str(value) -> str:
        """Sanitize text for this project's simple SQL parser.

        It is not robust for commas inside quoted strings, so we remove commas.
        Also escape single quotes and normalize whitespace.
        """
        if value is None:
            return ''
        text = str(value)
        text = text.replace("'", "''")
        text = text.replace(",", " ")
        text = text.replace("\r", " ").replace("\n", " ")
        return " ".join(text.split())

    def ensure_schema():
        """Create all School ERP tables if missing."""
        print("🧱 Ensuring schema exists...")

        if storage.get_table('users') is None:
            exec_sql("""
                CREATE TABLE users (
                    id INT PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100) UNIQUE,
                    role VARCHAR(20),
                    phone VARCHAR(20),
                    address VARCHAR(200),
                    date_of_birth DATE,
                    enrollment_date DATE
                )
            """)

        if storage.get_table('auth_users') is None:
            exec_sql("""
                CREATE TABLE auth_users (
                    id INT PRIMARY KEY,
                    user_id INT,
                    name VARCHAR(100),
                    email VARCHAR(100) UNIQUE,
                    password VARCHAR(100),
                    role VARCHAR(20),
                    created_at VARCHAR(50)
                )
            """)

        if storage.get_table('courses') is None:
            exec_sql("""
                CREATE TABLE courses (
                    id INT PRIMARY KEY,
                    title VARCHAR(150),
                    code VARCHAR(20) UNIQUE,
                    description VARCHAR(300),
                    teacher_id INT,
                    credits INT,
                    semester VARCHAR(20),
                    capacity INT,
                    room VARCHAR(50)
                )
            """)

        if storage.get_table('enrollments') is None:
            exec_sql("""
                CREATE TABLE enrollments (
                    id INT PRIMARY KEY,
                    student_id INT,
                    course_id INT,
                    grade VARCHAR(5),
                    enrollment_date DATE,
                    status VARCHAR(20),
                    midterm_score FLOAT,
                    final_score FLOAT
                )
            """)

        if storage.get_table('financials') is None:
            exec_sql("""
                CREATE TABLE financials (
                    id INT PRIMARY KEY,
                    student_id INT,
                    semester VARCHAR(20),
                    total_fees FLOAT,
                    fees_paid FLOAT,
                    balance FLOAT,
                    payment_date DATE,
                    payment_status VARCHAR(20)
                )
            """)

        if storage.get_table('attendance') is None:
            exec_sql("""
                CREATE TABLE attendance (
                    id INT PRIMARY KEY,
                    student_id INT,
                    course_id INT,
                    date DATE,
                    status VARCHAR(20),
                    remarks VARCHAR(200)
                )
            """)

        if storage.get_table('books') is None:
            exec_sql("""
                CREATE TABLE books (
                    id INT PRIMARY KEY,
                    title VARCHAR(200),
                    author VARCHAR(100),
                    isbn VARCHAR(20) UNIQUE,
                    category VARCHAR(50),
                    total_copies INT,
                    available_copies INT,
                    shelf_location VARCHAR(50)
                )
            """)

        if storage.get_table('borrowings') is None:
            exec_sql("""
                CREATE TABLE borrowings (
                    id INT PRIMARY KEY,
                    student_id INT,
                    book_id INT,
                    borrow_date DATE,
                    due_date DATE,
                    return_date DATE,
                    status VARCHAR(20),
                    fine FLOAT
                )
            """)

        if storage.get_table('exams') is None:
            exec_sql("""
                CREATE TABLE exams (
                    id INT PRIMARY KEY,
                    course_id INT,
                    exam_type VARCHAR(50),
                    exam_date DATE,
                    max_marks INT,
                    duration_minutes INT,
                    room VARCHAR(50)
                )
            """)

        if storage.get_table('departments') is None:
            exec_sql("""
                CREATE TABLE departments (
                    id INT PRIMARY KEY,
                    name VARCHAR(100),
                    head_teacher_id INT,
                    building VARCHAR(50),
                    budget FLOAT
                )
            """)

        if storage.get_table('system_logs') is None:
            exec_sql("""
                CREATE TABLE system_logs (
                    id INT PRIMARY KEY,
                    timestamp VARCHAR(50),
                    user_role VARCHAR(20),
                    action VARCHAR(100),
                    sql_command VARCHAR(500),
                    status VARCHAR(20)
                )
            """)

        # Helpful indexes (ignore if they already exist)
        try:
            exec_sql("CREATE INDEX idx_users_role ON users (role)")
        except Exception:
            pass
        try:
            exec_sql("CREATE INDEX idx_auth_email ON auth_users (email)")
        except Exception:
            pass
        try:
            exec_sql("CREATE INDEX idx_auth_role ON auth_users (role)")
        except Exception:
            pass
        try:
            exec_sql("CREATE INDEX idx_enrollments_student ON enrollments (student_id)")
            exec_sql("CREATE INDEX idx_enrollments_course ON enrollments (course_id)")
            exec_sql("CREATE INDEX idx_attendance_student ON attendance (student_id)")
            exec_sql("CREATE INDEX idx_financials_student ON financials (student_id)")
            exec_sql("CREATE INDEX idx_borrowings_student ON borrowings (student_id)")
        except Exception:
            pass

        print("✅ Schema ready")

    ensure_schema()
    
    # Clear existing data (if any)
    print("🗑️  Clearing existing data...")
    for table in storage.list_tables():
        try:
            exec_sql(f"DELETE FROM {table}")
        except:
            pass
    
    # Demo login accounts (known passwords)
    print("\n🔐 Creating demo login accounts...")
    demo_accounts = [
        (99991, "System Administrator", "admin@school.edu", "Admin", "admin123"),
        (99992, "Prof. John Doe", "teacher@school.edu", "Teacher", "teacher123"),
        (99993, "Alice Smith", "student@school.edu", "Student", "student123"),
        (99994, "Jane Official", "registrar@school.edu", "Registrar", "registrar123"),
    ]
    for uid, name, email, role, pwd in demo_accounts:
        phone = f"+2547{random.randint(10000000, 99999999)}"
        address = f"{random.randint(1, 999)} {random.choice(KENYAN_STREETS)} Nairobi"
        dob = f"{random.randint(1980, 2006)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        enrollment = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"

        exec_sql(f"""
            INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
            VALUES ({uid}, '{sql_str(name)}', '{email}', '{role}', '{phone}', '{sql_str(address)}', '{dob}', '{enrollment}')
        """)
        exec_sql(f"""
            INSERT INTO auth_users (id, user_id, name, email, password, role, created_at)
            VALUES ({uid}, {uid}, '{sql_str(name)}', '{email}', '{pwd}', '{role}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
        """)

    # Generate Students
    STUDENT_COUNT = 800
    print(f"\n👨‍🎓 Creating {STUDENT_COUNT} students...")
    student_ids = []
    for i in range(STUDENT_COUNT):
        user_id = 1000 + i
        student_ids.append(user_id)
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{i}@school.edu"
        phone = f"+2547{random.randint(10000000, 99999999)}"
        address = f"{random.randint(1, 999)} {random.choice(KENYAN_STREETS)} Nairobi"
        dob = f"{random.randint(2003, 2008)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        enrollment = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        
        exec_sql(f"""
            INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
            VALUES ({user_id}, '{sql_str(first_name + ' ' + last_name)}', '{email}', 'Student', 
                '{phone}', '{sql_str(address)}', '{dob}', '{enrollment}')
        """)

        # Create auth account (shared demo password for easy testing)
        exec_sql(f"""
            INSERT INTO auth_users (id, user_id, name, email, password, role, created_at)
            VALUES ({user_id}, {user_id}, '{sql_str(first_name + ' ' + last_name)}', '{email}', 'student123', 'Student', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
        """)
    
    print(f"✅ Created {len(student_ids)} students")
    
    # Generate Teachers
    TEACHER_COUNT = 60
    print(f"\n👨‍🏫 Creating {TEACHER_COUNT} teachers...")
    teacher_ids = []
    for i in range(TEACHER_COUNT):
        user_id = 2000 + i
        teacher_ids.append(user_id)
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}.teacher{i}@school.edu"
        phone = f"+2547{random.randint(10000000, 99999999)}"
        address = f"{random.randint(1, 999)} {random.choice(KENYAN_STREETS)} Nairobi"
        dob = f"{random.randint(1975, 1995)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        enrollment = f"{random.randint(2015, 2023)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        
        exec_sql(f"""
            INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
            VALUES ({user_id}, 'Prof. {sql_str(first_name + ' ' + last_name)}', '{email}', 'Teacher', 
                '{phone}', '{sql_str(address)}', '{dob}', '{enrollment}')
        """)

        exec_sql(f"""
            INSERT INTO auth_users (id, user_id, name, email, password, role, created_at)
            VALUES ({user_id}, {user_id}, 'Prof. {sql_str(first_name + ' ' + last_name)}', '{email}', 'teacher123', 'Teacher', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
        """)
    
    print(f"✅ Created {len(teacher_ids)} teachers")
    
    # Generate Courses
    # Start with curated list, then extend with synthetic courses.
    EXTRA_COURSES = 15
    print(f"\n📚 Creating {len(COURSE_TITLES) + EXTRA_COURSES} courses...")
    course_ids = []
    all_course_defs = list(COURSE_TITLES)
    for i in range(EXTRA_COURSES):
        all_course_defs.append(
            (
                f"Special Topics in Computing {i+1}",
                f"SPC{300+i}",
                "Applied projects and research readings with practical assessments"
            )
        )

    for i, (title, code, description) in enumerate(all_course_defs):
        course_id = 100 + i
        course_ids.append(course_id)
        teacher_id = random.choice(teacher_ids)
        credits = random.choice([3, 4])
        semester = random.choice(["Fall 2026", "Spring 2026"])
        capacity = random.randint(30, 50)
        room = f"Room {random.randint(101, 450)}"
        
        exec_sql(f"""
            INSERT INTO courses (id, title, code, description, teacher_id, credits, semester, capacity, room)
            VALUES ({course_id}, '{sql_str(title)}', '{code}', '{sql_str(description)}', {teacher_id}, 
                {credits}, '{semester}', {capacity}, '{sql_str(room)}')
        """)
    
    print(f"✅ Created {len(course_ids)} courses")
    
    # Generate Enrollments
    print("\n📝 Creating enrollments (students enrolled in courses)...")
    enrollment_id = 10000
    grades = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F", "N/A"]
    statuses = ["Active", "Active", "Active", "Completed", "Dropped"]
    
    for student_id in random.sample(student_ids, min(650, len(student_ids))):
        courses_to_enroll = random.sample(course_ids, random.randint(4, 7))
        for course_id in courses_to_enroll:
            enrollment_id += 1
            grade = random.choice(grades)
            status = random.choice(statuses)
            midterm = round(random.uniform(40, 100), 1)
            final = round(random.uniform(40, 100), 1)
            enrollment_date = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            
            exec_sql(f"""
                INSERT INTO enrollments (id, student_id, course_id, grade, enrollment_date, status, midterm_score, final_score)
                VALUES ({enrollment_id}, {student_id}, {course_id}, '{grade}', '{enrollment_date}', 
                        '{status}', {midterm}, {final})
            """)
    
    print(f"✅ Created {enrollment_id - 10000} enrollments")
    
    # Generate Financials (one per student per semester)
    print("\n💰 Creating financial records...")
    financial_id = 50000
    for student_id in random.sample(student_ids, min(700, len(student_ids))):
        for semester in ["Fall 2026", "Spring 2026"]:
            financial_id += 1
            total_fees = round(random.uniform(50000, 150000), 2)
            fees_paid = round(random.uniform(0, total_fees), 2)
            balance = round(total_fees - fees_paid, 2)
            payment_date = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            payment_status = "Paid" if balance <= 0 else ("Partial" if fees_paid > 0 else "Pending")
            
            exec_sql(f"""
                INSERT INTO financials (id, student_id, semester, total_fees, fees_paid, balance, payment_date, payment_status)
                VALUES ({financial_id}, {student_id}, '{semester}', {total_fees}, {fees_paid}, 
                        {balance}, '{payment_date}', '{payment_status}')
            """)
    
    print(f"✅ Created {financial_id - 50000} financial records")
    
    # Generate Attendance Records
    print("\n📋 Creating attendance records...")
    attendance_id = 60000
    for _ in range(4000):
        attendance_id += 1
        student_id = random.choice(student_ids)
        course_id = random.choice(course_ids)
        date = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        status = random.choice(["Present", "Present", "Present", "Absent", "Late"])
        remarks = random.choice(["", "", "Medical excuse", "Family emergency", ""])
        
        exec_sql(f"""
            INSERT INTO attendance (id, student_id, course_id, date, status, remarks)
            VALUES ({attendance_id}, {student_id}, {course_id}, '{date}', '{status}', '{remarks}')
        """)
    
    print(f"✅ Created {attendance_id - 60000} attendance records")
    
    # Generate Library Books
    print("\n📖 Creating library books...")
    book_id = 300
    for i, (title, author, category) in enumerate(BOOK_TITLES):
        book_id += 1
        isbn = f"978-{random.randint(0, 9)}-{random.randint(100, 999)}-{random.randint(10000, 99999)}-{random.randint(0, 9)}"
        total_copies = random.randint(3, 10)
        available_copies = random.randint(0, total_copies)
        shelf_location = f"{random.choice(['A', 'B', 'C', 'D'])}-{random.randint(1, 20):02d}-{random.randint(1, 10):02d}"
        
        exec_sql(f"""
            INSERT INTO books (id, title, author, isbn, category, total_copies, available_copies, shelf_location)
            VALUES ({book_id}, '{title}', '{author}', '{isbn}', '{category}', 
                    {total_copies}, {available_copies}, '{shelf_location}')
        """)
    
    print(f"✅ Created {book_id - 300} books")
    
    # Generate Book Borrowings
    print("\n📚 Creating book borrowing records...")
    borrowing_id = 70000
    for _ in range(450):
        borrowing_id += 1
        student_id = random.choice(student_ids)
        book_id_sample = random.randint(301, book_id)
        borrow_date = datetime.now() - timedelta(days=random.randint(0, 30))
        due_date = borrow_date + timedelta(days=14)
        return_date_obj = None if random.random() > 0.7 else borrow_date + timedelta(days=random.randint(1, 20))
        status = "Returned" if return_date_obj else "Borrowed"
        fine = 0 if status == "Returned" else (random.randint(0, 500) if random.random() > 0.8 else 0)
        
        borrow_str = borrow_date.strftime("%Y-%m-%d")
        due_str = due_date.strftime("%Y-%m-%d")
        return_str = return_date_obj.strftime("%Y-%m-%d") if return_date_obj else "NULL"
        
        exec_sql(f"""
            INSERT INTO borrowings (id, student_id, book_id, borrow_date, due_date, return_date, status, fine)
            VALUES ({borrowing_id}, {student_id}, {book_id_sample}, '{borrow_str}', '{due_str}', 
                    {f"'{return_str}'" if return_str != "NULL" else "NULL"}, '{status}', {fine})
        """)

    # Generate Exams
    print("\n🧪 Creating exams (midterm + final)...")
    exam_id = 80000
    for course_id in course_ids:
        for exam_type, offset in [("Midterm", 20), ("Final", 60)]:
            exam_id += 1
            exam_date = (datetime.now() + timedelta(days=offset + random.randint(0, 14))).strftime("%Y-%m-%d")
            max_marks = 100
            duration = random.choice([60, 90, 120])
            room = f"Exam Hall {random.randint(1, 5)}"
            exec_sql(f"""
                INSERT INTO exams (id, course_id, exam_type, exam_date, max_marks, duration_minutes, room)
                VALUES ({exam_id}, {course_id}, '{exam_type}', '{exam_date}', {max_marks}, {duration}, '{room}')
            """)

    # Generate Departments
    print("\n🏢 Creating departments...")
    dept_names = [
        (1, "Computer Science", "ICT Block"),
        (2, "Mathematics", "Science Block"),
        (3, "Business", "Business Block"),
        (4, "Humanities", "Arts Block"),
        (5, "Natural Sciences", "Science Block"),
        (6, "Languages", "Arts Block"),
    ]
    for dept_id, dept_name, building in dept_names:
        head_teacher_id = random.choice(teacher_ids)
        budget = round(random.uniform(2_000_000, 15_000_000), 2)
        exec_sql(f"""
            INSERT INTO departments (id, name, head_teacher_id, building, budget)
            VALUES ({dept_id}, '{dept_name}', {head_teacher_id}, '{building}', {budget})
        """)

    # Seed System Logs (so dashboards look alive)
    print("\n🧾 Seeding system logs...")
    log_id = 900000
    for _ in range(50):
        log_id += 1
        ts = (datetime.now() - timedelta(minutes=random.randint(0, 600))).strftime("%Y-%m-%d %H:%M:%S")
        role = random.choice(["Admin", "Teacher", "Student", "Registrar", "API"])
        action = random.choice(["Login", "Fetch Users", "Fetch Courses", "Update Grade", "Bulk Import", "Analytics"])
        sql_cmd = random.choice([
            "SELECT * FROM users LIMIT 10",
            "SELECT * FROM courses",
            "SELECT * FROM enrollments LIMIT 10",
            "UPDATE enrollments SET grade='B' WHERE id=10001",
            "SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 20"
        ])
        status = random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "ERROR"])
        exec_sql(f"""
            INSERT INTO system_logs (id, timestamp, user_role, action, sql_command, status)
            VALUES ({log_id}, '{ts}', '{role}', '{action}', '{sql_cmd}', '{status}')
        """)
    
    print(f"✅ Created {borrowing_id - 70000} borrowing records")
    
    print("\n" + "="*60)
    print("✅ School ERP Database Population Complete!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   • {len(student_ids)} Students")
    print(f"   • {len(teacher_ids)} Teachers")
    print(f"   • {len(course_ids)} Courses")
    print(f"   • {enrollment_id - 10000} Enrollments")
    print(f"   • {financial_id - 50000} Financial Records")
    print(f"   • {attendance_id - 60000} Attendance Records")
    print(f"   • {book_id - 300} Library Books")
    print(f"   • {borrowing_id - 70000} Book Borrowings")
    print(f"   • {exam_id - 80000} Exams")
    print(f"   • {len(dept_names)} Departments")
    print(f"   • 50 System Logs")
    print(f"\n🚀 Ready to test the School ERP system!\n")

if __name__ == "__main__":
    populate_school_data()
