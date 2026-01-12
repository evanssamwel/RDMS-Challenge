# SimpleSQLDB - A Simple Relational Database Management System

**Pesapal Junior Dev Challenge 2026**

SimpleSQLDB is a fully functional relational database management system (RDBMS) built from scratch in Python. It features SQL query support, B-tree indexing, JOIN operations, and a web-based demo application showcasing CRUD operations.

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

### Installation

1. **Clone or download this repository**
   ```powershell
   cd "c:\Users\E.Samwel\Desktop\RDMS"
   ```

2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

### Running the REPL

Start the interactive SQL REPL:

```powershell
python repl/cli.py
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

1 row(s) returned

sql> .exit
```

### Running the Web Application

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

2. **B-tree Max Keys**: Set to 4 for demonstration purposes. Production systems typically use higher values (100+).

3. **No Transaction Log**: Current implementation doesn't support crash recovery. Could be added with write-ahead logging.

4. **In-Memory Caching**: All data loaded into memory on startup for performance. Larger datasets would require pagination.

5. **Simple JOIN Algorithm**: Nested loop joins are easy to understand. Hash joins would be more efficient for large datasets.

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
- **JSON**: Data persistence format
- **HTML/CSS**: Frontend interface

## 📝 Acknowledgments

This project was built from scratch for the Pesapal Junior Dev Challenge 2026. All core components (parser, storage engine, indexing, query execution) were implemented without external database libraries.

## 👨‍💻 Author

E. Samwel

## 📄 License

This project is open source and available for educational purposes.

---

**Note**: This is a demonstration project built for a coding challenge. While it implements core RDBMS concepts, it's not intended for production use. For production databases, consider established systems like PostgreSQL, MySQL, or SQLite.
