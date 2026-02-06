from datetime import datetime
from typing import Dict, List, Optional
import sqlite3

from database.db import get_db_connection
from inventory.recipe_inventory import InventoryService


class POSService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def add_product(self, name: str, category: str, price: float, cost: float, description: str = "") -> bool:
        query = """
            INSERT INTO products (name, category, price, cost, description, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """
        try:
            with get_db_connection(self.db_path) if self.db_path else get_db_connection() as db:
                db.execute(query, (name, category, price, cost, description), commit=True)
            return True
        except Exception as e:
            print(f"Error adding product: {e}")
            return False

    def get_all_products(self) -> List[Dict]:
        query = """
            SELECT id, name, category, price, description, image_path
            FROM products
            WHERE is_active = 1
            ORDER BY category, name
        """
        try:
            with get_db_connection(self.db_path) if self.db_path else get_db_connection() as db:
                rows = db.execute_fetch_all(query)
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "price": row[3],
                    "description": row[4],
                    "image_path": row[5],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []

    def get_products_by_category(self, category: str) -> List[Dict]:
        query = """
            SELECT id, name, category, price, description, image_path
            FROM products
            WHERE is_active = 1 AND category = ?
            ORDER BY name
        """
        try:
            with get_db_connection(self.db_path) if self.db_path else get_db_connection() as db:
                rows = db.execute_fetch_all(query, (category,))
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "price": row[3],
                    "description": row[4],
                    "image_path": row[5],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching products by category: {e}")
            return []

    def get_product(self, product_id: int) -> Optional[Dict]:
        query = """
            SELECT id, name, category, price, cost, description, image_path
            FROM products
            WHERE id = ? AND is_active = 1
        """
        try:
            with get_db_connection(self.db_path) if self.db_path else get_db_connection() as db:
                row = db.execute_fetch_one(query, (product_id,))
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "price": row[3],
                    "cost": row[4],
                    "description": row[5],
                    "image_path": row[6],
                }
            return None
        except Exception as e:
            print(f"Error fetching product {product_id}: {e}")
            return None

    def get_categories(self) -> List[str]:
        query = """
            SELECT DISTINCT category
            FROM products
            WHERE is_active = 1
            ORDER BY category
        """
        try:
            with get_db_connection(self.db_path) if self.db_path else get_db_connection() as db:
                rows = db.execute_fetch_all(query)
            return [row[0] for row in rows if row[0]]
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return []

    def create_order(
        self,
        user_id: int,
        items: List[Dict],
        total_amount: float,
        payment_method: str,
        discount_percent: float = 0.0,
        order_name: str = "",
        reference: Optional[str] = None,
    ) -> Optional[int]:
        if not items:
            return None

        order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            db_cm = get_db_connection(self.db_path) if self.db_path else get_db_connection()
            with db_cm as db:
                if hasattr(db, "begin_immediate"):
                    db.begin_immediate()

                cursor = db.get_cursor()

                cursor.execute(
                    """
                    INSERT INTO orders (order_number, user_id, total_amount, payment_method, status, completed_at)
                    VALUES (?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)
                    """,
                    (order_number, user_id, float(total_amount), payment_method),
                )
                order_id = cursor.lastrowid

                inv = InventoryService(self.db_path)

                cart_for_deduction = [
                    {"product_id": int(item["id"]), "quantity": int(item["quantity"])}
                    for item in items
                ]

                inv.deduct_ingredients_for_sale(
                    cursor=cursor,
                    cart_items=cart_for_deduction,
                    order_id=order_id,
                    performed_by=user_id,
                    strict_recipes=True,
                    log_legacy_transactions=True,
                )

                notes_parts = [f"Order {order_number}"]
                if order_name:
                    notes_parts.append(order_name)
                if reference:
                    notes_parts.append(f"Ref:{reference}")
                if discount_percent:
                    notes_parts.append(f"Disc:{float(discount_percent):.2f}%")
                notes = " - ".join(notes_parts)

                for item in items:
                    pid = int(item["id"])
                    qty = int(item["quantity"])
                    price = float(item["price"])
                    subtotal = float(qty * price)

                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (order_id, pid, qty, price, subtotal),
                    )

                    cursor.execute(
                        """
                        INSERT INTO transactions (type, product_id, quantity, unit_price, total_amount, user_id, notes)
                        VALUES ('sale', ?, ?, ?, ?, ?, ?)
                        """,
                        (pid, qty, price, subtotal, user_id, notes),
                    )

                cursor.execute(
                    """
                    INSERT INTO audit_log (user_id, action, table_name, record_id, old_value, new_value)
                    VALUES (?, 'CREATE_ORDER', 'orders', ?, NULL, ?)
                    """,
                    (
                        user_id,
                        order_id,
                        f"order_number={order_number}; total={float(total_amount):.2f}; payment={payment_method}",
                    ),
                )

                return order_id

        except Exception as e:
            print(f"Error creating order: {e}")
            return None

    def get_order_details(self, order_id: int) -> Optional[Dict]:
        try:
            db_cm = get_db_connection(self.db_path) if self.db_path else get_db_connection()
            with db_cm as db:
                order_row = db.execute_fetch_one(
                    """
                    SELECT id, order_number, user_id, total_amount, payment_method, created_at, status
                    FROM orders
                    WHERE id = ?
                    """,
                    (order_id,),
                )

                if not order_row:
                    return None

                order = {
                    "id": order_row[0],
                    "order_number": order_row[1],
                    "user_id": order_row[2],
                    "total_amount": order_row[3],
                    "payment_method": order_row[4],
                    "created_at": order_row[5],
                    "status": order_row[6],
                    "items": [],
                }

                items_rows = db.execute_fetch_all(
                    """
                    SELECT oi.id, oi.product_id, p.name, oi.quantity, oi.unit_price, oi.subtotal
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = ?
                    """,
                    (order_id,),
                )

                for item_row in items_rows:
                    order["items"].append(
                        {
                            "id": item_row[0],
                            "product_id": item_row[1],
                            "name": item_row[2],
                            "quantity": item_row[3],
                            "unit_price": item_row[4],
                            "subtotal": item_row[5],
                        }
                    )

                return order

        except Exception as e:
            print(f"Error fetching order {order_id}: {e}")
            return None

    def get_recent_orders(self, limit: int = 10) -> List[Dict]:
        query = """
            SELECT id, order_number, user_id, total_amount, payment_method, created_at, status
            FROM orders
            ORDER BY created_at DESC
            LIMIT ?
        """
        try:
            with get_db_connection(self.db_path) if self.db_path else get_db_connection() as db:
                rows = db.execute_fetch_all(query, (limit,))
            return [
                {
                    "id": row[0],
                    "order_number": row[1],
                    "user_id": row[2],
                    "total_amount": row[3],
                    "payment_method": row[4],
                    "created_at": row[5],
                    "status": row[6],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching recent orders: {e}")
            return []

    def get_daily_sales(self, date: str = None) -> Dict:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        query = """
            SELECT COUNT(id), SUM(total_amount)
            FROM orders
            WHERE DATE(created_at) = ? AND status = 'completed'
        """
        try:
            with get_db_connection(self.db_path) if self.db_path else get_db_connection() as db:
                row = db.execute_fetch_one(query, (date,))
            return {
                "date": date,
                "order_count": row[0] or 0,
                "total_sales": row[1] or 0.0,
            }
        except Exception as e:
            print(f"Error fetching daily sales: {e}")
            return {"date": date, "order_count": 0, "total_sales": 0.0}

    def generate_receipt_data(self, order_id: int) -> Optional[Dict]:
        order = self.get_order_details(order_id)
        if not order:
            return None

        try:
            db_cm = get_db_connection(self.db_path) if self.db_path else get_db_connection()
            with db_cm as db:
                user_row = db.execute_fetch_one(
                    "SELECT full_name FROM users WHERE id = ?",
                    (order["user_id"],),
                )

                receipt = {
                    "order_id": order["id"],
                    "order_number": order["order_number"],
                    "cashier": user_row[0] if user_row else "Unknown",
                    "timestamp": order["created_at"],
                    "items": order["items"],
                    "subtotal": sum(item["subtotal"] for item in order["items"]),
                    "total": order["total_amount"],
                    "payment_method": order["payment_method"],
                }
                return receipt

        except Exception as e:
            print(f"Error generating receipt: {e}")
            return None
