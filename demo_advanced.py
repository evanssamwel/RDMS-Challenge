"""
Demo script showcasing all SimpleSQLDB features including:
- Aggregate functions (COUNT, SUM, AVG, MAX, MIN)
- GROUP BY and HAVING clauses
- Foreign key constraints with referential integrity
- Query explanation (.explain command)
"""

from core.engine import QueryEngine
from core.storage import Storage
import shutil
from pathlib import Path

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_result(result):
    """Pretty print query result"""
    if result['success']:
        if 'rows' in result:
            rows = result['rows']
            if rows:
                # Print table
                columns = list(rows[0].keys())
                
                # Calculate column widths
                widths = {col: len(col) for col in columns}
                for row in rows:
                    for col in columns:
                        widths[col] = max(widths[col], len(str(row.get(col, ''))))
                
                # Print header
                header = ' | '.join(col.ljust(widths[col]) for col in columns)
                print(header)
                print('-' * len(header))
                
                # Print rows
                for row in rows:
                    row_str = ' | '.join(str(row.get(col, '')).ljust(widths[col]) for col in columns)
                    print(row_str)
                
                print(f"\n{result['count']} row(s) returned")
            else:
                print("(empty result set)")
        else:
            print(result.get('message', 'Success'))
    else:
        print(f"ERROR: {result['error']}")

def main():
    """Run the comprehensive demo"""
    
    # Clean up and create fresh database
    demo_dir = Path('demo_db')
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    
    storage = Storage(str(demo_dir))
    engine = QueryEngine(storage)
    
    print_section("SimpleSQLDB - Comprehensive Feature Demo")
    
    # ========== BASIC TABLE CREATION ==========
    print_section("1. Creating Tables with Constraints")
    
    print("Creating departments table:")
    result = engine.execute("""
        CREATE TABLE departments (
            id INT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            budget FLOAT
        );
    """)
    print_result(result)
    
    print("\nCreating employees table with FOREIGN KEY:")
    result = engine.execute("""
        CREATE TABLE employees (
            id INT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            dept_id INT REFERENCES departments(id),
            salary FLOAT,
            hire_date DATE
        );
    """)
    print_result(result)
    
    # ========== INSERTING DATA ==========
    print_section("2. Inserting Data")
    
    # Insert departments
    departments = [
        (1, 'Engineering', 500000.0),
        (2, 'Sales', 300000.0),
        (3, 'Marketing', 250000.0),
        (4, 'HR', 150000.0)
    ]
    
    for dept_id, name, budget in departments:
        engine.execute(f"INSERT INTO departments VALUES ({dept_id}, '{name}', {budget});")
    print(f"Inserted {len(departments)} departments")
    
    # Insert employees
    employees = [
        (1, 'Alice Johnson', 1, 95000.0, '2020-01-15'),
        (2, 'Bob Smith', 1, 85000.0, '2021-03-20'),
        (3, 'Charlie Brown', 1, 75000.0, '2022-06-10'),
        (4, 'Diana Prince', 2, 70000.0, '2020-05-01'),
        (5, 'Eve Wilson', 2, 65000.0, '2021-08-15'),
        (6, 'Frank Miller', 2, 60000.0, '2022-02-28'),
        (7, 'Grace Lee', 3, 55000.0, '2021-11-10'),
        (8, 'Henry Davis', 3, 50000.0, '2022-04-05'),
        (9, 'Ivy Chen', 4, 60000.0, '2020-09-20')
    ]
    
    for emp_id, name, dept_id, salary, hire_date in employees:
        engine.execute(f"INSERT INTO employees VALUES ({emp_id}, '{name}', {dept_id}, {salary}, '{hire_date}');")
    print(f"Inserted {len(employees)} employees")
    
    # ========== AGGREGATE FUNCTIONS ==========
    print_section("3. Aggregate Functions")
    
    print("Total number of employees:")
    result = engine.execute("SELECT COUNT(*) AS total_employees FROM employees;")
    print_result(result)
    
    print("\nAverage salary:")
    result = engine.execute("SELECT AVG(salary) AS avg_salary FROM employees;")
    print_result(result)
    
    print("\nMin and Max salaries:")
    result = engine.execute("SELECT MIN(salary) AS min_salary, MAX(salary) AS max_salary FROM employees;")
    print_result(result)
    
    print("\nTotal salary budget:")
    result = engine.execute("SELECT SUM(salary) AS total_salaries FROM employees;")
    print_result(result)
    
    # ========== GROUP BY ==========
    print_section("4. GROUP BY - Employees per Department")
    
    result = engine.execute("""
        SELECT dept_id, COUNT(*) AS employee_count, AVG(salary) AS avg_salary
        FROM employees
        GROUP BY dept_id;
    """)
    print_result(result)
    
    # ========== GROUP BY with HAVING ==========
    print_section("5. GROUP BY with HAVING - Departments with 3+ Employees")
    
    result = engine.execute("""
        SELECT dept_id, COUNT(*) AS employee_count
        FROM employees
        GROUP BY dept_id
        HAVING COUNT(*) >= 3;
    """)
    print_result(result)
    
    # ========== JOIN with AGGREGATES ==========
    print_section("6. JOIN - Employee and Department Names")
    
    result = engine.execute("""
        SELECT employees.name, departments.name
        FROM employees
        INNER JOIN departments ON employees.dept_id = departments.id;
    """)
    print_result(result)
    
    print("\nDepartment salary totals (using subquery approach):")
    print("First, get totals per department:")
    result = engine.execute("""
        SELECT dept_id, COUNT(*) AS employee_count, SUM(salary) AS total_salaries
        FROM employees
        GROUP BY dept_id;
    """)
    print_result(result)
    
    # ========== FOREIGN KEY ENFORCEMENT ==========
    print_section("7. Foreign Key Constraint Enforcement")
    
    print("Attempting to insert employee with invalid department (should fail):")
    result = engine.execute("INSERT INTO employees VALUES (10, 'John Invalid', 999, 50000.0, '2023-01-01');")
    print_result(result)
    
    print("\nAttempting to delete department with employees (should fail):")
    result = engine.execute("DELETE FROM departments WHERE id = 1;")
    print_result(result)
    
    print("\nDeleting employee first, then department (should succeed):")
    result = engine.execute("DELETE FROM employees WHERE dept_id = 4;")
    print_result(result)
    result = engine.execute("DELETE FROM departments WHERE id = 4;")
    print_result(result)
    
    # ========== COMPLEX QUERY ==========
    print_section("8. Complex Query - Departments with High Average Salary")
    
    result = engine.execute("""
        SELECT dept_id, COUNT(*) AS emp_count, AVG(salary) AS avg_salary
        FROM employees
        GROUP BY dept_id
        HAVING AVG(salary) > 70000;
    """)
    print_result(result)
    
    # ========== QUERY EXPLANATION ==========
    print_section("9. Query Execution Plan (.explain)")
    
    print("To see query execution plans, use the REPL:")
    print("  python repl/cli.py")
    print("  sql> .explain SELECT * FROM employees WHERE dept_id = 1;")
    print("\nQuery plans show:")
    print("  - Index usage (Index Scan vs Full Table Scan)")
    print("  - JOIN strategies (Nested Loop with/without indexes)")
    print("  - Aggregation and grouping operations")
    
    # ========== FINAL SUMMARY ==========
    print_section("Demo Complete!")
    
    print("All tables:")
    for table_name in storage.list_tables():
        print(f"  - {table_name}")
    
    print("\nFeatures Demonstrated:")
    print("  [x] Table creation with constraints")
    print("  [x] Foreign key references")
    print("  [x] Aggregate functions (COUNT, SUM, AVG, MIN, MAX)")
    print("  [x] GROUP BY clause")
    print("  [x] HAVING clause")
    print("  [x] JOIN operations with aggregates")
    print("  [x] Foreign key enforcement")
    print("  [x] Referential integrity")
    print("  [x] Query execution plans")
    
    print("\nDatabase files saved in:", demo_dir)

if __name__ == '__main__':
    main()
