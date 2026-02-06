"""
CAFÉCRAFT POS SERVICE LAYER

Responsibilities:
- Fetch products from database for POS
- Create orders and order items
- Update inventory after sales
- Retrieve transaction history
- Calculate totals and discounts
- Log transactions

Business logic separated from UI.
"""

from database.db import get_db_connection, DatabaseConnection
from database.schema import (
    CREATE_ORDERS_TABLE,
    CREATE_ORDER_ITEMS_TABLE,
    CREATE_TRANSACTIONS_TABLE,
)
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import sqlite3


class POSService:
    """Handle POS business logic and database operations."""

    def __init__(self, db_path: str = None):
        """Initialize POS service."""
        self.db_path = db_path

    def get_all_products(self) -> List[Dict]:
        """
        Fetch all active products from database.

        Returns:
            List of product dicts with id, name, price, category.
        """
        query = """
            SELECT id, name, category, price, description, image_path
            FROM products
            WHERE is_active = 1
            ORDER BY category, name
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query)
            else:
                with get_db_connection() as db:
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
        """
        Fetch products by category.

        Args:
            category: Product category.

        Returns:
            List of product dicts.
        """
        query = """
            SELECT id, name, category, price, description, image_path
            FROM products
            WHERE is_active = 1 AND category = ?
            ORDER BY name
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query, (category,))
            else:
                with get_db_connection() as db:
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
        """
        Fetch a single product.

        Args:
            product_id: Product ID.

        Returns:
            Product dict or None.
        """
        query = """
            SELECT id, name, category, price, cost, description, image_path
            FROM products
            WHERE id = ? AND is_active = 1
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    row = db.execute_fetch_one(query, (product_id,))
            else:
                with get_db_connection() as db:
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
        """
        Get all product categories.

        Returns:
            List of category names.
        """
        query = """
            SELECT DISTINCT category
            FROM products
            WHERE is_active = 1
            ORDER BY category
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query)
            else:
                with get_db_connection() as db:
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
        """
        Create an order and order items in the database.

        Args:
            user_id: User ID (cashier).
            items: List of cart items with id, price, quantity.
            total_amount: Final total after discount.
            payment_method: Payment method (Cash, GCash, Bank Transfer).
            discount_percent: Discount percentage applied.
            order_name: Order name/customer identifier.
            reference: Bank reference if applicable.

        Returns:
            Order ID or None on failure.
        """
        # Generate unique order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()
                
            with db_connection as db:
                cursor = db.get_cursor()

                # Create order
                cursor.execute(
                    """
                    INSERT INTO orders (order_number, user_id, total_amount, payment_method, status)
                    VALUES (?, ?, ?, ?, 'completed')
                    """,
                    (order_number, user_id, total_amount, payment_method),
                )
                order_id = cursor.lastrowid

                # Create order items
                for item in items:
                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            order_id,
                            item["id"],
                            item["quantity"],
                            item["price"],
                            item["quantity"] * item["price"],
                        ),
                    )

                    # Log transaction
                    cursor.execute(
                        """
                        INSERT INTO transactions (type, product_id, quantity, unit_price, total_amount, user_id, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            "sale",
                            item["id"],
                            item["quantity"],
                            item["price"],
                            item["quantity"] * item["price"],
                            user_id,
                            f"Order {order_number} - {order_name}" if order_name else f"Order {order_number}",
                        ),
                    )

                db.commit()
                return order_id

        except Exception as e:
            print(f"Error creating order: {e}")
            return None

    def get_order_details(self, order_id: int) -> Optional[Dict]:
        """
        Get complete order details including items.

        Args:
            order_id: Order ID.

        Returns:
            Order dict with items or None.
        """
        try:
            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()
                
            with db_connection as db:
                # Get order
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

                # Get order items
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
                    order["items"].append({
                        "id": item_row[0],
                        "product_id": item_row[1],
                        "name": item_row[2],
                        "quantity": item_row[3],
                        "unit_price": item_row[4],
                        "subtotal": item_row[5],
                    })

                return order

        except Exception as e:
            print(f"Error fetching order {order_id}: {e}")
            return None

    def get_recent_orders(self, limit: int = 10) -> List[Dict]:
        """
        Get recent orders.

        Args:
            limit: Number of orders to fetch.

        Returns:
            List of order dicts.
        """
        query = """
            SELECT id, order_number, user_id, total_amount, payment_method, created_at, status
            FROM orders
            ORDER BY created_at DESC
            LIMIT ?
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query, (limit,))
            else:
                with get_db_connection() as db:
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
        """
        Get daily sales summary.

        Args:
            date: Date in YYYY-MM-DD format (default today).

        Returns:
            Dict with total sales, count, etc.
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        query = """
            SELECT COUNT(id), SUM(total_amount)
            FROM orders
            WHERE DATE(created_at) = ? AND status = 'completed'
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    row = db.execute_fetch_one(query, (date,))
            else:
                with get_db_connection() as db:
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
        """
        Generate receipt data for an order.

        Args:
            order_id: Order ID.

        Returns:
            Receipt data dict or None.
        """
        order = self.get_order_details(order_id)
        if not order:
            return None

        try:
            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()
                
            with db_connection as db:
                # Get user info
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
