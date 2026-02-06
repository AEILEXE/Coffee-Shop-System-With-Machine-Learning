from datetime import datetime
from typing import Dict, List, Optional

from database.db import get_db_connection
from inventory.recipe_inventory import InventoryService


class POSService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_all_products(self) -> List[Dict]:
        query = """
            SELECT id, name, category, price, description, image_path
            FROM products
            WHERE is_active = 1
            ORDER BY category, name
        """
        try:
            with (get_db_connection(self.db_path) if self.db_path else get_db_connection()) as db:
                rows = db.execute_fetch_all(query)
            return [
                {"id": row[0], "name": row[1], "category": row[2], "price": row[3], "description": row[4], "image_path": row[5]}
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []

    def get_categories(self) -> List[str]:
        query = """
            SELECT DISTINCT category
            FROM products
            WHERE is_active = 1
            ORDER BY category
        """
        try:
            with (get_db_connection(self.db_path) if self.db_path else get_db_connection()) as db:
                rows = db.execute_fetch_all(query)
            return [row[0] for row in rows if row[0]]
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return []

    def create_draft_order(self, user_id: int, items: List[Dict], order_name: str = "") -> Optional[int]:
        if not items:
            return None

        order_number = f"DRF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            with (get_db_connection(self.db_path) if self.db_path else get_db_connection()) as db:
                cursor = db.get_cursor()

                cursor.execute(
                    """
                    INSERT INTO orders (order_number, user_id, total_amount, status, payment_method)
                    VALUES (?, ?, 0, 'draft', NULL)
                    """,
                    (order_number, user_id),
                )
                order_id = cursor.lastrowid

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
                    INSERT INTO audit_log (user_id, action, table_name, record_id, old_value, new_value)
                    VALUES (?, 'HOLD_ORDER', 'orders', ?, NULL, ?)
                    """,
                    (user_id, order_id, f"order_number={order_number}; note={order_name}"),
                )

                db.commit()
                return order_id

        except Exception as e:
            print(f"Error creating draft order: {e}")
            return None

    def finalize_draft_order(
        self,
        order_id: int,
        user_id: int,
        payment_method: str,
        discount_percent: float = 0.0,
        reference: Optional[str] = None,
    ) -> bool:
        try:
            with (get_db_connection(self.db_path) if self.db_path else get_db_connection()) as db:
                cursor = db.get_cursor()

                order = cursor.execute(
                    "SELECT id, order_number, status FROM orders WHERE id = ?",
                    (order_id,),
                ).fetchone()
                if not order or (order["status"] or "").lower() != "draft":
                    raise ValueError("Order is not a draft or does not exist.")

                items = cursor.execute(
                    """
                    SELECT product_id, quantity, unit_price
                    FROM order_items
                    WHERE order_id = ?
                    """,
                    (order_id,),
                ).fetchall()

                if not items:
                    raise ValueError("Draft order has no items.")

                subtotal = sum(float(r["quantity"]) * float(r["unit_price"]) for r in items)
                disc = float(discount_percent or 0.0)
                total = subtotal - (subtotal * (disc / 100.0))

                inv = InventoryService(self.db_path)
                cart_for_deduction = [{"product_id": int(r["product_id"]), "quantity": int(r["quantity"])} for r in items]
                inv.deduct_ingredients_for_sale(
                    cursor=cursor,
                    cart_items=cart_for_deduction,
                    order_id=order_id,
                    performed_by=user_id,
                    strict_recipes=True,
                    log_legacy_transactions=True,
                )

                cursor.execute(
                    """
                    UPDATE orders
                    SET total_amount = ?, payment_method = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (float(total), payment_method, order_id),
                )

                cursor.execute(
                    """
                    INSERT INTO audit_log (user_id, action, table_name, record_id, old_value, new_value)
                    VALUES (?, 'FINALIZE_DRAFT', 'orders', ?, NULL, ?)
                    """,
                    (user_id, order_id, f"total={float(total):.2f}; payment={payment_method}; disc={disc:.2f}; ref={reference or ''}"),
                )

                db.commit()
                return True

        except Exception as e:
            print(f"Error finalizing draft: {e}")
            return False

    def void_order(self, order_id: int, performed_by: int, reason: str, restock_ingredients: bool = False) -> bool:
        try:
            with (get_db_connection(self.db_path) if self.db_path else get_db_connection()) as db:
                cursor = db.get_cursor()

                row = cursor.execute(
                    "SELECT id, status FROM orders WHERE id = ?",
                    (order_id,),
                ).fetchone()
                if not row:
                    raise ValueError("Order not found.")
                if (row["status"] or "").lower() == "voided":
                    return True

                cursor.execute(
                    """
                    UPDATE orders
                    SET status = 'voided', void_reason = ?, voided_by = ?, voided_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (reason, performed_by, order_id),
                )

                cursor.execute(
                    """
                    INSERT INTO audit_log (user_id, action, table_name, record_id, old_value, new_value)
                    VALUES (?, 'VOID_ORDER', 'orders', ?, NULL, ?)
                    """,
                    (performed_by, order_id, f"reason={reason}; restock={int(bool(restock_ingredients))}"),
                )

                db.commit()
                return True

        except Exception as e:
            print(f"Error voiding order: {e}")
            return False

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
            with (get_db_connection(self.db_path) if self.db_path else get_db_connection()) as db:
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
                cart_for_deduction = [{"product_id": int(i["id"]), "quantity": int(i["quantity"])} for i in items]
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
                    (user_id, order_id, f"order_number={order_number}; total={float(total_amount):.2f}; payment={payment_method}"),
                )

                db.commit()
                return order_id

        except Exception as e:
            print(f"Error creating order: {e}")
            return None

    def get_order_details(self, order_id: int) -> Optional[Dict]:
        try:
            with (get_db_connection(self.db_path) if self.db_path else get_db_connection()) as db:
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
                for r in items_rows:
                    order["items"].append(
                        {"id": r[0], "product_id": r[1], "name": r[2], "quantity": r[3], "unit_price": r[4], "subtotal": r[5]}
                    )

                return order
        except Exception as e:
            print(f"Error fetching order {order_id}: {e}")
            return None

    def generate_receipt_data(self, order_id: int) -> Optional[Dict]:
        order = self.get_order_details(order_id)
        if not order:
            return None

        try:
            with (get_db_connection(self.db_path) if self.db_path else get_db_connection()) as db:
                user_row = db.execute_fetch_one("SELECT full_name FROM users WHERE id = ?", (order["user_id"],))

                return {
                    "order_id": order["id"],
                    "order_number": order["order_number"],
                    "cashier": user_row[0] if user_row else "Unknown",
                    "timestamp": order["created_at"],
                    "items": order["items"],
                    "subtotal": sum(item["subtotal"] for item in order["items"]),
                    "total": order["total_amount"],
                    "payment_method": order["payment_method"] or "",
                }

        except Exception as e:
            print(f"Error generating receipt: {e}")
            return None
