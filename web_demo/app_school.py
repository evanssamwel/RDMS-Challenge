"""
SimpleSQLDB - School Management ERP System
A feature-rich school management system demonstrating complex RDBMS operations
Showcases multi-table relationships, foreign keys, aggregates, and real-world business logic
"""

from flask import Flask, render_template, request, jsonify, session, redirect
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import QueryEngine
from core.storage import Storage

app = Flask(__name__)
app.secret_key = 'school-erp-simplesqldb-2026'

# Demo Credentials
DEMO_USERS = {
    'admin@school.edu': {'password': 'admin123', 'role': 'Admin', 'name': 'System Administrator', 'id': 99991},
    'teacher@school.edu': {'password': 'teacher123', 'role': 'Teacher', 'name': 'Prof. John Doe', 'id': 99992},
    'student@school.edu': {'password': 'student123', 'role': 'Student', 'name': 'Alice Smith', 'id': 99993},
    'registrar@school.edu': {'password': 'registrar123', 'role': 'Registrar', 'name': 'Jane Official', 'id': 99994}
}

# Initialize database ("database" == a folder, like MariaDB databases)
DB_NAME = 'school_erp'
DB_DIR = os.path.join('databases', DB_NAME)
storage = Storage(data_dir=DB_DIR)
engine = QueryEngine(storage)


def db_exec(sql: str) -> dict:
    """Execute SQL and raise on failure (QueryEngine.execute returns a dict)."""
    result = engine.execute(sql)
    if isinstance(result, dict) and result.get('success') is False:
        raise ValueError(result.get('error') or 'SQL execution failed')
    return result


def db_rows(sql: str):
    """Execute a SELECT and return rows list (empty list on no rows)."""
    result = engine.execute(sql)
    if isinstance(result, dict):
        if result.get('success') is False:
            raise ValueError(result.get('error') or 'SQL query failed')
        return result.get('rows') or []
    # Backward-compat (if engine ever returns raw rows)
    return result or []

# Track initialization status
system_initialized = False


def init_school_database():
    """Initialize comprehensive school management database schema"""
    global system_initialized
    
    if system_initialized:
        return

    # If tables already exist on disk, don't recreate; just ensure auth tables exist.
    if storage.get_table('users') is not None:
        if storage.get_table('auth_users') is None:
            try:
                db_exec("""
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
                db_exec("CREATE INDEX idx_auth_email ON auth_users (email)")
                db_exec("CREATE INDEX idx_auth_role ON auth_users (role)")
            except Exception:
                pass

        system_initialized = True
        ensure_demo_data()
        return
    
    print("🏫 Initializing School Management ERP Database...")
    
    # Users Table (Students, Teachers, Admins)
    db_exec("""
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

    # Auth Users Table (Login credentials + roles)
    db_exec("""
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
    
    # Courses Table
    db_exec("""
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
    
    # Enrollments Table (Many-to-Many: Students ↔ Courses)
    db_exec("""
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
    
    # Financials Table
    db_exec("""
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
    
    # Attendance Table
    db_exec("""
        CREATE TABLE attendance (
            id INT PRIMARY KEY,
            student_id INT,
            course_id INT,
            date DATE,
            status VARCHAR(20),
            remarks VARCHAR(200)
        )
    """)
    
    # Library Table (Books)
    db_exec("""
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
    
    # Book Borrowings Table (Many-to-Many: Students ↔ Books)
    db_exec("""
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
    
    # Exams Table
    db_exec("""
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
    
    # Departments Table
    db_exec("""
        CREATE TABLE departments (
            id INT PRIMARY KEY,
            name VARCHAR(100),
            head_teacher_id INT,
            building VARCHAR(50),
            budget FLOAT
        )
    """)
    
    # System Logs Table (for live feed)
    db_exec("""
        CREATE TABLE system_logs (
            id INT PRIMARY KEY,
            timestamp VARCHAR(50),
            user_role VARCHAR(20),
            action VARCHAR(100),
            sql_command VARCHAR(500),
            status VARCHAR(20)
        )
    """)
    
    # Create indexes for performance
    db_exec("CREATE INDEX idx_users_role ON users (role)")
    db_exec("CREATE INDEX idx_auth_email ON auth_users (email)")
    db_exec("CREATE INDEX idx_auth_role ON auth_users (role)")
    db_exec("CREATE INDEX idx_enrollments_student ON enrollments (student_id)")
    db_exec("CREATE INDEX idx_enrollments_course ON enrollments (course_id)")
    db_exec("CREATE INDEX idx_attendance_student ON attendance (student_id)")
    db_exec("CREATE INDEX idx_financials_student ON financials (student_id)")
    db_exec("CREATE INDEX idx_borrowings_student ON borrowings (student_id)")
    
    print("✅ School ERP Database initialized (tables + indexes ready)")
    system_initialized = True
    ensure_demo_data()


def ensure_demo_data():
    """Ensure demo users and relationships exist for a feasibility"""
    print("🔧 Verifying Demo Data Integrity...")
    
    # 0. Ensure Admin and Registrar exist
    admin = DEMO_USERS['admin@school.edu']
    res = db_rows("SELECT id FROM users WHERE email = 'admin@school.edu'")
    if not res:
        print(f"Creating Demo Admin: {admin['name']}")
        try:
            db_exec(f"""
                INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
                VALUES ({admin['id']}, '{admin['name']}', 'admin@school.edu', 'Admin', 
                        '+254700000001', 'Admin Block', '1980-01-01', '{datetime.now().strftime('%Y-%m-%d')}')
            """)
        except Exception:
            pass

    auth = db_rows(f"SELECT id FROM auth_users WHERE email = 'admin@school.edu'")
    if not auth:
        try:
            db_exec(f"""
                INSERT INTO auth_users (id, user_id, name, email, password, role, created_at)
                VALUES ({admin['id']}, {admin['id']}, '{admin['name']}', 'admin@school.edu', '{admin['password']}', 'Admin', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
            """)
        except Exception:
            pass

    registrar = DEMO_USERS['registrar@school.edu']
    res = db_rows("SELECT id FROM users WHERE email = 'registrar@school.edu'")
    if not res:
        print(f"Creating Demo Registrar: {registrar['name']}")
        try:
            db_exec(f"""
                INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
                VALUES ({registrar['id']}, '{registrar['name']}', 'registrar@school.edu', 'Registrar', 
                        '+254700000004', 'Admin Block', '1982-01-01', '{datetime.now().strftime('%Y-%m-%d')}')
            """)
        except Exception:
            pass

    auth = db_rows(f"SELECT id FROM auth_users WHERE email = 'registrar@school.edu'")
    if not auth:
        try:
            db_exec(f"""
                INSERT INTO auth_users (id, user_id, name, email, password, role, created_at)
                VALUES ({registrar['id']}, {registrar['id']}, '{registrar['name']}', 'registrar@school.edu', '{registrar['password']}', 'Registrar', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
            """)
        except Exception:
            pass

    # 1. Ensure Demo Teacher exists
    teacher = DEMO_USERS['teacher@school.edu']
    res = db_rows("SELECT id FROM users WHERE email = 'teacher@school.edu'")
    if not res:
        print(f"Creating Demo Teacher: {teacher['name']}")
        try:
            db_exec(f"""
                INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
                VALUES ({teacher['id']}, '{teacher['name']}', 'teacher@school.edu', 'Teacher', 
                        '+254700000002', 'Staff Quarters School', '1985-05-15', '{datetime.now().strftime('%Y-%m-%d')}')
            """)
        except Exception:
            pass

    auth = db_rows(f"SELECT id FROM auth_users WHERE email = 'teacher@school.edu'")
    if not auth:
        try:
            db_exec(f"""
                INSERT INTO auth_users (id, user_id, name, email, password, role, created_at)
                VALUES ({teacher['id']}, {teacher['id']}, '{teacher['name']}', 'teacher@school.edu', '{teacher['password']}', 'Teacher', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
            """)
        except Exception:
            pass

    # 2. Ensure Demo Student exists
    student = DEMO_USERS['student@school.edu']
    res = db_rows("SELECT id FROM users WHERE email = 'student@school.edu'")
    if not res:
        print(f"Creating Demo Student: {student['name']}")
        try:
            db_exec(f"""
                INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
                VALUES ({student['id']}, '{student['name']}', 'student@school.edu', 'Student', 
                        '+254700000003', 'Dormitory A', '2005-08-20', '{datetime.now().strftime('%Y-%m-%d')}')
            """)
        except Exception:
            pass

    auth = db_rows(f"SELECT id FROM auth_users WHERE email = 'student@school.edu'")
    if not auth:
        try:
            db_exec(f"""
                INSERT INTO auth_users (id, user_id, name, email, password, role, created_at)
                VALUES ({student['id']}, {student['id']}, '{student['name']}', 'student@school.edu', '{student['password']}', 'Student', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
            """)
        except Exception:
            pass
        
    # 3. Assign 3 random courses to Demo Teacher (if they have none)
    my_courses = db_rows(f"SELECT id FROM courses WHERE teacher_id = {teacher['id']}")
    if not my_courses:
        print("Assigning courses to Demo Teacher...")
        # Get 3 course IDs
        courses = db_rows("SELECT id FROM courses LIMIT 3")
        for c in courses:
            db_exec(f"UPDATE courses SET teacher_id = {teacher['id']} WHERE id = {c['id']}")

    # 4. Enroll Demo Student in Demo Teacher's courses (if not enrolled)
    my_courses = db_rows(f"SELECT id FROM courses WHERE teacher_id = {teacher['id']}")
    for c in my_courses:
        enrollment = db_rows(f"SELECT id FROM enrollments WHERE student_id = {student['id']} AND course_id = {c['id']}")
        if not enrollment:
            print(f"Enrolling Demo Student in Course {c['id']}...")
            eid = random.randint(100000, 999999)
            db_exec(f"""
                INSERT INTO enrollments (id, student_id, course_id, grade, enrollment_date, status, midterm_score, final_score)
                VALUES ({eid}, {student['id']}, {c['id']}, 'B', '2024-01-15', 'Active', 75.5, 82.0)
            """)
    
    # 5. Ensure plenty of students in Demo Teacher's courses (for Gradebook demo)
    # Get all students
    all_students_res = db_rows("SELECT id FROM users WHERE role = 'Student' LIMIT 50")
    if all_students_res:
        all_students = [s['id'] for s in all_students_res]
        for c in my_courses:
            # Check enrollment count
            count_res = db_rows(f"SELECT COUNT(*) as cnt FROM enrollments WHERE course_id = {c['id']}")
            count = count_res[0]['cnt'] if count_res else 0
            if count < 5:
                # Add 10 random students
                print(f"Populating Course {c['id']} with random students...")
                target_students = random.sample(all_students, min(10, len(all_students)))
                for sid in target_students:
                    # Check if already enrolled
                    check = db_rows(f"SELECT id FROM enrollments WHERE student_id = {sid} AND course_id = {c['id']}")
                    if not check:
                        eid = random.randint(100000, 999999)
                        grade = random.choice(['A', 'B', 'C', 'D', 'F'])
                        mid = random.uniform(40, 99)
                        fin = random.uniform(40, 99)
                        db_exec(f"""
                            INSERT INTO enrollments (id, student_id, course_id, grade, enrollment_date, status, midterm_score, final_score)
                            VALUES ({eid}, {sid}, {c['id']}, '{grade}', '2024-01-15', 'Active', {mid:.1f}, {fin:.1f})
                        """)


def log_action(user_role, action, sql_command, status="SUCCESS"):
    """Log system actions for the live feed"""
    try:
        log_id = random.randint(100000, 999999)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Escape single quotes in SQL command
        sql_escaped = sql_command.replace("'", "''")
        
        engine.execute(f"""
            INSERT INTO system_logs (id, timestamp, user_role, action, sql_command, status)
            VALUES ({log_id}, '{timestamp}', '{user_role}', '{action}', '{sql_escaped[:500]}', '{status}')
        """)
    except Exception as e:
        print(f"⚠️ Logging failed: {e}")


# ============ ROUTES ============

@app.route('/')
def index():
    """School ERP Login Page"""
    if not system_initialized:
        init_school_database()
        
    # If already logged in, redirect to appropriate dashboard
    if 'user' in session:
        role = session['user']['role']
        if role == 'Admin': return redirect('/admin')
        if role == 'Teacher': return redirect('/teacher')
        if role == 'Student': return redirect('/student')
        if role == 'Registrar': return redirect('/registrar')
        
    return render_template('school/login.html')


@app.route('/login', methods=['POST'])
def login():
    """Handle login authentication"""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # 1) DB-backed auth (MariaDB-like: credentials live in auth_users table)
    try:
        sql = f"SELECT user_id, name, email, role FROM auth_users WHERE email = '{email}' AND password = '{password}'"
        rows = db_rows(sql)
        if rows:
            row = rows[0]
            user_obj = {
                'id': row['user_id'],
                'name': row['name'],
                'email': row['email'],
                'role': row['role']
            }
            session['user'] = user_obj
            log_action(row['role'], "Login", f"User {email} logged in via DB")
            return jsonify({"success": True, "role": row['role']})
    except Exception as e:
        print(f"Login DB error: {e}")

    # 2) Fallback demo users (only if DB isn't ready)
    if email in DEMO_USERS and DEMO_USERS[email]['password'] == password:
        demo = DEMO_USERS[email].copy()
        demo['email'] = email
        session['user'] = demo
        log_action(DEMO_USERS[email]['role'], "Login", f"User {email} logged in (Demo Fallback)")
        return jsonify({"success": True, "role": DEMO_USERS[email]['role']})
    
    return jsonify({"success": False, "error": "Invalid email or password"}), 401


@app.route('/logout')
def logout():
    """Clear session and redirect to login"""
    session.pop('user', None)
    return redirect('/')


@app.route('/admin')
def admin_dashboard():
    """Admin Dashboard - Full CRUD access"""
    if not system_initialized: init_school_database()
    if 'user' not in session or session['user']['role'] != 'Admin':
        return redirect('/')
    return render_template('school/admin.html', user=session['user'])


@app.route('/teacher')
def teacher_dashboard():
    """Teacher Dashboard - Grade management"""
    if not system_initialized: init_school_database()
    if 'user' not in session or session['user']['role'] != 'Teacher':
        return redirect('/')
    return render_template('school/teacher.html', user=session['user'])


@app.route('/student')
def student_dashboard():
    """Student Dashboard - View only"""
    if not system_initialized: init_school_database()
    if 'user' not in session or session['user']['role'] != 'Student':
        return redirect('/')
    return render_template('school/student.html', user=session['user'])


@app.route('/registrar')
def registrar_dashboard():
    """Registrar Dashboard - Advanced Analytics"""
    if not system_initialized: init_school_database()
    if 'user' not in session or session['user']['role'] != 'Registrar':
        return redirect('/')
    return render_template('school/registrar.html', user=session['user'])


# ============ API ENDPOINTS ============

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users or filter by role"""
    role = request.args.get('role', '')
    
    if role:
        sql = f"SELECT * FROM users WHERE role = '{role}'"
    else:
        sql = "SELECT * FROM users"

    rows = db_rows(sql)
    log_action("API", "Fetch Users", sql)
    return jsonify(rows)


@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user (Admin/Teacher/Student)"""
    data = request.json
    user_id = random.randint(1000, 99999)
    
    sql = f"""
        INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
        VALUES ({user_id}, '{data['name']}', '{data['email']}', '{data['role']}', 
                '{data.get('phone', '')}', '{data.get('address', '')}', 
                '{data.get('date_of_birth', '2000-01-01')}', '{datetime.now().strftime('%Y-%m-%d')}')
    """
    
    try:
        db_exec(sql)
        log_action(data['role'], "Create User", sql)
        return jsonify({"success": True, "id": user_id, "message": "User created successfully"})
    except Exception as e:
        log_action(data['role'], "Create User", sql, "ERROR")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user information"""
    data = request.json
    
    sql = f"""
        UPDATE users 
        SET name = '{data['name']}', email = '{data['email']}', 
            phone = '{data.get('phone', '')}', address = '{data.get('address', '')}'
        WHERE id = {user_id}
    """
    
    try:
        db_exec(sql)
        log_action("Admin", "Update User", sql)
        return jsonify({"success": True, "message": "User updated successfully"})
    except Exception as e:
        log_action("Admin", "Update User", sql, "ERROR")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user"""
    sql = f"DELETE FROM users WHERE id = {user_id}"
    
    try:
        db_exec(sql)
        log_action("Admin", "Delete User", sql)
        return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        log_action("Admin", "Delete User", sql, "ERROR")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    sql = "SELECT * FROM courses"
    rows = db_rows(sql)
    log_action("API", "Fetch Courses", sql)
    return jsonify(rows)


@app.route('/api/courses', methods=['POST'])
def create_course():
    """Create new course"""
    data = request.json
    course_id = random.randint(100, 9999)
    
    sql = f"""
        INSERT INTO courses (id, title, code, description, teacher_id, credits, semester, capacity, room)
        VALUES ({course_id}, '{data['title']}', '{data['code']}', '{data.get('description', '')}',
                {data['teacher_id']}, {data['credits']}, '{data['semester']}', 
                {data.get('capacity', 30)}, '{data.get('room', 'TBA')}')
    """
    
    try:
        db_exec(sql)
        log_action("Admin", "Create Course", sql)
        return jsonify({"success": True, "id": course_id, "message": "Course created successfully"})
    except Exception as e:
        log_action("Admin", "Create Course", sql, "ERROR")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/enrollments', methods=['GET'])
def get_enrollments():
    """Get enrollments with JOINs"""
    student_id = request.args.get('student_id', '')
    course_id = request.args.get('course_id', '')
    
    if student_id:
        sql = f"""
            SELECT e.id, u.name as student_name, c.title as course_title, 
                   e.grade, e.midterm_score, e.final_score, e.status
            FROM enrollments e
            INNER JOIN users u ON e.student_id = u.id
            INNER JOIN courses c ON e.course_id = c.id
            WHERE e.student_id = {student_id}
        """
    elif course_id:
        sql = f"""
            SELECT e.id, u.name as student_name, u.email, 
                   e.grade, e.midterm_score, e.final_score, e.status
            FROM enrollments e
            INNER JOIN users u ON e.student_id = u.id
            WHERE e.course_id = {course_id}
        """
    else:
        sql = """
            SELECT e.id, u.name as student_name, c.title as course_title, 
                   e.grade, e.status
            FROM enrollments e
            INNER JOIN users u ON e.student_id = u.id
            INNER JOIN courses c ON e.course_id = c.id
            LIMIT 100
        """
    
    rows = db_rows(sql)
    log_action("API", "Fetch Enrollments", sql)
    return jsonify(rows)


@app.route('/api/enrollments', methods=['POST'])
def create_enrollment():
    """Enroll student in course"""
    data = request.json
    enrollment_id = random.randint(10000, 99999)
    
    sql = f"""
        INSERT INTO enrollments (id, student_id, course_id, grade, enrollment_date, status, midterm_score, final_score)
        VALUES ({enrollment_id}, {data['student_id']}, {data['course_id']}, 
                'N/A', '{datetime.now().strftime('%Y-%m-%d')}', 'Active', 0.0, 0.0)
    """
    
    try:
        db_exec(sql)
        log_action("Admin", "Create Enrollment", sql)
        return jsonify({"success": True, "id": enrollment_id, "message": "Enrollment created successfully"})
    except Exception as e:
        log_action("Admin", "Create Enrollment", sql, "ERROR")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/enrollments/<int:enrollment_id>/grade', methods=['PUT'])
def update_grade(enrollment_id):
    """Update student grade (Teacher action)"""
    data = request.json
    
    sql = f"""
        UPDATE enrollments 
        SET grade = '{data['grade']}', 
            midterm_score = {data.get('midterm_score', 0.0)},
            final_score = {data.get('final_score', 0.0)}
        WHERE id = {enrollment_id}
    """
    
    try:
        db_exec(sql)
        log_action("Teacher", "Update Grade", sql)
        return jsonify({"success": True, "message": "Grade updated successfully"})
    except Exception as e:
        log_action("Teacher", "Update Grade", sql, "ERROR")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/analytics/top-performers', methods=['GET'])
def get_top_performers():
    """Get top 10 students by average grade"""
    sql = """
        SELECT u.name, u.email, AVG(e.final_score) as avg_score, COUNT(e.id) as courses_taken
        FROM users u
        INNER JOIN enrollments e ON u.id = e.student_id
        WHERE u.role = 'Student'
        GROUP BY u.id, u.name, u.email
        ORDER BY avg_score DESC
        LIMIT 10
    """
    
    rows = db_rows(sql)
    log_action("Registrar", "Analytics - Top Performers", sql)
    return jsonify(rows)


@app.route('/api/analytics/financial-summary', methods=['GET'])
def get_financial_summary():
    """Get financial summary with aggregates"""
    sql = """
        SELECT 
            SUM(total_fees) as total_billed,
            SUM(fees_paid) as total_collected,
            SUM(balance) as total_pending,
            AVG(fees_paid) as avg_payment,
            COUNT(*) as total_students
        FROM financials
    """
    
    rows = db_rows(sql)
    log_action("Registrar", "Analytics - Financial Summary", sql)
    return jsonify(rows)


@app.route('/api/analytics/attendance-rate', methods=['GET'])
def get_attendance_rate():
    """Calculate attendance rate"""
    sql = """
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
            (SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as attendance_rate
        FROM attendance
    """
    
    rows = db_rows(sql)
    log_action("Registrar", "Analytics - Attendance Rate", sql)
    return jsonify(rows)


@app.route('/api/analytics/course-enrollment', methods=['GET'])
def get_course_enrollment():
    """Get enrollment stats per course"""
    sql = """
        SELECT c.title, c.code, c.capacity, 
               COUNT(e.id) as enrolled_students,
               (COUNT(e.id) * 100.0 / c.capacity) as occupancy_rate
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        GROUP BY c.id, c.title, c.code, c.capacity
        ORDER BY enrolled_students DESC
    """
    
    rows = db_rows(sql)
    log_action("Registrar", "Analytics - Course Enrollment", sql)
    return jsonify(rows)


@app.route('/api/financials', methods=['GET'])
def get_financials():
    """Get financial records"""
    student_id = request.args.get('student_id', '')
    
    if student_id:
        sql = f"""
            SELECT f.*, u.name as student_name
            FROM financials f
            INNER JOIN users u ON f.student_id = u.id
            WHERE f.student_id = {student_id}
        """
    else:
        sql = """
            SELECT f.*, u.name as student_name
            FROM financials f
            INNER JOIN users u ON f.student_id = u.id
        """
    
    rows = db_rows(sql)
    log_action("API", "Fetch Financials", sql)
    return jsonify(rows)


@app.route('/api/financials', methods=['POST'])
def create_invoice():
    """Create new financial record"""
    data = request.json
    try:
        inv_id = random.randint(1000, 99999)
        sql = f"""
            INSERT INTO financials (id, student_id, semester, total_fees, fees_paid, balance, payment_date, payment_status)
            VALUES ({inv_id}, {data['student_id']}, '{data['semester']}', {data['total_fees']}, 0, {data['total_fees']}, '{datetime.now().strftime('%Y-%m-%d')}', 'Unpaid')
        """
        db_exec(sql)
        log_action("Financials", f"Created Invoice #{inv_id}", sql)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/financials/<int:id>/pay', methods=['PUT'])
def pay_fees(id):
    """Record fee payment"""
    data = request.json
    amount = float(data.get('amount', 0))
    try:
        # Get current state
        rows = db_rows(f"SELECT * FROM financials WHERE id = {id}")
        if not rows:
            return jsonify({"success": False, "error": "Record not found"}), 404
        
        record = rows[0]
        new_paid = record['fees_paid'] + amount
        new_balance = record['total_fees'] - new_paid
        status = 'Paid' if new_balance <= 0 else 'Partial'
        
        sql = f"""
            UPDATE financials 
            SET fees_paid = {new_paid}, balance = {new_balance}, payment_status = '{status}', payment_date = '{datetime.now().strftime('%Y-%m-%d')}'
            WHERE id = {id}
        """
        db_exec(sql)
        log_action("Financials", f"Payment Rec: {id}Amt: {amount}", sql)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    """Get attendance records"""
    student_id = request.args.get('student_id', '')
    course_id = request.args.get('course_id', '')
    
    if student_id:
        sql = f"""
            SELECT a.*, u.name as student_name, c.title as course_title
            FROM attendance a
            INNER JOIN users u ON a.student_id = u.id
            INNER JOIN courses c ON a.course_id = c.id
            WHERE a.student_id = {student_id}
            ORDER BY a.date DESC
        """
    elif course_id:
        sql = f"""
            SELECT a.*, u.name as student_name
            FROM attendance a
            INNER JOIN users u ON a.student_id = u.id
            INNER JOIN courses c ON a.course_id = c.id
            WHERE a.course_id = {course_id}
            ORDER BY a.date DESC
        """
    else:
        sql = """
            SELECT a.*, u.name as student_name, c.title as course_title
            FROM attendance a
            INNER JOIN users u ON a.student_id = u.id
            INNER JOIN courses c ON a.course_id = c.id
            ORDER BY a.date DESC
        """
    
    rows = db_rows(sql)
    log_action("API", "Fetch Attendance", sql)
    return jsonify(rows)


@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    """Mark attendance"""
    data = request.json
    try:
        att_id = random.randint(10000, 99999)
        sql = f"""
            INSERT INTO attendance (id, student_id, course_id, date, status, remarks)
            VALUES ({att_id}, {data['student_id']}, {data['course_id']}, '{data['date']}', '{data['status']}', '{data.get('remarks', '')}')
        """
        db_exec(sql)
        log_action("Attendance", "Mark Attendance", sql)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/library/books', methods=['GET'])
def get_books():
    """Get library books"""
    sql = "SELECT * FROM books"
    rows = db_rows(sql)
    log_action("API", "Fetch Books", sql)
    return jsonify(rows)


@app.route('/api/library/books', methods=['POST'])
def add_book():
    """Add new book"""
    data = request.json
    try:
        book_id = random.randint(1000, 99999)
        sql = f"""
            INSERT INTO books (id, title, author, isbn, category, total_copies, available_copies, shelf_location)
            VALUES ({book_id}, '{data['title']}', '{data['author']}', '{data['isbn']}', '{data['category']}', {data['copies']}, {data['copies']}, '{data['shelf']}')
        """
        db_exec(sql)
        log_action("Library", f"Add Book: {data['title']}", sql)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/library/borrowings', methods=['GET'])
def get_borrowings():
    """Get borrowing records with JOINs"""
    student_id = request.args.get('student_id', '')
    
    if student_id:
        sql = f"""
            SELECT b.*, bk.title as book_title, bk.author, u.name as student_name
            FROM borrowings b
            INNER JOIN books bk ON b.book_id = bk.id
            INNER JOIN users u ON b.student_id = u.id
            WHERE b.student_id = {student_id}
            ORDER BY b.borrow_date DESC
        """
    else:
        sql = """
            SELECT b.*, bk.title as book_title, u.name as student_name
            FROM borrowings b
            INNER JOIN books bk ON b.book_id = bk.id
            INNER JOIN users u ON b.student_id = u.id
            ORDER BY b.borrow_date DESC
        """
    
    rows = db_rows(sql)
    log_action("API", "Fetch Borrowings", sql)
    return jsonify(rows)


@app.route('/api/library/borrowings', methods=['POST'])
def issue_book():
    """Issue book to student"""
    data = request.json
    try:
        # Check availability
        books = db_rows(f"SELECT available_copies FROM books WHERE id = {data['book_id']}")
        if not books or books[0]['available_copies'] < 1:
            return jsonify({"success": False, "error": "Book not available"}), 400

        bor_id = random.randint(1000, 99999)
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        # Create borrowing
        sql = f"""
            INSERT INTO borrowings (id, student_id, book_id, borrow_date, due_date, status, fine)
            VALUES ({bor_id}, {data['student_id']}, {data['book_id']}, '{datetime.now().strftime('%Y-%m-%d')}', '{due_date}', 'Borrowed', 0)
        """
        db_exec(sql)
        
        # Decrement stock
        db_exec(f"UPDATE books SET available_copies = available_copies - 1 WHERE id = {data['book_id']}")
        
        log_action("Library", f"Issue Book: {data['book_id']} to {data['student_id']}", sql)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/library/borrowings/<int:id>/return', methods=['PUT'])
def return_book(id):
    """Return book"""
    data = request.json
    try:
        # Get borrowing
        rows = db_rows(f"SELECT book_id FROM borrowings WHERE id = {id}")
        if not rows:
            return jsonify({"success": False, "error": "Record not found"}), 404
            
        book_id = rows[0]['book_id']
        
        sql = f"""
            UPDATE borrowings 
            SET status = 'Returned', return_date = '{datetime.now().strftime('%Y-%m-%d')}'
            WHERE id = {id}
        """
        db_exec(sql)
        
        # Increment stock
        db_exec(f"UPDATE books SET available_copies = available_copies + 1 WHERE id = {book_id}")
        
        log_action("Library", f"Return Book: {id}", sql)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/system-logs', methods=['GET'])
def get_system_logs():
    """Get recent system logs for live feed"""
    sql = """
        SELECT * FROM system_logs 
        ORDER BY timestamp DESC 
        LIMIT 20
    """
    rows = db_rows(sql)
    return jsonify(rows)


@app.route('/api/execute', methods=['POST'])
def execute_sql():
    """Execute custom SQL query"""
    data = request.json
    sql = data.get('sql', '').strip()
    
    if not sql:
        return jsonify({"success": False, "error": "No SQL provided"}), 400
    
    try:
        result = engine.execute(sql)
        log_action("Custom", "Execute SQL", sql)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        log_action("Custom", "Execute SQL", sql, "ERROR")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/explain', methods=['POST'])
def explain_query():
    """Get query execution plan"""
    data = request.json
    sql = data.get('sql', '').strip()
    
    if not sql:
        return jsonify({"success": False, "error": "No SQL provided"}), 400
    
    try:
        result = engine.explain(sql)
        log_action("Custom", "Explain Query", sql)
        return jsonify({"success": True, "plan": result})
    except Exception as e:
        log_action("Custom", "Explain Query", sql, "ERROR")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/bulk-import/students', methods=['POST'])
def bulk_import_students():
    """Bulk import students from CSV data"""
    data = request.json
    students = data.get('students', [])
    
    if not students:
        return jsonify({"success": False, "error": "No student data provided"}), 400
    
    success_count = 0
    errors = []
    
    for student in students:
        try:
            user_id = random.randint(1000, 99999)
            sql = f"""
                INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
                VALUES ({user_id}, '{student['name']}', '{student['email']}', 'Student',
                        '{student.get('phone', '')}', '{student.get('address', '')}',
                        '{student.get('date_of_birth', '2005-01-01')}', '{datetime.now().strftime('%Y-%m-%d')}')
            """
            db_exec(sql)
            success_count += 1
        except Exception as e:
            errors.append({"student": student['name'], "error": str(e)})
    
    log_action("Admin", f"Bulk Import ({success_count} students)", "BULK INSERT INTO users")
    
    return jsonify({
        "success": True,
        "imported": success_count,
        "total": len(students),
        "errors": errors
    })


@app.route('/api/schema', methods=['GET'])
def get_schema():
    """Get database schema information"""
    rows = db_rows("SELECT * FROM .sys_tables")
    return jsonify(rows)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏫 SimpleSQLDB - School Management ERP System")
    print("="*60)
    print("\n📊 System Features:")
    print("  ✓ Multi-user roles (Admin, Teacher, Student)")
    print("  ✓ 10 interconnected tables")
    print("  ✓ Advanced analytics with GROUP BY & aggregates")
    print("  ✓ Foreign key relationships")
    print("  ✓ Bulk import capabilities")
    print("  ✓ Real-time system logs")
    print("\n🚀 Starting server on http://localhost:5001")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5001)
