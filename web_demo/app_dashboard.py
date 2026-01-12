"""
Flask Web Application - Database Management Studio
Professional dashboard interface for SimpleSQLDB
"""
from flask import Flask, render_template, request, jsonify
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import QueryEngine
from core.storage import Storage

app = Flask(__name__)
app.secret_key = 'simplesqldb-2026-secret'

# Initialize database
storage = Storage(data_dir='web_data')
engine = QueryEngine(storage)


@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('dashboard.html')

# Initialize demo data
def init_demo_data():
    """Initialize demo database with sample data"""
    tables = storage.list_tables()
    
    if not tables:
        # Create demo tables
        engine.execute("""
            CREATE TABLE departments (
                id INT PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                budget FLOAT
            )
        """)
        
        engine.execute("""
            CREATE TABLE employees (
                id INT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                dept_id INT REFERENCES departments(id),
                salary FLOAT,
                hire_date DATE
            )
        """)
        
        # Insert sample data
        engine.execute("INSERT INTO departments VALUES (1, 'Engineering', 500000.0)")
        engine.execute("INSERT INTO departments VALUES (2, 'Sales', 300000.0)")
        engine.execute("INSERT INTO departments VALUES (3, 'Marketing', 250000.0)")
        
        engine.execute("INSERT INTO employees VALUES (1, 'Alice Johnson', 'alice@company.com', 1, 95000.0, '2020-01-15')")
        engine.execute("INSERT INTO employees VALUES (2, 'Bob Smith', 'bob@company.com', 1, 85000.0, '2021-03-20')")
        engine.execute("INSERT INTO employees VALUES (3, 'Carol White', 'carol@company.com', 2, 70000.0, '2020-05-01')")
        engine.execute("INSERT INTO employees VALUES (4, 'David Brown', 'david@company.com', 2, 65000.0, '2021-08-15')")
        engine.execute("INSERT INTO employees VALUES (5, 'Eve Davis', 'eve@company.com', 3, 55000.0, '2021-11-10')")

init_demo_data()

@app.route('/')
def dashboard():
    """Main dashboard view"""
    return render_template('dashboard.html')

@app.route('/api/tables')
def api_tables():
    """Get list of all tables with metadata"""
    tables_info = storage.get_system_tables_info()
    return jsonify(tables_info)

@app.route('/api/table/<table_name>')
def api_table_data(table_name):
    """Get data from a specific table"""
    try:
        result = engine.execute(f"SELECT * FROM {table_name}")
        if result['success']:
            return jsonify({
                'success': True,
                'data': result.get('rows', []),
                'count': result.get('count', 0)
            })
        return jsonify({'success': False, 'error': result.get('error', 'Unknown error')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/schema/<table_name>')
def api_table_schema(table_name):
    """Get schema for a specific table"""
    table = storage.get_table(table_name)
    if table:
        columns = [{
            'name': col.name,
            'type': col.data_type.value,
            'length': col.length,
            'primary_key': col.primary_key,
            'unique': col.unique,
            'not_null': col.not_null,
            'foreign_key': col.foreign_key
        } for col in table.columns]
        return jsonify({
            'success': True,
            'table_name': table.name,
            'columns': columns,
            'primary_key': table.primary_key
        })
    return jsonify({'success': False, 'error': f'Table {table_name} not found'})

@app.route('/api/indexes')
def api_indexes():
    """Get all indexes"""
    indexes_info = storage.get_system_indexes_info()
    return jsonify(indexes_info)

@app.route('/api/execute', methods=['POST'])
def api_execute():
    """Execute SQL query"""
    data = request.get_json()
    sql = data.get('sql', '').strip()
    
    if not sql:
        return jsonify({'success': False, 'error': 'No SQL provided'})
    
    try:
        result = engine.execute(sql)
        
        # Format response
        response = {
            'success': result['success'],
            'sql': sql
        }
        
        if result['success']:
            if 'rows' in result:
                response['rows'] = result['rows']
                response['count'] = result['count']
                response['type'] = 'SELECT'
            else:
                response['message'] = result.get('message', 'Query executed successfully')
                response['type'] = 'DDL/DML'
        else:
            response['error'] = result.get('error', 'Unknown error')
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/explain', methods=['POST'])
def api_explain():
    """Get query execution plan"""
    data = request.get_json()
    sql = data.get('sql', '').strip()
    
    if not sql:
        return jsonify({'success': False, 'error': 'No SQL provided'})
    
    try:
        from core.parser import SQLParser
        parser = SQLParser()
        parsed = parser.parse(sql)
        
        # Build execution plan
        plan = {
            'query_type': parsed['type'].name,
            'table': parsed.get('table'),
            'access_method': 'Full Table Scan',
            'index_used': None,
            'joins': [],
            'aggregates': [],
            'grouping': None,
            'filtering': None
        }
        
        # Check for index usage
        if parsed.get('where') and parsed['where'].get('column'):
            where_col = parsed['where']['column']
            table_name = parsed.get('table')
            if table_name and where_col in storage.indexes.get(table_name, {}):
                plan['access_method'] = 'Index Scan'
                plan['index_used'] = f"{where_col}_idx"
        
        # Add JOIN info
        if parsed.get('joins'):
            for join in parsed['joins']:
                plan['joins'].append({
                    'type': join['type'].name,
                    'table': join['table'],
                    'condition': f"{join['on']['left_col']} = {join['on']['right_col']}"
                })
        
        # Add aggregate info
        if parsed.get('aggregates'):
            for agg in parsed['aggregates']:
                plan['aggregates'].append({
                    'function': agg['function'],
                    'column': agg['column'] or '*',
                    'alias': agg['alias']
                })
        
        # Add GROUP BY info
        if parsed.get('group_by'):
            plan['grouping'] = {
                'columns': parsed['group_by'],
                'having': parsed.get('having')
            }
        
        # Add WHERE info
        if parsed.get('where'):
            plan['filtering'] = parsed['where']
        
        return jsonify({'success': True, 'plan': plan})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/schema-graph')
def api_schema_graph():
    """Get schema relationships for ERD visualization"""
    tables_info = storage.get_system_tables_info()
    relationships = []
    
    # Find all foreign key relationships
    for table_name in storage.list_tables():
        table = storage.get_table(table_name)
        if table:
            for col in table.columns:
                if col.foreign_key:
                    ref_table, ref_col = col.foreign_key
                    relationships.append({
                        'from_table': table_name,
                        'from_column': col.name,
                        'to_table': ref_table,
                        'to_column': ref_col
                    })
    
    # Build tables structure
    tables = []
    for table_name in storage.list_tables():
        table = storage.get_table(table_name)
        if table:
            tables.append({
                'name': table_name,
                'columns': [{
                    'name': col.name,
                    'type': col.data_type.value,
                    'primary_key': col.primary_key,
                    'foreign_key': col.foreign_key is not None
                } for col in table.columns]
            })
    
    return jsonify({
        'tables': tables,
        'relationships': relationships
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
