"""Database manager for SimpleSQLDB.

Adds MySQL/MariaDB-like multi-database support by mapping database names
(e.g. `school_erp`) to on-disk directories that contain table schema/data JSON.

A "database" in SimpleSQLDB is simply a folder containing:
  - {table}.schema.json
  - {table}.data.json

This module is intentionally small and conservative: it validates names to
avoid path traversal and keeps the Storage layer unchanged.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from core.storage import Storage


_DB_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_db_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("Database name is required")
    if not _DB_NAME_RE.match(name):
        raise ValueError(
            "Invalid database name. Use letters/numbers/underscore and don't start with a number."
        )
    return name


@dataclass(frozen=True)
class DatabaseInfo:
    name: str
    path: str
    exists: bool
    registered: bool


class DatabaseManager:
    """Discovers, creates, and opens databases (folders)."""

    def __init__(self, base_dir: str = "databases"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._registry: Dict[str, Path] = {}

    def register_database(self, name: str, path: str | Path) -> None:
        """Register a database name to a specific folder path.

        This is useful for backwards compatibility (e.g. mapping `studio` → `studio_data`).
        """
        db_name = _validate_db_name(name)
        db_path = Path(path)
        self._registry[db_name] = db_path

    def list_databases(self) -> List[DatabaseInfo]:
        seen: Dict[str, DatabaseInfo] = {}

        # Registered databases first
        for name, path in self._registry.items():
            exists = Path(path).exists()
            seen[name] = DatabaseInfo(name=name, path=str(path), exists=exists, registered=True)

        # Then any folders under base_dir
        if self.base_dir.exists():
            for child in sorted(self.base_dir.iterdir(), key=lambda p: p.name.lower()):
                if not child.is_dir():
                    continue
                name = child.name
                if not _DB_NAME_RE.match(name):
                    continue
                if name in seen:
                    continue
                seen[name] = DatabaseInfo(name=name, path=str(child), exists=True, registered=False)

        return sorted(seen.values(), key=lambda d: d.name.lower())

    def database_exists(self, name: str) -> bool:
        db_name = _validate_db_name(name)
        return self._resolve_path(db_name).exists()

    def create_database(self, name: str) -> Path:
        db_name = _validate_db_name(name)
        path = self._resolve_path(db_name)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def drop_database(self, name: str) -> None:
        db_name = _validate_db_name(name)
        path = self._resolve_path(db_name)
        if not path.exists():
            raise ValueError(f"Database '{db_name}' does not exist")
        shutil.rmtree(path)

    def open_storage(self, name: str) -> Storage:
        db_name = _validate_db_name(name)
        path = self._resolve_path(db_name)
        if not path.exists():
            raise ValueError(f"Database '{db_name}' does not exist")
        return Storage(data_dir=str(path))

    def _resolve_path(self, name: str) -> Path:
        if name in self._registry:
            return Path(self._registry[name])
        return self.base_dir / name
