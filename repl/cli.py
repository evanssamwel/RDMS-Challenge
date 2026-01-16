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
import os
from typing import Optional
from core.engine import QueryEngine
from core.storage import Storage
from core.database_manager import DatabaseManager


class REPL:
    """Interactive SQL REPL"""
    
    def __init__(self, data_dir: str = "databases"):
        # If a directory looks like a single database (contains *.schema.json),
        # keep legacy behavior. Otherwise treat it as a multi-db base directory.
        use_legacy = False
        try:
            path = os.path.abspath(data_dir)
            if os.path.isdir(path):
                schema_files = [f for f in os.listdir(path) if f.endswith('.schema.json')]
                use_legacy = len(schema_files) > 0
        except Exception:
            use_legacy = False

        if use_legacy:
            self.storage = Storage(data_dir)
            self.engine = QueryEngine(self.storage)
        else:
            manager = DatabaseManager(base_dir=data_dir)
            # Back-compat: expose any existing single-db folders.
            manager.register_database('school_erp', os.path.join('databases', 'school_erp'))
            if os.path.isdir('studio_data'):
                manager.register_database('studio', 'studio_data')
            # Ensure a default database exists for the REPL.
            manager.create_database('default')
            self.storage = manager.open_storage('default')
            self.engine = QueryEngine(self.storage, database_manager=manager, default_database='default')
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
        print("Multi-database SQL:")
        print("  SHOW DATABASES;  USE <db>;  CREATE DATABASE <db>;  SHOW TABLES;")
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
        """Explain a query by printing the engine's structured plan."""
        try:
            plan = self.engine.explain(sql)
            print()
            self._print_plan_tree(plan)
            print()
        except Exception as e:
            print(f"Error generating explain plan: {e}")

    def _print_plan_tree(self, node: dict, prefix: str = "", is_last: bool = True):
        """Pretty-print a plan tree returned by QueryEngine.explain()."""
        if not node:
            return

        connector = "└─ " if is_last else "├─ "
        node_type = node.get('type', 'UNKNOWN')
        details = node.get('details')
        label = node_type
        if details:
            label = f"{node_type} {details}"
        print(prefix + connector + label)

        children = node.get('children') or []
        next_prefix = prefix + ("   " if is_last else "│  ")
        for i, child in enumerate(children):
            self._print_plan_tree(child, next_prefix, i == len(children) - 1)



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
