"""
Query Execution Engine - Executes parsed SQL queries

This module implements the query execution layer that:
    1. Takes parsed SQL from SQLParser
    2. Plans and optimizes execution
    3. Executes operations against Storage
    4. Returns formatted results

Execution Pipeline:
    SQL String (input)
        ↓
    SQLParser (parsing)
        ↓
    Parsed Dictionary (intermediate)
        ↓
    QueryEngine.execute() (this module)
        ↓
    Storage operations
        ↓
    Result Dictionary (output)

Supported Operations:
    - CREATE TABLE: Schema definition
    - INSERT: Data insertion with constraint checking
    - SELECT: Queries with WHERE, ORDER BY, LIMIT, JOINs
    - UPDATE: Record modification
    - DELETE: Record removal
    - CREATE INDEX: Index creation

Query Optimization:
    - Index usage for equality conditions
    - Full table scan fallback
    - Column selection projection
    - ORDER BY sorting
    - LIMIT early termination

Future Enhancements:
    - Query plan caching
    - Cost-based optimization
    - Aggregate function support
    - Subquery execution
    - Query explain plans
"""
from typing import List, Dict, Any, Optional
from core.parser import SQLParser, StatementType, JoinType
from core.storage import Storage
from core.schema import Table
from core.advanced_queries import AggregateType, AggregateFunction
from core.database_manager import DatabaseManager


class QueryEngine:
    """
    SQL query execution engine.
    
    This is the core execution layer that:
    - Accepts parsed SQL statements from SQLParser
    - Plans and executes operations on Storage
    - Returns results in consistent format
    - Handles all SQL operations (DDL, DML, DQL)
    
    Execution Flow:
        1. Parse SQL -> get statement type and parameters
        2. Dispatch to operation-specific executor
        3. Execute against Storage layer
        4. Format and return results
    
    Result Format:
        Dictionary with:
        - 'success': Boolean indicating success/failure
        - 'message': Human-readable status message
        - 'rows': Result rows (SELECT only)
        - 'count': Number of results/affected rows
        - 'error': Error message if failed
    
    Attributes:
        storage: Storage engine instance
        parser: SQL parser instance
    """
    
    def __init__(
        self,
        storage: Optional[Storage] = None,
        database_manager: Optional[DatabaseManager] = None,
        default_database: Optional[str] = None,
    ):
        """
        Initialize the query engine.
        
        Args:
            storage: Storage engine instance to execute against (single-database mode)
            database_manager: Optional DatabaseManager for multi-database mode
            default_database: Database name to select initially (multi-database mode)
        """
        self.database_manager = database_manager
        self.current_database: Optional[str] = None

        # Backward-compatible: if storage is provided, start in single-db mode.
        self.storage = storage or Storage(data_dir="data")

        # Multi-db: optionally select a default database.
        if self.database_manager is not None and default_database:
            self.use_database(default_database)

        self.parser = SQLParser()

    def use_database(self, name: str) -> Dict[str, Any]:
        if self.database_manager is None:
            return {
                'success': False,
                'error': 'Multi-database mode is not enabled'
            }
        try:
            self.storage = self.database_manager.open_storage(name)
            self.current_database = name
            return {
                'success': True,
                'message': f"Database changed to '{name}'",
                'rows_affected': 0,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute(self, sql: str) -> Dict[str, Any]:
        """
        Execute a SQL statement.
        
        Main entry point for SQL execution. Handles:
        1. Parsing SQL to identify statement type
        2. Dispatching to appropriate executor
        3. Error handling and formatting
        
        Args:
            sql: Raw SQL statement string
            
        Returns:
            Dictionary with execution results:
                success: True if executed successfully
                message: Status message
                rows: Result rows (if SELECT)
                count: Number of affected rows
                error: Error message if failed
                
        Examples:
            >>> engine = QueryEngine(storage)
            >>> result = engine.execute("SELECT * FROM users WHERE age > 18")
            >>> if result['success']:
            ...     for row in result['rows']:
            ...         print(row)
        """
        try:
            # Parse SQL statement
            parsed = self.parser.parse(sql)
            stmt_type = parsed['type']
            
            # Dispatch to appropriate executor based on statement type
            if stmt_type == StatementType.CREATE_DATABASE:
                return self._execute_create_database(parsed)
            elif stmt_type == StatementType.DROP_DATABASE:
                return self._execute_drop_database(parsed)
            elif stmt_type == StatementType.USE_DATABASE:
                return self.use_database(parsed['database'])
            elif stmt_type == StatementType.SHOW_DATABASES:
                return self._execute_show_databases()
            elif stmt_type == StatementType.SHOW_TABLES:
                return self._execute_show_tables()
            elif stmt_type == StatementType.CREATE_TABLE:
                return self._execute_create_table(parsed)
            elif stmt_type == StatementType.INSERT:
                return self._execute_insert(parsed)
            elif stmt_type == StatementType.SELECT:
                return self._execute_select(parsed)
            elif stmt_type == StatementType.UPDATE:
                return self._execute_update(parsed)
            elif stmt_type == StatementType.DELETE:
                return self._execute_delete(parsed)
            elif stmt_type == StatementType.CREATE_INDEX:
                return self._execute_create_index(parsed)
            else:
                return {'success': False, 'error': 'Unsupported statement type'}
        
        except Exception as e:
            # Return error without re-raising
            return {'success': False, 'error': str(e)}

    def _execute_create_database(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        if self.database_manager is None:
            return {'success': False, 'error': 'Multi-database mode is not enabled'}
        name = parsed['database']
        self.database_manager.create_database(name)
        return {
            'success': True,
            'message': f"Database '{name}' created",
            'rows_affected': 0,
        }

    def _execute_drop_database(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        if self.database_manager is None:
            return {'success': False, 'error': 'Multi-database mode is not enabled'}
        name = parsed['database']
        if self.current_database and name == self.current_database:
            return {'success': False, 'error': 'Cannot drop the currently selected database'}
        self.database_manager.drop_database(name)
        return {
            'success': True,
            'message': f"Database '{name}' dropped",
            'rows_affected': 0,
        }

    def _execute_show_databases(self) -> Dict[str, Any]:
        if self.database_manager is None:
            return {'success': False, 'error': 'Multi-database mode is not enabled'}
        dbs = self.database_manager.list_databases()
        rows = [
            {
                'database': db.name,
                'path': db.path,
                'exists': db.exists,
                'current': (db.name == self.current_database),
            }
            for db in dbs
        ]
        return {'success': True, 'rows': rows, 'count': len(rows)}

    def _execute_show_tables(self) -> Dict[str, Any]:
        tables = self.storage.list_tables()
        rows = [{'table': name} for name in tables]
        return {'success': True, 'rows': rows, 'count': len(rows)}
    
    def _execute_create_table(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CREATE TABLE"""
        table = Table(name=parsed['table'], columns=parsed['columns'])
        self.storage.create_table(table)
        
        return {
            'success': True,
            'message': f"Table {parsed['table']} created successfully",
            'rows_affected': 0
        }
    
    def _execute_insert(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Execute INSERT"""
        table_name = parsed['table']
        table = self.storage.get_table(table_name)
        
        if not table:
            return {'success': False, 'error': f"Table {table_name} does not exist"}
        
        # Build row dict
        if parsed['columns']:
            # Columns specified
            if len(parsed['columns']) != len(parsed['values']):
                return {'success': False, 'error': 'Column count does not match value count'}
            row = dict(zip(parsed['columns'], parsed['values']))
        else:
            # No columns specified - use all columns in order
            if len(table.columns) != len(parsed['values']):
                return {'success': False, 'error': 'Value count does not match table column count'}
            row = dict(zip([col.name for col in table.columns], parsed['values']))
        
        row_id = self.storage.insert_row(table_name, row)
        
        return {
            'success': True,
            'message': f"Row inserted with ID {row_id}",
            'rows_affected': 1
        }
    
    def _execute_select(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SELECT with JOIN support, aggregates, and GROUP BY.
        
        Supports:
        - Simple SELECT with WHERE, ORDER BY, LIMIT
        - JOINs (INNER, LEFT)
        - Aggregate functions (COUNT, SUM, AVG, MAX, MIN)
        - GROUP BY with aggregates
        - HAVING clause for filtering groups
        """
        table_name = parsed['table']
        
        # Check if table exists
        table = self.storage.get_table(table_name)
        if not table:
            return {'success': False, 'error': f"Table {table_name} does not exist"}
        
        # Handle JOINs if present
        if parsed['joins']:
            return self._execute_select_with_joins(parsed)
        
        # Check if aggregates or GROUP BY present
        if parsed['aggregates'] or parsed['group_by']:
            return self._execute_select_with_aggregates(parsed)
        
        # Simple SELECT without aggregates
        rows = self.storage.select_rows(table_name, parsed['where'])
        
        # Apply column selection
        if parsed['columns'] != ['*']:
            rows = self._select_columns(rows, parsed['columns'])
        
        # Apply ORDER BY
        if parsed['order_by']:
            rows = self._apply_order_by(rows, parsed['order_by'])
        
        # Apply LIMIT
        if parsed['limit']:
            rows = rows[:parsed['limit']]
        
        return {
            'success': True,
            'rows': rows,
            'count': len(rows)
        }
    
    def _execute_select_with_joins(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SELECT with JOINs"""
        # Get main table rows
        main_table = parsed['table']
        main_rows = self.storage.select_rows(main_table, parsed['where'])
        
        # Prefix columns with table name
        main_rows = [self._prefix_columns(row, main_table) for row in main_rows]
        
        # Process each join
        result_rows = main_rows
        
        for join in parsed['joins']:
            join_table = join['table']
            join_type = join['type']
            join_condition = join['on']
            
            # Get join table rows
            join_rows = self.storage.select_rows(join_table)
            join_rows = [self._prefix_columns(row, join_table) for row in join_rows]
            
            # Perform join
            if join_type == JoinType.INNER:
                result_rows = self._inner_join(result_rows, join_rows, join_condition)
            elif join_type == JoinType.LEFT:
                result_rows = self._left_join(result_rows, join_rows, join_condition)
        
        # Apply column selection
        if parsed['columns'] != ['*']:
            result_rows = self._select_columns(result_rows, parsed['columns'])
        
        # Apply ORDER BY
        if parsed['order_by']:
            result_rows = self._apply_order_by(result_rows, parsed['order_by'])
        
        # Apply LIMIT
        if parsed['limit']:
            result_rows = result_rows[:parsed['limit']]
        
        return {
            'success': True,
            'rows': result_rows,
            'count': len(result_rows)
        }    
    def _execute_select_with_aggregates(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SELECT with aggregate functions and GROUP BY.
        
        Handles:
        - COUNT(*), COUNT(col), SUM(col), AVG(col), MAX(col), MIN(col)
        - GROUP BY one or more columns
        - HAVING clause for filtering aggregated groups
        """
        table_name = parsed['table']
        rows = self.storage.select_rows(table_name, parsed['where'])
        
        # Parse aggregate functions
        agg_funcs = []
        for agg_info in parsed['aggregates']:
            func_name = agg_info['function'].upper()
            agg_type = AggregateType[func_name]
            agg_funcs.append({
                'type': agg_type,
                'column': agg_info['column'],
                'alias': agg_info['alias']
            })
        
        # If no GROUP BY, compute aggregates on all rows
        if not parsed['group_by']:
            result_row = {}
            for agg_info in agg_funcs:
                agg = AggregateFunction(agg_info['type'])
                for row in rows:
                    if agg_info['column']:
                        value = row.get(agg_info['column'])
                        if value is not None:
                            agg.add(value)
                    else:
                        # COUNT(*)
                        agg.add(1)
                result_row[agg_info['alias']] = agg.get_result()
            
            # Add any selected columns (if not aggregated)
            if parsed['columns'] != ['*'] and not all(col in [a['alias'] for a in agg_funcs] for col in parsed['columns']):
                # Include first row's non-aggregate columns
                if rows:
                    for col in parsed['columns']:
                        if col not in result_row and col in rows[0]:
                            result_row[col] = rows[0][col]
            
            return {
                'success': True,
                'rows': [result_row],
                'count': 1
            }
        
        # GROUP BY: group rows by specified columns
        groups = {}
        for row in rows:
            # Create group key from GROUP BY columns
            group_key = tuple(row.get(col) for col in parsed['group_by'])
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(row)
        
        # Compute aggregates for each group
        result_rows = []
        for group_key, group_rows in groups.items():
            result_row = {}
            
            # Add GROUP BY columns to result
            for i, col in enumerate(parsed['group_by']):
                result_row[col] = group_key[i]
            
            # Compute aggregates for this group
            for agg_info in agg_funcs:
                agg = AggregateFunction(agg_info['type'])
                for row in group_rows:
                    if agg_info['column']:
                        value = row.get(agg_info['column'])
                        if value is not None:
                            agg.add(value)
                    else:
                        # COUNT(*)
                        agg.add(1)
                result_row[agg_info['alias']] = agg.get_result()
            
            result_rows.append(result_row)
        
        # Apply HAVING clause if present
        if parsed['having']:
            filtered_rows = []
            for row in result_rows:
                if self._evaluate_having(row, parsed['having'], agg_funcs):
                    filtered_rows.append(row)
            result_rows = filtered_rows
        
        # Apply ORDER BY if present
        if parsed['order_by']:
            result_rows = self._apply_order_by(result_rows, parsed['order_by'])
        
        # Apply LIMIT if present
        if parsed['limit']:
            result_rows = result_rows[:parsed['limit']]
        
        return {
            'success': True,
            'rows': result_rows,
            'count': len(result_rows)
        }
    
    def _evaluate_having(self, row: Dict[str, Any], having: Dict[str, Any], agg_funcs: List[Dict]) -> bool:
        """
        Evaluate HAVING clause on aggregated row.
        Similar to WHERE evaluation but operates on aggregate results.
        
        The HAVING column may be an aggregate function like 'SUM(total)',
        which needs to be mapped to its alias in the result row.
        """
        column = having['column']
        operator = having['operator']
        value = having['value']
        
        # If column looks like an aggregate function, find its alias
        if '(' in column:
            # Match SUM(total) to its alias
            for agg_info in agg_funcs:
                agg_expr = f"{agg_info['type'].name}({agg_info['column'] or '*'})"
                if agg_expr.upper() == column.upper():
                    column = agg_info['alias']
                    break
        
        # Get actual value from row
        actual = row.get(column)
        if actual is None:
            return False
        
        # Convert value to appropriate type for comparison
        try:
            if isinstance(actual, (int, float)):
                value = float(value)
        except (ValueError, TypeError):
            pass
        
        # Apply operator
        if operator == '=':
            return actual == value
        elif operator == '!=':
            return actual != value
        elif operator == '>':
            return actual > value
        elif operator == '<':
            return actual < value
        elif operator == '>=':
            return actual >= value
        elif operator == '<=':
            return actual <= value
        
        return False    
    def _inner_join(self, left_rows: List[Dict], right_rows: List[Dict], condition: Dict) -> List[Dict]:
        """Perform INNER JOIN"""
        result = []
        
        left_col = condition['left']
        right_col = condition['right']
        
        for left_row in left_rows:
            for right_row in right_rows:
                if left_row.get(left_col) == right_row.get(right_col):
                    # Merge rows
                    merged = {**left_row, **right_row}
                    result.append(merged)
        
        return result
    
    def _left_join(self, left_rows: List[Dict], right_rows: List[Dict], condition: Dict) -> List[Dict]:
        """Perform LEFT JOIN"""
        result = []
        
        left_col = condition['left']
        right_col = condition['right']
        
        for left_row in left_rows:
            matched = False
            for right_row in right_rows:
                if left_row.get(left_col) == right_row.get(right_col):
                    # Merge rows
                    merged = {**left_row, **right_row}
                    result.append(merged)
                    matched = True
            
            if not matched:
                # Include left row with NULL for right columns
                result.append(left_row)
        
        return result
    
    def _prefix_columns(self, row: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """Prefix column names with table name"""
        return {f"{table_name}.{col}": val for col, val in row.items()}
    
    def _select_columns(self, rows: List[Dict], columns: List[str]) -> List[Dict]:
        """Select specific columns from rows"""
        result = []
        for row in rows:
            selected_row = {}
            for col in columns:
                # Handle table.column notation
                if col in row:
                    selected_row[col] = row[col]
                else:
                    # Try without table prefix
                    for key, val in row.items():
                        if key.endswith(f".{col}"):
                            selected_row[col] = val
                            break
            result.append(selected_row)
        return result
    
    def _apply_order_by(self, rows: List[Dict], order_by: str) -> List[Dict]:
        """Apply ORDER BY clause"""
        # Parse ORDER BY (e.g., "column_name ASC" or "column_name DESC")
        parts = order_by.strip().split()
        column = parts[0]
        desc = len(parts) > 1 and parts[1].upper() == 'DESC'
        
        # Find actual column name in rows (handle table.column notation)
        def get_sort_key(row):
            if column in row:
                return row[column]
            # Try with table prefix
            for key in row.keys():
                if key.endswith(f".{column}"):
                    return row[key]
            return None
        
        try:
            return sorted(rows, key=get_sort_key, reverse=desc)
        except:
            return rows
    
    def _execute_update(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Execute UPDATE"""
        table_name = parsed['table']
        
        if not self.storage.get_table(table_name):
            return {'success': False, 'error': f"Table {table_name} does not exist"}
        
        updated_count = self.storage.update_rows(
            table_name,
            parsed['updates'],
            parsed['where']
        )
        
        return {
            'success': True,
            'message': f"{updated_count} row(s) updated",
            'rows_affected': updated_count
        }
    
    def _execute_delete(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Execute DELETE"""
        table_name = parsed['table']
        
        if not self.storage.get_table(table_name):
            return {'success': False, 'error': f"Table {table_name} does not exist"}
        
        deleted_count = self.storage.delete_rows(table_name, parsed['where'])
        
        return {
            'success': True,
            'message': f"{deleted_count} row(s) deleted",
            'rows_affected': deleted_count
        }
    
    def _execute_create_index(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CREATE INDEX"""
        table_name = parsed['table']
        column_name = parsed['column']
        
        if not self.storage.get_table(table_name):
            return {'success': False, 'error': f"Table {table_name} does not exist"}
        
        self.storage.create_index(table_name, column_name)
        
        return {
            'success': True,
            'message': f"Index created on {table_name}.{column_name}",
            'rows_affected': 0
        }
