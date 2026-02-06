"""
Database package for CAFÉCRAFT application.
"""

from .db import (
    DatabaseConnection,
    get_db_connection,
    get_connection,
    DB_NAME,
    DB_PATH,
)
from .schema import (
    init_database,
    drop_all_tables,
    get_table_info,
    verify_user,
)

__all__ = [
    "DatabaseConnection",
    "get_db_connection",
    "get_connection",
    "DB_NAME",
    "DB_PATH",
    "init_database",
    "drop_all_tables",
    "get_table_info",
    "verify_user",
]
