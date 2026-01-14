"""
SimpleSQLDB - Unified Database Management Studio
Professional dashboard showcasing CRUD operations, analytics, and SQL execution
Demonstrates both educational datasets and Kenyan HR analytics
"""

from flask import Flask, render_template, request, jsonify
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import QueryEngine
from core.storage import Storage
from core.database_manager import DatabaseManager

app = Flask(__name__)
app.secret_key = 'simplesqldb-studio-2026'

# Multi-database setup (MariaDB/MySQL-style)
db_manager = DatabaseManager(base_dir='databases')

# Backward-compatible registrations
if os.path.isdir('studio_data'):
    db_manager.register_database('studio', 'studio_data')
db_manager.register_database('school_erp', os.path.join('databases', 'school_erp'))

# Ensure the Studio database exists, then select it
db_manager.create_database('studio')
storage = db_manager.open_storage('studio')
engine = QueryEngine(storage, database_manager=db_manager, default_database='studio')

# Track engine status
engine_status = {
    'online': True,
    'persistence': 'Atomic JSON (os.replace)',
    'storage_mode': 'B-Tree Indexed',
    'initialized': False
}


@app.route('/api/databases', methods=['GET'])
def list_databases():
    """List available databases (MariaDB/MySQL-style)."""
    infos = db_manager.list_databases()
    return jsonify({
        'success': True,
        'current': engine.current_database,
        'databases': [
            {
                'name': info.name,
                'path': info.path,
                'exists': info.exists,
                'current': (info.name == engine.current_database)
            }
            for info in infos
        ]
    })


@app.route('/api/databases', methods=['POST'])
def create_database():
    """Create a new database folder under the base databases directory."""
    payload = request.json or {}
    name = (payload.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Database name is required'}), 400
    try:
        db_manager.create_database(name)
        return jsonify({'success': True, 'message': f"Database '{name}' created"})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/databases/use', methods=['POST'])
def use_database():
    """Switch the active database for the Studio engine."""
    payload = request.json or {}
    name = (payload.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Database name is required'}), 400
    result = engine.use_database(name)
    status = 200 if result.get('success') else 400
    return jsonify(result), status


def _sql_text(value) -> str:
    """Sanitize text for the project's simple SQL parser.

    - Escapes single quotes.
    - Removes commas (the parser is not robust with commas inside quoted strings).
    - Normalizes whitespace.
    """
    if value is None:
        return ''
    text = str(value)
    text = text.replace("'", "''")
    text = text.replace(",", " ")
    text = text.replace("\r", " ").replace("\n", " ")
    return " ".join(text.split())


def _next_int_id(table_name: str, id_column: str) -> int:
    """Compute the next integer id for a table using in-memory storage."""
    if table_name not in engine.storage.data:
        return 1
    values = []
    for row in engine.storage.data.get(table_name, []):
        value = row.get(id_column)
        if isinstance(value, int):
            values.append(value)
        else:
            try:
                values.append(int(value))
            except Exception:
                continue
    return (max(values) + 1) if values else 1


def init_databases():
    """Initialize both educational and analytics datasets"""
    tables = engine.storage.list_tables()
    
    if 'students' not in tables:
        print("📚 Initializing Educational Database...")
        
        # Create students table
        engine.execute("""
            CREATE TABLE students (
                student_id INT PRIMARY KEY,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
                enrollment_date DATE
            )
        """)
        
        # Create courses table
        engine.execute("""
            CREATE TABLE courses (
                course_id INT PRIMARY KEY,
                course_name VARCHAR(100),
                course_code VARCHAR(20) UNIQUE,
                credits INT,
                instructor VARCHAR(100)
            )
        """)
        
        # Create enrollments table (JUNCTION TABLE for M:M relationship)
        engine.execute("""
            CREATE TABLE enrollments (
                enrollment_id INT PRIMARY KEY,
                student_id INT,
                course_id INT,
                grade VARCHAR(2),
                enrollment_date DATE,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            )
        """)
        
        # Insert sample data
        engine.execute("INSERT INTO students (student_id, first_name, last_name, email, phone, enrollment_date) VALUES (1, 'John', 'Doe', 'john.doe@university.edu', '+254712345678', '2023-01-15')")
        engine.execute("INSERT INTO students (student_id, first_name, last_name, email, phone, enrollment_date) VALUES (2, 'Jane', 'Smith', 'jane.smith@university.edu', '+254723456789', '2023-02-20')")
        engine.execute("INSERT INTO students (student_id, first_name, last_name, email, phone, enrollment_date) VALUES (3, 'James', 'Wilson', 'james.wilson@university.edu', '+254734567890', '2023-03-10')")
        
        engine.execute("INSERT INTO courses (course_id, course_name, course_code, credits, instructor) VALUES (1, 'Database Systems', 'CS301', 3, 'Dr. Samuel')")
        engine.execute("INSERT INTO courses (course_id, course_name, course_code, credits, instructor) VALUES (2, 'Web Development', 'CS201', 3, 'Dr. Kipchoge')")
        engine.execute("INSERT INTO courses (course_id, course_name, course_code, credits, instructor) VALUES (3, 'Data Structures', 'CS102', 4, 'Prof. Kariuki')")
        
        engine.execute("INSERT INTO enrollments (enrollment_id, student_id, course_id, grade, enrollment_date) VALUES (1, 1, 1, 'A', '2023-01-15')")
        engine.execute("INSERT INTO enrollments (enrollment_id, student_id, course_id, grade, enrollment_date) VALUES (2, 1, 2, 'B', '2023-01-15')")
        engine.execute("INSERT INTO enrollments (enrollment_id, student_id, course_id, grade, enrollment_date) VALUES (3, 2, 1, 'A', '2023-02-20')")
        engine.execute("INSERT INTO enrollments (enrollment_id, student_id, course_id, grade, enrollment_date) VALUES (4, 3, 3, 'B', '2023-03-10')")
        
        # Create indexes
        engine.execute("CREATE INDEX idx_student_email ON students(email)")
        engine.execute("CREATE INDEX idx_course_code ON courses(course_code)")
        engine.execute("CREATE INDEX idx_enrollment_student ON enrollments(student_id)")
        
        print("✅ Educational database initialized!")
    
    if 'employees' not in tables:
        print("💼 Initializing Analytics Database...")
        
        # Create departments
        engine.execute("""
            CREATE TABLE departments (
                dept_id INT PRIMARY KEY,
                dept_name VARCHAR(100) UNIQUE,
                location VARCHAR(100),
                budget INT
            )
        """)
        
        # Create employees with FK
        engine.execute("""
            CREATE TABLE employees (
                emp_id INT PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100) UNIQUE,
                position VARCHAR(100),
                salary INT,
                dept_id INT,
                FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
            )
        """)
        
        # Sample departments
        for i, (name, location) in enumerate([
            ('Engineering', 'Nairobi'),
            ('Sales', 'Mombasa'),
            ('Finance', 'Nairobi'),
            ('Operations', 'Kisumu')
        ], 1):
            engine.execute(f"INSERT INTO departments (dept_id, dept_name, location, budget) VALUES ({i}, '{name}', '{location}', {500000 + i*100000})")
        
        # Sample employees
        employees = [
            (1, 'Alice Kipchoge', 'alice@company.ke', 'Senior Engineer', 150000, 1),
            (2, 'Bob Omondi', 'bob@company.ke', 'Sales Manager', 120000, 2),
            (3, 'Carol Wanjiru', 'carol@company.ke', 'Finance Manager', 130000, 3),
            (4, 'David Kimani', 'david@company.ke', 'Software Engineer', 95000, 1),
            (5, 'Eve Kiplagat', 'eve@company.ke', 'Junior Engineer', 65000, 1),
            (6, 'Frank Otieno', 'frank@company.ke', 'Sales Executive', 85000, 2),
        ]
        
        for emp_id, name, email, position, salary, dept_id in employees:
            engine.execute(f"INSERT INTO employees (emp_id, name, email, position, salary, dept_id) VALUES ({emp_id}, '{name}', '{email}', '{position}', {salary}, {dept_id})")
        
        print("✅ Analytics database initialized!")
    
    engine_status['initialized'] = True


@app.route('/')
def index():
    """Render the gateway homepage with entry points"""
    return render_template('index.html')


@app.route('/school')
def school_home():
    """Redirect to School ERP homepage"""
    return "<html><body><h1>School ERP System</h1><p>Please run the School ERP on port 5001:</p><code>python web_demo/app_school.py</code><p>Or visit <a href='http://localhost:5001'>http://localhost:5001</a></p><p><a href='/'>← Back to Gateway</a></p></body></html>"


@app.route('/studio')
def studio():
    """Render the main studio dashboard"""
    if not engine_status['initialized']:
        init_databases()
    return render_template('studio.html')


# ============ CRUD ENDPOINTS ============

@app.route('/api/students', methods=['GET'])
def get_students():
    """Fetch all students"""
    try:
        result = engine.execute("SELECT * FROM students")
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Query failed')}), 400
        return jsonify({'success': True, 'data': result.get('rows', []), 'count': result.get('count', 0)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/students', methods=['POST'])
def create_student():
    """Create a new student"""
    try:
        data = request.json or {}
        student_id = data.get('student_id')
        if student_id in (None, ''):
            student_id = _next_int_id('students', 'student_id')
        else:
            student_id = int(student_id)

        first_name = _sql_text(data.get('first_name', ''))
        last_name = _sql_text(data.get('last_name', ''))
        email = _sql_text(data.get('email', ''))
        phone = _sql_text(data.get('phone', ''))
        enrollment_date = _sql_text(data.get('enrollment_date', datetime.now().date().isoformat()))

        query = f"""
            INSERT INTO students 
            (student_id, first_name, last_name, email, phone, enrollment_date) 
            VALUES ({student_id}, '{first_name}', '{last_name}', '{email}', '{phone}', '{enrollment_date}')
        """
        result = engine.execute(query)
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Insert failed')}), 400
        return jsonify({'success': True, 'message': 'Student created', 'student_id': student_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Update a student"""
    try:
        data = request.json or {}
        first_name = _sql_text(data.get('first_name', ''))
        last_name = _sql_text(data.get('last_name', ''))
        email = _sql_text(data.get('email', ''))
        phone = _sql_text(data.get('phone', ''))
        query = f"""
            UPDATE students 
            SET first_name = '{data['first_name']}', 
                last_name = '{data['last_name']}', 
                email = '{data['email']}', 
                phone = '{data['phone']}'
            WHERE student_id = {student_id}
        """
        query = f"""
            UPDATE students 
            SET first_name = '{first_name}', 
                last_name = '{last_name}', 
                email = '{email}', 
                phone = '{phone}'
            WHERE student_id = {student_id}
        """
        result = engine.execute(query)
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Update failed')}), 400
        return jsonify({'success': True, 'message': 'Student updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
    try:
        result = engine.execute(f"DELETE FROM students WHERE student_id = {student_id}")
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Delete failed')}), 400
        return jsonify({'success': True, 'message': 'Student deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Fetch all courses"""
    try:
        result = engine.execute("SELECT * FROM courses")
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Query failed')}), 400
        return jsonify({'success': True, 'data': result.get('rows', []), 'count': result.get('count', 0)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/courses', methods=['POST'])
def create_course():
    """Create a new course"""
    try:
        data = request.json or {}
        course_id = data.get('course_id')
        if course_id in (None, ''):
            course_id = _next_int_id('courses', 'course_id')
        else:
            course_id = int(course_id)

        course_name = _sql_text(data.get('course_name', ''))
        course_code = _sql_text(data.get('course_code', ''))
        instructor = _sql_text(data.get('instructor', ''))
        credits = int(data.get('credits', 0) or 0)
        query = f"""
            INSERT INTO courses 
            (course_id, course_name, course_code, credits, instructor) 
            VALUES ({course_id}, '{course_name}', '{course_code}', {credits}, '{instructor}')
        """
        result = engine.execute(query)
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Insert failed')}), 400
        return jsonify({'success': True, 'message': 'Course created', 'course_id': course_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enrollments', methods=['GET'])
def get_enrollments():
    """Fetch all enrollments with student and course info"""
    try:
        # Avoid SQL JOIN aliases: the parser doesn't support "FROM enrollments e".
        enr = engine.execute("SELECT * FROM enrollments")
        stu = engine.execute("SELECT * FROM students")
        cou = engine.execute("SELECT * FROM courses")

        for r in (enr, stu, cou):
            if not r.get('success'):
                return jsonify({'success': False, 'error': r.get('error', 'Query failed')}), 400

        students_by_id = {row.get('student_id'): row for row in stu.get('rows', [])}
        courses_by_id = {row.get('course_id'): row for row in cou.get('rows', [])}

        enriched = []
        for row in enr.get('rows', []):
            student = students_by_id.get(row.get('student_id'), {})
            course = courses_by_id.get(row.get('course_id'), {})
            enriched.append({
                'enrollment_id': row.get('enrollment_id'),
                'student_id': row.get('student_id'),
                'course_id': row.get('course_id'),
                'grade': row.get('grade'),
                'enrollment_date': row.get('enrollment_date'),
                'first_name': student.get('first_name'),
                'last_name': student.get('last_name'),
                'email': student.get('email'),
                'course_name': course.get('course_name'),
                'course_code': course.get('course_code'),
                'instructor': course.get('instructor'),
            })

        return jsonify({'success': True, 'data': enriched, 'count': len(enriched)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enrollments', methods=['POST'])
def create_enrollment():
    """Create a new enrollment"""
    try:
        data = request.json or {}
        enrollment_id = data.get('enrollment_id')
        if enrollment_id in (None, ''):
            enrollment_id = _next_int_id('enrollments', 'enrollment_id')
        else:
            enrollment_id = int(enrollment_id)

        student_id = int(data.get('student_id'))
        course_id = int(data.get('course_id'))
        grade = _sql_text(data.get('grade', ''))
        enrollment_date = _sql_text(data.get('enrollment_date', datetime.now().date().isoformat()))
        query = f"""
            INSERT INTO enrollments 
            (enrollment_id, student_id, course_id, grade, enrollment_date) 
            VALUES ({enrollment_id}, {student_id}, {course_id}, '{grade}', '{enrollment_date}')
        """
        result = engine.execute(query)
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Insert failed')}), 400
        return jsonify({'success': True, 'message': 'Enrollment created', 'enrollment_id': enrollment_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enrollments/<int:enrollment_id>', methods=['PUT'])
def update_enrollment(enrollment_id):
    """Update an enrollment"""
    try:
        data = request.json or {}

        updates = []
        if 'student_id' in data and data['student_id'] not in (None, ''):
            updates.append(f"student_id = {int(data['student_id'])}")
        if 'course_id' in data and data['course_id'] not in (None, ''):
            updates.append(f"course_id = {int(data['course_id'])}")
        if 'grade' in data:
            updates.append(f"grade = '{_sql_text(data.get('grade', ''))}'")
        if 'enrollment_date' in data and data['enrollment_date'] not in (None, ''):
            updates.append(f"enrollment_date = '{_sql_text(data['enrollment_date'])}'")

        if not updates:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400

        query = f"UPDATE enrollments SET {', '.join(updates)} WHERE enrollment_id = {enrollment_id}"
        result = engine.execute(query)
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Update failed')}), 400
        return jsonify({'success': True, 'message': 'Enrollment updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enrollments/<int:enrollment_id>', methods=['DELETE'])
def delete_enrollment(enrollment_id):
    """Delete an enrollment"""
    try:
        result = engine.execute(f"DELETE FROM enrollments WHERE enrollment_id = {enrollment_id}")
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Delete failed')}), 400
        return jsonify({'success': True, 'message': 'Enrollment deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ ANALYTICS ENDPOINTS ============

@app.route('/api/analytics/employees', methods=['GET'])
def get_analytics_employees():
    """Fetch employees with department info"""
    try:
        # Avoid SQL JOIN aliases for parser compatibility.
        emp = engine.execute("SELECT * FROM employees")
        dep = engine.execute("SELECT * FROM departments")
        for r in (emp, dep):
            if not r.get('success'):
                return jsonify({'success': False, 'error': r.get('error', 'Query failed')}), 400

        departments_by_id = {row.get('dept_id'): row for row in dep.get('rows', [])}
        enriched = []
        for row in emp.get('rows', []):
            d = departments_by_id.get(row.get('dept_id'), {})
            enriched.append({
                'emp_id': row.get('emp_id'),
                'name': row.get('name'),
                'email': row.get('email'),
                'position': row.get('position'),
                'salary': row.get('salary'),
                'dept_name': d.get('dept_name'),
                'location': d.get('location'),
            })

        return jsonify({'success': True, 'data': enriched, 'count': len(enriched)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/salary-by-department', methods=['GET'])
def get_salary_analytics():
    """Get salary statistics by department"""
    try:
        result = engine.execute("""
            SELECT d.dept_name, COUNT(*) as emp_count, AVG(e.salary) as avg_salary, 
                   MAX(e.salary) as max_salary, MIN(e.salary) as min_salary
            FROM employees e
            INNER JOIN departments d ON e.dept_id = d.dept_id
            GROUP BY d.dept_id
        """)
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'Query failed')}), 400
        return jsonify({'success': True, 'data': result.get('rows', [])})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ SQL EXECUTION & EXPLAIN ENDPOINTS ============

@app.route('/api/execute', methods=['POST'])
def execute_sql():
    """Execute arbitrary SQL and return results"""
    try:
        data = request.json
        sql = data.get('sql', '').strip()
        
        if not sql:
            return jsonify({'success': False, 'error': 'Empty SQL query'}), 400
        
        result = engine.execute(sql)
        if not result.get('success'):
            return jsonify({'success': False, 'type': 'ERROR', 'error': result.get('error', 'SQL failed')}), 400

        query_type = 'SELECT' if sql.upper().startswith('SELECT') else 'DDL/DML'
        return jsonify({
            'success': True,
            'type': query_type,
            'rows': result.get('rows', []),
            'count': result.get('count', result.get('rows_affected', 0)),
            'message': result.get('message', 'Query executed successfully')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'ERROR'
        }), 500


@app.route('/api/explain', methods=['POST'])
def explain_sql():
    """Get execution plan for SQL query"""
    try:
        data = request.json
        sql = data.get('sql', '').strip()
        
        if not sql:
            return jsonify({'success': False, 'error': 'Empty SQL query'}), 400
        
        # Use the explain command
        explain_result = engine.explain(sql)
        
        return jsonify({
            'success': True,
            'plan': explain_result,
            'sql': sql
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/schema', methods=['GET'])
def get_schema():
    """Get database schema information"""
    try:
        tables_info = engine.storage.get_system_tables_info()
        indexes_info = engine.storage.get_system_indexes_info()
        
        return jsonify({
            'success': True,
            'tables': tables_info,
            'indexes': indexes_info
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/engine-status', methods=['GET'])
def get_engine_status():
    """Get engine status and configuration"""
    return jsonify({
        'online': engine_status['online'],
        'persistence': engine_status['persistence'],
        'storage_mode': engine_status['storage_mode'],
        'initialized': engine_status['initialized'],
        'database': engine.current_database,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Get all tables with metadata"""
    try:
        tables = engine.storage.list_tables()
        tables_info = engine.storage.get_system_tables_info()
        
        result = []
        for table_info in tables_info:
            result.append({
                'table_name': table_info['table_name'],
                'row_count': table_info['row_count'],
                'column_count': len(table_info.get('columns', []))
            })
        
        return jsonify({
            'success': True,
            'database': engine.current_database,
            'tables': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    init_databases()
    app.run(debug=True, host='127.0.0.1', port=5000)
