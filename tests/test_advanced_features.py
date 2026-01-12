"""
Tests for advanced features: aggregates, GROUP BY, HAVING, foreign keys, .explain

This test suite covers:
- Aggregate functions (COUNT, SUM, AVG, MAX, MIN)
- GROUP BY clause
- HAVING clause for filtering groups
- Foreign key constraints
- Referential integrity enforcement
- Query explanation (.explain command)
"""
import pytest
import shutil
from pathlib import Path
from core.engine import QueryEngine
from core.storage import Storage


@pytest.fixture
def test_storage(tmp_path):
    """Create a temporary storage for testing"""
    storage = Storage(str(tmp_path))
    yield storage
    # Cleanup
    if Path(tmp_path).exists():
        shutil.rmtree(tmp_path)


@pytest.fixture
def test_engine(test_storage):
    """Create a test engine"""
    return QueryEngine(test_storage)


def test_aggregate_count_all(test_engine):
    """Test COUNT(*) aggregate"""
    # Create table
    test_engine.execute("CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100), price FLOAT);")
    
    # Insert data
    test_engine.execute("INSERT INTO products VALUES (1, 'Laptop', 999.99);")
    test_engine.execute("INSERT INTO products VALUES (2, 'Mouse', 29.99);")
    test_engine.execute("INSERT INTO products VALUES (3, 'Keyboard', 79.99);")
    
    # Test COUNT(*)
    result = test_engine.execute("SELECT COUNT(*) AS total FROM products;")
    assert result['success']
    assert result['rows'][0]['total'] == 3


def test_aggregate_sum_avg(test_engine):
    """Test SUM and AVG aggregates"""
    # Create table
    test_engine.execute("CREATE TABLE sales (id INT PRIMARY KEY, amount FLOAT, quantity INT);")
    
    # Insert data
    test_engine.execute("INSERT INTO sales VALUES (1, 100.0, 5);")
    test_engine.execute("INSERT INTO sales VALUES (2, 200.0, 10);")
    test_engine.execute("INSERT INTO sales VALUES (3, 150.0, 7);")
    
    # Test SUM
    result = test_engine.execute("SELECT SUM(amount) AS total_amount FROM sales;")
    assert result['success']
    assert result['rows'][0]['total_amount'] == 450.0
    
    # Test AVG
    result = test_engine.execute("SELECT AVG(quantity) AS avg_qty FROM sales;")
    assert result['success']
    assert abs(result['rows'][0]['avg_qty'] - 7.333) < 0.01


def test_aggregate_max_min(test_engine):
    """Test MAX and MIN aggregates"""
    # Create table
    test_engine.execute("CREATE TABLE scores (id INT PRIMARY KEY, score INT);")
    
    # Insert data
    test_engine.execute("INSERT INTO scores VALUES (1, 85);")
    test_engine.execute("INSERT INTO scores VALUES (2, 92);")
    test_engine.execute("INSERT INTO scores VALUES (3, 78);")
    
    # Test MAX
    result = test_engine.execute("SELECT MAX(score) AS max_score FROM scores;")
    assert result['success']
    assert result['rows'][0]['max_score'] == 92
    
    # Test MIN
    result = test_engine.execute("SELECT MIN(score) AS min_score FROM scores;")
    assert result['success']
    assert result['rows'][0]['min_score'] == 78


def test_group_by_single_column(test_engine):
    """Test GROUP BY with single column"""
    # Create table
    test_engine.execute("CREATE TABLE orders (id INT PRIMARY KEY, category VARCHAR(50), amount FLOAT);")
    
    # Insert data
    test_engine.execute("INSERT INTO orders VALUES (1, 'Electronics', 100.0);")
    test_engine.execute("INSERT INTO orders VALUES (2, 'Electronics', 200.0);")
    test_engine.execute("INSERT INTO orders VALUES (3, 'Books', 30.0);")
    test_engine.execute("INSERT INTO orders VALUES (4, 'Books', 45.0);")
    
    # Test GROUP BY
    result = test_engine.execute("SELECT category, COUNT(*) AS count, SUM(amount) AS total FROM orders GROUP BY category;")
    assert result['success']
    assert len(result['rows']) == 2
    
    # Find Electronics group
    electronics = [r for r in result['rows'] if r['category'] == 'Electronics'][0]
    assert electronics['count'] == 2
    assert electronics['total'] == 300.0
    
    # Find Books group
    books = [r for r in result['rows'] if r['category'] == 'Books'][0]
    assert books['count'] == 2
    assert books['total'] == 75.0


def test_group_by_multiple_columns(test_engine):
    """Test GROUP BY with multiple columns"""
    # Create table
    test_engine.execute("CREATE TABLE sales (id INT PRIMARY KEY, region VARCHAR(50), category VARCHAR(50), amount FLOAT);")
    
    # Insert data
    test_engine.execute("INSERT INTO sales VALUES (1, 'North', 'Electronics', 100.0);")
    test_engine.execute("INSERT INTO sales VALUES (2, 'North', 'Electronics', 150.0);")
    test_engine.execute("INSERT INTO sales VALUES (3, 'North', 'Books', 50.0);")
    test_engine.execute("INSERT INTO sales VALUES (4, 'South', 'Electronics', 200.0);")
    
    # Test GROUP BY multiple columns
    result = test_engine.execute("SELECT region, category, SUM(amount) AS total FROM sales GROUP BY region, category;")
    assert result['success']
    assert len(result['rows']) == 3


def test_having_clause(test_engine):
    """Test HAVING clause for filtering groups"""
    # Create table
    test_engine.execute("CREATE TABLE orders (id INT PRIMARY KEY, customer VARCHAR(50), total FLOAT);")
    
    # Insert data
    test_engine.execute("INSERT INTO orders VALUES (1, 'Alice', 100.0);")
    test_engine.execute("INSERT INTO orders VALUES (2, 'Alice', 150.0);")
    test_engine.execute("INSERT INTO orders VALUES (3, 'Bob', 50.0);")
    test_engine.execute("INSERT INTO orders VALUES (4, 'Bob', 30.0);")
    test_engine.execute("INSERT INTO orders VALUES (5, 'Charlie', 300.0);")
    
    # Test HAVING: customers with total > 200
    result = test_engine.execute(
        "SELECT customer, SUM(total) AS sum_total FROM orders GROUP BY customer HAVING SUM(total) > 200;"
    )
    assert result['success']
    assert len(result['rows']) == 2  # Alice and Charlie
    
    customers = {r['customer'] for r in result['rows']}
    assert 'Alice' in customers
    assert 'Charlie' in customers
    assert 'Bob' not in customers


def test_foreign_key_insert_valid(test_engine):
    """Test foreign key constraint with valid insert"""
    # Create parent table
    test_engine.execute("CREATE TABLE departments (id INT PRIMARY KEY, name VARCHAR(100));")
    test_engine.execute("INSERT INTO departments VALUES (1, 'Engineering');")
    test_engine.execute("INSERT INTO departments VALUES (2, 'Sales');")
    
    # Create child table with foreign key
    test_engine.execute(
        "CREATE TABLE employees (id INT PRIMARY KEY, name VARCHAR(100), dept_id INT REFERENCES departments(id));"
    )
    
    # Insert with valid foreign key
    result = test_engine.execute("INSERT INTO employees VALUES (1, 'Alice', 1);")
    assert result['success']


def test_foreign_key_insert_invalid(test_engine):
    """Test foreign key constraint with invalid insert"""
    # Create parent table
    test_engine.execute("CREATE TABLE departments (id INT PRIMARY KEY, name VARCHAR(100));")
    test_engine.execute("INSERT INTO departments VALUES (1, 'Engineering');")
    
    # Create child table with foreign key
    test_engine.execute(
        "CREATE TABLE employees (id INT PRIMARY KEY, name VARCHAR(100), dept_id INT REFERENCES departments(id));"
    )
    
    # Try to insert with invalid foreign key
    result = test_engine.execute("INSERT INTO employees VALUES (1, 'Alice', 999);")
    assert not result['success']
    assert 'foreign key' in result['error'].lower()


def test_foreign_key_delete_violation(test_engine):
    """Test referential integrity on delete"""
    # Create parent table
    test_engine.execute("CREATE TABLE departments (id INT PRIMARY KEY, name VARCHAR(100));")
    test_engine.execute("INSERT INTO departments VALUES (1, 'Engineering');")
    
    # Create child table with foreign key
    test_engine.execute(
        "CREATE TABLE employees (id INT PRIMARY KEY, name VARCHAR(100), dept_id INT REFERENCES departments(id));"
    )
    test_engine.execute("INSERT INTO employees VALUES (1, 'Alice', 1);")
    
    # Try to delete parent row that is referenced
    result = test_engine.execute("DELETE FROM departments WHERE id = 1;")
    assert not result['success']
    assert 'referenced' in result['error'].lower()


def test_foreign_key_update_valid(test_engine):
    """Test foreign key constraint with valid update"""
    # Create parent table
    test_engine.execute("CREATE TABLE departments (id INT PRIMARY KEY, name VARCHAR(100));")
    test_engine.execute("INSERT INTO departments VALUES (1, 'Engineering');")
    test_engine.execute("INSERT INTO departments VALUES (2, 'Sales');")
    
    # Create child table with foreign key
    test_engine.execute(
        "CREATE TABLE employees (id INT PRIMARY KEY, name VARCHAR(100), dept_id INT REFERENCES departments(id));"
    )
    test_engine.execute("INSERT INTO employees VALUES (1, 'Alice', 1);")
    
    # Update to valid foreign key
    result = test_engine.execute("UPDATE employees SET dept_id = 2 WHERE id = 1;")
    assert result['success']


def test_foreign_key_update_invalid(test_engine):
    """Test foreign key constraint with invalid update"""
    # Create parent table
    test_engine.execute("CREATE TABLE departments (id INT PRIMARY KEY, name VARCHAR(100));")
    test_engine.execute("INSERT INTO departments VALUES (1, 'Engineering');")
    
    # Create child table with foreign key
    test_engine.execute(
        "CREATE TABLE employees (id INT PRIMARY KEY, name VARCHAR(100), dept_id INT REFERENCES departments(id));"
    )
    test_engine.execute("INSERT INTO employees VALUES (1, 'Alice', 1);")
    
    # Update to invalid foreign key
    result = test_engine.execute("UPDATE employees SET dept_id = 999 WHERE id = 1;")
    assert not result['success']
    assert 'foreign key' in result['error'].lower()


def test_aggregate_with_where(test_engine):
    """Test aggregates combined with WHERE clause"""
    # Create table
    test_engine.execute("CREATE TABLE products (id INT PRIMARY KEY, category VARCHAR(50), price FLOAT);")
    
    # Insert data
    test_engine.execute("INSERT INTO products VALUES (1, 'Electronics', 100.0);")
    test_engine.execute("INSERT INTO products VALUES (2, 'Electronics', 200.0);")
    test_engine.execute("INSERT INTO products VALUES (3, 'Books', 30.0);")
    test_engine.execute("INSERT INTO products VALUES (4, 'Books', 45.0);")
    
    # Test aggregate with WHERE
    result = test_engine.execute("SELECT COUNT(*) AS count FROM products WHERE category = 'Electronics';")
    assert result['success']
    assert result['rows'][0]['count'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
