from typing import Any, Dict, Optional

from .db import get_connection
from utils.security import verify_password


CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL
)
"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT CHECK(role IN ('owner','admin','manager','cashier','inventory_staff','employee')) NOT NULL,
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
    type TEXT CHECK(type IN ('purchase','sale','adjustment','waste')) NOT NULL,
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
    status TEXT CHECK(status IN ('draft','pending','completed','cancelled','voided')) DEFAULT 'draft',
    payment_method TEXT,
    reference TEXT,
    discount_percent REAL DEFAULT 0,
    order_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    void_reason TEXT,
    voided_by INTEGER,
    voided_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (voided_by) REFERENCES users (id)
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

CREATE_RECIPES_TABLE = """
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL UNIQUE,
    yield_qty REAL NOT NULL DEFAULT 1,
    yield_unit TEXT NOT NULL DEFAULT 'serving',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id)
)
"""

CREATE_RECIPE_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS recipe_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    qty REAL NOT NULL,
    unit TEXT NOT NULL,
    wastage_factor REAL DEFAULT 0,
    FOREIGN KEY(recipe_id) REFERENCES recipes(id),
    FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
)
"""

CREATE_INVENTORY_MOVEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS inventory_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    movement_type TEXT CHECK(movement_type IN ('restock','consume','adjust','waste','refund')) NOT NULL,
    qty REAL NOT NULL,
    unit TEXT NOT NULL,
    ref_type TEXT,
    ref_id INTEGER,
    performed_by INTEGER,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ingredient_id) REFERENCES ingredients(id),
    FOREIGN KEY(performed_by) REFERENCES users(id)
)
"""

CREATE_PAYMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    method TEXT CHECK(method IN ('cash','gcash','card','other')) NOT NULL,
    amount REAL NOT NULL,
    received REAL DEFAULT 0,
    change REAL DEFAULT 0,
    status TEXT CHECK(status IN ('paid','refunded','voided')) DEFAULT 'paid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id)
)
"""

ALL_TABLES = [
    CREATE_SCHEMA_VERSION_TABLE,
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
    CREATE_RECIPES_TABLE,
    CREATE_RECIPE_ITEMS_TABLE,
    CREATE_INVENTORY_MOVEMENTS_TABLE,
    CREATE_PAYMENTS_TABLE,
]


def _table_exists(cursor, name: str) -> bool:
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _column_exists(cursor, table: str, column: str) -> bool:
    rows = cursor.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def _ensure_schema_version(cursor) -> int:
    cursor.execute(CREATE_SCHEMA_VERSION_TABLE)
    row = cursor.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
    if not row:
        cursor.execute("INSERT INTO schema_version (id, version) VALUES (1, 1)")
        return 1
    try:
        return int(row[0])
    except Exception:
        cursor.execute("UPDATE schema_version SET version = 1 WHERE id = 1")
        return 1


def _set_schema_version(cursor, version: int) -> None:
    cursor.execute("UPDATE schema_version SET version = ? WHERE id = 1", (version,))


def _apply_migrations(cursor) -> None:
    version = _ensure_schema_version(cursor)

    if version < 2:
        if _table_exists(cursor, "orders"):
            if not _column_exists(cursor, "orders", "void_reason"):
                cursor.execute("ALTER TABLE orders ADD COLUMN void_reason TEXT")
            if not _column_exists(cursor, "orders", "voided_by"):
                cursor.execute("ALTER TABLE orders ADD COLUMN voided_by INTEGER")
            if not _column_exists(cursor, "orders", "voided_at"):
                cursor.execute("ALTER TABLE orders ADD COLUMN voided_at TIMESTAMP")

        cursor.execute(CREATE_RECIPES_TABLE)
        cursor.execute(CREATE_RECIPE_ITEMS_TABLE)
        cursor.execute(CREATE_INVENTORY_MOVEMENTS_TABLE)
        cursor.execute(CREATE_PAYMENTS_TABLE)

        _set_schema_version(cursor, 2)

    if version < 3:
        if _table_exists(cursor, "orders"):
            if not _column_exists(cursor, "orders", "reference"):
                cursor.execute("ALTER TABLE orders ADD COLUMN reference TEXT")
            if not _column_exists(cursor, "orders", "discount_percent"):
                cursor.execute("ALTER TABLE orders ADD COLUMN discount_percent REAL DEFAULT 0")
            if not _column_exists(cursor, "orders", "order_name"):
                cursor.execute("ALTER TABLE orders ADD COLUMN order_name TEXT")

        _set_schema_version(cursor, 3)


def _create_indexes(cursor) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)",
        "CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_ingredients_is_active ON ingredients(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_ingredient_id ON inventory(ingredient_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_ingredient_id ON transactions(ingredient_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_product_id ON transactions(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
        "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_orders_voided_at ON orders(voided_at)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_custom_drinks_base_product_id ON custom_drinks(base_product_id)",
        "CREATE INDEX IF NOT EXISTS idx_custom_drinks_created_by_user_id ON custom_drinks(created_by_user_id)",
        "CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_recipe_items_recipe_id ON recipe_items(recipe_id)",
        "CREATE INDEX IF NOT EXISTS idx_recipe_items_ingredient_id ON recipe_items(ingredient_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_movements_ingredient_id ON inventory_movements(ingredient_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_movements_created_at ON inventory_movements(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at)",
    ]
    for sql in indexes:
        try:
            cursor.execute(sql)
        except Exception:
            pass


def _seed_default_users(cursor) -> None:
    from utils.security import hash_password

    default_users = [
        {
            "username": "owner",
            "password": "OwnerPass123!",
            "full_name": "System Owner",
            "role": "owner",
            "can_pos": 1,
            "can_inventory": 1,
            "can_reports": 1,
            "can_user_management": 1,
        },
        {
            "username": "employee1",
            "password": "Emp1Pass123!",
            "full_name": "Employee One",
            "role": "employee",
            "can_pos": 1,
            "can_inventory": 0,
            "can_reports": 0,
            "can_user_management": 0,
        },
        {
            "username": "employee2",
            "password": "Emp2Pass123!",
            "full_name": "Employee Two",
            "role": "employee",
            "can_pos": 1,
            "can_inventory": 0,
            "can_reports": 0,
            "can_user_management": 0,
        },
    ]

    for user in default_users:
        row = cursor.execute("SELECT id FROM users WHERE username = ?", (user["username"],)).fetchone()
        if row:
            continue

        password_hash = hash_password(user["password"])
        cursor.execute(
            """
            INSERT INTO users
            (username, password_hash, full_name, role, can_pos, can_inventory, can_reports, can_user_management)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["username"],
                password_hash,
                user["full_name"],
                user["role"],
                user["can_pos"],
                user["can_inventory"],
                user["can_reports"],
                user["can_user_management"],
            ),
        )


def _seed_default_products(cursor) -> None:
    default_products = [
        {"name": "Espresso", "category": "Hot Beverages", "price": 60, "cost": 15},
        {"name": "Americano", "category": "Hot Beverages", "price": 80, "cost": 20},
        {"name": "Cappuccino", "category": "Hot Beverages", "price": 120, "cost": 35},
        {"name": "Latte", "category": "Hot Beverages", "price": 130, "cost": 40},
        {"name": "Mocha", "category": "Hot Beverages", "price": 140, "cost": 45},
        {"name": "Macchiato", "category": "Hot Beverages", "price": 110, "cost": 30},
        {"name": "Iced Coffee", "category": "Iced Beverages", "price": 90, "cost": 25},
        {"name": "Iced Latte", "category": "Iced Beverages", "price": 130, "cost": 40},
        {"name": "Iced Cappuccino", "category": "Iced Beverages", "price": 130, "cost": 40},
        {"name": "Cold Brew", "category": "Iced Beverages", "price": 110, "cost": 30},
        {"name": "Green Tea", "category": "Tea", "price": 70, "cost": 15},
        {"name": "Black Tea", "category": "Tea", "price": 70, "cost": 15},
        {"name": "Milk Tea", "category": "Tea", "price": 100, "cost": 25},
        {"name": "Matcha Latte", "category": "Tea", "price": 140, "cost": 40},
        {"name": "Croissant", "category": "Pastries", "price": 80, "cost": 25},
        {"name": "Donut", "category": "Pastries", "price": 50, "cost": 15},
        {"name": "Muffin", "category": "Pastries", "price": 90, "cost": 28},
        {"name": "Sandwich", "category": "Food", "price": 150, "cost": 50},
        {"name": "Quiche", "category": "Food", "price": 120, "cost": 40},
        {"name": "Cheesecake", "category": "Desserts", "price": 140, "cost": 45},
        {"name": "Chocolate Cake", "category": "Desserts", "price": 120, "cost": 40},
        {"name": "Ice Cream", "category": "Desserts", "price": 100, "cost": 30},
    ]

    for product in default_products:
        row = cursor.execute("SELECT id FROM products WHERE name = ?", (product["name"],)).fetchone()
        if row:
            continue
        cursor.execute(
            "INSERT INTO products (name, category, price, cost, is_active) VALUES (?, ?, ?, ?, 1)",
            (product["name"], product["category"], product["price"], product["cost"]),
        )


def _seed_default_ingredients(cursor) -> None:
    default_ingredients = [
        {"name": "Coffee Beans", "unit": "kg", "cost_per_unit": 500, "reorder_level": 5},
        {"name": "Milk", "unit": "liter", "cost_per_unit": 60, "reorder_level": 10},
        {"name": "Sugar", "unit": "kg", "cost_per_unit": 40, "reorder_level": 8},
        {"name": "Chocolate Syrup", "unit": "liter", "cost_per_unit": 120, "reorder_level": 3},
        {"name": "Tea Leaves", "unit": "kg", "cost_per_unit": 300, "reorder_level": 2},
        {"name": "Butter", "unit": "kg", "cost_per_unit": 250, "reorder_level": 2},
        {"name": "Eggs", "unit": "pieces", "cost_per_unit": 8, "reorder_level": 30},
        {"name": "Flour", "unit": "kg", "cost_per_unit": 50, "reorder_level": 10},
    ]
    for ing in default_ingredients:
        row = cursor.execute("SELECT id FROM ingredients WHERE name = ?", (ing["name"],)).fetchone()
        if row:
            continue
        cursor.execute(
            "INSERT INTO ingredients (name, unit, cost_per_unit, reorder_level, is_active) VALUES (?, ?, ?, ?, 1)",
            (ing["name"], ing["unit"], ing["cost_per_unit"], ing["reorder_level"]),
        )


def init_database(db_path: Optional[str] = None) -> bool:
    try:
        conn = get_connection(db_path) if db_path else get_connection()
        cursor = conn.cursor()

        for table_sql in ALL_TABLES:
            cursor.execute(table_sql)

        _apply_migrations(cursor)
        _create_indexes(cursor)
        _seed_default_users(cursor)
        _seed_default_products(cursor)
        _seed_default_ingredients(cursor)

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        raise Exception(f"Database initialization failed: {e}")


def drop_all_tables(db_path: Optional[str] = None) -> bool:
    try:
        conn = get_connection(db_path) if db_path else get_connection()
        cursor = conn.cursor()

        tables_to_drop = [
            "payments",
            "inventory_movements",
            "recipe_items",
            "recipes",
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
            "schema_version",
        ]

        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        raise Exception(f"Failed to drop tables: {e}")


def get_table_info(db_path: Optional[str] = None) -> dict:
    try:
        conn = get_connection(db_path) if db_path else get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        table_info = {}
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            table_info[table_name] = cursor.fetchall()

        conn.close()
        return table_info
    except Exception as e:
        raise Exception(f"Failed to get table info: {e}")


def verify_user(username: str, password: str) -> Dict[str, Any] | None:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, username, full_name, role, can_pos, can_inventory,
                   can_reports, can_user_management, password_hash
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        user_row = cursor.fetchone()
        conn.close()

        if not user_row:
            return None

        if not verify_password(password, user_row["password_hash"]):
            return None

        return {
            "id": user_row["id"],
            "username": user_row["username"],
            "name": user_row["full_name"],
            "role": user_row["role"],
            "can_pos": user_row["can_pos"],
            "can_inventory": user_row["can_inventory"],
            "can_reports": user_row["can_reports"],
            "can_user_management": user_row["can_user_management"],
        }
    except Exception as e:
        raise Exception(f"Error verifying user: {e}")
