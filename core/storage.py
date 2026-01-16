"""
Storage Engine - Handles data persistence and in-memory caching

This module implements the core storage layer of the RDBMS:

    1. In-Memory Caching: All data loaded into RAM for fast access
    2. Disk Persistence: Changes written to JSON files
    3. Constraint Enforcement: Validates primary key and unique constraints
    4. Index Management: Maintains B-tree indexes for fast lookups
    5. Transaction Support: Basic ACID properties (atomicity via atomic writes)

Storage Architecture:
    
    Storage Layer:
        ├── Table Schemas (in-memory + disk)
        ├── Row Data (in-memory + disk)
        ├── Index Manager (maintains B-trees)
        └── Row ID Generator (ensures unique IDs)
    
    File Structure:
        data/
        ├── {table_name}.schema.json    # Table schema definition
        └── {table_name}.data.json      # Row data and metadata

Key Features:
    - Automatic index creation on primary/unique keys
    - Constraint validation before insertion
    - Atomic writes ensure data consistency
    - In-memory caching for performance
    - Efficient condition-based row retrieval
    - Index-accelerated lookups

Limitations & TODO:
    - No crash recovery (no WAL)
    - All data must fit in memory
    - No multi-user concurrency control
    - No query result streaming
    - Limited transaction support
"""
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from core.schema import Table
from core.index import IndexManager


class Storage:
    """
    Storage engine for managing table data and indexes.
    
    This class is the main interface for all data operations:
    - Table creation and management
    - CRUD operations (Create, Read, Update, Delete)
    - Constraint validation
    - Index management
    - Data persistence
    
    Architecture:
        In-Memory State:
            - tables: Dict[table_name -> Table schema]
            - data: Dict[table_name -> List of rows]
            - indexes: Dict[table_name -> IndexManager]
            - next_row_ids: Dict[table_name -> next ID]
        
        Disk Storage:
            - {table}.schema.json: Table schema definition
            - {table}.data.json: Rows and metadata
    
    Thread Safety: NOT thread-safe. Use locks for concurrent access.
    
    Attributes:
        data_dir: Directory for storing database files
        tables: In-memory table schemas
        data: In-memory row data
        indexes: B-tree indexes for each table
        next_row_ids: Row ID generators
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the storage engine.
        
        Creates data directory if it doesn't exist and loads
        all existing table schemas and data from disk.
        
        Args:
            data_dir: Directory for storing database files
            
        Raises:
            OSError: If data directory cannot be created
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory state mirrors disk storage
        self.tables: Dict[str, Table] = {}                    # Table schemas
        self.data: Dict[str, List[Dict[str, Any]]] = {}      # Row data
        self.indexes: Dict[str, IndexManager] = {}            # Index managers
        self.next_row_ids: Dict[str, int] = {}                # Row ID generators
        
        # Load existing tables from disk
        self._load_all_tables()
    
    def create_table(self, table: Table):
        """
        Create a new table in the database.
        
        Steps:
        1. Validate table doesn't already exist
        2. Initialize empty data structures
        3. Create automatic indexes on constraints
        4. Save schema to disk
        
        Args:
            table: Table object with schema definition
            
        Raises:
            ValueError: If table already exists
            
        Note:
            - Automatically creates index on primary key
            - Automatically creates indexes on unique columns
        """
        if table.name in self.tables:
            raise ValueError(f"Table '{table.name}' already exists")
        
        # Register table schema
        self.tables[table.name] = table
        self.data[table.name] = []
        self.indexes[table.name] = IndexManager()
        self.next_row_ids[table.name] = 0
        
        # Create automatic indexes on constraints
        if table.primary_key:
            self.indexes[table.name].create_index(table.primary_key)
        
        for col_name in table.unique_columns:
            if col_name != table.primary_key:  # Avoid duplicate
                self.indexes[table.name].create_index(col_name)
        
        # Persist schema to disk
        self._save_table_schema(table)
    
    def get_table(self, table_name: str) -> Optional[Table]:
        """Get table schema"""
        return self.tables.get(table_name)
    
    def insert_row(self, table_name: str, row: Dict[str, Any]) -> int:
        """
        Insert a row into a table.
        
        Execution flow:
        1. Validate table exists
        2. Validate and convert row data
        3. Check unique/primary key constraints
        4. Check foreign key constraints
        5. Assign unique row ID
        6. Add to in-memory data
        7. Update indexes
        8. Persist to disk
        
        Args:
            table_name: Name of target table
            row: Dictionary with column_name -> value mappings
            
        Returns:
            Internal row ID assigned to the row
            
        Raises:
            ValueError: If table doesn't exist or constraints violated
            
        Note:
            Row must contain all NOT NULL columns.
            Missing nullable columns are stored as None.
        """
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' does not exist")
        
        table = self.tables[table_name]

        # Generated columns are computed; they cannot be inserted directly.
        for col in table.columns:
            if col.generated_expr and col.name in row:
                raise ValueError(f"Cannot insert into generated column '{col.name}'")
        
        # Validate row against schema (type conversion, NOT NULL checks)
        validated_row = table.validate_row(row)
        
        # Check uniqueness constraints (UNIQUE and PRIMARY KEY)
        self._check_unique_constraints(table_name, validated_row)
        
        # Check foreign key constraints
        self._check_foreign_keys(table, validated_row)
        
        # Assign unique internal row ID
        row_id = self.next_row_ids[table_name]
        self.next_row_ids[table_name] += 1
        validated_row['_row_id'] = row_id
        
        # Add to in-memory data structure
        self.data[table_name].append(validated_row)

        try:
            # Update indexes with new row
            self.indexes[table_name].insert(validated_row, row_id)

            # Persist to disk
            self._save_table_data(table_name)

            # Update row count metadata
            table.row_count += 1
        except Exception:
            # Best-effort rollback: remove row and index entries.
            try:
                self.indexes[table_name].delete(validated_row, row_id)
            except Exception:
                pass

            try:
                # Remove the inserted row if it still exists.
                self.data[table_name] = [r for r in self.data[table_name] if r.get('_row_id') != row_id]
            except Exception:
                pass

            # Rewind row id generator if this was the last assigned id.
            try:
                if self.next_row_ids.get(table_name) == row_id + 1:
                    self.next_row_ids[table_name] = row_id
            except Exception:
                pass

            raise
        
        return row_id
    
    def select_rows(self, table_name: str, condition: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Select rows from a table"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        rows = self.data[table_name]
        
        if condition is None:
            return [self._remove_internal_fields(row) for row in rows]
        
        # Try to use index if available (single-column or composite) for equality predicates
        eq_map = self._extract_equality_conditions(condition)
        if eq_map:
            # Convert values to proper types
            converted = {}
            table = self.tables[table_name]
            for col, value in eq_map.items():
                col_def = table.get_column(col)
                if col_def:
                    try:
                        value = col_def.convert(value)
                    except Exception:
                        pass
                converted[col] = value

            index_mgr = self.indexes[table_name]
            best_def = None
            for idx_def in index_mgr.list_indexes():
                if all(c in converted for c in idx_def.columns):
                    if best_def is None or len(idx_def.columns) > len(best_def.columns):
                        best_def = idx_def

            if best_def is not None:
                if len(best_def.columns) == 1:
                    key = converted[best_def.columns[0]]
                else:
                    key = tuple(converted[c] for c in best_def.columns)
                row_ids = best_def.index.search(key)
                matching_rows = [row for row in rows if row['_row_id'] in set(row_ids)]
                return [self._remove_internal_fields(row) for row in matching_rows]
        
        # Full table scan
        matching_rows = [row for row in rows if self._matches_condition(row, condition, table_name)]
        return [self._remove_internal_fields(row) for row in matching_rows]
    
    def update_rows(self, table_name: str, updates: Dict[str, Any], condition: Optional[Dict] = None) -> int:
        """Update rows in a table"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        table = self.tables[table_name]
        rows = self.data[table_name]

        # Generated columns are computed; they cannot be updated directly.
        for col in table.columns:
            if col.generated_expr and col.name in updates:
                raise ValueError(f"Cannot update generated column '{col.name}'")
        
        # Find rows to update
        rows_to_update = []
        for row in rows:
            if condition is None or self._matches_condition(row, condition, table_name):
                rows_to_update.append(row)
        
        # Update each row
        updated_count = 0
        for row in rows_to_update:
            old_row = row.copy()
            
            # Apply updates with validation
            for col_name, value in updates.items():
                col_def = table.get_column(col_name)
                if col_def:
                    row[col_name] = col_def.convert(value)

            # Recompute generated columns (if any) based on updated values
            try:
                validated = table.validate_row(row)
                for k, v in validated.items():
                    row[k] = v
            except (ValueError, TypeError) as e:
                raise ValueError(str(e))
            
            # Check unique constraints
            self._check_unique_constraints(table_name, row, exclude_row_id=row['_row_id'])
            
            # Check foreign key constraints
            self._check_foreign_keys(table, row)
            
            # Update indexes
            self.indexes[table_name].update(old_row, row, row['_row_id'])
            
            updated_count += 1
        
        if updated_count > 0:
            self._save_table_data(table_name)
        
        return updated_count
    
    def delete_rows(self, table_name: str, condition: Optional[Dict] = None) -> int:
        """
        Delete rows from a table.
        
        Checks for referential integrity - rows cannot be deleted if they
        are referenced by foreign keys in other tables.
        """
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        rows = self.data[table_name]
        table = self.tables[table_name]
        
        # Find rows to delete
        rows_to_delete = []
        for row in rows:
            if condition is None or self._matches_condition(row, condition, table_name):
                rows_to_delete.append(row)
        
        # Apply foreign key ON DELETE actions (RESTRICT/CASCADE/SET NULL)
        if table.primary_key:
            self._apply_on_delete_actions(table_name, rows_to_delete, table.primary_key)
        
        # Delete rows
        for row in rows_to_delete:
            # Update indexes
            self.indexes[table_name].delete(row, row['_row_id'])
            
            # Remove from data
            self.data[table_name].remove(row)
        
        if rows_to_delete:
            self._save_table_data(table_name)
        
        return len(rows_to_delete)
    
    def create_index(self, table_name: str, columns, index_name: Optional[str] = None):
        """Create an index on one or more columns."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")

        if isinstance(columns, str):
            cols = [columns]
        else:
            cols = list(columns)
        if not cols:
            raise ValueError("Index must specify at least one column")

        table = self.tables[table_name]
        for col in cols:
            if not table.get_column(col):
                raise ValueError(f"Column {col} does not exist in table {table_name}")

        # Create index
        index_mgr = self.indexes[table_name]
        index = index_mgr.create_index(cols, name=index_name)

        # Build index from existing data
        for row in self.data[table_name]:
            key_parts = []
            missing = False
            for col in cols:
                if col not in row:
                    missing = True
                    break
                key_parts.append(row.get(col))
            if missing or any(v is None for v in key_parts):
                continue
            key = key_parts[0] if len(key_parts) == 1 else tuple(key_parts)
            index.insert(key, row['_row_id'])

        # Persist updated schema (includes indexes metadata)
        self._save_table_schema(self.tables[table_name])

    def _unqualify_column(self, name: str) -> str:
        return name.split('.')[-1]

    def _extract_equality_conditions(self, condition: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract simple equality predicates from a WHERE condition tree.

        Supports:
        - single condition: {'column': 'a', 'operator': '=', 'value': 1}
        - AND-chains: {'conditions': [...], 'operators': ['AND', ...]}
        """
        if not condition:
            return None

        if 'column' in condition and condition.get('operator') == '=':
            return {self._unqualify_column(condition['column']): condition.get('value')}

        if 'conditions' in condition:
            ops = condition.get('operators') or []
            if any(op != 'AND' for op in ops):
                return None
            merged: Dict[str, Any] = {}
            for child in condition.get('conditions') or []:
                m = self._extract_equality_conditions(child)
                if not m:
                    return None
                merged.update(m)
            return merged

        return None
    
    def _check_unique_constraints(self, table_name: str, row: Dict[str, Any], exclude_row_id: Optional[int] = None):
        """Check unique constraints for a row"""
        table = self.tables[table_name]
        existing_rows = self.data[table_name]
        
        for col_name in table.unique_columns:
            if col_name not in row or row[col_name] is None:
                continue
            
            value = row[col_name]
            
            for existing_row in existing_rows:
                if exclude_row_id is not None and existing_row['_row_id'] == exclude_row_id:
                    continue
                
                if existing_row.get(col_name) == value:
                    raise ValueError(f"Unique constraint violation on column {col_name}")
    
    def _check_foreign_keys(self, table: Table, row: Dict[str, Any]):
        """
        Check foreign key constraints for a row.
        
        Validates that all foreign key values reference existing rows
        in the referenced table's referenced column.
        
        Args:
            table: Table schema containing foreign key definitions
            row: Row data to validate
            
        Raises:
            ValueError: If foreign key constraint is violated
        """
        for column in table.columns:
            if column.foreign_key:
                ref_table, ref_column = column.foreign_key
                value = row.get(column.name)
                
                # NULL values are allowed unless NOT NULL constraint
                if value is None:
                    if column.not_null:
                        raise ValueError(f"Foreign key column {column.name} cannot be NULL")
                    continue
                
                # Check if referenced table exists
                if ref_table not in self.tables:
                    raise ValueError(f"Referenced table {ref_table} does not exist")
                
                # Check if value exists in referenced table
                ref_rows = self.data[ref_table]
                value_exists = any(ref_row.get(ref_column) == value for ref_row in ref_rows)
                
                if not value_exists:
                    raise ValueError(
                        f"Foreign key constraint violation: "
                        f"Value {value} does not exist in {ref_table}.{ref_column}"
                    )
    
    def _apply_on_delete_actions(self, table_name: str, rows_to_delete: List[Dict], pk_column: str):
        """Apply ON DELETE actions for foreign key references.

        Default behavior is RESTRICT (existing behavior): prevent deletes when referenced.
        Supported actions:
        - RESTRICT: raise if referenced
        - CASCADE: delete referencing rows
        - SET NULL: set referencing FK columns to NULL (if allowed)
        """
        if not rows_to_delete:
            return

        pk_values = {row[pk_column] for row in rows_to_delete}
        if not pk_values:
            return

        for other_table_name, other_table in self.tables.items():
            if other_table_name == table_name:
                continue

            for column in other_table.columns:
                if not column.foreign_key:
                    continue
                ref_table, ref_column = column.foreign_key
                if ref_table != table_name or ref_column != pk_column:
                    continue

                # Identify referencing rows
                other_rows = self.data[other_table_name]
                has_refs = any(other_row.get(column.name) in pk_values for other_row in other_rows)
                if not has_refs:
                    continue

                action = (column.foreign_key_on_delete or 'RESTRICT').upper()
                if action == 'RESTRICT':
                    raise ValueError(
                        f"Cannot delete from {table_name}: "
                        f"row is referenced by {other_table_name}.{column.name}"
                    )

                if action == 'SET NULL':
                    if column.not_null:
                        raise ValueError(
                            f"Cannot SET NULL on {other_table_name}.{column.name}: column is NOT NULL"
                        )
                    cond = self._build_or_equals_condition(column.name, pk_values)
                    self.update_rows(other_table_name, {column.name: None}, cond)
                    continue

                if action == 'CASCADE':
                    cond = self._build_or_equals_condition(column.name, pk_values)
                    self.delete_rows(other_table_name, cond)
                    continue

                raise ValueError(f"Unsupported ON DELETE action: {action}")

    def _build_or_equals_condition(self, column_name: str, values) -> Dict[str, Any]:
        values_list = list(values)
        if len(values_list) == 1:
            return {'column': column_name, 'operator': '=', 'value': values_list[0]}
        conditions = [{'column': column_name, 'operator': '=', 'value': v} for v in values_list]
        return {'conditions': conditions, 'operators': ['OR'] * (len(conditions) - 1)}
    
    def _matches_condition(self, row: Dict[str, Any], condition: Dict[str, Any], table_name: str) -> bool:
        """Check if a row matches a condition"""
        if 'conditions' in condition:
            # Multiple conditions with AND/OR
            results = []
            for cond in condition['conditions']:
                results.append(self._matches_condition(row, cond, table_name))
            
            # Apply logical operators
            result = results[0]
            for i, op in enumerate(condition['operators']):
                if op == 'AND':
                    result = result and results[i + 1]
                elif op == 'OR':
                    result = result or results[i + 1]
            
            return result
        
        # Single condition
        column = condition['column']
        operator = condition['operator']
        value = condition['value']
        
        # Get column definition for type conversion
        table = self.tables[table_name]
        col_def = table.get_column(column)
        
        if column not in row:
            return False
        
        row_value = row[column]
        
        # Convert value to proper type
        if col_def:
            try:
                value = col_def.convert(value)
            except:
                pass
        
        # Compare
        if operator == '=':
            return row_value == value
        elif operator == '!=':
            return row_value != value
        elif operator == '<':
            return row_value < value
        elif operator == '>':
            return row_value > value
        elif operator == '<=':
            return row_value <= value
        elif operator == '>=':
            return row_value >= value
        elif operator == 'LIKE':
            # Simple LIKE implementation (% as wildcard)
            import re
            pattern = value.replace('%', '.*')
            return re.match(f'^{pattern}$', str(row_value), re.IGNORECASE) is not None
        
        return False
    
    def _remove_internal_fields(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Remove internal fields from a row"""
        return {k: v for k, v in row.items() if not k.startswith('_')}
    
    def _save_table_schema(self, table: Table):
        """Save table schema to disk"""
        schema_file = self.data_dir / f"{table.name}.schema.json"
        with open(schema_file, 'w') as f:
            data = table.to_dict()
            # Persist indexes so they can be rebuilt on restart (including composite indexes)
            idx_mgr = self.indexes.get(table.name)
            if idx_mgr:
                data['indexes'] = [
                    {'name': idx.name, 'columns': list(idx.columns)} for idx in idx_mgr.list_indexes()
                ]
            json.dump(data, f, indent=2)
    
    def _save_table_data(self, table_name: str):
        """Save table data to disk with atomic write"""
        data_file = self.data_dir / f"{table_name}.data.json"
        temp_file = self.data_dir / f"{table_name}.data.json.tmp"
        
        # Write to temporary file first
        with open(temp_file, 'w') as f:
            json.dump({
                'rows': self.data[table_name],
                'next_row_id': self.next_row_ids[table_name]
            }, f, indent=2, default=str)
        
        # Atomic rename - prevents corruption if power fails mid-write
        import os
        import time
        # On Windows, file indexers/AV can transiently lock files causing PermissionError.
        # Retry a few times to make saves reliable under normal desktop environments.
        for attempt in range(6):
            try:
                os.replace(temp_file, data_file)
                break
            except PermissionError:
                if attempt >= 5:
                    raise
                time.sleep(0.05 * (attempt + 1))
    
    def _load_all_tables(self):
        """Load all tables from disk"""
        if not self.data_dir.exists():
            return
        
        # Load all schema files
        for schema_file in self.data_dir.glob("*.schema.json"):
            table_name = schema_file.stem.replace('.schema', '')
            
            # Load schema
            try:
                with open(schema_file, 'r') as f:
                    schema_data = json.load(f)
                    table = Table.from_dict(schema_data)
                    self.tables[table_name] = table
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"WARNING: Skipping corrupt table '{table_name}': {e}")
                continue
            
            # Load data
            data_file = self.data_dir / f"{table_name}.data.json"
            if data_file.exists():
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    self.data[table_name] = data.get('rows', [])
                    self.next_row_ids[table_name] = data.get('next_row_id', 0)
            else:
                self.data[table_name] = []
                self.next_row_ids[table_name] = 0
            
            # Rebuild indexes
            index_mgr = IndexManager()
            if table.primary_key:
                index_mgr.create_index(table.primary_key, name=table.primary_key)
            for col_name in table.unique_columns:
                if col_name != table.primary_key:
                    index_mgr.create_index(col_name, name=col_name)

            # Load any additional indexes from schema (e.g. CREATE INDEX)
            for idx in schema_data.get('indexes', []) or []:
                try:
                    index_mgr.create_index(idx.get('columns') or [], name=idx.get('name'))
                except Exception:
                    # Be conservative: skip invalid index definitions.
                    continue
            
            # Populate indexes
            for row in self.data[table_name]:
                index_mgr.insert(row, row['_row_id'])
            
            self.indexes[table_name] = index_mgr
    
    def list_tables(self) -> List[str]:
        """List all tables"""
        return list(self.tables.keys())
    
    def get_system_tables_info(self) -> List[Dict[str, Any]]:
        """Get metadata about all tables (virtual sys_tables)"""
        result = []
        for table_name, table in self.tables.items():
            result.append({
                'table_name': table_name,
                'column_count': len(table.columns),
                'row_count': len(self.data.get(table_name, [])),
                'has_primary_key': table.primary_key is not None,
                'primary_key': table.primary_key,
                'created_at': table.created_at.isoformat()
            })
        return result
    
    def get_system_indexes_info(self) -> List[Dict[str, Any]]:
        """Get metadata about all indexes (virtual sys_indexes)"""
        result = []
        for table_name, index_mgr in self.indexes.items():
            for col_name, btree in index_mgr.indexes.items():
                result.append({
                    'table_name': table_name,
                    'column_name': col_name,
                    'index_type': 'B-Tree',
                    'is_unique': col_name in self.tables[table_name].unique_columns or col_name == self.tables[table_name].primary_key
                })
        return result

