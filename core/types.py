"""
Data type definitions for the RDBMS

This module defines the type system for SimpleSQLDB, including:
- Supported data types (INT, VARCHAR, FLOAT, DATE, BOOLEAN)
- Column definitions with constraints
- Type validation and conversion utilities
- Data type compatibility checking

Type System Architecture:
    - DataType enum: Defines all supported types
    - Column class: Represents a table column with its properties
    - TypeValidator: Validates and converts values to proper types
"""
from enum import Enum
from typing import Any, Optional, Union
from datetime import datetime, date
import re


class DataType(Enum):
    """
    Enumeration of supported data types in SimpleSQLDB.
    
    Types:
        INT: 32/64-bit integer (-2^31 to 2^31-1)
        VARCHAR: Variable-length string with optional length limit
        FLOAT: Floating-point decimal number
        DATE: Calendar date (YYYY-MM-DD)
        BOOLEAN: True/False logical value
    """
    INT = "INT"
    VARCHAR = "VARCHAR"
    FLOAT = "FLOAT"
    DATE = "DATE"
    BOOLEAN = "BOOLEAN"
    
    @classmethod
    def is_valid(cls, type_name: str) -> bool:
        """
        Check if a type name is valid.
        
        Args:
            type_name: String representation of type (case-insensitive)
            
        Returns:
            True if type is supported, False otherwise
        """
        try:
            cls[type_name.upper()]
            return True
        except KeyError:
            return False


class Column:
    """
    Represents a single column in a table with its properties and constraints.
    
    This class manages:
    - Column metadata (name, data type, length)
    - Constraints (PRIMARY KEY, UNIQUE, NOT NULL, FOREIGN KEY)
    - Type validation and conversion
    - Serialization for storage
    
    Attributes:
        name: Column identifier
        data_type: DataType enum value
        length: Maximum length for VARCHAR (None = unlimited)
        primary_key: Whether this is a primary key (implies NOT NULL and UNIQUE)
        unique: Whether column must have unique values
        not_null: Whether NULL values are prohibited
        foreign_key: Tuple of (table_name, column_name) if this references another table
        created_at: Timestamp when column was defined
    """
    
    def __init__(self, name: str, data_type: DataType, length: Optional[int] = None,
                 primary_key: bool = False, unique: bool = False, not_null: bool = False,
                 foreign_key: Optional[tuple] = None):
        """
        Initialize a column definition.
        
        Args:
            name: Column name (must be valid identifier)
            data_type: DataType enum value
            length: Max length for VARCHAR, None for unlimited
            primary_key: If True, column is primary key (implies NOT NULL)
            unique: If True, column values must be unique
            not_null: If True, column cannot accept NULL values
            foreign_key: Tuple of (table_name, column_name) for foreign key reference
            
        Raises:
            ValueError: If name is invalid or constraints are contradictory
        """
        # Validate column name
        if not name or not name.replace('_', '').isalnum():
            raise ValueError(f"Invalid column name: {name}")
        
        self.name = name
        self.data_type = data_type
        self.length = length
        self.primary_key = primary_key
        self.unique = unique
        # Primary keys are always NOT NULL
        self.not_null = not_null or primary_key
        self.foreign_key = foreign_key
        
        # Validate constraints
        if length is not None and data_type != DataType.VARCHAR:
            raise ValueError(f"Length constraint only valid for VARCHAR, not {data_type.value}")
        
        self.created_at = datetime.now()
        
    def validate(self, value: Any) -> bool:
        """
        Validate if a value matches this column's type and constraints.
        
        This performs preliminary validation without type conversion.
        
        Args:
            value: Value to validate
            
        Returns:
            True if value is valid for this column, False otherwise
            
        Examples:
            >>> col = Column('age', DataType.INT, not_null=True)
            >>> col.validate(25)  # Returns True
            >>> col.validate(None)  # Returns False (NOT NULL)
        """
        if value is None:
            return not self.not_null
            
        try:
            self.convert(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def convert(self, value: Any) -> Any:
        """
        Convert and validate a value to this column's data type.
        
        Performs type conversion and constraint checking. Handles various
        input formats and intelligently converts between compatible types.
        
        Args:
            value: Value to convert
            
        Returns:
            Converted value in proper type
            
        Raises:
            ValueError: If value cannot be converted or violates constraints
            TypeError: If value is fundamentally incompatible
            
        Examples:
            >>> col = Column('age', DataType.INT, not_null=False)
            >>> col.convert('25')  # Returns 25 (int)
            >>> col.convert(None)  # Returns None
        """
        # Handle NULL values
        if value is None:
            if self.not_null:
                raise ValueError(f"Column '{self.name}' cannot be NULL (NOT NULL constraint)")
            return None
        
        # Type conversion based on data type
        if self.data_type == DataType.INT:
            # Convert to integer, accepting string representations
            try:
                return int(float(value)) if isinstance(value, str) and '.' in value else int(value)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert '{value}' to INT")
        
        elif self.data_type == DataType.FLOAT:
            # Convert to float, accepting integer inputs
            try:
                return float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert '{value}' to FLOAT")
        
        elif self.data_type == DataType.VARCHAR:
            # Convert to string with length validation
            str_val = str(value)
            if self.length and len(str_val) > self.length:
                raise ValueError(
                    f"VARCHAR value length {len(str_val)} exceeds maximum {self.length} "
                    f"for column '{self.name}'"
                )
            return str_val
        
        elif self.data_type == DataType.DATE:
            # Handle date conversion from various formats
            if isinstance(value, date):
                return value
            
            # Try parsing common date formats
            date_formats = [
                '%Y-%m-%d',     # ISO 8601 (standard)
                '%Y/%m/%d',     # Slash separator
                '%d-%m-%Y',     # DD-MM-YYYY
                '%d/%m/%Y',     # DD/MM/YYYY
                '%m-%d-%Y',     # MM-DD-YYYY
                '%B %d, %Y',    # Full date
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(str(value), fmt).date()
                except ValueError:
                    continue
            
            raise ValueError(
                f"Invalid date format for '{value}'. Expected YYYY-MM-DD or similar format"
            )
        
        elif self.data_type == DataType.BOOLEAN:
            # Convert various representations to boolean
            if isinstance(value, bool):
                return value
            
            str_val = str(value).lower()
            if str_val in ('true', '1', 'yes', 't', 'y', 'on'):
                return True
            elif str_val in ('false', '0', 'no', 'f', 'n', 'off'):
                return False
            
            raise ValueError(
                f"Cannot convert '{value}' to BOOLEAN. "
                f"Expected: true/false, yes/no, 1/0, or t/f"
            )
        
        # Default: return as-is (should not reach here)
        return value
    
    def to_dict(self) -> dict:
        """
        Serialize column definition to dictionary for storage.
        
        Used for persisting table schema to disk. Includes all column
        metadata and constraint information.
        
        Returns:
            Dictionary representation with all column properties
        """
        result = {
            'name': self.name,
            'data_type': self.data_type.value,
            'length': self.length,
            'primary_key': self.primary_key,
            'unique': self.unique,
            'not_null': self.not_null,
            'created_at': self.created_at.isoformat()
        }
        if self.foreign_key:
            result['foreign_key'] = {
                'table': self.foreign_key[0],
                'column': self.foreign_key[1]
            }
        return result
    
    @staticmethod
    def from_dict(data: dict) -> 'Column':
        """
        Deserialize column definition from dictionary.
        
        Reconstructs a Column object from its serialized form,
        used when loading table schemas from disk.
        
        Args:
            data: Dictionary with column properties
            
        Returns:
            Reconstructed Column object
            
        Raises:
            KeyError: If required fields are missing
            ValueError: If data is invalid
        """
        foreign_key = None
        if 'foreign_key' in data:
            fk = data['foreign_key']
            foreign_key = (fk['table'], fk['column'])
        
        return Column(
            name=data['name'],
            data_type=DataType(data['data_type']),
            length=data.get('length'),
            primary_key=data.get('primary_key', False),
            unique=data.get('unique', False),
            not_null=data.get('not_null', False),
            foreign_key=foreign_key
        )
    
    def __repr__(self) -> str:
        """
        Generate SQL column definition string.
        
        Used for displaying column information and debugging.
        Example output: "name VARCHAR(100) NOT NULL"
        
        Returns:
            SQL-style column definition
        """
        type_str = self.data_type.value
        if self.length:
            type_str += f"({self.length})"
        
        # Collect constraint strings
        constraints = []
        if self.primary_key:
            constraints.append("PRIMARY KEY")
        if self.unique and not self.primary_key:  # Avoid redundant UNIQUE
            constraints.append("UNIQUE")
        if self.not_null and not self.primary_key:  # Avoid redundant NOT NULL
            constraints.append("NOT NULL")
        if self.foreign_key:
            constraints.append(f"REFERENCES {self.foreign_key[0]}({self.foreign_key[1]})")
        
        constraint_str = " " + " ".join(constraints) if constraints else ""
        return f"{self.name} {type_str}{constraint_str}"
    
    def __eq__(self, other) -> bool:
        """Check if two columns are equal."""
        if not isinstance(other, Column):
            return False
        return (self.name == other.name and 
                self.data_type == other.data_type and
                self.length == other.length)
