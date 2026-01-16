"""
B-tree Index Implementation for Fast Lookups

This module provides indexed data structure for O(log n) lookups:

    B-tree Properties:
    - Balanced: All leaves at same depth for consistent performance
    - Self-balancing: Maintains balance during inserts/deletes
    - Multi-key nodes: Each node can store multiple keys
    - Suitable for disk-based storage (future enhancement)

Index Architecture:
    
    BTreeIndex:
        ├── Root Node
        ├── Internal Nodes (branching)
        └── Leaf Nodes (data storage)
    
    Each Node:
        - Keys: Sorted index values
        - Values: Row IDs (for leaves) or child pointers (for internal)
        - Is Leaf: Boolean flag
        - Max Keys: Configurable node capacity

Use Cases:
    - PRIMARY KEY lookup: O(log n) instead of O(n) scan
    - UNIQUE constraint checking: Fast duplicate detection
    - Range queries: Efficient range scans
    - Equality conditions in WHERE clauses

Performance:
    - Insert: O(log n)
    - Delete: O(log n)
    - Search: O(log n)
    - Range search: O(log n + result size)

Limitations:
    - Current implementation: Simple B-tree (max_keys=4)
    - Production systems use larger keys (100+)
    - No block-level compression
    - No multi-column indexes (yet)
"""
from dataclasses import dataclass
from typing import Any, Optional, List, Tuple, Dict, Iterable, Union
import bisect


class BTreeNode:
    """
    A single node in the B-tree structure.
    
    Each node contains:
    - Keys: Sorted index values
    - Values: Row IDs (leaf nodes) or None (internal nodes)
    - Children: Pointers to child nodes (internal nodes only)
    - is_leaf: Boolean indicating if this is a leaf node
    
    Node Structure:
        Leaf Node:
            keys: [k1, k2, k3]
            values: [rowid1, rowid2, rowid3]
            children: []
        
        Internal Node:
            keys: [k1, k2]
            children: [child0, child1, child2]
    
    Attributes:
        is_leaf: True if leaf node, False if internal
        keys: List of index key values (sorted)
        values: List of row IDs (for leaves only)
        children: List of child nodes (for internal nodes)
        max_keys: Maximum keys allowed in this node
    """
    
    def __init__(self, is_leaf: bool = True, max_keys: int = 4):
        """
        Initialize a B-tree node.
        
        Args:
            is_leaf: True for leaf nodes, False for internal
            max_keys: Maximum number of keys before split
        """
        self.is_leaf = is_leaf
        self.keys = []        # Sorted key values
        self.values = []      # Row IDs (leaf nodes only)
        self.children = []    # Child nodes (internal nodes)
        self.max_keys = max_keys
    
    def is_full(self) -> bool:
        """Check if node has reached maximum capacity."""
        return len(self.keys) >= self.max_keys


class BTreeIndex:
    """
    B-tree index for efficient data lookups.
    
    Maintains a balanced B-tree structure for O(log n) operations:
    - Insert new (key, row_id) pairs
    - Search for specific key values
    - Range searches (greater than, less than, between)
    - Delete key-value pairs
    
    The index automatically rebalances on inserts/deletes to maintain
    logarithmic performance characteristics.
    
    Attributes:
        column_name: Name of indexed column
        root: Root node of B-tree
        max_keys: Node capacity (default 4 for demo)
        
    Complexity:
        Insert: O(log n)
        Search: O(log n)
        Delete: O(log n)
        Range: O(log n + result_size)
    
    Example:
        >>> index = BTreeIndex('user_id')
        >>> index.insert(5, 0)  # user_id=5, row_id=0
        >>> index.insert(3, 1)  # user_id=3, row_id=1
        >>> results = index.search(5)  # Returns [0]
    """
    
    def __init__(self, column_name: str, max_keys: int = 4):
        """
        Initialize B-tree index.
        
        Args:
            column_name: Column being indexed
            max_keys: Maximum keys per node (higher = deeper tree)
        """
        self.column_name = column_name
        self.root = BTreeNode(is_leaf=True, max_keys=max_keys)
        self.max_keys = max_keys
    
    def insert(self, key: Any, row_id: int):
        """
        Insert a key-value pair into the index.
        
        Steps:
        1. Normalize key for comparison
        2. Check if root is full (split if needed)
        3. Recursively insert into appropriate subtree
        4. Rebalance tree as needed
        
        Args:
            key: Index key value
            row_id: Internal row ID to associate
            
        Note:
            NULL keys are not indexed (typical RDBMS behavior)
        """
        if key is None:
            return  # Don't index NULL values
        
        # Normalize key for consistent comparison
        key = self._normalize_key(key)
        
        root = self.root
        
        # If root is full, create new root and split old root
        if root.is_full():
            new_root = BTreeNode(is_leaf=False, max_keys=self.max_keys)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        
        self._insert_non_full(self.root, key, row_id)
    
    def search(self, key: Any) -> List[int]:
        """
        Search for a specific key value.
        
        Args:
            key: Value to search for
            
        Returns:
            List of row IDs with this key (usually 0 or 1 for unique keys)
        """
        if key is None:
            return []
        
        key = self._normalize_key(key)
        return self._search_node(self.root, key)
    
    def search_range(self, min_key: Any = None, max_key: Any = None) -> List[int]:
        """
        Search for keys within a range.
        
        Args:
            min_key: Minimum key (inclusive), None for unbounded
            max_key: Maximum key (inclusive), None for unbounded
            
        Returns:
            List of row IDs in range
            
        Example:
            index.search_range(min_key=10, max_key=20)  # Keys 10-20
        """
        if min_key is not None:
            min_key = self._normalize_key(min_key)
        if max_key is not None:
            max_key = self._normalize_key(max_key)
        
        results = []
        self._search_range_node(self.root, min_key, max_key, results)
        return results
    
    def delete(self, key: Any, row_id: int):
        """Delete a key-value pair from the index"""
        if key is None:
            return
        
        key = self._normalize_key(key)
        self._delete_from_node(self.root, key, row_id)
    
    def _normalize_key(self, key: Any) -> Any:
        """Normalize key for comparison.

        Supports scalar keys and composite tuple keys.
        """
        if isinstance(key, tuple):
            return tuple(self._normalize_key(k) for k in key)
        if isinstance(key, list):
            return tuple(self._normalize_key(k) for k in key)
        if isinstance(key, str):
            return key.lower()  # Case-insensitive string comparison
        return key
    
    def _insert_non_full(self, node: BTreeNode, key: Any, row_id: int):
        """Insert into a node that is not full"""
        i = len(node.keys) - 1
        
        if node.is_leaf:
            # Insert into leaf node
            node.keys.append(None)
            node.values.append(None)
            
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            
            node.keys[i + 1] = key
            node.values[i + 1] = row_id
        else:
            # Find child to insert into
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            if node.children[i].is_full():
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], key, row_id)
    
    def _split_child(self, parent: BTreeNode, index: int):
        """Split a full child node"""
        full_child = parent.children[index]
        mid = len(full_child.keys) // 2
        
        new_child = BTreeNode(is_leaf=full_child.is_leaf, max_keys=self.max_keys)
        
        # Capture the middle key before modifying the list
        mid_key = full_child.keys[mid]
        
        if full_child.is_leaf:
            # Leaf Split: Keep 'mid' in the right child (Copy Up)
            new_child.keys = full_child.keys[mid:]
            full_child.keys = full_child.keys[:mid]
            
            # Split values
            new_child.values = full_child.values[mid:]
            full_child.values = full_child.values[:mid]
        else:
            # Internal Split: 'mid' moves up (Push Up) and is excluded from children
            new_child.keys = full_child.keys[mid + 1:]
            full_child.keys = full_child.keys[:mid]
            
            # Split children
            new_child.children = full_child.children[mid + 1:]
            full_child.children = full_child.children[:mid + 1]
        
        # Insert middle key into parent
        parent.keys.insert(index, mid_key)
        parent.children.insert(index + 1, new_child)
    
    def _search_node(self, node: BTreeNode, key: Any) -> List[int]:
        """Search for key in a node"""
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if i < len(node.keys) and key == node.keys[i]:
            if node.is_leaf:
                return [node.values[i]]
            else:
                # Continue searching in child
                return self._search_node(node.children[i], key)
        
        if node.is_leaf:
            return []
        else:
            return self._search_node(node.children[i], key)
    
    def _search_range_node(self, node: BTreeNode, min_key: Any, max_key: Any, results: List[int]):
        """Search for keys in range in a node"""
        if node.is_leaf:
            for i, key in enumerate(node.keys):
                if (min_key is None or key >= min_key) and (max_key is None or key <= max_key):
                    results.append(node.values[i])
        else:
            for i, key in enumerate(node.keys):
                if min_key is None or key >= min_key:
                    self._search_range_node(node.children[i], min_key, max_key, results)
                
                if (min_key is None or key >= min_key) and (max_key is None or key <= max_key):
                    # Key itself might have corresponding values in next child
                    pass
            
            # Check last child
            if len(node.children) > len(node.keys):
                self._search_range_node(node.children[-1], min_key, max_key, results)
    
    def _delete_from_node(self, node: BTreeNode, key: Any, row_id: int):
        """Delete key from node (simplified implementation)"""
        if node.is_leaf:
            try:
                idx = node.keys.index(key)
                if node.values[idx] == row_id:
                    node.keys.pop(idx)
                    node.values.pop(idx)
            except (ValueError, IndexError):
                pass


@dataclass(frozen=True)
class IndexDefinition:
    name: str
    columns: Tuple[str, ...]
    index: BTreeIndex


class IndexManager:
    """Manage all indexes for a table.

    Supports:
    - Single-column indexes (backwards compatible with existing APIs)
    - Composite indexes across 2+ columns
    - Named indexes (CREATE INDEX name ON table(colA, colB))
    """

    def __init__(self):
        self._by_name: Dict[str, IndexDefinition] = {}
        self._by_columns: Dict[Tuple[str, ...], IndexDefinition] = {}

    def create_index(self, columns: Union[str, Iterable[str]], name: Optional[str] = None) -> BTreeIndex:
        """Create an index.

        Args:
            columns: Column name (string) or an iterable of column names.
            name: Optional index name.

        Returns:
            The created or existing BTreeIndex.
        """
        if isinstance(columns, str):
            cols = (columns,)
        else:
            cols = tuple(str(c).strip() for c in columns if str(c).strip())
        if not cols:
            raise ValueError("Index must have at least one column")

        idx_name = (name or (cols[0] if len(cols) == 1 else "idx_" + "_".join(cols))).strip()
        if idx_name in self._by_name:
            return self._by_name[idx_name].index
        if cols in self._by_columns:
            # Already exists under a different name; re-use it.
            existing = self._by_columns[cols]
            self._by_name[idx_name] = existing
            return existing.index

        index = BTreeIndex(",".join(cols))
        definition = IndexDefinition(name=idx_name, columns=cols, index=index)
        self._by_name[idx_name] = definition
        self._by_columns[cols] = definition
        return index

    def get_index(self, column_name: str) -> Optional[BTreeIndex]:
        """Get index for a single column (backwards compatible)."""
        definition = self._by_columns.get((column_name,))
        return definition.index if definition else None

    def get_index_by_name(self, name: str) -> Optional[BTreeIndex]:
        definition = self._by_name.get(name)
        return definition.index if definition else None

    def get_index_for_columns(self, columns: Iterable[str]) -> Optional[BTreeIndex]:
        cols = tuple(columns)
        definition = self._by_columns.get(cols)
        return definition.index if definition else None

    def get_index_definition_for_columns(self, columns: Iterable[str]) -> Optional[IndexDefinition]:
        cols = tuple(columns)
        return self._by_columns.get(cols)

    def list_indexes(self) -> List[IndexDefinition]:
        # Unique by columns
        return list(self._by_columns.values())

    def has_index(self, column_name: str) -> bool:
        """Check if a single-column index exists (backwards compatible)."""
        return (column_name,) in self._by_columns

    def insert(self, row: dict, row_id: int):
        """Insert row into all indexes."""
        for definition in self._by_columns.values():
            key = self._build_key(row, definition.columns)
            if key is None:
                continue
            definition.index.insert(key, row_id)

    def delete(self, row: dict, row_id: int):
        """Delete row from all indexes."""
        for definition in self._by_columns.values():
            key = self._build_key(row, definition.columns)
            if key is None:
                continue
            definition.index.delete(key, row_id)

    def update(self, old_row: dict, new_row: dict, row_id: int):
        """Update row in indexes."""
        for definition in self._by_columns.values():
            old_key = self._build_key(old_row, definition.columns)
            if old_key is not None:
                definition.index.delete(old_key, row_id)

            new_key = self._build_key(new_row, definition.columns)
            if new_key is not None:
                definition.index.insert(new_key, row_id)

    def _build_key(self, row: dict, columns: Tuple[str, ...]) -> Optional[Any]:
        values = []
        for col in columns:
            if col not in row:
                return None
            values.append(row.get(col))
        # Conservative: if any component is NULL, don't index.
        if any(v is None for v in values):
            return None
        if len(values) == 1:
            return values[0]
        return tuple(values)
