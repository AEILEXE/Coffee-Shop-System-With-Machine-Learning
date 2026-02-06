"""
CAFÉCRAFT INVENTORY SERVICE LAYER

Responsibilities:
- Manage ingredient and product inventory
- Track stock levels and reorder thresholds
- Log inventory transactions
- Integration with POS for stock depletion
- Low-stock alerts
"""

from database.db import get_db_connection
from typing import List, Dict, Optional
from datetime import datetime


class InventoryService:
    """Handle inventory operations and database interactions."""

    def __init__(self, db_path: str = None):
        """Initialize inventory service."""
        self.db_path = db_path

    def get_all_ingredients(self) -> List[Dict]:
        """
        Fetch all ingredients with current stock levels.

        Returns:
            List of ingredient dicts with stock info.
        """
        query = """
            SELECT 
                i.id, i.name, i.unit, i.cost_per_unit, i.reorder_level,
                inv.quantity, inv.last_restocked, inv.expiry_date, inv.supplier
            FROM ingredients i
            LEFT JOIN inventory inv ON i.id = inv.ingredient_id
            WHERE i.is_active = 1
            ORDER BY i.name
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
                    "unit": row[2],
                    "cost_per_unit": row[3],
                    "reorder_level": row[4],
                    "quantity": row[5] or 0,
                    "last_restocked": row[6],
                    "expiry_date": row[7],
                    "supplier": row[8],
                    "is_low_stock": (row[5] or 0) < (row[4] or 10),
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching ingredients: {e}")
            return []

    def update_stock(
        self,
        ingredient_id: int,
        quantity: float,
        notes: str = "",
    ) -> bool:
        """
        Update ingredient stock level.

        Args:
            ingredient_id: Ingredient ID.
            quantity: New quantity (absolute value, not delta).
            notes: Transaction notes.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()

            with db_connection as db:
                cursor = db.get_cursor()

                # Get current quantity
                cursor.execute(
                    "SELECT quantity FROM inventory WHERE ingredient_id = ?",
                    (ingredient_id,),
                )
                result = cursor.fetchone()
                old_quantity = result[0] if result else 0

                # Update inventory
                if result:
                    cursor.execute(
                        """UPDATE inventory 
                           SET quantity = ?, last_restocked = CURRENT_TIMESTAMP
                           WHERE ingredient_id = ?""",
                        (quantity, ingredient_id),
                    )
                else:
                    cursor.execute(
                        """INSERT INTO inventory (ingredient_id, quantity, last_restocked)
                           VALUES (?, ?, CURRENT_TIMESTAMP)""",
                        (ingredient_id, quantity),
                    )

                # Log transaction
                delta = quantity - old_quantity
                cursor.execute(
                    """INSERT INTO transactions (type, ingredient_id, quantity, unit_price, total_amount, notes)
                       VALUES (?, ?, ?, 1, ?, ?)""",
                    ("adjustment", ingredient_id, abs(delta), abs(delta), notes),
                )

                db.commit()
                return True

        except Exception as e:
            print(f"Error updating stock: {e}")
            return False

    def get_low_stock_items(self) -> List[Dict]:
        """
        Get items below reorder threshold.

        Returns:
            List of low-stock ingredient dicts.
        """
        query = """
            SELECT 
                i.id, i.name, i.unit, i.reorder_level,
                inv.quantity, i.cost_per_unit
            FROM ingredients i
            LEFT JOIN inventory inv ON i.id = inv.ingredient_id
            WHERE i.is_active = 1 AND (inv.quantity IS NULL OR inv.quantity < i.reorder_level)
            ORDER BY i.name
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
                    "unit": row[2],
                    "reorder_level": row[3],
                    "current_quantity": row[4] or 0,
                    "cost_per_unit": row[5],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching low stock items: {e}")
            return []

    def get_inventory_value(self) -> Dict:
        """
        Calculate total inventory value.

        Returns:
            Dict with total_items, total_cost_value.
        """
        query = """
            SELECT COUNT(DISTINCT ingredient_id), SUM(inv.quantity * i.cost_per_unit)
            FROM inventory inv
            JOIN ingredients i ON inv.ingredient_id = i.id
            WHERE i.is_active = 1
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    row = db.execute_fetch_one(query)
            else:
                with get_db_connection() as db:
                    row = db.execute_fetch_one(query)

            return {
                "total_items": row[0] or 0,
                "total_value": row[1] or 0.0,
            }
        except Exception as e:
            print(f"Error calculating inventory value: {e}")
            return {"total_items": 0, "total_value": 0.0}

    def add_ingredient(
        self,
        name: str,
        unit: str,
        cost_per_unit: float,
        reorder_level: float = 10,
    ) -> bool:
        """
        Add new ingredient to inventory.

        Args:
            name: Ingredient name.
            unit: Unit of measurement (kg, liter, pieces, etc).
            cost_per_unit: Cost per unit.
            reorder_level: Reorder threshold.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()

            with db_connection as db:
                cursor = db.get_cursor()
                cursor.execute(
                    """INSERT INTO ingredients (name, unit, cost_per_unit, reorder_level, is_active)
                       VALUES (?, ?, ?, ?, 1)""",
                    (name, unit, cost_per_unit, reorder_level),
                )
                db.commit()
                return True

        except Exception as e:
            print(f"Error adding ingredient: {e}")
            return False

    def deduct_stock_for_sale(self, product_id: int, quantity: int) -> bool:
        """
        Deduct product quantity for a completed sale (from POS).

        Args:
            product_id: Product ID.
            quantity: Quantity sold.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()

            with db_connection as db:
                cursor = db.get_cursor()

                # Log as sale transaction
                cursor.execute(
                    """INSERT INTO transactions (type, product_id, quantity, unit_price, total_amount, notes)
                       VALUES (?, ?, ?, 1, ?, 'Sale')""",
                    ("sale", product_id, quantity, quantity),
                )

                db.commit()
                return True

        except Exception as e:
            print(f"Error deducting stock: {e}")
            return False
