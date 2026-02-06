import os
import sqlite3
from contextlib import contextmanager
from sqlite3 import Cursor
from typing import Iterator, Optional

DB_NAME = "cafecraft.db"
DB_PATH = os.path.join(os.getcwd(), DB_NAME)


class DatabaseConnection:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def open(self) -> sqlite3.Connection:
        try:
            self._connection = sqlite3.connect(self.db_path, timeout=30.0)
            self._connection.row_factory = sqlite3.Row

            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute("PRAGMA busy_timeout = 30000")

            return self._connection
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Failed to connect to database: {e}")

    def close(self) -> None:
        if self._connection:
            try:
                self._connection.close()
            except sqlite3.Error:
                pass
            finally:
                self._connection = None

    def get_cursor(self) -> Cursor:
        if not self._connection:
            raise RuntimeError("Database connection not open. Call open() first.")
        return self._connection.cursor()

    def begin_immediate(self) -> None:
        if not self._connection:
            raise RuntimeError("Database connection not open. Call open() first.")
        self._connection.execute("BEGIN IMMEDIATE")

    def execute(self, query: str, params: tuple = (), commit: bool = False) -> Cursor:
        cursor = self.get_cursor()
        cursor.execute(query, params)
        if commit and self._connection:
            self._connection.commit()
        return cursor

    def execute_fetch_one(self, query: str, params: tuple = ()):
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        return row

    def execute_fetch_all(self, query: str, params: tuple = ()):
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def commit(self) -> None:
        if self._connection:
            self._connection.commit()

    def rollback(self) -> None:
        if self._connection:
            self._connection.rollback()

    def __enter__(self) -> "DatabaseConnection":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


@contextmanager
def get_db_connection(db_path: str = DB_PATH) -> Iterator[DatabaseConnection]:
    db = DatabaseConnection(db_path)
    try:
        db.open()
        yield db
    except sqlite3.Error:
        db.rollback()
        raise
    finally:
        db.close()


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn
