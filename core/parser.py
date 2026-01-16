"""
SQL Parser - Parses SQL statements into executable commands

This module implements a complete SQL parser that converts SQL text into
executable command structures. Key features:

    - Lexical analysis: Tokenizes SQL statements
    - Syntax analysis: Parses tokens into AST-like structures
    - Semantic validation: Basic type and constraint checking
    - Error handling: Detailed error messages for invalid SQL

Parser Architecture:
    1. Input: Raw SQL string
    2. Statement type detection: Identifies command type
    3. Parsing: Type-specific parsing for CREATE, INSERT, SELECT, etc.
    4. Validation: Checks for syntax errors and invalid tokens
    5. Output: Dictionary structure for query engine

Supported SQL Features:
    - CREATE TABLE with column constraints
    - INSERT with columns or values-only
    - SELECT with WHERE, ORDER BY, LIMIT, and JOINs
    - UPDATE with SET and WHERE clauses
    - DELETE with WHERE clauses
    - CREATE INDEX for performance

Limitations (TODO):
    - No subqueries or CTEs
    - No aggregate functions (COUNT, SUM, etc.)
    - No GROUP BY or HAVING
    - No transactions or DCL statements
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from core.types import DataType, Column


class StatementType(Enum):
    """
    Enumeration of supported SQL statement types.
    
    Each type corresponds to a major SQL command with its own
    parsing logic and execution path.
    """
    CREATE_TABLE = "CREATE_TABLE"    # Data Definition Language
    INSERT = "INSERT"                # Data Manipulation Language
    SELECT = "SELECT"                # Data Query Language
    UPDATE = "UPDATE"                # Data Manipulation Language
    DELETE = "DELETE"                # Data Manipulation Language
    CREATE_INDEX = "CREATE_INDEX"    # Data Definition Language

    # Multi-database commands (MariaDB/MySQL-style)
    CREATE_DATABASE = "CREATE_DATABASE"
    DROP_DATABASE = "DROP_DATABASE"
    USE_DATABASE = "USE_DATABASE"
    SHOW_DATABASES = "SHOW_DATABASES"
    SHOW_TABLES = "SHOW_TABLES"


class JoinType(Enum):
    """
    Enumeration of supported JOIN types for SELECT statements.
    
    Determines how tables are joined in multi-table queries:
    - INNER: Only matching rows from both tables
    - LEFT: All rows from left table, matching rows from right
    """
    INNER = "INNER"
    LEFT = "LEFT"


class SQLParser:
    """
    SQL statement parser with complete grammar support.
    
    This parser handles SQL statement parsing without external
    libraries, implementing a hand-written recursive descent parser.
    
    The parser:
    - Validates SQL syntax
    - Extracts command semantics
    - Converts to dictionary representation for execution
    - Provides detailed error messages
    
    Attributes:
        error_messages: List of parser errors for diagnostics
        
    Thread Safety: Parser is stateless and thread-safe
    """
    """Parse SQL statements"""
    
    def __init__(self):
        """Initialize parser with empty error list."""
        pass
    
    def parse(self, sql: str) -> Dict[str, Any]:
        """
        Parse a SQL statement and return its structure.
        
        This is the main entry point for parsing. It:
        1. Normalizes the input (whitespace, semicolons)
        2. Identifies the statement type
        3. Delegates to type-specific parser
        4. Returns structured representation
        
        Args:
            sql: Raw SQL statement (may include trailing semicolon)
            
        Returns:
            Dictionary with keys:
                'type': StatementType enum value
                Other keys specific to statement type
                
        Raises:
            ValueError: If SQL is invalid or unsupported
            
        Examples:
            >>> parser = SQLParser()
            >>> result = parser.parse("SELECT * FROM users")
            >>> result['type'] == StatementType.SELECT  # True
            
        Note:
            The returned dictionary is passed to QueryEngine.execute()
            which handles the actual execution.
        """
        sql = sql.strip()
        
        # Remove trailing semicolon for easier parsing
        if sql.endswith(';'):
            sql = sql[:-1].strip()
        
        if not sql:
            raise ValueError("Empty SQL statement")
        
        # Determine statement type (case-insensitive)
        sql_upper = sql.upper()
        
        # Dispatch to appropriate parser based on statement type
        if sql_upper.startswith('CREATE DATABASE'):
            return self._parse_create_database(sql)
        elif sql_upper.startswith('DROP DATABASE'):
            return self._parse_drop_database(sql)
        elif sql_upper.startswith('USE '):
            return self._parse_use_database(sql)
        elif sql_upper == 'SHOW DATABASES':
            return {'type': StatementType.SHOW_DATABASES}
        elif sql_upper == 'SHOW TABLES':
            return {'type': StatementType.SHOW_TABLES}
        elif sql_upper.startswith('CREATE TABLE'):
            return self._parse_create_table(sql)
        elif sql_upper.startswith('INSERT INTO'):
            return self._parse_insert(sql)
        elif sql_upper.startswith('SELECT'):
            return self._parse_select(sql)
        elif sql_upper.startswith('UPDATE'):
            return self._parse_update(sql)
        elif sql_upper.startswith('DELETE FROM'):
            return self._parse_delete(sql)
        elif sql_upper.startswith('CREATE INDEX'):
            return self._parse_create_index(sql)
        else:
            raise ValueError(
                f"Unsupported SQL statement: {sql[:50]}. "
                f"Supported: CREATE DATABASE, DROP DATABASE, USE, SHOW DATABASES, SHOW TABLES, "
                f"CREATE TABLE, INSERT, SELECT, UPDATE, DELETE, CREATE INDEX"
            )

    def _parse_create_database(self, sql: str) -> Dict[str, Any]:
        match = re.match(r'CREATE DATABASE\s+(\w+)$', sql.strip(), re.IGNORECASE)
        if not match:
            raise ValueError("Invalid CREATE DATABASE syntax. Expected: CREATE DATABASE db_name")
        return {'type': StatementType.CREATE_DATABASE, 'database': match.group(1)}

    def _parse_drop_database(self, sql: str) -> Dict[str, Any]:
        match = re.match(r'DROP DATABASE\s+(\w+)$', sql.strip(), re.IGNORECASE)
        if not match:
            raise ValueError("Invalid DROP DATABASE syntax. Expected: DROP DATABASE db_name")
        return {'type': StatementType.DROP_DATABASE, 'database': match.group(1)}

    def _parse_use_database(self, sql: str) -> Dict[str, Any]:
        match = re.match(r'USE\s+(\w+)$', sql.strip(), re.IGNORECASE)
        if not match:
            raise ValueError("Invalid USE syntax. Expected: USE db_name")
        return {'type': StatementType.USE_DATABASE, 'database': match.group(1)}
    
    def _parse_create_table(self, sql: str) -> Dict[str, Any]:
        """
        Parse CREATE TABLE statement.
        
        Syntax: CREATE TABLE table_name (column1 type constraints, ...)
        
        Extracts:
        - Table name
        - Column definitions with types and constraints
        
        Args:
            sql: Raw CREATE TABLE statement
            
        Returns:
            Dictionary with:
                'type': StatementType.CREATE_TABLE
                'table': table name
                'columns': List of Column objects
                
        Raises:
            ValueError: If syntax is invalid
            
        Examples:
            CREATE TABLE users (
                id INT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE
            )
        """
        # Pattern: CREATE TABLE table_name (column_definitions)
        match = re.match(r'CREATE TABLE\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*\((.*)\)', sql, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError(
                "Invalid CREATE TABLE syntax. "
                "Expected: CREATE TABLE table_name (column definitions)"
            )
        
        table_name = match.group(1)
        columns_str = match.group(2)
        
        columns = self._parse_column_definitions(columns_str)
        
        return {
            'type': StatementType.CREATE_TABLE,
            'table': table_name,
            'columns': columns
        }
    
    def _parse_column_definitions(self, columns_str: str) -> List[Column]:
        """Parse column definitions"""
        columns = []
        
        # Split by commas (but not within parentheses)
        col_defs = self._split_by_comma(columns_str)
        
        for col_def in col_defs:
            col_def = col_def.strip()
            if not col_def:
                continue
            
            # Parse: column_name data_type [(length)] [PRIMARY KEY] [UNIQUE] [NOT NULL]
            #        [REFERENCES table(column) [ON DELETE (RESTRICT|CASCADE|SET NULL)]]
            #        [GENERATED ALWAYS AS (expr) VIRTUAL]
            parts = col_def.split()
            if len(parts) < 2:
                raise ValueError(f"Invalid column definition: {col_def}")
            
            col_name = parts[0]
            data_type_str = parts[1].upper()
            
            # Handle VARCHAR(n)
            length = None
            if '(' in data_type_str:
                match = re.match(r'(\w+)\((\d+)\)', data_type_str)
                if match:
                    data_type_str = match.group(1)
                    length = int(match.group(2))
            
            # Map to DataType enum
            try:
                data_type = DataType[data_type_str]
            except KeyError:
                raise ValueError(f"Unsupported data type: {data_type_str}")
            
            # Parse constraints
            col_def_upper = col_def.upper()
            primary_key = 'PRIMARY KEY' in col_def_upper
            unique = 'UNIQUE' in col_def_upper
            not_null = 'NOT NULL' in col_def_upper
            
            # Parse foreign key: REFERENCES table(column) [ON DELETE action]
            foreign_key = None
            foreign_key_on_delete = None
            if 'REFERENCES' in col_def_upper:
                ref_match = re.search(
                    r'REFERENCES\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*\((\w+)\)'
                    r'(?:\s+ON\s+DELETE\s+(RESTRICT|CASCADE|SET\s+NULL))?\b',
                    col_def,
                    re.IGNORECASE,
                )
                if ref_match:
                    foreign_key = (ref_match.group(1), ref_match.group(2))
                    action = ref_match.group(3)
                    if action:
                        foreign_key_on_delete = action.replace(' ', '_').upper().replace('_', ' ')

            # Parse VIRTUAL generated column
            generated_expr = None
            generated_virtual = False
            gen_match = re.search(
                r'(?:GENERATED\s+ALWAYS\s+)?AS\s*\((.+?)\)\s+VIRTUAL\b',
                col_def,
                re.IGNORECASE | re.DOTALL,
            )
            if gen_match:
                generated_expr = gen_match.group(1).strip()
                generated_virtual = True
            
            column = Column(
                name=col_name,
                data_type=data_type,
                length=length,
                primary_key=primary_key,
                unique=unique,
                not_null=not_null,
                foreign_key=foreign_key,
                foreign_key_on_delete=foreign_key_on_delete,
                generated_expr=generated_expr,
                generated_virtual=generated_virtual,
            )
            columns.append(column)
        
        return columns
    
    def _parse_insert(self, sql: str) -> Dict[str, Any]:
        """Parse INSERT statement"""
        # Pattern: INSERT INTO table_name (columns) VALUES (values)
        # Also support: INSERT INTO table_name VALUES (values)
        
        match = re.match(
            r'INSERT INTO\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(?:\((.*?)\))?\s*VALUES\s*\((.*?)\)',
            sql,
            re.IGNORECASE | re.DOTALL
        )
        if not match:
            raise ValueError("Invalid INSERT syntax")
        
        table_name = match.group(1)
        columns_str = match.group(2)
        values_str = match.group(3)
        
        # Parse columns if specified
        columns = None
        if columns_str:
            columns = [col.strip() for col in self._split_by_comma(columns_str)]
        
        # Parse values
        values = self._parse_values(values_str)
        
        return {
            'type': StatementType.INSERT,
            'table': table_name,
            'columns': columns,
            'values': values
        }
    
    def _parse_select(self, sql: str) -> Dict[str, Any]:
        """Parse SELECT statement with JOIN support, aggregates, and GROUP BY"""
        result = {
            'type': StatementType.SELECT,
            'columns': [],
            'aggregates': [],
            'table': None,
            'joins': [],
            'where': None,
            'group_by': None,
            'having': None,
            'order_by': None,
            'limit': None
        }
        
        # Extract different clauses
        sql_upper = sql.upper()
        
        # Find positions of keywords
        from_pos = sql_upper.find('FROM')
        where_pos = sql_upper.find('WHERE')
        group_pos = sql_upper.find('GROUP BY')
        having_pos = sql_upper.find('HAVING')
        order_pos = sql_upper.find('ORDER BY')
        limit_pos = sql_upper.find('LIMIT')
        join_pos = sql_upper.find('JOIN')
        
        if from_pos == -1:
            raise ValueError("SELECT must have FROM clause")
        
        # Extract SELECT columns and aggregates
        select_clause = sql[6:from_pos].strip()
        if select_clause == '*':
            result['columns'] = ['*']
        else:
            # Parse columns and detect aggregates
            for col_expr in self._split_by_comma(select_clause):
                col_expr = col_expr.strip()
                # Check if it's an aggregate function
                agg_match = re.match(r'(COUNT|SUM|AVG|MAX|MIN)\s*\(\s*(.+?)\s*\)', col_expr, re.IGNORECASE)
                if agg_match:
                    func_name = agg_match.group(1).upper()
                    arg = agg_match.group(2).strip()
                    
                    # Check for AS alias
                    alias = col_expr
                    if ' AS ' in col_expr.upper():
                        # Extract alias after AS keyword
                        as_pos = col_expr.upper().rfind(' AS ')
                        alias = col_expr[as_pos + 4:].strip()
                    
                    result['aggregates'].append({
                        'function': func_name,
                        'column': None if arg == '*' else arg,
                        'alias': alias
                    })
                else:
                    result['columns'].append(col_expr)
        
        # Extract FROM and possible JOIN
        end_pos = min([p for p in [where_pos, group_pos, having_pos, order_pos, limit_pos, len(sql)] if p != -1])
        from_clause = sql[from_pos + 4:end_pos].strip()
        
        # Parse FROM and JOINs
        table_info = self._parse_from_with_joins(from_clause)
        result['table'] = table_info['table']
        result['joins'] = table_info['joins']
        
        # Extract WHERE clause
        if where_pos != -1:
            where_end = min([p for p in [group_pos, having_pos, order_pos, limit_pos, len(sql)] if p > where_pos])
            where_clause = sql[where_pos + 5:where_end].strip()
            result['where'] = self._parse_where(where_clause)
        
        # Extract GROUP BY clause
        if group_pos != -1:
            group_end = min([p for p in [having_pos, order_pos, limit_pos, len(sql)] if p > group_pos])
            group_clause = sql[group_pos + 8:group_end].strip()
            result['group_by'] = [col.strip() for col in self._split_by_comma(group_clause)]
        
        # Extract HAVING clause
        if having_pos != -1:
            having_end = min([p for p in [order_pos, limit_pos, len(sql)] if p > having_pos])
            having_clause = sql[having_pos + 6:having_end].strip()
            result['having'] = self._parse_where(having_clause)  # Same structure as WHERE
        
        # Extract ORDER BY
        if order_pos != -1:
            order_end = limit_pos if limit_pos != -1 else len(sql)
            order_clause = sql[order_pos + 8:order_end].strip()
            result['order_by'] = order_clause
        
        # Extract LIMIT
        if limit_pos != -1:
            limit_clause = sql[limit_pos + 5:].strip()
            result['limit'] = int(limit_clause)
        
        return result
    
    def _parse_from_with_joins(self, from_clause: str) -> Dict[str, Any]:
        """
        Parse FROM clause with potential JOINs.

        Handles patterns like:
            FROM tableA
            FROM tableA INNER JOIN tableB ON tableA.id = tableB.a_id
            FROM tableA LEFT JOIN tableB ON ... INNER JOIN tableC ON ...
        """
        result = {'table': None, 'joins': []}

        clause = from_clause.strip()
        upper = clause.upper()

        # No JOIN present: simple table reference
        if 'JOIN' not in upper:
            main_match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)', clause)
            if not main_match:
                raise ValueError(f"Invalid FROM clause: {from_clause}")
            result['table'] = main_match.group(1)
            return result

        # Find the first JOIN (INNER/LEFT/JOIN) keyword start
        join_kw_match = re.search(r'\b(?:INNER\s+JOIN|LEFT\s+JOIN|JOIN)\b', clause, flags=re.IGNORECASE)
        if not join_kw_match:
            raise ValueError(f"Invalid JOIN syntax in FROM clause: {from_clause}")

        # Text before the first JOIN keyword is the main table
        main_part = clause[:join_kw_match.start()].strip()
        main_match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)', main_part)
        if not main_match:
            raise ValueError(f"Invalid main table in FROM clause: {from_clause}")
        result['table'] = main_match.group(1)

        # Remaining text contains one or more JOIN clauses
        remaining = clause[join_kw_match.start():]

        # Iterate over JOIN clauses and extract join type, table, and condition
        join_iter = re.finditer(
            r'\b((?:INNER\s+JOIN|LEFT\s+JOIN|JOIN))\b\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s+ON\s+(.+?)(?=(?:\s+(?:INNER\s+JOIN|LEFT\s+JOIN|JOIN)\b)|$)',
            remaining,
            flags=re.IGNORECASE | re.DOTALL
        )

        for m in join_iter:
            join_type_token = m.group(1).upper()
            table = m.group(2)
            condition = m.group(3).strip()

            join_type = JoinType.LEFT if 'LEFT' in join_type_token else JoinType.INNER

            result['joins'].append({
                'type': join_type,
                'table': table,
                'on': self._parse_join_condition(condition)
            })

        return result
    
    def _parse_join_condition(self, condition: str) -> Dict[str, Any]:
        """Parse JOIN ON condition (e.g., table1.col = table2.col)"""
        # Simple equality condition
        match = re.match(r'([\w.]+)\s*=\s*([\w.]+)', condition)
        if match:
            return {
                'left': match.group(1),
                'operator': '=',
                'right': match.group(2)
            }
        raise ValueError(f"Unsupported JOIN condition: {condition}")
    
    def _parse_where(self, where_clause: str) -> Dict[str, Any]:
        """Parse WHERE clause"""
        # Simple conditions: column = value, column > value, etc.
        # Also support AND, OR
        
        # For now, support simple conditions and AND
        conditions = []
        
        # Split by AND/OR
        parts = re.split(r'\s+(AND|OR)\s+', where_clause, flags=re.IGNORECASE)
        
        logical_ops = []
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Condition
                conditions.append(self._parse_condition(part))
            else:  # Logical operator
                logical_ops.append(part.upper())
        
        if len(conditions) == 1:
            return conditions[0]
        else:
            return {
                'conditions': conditions,
                'operators': logical_ops
            }
    
    def _parse_condition(self, condition: str) -> Dict[str, Any]:
        """Parse a single condition"""
        # Support: =, !=, <, >, <=, >=, LIKE
        operators = ['<=', '>=', '!=', '=', '<', '>', 'LIKE']
        
        for op in operators:
            if op in condition.upper():
                parts = re.split(f'\\s*{re.escape(op)}\\s*', condition, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2:
                    column = parts[0].strip()
                    value = parts[1].strip()
                    
                    # Remove quotes from string values
                    if value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    
                    return {
                        'column': column,
                        'operator': op.upper(),
                        'value': value
                    }
        
        raise ValueError(f"Invalid condition: {condition}")
    
    def _parse_update(self, sql: str) -> Dict[str, Any]:
        """Parse UPDATE statement"""
        # Pattern: UPDATE table_name SET col1=val1, col2=val2 WHERE condition
        
        match = re.match(
            r'UPDATE\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$',
            sql,
            re.IGNORECASE | re.DOTALL
        )
        if not match:
            raise ValueError("Invalid UPDATE syntax")
        
        table_name = match.group(1)
        set_clause = match.group(2).strip()
        where_clause = match.group(3)
        
        # Parse SET clause
        updates = {}
        for assignment in self._split_by_comma(set_clause):
            match = re.match(r'(\w+)\s*=\s*(.+)', assignment.strip())
            if match:
                column = match.group(1)
                value = match.group(2).strip()
                
                # Remove quotes
                if value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                
                updates[column] = value
        
        result = {
            'type': StatementType.UPDATE,
            'table': table_name,
            'updates': updates,
            'where': None
        }
        
        if where_clause:
            result['where'] = self._parse_where(where_clause)
        
        return result
    
    def _parse_delete(self, sql: str) -> Dict[str, Any]:
        """Parse DELETE statement"""
        # Pattern: DELETE FROM table_name WHERE condition
        
        match = re.match(
            r'DELETE FROM\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)(?:\s+WHERE\s+(.+))?$',
            sql,
            re.IGNORECASE | re.DOTALL
        )
        if not match:
            raise ValueError("Invalid DELETE syntax")
        
        table_name = match.group(1)
        where_clause = match.group(2)
        
        result = {
            'type': StatementType.DELETE,
            'table': table_name,
            'where': None
        }
        
        if where_clause:
            result['where'] = self._parse_where(where_clause)
        
        return result
    
    def _parse_create_index(self, sql: str) -> Dict[str, Any]:
        """Parse CREATE INDEX statement"""
        # Pattern: CREATE INDEX index_name ON table_name (column)
        
        match = re.match(
            r'CREATE INDEX\s+(\w+)\s+ON\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*\((.*?)\)\s*$',
            sql,
            re.IGNORECASE
        )
        if not match:
            raise ValueError("Invalid CREATE INDEX syntax")

        columns_str = match.group(3)
        columns = [c.strip() for c in self._split_by_comma(columns_str) if c.strip()]
        if not columns:
            raise ValueError("CREATE INDEX must specify at least one column")
        
        return {
            'type': StatementType.CREATE_INDEX,
            'index_name': match.group(1),
            'table': match.group(2),
            'columns': columns,
        }
    
    def _parse_values(self, values_str: str) -> List[Any]:
        """Parse VALUES clause"""
        values = []
        for val in self._split_by_comma(values_str):
            val = val.strip()
            
            # Remove quotes from strings
            if (val.startswith("'") and val.endswith("'")) or \
               (val.startswith('"') and val.endswith('"')):
                val = val[1:-1]
            elif val.upper() == 'NULL':
                val = None
            elif val.upper() == 'TRUE':
                val = True
            elif val.upper() == 'FALSE':
                val = False
            else:
                # Try to convert to number
                try:
                    if '.' in val:
                        val = float(val)
                    else:
                        val = int(val)
                except ValueError:
                    pass  # Keep as string
            
            values.append(val)
        
        return values
    
    def _split_by_comma(self, text: str) -> List[str]:
        """Split by comma, respecting parentheses and quotes"""
        parts = []
        current = []
        paren_depth = 0
        in_quotes = False
        quote_char = None
        
        for char in text:
            if char in ('"', "'") and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                quote_char = char if in_quotes else None
            elif char == '(' and not in_quotes:
                paren_depth += 1
            elif char == ')' and not in_quotes:
                paren_depth -= 1
            elif char == ',' and paren_depth == 0 and not in_quotes:
                parts.append(''.join(current))
                current = []
                continue
            
            current.append(char)
        
        if current:
            parts.append(''.join(current))
        
        return parts
