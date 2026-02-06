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

# Lazy import schema symbols to avoid circular/partial imports
def init_database(*args, **kwargs):
    from .schema import init_database as _fn
    return _fn(*args, **kwargs)

def drop_all_tables(*args, **kwargs):
    from .schema import drop_all_tables as _fn
    return _fn(*args, **kwargs)

def get_table_info(*args, **kwargs):
    from .schema import get_table_info as _fn
    return _fn(*args, **kwargs)

def verify_user(*args, **kwargs):
    from .schema import verify_user as _fn
    return _fn(*args, **kwargs)

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
