"""
Schema management for tables

This module provides table schema definition and management:
- Table class: Represents a complete table with all column definitions
- Schema validation: Ensures data conforms to table schema
- Metadata management: Manages table-level constraints and properties

Table Schema Architecture:
    - Tables contain columns with specific types and constraints
    - Primary key constraint enforces uniqueness
    - Unique constraints enforce column-level uniqueness
    - NOT NULL constraints require non-null values
    - Foreign key support can be added for referential integrity
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import ast
import operator
from core.types import Column


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _safe_eval_expr(expr: str, env: Dict[str, Any]) -> Any:
    """Safely evaluate a limited expression for generated columns.

    Supported:
    - constants (numbers, strings, booleans, NULL as None isn't supported directly)
    - column references by name
    - arithmetic + - * / %
    - unary + -

    Disallowed:
    - function calls, attribute access, subscripts, comprehensions, etc.
    """
    tree = ast.parse(expr, mode='eval')

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise KeyError(node.id)
            return env[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            left = _eval(node.left)
            right = _eval(node.right)
            return _BIN_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](_eval(node.operand))
        raise ValueError("Unsupported expression in generated column")

    return _eval(tree)


class Table:
    """
    Represents a database table with its complete schema definition.
    
    A table consists of:
    - Column definitions: Type, constraints, metadata for each column
    - Primary key: Single column that uniquely identifies each row
    - Unique constraints: Columns that must have unique values
    - Row data: Actual data stored in this table
    
    This class manages schema-level operations like validation and
    constraint checking. Data operations are handled by Storage.
    
    Attributes:
        name: Table identifier (must be unique in database)
        columns: List of Column objects defining table structure
        column_map: Dictionary for fast column lookup by name
        primary_key: Name of primary key column (or None)
        unique_columns: List of column names with UNIQUE constraint
        created_at: Timestamp when table was created
        row_count: Current number of rows (for metadata)
    """
    
    def __init__(self, name: str, columns: List[Column]):
        """
        Initialize a table with its schema.
        
        Args:
            name: Table name (must be valid identifier)
            columns: List of Column objects
            
        Raises:
            ValueError: If name is invalid or columns are invalid
            
        Note:
            Validates that:
            - Table name is non-empty
            - Exactly one primary key exists (if any)
            - All column names are unique
            - Columns are valid
        """
        if not name or not name.replace('_', '').isalnum():
            raise ValueError(f"Invalid table name: {name}")
        
        if not columns:
            raise ValueError("Table must have at least one column")
        
        self.name = name
        self.columns = columns
        self.column_map = {col.name: col for col in columns}
        
        # Validate column names are unique
        if len(self.column_map) != len(columns):
            raise ValueError("Duplicate column names in table definition")
        
        # Identify special columns
        primary_keys = [col.name for col in columns if col.primary_key]
        if len(primary_keys) > 1:
            raise ValueError("Table can have at most one primary key")
        self.primary_key = primary_keys[0] if primary_keys else None
        
        # Unique columns include primary key
        self.unique_columns = [col.name for col in columns if col.unique or col.primary_key]
        
        self.created_at = datetime.now()
        self.row_count = 0
        
    def validate_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and convert a complete row of data.
        
        Ensures:
        - All columns have valid values for their type
        - NOT NULL constraints are satisfied
        - Data is converted to proper types
        
        Args:
            row: Dictionary mapping column names to values
            
        Returns:
            Validated and type-converted row dictionary
            
        Raises:
            ValueError: If row violates any constraint
            KeyError: If required columns are missing
            
        Note:
            This is a schema-level validation only.
            Uniqueness constraint checking is done at storage level.
        """
        validated: Dict[str, Any] = {}

        # First pass: validate and convert non-generated columns
        for column in self.columns:
            if column.generated_expr:
                continue
            value = row.get(column.name)
            try:
                validated[column.name] = column.convert(value)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Validation error in column '{column.name}': {str(e)}"
                )

        # Second pass: compute generated columns (allow dependencies)
        pending = [c for c in self.columns if c.generated_expr]
        for _ in range(len(pending) + 1):
            if not pending:
                break
            progressed = False
            for column in list(pending):
                try:
                    computed = _safe_eval_expr(column.generated_expr or "", validated)
                except KeyError:
                    continue
                except Exception as e:
                    raise ValueError(
                        f"Validation error in column '{column.name}': {str(e)}"
                    )

                try:
                    validated[column.name] = column.convert(computed)
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"Validation error in column '{column.name}': {str(e)}"
                    )

                pending.remove(column)
                progressed = True

            if not progressed and pending:
                deps = ", ".join(c.name for c in pending)
                raise ValueError(f"Cannot compute generated column(s): {deps}")

        return validated
    
    def get_column(self, name: str) -> Optional[Column]:
        """
        Get column definition by name.
        
        Args:
            name: Column name to look up
            
        Returns:
            Column object if found, None otherwise
        """
        return self.column_map.get(name)
    
    def has_column(self, name: str) -> bool:
        """Check if column exists in table."""
        return name in self.column_map
    
    def get_columns_by_type(self, data_type: type) -> List[Column]:
        """Get all columns of a specific type."""
        from core.types import DataType
        return [col for col in self.columns if col.data_type == data_type]
    
    def to_dict(self) -> dict:
        """
        Serialize table schema to dictionary for storage.
        
        Used for persisting table definitions to disk.
        
        Returns:
            Dictionary with table name and column definitions
        """
        return {
            'name': self.name,
            'columns': [col.to_dict() for col in self.columns],
            'created_at': self.created_at.isoformat(),
            'row_count': self.row_count
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Table':
        """
        Deserialize table schema from dictionary.
        
        Reconstructs a Table object from its stored representation,
        used when loading table definitions from disk.
        
        Args:
            data: Dictionary with table properties
            
        Returns:
            Reconstructed Table object
        """
        columns = [Column.from_dict(col_data) for col_data in data['columns']]
        table = Table(name=data['name'], columns=columns)
        table.row_count = data.get('row_count', 0)
        return table
    
    def __repr__(self) -> str:
        """
        Generate string representation of table schema.
        
        Example:
            Table: users
              id INT PRIMARY KEY
              name VARCHAR(100) NOT NULL
              email VARCHAR(100) UNIQUE
        """
        cols_str = ",\n  ".join(str(col) for col in self.columns)
        return f"Table: {self.name}\n  {cols_str}"
    
    def __str__(self) -> str:
        """Short string representation."""
        return f"Table '{self.name}' with {len(self.columns)} columns"
    
    def __eq__(self, other) -> bool:
        """Check if two tables have the same schema."""
        if not isinstance(other, Table):
            return False
        return self.name == other.name and self.columns == other.columns
