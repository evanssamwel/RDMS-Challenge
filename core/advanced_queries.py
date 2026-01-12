"""
Advanced Query Features - GROUP BY, HAVING, Aggregates

This module extends the SQL engine with advanced query capabilities:

    GROUP BY Functionality:
    - Groups rows by one or more columns
    - Aggregate functions computed per group
    - Reduces result set to one row per group
    
    HAVING Clause:
    - Filters groups after aggregation
    - Similar to WHERE but operates on aggregate results
    - Allows filtering by aggregate values
    
    Aggregate Functions:
    - COUNT(*), COUNT(col): Row count
    - SUM(col): Sum of values
    - AVG(col): Average of values
    - MAX(col): Maximum value
    - MIN(col): Minimum value
    
    Example Queries:
    - SELECT category, COUNT(*) FROM products GROUP BY category;
    - SELECT dept, AVG(salary) FROM employees 
      GROUP BY dept HAVING AVG(salary) > 50000;
    
    Implementation:
    - Aggregates computed during query execution
    - Supports multiple aggregates in single query
    - Efficient grouping with dictionary-based accumulators
"""
from typing import Any, List, Optional, Dict, Tuple
from enum import Enum


class AggregateType(Enum):
    """Enumeration of aggregate function types"""
    COUNT = "COUNT"       # Count rows or non-NULL values
    SUM = "SUM"           # Sum numeric values
    AVG = "AVG"           # Average numeric values
    MAX = "MAX"           # Maximum value
    MIN = "MIN"           # Minimum value


class AggregateFunction:
    """
    Aggregate function implementation.
    
    Aggregates process multiple rows to produce a single result value.
    Used in GROUP BY queries to compute statistics per group.
    
    Attributes:
        func_type: Type of aggregate (COUNT, SUM, AVG, MAX, MIN)
        column: Column being aggregated (None for COUNT(*))
        accumulator: Internal state for computation
        count: Number of values processed (for averaging)
    """
    
    def __init__(self, func_type: AggregateType, column: Optional[str] = None):
        """
        Initialize aggregate function.
        
        Args:
            func_type: Type of aggregate function
            column: Column name to aggregate (None for COUNT(*))
        """
        self.func_type = func_type
        self.column = column
        self.accumulator = None
        self.count = 0
    
    def add(self, value: Any):
        """
        Process a single value in the aggregation.
        
        Args:
            value: Column value from current row
        """
        if self.func_type == AggregateType.COUNT:
            # COUNT(*) counts all rows, COUNT(col) counts non-NULL
            if self.column is None or value is not None:
                self.count += 1
        
        elif self.func_type == AggregateType.SUM:
            if value is not None:
                if self.accumulator is None:
                    self.accumulator = 0
                self.accumulator += float(value)
        
        elif self.func_type == AggregateType.AVG:
            if value is not None:
                if self.accumulator is None:
                    self.accumulator = 0
                self.accumulator += float(value)
                self.count += 1
        
        elif self.func_type == AggregateType.MAX:
            if value is not None:
                if self.accumulator is None:
                    self.accumulator = value
                else:
                    self.accumulator = max(self.accumulator, value)
        
        elif self.func_type == AggregateType.MIN:
            if value is not None:
                if self.accumulator is None:
                    self.accumulator = value
                else:
                    self.accumulator = min(self.accumulator, value)
    
    def get_result(self) -> Any:
        """
        Get final aggregated result.
        
        Returns:
            Final aggregate value
        """
        if self.func_type == AggregateType.COUNT:
            return self.count
        elif self.func_type == AggregateType.AVG:
            if self.count == 0:
                return None
            return self.accumulator / self.count
        else:
            return self.accumulator
    
    def __repr__(self) -> str:
        """String representation"""
        if self.column:
            return f"{self.func_type.value}({self.column})"
        else:
            return f"{self.func_type.value}(*)"
