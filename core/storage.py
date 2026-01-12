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
        self.data_dir.mkdir(exist_ok=True)
        
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
        
        # Update indexes with new row
        self.indexes[table_name].insert(validated_row, row_id)
        
        # Persist to disk
        self._save_table_data(table_name)
        
        # Update row count metadata
        table.row_count += 1
        
        return row_id
    
    def select_rows(self, table_name: str, condition: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Select rows from a table"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        rows = self.data[table_name]
        
        if condition is None:
            return [self._remove_internal_fields(row) for row in rows]
        
        # Try to use index if available
        if 'column' in condition and condition['operator'] == '=':
            column = condition['column']
            value = condition['value']
            
            # Convert value to proper type
            col_def = self.tables[table_name].get_column(column)
            if col_def:
                try:
                    value = col_def.convert(value)
                except:
                    pass
            
            index_mgr = self.indexes[table_name]
            if index_mgr.has_index(column):
                # Use index
                index = index_mgr.get_index(column)
                row_ids = index.search(value)
                matching_rows = [row for row in rows if row['_row_id'] in row_ids]
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
        
        # Check if any rows are referenced by foreign keys
        if table.primary_key:
            self._check_referential_integrity(table_name, rows_to_delete, table.primary_key)
        
        # Delete rows
        for row in rows_to_delete:
            # Update indexes
            self.indexes[table_name].delete(row, row['_row_id'])
            
            # Remove from data
            self.data[table_name].remove(row)
        
        if rows_to_delete:
            self._save_table_data(table_name)
        
        return len(rows_to_delete)
    
    def create_index(self, table_name: str, column_name: str):
        """Create an index on a column"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        table = self.tables[table_name]
        if not table.get_column(column_name):
            raise ValueError(f"Column {column_name} does not exist in table {table_name}")
        
        # Create index
        index_mgr = self.indexes[table_name]
        index = index_mgr.create_index(column_name)
        
        # Build index from existing data
        for row in self.data[table_name]:
            if column_name in row:
                index.insert(row[column_name], row['_row_id'])
    
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
    
    def _check_referential_integrity(self, table_name: str, rows_to_delete: List[Dict], pk_column: str):
        """
        Check if deleting rows would violate foreign key constraints.
        
        Prevents deletion of rows that are referenced by foreign keys in other tables.
        
        Args:
            table_name: Table from which rows are being deleted
            rows_to_delete: List of rows to delete
            pk_column: Primary key column name
            
        Raises:
            ValueError: If deletion would violate foreign key constraint
        """
        # Get primary key values being deleted
        pk_values = {row[pk_column] for row in rows_to_delete}
        
        # Check all other tables for foreign key references
        for other_table_name, other_table in self.tables.items():
            if other_table_name == table_name:
                continue
            
            # Check if this table has foreign keys referencing the table being deleted from
            for column in other_table.columns:
                if column.foreign_key:
                    ref_table, ref_column = column.foreign_key
                    if ref_table == table_name and ref_column == pk_column:
                        # Found a foreign key reference - check if any rows reference deleted values
                        other_rows = self.data[other_table_name]
                        for other_row in other_rows:
                            fk_value = other_row.get(column.name)
                            if fk_value in pk_values:
                                raise ValueError(
                                    f"Cannot delete from {table_name}: "
                                    f"row is referenced by {other_table_name}.{column.name}"
                                )
    
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
            json.dump(table.to_dict(), f, indent=2)
    
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
        os.replace(temp_file, data_file)
    
    def _load_all_tables(self):
        """Load all tables from disk"""
        if not self.data_dir.exists():
            return
        
        # Load all schema files
        for schema_file in self.data_dir.glob("*.schema.json"):
            table_name = schema_file.stem.replace('.schema', '')
            
            # Load schema
            with open(schema_file, 'r') as f:
                schema_data = json.load(f)
                table = Table.from_dict(schema_data)
                self.tables[table_name] = table
            
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
                index_mgr.create_index(table.primary_key)
            for col_name in table.unique_columns:
                if col_name != table.primary_key:
                    index_mgr.create_index(col_name)
            
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

