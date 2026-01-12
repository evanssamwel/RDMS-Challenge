import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.engine import QueryEngine
from core.storage import Storage

storage = Storage(data_dir='tmp_debug')
engine = QueryEngine(storage)

engine.execute("CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(50))")
engine.execute("CREATE TABLE courses (id INT PRIMARY KEY, name VARCHAR(50))")
engine.execute("CREATE TABLE enrollments (id INT PRIMARY KEY, student_id INT, course_id INT)")
engine.execute("INSERT INTO students VALUES (1, 'Alice')")
engine.execute("INSERT INTO courses VALUES (1, 'Math')")
engine.execute("INSERT INTO enrollments VALUES (1, 1, 1)")

sql = """
SELECT students.name, courses.name
FROM enrollments
INNER JOIN students ON enrollments.student_id = students.id
INNER JOIN courses ON enrollments.course_id = courses.id
"""
res = engine.execute(sql)
print(res)
