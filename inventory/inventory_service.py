import sqlite3
from typing import Dict, List, Tuple, Optional


class InventoryService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def compute_required_ingredients(
        self,
        cursor: sqlite3.Cursor,
        cart_items: List[Dict],
        strict_recipes: bool = True,
    ) -> Tuple[Dict[int, Dict], List[str]]:
        required: Dict[int, Dict] = {}
        errors: List[str] = []

        if not cart_items:
            return required, errors

        product_ids = [int(i["product_id"]) for i in cart_items]
        placeholders = ",".join(["?"] * len(product_ids))

        products = cursor.execute(
            f"SELECT id, name, is_active FROM products WHERE id IN ({placeholders})",
            tuple(product_ids),
        ).fetchall()
        product_map = {int(r["id"]): {"name": r["name"], "is_active": int(r["is_active"])} for r in products}

        for li in cart_items:
            product_id = int(li["product_id"])
            qty_sold = int(li.get("quantity", 0) or 0)

            if qty_sold <= 0:
                continue

            p = product_map.get(product_id)
            if not p or p["is_active"] != 1:
                errors.append(f"Invalid/inactive product: {product_id}")
                continue

            recipe_row = cursor.execute(
                "SELECT id FROM recipes WHERE product_id = ?",
                (product_id,),
            ).fetchone()

            if not recipe_row:
                if strict_recipes:
                    errors.append(f"Missing recipe for product: {p['name']}")
                continue

            recipe_id = int(recipe_row["id"])
            recipe_items = cursor.execute(
                """
                SELECT ingredient_id, qty, unit, COALESCE(wastage_factor, 0) AS wastage_factor
                FROM recipe_items
                WHERE recipe_id = ?
                """,
                (recipe_id,),
            ).fetchall()

            if not recipe_items:
                if strict_recipes:
                    errors.append(f"Recipe has no items for product: {p['name']}")
                continue

            for ri in recipe_items:
                ingredient_id = int(ri["ingredient_id"])
                unit = ri["unit"]
                base_qty = float(ri["qty"])
                wastage = float(ri["wastage_factor"] or 0.0)

                needed = base_qty * qty_sold * (1.0 + wastage)

                if ingredient_id not in required:
                    required[ingredient_id] = {"qty": 0.0, "unit": unit}
                else:
                    if required[ingredient_id]["unit"] != unit:
                        errors.append(f"Unit mismatch in recipes for ingredient_id={ingredient_id}")

                required[ingredient_id]["qty"] += needed

        return required, errors

    def validate_inventory(
        self,
        cursor: sqlite3.Cursor,
        required: Dict[int, Dict],
    ) -> List[Dict]:
        shortages: List[Dict] = []

        for ingredient_id, req in required.items():
            needed = float(req["qty"])
            unit = req["unit"]

            row = cursor.execute(
                "SELECT COALESCE(SUM(quantity), 0) AS qty FROM inventory WHERE ingredient_id = ?",
                (ingredient_id,),
            ).fetchone()

            available = float(row["qty"]) if row else 0.0

            if available + 1e-9 < needed:
                name_row = cursor.execute(
                    "SELECT name FROM ingredients WHERE id = ?",
                    (ingredient_id,),
                ).fetchone()
                name = name_row["name"] if name_row else f"ingredient_id={ingredient_id}"

                shortages.append(
                    {
                        "ingredient_id": ingredient_id,
                        "name": name,
                        "needed": needed,
                        "available": available,
                        "short_by": needed - available,
                        "unit": unit,
                    }
                )

        return shortages

    def consume_inventory(
        self,
        cursor: sqlite3.Cursor,
        required: Dict[int, Dict],
        order_id: int,
        performed_by: int,
        log_legacy_transactions: bool = True,
    ) -> None:
        for ingredient_id, req in required.items():
            remaining = float(req["qty"])
            unit = req["unit"]

            rows = cursor.execute(
                """
                SELECT id, quantity
                FROM inventory
                WHERE ingredient_id = ?
                ORDER BY
                    CASE WHEN expiry_date IS NULL THEN 1 ELSE 0 END,
                    expiry_date ASC,
                    last_restocked ASC,
                    id ASC
                """,
                (ingredient_id,),
            ).fetchall()

            for r in rows:
                if remaining <= 1e-9:
                    break

                inv_id = int(r["id"])
                qty = float(r["quantity"])

                if qty <= remaining + 1e-9:
                    cursor.execute("DELETE FROM inventory WHERE id = ?", (inv_id,))
                    remaining -= qty
                else:
                    cursor.execute(
                        "UPDATE inventory SET quantity = ? WHERE id = ?",
                        (qty - remaining, inv_id),
                    )
                    remaining = 0.0

            if remaining > 1e-6:
                raise ValueError(f"Inventory became insufficient during deduction (ingredient_id={ingredient_id}).")

            cursor.execute(
                """
                INSERT INTO inventory_movements
                (ingredient_id, movement_type, qty, unit, ref_type, ref_id, performed_by, reason)
                VALUES (?, 'consume', ?, ?, 'order', ?, ?, ?)
                """,
                (
                    ingredient_id,
                    float(req["qty"]),
                    unit,
                    order_id,
                    performed_by,
                    "Auto-deduct from sale",
                ),
            )

            if log_legacy_transactions:
                cursor.execute(
                    """
                    INSERT INTO transactions
                    (type, ingredient_id, quantity, unit_price, total_amount, user_id, notes)
                    VALUES ('sale', ?, ?, 0, 0, ?, ?)
                    """,
                    (
                        ingredient_id,
                        float(req["qty"]),
                        performed_by,
                        f"Auto-deduct (order_id={order_id})",
                    ),
                )

    def deduct_ingredients_for_sale(
        self,
        cursor: sqlite3.Cursor,
        cart_items: List[Dict],
        order_id: int,
        performed_by: int,
        strict_recipes: bool = True,
        log_legacy_transactions: bool = True,
    ) -> None:
        required, errors = self.compute_required_ingredients(
            cursor=cursor,
            cart_items=cart_items,
            strict_recipes=strict_recipes,
        )
        if errors:
            raise ValueError("; ".join(errors))

        shortages = self.validate_inventory(cursor, required)
        if shortages:
            msg = "Insufficient ingredients: " + ", ".join(
                [f"{s['name']} short by {s['short_by']:.2f} {s['unit']}" for s in shortages]
            )
            raise ValueError(msg)

        self.consume_inventory(
            cursor=cursor,
            required=required,
            order_id=order_id,
            performed_by=performed_by,
            log_legacy_transactions=log_legacy_transactions,
        )
