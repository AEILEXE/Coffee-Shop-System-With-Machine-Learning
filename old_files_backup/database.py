import sqlite3
from datetime import datetime
from hashlib import sha256

DB_NAME = "cafecraft.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT CHECK(role IN ('owner','admin', 'manager', 'cashier', 'inventory_staff', 'employee')) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            can_pos INTEGER DEFAULT 1,
            can_inventory INTEGER DEFAULT 0,
            can_reports INTEGER DEFAULT 0,
            can_user_management INTEGER DEFAULT 0
        )
    ''')
    
    # Add permission columns if not exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN can_pos INTEGER DEFAULT 1')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN can_inventory INTEGER DEFAULT 0')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN can_reports INTEGER DEFAULT 0')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN can_user_management INTEGER DEFAULT 0')
    except:
        pass
    
    # Menu items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            is_available INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inventory items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'Other',
            quantity REAL DEFAULT 0,
            unit TEXT NOT NULL,
            cost_per_unit REAL DEFAULT 0,
            reorder_threshold REAL DEFAULT 10,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cashier_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            discount_amount REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'cash',
            status TEXT DEFAULT 'completed',
            payment_details TEXT,
            reference_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cashier_id) REFERENCES users(id)
        )
    ''')
    
    # Add status and payment_details if not exist
    try:
        cursor.execute('ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT \'completed\'')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE transactions ADD COLUMN payment_details TEXT')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE transactions ADD COLUMN reference_number TEXT')
    except:
        pass
    
    # Transaction items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
        )
    ''')
    
    # Inventory logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            change_amount REAL NOT NULL,
            change_type TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Menu recipes table (links menu items to inventory ingredients)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_item_id INTEGER NOT NULL,
            inventory_item_id INTEGER NOT NULL,
            quantity_required REAL NOT NULL,
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id),
            FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id)
        )
    ''')
    
    # Insert default admin if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', hash_password('admin123'), 'Administrator', 'admin'))
    
    # Insert sample menu items
    cursor.execute("SELECT COUNT(*) FROM menu_items")
    if cursor.fetchone()[0] == 0:
        sample_items = [
            ('Espresso', 'Coffee', 3.50),
            ('Americano', 'Coffee', 4.00),
            ('Cappuccino', 'Coffee', 4.50),
            ('Latte', 'Coffee', 5.00),
            ('Green Tea', 'Tea', 3.00),
            ('Croissant', 'Pastry', 3.50),
            ('Muffin', 'Pastry', 3.00),
            ('Sandwich', 'Snack', 6.50),
        ]
        cursor.executemany(
            'INSERT INTO menu_items (name, category, price) VALUES (?, ?, ?)',
            sample_items
        )
    
    conn.commit()
    conn.close()

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def verify_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, full_name, role, can_pos, can_inventory, can_reports, can_user_management FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    return user  # Returns (id, full_name, role, can_pos, can_inventory, can_reports, can_user_management) or None
