"""
Aggregate Functions - COUNT, SUM, AVG, MAX, MIN

This module implements SQL aggregate functions:

    Aggregate Functions:
    - COUNT(*): Number of rows
    - COUNT(column): Number of non-NULL values
    - SUM(column): Sum of numeric values
    - AVG(column): Average of numeric values
    - MAX(column): Maximum value
    - MIN(column): Minimum value
    
    Typical Use:
        SELECT COUNT(*) FROM users
        SELECT AVG(age), MAX(salary) FROM employees WHERE department = 'IT'
        SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id
    
    Complexity:
    - Simple aggregates: O(n) full table scan
    - With GROUP BY: O(n log n) sort or hash grouping
    - Future: Index-accelerated aggregates
"""
from typing import Any, List, Dict, Optional, Union
from core.types import DataType


class AggregateFunction:
    """
    Base class for aggregate functions.
    
    Aggregate functions reduce multiple rows to a single value:
    - Accumulate: Process each row value
    - Finalize: Return the aggregate result
    
    Attributes:
        name: Function name (COUNT, SUM, etc.)
        column: Column being aggregated (None for COUNT(*))
        distinct: Whether to count only distinct values
    """
    
    def __init__(self, name: str, column: Optional[str] = None, distinct: bool = False):
        """
        Initialize aggregate function.
        
        Args:
            name: Function name
            column: Column to aggregate
            distinct: Count only unique values
        """
        self.name = name.upper()
        self.column = column
        self.distinct = distinct
        self.values = []  # Accumulated values
        self.count = 0    # Row count
    
    def accumulate(self, value: Any):
        """
        Add a value to the aggregate.
        
        Called for each row during aggregation.
        
        Args:
            value: Value from current row
        """
        raise NotImplementedError
    
    def finalize(self) -> Any:
        """
        Return the final aggregate result.
        
        Called after all rows processed.
        
        Returns:
            Computed aggregate value
        """
        raise NotImplementedError
    
    def reset(self):
        """Reset aggregate for next group."""
        self.values = []
        self.count = 0


class CountAggregate(AggregateFunction):
    """
    COUNT aggregate function.
    
    Counts rows or non-NULL values:
    - COUNT(*): All rows
    - COUNT(column): Non-NULL column values
    - COUNT(DISTINCT column): Unique non-NULL values
    
    Examples:
        COUNT(*) -> 100  (total rows)
        COUNT(age) -> 95  (non-NULL ages)
        COUNT(DISTINCT department) -> 8  (unique departments)
    """
    
    def __init__(self, column: Optional[str] = None, distinct: bool = False):
        super().__init__('COUNT', column, distinct)
        self.unique_values = set()
    
    def accumulate(self, value: Any):
        """Count the value if not NULL."""
        if self.column is None:
            # COUNT(*) counts all rows
            self.count += 1
        elif value is not None:
            # COUNT(column) counts non-NULL
            if self.distinct:
                self.unique_values.add(value)
            self.count += 1
    
    def finalize(self) -> int:
        """Return count."""
        if self.distinct:
            return len(self.unique_values)
        return self.count


class SumAggregate(AggregateFunction):
    """
    SUM aggregate function.
    
    Sums numeric values:
    - Ignores NULL values
    - Returns NULL if all values are NULL
    - Only for INT and FLOAT types
    
    Examples:
        SUM(salary) -> 250000.50
        SUM(quantity) -> 1000
    """
    
    def __init__(self, column: str):
        super().__init__('SUM', column)
        self.total = 0
        self.has_value = False
    
    def accumulate(self, value: Any):
        """Add value to sum."""
        if value is not None:
            try:
                self.total += float(value)
                self.has_value = True
            except (TypeError, ValueError):
                pass  # Skip non-numeric values
    
    def finalize(self) -> Union[float, None]:
        """Return sum or NULL."""
        return self.total if self.has_value else None


class AvgAggregate(AggregateFunction):
    """
    AVG aggregate function.
    
    Calculates average of numeric values:
    - Ignores NULL values
    - Returns NULL if no non-NULL values
    - Result is floating point
    
    Examples:
        AVG(age) -> 35.5
        AVG(price) -> 99.99
    """
    
    def __init__(self, column: str):
        super().__init__('AVG', column)
        self.total = 0
        self.count = 0
    
    def accumulate(self, value: Any):
        """Add value to average calculation."""
        if value is not None:
            try:
                self.total += float(value)
                self.count += 1
            except (TypeError, ValueError):
                pass
    
    def finalize(self) -> Union[float, None]:
        """Return average or NULL."""
        return self.total / self.count if self.count > 0 else None


class MaxAggregate(AggregateFunction):
    """
    MAX aggregate function.
    
    Finds maximum value:
    - Works with any comparable type
    - Ignores NULL values
    - Returns NULL if all values NULL
    
    Examples:
        MAX(salary) -> 150000
        MAX(name) -> "Zoe" (lexicographic)
        MAX(hire_date) -> 2024-01-15
    """
    
    def __init__(self, column: str):
        super().__init__('MAX', column)
        self.max_value = None
    
    def accumulate(self, value: Any):
        """Update maximum."""
        if value is not None:
            if self.max_value is None or value > self.max_value:
                self.max_value = value
    
    def finalize(self) -> Any:
        """Return maximum value."""
        return self.max_value


class MinAggregate(AggregateFunction):
    """
    MIN aggregate function.
    
    Finds minimum value:
    - Works with any comparable type
    - Ignores NULL values
    - Returns NULL if all values NULL
    
    Examples:
        MIN(salary) -> 25000
        MIN(name) -> "Alice" (lexicographic)
        MIN(hire_date) -> 2020-03-01
    """
    
    def __init__(self, column: str):
        super().__init__('MIN', column)
        self.min_value = None
    
    def accumulate(self, value: Any):
        """Update minimum."""
        if value is not None:
            if self.min_value is None or value < self.min_value:
                self.min_value = value
    
    def finalize(self) -> Any:
        """Return minimum value."""
        return self.min_value


class AggregateBuilder:
    """
    Factory for creating aggregate function objects.
    
    Helper class to create appropriate aggregate function instances
    from function names and column specifications.
    
    Example:
        builder = AggregateBuilder()
        count_all = builder.build('COUNT', None)
        sum_salary = builder.build('SUM', 'salary')
    """
    
    @staticmethod
    def build(function_name: str, column: Optional[str] = None, 
              distinct: bool = False) -> AggregateFunction:
        """
        Build appropriate aggregate function.
        
        Args:
            function_name: Name of function (case-insensitive)
            column: Column to aggregate
            distinct: Use DISTINCT modifier
            
        Returns:
            Appropriate AggregateFunction subclass
            
        Raises:
            ValueError: If function not supported
        """
        func_upper = function_name.upper()
        
        if func_upper == 'COUNT':
            return CountAggregate(column, distinct)
        elif func_upper == 'SUM':
            if column is None:
                raise ValueError("SUM requires a column")
            return SumAggregate(column)
        elif func_upper == 'AVG':
            if column is None:
                raise ValueError("AVG requires a column")
            return AvgAggregate(column)
        elif func_upper == 'MAX':
            if column is None:
                raise ValueError("MAX requires a column")
            return MaxAggregate(column)
        elif func_upper == 'MIN':
            if column is None:
                raise ValueError("MIN requires a column")
            return MinAggregate(column)
        else:
            raise ValueError(f"Unknown aggregate function: {function_name}")
