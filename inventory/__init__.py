"""
Inventory module for CAFÉCRAFT application.
"""

from .inventory_view import InventoryView
from .inventory_service import InventoryService
from .inventory_manager import InventoryManager

__all__ = [
    "InventoryView",
    "InventoryService",
    "InventoryManager",
]
