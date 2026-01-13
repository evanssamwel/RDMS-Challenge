# SimpleSQLDB - Developer Guide

## Understanding the Architecture

Before diving in, understand that **SimpleSQLDB is an independent RDBMS** that can be used in multiple ways.

### The "Separation of Concerns" Principle

```
Your RDBMS (core/)  ← Can be used independently
    ↓
    ├─→ CLI Interface (repl/)
    ├─→ Web Application (web_demo/)
    ├─→ Your Custom App
    └─→ Mobile App, etc.
```

**The key insight:** The engine doesn't care how it's being used.

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/evanssamwel/RDMS-Challenge.git
cd RDMS-Challenge
pip install -r requirements.txt
```

### 2. Run the Application

```bash
# Interactive menu
python main.py

# Or directly:
# Option 1: CLI Mode
python -m repl.cli

# Option 2: Web Mode
python web_demo/app_studio.py
```

### 3. Access the Web Studio

Open browser: **http://127.0.0.1:5000**

## Using SimpleSQLDB Programmatically

### Example 1: Direct Engine Usage

```python
from core.engine import QueryEngine

# Create engine
engine = QueryEngine()

# Execute queries
students = engine.execute("SELECT * FROM students")
print(students)
# Output: [{'id': 1, 'name': 'John', 'email': 'john@uni.edu'}, ...]

# Insert data
engine.execute("INSERT INTO students (id, name, email) VALUES (5, 'Alice', 'alice@uni.edu')")

# Use aggregates
stats = engine.execute("SELECT dept_id, COUNT(*) as count FROM employees GROUP BY dept_id")

# Get execution plan
plan = engine.explain("SELECT * FROM employees WHERE salary > 100000")
print(plan)
```

### Example 2: Custom Application

```python
from core.engine import QueryEngine

class MyDatabaseApp:
    def __init__(self):
        self.engine = QueryEngine()
    
    def get_user(self, user_id):
        # Use engine as black box
        result = self.engine.execute(f"SELECT * FROM students WHERE id = {user_id}")
        return result[0] if result else None
    
    def create_user(self, name, email):
        sql = f"INSERT INTO students (name, email) VALUES ('{name}', '{email}')"
        self.engine.execute(sql)
        return True

# Use it
app = MyDatabaseApp()
user = app.get_user(1)
print(user)
```

### Example 3: With Custom Storage Location

```python
from core.engine import QueryEngine
from core.storage import Storage

# Use different storage location
custom_storage = Storage(data_dir='my_custom_data/')
engine = QueryEngine(custom_storage)

# Rest is the same
results = engine.execute("SELECT * FROM students")
```

## Project Structure

```
RDMS-Challenge/
│
├── 📁 core/                 ← THE RDBMS ENGINE
│   ├── engine.py            # Main entry point
│   ├── parser.py            # SQL parser
│   ├── storage.py           # File I/O with atomic writes
│   ├── index.py             # B-Tree indexing
│   └── ...
│
├── 📁 repl/                 ← CLI INTERFACE
│   ├── cli.py               # Interactive terminal
│   └── ...
│
├── 📁 web_demo/             ← WEB APPLICATION
│   ├── app_studio.py        # Flask app (uses core)
│   ├── templates/
│   │   └── studio.html
│   └── ...
│
├── 📁 tests/                ← UNIT TESTS
│   ├── test_engine.py
│   └── ...
│
├── main.py                  ← ENTRY POINT
├── ARCHITECTURE.md          ← THIS FILE
└── README.md
```

## Core API Reference

### QueryEngine

```python
from core.engine import QueryEngine

engine = QueryEngine(storage=None)

# Methods:
results = engine.execute(sql_string)     # Returns List[Dict]
plan = engine.explain(sql_string)        # Returns execution plan dict
tables = engine.get_tables()              # Returns list of table names
schema = engine.get_table_schema(name)   # Returns table schema
```

### Supported SQL

#### DDL (Data Definition Language)
```sql
CREATE TABLE students (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    created_date DATE
)

CREATE INDEX idx_email ON students(email)

DROP TABLE students
```

#### DML (Data Manipulation Language)
```sql
INSERT INTO students VALUES (1, 'John', 'john@uni.edu', '2023-01-15')

UPDATE students SET name = 'Jane' WHERE id = 1

DELETE FROM students WHERE id = 1
```

#### DQL (Data Query Language)
```sql
SELECT * FROM students

SELECT id, name FROM students WHERE id > 5

SELECT dept_id, COUNT(*) FROM employees GROUP BY dept_id

SELECT e.name, d.dept_name 
FROM employees e 
INNER JOIN departments d ON e.dept_id = d.dept_id

SELECT COUNT(*), AVG(salary), MAX(salary) FROM employees
```

#### Special Commands
```sql
.sys_tables           -- View all tables

.sys_indexes          -- View all indexes

.explain SELECT * ... -- Get execution plan
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_engine.py -v

# Run with coverage
pytest tests/ --cov=core
```

## Understanding the Web Architecture

### How the Web App Works

1. **User opens browser** → http://127.0.0.1:5000
2. **Flask app serves** → `studio.html` (HTML/CSS/JS)
3. **Frontend sends** → SQL queries via AJAX
4. **Backend receives** → POST `/api/execute` endpoint
5. **Backend calls** → `engine.execute(sql)` from core
6. **Engine processes** → Returns results
7. **Backend responds** → JSON response
8. **Frontend displays** → Results in table/chart

```python
# In web_demo/app_studio.py

@app.route('/api/execute', methods=['POST'])
def execute_sql():
    data = request.json
    sql = data.get('sql')
    
    # Core engine does the work
    result = engine.execute(sql)
    
    # Return standardized response
    return jsonify({
        'success': True,
        'rows': result,
        'count': len(result)
    })
```

### Web Features

| Feature | What It Does |
|---------|-------------|
| CRUD Manager | Insert/Update/Delete students, courses |
| Enrollments | View JOINed data (students + courses) |
| Analytics | HR dashboard with GROUP BY aggregates |
| SQL Terminal | Execute arbitrary SQL |
| Explain Plans | See query execution strategies |

## Development Tips

### 1. Adding a New SQL Feature

```python
# In core/engine.py
def execute(self, sql):
    # 1. Parse SQL
    ast = self.parser.parse(sql)
    
    # 2. Validate
    self._validate(ast)
    
    # 3. Execute
    result = self._execute_plan(ast)
    
    # 4. Return standardized format
    return result
```

### 2. Adding a New Web Endpoint

```python
# In web_demo/app_studio.py
@app.route('/api/my-feature', methods=['POST'])
def my_feature():
    data = request.json
    
    # Use engine
    result = engine.execute("SELECT ...")
    
    return jsonify({'success': True, 'data': result})
```

### 3. Testing Your Changes

```python
# In tests/test_my_feature.py
from core.engine import QueryEngine

def test_my_feature():
    engine = QueryEngine()
    result = engine.execute("SELECT * FROM students")
    assert len(result) > 0
```

## Performance Considerations

### B-Tree Indexing

The engine uses B-Tree indexing for faster lookups:

```python
# This is fast (uses index)
SELECT * FROM students WHERE email = 'john@uni.edu'

# This might be slower (table scan)
SELECT * FROM students WHERE name LIKE '%John%'
```

### Query Plans

Use `.explain` to understand how your query will execute:

```sql
.explain SELECT * FROM employees WHERE salary > 100000
-- Returns: access_method: INDEX SEEK
```

## Common Issues

### Issue: Empty database on first run

**Solution:** Run `populate_kenyan_data.py` to seed data:

```bash
python populate_kenyan_data.py
```

### Issue: "Table not found"

**Solution:** Check `.sys_tables` to see what tables exist:

```sql
.sys_tables
```

### Issue: Web app not loading

**Solution:** Ensure Flask is running and check:

```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Or use different port
python web_demo/app_studio.py --port 5001
```

## Next Steps

1. **Read ARCHITECTURE.md** - Understand the design
2. **Run main.py** - Try both CLI and Web
3. **Explore tests/** - See how engine is tested
4. **Modify and extend** - Add your own features
5. **Submit to Pesapal** - Show them professional code!

## Questions?

Check these files:
- **README.md** - Overview and features
- **ADVANCED_FEATURES.md** - Detailed feature docs
- **FINISHING_TOUCHES.md** - Production features
- **ARCHITECTURE.md** - Design patterns
- **tests/** - Real usage examples

---

**Remember:** SimpleSQLDB is a **professional RDBMS**, not just a web app. The architecture proves it. 🏆
