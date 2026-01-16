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

    def explain(self, sql: str) -> Dict[str, Any]:
        """Return a structured execution plan for a SQL statement.

        This is a lightweight, deterministic planner meant for demos and UX.
        It does not execute the query.
        """
        parsed = self.parser.parse(sql)
        stmt_type = parsed.get('type')

        # Only SELECT has a meaningful plan today.
        if stmt_type != StatementType.SELECT:
            return {
                'type': 'STATEMENT',
                'statement': str(stmt_type),
                'details': 'Explain plans are currently supported for SELECT only.',
                'children': [],
            }

        return self._build_select_plan(parsed)

    def _build_select_plan(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Build a plan tree for SELECT."""
        table = parsed['table']
        where = parsed.get('where')
        joins = parsed.get('joins') or []
        order_by = parsed.get('order_by')
        limit = parsed.get('limit')
        columns = parsed.get('columns') or ['*']
        aggregates = parsed.get('aggregates') or []
        group_by = parsed.get('group_by') or []

        root: Dict[str, Any] = {
            'type': 'SELECT',
            'details': {'from': table},
            'children': [],
        }

        # Aggregates/GROUP BY are executed via a separate path; still show a simple plan.
        if aggregates or group_by:
            root['details']['mode'] = 'aggregate'

        # Base access path
        access_node = self._plan_access_path(table, where)
        current = access_node

        # JOINs
        for join in joins:
            join_table = join['table']
            join_type = join['type']
            on = join['on']
            left_key = on.get('left')
            right_key = on.get('right')
            right_col = self._unqualify_column(right_key)

            method = 'NESTED_LOOP'
            try:
                if join_table in self.storage.indexes and right_col and self.storage.indexes[join_table].has_index(right_col):
                    method = 'INDEX_LOOKUP'
            except Exception:
                method = 'NESTED_LOOP'

            join_node: Dict[str, Any] = {
                'type': 'JOIN',
                'details': {
                    'join_type': str(join_type),
                    'table': join_table,
                    'on': {'left': left_key, 'right': right_key},
                    'method': method,
                },
                'children': [current, {'type': 'SCAN', 'details': {'table': join_table}, 'children': []}],
            }
            current = join_node

        # GROUP BY / AGG
        if aggregates or group_by:
            agg_node: Dict[str, Any] = {
                'type': 'AGGREGATE',
                'details': {
                    'group_by': group_by,
                    'aggregates': aggregates,
                },
                'children': [current],
            }
            current = agg_node

        # ORDER BY
        if order_by:
            sort_node: Dict[str, Any] = {
                'type': 'SORT',
                'details': {'order_by': order_by},
                'children': [current],
            }
            current = sort_node

        # LIMIT
        if limit:
            limit_node: Dict[str, Any] = {
                'type': 'LIMIT',
                'details': {'limit': limit},
                'children': [current],
            }
            current = limit_node

        # PROJECTION
        if columns != ['*']:
            proj_node: Dict[str, Any] = {
                'type': 'PROJECTION',
                'details': {'columns': columns},
                'children': [current],
            }
            current = proj_node

        root['children'].append(current)
        return root

    def _plan_access_path(self, table: str, where: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Choose a basic access path node: INDEX_LOOKUP vs SCAN (+ optional FILTER)."""
        if where and where.get('operator') == '=' and 'column' in where:
            col = where.get('column')
            try:
                if table in self.storage.indexes and self.storage.indexes[table].has_index(col):
                    return {
                        'type': 'INDEX_LOOKUP',
                        'details': {'table': table, 'column': col, 'operator': '=', 'value': where.get('value')},
                        'children': [],
                    }
            except Exception:
                pass

        scan: Dict[str, Any] = {'type': 'SCAN', 'details': {'table': table}, 'children': []}
        if where:
            return {
                'type': 'FILTER',
                'details': {'where': where},
                'children': [scan],
            }
        return scan

    def _unqualify_column(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        # Accept either "col" or "table.col"
        return name.split('.')[-1]

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

        # Earlier projection before sorting (keep ORDER BY column if needed)
        if parsed['columns'] != ['*'] and parsed['order_by']:
            requested = parsed['columns']
            order_col = parsed['order_by'].strip().split()[0]
            needed = list(dict.fromkeys(requested + [order_col]))
            rows = self._select_columns(rows, needed)
            rows = self._apply_order_by(rows, parsed['order_by'])
            if needed != requested:
                rows = self._select_columns(rows, requested)
        else:
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

            # Choose join strategy
            if join_type == JoinType.INNER:
                result_rows = self._inner_join_index_aware(result_rows, join_table, join_condition)
            elif join_type == JoinType.LEFT:
                result_rows = self._left_join_index_aware(result_rows, join_table, join_condition)
        
        # Earlier projection before sorting (keep ORDER BY column if needed)
        if parsed['columns'] != ['*'] and parsed['order_by']:
            requested = parsed['columns']
            order_col = parsed['order_by'].strip().split()[0]
            needed = list(dict.fromkeys(requested + [order_col]))
            result_rows = self._select_columns(result_rows, needed)
            result_rows = self._apply_order_by(result_rows, parsed['order_by'])
            if needed != requested:
                result_rows = self._select_columns(result_rows, requested)
        else:
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

    def _inner_join_index_aware(self, left_rows: List[Dict], right_table: str, condition: Dict) -> List[Dict]:
        """Perform INNER JOIN, using an index on the right table when available."""
        left_col = condition['left']
        right_col_qualified = condition['right']
        right_col = self._unqualify_column(right_col_qualified) or right_col_qualified

        right_rows_raw = self.storage.data.get(right_table, [])
        right_by_id = {r.get('_row_id'): r for r in right_rows_raw}

        index_mgr = self.storage.indexes.get(right_table)
        use_index = bool(index_mgr and index_mgr.has_index(right_col))

        result: List[Dict] = []
        if use_index:
            index = index_mgr.get_index(right_col)
            for left_row in left_rows:
                key = left_row.get(left_col)
                if key is None:
                    continue
                row_ids = index.search(key)
                for row_id in row_ids:
                    raw = right_by_id.get(row_id)
                    if not raw:
                        continue
                    clean = {k: v for k, v in raw.items() if k != '_row_id'}
                    merged = {**left_row, **self._prefix_columns(clean, right_table)}
                    result.append(merged)
            return result

        # Fallback: nested-loop join
        right_rows = [self._prefix_columns(row, right_table) for row in self.storage.select_rows(right_table)]
        return self._inner_join(left_rows, right_rows, condition)

    def _left_join_index_aware(self, left_rows: List[Dict], right_table: str, condition: Dict) -> List[Dict]:
        """Perform LEFT JOIN, using an index on the right table when available."""
        left_col = condition['left']
        right_col_qualified = condition['right']
        right_col = self._unqualify_column(right_col_qualified) or right_col_qualified

        right_rows_raw = self.storage.data.get(right_table, [])
        right_by_id = {r.get('_row_id'): r for r in right_rows_raw}

        index_mgr = self.storage.indexes.get(right_table)
        use_index = bool(index_mgr and index_mgr.has_index(right_col))

        result: List[Dict] = []
        if use_index:
            index = index_mgr.get_index(right_col)
            for left_row in left_rows:
                key = left_row.get(left_col)
                matched_any = False
                if key is not None:
                    row_ids = index.search(key)
                    for row_id in row_ids:
                        raw = right_by_id.get(row_id)
                        if not raw:
                            continue
                        clean = {k: v for k, v in raw.items() if k != '_row_id'}
                        merged = {**left_row, **self._prefix_columns(clean, right_table)}
                        result.append(merged)
                        matched_any = True
                if not matched_any:
                    result.append(left_row)
            return result

        # Fallback: nested-loop join
        right_rows = [self._prefix_columns(row, right_table) for row in self.storage.select_rows(right_table)]
        return self._left_join(left_rows, right_rows, condition)
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
        columns = parsed.get('columns') or []
        index_name = parsed.get('index_name')
        
        if not self.storage.get_table(table_name):
            return {'success': False, 'error': f"Table {table_name} does not exist"}

        self.storage.create_index(table_name, columns, index_name=index_name)
        
        return {
            'success': True,
            'message': f"Index '{index_name}' created on {table_name}({', '.join(columns)})",
            'rows_affected': 0
        }
