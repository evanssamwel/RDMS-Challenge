"""
SimpleSQLDB - School Management ERP System
A feature-rich school management system demonstrating complex RDBMS operations
Showcases multi-table relationships, foreign keys, aggregates, and real-world business logic
"""

from flask import Flask, render_template, request, jsonify, session
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import QueryEngine
from core.storage import Storage

app = Flask(__name__)
app.secret_key = 'school-erp-simplesqldb-2026'

# Initialize database
storage = Storage(data_dir='school_data')
engine = QueryEngine(storage)

# Track initialization status
system_initialized = False


def init_school_database():
    """Initialize comprehensive school management database schema"""
    global system_initialized
    
    if system_initialized:
        return
    
    print("🏫 Initializing School Management ERP Database...")
    
    # Users Table (Students, Teachers, Admins)
    engine.execute("""
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
    
    # Courses Table
    engine.execute("""
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
    engine.execute("""
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
    engine.execute("""
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
    engine.execute("""
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
    engine.execute("""
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
    engine.execute("""
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
    engine.execute("""
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
    engine.execute("""
        CREATE TABLE departments (
            id INT PRIMARY KEY,
            name VARCHAR(100),
            head_teacher_id INT,
            building VARCHAR(50),
            budget FLOAT
        )
    """)
    
    # System Logs Table (for live feed)
    engine.execute("""
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
    engine.execute("CREATE INDEX idx_users_role ON users (role)")
    engine.execute("CREATE INDEX idx_enrollments_student ON enrollments (student_id)")
    engine.execute("CREATE INDEX idx_enrollments_course ON enrollments (course_id)")
    engine.execute("CREATE INDEX idx_attendance_student ON attendance (student_id)")
    engine.execute("CREATE INDEX idx_financials_student ON financials (student_id)")
    engine.execute("CREATE INDEX idx_borrowings_student ON borrowings (student_id)")
    
    print("✅ School ERP Database initialized with 10 tables and 6 indexes")
    system_initialized = True


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
    """School ERP Homepage with role switcher"""
    if not system_initialized:
        init_school_database()
    return render_template('school/index.html')


@app.route('/admin')
def admin_dashboard():
    """Admin Dashboard - Full CRUD access"""
    if not system_initialized:
        init_school_database()
    return render_template('school/admin.html')


@app.route('/teacher')
def teacher_dashboard():
    """Teacher Dashboard - Grade management"""
    if not system_initialized:
        init_school_database()
    return render_template('school/teacher.html')


@app.route('/student')
def student_dashboard():
    """Student Dashboard - View only"""
    if not system_initialized:
        init_school_database()
    return render_template('school/student.html')


@app.route('/registrar')
def registrar_dashboard():
    """Registrar Dashboard - Advanced Analytics"""
    if not system_initialized:
        init_school_database()
    return render_template('school/registrar.html')


# ============ API ENDPOINTS ============

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users or filter by role"""
    role = request.args.get('role', '')
    
    if role:
        result = engine.execute(f"SELECT * FROM users WHERE role = '{role}'")
    else:
        result = engine.execute("SELECT * FROM users")
    
    log_action("API", "Fetch Users", f"SELECT * FROM users WHERE role = '{role}'")
    return jsonify(result)


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
        engine.execute(sql)
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
        engine.execute(sql)
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
        engine.execute(sql)
        log_action("Admin", "Delete User", sql)
        return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        log_action("Admin", "Delete User", sql, "ERROR")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    result = engine.execute("SELECT * FROM courses")
    log_action("API", "Fetch Courses", "SELECT * FROM courses")
    return jsonify(result)


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
        engine.execute(sql)
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
    
    result = engine.execute(sql)
    log_action("API", "Fetch Enrollments", sql)
    return jsonify(result)


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
        engine.execute(sql)
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
        engine.execute(sql)
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
    
    result = engine.execute(sql)
    log_action("Registrar", "Analytics - Top Performers", sql)
    return jsonify(result)


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
    
    result = engine.execute(sql)
    log_action("Registrar", "Analytics - Financial Summary", sql)
    return jsonify(result)


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
    
    result = engine.execute(sql)
    log_action("Registrar", "Analytics - Attendance Rate", sql)
    return jsonify(result)


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
    
    result = engine.execute(sql)
    log_action("Registrar", "Analytics - Course Enrollment", sql)
    return jsonify(result)


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
            LIMIT 100
        """
    
    result = engine.execute(sql)
    log_action("API", "Fetch Financials", sql)
    return jsonify(result)


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
            LIMIT 50
        """
    elif course_id:
        sql = f"""
            SELECT a.*, u.name as student_name
            FROM attendance a
            INNER JOIN users u ON a.student_id = u.id
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
            LIMIT 100
        """
    
    result = engine.execute(sql)
    log_action("API", "Fetch Attendance", sql)
    return jsonify(result)


@app.route('/api/library/books', methods=['GET'])
def get_books():
    """Get library books"""
    result = engine.execute("SELECT * FROM books")
    log_action("API", "Fetch Books", "SELECT * FROM books")
    return jsonify(result)


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
            LIMIT 100
        """
    
    result = engine.execute(sql)
    log_action("API", "Fetch Borrowings", sql)
    return jsonify(result)


@app.route('/api/system-logs', methods=['GET'])
def get_system_logs():
    """Get recent system logs for live feed"""
    result = engine.execute("""
        SELECT * FROM system_logs 
        ORDER BY timestamp DESC 
        LIMIT 20
    """)
    return jsonify(result)


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
            engine.execute(sql)
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
    result = engine.execute("SELECT * FROM .sys_tables")
    return jsonify(result)


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
