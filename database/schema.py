"""
CAFÉCRAFT DATABASE SCHEMA

Responsibilities:
- Define all table schemas
- Create tables if not exist
- Provide init_db() function
- Database structure management

No GUI dependencies.
"""

from .db import get_connection
from typing import Optional


# SQL CREATE TABLE statements
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT CHECK(role IN ('owner','admin', 'manager', 'cashier', 'inventory_staff', 'employee')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    can_pos INTEGER DEFAULT 1,
    can_inventory INTEGER DEFAULT 0,
    can_reports INTEGER DEFAULT 0,
    can_user_management INTEGER DEFAULT 0
)
"""

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    cost REAL DEFAULT 0,
    description TEXT,
    image_path TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_INGREDIENTS_TABLE = """
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    unit TEXT NOT NULL,
    cost_per_unit REAL NOT NULL,
    reorder_level REAL DEFAULT 10,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_INVENTORY_TABLE = """
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    last_restocked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP,
    location TEXT,
    supplier TEXT,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
)
"""

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT CHECK(type IN ('purchase', 'sale', 'adjustment', 'waste')) NOT NULL,
    ingredient_id INTEGER,
    product_id INTEGER,
    quantity REAL NOT NULL,
    unit_price REAL NOT NULL,
    total_amount REAL NOT NULL,
    user_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients (id),
    FOREIGN KEY (product_id) REFERENCES products (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
)
"""

CREATE_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT CHECK(status IN ('pending', 'completed', 'cancelled')) DEFAULT 'pending',
    payment_method TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
"""

CREATE_ORDER_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    subtotal REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
)
"""

CREATE_CUSTOM_DRINKS_TABLE = """
CREATE TABLE IF NOT EXISTS custom_drinks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    base_product_id INTEGER NOT NULL,
    created_by_user_id INTEGER,
    price REAL NOT NULL,
    ingredients TEXT,
    instructions TEXT,
    is_favorite INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_product_id) REFERENCES products (id),
    FOREIGN KEY (created_by_user_id) REFERENCES users (id)
)
"""

CREATE_REPORTS_TABLE = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT NOT NULL,
    report_name TEXT NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    total_sales REAL DEFAULT 0,
    total_cost REAL DEFAULT 0,
    profit REAL DEFAULT 0,
    item_count INTEGER DEFAULT 0,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
"""

CREATE_AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    table_name TEXT,
    record_id INTEGER,
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
"""

# List of all CREATE TABLE statements
ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_PRODUCTS_TABLE,
    CREATE_INGREDIENTS_TABLE,
    CREATE_INVENTORY_TABLE,
    CREATE_TRANSACTIONS_TABLE,
    CREATE_ORDERS_TABLE,
    CREATE_ORDER_ITEMS_TABLE,
    CREATE_CUSTOM_DRINKS_TABLE,
    CREATE_REPORTS_TABLE,
    CREATE_AUDIT_LOG_TABLE,
]


def init_database(db_path: Optional[str] = None) -> bool:
    """
    Initialize database by creating all required tables if they don't exist.
    
    Args:
        db_path: Optional path to database file. Uses default if not provided.
        
    Returns:
        True if initialization succeeded, False otherwise.
        
    Raises:
        Exception: If database operations fail.
    """
    try:
        if db_path:
            conn = get_connection(db_path)
        else:
            conn = get_connection()
        
        cursor = conn.cursor()
        
        # Create all tables
        for table_sql in ALL_TABLES:
            cursor.execute(table_sql)
        
        # Create indexes for better query performance
        _create_indexes(cursor)
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        raise Exception(f"Database initialization failed: {e}")


def _create_indexes(cursor) -> None:
    """
    Create indexes for better query performance.
    
    Args:
        cursor: Database cursor.
    """
    indexes = [
        # Users indexes
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
        
        # Products indexes
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)",
        "CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active)",
        
        # Ingredients indexes
        "CREATE INDEX IF NOT EXISTS idx_ingredients_is_active ON ingredients(is_active)",
        
        # Inventory indexes
        "CREATE INDEX IF NOT EXISTS idx_inventory_ingredient_id ON inventory(ingredient_id)",
        
        # Transactions indexes
        "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_ingredient_id ON transactions(ingredient_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_product_id ON transactions(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at)",
        
        # Orders indexes
        "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
        "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
        
        # Order items indexes
        "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)",
        
        # Custom drinks indexes
        "CREATE INDEX IF NOT EXISTS idx_custom_drinks_base_product_id ON custom_drinks(base_product_id)",
        "CREATE INDEX IF NOT EXISTS idx_custom_drinks_created_by_user_id ON custom_drinks(created_by_user_id)",
        
        # Reports indexes
        "CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at)",
        
        # Audit log indexes
        "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
        except Exception:
            pass  # Index may already exist


def drop_all_tables(db_path: Optional[str] = None) -> bool:
    """
    Drop all tables from the database (for testing/reset purposes).
    
    CAUTION: This will permanently delete all data!
    
    Args:
        db_path: Optional path to database file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        if db_path:
            conn = get_connection(db_path)
        else:
            conn = get_connection()
        
        cursor = conn.cursor()
        
        tables_to_drop = [
            "audit_log",
            "reports",
            "custom_drinks",
            "order_items",
            "orders",
            "transactions",
            "inventory",
            "ingredients",
            "products",
            "users",
        ]
        
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        raise Exception(f"Failed to drop tables: {e}")


def get_table_info(db_path: Optional[str] = None) -> dict:
    """
    Get information about all tables in the database.
    
    Args:
        db_path: Optional path to database file.
        
    Returns:
        Dictionary with table names and column information.
    """
    try:
        if db_path:
            conn = get_connection(db_path)
        else:
            conn = get_connection()
        
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        table_info = {}
        
        for (table_name,) in tables:
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            table_info[table_name] = columns
        
        conn.close()
        
        return table_info
    except Exception as e:
        raise Exception(f"Failed to get table info: {e}")
