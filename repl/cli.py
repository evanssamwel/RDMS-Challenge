"""
Interactive SQL REPL - Read-Eval-Print Loop

This module provides a command-line interface for interactive SQL:
    
    Features:
    - Multi-line SQL statement support (complete with ;)
    - Special commands (.tables, .schema, .exit)
    - Error handling and recovery
    - Result formatting as tables
    - Command history and editing (via readline)
    
    REPL Modes:
    - Normal mode: Waiting for new statement
    - Continuation mode: Waiting for statement completion (ends with ;)
    
    Special Commands:
    - .tables       List all tables in database
    - .schema <T>   Show schema for table T
    - .exit / .quit Exit the REPL
    - .help         Show available commands
    
    Input Processing:
    1. Read line from user
    2. Check for special command (starts with .)
    3. If normal SQL: add to buffer
    4. When ends with ;: execute buffered statement
    5. Display results or errors
    6. Clear buffer and continue
    
    Example Session:
        sql> CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        Table users created successfully
        
        sql> INSERT INTO users VALUES (1, 'Alice');
        Row inserted with ID 0
        
        sql> SELECT * FROM users;
        id | name
        ---+-------
        1  | Alice
        
        sql> .tables
        Tables:
          - users
        
        sql> .exit
        Goodbye!
"""
import sys
from typing import Optional
from core.engine import QueryEngine
from core.storage import Storage


class REPL:
    """Interactive SQL REPL"""
    
    def __init__(self, data_dir: str = "data"):
        self.storage = Storage(data_dir)
        self.engine = QueryEngine(self.storage)
        self.running = False
    
    def start(self):
        """Start the REPL"""
        self.running = True
        
        print("=" * 60)
        print("Welcome to SimpleSQLDB - A Simple Relational Database")
        print("=" * 60)
        print("Type your SQL commands. End with semicolon (;)")
        print("Special commands:")
        print("  .tables  - List all tables")
        print("  .schema <table> - Show table schema")
        print("  .explain <query> - Show query execution plan")
        print("  .sys_tables - Show system metadata for all tables")
        print("  .sys_indexes - Show all indexes")
        print("  .exit or .quit - Exit the REPL")
        print("=" * 60)
        print()
        
        buffer = []
        
        while self.running:
            try:
                if buffer:
                    prompt = "... "
                else:
                    prompt = "sql> "
                
                line = input(prompt)
                
                # Handle special commands
                if line.startswith('.'):
                    self._handle_special_command(line)
                    continue
                
                # Add line to buffer
                buffer.append(line)
                
                # Check if statement is complete
                full_statement = ' '.join(buffer)
                if full_statement.strip().endswith(';'):
                    # Execute statement
                    self._execute_statement(full_statement)
                    buffer = []
            
            except KeyboardInterrupt:
                print("\nUse .exit or .quit to exit")
                buffer = []
            except EOFError:
                print("\nGoodbye!")
                break
    
    def _handle_special_command(self, command: str):
        """Handle special REPL commands"""
        parts = command.strip().split()
        cmd = parts[0].lower()
        
        if cmd in ['.exit', '.quit']:
            print("Goodbye!")
            self.running = False
        
        elif cmd == '.tables':
            tables = self.storage.list_tables()
            if tables:
                print("\nTables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("\nNo tables found")
            print()
        
        elif cmd == '.schema':
            if len(parts) < 2:
                print("Usage: .schema <table_name>")
                return
            
            table_name = parts[1]
            table = self.storage.get_table(table_name)
            
            if table:
                print(f"\n{table}")
                print()
            else:
                print(f"\nTable {table_name} does not exist\n")
        
        elif cmd == '.explain':
            # Extract SQL from command (everything after .explain)
            sql = command[8:].strip()
            if not sql:
                print("Usage: .explain <SQL query>")
                return
            self._explain_query(sql)
        
        elif cmd == '.sys_tables':
            tables_info = self.storage.get_system_tables_info()
            if tables_info:
                print("\nSystem Tables Metadata:")
                print("-" * 80)
                for info in tables_info:
                    print(f"Table: {info['table_name']}")
                    print(f"  Columns: {info['column_count']}")
                    print(f"  Rows: {info['row_count']}")
                    print(f"  Primary Key: {info['primary_key'] or 'None'}")
                    print(f"  Created: {info['created_at']}")
                    print()
            else:
                print("\nNo tables found\n")
        
        elif cmd == '.sys_indexes':
            indexes_info = self.storage.get_system_indexes_info()
            if indexes_info:
                print("\nSystem Indexes Metadata:")
                print("-" * 80)
                for info in indexes_info:
                    unique_str = " (UNIQUE)" if info['is_unique'] else ""
                    print(f"{info['table_name']}.{info['column_name']}: {info['index_type']}{unique_str}")
                print()
            else:
                print("\nNo indexes found\n")
        
        else:
            print(f"Unknown command: {cmd}")
    
    def _execute_statement(self, sql: str):
        """Execute a SQL statement"""
        sql = sql.strip()
        
        if not sql or sql == ';':
            return
        
        print()
        result = self.engine.execute(sql)
        
        if result['success']:
            if 'rows' in result:
                # SELECT query
                self._print_result_table(result['rows'])
                print(f"\n{result['count']} row(s) returned")
            else:
                # Other queries
                print(result['message'])
        else:
            print(f"Error: {result['error']}")
        
        print()
    
    def _print_result_table(self, rows: list):
        """Print query results in a table format"""
        if not rows:
            print("(empty result set)")
            return
        
        # Get all column names
        columns = list(rows[0].keys())
        
        # Calculate column widths
        widths = {col: len(col) for col in columns}
        for row in rows:
            for col in columns:
                value_str = str(row.get(col, ''))
                widths[col] = max(widths[col], len(value_str))
        
        # Print header
        header = ' | '.join(col.ljust(widths[col]) for col in columns)
        print(header)
        print('-' * len(header))
        
        # Print rows
        for row in rows:
            row_str = ' | '.join(str(row.get(col, '')).ljust(widths[col]) for col in columns)
            print(row_str)
    
    def _explain_query(self, sql: str):
        """
        Show query execution plan for SELECT statements.
        
        Displays:
        - Query type (SELECT, JOIN, aggregate)
        - Table access method (full scan vs index lookup)
        - Index usage for WHERE clauses
        - JOIN type and strategy
        - Aggregation and grouping details
        """
        print("\n--- Query Execution Plan ---\n")
        
        from core.parser import SQLParser
        parser = SQLParser()
        
        try:
            parsed = parser.parse(sql)
            
            if parsed['type'].name != 'SELECT':
                print(f"EXPLAIN only supports SELECT queries (got {parsed['type'].name})")
                return
            
            table_name = parsed['table']
            table = self.storage.get_table(table_name)
            
            if not table:
                print(f"Table {table_name} does not exist")
                return
            
            # Query type
            if parsed['joins']:
                print(f"Query Type: SELECT with JOIN")
            elif parsed['aggregates'] or parsed['group_by']:
                print(f"Query Type: SELECT with Aggregation")
            else:
                print(f"Query Type: Simple SELECT")
            
            # Main table access
            print(f"\nTable: {table_name}")
            
            # Check for index usage in WHERE clause
            if parsed['where']:
                where_col = parsed['where'].get('column')
                if where_col:
                    # Check if column has an index
                    if where_col in self.storage.indexes.get(table_name, {}):
                        print(f"  Access Method: Index Scan on {where_col}")
                        print(f"  Index: {where_col}_idx")
                    else:
                        print(f"  Access Method: Full Table Scan")
                        print(f"  Filter: {where_col} {parsed['where']['operator']} {parsed['where']['value']}")
            else:
                print(f"  Access Method: Full Table Scan")
            
            # JOIN details
            if parsed['joins']:
                print(f"\nJOINs:")
                for join in parsed['joins']:
                    print(f"  - {join['type'].name}: {join['table']}")
                    print(f"    Condition: {join['on']['left_col']} = {join['on']['right_col']}")
                    
                    # Check if join column is indexed
                    join_table = self.storage.get_table(join['table'])
                    if join_table:
                        right_col = join['on']['right_col'].split('.')[-1]
                        if right_col in self.storage.indexes.get(join['table'], {}):
                            print(f"    Strategy: Index Nested Loop (indexed on {right_col})")
                        else:
                            print(f"    Strategy: Nested Loop (no index)")
            
            # Aggregate details
            if parsed['aggregates']:
                print(f"\nAggregation:")
                for agg in parsed['aggregates']:
                    col_str = agg['column'] if agg['column'] else '*'
                    print(f"  - {agg['function']}({col_str}) AS {agg['alias']}")
            
            if parsed['group_by']:
                print(f"\nGrouping:")
                print(f"  GROUP BY: {', '.join(parsed['group_by'])}")
                
                if parsed['having']:
                    having = parsed['having']
                    print(f"  HAVING: {having['column']} {having['operator']} {having['value']}")
            
            # Output details
            if parsed['columns'] != ['*']:
                print(f"\nColumns: {', '.join(parsed['columns'])}")
            else:
                print(f"\nColumns: * (all)")
            
            if parsed['order_by']:
                order_cols = [f"{col} {direction}" for col, direction in parsed['order_by']]
                print(f"Order By: {', '.join(order_cols)}")
            
            if parsed['limit']:
                print(f"Limit: {parsed['limit']}")
            
            print()
            
        except Exception as e:
            print(f"Error parsing query: {e}")
            print()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SimpleSQLDB - Interactive SQL REPL')
    parser.add_argument('--data-dir', default='data', help='Data directory (default: data)')
    args = parser.parse_args()
    
    repl = REPL(data_dir=args.data_dir)
    repl.start()


if __name__ == '__main__':
    main()
