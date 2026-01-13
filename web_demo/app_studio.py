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

app = Flask(__name__)
app.secret_key = 'simplesqldb-studio-2026'

# Initialize database with both schemas
storage = Storage(data_dir='studio_data')
engine = QueryEngine(storage)

# Track engine status
engine_status = {
    'online': True,
    'persistence': 'Atomic JSON (os.replace)',
    'storage_mode': 'B-Tree Indexed',
    'initialized': False
}


def init_databases():
    """Initialize both educational and analytics datasets"""
    tables = storage.list_tables()
    
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
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/students', methods=['POST'])
def create_student():
    """Create a new student"""
    try:
        data = request.json
        query = f"""
            INSERT INTO students 
            (student_id, first_name, last_name, email, phone, enrollment_date) 
            VALUES ({data['student_id']}, '{data['first_name']}', '{data['last_name']}', '{data['email']}', '{data['phone']}', '{data['enrollment_date']}')
        """
        engine.execute(query)
        return jsonify({'success': True, 'message': 'Student created'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Update a student"""
    try:
        data = request.json
        query = f"""
            UPDATE students 
            SET first_name = '{data['first_name']}', 
                last_name = '{data['last_name']}', 
                email = '{data['email']}', 
                phone = '{data['phone']}'
            WHERE student_id = {student_id}
        """
        engine.execute(query)
        return jsonify({'success': True, 'message': 'Student updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
    try:
        engine.execute(f"DELETE FROM students WHERE student_id = {student_id}")
        return jsonify({'success': True, 'message': 'Student deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Fetch all courses"""
    try:
        result = engine.execute("SELECT * FROM courses")
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/courses', methods=['POST'])
def create_course():
    """Create a new course"""
    try:
        data = request.json
        query = f"""
            INSERT INTO courses 
            (course_id, course_name, course_code, credits, instructor) 
            VALUES ({data['course_id']}, '{data['course_name']}', '{data['course_code']}', {data['credits']}, '{data['instructor']}')
        """
        engine.execute(query)
        return jsonify({'success': True, 'message': 'Course created'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enrollments', methods=['GET'])
def get_enrollments():
    """Fetch all enrollments with student and course info"""
    try:
        result = engine.execute("""
            SELECT e.enrollment_id, s.first_name, s.last_name, c.course_name, c.course_code, e.grade, e.enrollment_date
            FROM enrollments e
            INNER JOIN students s ON e.student_id = s.student_id
            INNER JOIN courses c ON e.course_id = c.course_id
        """)
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enrollments', methods=['POST'])
def create_enrollment():
    """Create a new enrollment"""
    try:
        data = request.json
        query = f"""
            INSERT INTO enrollments 
            (enrollment_id, student_id, course_id, grade, enrollment_date) 
            VALUES ({data['enrollment_id']}, {data['student_id']}, {data['course_id']}, '{data['grade']}', '{data['enrollment_date']}')
        """
        engine.execute(query)
        return jsonify({'success': True, 'message': 'Enrollment created'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ ANALYTICS ENDPOINTS ============

@app.route('/api/analytics/employees', methods=['GET'])
def get_analytics_employees():
    """Fetch employees with department info"""
    try:
        result = engine.execute("""
            SELECT e.emp_id, e.name, e.email, e.position, e.salary, d.dept_name, d.location
            FROM employees e
            INNER JOIN departments d ON e.dept_id = d.dept_id
        """)
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
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
        return jsonify({
            'success': True,
            'data': result
        })
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
        
        # Determine query type
        query_type = 'SELECT' if sql.upper().startswith('SELECT') else 'DDL/DML'
        
        return jsonify({
            'success': True,
            'type': query_type,
            'rows': result if isinstance(result, list) else [],
            'count': len(result) if isinstance(result, list) else 0,
            'message': 'Query executed successfully'
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
        tables_info = storage.get_system_tables_info()
        indexes_info = storage.get_system_indexes_info()
        
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
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Get all tables with metadata"""
    try:
        tables = storage.list_tables()
        tables_info = storage.get_system_tables_info()
        
        result = []
        for table_info in tables_info:
            result.append({
                'table_name': table_info['table_name'],
                'row_count': table_info['row_count'],
                'column_count': len(table_info.get('columns', []))
            })
        
        return jsonify({
            'success': True,
            'tables': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    init_databases()
    app.run(debug=True, host='127.0.0.1', port=5000)
