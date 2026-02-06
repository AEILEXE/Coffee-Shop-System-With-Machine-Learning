"""
CAFÉCRAFT INVENTORY MANAGER

Coordinates between Inventory View and Service Layer
"""

from inventory.inventory_service import InventoryService
from inventory.inventory_view import InventoryView
from tkinter import messagebox
from typing import Dict, Optional, Callable


class InventoryManager:
    """Manages inventory operations."""

    def __init__(
        self,
        parent_frame,
        user_info: Dict,
        db_path: str = None,
        on_stock_update: Optional[Callable] = None,
    ):
        """
        Initialize inventory manager.

        Args:
            parent_frame: Parent widget.
            user_info: Current user info.
            db_path: Database path.
            on_stock_update: Callback on stock update.
        """
        self.parent_frame = parent_frame
        self.user_info = user_info
        self.db_path = db_path
        self.on_stock_update = on_stock_update

        # Initialize service
        self.service = InventoryService(db_path)

        # Initialize view
        self.view = InventoryView(
            parent_frame,
            user_info,
            on_stock_update=self._handle_stock_update,
        )

        # Load inventory data
        self._load_inventory()

    def _load_inventory(self):
        """Load inventory from database."""
        try:
            ingredients = self.service.get_all_ingredients()
            if hasattr(self.view, "populate_inventory"):
                self.view.populate_inventory(ingredients)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load inventory: {e}")

    def _handle_stock_update(self, ingredient_data: Dict):
        """Handle stock update from view."""
        try:
            success = self.service.update_stock(
                ingredient_id=ingredient_data["id"],
                quantity=ingredient_data["quantity"],
                notes=ingredient_data.get("notes", ""),
            )

            if success:
                self._load_inventory()
                messagebox.showinfo("Success", "Stock updated successfully")
                if self.on_stock_update:
                    self.on_stock_update(ingredient_data)
            else:
                messagebox.showerror("Error", "Failed to update stock")

        except Exception as e:
            messagebox.showerror("Error", f"Stock update failed: {e}")

    def get_low_stock_alerts(self) -> list:
        """Get items below reorder threshold."""
        return self.service.get_low_stock_items()

    def get_inventory_value(self) -> Dict:
        """Get total inventory value."""
        return self.service.get_inventory_value()

    def refresh(self):
        """Refresh inventory data."""
        self._load_inventory()
