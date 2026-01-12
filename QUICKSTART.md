# Quick Start Guide

## Installation

1. Install Flask:
```powershell
pip install Flask
```

## Running the REPL (SQL Command Line)

```powershell
python repl/cli.py
```

Try these commands:
```sql
sql> CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(100), age INT);
sql> INSERT INTO students VALUES (1, 'Alice', 20);
sql> SELECT * FROM students;
sql> .exit
```

## Running the Web App

```powershell
python web_demo/app.py
```

Then open: http://localhost:5000

## Running Tests

```powershell
pip install pytest
python -m pytest tests/ -v
```

## What to Showcase

1. **SQL Parser** - Parses complex SQL including JOINs
2. **B-tree Indexing** - Fast lookups on primary/unique keys
3. **Storage Engine** - Data persisted to disk as JSON
4. **Query Engine** - Executes SELECT, INSERT, UPDATE, DELETE
5. **JOIN Support** - INNER and LEFT joins
6. **Web Demo** - Full CRUD application with:
   - Student management
   - Course management  
   - Enrollments (demonstrates JOINs)
   - SQL Console for raw queries

## Key Files to Review

- `core/parser.py` - SQL parsing logic
- `core/index.py` - B-tree implementation
- `core/storage.py` - Data persistence
- `core/engine.py` - Query execution
- `web_demo/app.py` - Demo application
- `tests/test_database.py` - Test suite

## Features Implemented

✅ SQL statements (CREATE TABLE, INSERT, SELECT, UPDATE, DELETE)
✅ Data types (INT, VARCHAR, FLOAT, DATE, BOOLEAN)
✅ Constraints (PRIMARY KEY, UNIQUE, NOT NULL)
✅ B-tree indexing
✅ INNER JOIN & LEFT JOIN
✅ WHERE clauses with multiple operators
✅ ORDER BY & LIMIT
✅ Data persistence
✅ Interactive REPL
✅ Web demo with CRUD operations
✅ Comprehensive tests

Good luck with the submission! 🚀
