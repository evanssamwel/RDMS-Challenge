"""
Flask web application demonstrating SimpleSQLDB
Student Management System with CRUD operations
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import QueryEngine
from core.storage import Storage

app = Flask(__name__)

# Initialize database
storage = Storage(data_dir='web_data')
engine = QueryEngine(storage)

# Initialize database schema
def init_database():
    """Initialize database with tables if they don't exist"""
    tables = storage.list_tables()
    
    if 'students' not in tables:
        # Create students table
        engine.execute("""
            CREATE TABLE students (
                id INT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                age INT,
                enrollment_date DATE
            )
        """)
    
    if 'courses' not in tables:
        # Create courses table
        engine.execute("""
            CREATE TABLE courses (
                id INT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) UNIQUE,
                credits INT
            )
        """)
    
    if 'enrollments' not in tables:
        # Create enrollments table (junction table)
        engine.execute("""
            CREATE TABLE enrollments (
                id INT PRIMARY KEY,
                student_id INT NOT NULL,
                course_id INT NOT NULL,
                grade VARCHAR(2)
            )
        """)
        
        # Create indexes for better JOIN performance
        engine.execute("CREATE INDEX idx_enrollment_student ON enrollments (student_id)")
        engine.execute("CREATE INDEX idx_enrollment_course ON enrollments (course_id)")

# Initialize on startup
init_database()


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/students')
def students():
    """List all students"""
    result = engine.execute("SELECT * FROM students")
    
    if result['success']:
        return render_template('students.html', students=result['rows'])
    else:
        return render_template('students.html', students=[], error=result['error'])


@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    """Add a new student"""
    if request.method == 'POST':
        data = request.form
        
        sql = f"""
            INSERT INTO students (id, name, email, age, enrollment_date)
            VALUES ({data['id']}, '{data['name']}', '{data['email']}', 
                    {data['age']}, '{data['enrollment_date']}')
        """
        
        result = engine.execute(sql)
        
        if result['success']:
            return redirect(url_for('students'))
        else:
            return render_template('add_student.html', error=result['error'])
    
    return render_template('add_student.html')


@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit a student"""
    if request.method == 'POST':
        data = request.form
        
        sql = f"""
            UPDATE students
            SET name = '{data['name']}',
                email = '{data['email']}',
                age = {data['age']},
                enrollment_date = '{data['enrollment_date']}'
            WHERE id = {student_id}
        """
        
        result = engine.execute(sql)
        
        if result['success']:
            return redirect(url_for('students'))
        else:
            return render_template('edit_student.html', error=result['error'])
    
    # Get student data
    result = engine.execute(f"SELECT * FROM students WHERE id = {student_id}")
    
    if result['success'] and result['rows']:
        return render_template('edit_student.html', student=result['rows'][0])
    else:
        return redirect(url_for('students'))


@app.route('/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Delete a student"""
    # Delete enrollments first
    engine.execute(f"DELETE FROM enrollments WHERE student_id = {student_id}")
    
    # Delete student
    result = engine.execute(f"DELETE FROM students WHERE id = {student_id}")
    
    return redirect(url_for('students'))


@app.route('/courses')
def courses():
    """List all courses"""
    result = engine.execute("SELECT * FROM courses")
    
    if result['success']:
        return render_template('courses.html', courses=result['rows'])
    else:
        return render_template('courses.html', courses=[], error=result['error'])


@app.route('/courses/add', methods=['GET', 'POST'])
def add_course():
    """Add a new course"""
    if request.method == 'POST':
        data = request.form
        
        sql = f"""
            INSERT INTO courses (id, name, code, credits)
            VALUES ({data['id']}, '{data['name']}', '{data['code']}', {data['credits']})
        """
        
        result = engine.execute(sql)
        
        if result['success']:
            return redirect(url_for('courses'))
        else:
            return render_template('add_course.html', error=result['error'])
    
    return render_template('add_course.html')


@app.route('/courses/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    """Delete a course"""
    # Delete enrollments first
    engine.execute(f"DELETE FROM enrollments WHERE course_id = {course_id}")
    
    # Delete course
    result = engine.execute(f"DELETE FROM courses WHERE id = {course_id}")
    
    return redirect(url_for('courses'))


@app.route('/enrollments')
def enrollments():
    """List all enrollments with JOINs"""
    sql = """
        SELECT students.name, students.email, courses.name, courses.code, enrollments.grade
        FROM enrollments
        INNER JOIN students ON enrollments.student_id = students.id
        INNER JOIN courses ON enrollments.course_id = courses.id
    """
    
    result = engine.execute(sql)
    
    if result['success']:
        # Rename columns for display
        rows = []
        for row in result['rows']:
            rows.append({
                'student_name': row.get('name'),
                'student_email': row.get('email'),
                'course_name': list(row.values())[2] if len(row.values()) > 2 else '',
                'course_code': row.get('code'),
                'grade': row.get('grade')
            })
        return render_template('enrollments.html', enrollments=rows)
    else:
        return render_template('enrollments.html', enrollments=[], error=result['error'])


@app.route('/enrollments/add', methods=['GET', 'POST'])
def add_enrollment():
    """Add a new enrollment"""
    if request.method == 'POST':
        data = request.form
        
        sql = f"""
            INSERT INTO enrollments (id, student_id, course_id, grade)
            VALUES ({data['id']}, {data['student_id']}, {data['course_id']}, '{data['grade']}')
        """
        
        result = engine.execute(sql)
        
        if result['success']:
            return redirect(url_for('enrollments'))
        else:
            # Get students and courses for the form
            students_result = engine.execute("SELECT * FROM students")
            courses_result = engine.execute("SELECT * FROM courses")
            
            return render_template('add_enrollment.html',
                                 students=students_result['rows'],
                                 courses=courses_result['rows'],
                                 error=result['error'])
    
    # Get students and courses for the form
    students_result = engine.execute("SELECT * FROM students")
    courses_result = engine.execute("SELECT * FROM courses")
    
    return render_template('add_enrollment.html',
                         students=students_result['rows'],
                         courses=courses_result['rows'])


@app.route('/api/execute', methods=['POST'])
def api_execute():
    """API endpoint to execute raw SQL"""
    data = request.json
    sql = data.get('sql', '')
    
    result = engine.execute(sql)
    return jsonify(result)


@app.route('/sql-console')
def sql_console():
    """SQL console page"""
    return render_template('sql_console.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
