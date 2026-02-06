"""
CAFÉCRAFT DATABASE CONNECTION HANDLER

Responsibilities:
- SQLite connection handler
- Safe open/close methods
- Return cursor when needed
- Connection pooling and lifecycle management

No GUI dependencies.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, Cursor, Iterator

DB_NAME = "cafecraft.db"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), DB_NAME)


class DatabaseConnection:
    """
    Manages SQLite database connections safely.
    
    Provides:
    - Connection pooling
    - Context manager support
    - Cursor generation
    - Safe cleanup
    """

    def __init__(self, db_path: str = DB_PATH):
        """
        Initialize database connection handler.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def open(self) -> sqlite3.Connection:
        """
        Open a database connection.
        
        Returns:
            SQLite connection object.
            
        Raises:
            sqlite3.Error: If connection fails.
        """
        try:
            self._connection = sqlite3.connect(self.db_path, timeout=30.0)
            self._connection.row_factory = sqlite3.Row
            return self._connection
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Failed to connect to database: {e}")

    def close(self) -> None:
        """Close the database connection safely."""
        if self._connection:
            try:
                self._connection.close()
            except sqlite3.Error:
                pass
            finally:
                self._connection = None

    def get_cursor(self) -> Cursor:
        """
        Get a cursor for executing queries.
        
        Returns:
            SQLite cursor object.
            
        Raises:
            RuntimeError: If connection is not open.
        """
        if not self._connection:
            raise RuntimeError("Database connection not open. Call open() first.")
        return self._connection.cursor()

    def execute(self, query: str, params: tuple = ()) -> Cursor:
        """
        Execute a query without returning results.
        
        Args:
            query: SQL query string.
            params: Query parameters (for parameterized queries).
            
        Returns:
            Cursor object.
        """
        cursor = self.get_cursor()
        cursor.execute(query, params)
        return cursor

    def execute_fetch_one(self, query: str, params: tuple = ()):
        """
        Execute query and fetch one result.
        
        Args:
            query: SQL query string.
            params: Query parameters.
            
        Returns:
            Single row as tuple or None.
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def execute_fetch_all(self, query: str, params: tuple = ()):
        """
        Execute query and fetch all results.
        
        Args:
            query: SQL query string.
            params: Query parameters.
            
        Returns:
            List of rows as tuples.
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def commit(self) -> None:
        """Commit current transaction."""
        if self._connection:
            self._connection.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        if self._connection:
            self._connection.rollback()

    def __enter__(self) -> "DatabaseConnection":
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


@contextmanager
def get_db_connection(db_path: str = DB_PATH) -> Iterator[DatabaseConnection]:
    """
    Context manager for database connections.
    
    Automatically opens and closes connection.
    Handles commit/rollback on exception.
    
    Usage:
        with get_db_connection() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
    
    Args:
        db_path: Path to the SQLite database file.
        
    Yields:
        DatabaseConnection instance.
    """
    db = DatabaseConnection(db_path)
    try:
        db.open()
        yield db
    except sqlite3.Error as e:
        db.rollback()
        raise sqlite3.Error(f"Database operation failed: {e}")
    finally:
        db.close()


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Get a direct SQLite connection (legacy compatibility).
    
    Note: Caller is responsible for closing the connection.
    Prefer using get_db_connection() context manager instead.
    
    Args:
        db_path: Path to the SQLite database file.
        
    Returns:
        SQLite connection object.
    """
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn
