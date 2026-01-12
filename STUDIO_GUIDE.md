# SimpleSQLDB Studio - Getting Started Guide

A professional Database Management Studio demonstrating a fully-functional RDBMS engine with CRUD operations, advanced queries, and SQL execution insights.

## 🚀 Quick Start (30 seconds)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
cd web_demo
python app_studio.py
```

### 3. Open in Browser
```
http://127.0.0.1:5000
```

That's it! The database will auto-seed with sample data.

---

## 📱 Using the Studio

### **Tab 1: CRUD Manager** (Educational Database)

Practice full CRUD operations with students, courses, and enrollments:

#### Students
```
1. Click "Students" in sidebar
2. See list of enrolled students
3. Click "Add Student" to create new record
4. Click trash icon to delete
```

**What it demonstrates:**
- CREATE (INSERT), READ (SELECT), DELETE
- Data validation
- Referential integrity

#### Courses
```
1. Click "Courses" to see available courses
2. View course codes and credits
3. Add new courses with "Add Course" button
```

**What it demonstrates:**
- UNIQUE constraints (course_code can't duplicate)
- Structured data management

#### Enrollments
```
1. Click "Enrollments" to see all student-course pairs
2. Shows joined data: Student Name + Course Name + Grade
3. Color-coded grades (A=green, B=yellow)
```

**What it demonstrates:**
- INNER JOIN (students ⟷ enrollments ⟷ courses)
- Foreign Key relationships
- Data from multiple tables in single view

---

### **Tab 2: Analytics** (Kenyan HR Data)

See your RDBMS handling real-world business analytics:

#### Dashboard Cards
```
Shows salary statistics by department:
- Average salary
- Employee count
- Min/max salary ranges
```

**What it demonstrates:**
- GROUP BY department
- Aggregate functions (AVG, COUNT, MIN, MAX)
- Business intelligence queries

#### Employee Table
```
Shows all employees with:
- Name, Position, Department, Location
- Salary in KES (Kenyan Shillings)
- Uses INNER JOIN to get department names
```

**What it demonstrates:**
- Multi-table JOINs
- Real-world business data
- Formatted numeric output

---

### **Tab 3: SQL Terminal** (Power User Mode)

Execute raw SQL and see how your engine works:

#### Query Editor
```
Write any SQL:
SELECT * FROM students;
SELECT dept_name, AVG(salary) FROM employees 
GROUP BY dept_id;
```

**Supported Commands:**
- ✅ SELECT with WHERE, GROUP BY, HAVING, LIMIT, ORDER BY
- ✅ INSERT, UPDATE, DELETE
- ✅ CREATE TABLE with constraints
- ✅ CREATE INDEX
- ✅ JOINs (INNER, LEFT)
- ✅ Aggregates (COUNT, SUM, AVG, MAX, MIN)

#### Results Tab
```
Click "Execute" to run query
Results displayed in clean table format
Shows number of rows returned
```

#### Explain Tab
```
Click "Explain Plan" to see:
- Query optimization strategy
- Whether indexes are used
- Join methods (NESTED LOOP, INDEX SEEK, etc.)
- Estimated cost and rows scanned

Visual terminal-style output makes it clear!
```

---

## 🎯 Demo Queries to Try

### 1. **Basic SELECT**
```sql
SELECT * FROM students;
```
Shows all students with their details.

### 2. **GROUP BY with Aggregates**
```sql
SELECT dept_name, COUNT(*) as emp_count, AVG(salary) as avg_sal 
FROM employees e 
JOIN departments d ON e.dept_id = d.dept_id 
GROUP BY d.dept_id;
```
Salary analytics by department. Try this to see your engine's GROUP BY/HAVING power!

### 3. **Simple JOIN**
```sql
SELECT s.first_name, s.last_name, c.course_name 
FROM enrollments e 
JOIN students s ON e.student_id = s.student_id 
JOIN courses c ON e.course_id = c.course_id;
```
Shows student-course relationships using INNER JOINs.

### 4. **Filter with WHERE**
```sql
SELECT * FROM employees 
WHERE salary > 100000 
ORDER BY salary DESC;
```
Find high earners, ordered by salary.

### 5. **CREATE and INSERT** (make your own table!)
```sql
CREATE TABLE projects (
    project_id INT PRIMARY KEY,
    project_name VARCHAR(100),
    budget INT,
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO projects (project_id, project_name, budget, dept_id) 
VALUES (1, 'Mobile App', 500000, 1);
```
Create new tables and insert data on the fly!

---

## 🔍 Understanding Execution Plans

When you click "Explain Plan", you'll see something like:

```
═══════════════════════════════════════════
  QUERY EXECUTION PLAN
═══════════════════════════════════════════
▸ QUERY_TYPE: SELECT
▸ ACCESS_METHOD: Index Seek
  ├─ index_used: "idx_emp_salary"
  ├─ rows_scanned: 15
  ├─ estimated_cost: 0.42
▸ JOINS:
  ├─ type: INNER
  ├─ on_table: employees
  ├─ using_index: TRUE
▸ AGGREGATES:
  ├─ function: COUNT
  ├─ column: emp_id
═══════════════════════════════════════════
```

**Color meanings:**
- 🔵 Blue = Metadata (query type, methods)
- 🟢 Green = Actual values (index names, row counts)
- 🟡 Yellow = Keys (section labels)

**What to look for:**
- ✅ `using_index: TRUE` = Fast! Query uses B-tree index
- ✅ `access_method: Index Seek` = Efficient (not table scan)
- ⚠️ `access_method: Table Scan` = Could be slower for large tables

---

## 🏗️ Architecture

### Three Integrated Modules:

1. **CRUD Module** - Shows relational database fundamentals
   - Tables: students, courses, enrollments
   - Demonstrates: INSERT, SELECT, DELETE, FOREIGN KEYS

2. **Analytics Module** - Shows real-world business use
   - Tables: employees, departments
   - Demonstrates: GROUP BY, aggregates, complex JOINs

3. **SQL Terminal** - Shows engine internals
   - Execute any SQL
   - Explore execution strategies
   - Test all RDBMS features

### Why One App Instead of Three?
- **Cleaner**: Reviewers see one `python app_studio.py` command
- **Versatile**: Proves engine handles different schemas
- **Professional**: Like pgAdmin or MySQL Workbench
- **Educational**: Single place to learn RDBMS concepts

---

## 📊 Data Dictionary

### Educational Tables
```
students
├── student_id (INT) - Primary Key
├── first_name (VARCHAR)
├── last_name (VARCHAR)
├── email (VARCHAR) - UNIQUE
├── phone (VARCHAR)
└── enrollment_date (DATE)

courses
├── course_id (INT) - Primary Key
├── course_name (VARCHAR)
├── course_code (VARCHAR) - UNIQUE
├── credits (INT)
└── instructor (VARCHAR)

enrollments
├── enrollment_id (INT) - Primary Key
├── student_id (INT) - Foreign Key
├── course_id (INT) - Foreign Key
├── grade (VARCHAR)
└── enrollment_date (DATE)
```

### Analytics Tables
```
employees
├── emp_id (INT) - Primary Key
├── name (VARCHAR)
├── email (VARCHAR) - UNIQUE
├── position (VARCHAR)
├── salary (INT)
└── dept_id (INT) - Foreign Key

departments
├── dept_id (INT) - Primary Key
├── dept_name (VARCHAR) - UNIQUE
├── location (VARCHAR)
└── budget (INT)
```

---

## 🛠️ Troubleshooting

### "Port 5000 already in use"
```bash
# Kill the existing process
taskkill /PID <PID> /F

# Or use a different port:
python app_studio.py --port 5001
```

### "Database not initializing"
```bash
# Clear old data and restart
rm -r studio_data
python app_studio.py
```

### "Tables are empty"
The app auto-seeds data on first run. If empty:
```bash
# Restart the app
# It should initialize demo data automatically
```

---

## 📚 Learn More

- **README.md** - Full feature list and SQL examples
- **ADVANCED_FEATURES.md** - Detailed explanation of GROUP BY, HAVING, .explain
- **FINISHING_TOUCHES.md** - Atomic writes, system tables, production features
- **SUBMISSION_SUMMARY.md** - What makes this submission special

---

## 🎓 Key Learning Points

By exploring this studio, you'll understand:

1. **How SQL parsers work** - See tokenization and syntax analysis
2. **Query execution** - Watch JOIN and GROUP BY in action
3. **Database indexes** - See B-tree optimization in explain plans
4. **CRUD operations** - Create, read, update, delete in real time
5. **Data integrity** - Foreign keys and constraints prevent bad data
6. **Web apps** - Connect database to browser interface

---

## 🚀 Next Steps

1. **Explore CRUD Manager** - Add/delete students, understand INSERT/DELETE
2. **Check Analytics** - See GROUP BY aggregates in action
3. **Run Explain Queries** - Click "Explain Plan" to understand optimization
4. **Write Custom SQL** - Use Terminal to test your own queries
5. **Read Documentation** - Deep dive into how it works

---

## ✨ Cool Features to Try

- ✅ Multi-table JOINs (students → enrollments → courses)
- ✅ GROUP BY with aggregates (salary by department)
- ✅ Execution plans showing index usage
- ✅ Real-world Kenyan employee data
- ✅ Create your own tables on the fly
- ✅ Atomic writes (crash-safe persistence)
- ✅ Foreign key constraints (referential integrity)

---

**Built with ❤️ for Pesapal Junior Dev Challenge 2026**

**Enjoy exploring your RDBMS!** 🚀
