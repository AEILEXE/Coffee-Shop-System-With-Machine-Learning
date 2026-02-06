"""
CAFÉCRAFT DATABASE CONNECTION HANDLER

- Safe SQLite connection handling
- Context manager support
- Automatic commit/rollback
- Cursor management
- No GUI dependencies
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, Iterator
from sqlite3 import Cursor

DB_NAME = "cafecraft.db"
DB_PATH = os.path.join(os.getcwd(), DB_NAME)  # safer relative path


class DatabaseConnection:
    """
    SQLite database connection handler.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def open(self) -> sqlite3.Connection:
        """Open a SQLite connection."""
        try:
            self._connection = sqlite3.connect(self.db_path, timeout=30.0)
            self._connection.row_factory = sqlite3.Row
            return self._connection
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Failed to connect to database: {e}")

    def close(self) -> None:
        """Close the connection safely."""
        if self._connection:
            try:
                self._connection.close()
            except sqlite3.Error:
                pass
            finally:
                self._connection = None

    def get_cursor(self) -> Cursor:
        """Get a cursor for executing queries."""
        if not self._connection:
            raise RuntimeError("Database connection not open. Call open() first.")
        return self._connection.cursor()

    def execute(self, query: str, params: tuple = (), commit: bool = False) -> Cursor:
        """
        Execute a query.

        Args:
            query: SQL query string.
            params: Parameters for query.
            commit: Commit automatically if True.

        Returns:
            sqlite3.Cursor object
        """
        cursor = self.get_cursor()
        cursor.execute(query, params)
        if commit and self._connection:
            self._connection.commit()
        return cursor

    def execute_fetch_one(self, query: str, params: tuple = ()):
        """Execute a query and fetch a single row."""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        return row

    def execute_fetch_all(self, query: str, params: tuple = ()):
        """Execute a query and fetch all rows."""
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._connection:
            self._connection.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._connection:
            self._connection.rollback()

    # Context manager support
    def __enter__(self) -> "DatabaseConnection":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


# Context manager helper
@contextmanager
def get_db_connection(db_path: str = DB_PATH) -> Iterator[DatabaseConnection]:
    """
    Use this to safely get a database connection.

    Usage:
        with get_db_connection() as db:
            db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",), commit=True)
    """
    db = DatabaseConnection(db_path)
    try:
        db.open()
        yield db
    except sqlite3.Error:
        db.rollback()
        raise  # preserve original traceback
    finally:
        db.close()


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Legacy helper to get a direct sqlite3.Connection.
    Caller must close connection manually.
    Prefer get_db_connection() context manager instead.
    """
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn
