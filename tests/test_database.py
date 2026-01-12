"""
Unit tests for SimpleSQLDB
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from core.engine import QueryEngine
from core.storage import Storage
import tempfile
import shutil


@pytest.fixture
def engine():
    """Create a test engine with temporary storage"""
    temp_dir = tempfile.mkdtemp()
    storage = Storage(data_dir=temp_dir)
    engine = QueryEngine(storage)
    
    yield engine
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_create_table(engine):
    """Test CREATE TABLE"""
    result = engine.execute("""
        CREATE TABLE users (
            id INT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE
        )
    """)
    
    assert result['success'] == True
    assert 'users' in engine.storage.list_tables()


def test_insert_and_select(engine):
    """Test INSERT and SELECT"""
    # Create table
    engine.execute("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50))")
    
    # Insert data
    result = engine.execute("INSERT INTO users (id, name) VALUES (1, 'Alice')")
    assert result['success'] == True
    
    # Select data
    result = engine.execute("SELECT * FROM users")
    assert result['success'] == True
    assert len(result['rows']) == 1
    assert result['rows'][0]['name'] == 'Alice'


def test_where_clause(engine):
    """Test WHERE clause"""
    engine.execute("CREATE TABLE users (id INT PRIMARY KEY, age INT)")
    engine.execute("INSERT INTO users VALUES (1, 25)")
    engine.execute("INSERT INTO users VALUES (2, 30)")
    engine.execute("INSERT INTO users VALUES (3, 20)")
    
    result = engine.execute("SELECT * FROM users WHERE age > 22")
    assert result['success'] == True
    assert len(result['rows']) == 2


def test_update(engine):
    """Test UPDATE"""
    engine.execute("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50))")
    engine.execute("INSERT INTO users VALUES (1, 'Alice')")
    
    result = engine.execute("UPDATE users SET name = 'Bob' WHERE id = 1")
    assert result['success'] == True
    assert result['rows_affected'] == 1
    
    result = engine.execute("SELECT * FROM users WHERE id = 1")
    assert result['rows'][0]['name'] == 'Bob'


def test_delete(engine):
    """Test DELETE"""
    engine.execute("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50))")
    engine.execute("INSERT INTO users VALUES (1, 'Alice')")
    engine.execute("INSERT INTO users VALUES (2, 'Bob')")
    
    result = engine.execute("DELETE FROM users WHERE id = 1")
    assert result['success'] == True
    assert result['rows_affected'] == 1
    
    result = engine.execute("SELECT * FROM users")
    assert len(result['rows']) == 1


def test_inner_join(engine):
    """Test INNER JOIN"""
    # Create tables
    engine.execute("CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(50))")
    engine.execute("CREATE TABLE courses (id INT PRIMARY KEY, name VARCHAR(50))")
    engine.execute("CREATE TABLE enrollments (id INT PRIMARY KEY, student_id INT, course_id INT)")
    
    # Insert data
    engine.execute("INSERT INTO students VALUES (1, 'Alice')")
    engine.execute("INSERT INTO courses VALUES (1, 'Math')")
    engine.execute("INSERT INTO enrollments VALUES (1, 1, 1)")
    
    # Join
    result = engine.execute("""
        SELECT students.name, courses.name
        FROM enrollments
        INNER JOIN students ON enrollments.student_id = students.id
        INNER JOIN courses ON enrollments.course_id = courses.id
    """)
    
    assert result['success'] == True
    assert len(result['rows']) == 1


def test_unique_constraint(engine):
    """Test UNIQUE constraint"""
    engine.execute("CREATE TABLE users (id INT PRIMARY KEY, email VARCHAR(100) UNIQUE)")
    engine.execute("INSERT INTO users VALUES (1, 'test@example.com')")
    
    # Try to insert duplicate
    result = engine.execute("INSERT INTO users VALUES (2, 'test@example.com')")
    assert result['success'] == False


def test_primary_key_constraint(engine):
    """Test PRIMARY KEY constraint"""
    engine.execute("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50))")
    engine.execute("INSERT INTO users VALUES (1, 'Alice')")
    
    # Try to insert duplicate primary key
    result = engine.execute("INSERT INTO users VALUES (1, 'Bob')")
    assert result['success'] == False


def test_order_by(engine):
    """Test ORDER BY"""
    engine.execute("CREATE TABLE users (id INT PRIMARY KEY, age INT)")
    engine.execute("INSERT INTO users VALUES (1, 30)")
    engine.execute("INSERT INTO users VALUES (2, 20)")
    engine.execute("INSERT INTO users VALUES (3, 25)")
    
    result = engine.execute("SELECT * FROM users ORDER BY age ASC")
    assert result['rows'][0]['age'] == 20
    assert result['rows'][2]['age'] == 30


def test_limit(engine):
    """Test LIMIT"""
    engine.execute("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50))")
    engine.execute("INSERT INTO users VALUES (1, 'Alice')")
    engine.execute("INSERT INTO users VALUES (2, 'Bob')")
    engine.execute("INSERT INTO users VALUES (3, 'Charlie')")
    
    result = engine.execute("SELECT * FROM users LIMIT 2")
    assert len(result['rows']) == 2


def test_persistence(engine):
    """Test data persistence"""
    # Create and insert data
    engine.execute("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50))")
    engine.execute("INSERT INTO users VALUES (1, 'Alice')")
    
    # Create new engine with same storage
    storage = Storage(data_dir=engine.storage.data_dir)
    new_engine = QueryEngine(storage)
    
    # Verify data persisted
    result = new_engine.execute("SELECT * FROM users")
    assert len(result['rows']) == 1
    assert result['rows'][0]['name'] == 'Alice'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
