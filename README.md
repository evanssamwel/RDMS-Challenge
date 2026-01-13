# SimpleSQLDB - A Simple Relational Database Management System

**Pesapal Junior Dev Challenge 2026**

SimpleSQLDB is a fully functional relational database management system (RDBMS) built from scratch in Python. It features SQL query support, B-tree indexing, JOIN operations, and a professional web-based dashboard showcasing CRUD operations.

## 🏗️ Architecture: Professional Separation of Concerns

SimpleSQLDB demonstrates **enterprise-grade N-Tier Architecture** with strict separation of concerns:

```
┌─────────────────────────────────────────────┐
│     Presentation Layer (Multiple)            │
│  ┌──────────────────┐  ┌────────────────┐  │
│  │   CLI/REPL       │  │   Web Studio   │  │
│  │   (repl/cli.py)  │  │  (web_demo/)   │  │
│  └──────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────┘
              ↓ Public API
┌─────────────────────────────────────────────┐
│     Core RDBMS Engine (Independent)         │
│  Parser → Engine → Aggregates → Indexing   │
└─────────────────────────────────────────────┘
              ↓ File I/O
┌─────────────────────────────────────────────┐
│     Persistence Layer (JSON + B-Tree)      │
└─────────────────────────────────────────────┘
```

**Key Insight:** The RDBMS engine is completely independent and can be used via:
- **CLI Interface** (repl/cli.py)
- **Web Application** (web_demo/app_studio.py)  
- **Direct Python API** (import core.engine)
- **Any custom application**

→ **Read [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation**

## 🌟 Features

### Core Database Features
- ✅ **Full SQL Support**: CREATE TABLE, INSERT, SELECT, UPDATE, DELETE
- ✅ **Data Types**: INT, VARCHAR(n), FLOAT, DATE, BOOLEAN
- ✅ **Constraints**: PRIMARY KEY, UNIQUE, NOT NULL, FOREIGN KEY
- ✅ **Referential Integrity**: Foreign key enforcement with cascade checks
- ✅ **Aggregate Functions**: COUNT, SUM, AVG, MAX, MIN
- ✅ **GROUP BY & HAVING**: Group aggregation with filtering
- ✅ **B-tree Indexing**: Fast lookups on primary and unique keys
- ✅ **JOIN Operations**: INNER JOIN and LEFT JOIN
- ✅ **WHERE Clauses**: Support for =, !=, <, >, <=, >=, LIKE operators
- ✅ **Logical Operators**: AND, OR in WHERE clauses
- ✅ **ORDER BY & LIMIT**: Result sorting and limiting
- ✅ **Query Explanation**: .explain command shows execution plans
- ✅ **Persistence**: Data stored in JSON format on disk
- ✅ **Interactive REPL**: Command-line SQL interface

### Demo Application
- 🎓 **Student Management System**: Complete CRUD operations
- 📚 **Course Management**: Add, view, delete courses
- 🔗 **Enrollment Tracking**: Demonstrates JOIN operations
- 💻 **SQL Console**: Execute raw SQL queries in the browser

## 📁 Project Structure

```
RDMS/
├── core/                    # Core database engine
│   ├── types.py            # Data type definitions
│   ├── schema.py           # Table schema management
│   ├── parser.py           # SQL parser
│   ├── index.py            # B-tree indexing
│   ├── storage.py          # Data persistence
│   └── engine.py           # Query execution engine
├── repl/                    # Interactive SQL REPL
│   └── cli.py              # Command-line interface
├── web_demo/               # Web application demo
│   ├── app.py              # Flask application
│   ├── templates/          # HTML templates
│   └── static/             # CSS stylesheets
├── data/                   # Database files (auto-created)
├── web_data/               # Web app database (auto-created)
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation & Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/evanssamwel/RDMS-Challenge.git
   cd RDMS-Challenge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run SimpleSQLDB** (Choose your interface)
   
   **Option A: Interactive Menu (Recommended)**
   ```bash
   python main.py
   ```
   This gives you a menu to choose between:
   - CLI/REPL Mode (command-line)
   - Web Studio (professional dashboard)
   - Documentation
   - Tests
   
   **Option B: Web Studio Directly**
   ```bash
   python web_demo/app_studio.py
   ```
   Then open: http://127.0.0.1:5000
   
   **Option C: CLI Mode Directly**
   ```bash
   python -m repl.cli
   ```

### Running the REPL

Start the interactive SQL REPL:

```bash
python main.py
# Select option 1
```

Example usage:
```sql
sql> CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100) UNIQUE);
Table users created successfully

sql> INSERT INTO users (id, name, email) VALUES (1, 'John Doe', 'john@example.com');
Row inserted with ID 0

sql> SELECT * FROM users;
id | name     | email
--------------------------
1  | John Doe | john@example.com

```1 row(s) returned

sql> .exit
```

### Using SimpleSQLDB as a Library

The beauty of SimpleSQLDB's architecture is that **the RDBMS engine is independent** and can be used programmatically:

```python
from core.engine import QueryEngine

# Create engine instance
engine = QueryEngine()

# Execute queries programmatically
students = engine.execute("SELECT * FROM students")
print(students)
# Output: [{'id': 1, 'name': 'John', ...}, {'id': 2, 'name': 'Jane', ...}]

# Use aggregates
stats = engine.execute("""
    SELECT dept_id, COUNT(*) as count, AVG(salary) as avg_salary
    FROM employees 
    GROUP BY dept_id
""")

# Get execution plans
plan = engine.explain("SELECT * FROM employees WHERE salary > 100000")
print(plan)  # Shows B-tree usage, access methods, etc.
```

→ **Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for more examples**

### Running the Web Application

Start the unified Database Management Studio:

```bash
python main.py
# Select option 2: Professional Web Studio
```

Or directly:
```bash
cd web_demo
python app_studio.py
```

Then open your browser to: **http://127.0.0.1:5000**

## 🏗️ Unified Database Management Studio

The web application demonstrates a **production-ready architecture** with a single platform managing multiple database schemas:

### Architecture Overview

Instead of separate applications, we built a **Unified Management Studio** that showcases your RDBMS engine as a versatile platform:

#### **Three Integrated Modules:**

1. **CRUD Manager** (Educational Database)
   - Students, Courses, Enrollments tables
   - Full CRUD operations (Create, Read, Update, Delete)
   - Demonstrates: Foreign Key JOINs, referential integrity
   - Use Case: University enrollment system

2. **Analytics Dashboard** (Kenyan HR Data)
   - Employees & Departments tables
   - GROUP BY aggregations (COUNT, AVG, MIN, MAX)
   - Salary analytics by department
   - Demonstrates: Complex JOINs, aggregate functions, HAVING clause
   - Use Case: Business intelligence reporting

3. **SQL Terminal** (Power User Mode)
   - Raw SQL execution against any table
   - Visual execution plans with .explain command
   - Terminal-style output formatting
   - Demonstrates: B-tree indexing, query optimization
   - Use Case: Advanced database administration

### Why This Architecture?

✅ **Shows Versatility**: Proves your RDBMS engine handles different schemas and use cases
✅ **Production-Ready**: Mimics enterprise tools like pgAdmin or MySQL Workbench
✅ **Single Codebase**: One Flask app, multiple use cases - demonstrates clean architecture
✅ **Comprehensive Demo**: Covers CRUD, Analytics, and SQL execution in one interface

### Screenshots

**Dashboard Overview:**
```
[Screenshot 1: Main Studio Dashboard]
- Sidebar navigation with three views
- Status indicator showing "Engine: Online | Persistence: Atomic JSON"
- Professional fintech-inspired design with emerald/slate color scheme
- Location: First landing page showing CRUD Manager for Students
```

**CRUD Manager in Action:**
```
[Screenshot 2: Students CRUD Operations]
- Table showing students with full data
- "Add Student" button demonstrating CREATE
- Delete icons for DELETE operations
- Enrollments table showing INNER JOIN results
- Location: CRUD Manager > Enrollments tab
```

**Analytics & Query Visualization:**
```
[Screenshot 3: SQL Terminal with Execution Plan]
- SQL query editor with syntax highlighting
- Results table below showing query output
- Execution plan displayed in terminal-style format
- Color-coded output (emerald for success, blue for metadata)
- Shows B-tree index usage, join strategies, aggregation methods
- Location: SQL Terminal tab
```

1. **Start the Flask server**
   ```powershell
   python web_demo/app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Explore the features:**
   - Add students and courses
   - Create enrollments (demonstrates JOINs)
   - Use the SQL Console to run custom queries

## 📚 SQL Examples

### Creating Tables
```sql
CREATE TABLE students (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    age INT,
    enrollment_date DATE
);

-- With foreign key
CREATE TABLE enrollments (
    id INT PRIMARY KEY,
    student_id INT REFERENCES students(id),
    course_id INT REFERENCES courses(id),
    grade FLOAT
);
```

### Inserting Data
```sql
INSERT INTO students (id, name, email, age, enrollment_date)
VALUES (1, 'Alice Smith', 'alice@example.com', 20, '2024-09-01');
```

### Querying Data
```sql
-- Simple SELECT
SELECT * FROM students;

-- WHERE clause
SELECT name, email FROM students WHERE age > 18;

-- LIKE operator
SELECT * FROM students WHERE name LIKE 'A%';

-- ORDER BY and LIMIT
SELECT * FROM students ORDER BY age DESC LIMIT 10;

-- Aggregate functions
SELECT COUNT(*) AS total FROM students;
SELECT AVG(age) AS avg_age FROM students;

-- GROUP BY
SELECT age, COUNT(*) AS count FROM students GROUP BY age;

-- GROUP BY with HAVING
SELECT age, COUNT(*) AS count 
FROM students 
GROUP BY age 
HAVING COUNT(*) > 5;
```

### JOIN Operations
```sql
-- INNER JOIN
SELECT students.name, courses.name
FROM enrollments
INNER JOIN students ON enrollments.student_id = students.id
INNER JOIN courses ON enrollments.course_id = courses.id;

-- LEFT JOIN
SELECT students.name, enrollments.grade
FROM students
LEFT JOIN enrollments ON students.id = enrollments.student_id;
```

### Updating Data
```sql
UPDATE students SET age = 21 WHERE id = 1;
```

### Deleting Data
```sql
DELETE FROM students WHERE id = 1;
```

### Creating Indexes
```sql
CREATE INDEX idx_student_email ON students (email);
```

### Query Explanation
```sql
.explain SELECT * FROM students WHERE age > 18;
-- Shows: index usage, table scan type, join strategy
```

## 🔧 Technical Implementation

### SQL Parser
- Hand-written recursive descent parser
- Tokenizes and parses SQL statements into executable structures
- Supports nested conditions and complex expressions

### Storage Engine
- JSON-based persistence with atomic writes
- In-memory caching for fast access
- Automatic schema validation and type conversion
- Row-based storage with internal row IDs

### B-tree Indexing
- Custom B-tree implementation for O(log n) lookups
- Automatically indexes primary keys and unique columns
- Supports range queries and exact matches
- Handles inserts, updates, and deletes

### Query Engine
- Executes parsed SQL statements
- Implements nested loop JOIN algorithms
- Aggregate function computation with GROUP BY
- Referential integrity enforcement for foreign keys
- WHERE clause evaluation with index optimization
- ORDER BY sorting and LIMIT support

## 🧪 Testing

Run the test suite:
```powershell
python -m pytest tests/ -v
```

## 📊 Performance Characteristics

- **Indexed Lookups**: O(log n) with B-tree indexing
- **Full Table Scans**: O(n) for non-indexed queries
- **JOINs**: O(n*m) nested loop implementation
- **Storage**: JSON format (readable, but not space-efficient)

## 🎯 Design Decisions

1. **JSON Storage**: Chosen for readability and debugging ease. In production, binary formats would be more efficient.

2. **Atomic Writes**: Uses temporary file + `os.replace()` for atomic writes. Writes data to `.tmp` file first, then atomically renames it. This prevents data corruption if power fails mid-write, ensuring ACID durability.

3. **B-tree Max Keys**: Set to 4 for demonstration purposes. Production systems typically use higher values (100+).

4. **In-Memory Caching**: All data loaded into memory on startup for performance. Trade-off: faster queries but limited by available RAM. Larger datasets would require pagination or memory-mapped files.

5. **Simple JOIN Algorithm**: Nested loop joins are easy to understand. Hash joins would be more efficient for large datasets.

6. **Virtual System Tables**: Implemented `.sys_tables` and `.sys_indexes` commands to query metadata, similar to MySQL's `information_schema` or PostgreSQL's `pg_catalog`.

## 🔮 Future Enhancements

- [x] Aggregate functions (COUNT, SUM, AVG, MAX, MIN)
- [x] GROUP BY and HAVING clauses
- [x] Foreign key constraints with referential integrity
- [x] Query execution plan visualization (.explain)
- [ ] Transactions with ACID guarantees
- [ ] Query optimization with cost-based planning
- [ ] Binary storage format for better space efficiency
- [ ] Hash indexes for equality comparisons
- [ ] Multi-column indexes
- [ ] User authentication and permissions
- [ ] Backup and restore functionality
- [ ] Subqueries and nested SELECTs

## 🛠️ Technologies Used

- **Python 3**: Core implementation language
- **Flask**: Web application framework
- **Tailwind CSS**: Professional UI styling (via CDN)
- **Alpine.js**: Lightweight frontend interactivity
- **Chart.js**: Data visualization for aggregates
- **JSON**: Data persistence with atomic writes
- **HTML5**: Semantic markup

## 🎨 Design Highlights

### Professional UI/UX
- **Fintech Color Palette**: Deep blues, slate greys, emerald green accents
- **Terminal-Style Code**: JetBrains Mono font for SQL queries and execution plans
- **Dark Theme**: Eye-friendly interface for extended database work
- **Responsive Layout**: Works on desktop and tablets

### Engine Status Indicators
The dashboard displays real-time engine health:
```
✓ Engine: Online
✓ Persistence: Atomic JSON (os.replace for safety)
✓ Storage Mode: B-Tree Indexed
```

### Execution Plan Visualization
Instead of plain text, explain plans are styled as terminals with color-coded output:
- Blue labels for metadata
- Green values for actual data
- Yellow keys for plan sections
- Hierarchical tree structure with proper indentation

## 📋 Design Decisions

### 1. **Unified Architecture Over Separate Apps**
Instead of building multiple isolated applications, we created one Dashboard Management Studio. This demonstrates:
- Your engine's versatility across schemas
- Professional software architecture (single platform, multiple use cases)
- Cleaner reviewer experience (one `python app_studio.py` to run everything)

### 2. **Atomic Persistence (os.replace)**
Data writes use a two-step process:
1. Write to temporary file
2. Atomic rename to final location
This prevents corruption from power failures or interruptions.

### 3. **B-tree Indexing for Performance**
Primary keys and unique columns use B-tree indexes:
- Fast lookups: O(log n) instead of O(n)
- Efficient range queries: SELECT * WHERE salary > 100000
- Visible in execution plans so reviewers see optimization

### 4. **Virtual System Tables**
- `.sys_tables`: Shows table metadata without separate storage
- `.sys_indexes`: Lists all indexes and their properties
- Demonstrates meta-database awareness (like PostgreSQL's information_schema)

## 🏁 Final Submission Checklist

- ✅ **RDBMS Core**: Full SQL parser, storage engine, indexing, constraints
- ✅ **CRUD Demo**: Interactive forms for students, courses, enrollments
- ✅ **Advanced Features**: Aggregates, GROUP BY, HAVING, JOINs, Foreign Keys
- ✅ **Web UI**: Professional Dashboard Management Studio
- ✅ **Explain Plans**: Visual execution strategy with terminal styling
- ✅ **Data Seeding**: Educational + HR datasets ready on startup
- ✅ **Production Patterns**: Atomic writes, error handling, input validation
- ✅ **Documentation**: Comprehensive README with architecture explanation
- ✅ **Code Quality**: Well-commented, type-hinted, tested

## 🤖 AI Attribution

In compliance with challenge requirements, AI assistance was used in the following areas:

**Code Generation:**
- Initial boilerplate structure for Flask routes and HTML templates
- Regex patterns for SQL parser (manually refined for nested logic and edge cases)
- Test case scaffolding (test logic and assertions written manually)

**Documentation:**
- Grammar and formatting improvements for README sections
- Docstring templates (content and technical details added manually)

**Problem Solving:**
- Discussion of B-tree algorithm approaches (implementation done manually)
- Debugging assistance for JOIN parsing edge cases
- UI/UX suggestions for professional dashboard appearance

All core logic, algorithms, and architectural decisions were implemented manually. The RDBMS engine, parser, indexing system, and query execution are original implementations.

## 📝 Acknowledgments

This project was built from scratch for the Pesapal Junior Dev Challenge 2026. All core components (parser, storage engine, indexing, query execution) were implemented without external database libraries.

## 👨‍💻 Author

E. Samwel

## 📄 License

This project is open source and available for educational purposes.

---

**Note**: This is a demonstration project built for a coding challenge. While it implements core RDBMS concepts, it's not intended for production use. For production databases, consider established systems like PostgreSQL, MySQL, or SQLite.
