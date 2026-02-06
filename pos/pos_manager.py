"""
CAFÉCRAFT POS MANAGER/CONTROLLER

Responsibilities:
- Coordinate between POSView and POSService
- Handle product loading and display
- Process sales transactions
- Update inventory
- Generate receipts
- Handle user role validation
"""

from pos.pos_service import POSService
from pos.pos_view import POSView
from pos.receipt_generator import ReceiptGenerator
from tkinter import messagebox
from typing import Dict, Optional, Callable


class POSManager:
    """Manages POS operations and coordinates view with service layer."""

    def __init__(
        self,
        parent_frame,
        user_info: Dict,
        db_path: str = None,
        on_transaction_complete: Optional[Callable] = None,
    ):
        """
        Initialize POS manager.

        Args:
            parent_frame: Parent widget for POS view.
            user_info: Current user info dict.
            db_path: Database path (optional).
            on_transaction_complete: Callback when transaction completes.
        """
        self.parent_frame = parent_frame
        self.user_info = user_info
        self.db_path = db_path
        self.on_transaction_complete = on_transaction_complete

        # Initialize service
        self.service = POSService(db_path)
        self.receipt_generator = ReceiptGenerator()

        # Initialize view
        self.view = POSView(
            parent_frame,
            user_info,
            on_transaction_complete=self._handle_transaction_complete,
        )

        # Load products and populate UI
        self._load_products()

    def _load_products(self):
        """Load products from database and populate view."""
        try:
            products = self.service.get_all_products()
            categories = self.service.get_categories()

            # Pass products to view for display
            if hasattr(self.view, "populate_products"):
                self.view.populate_products(products, categories)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load products: {e}")

    def _handle_transaction_complete(self, transaction_data: Dict):
        """
        Handle completed transaction.

        Validates user role, saves to database, generates receipt, and updates inventory.

        Args:
            transaction_data: Transaction dict from view.
        """
        # Validate user role
        user_role = self.user_info.get("role", "").lower()
        if user_role not in ["owner", "admin", "manager", "cashier", "employee"]:
            messagebox.showerror("Unauthorized", "Your role cannot process transactions.")
            return

        try:
            # Create order in database
            order_id = self.service.create_order(
                user_id=self.user_info["id"],
                items=transaction_data["items"],
                total_amount=transaction_data["total"],
                payment_method=transaction_data["payment_method"],
                discount_percent=transaction_data.get("discount_percent", 0),
                order_name=transaction_data.get("order_name", ""),
                reference=transaction_data.get("reference"),
            )

            if not order_id:
                messagebox.showerror("Error", "Failed to save transaction to database.")
                return

            # Generate receipt
            receipt_data = self.service.generate_receipt_data(order_id)
            if receipt_data:
                receipt_text = self.receipt_generator.generate_receipt(receipt_data)
                # Show receipt dialog
                self._show_receipt_dialog(receipt_text, receipt_data)

            # Invoke callback if provided
            if self.on_transaction_complete:
                self.on_transaction_complete(
                    {
                        "order_id": order_id,
                        "transaction_data": transaction_data,
                        "receipt_data": receipt_data,
                    }
                )

            messagebox.showinfo(
                "Success",
                f"Transaction completed successfully!\nOrder: {receipt_data['order_number']}",
            )

        except Exception as e:
            messagebox.showerror("Error", f"Transaction processing failed: {e}")

    def _show_receipt_dialog(self, receipt_text: str, receipt_data: Dict):
        """
        Show receipt in a dialog window.

        Args:
            receipt_text: Formatted receipt text.
            receipt_data: Receipt data dict.
        """
        try:
            import customtkinter as ctk
            CTK_AVAILABLE = True
        except ImportError:
            import tkinter as tk
            CTK_AVAILABLE = False

        if CTK_AVAILABLE:
            from tkinter import scrolledtext

            # Create receipt window
            receipt_window = ctk.CTkToplevel(self.parent_frame.master)
            receipt_window.title(f"Receipt - {receipt_data['order_number']}")
            receipt_window.geometry("500x600")

            # Receipt text
            text_widget = scrolledtext.ScrolledText(
                receipt_window,
                width=60,
                height=35,
                font=("Courier New", 9),
                bg="#1a1a2e",
                fg="white",
            )
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", receipt_text)
            text_widget.config(state="disabled")

            # Buttons
            button_frame = ctk.CTkFrame(receipt_window, fg_color="transparent")
            button_frame.pack(fill="x", padx=10, pady=10)

            print_btn = ctk.CTkButton(
                button_frame,
                text="Print",
                command=lambda: self._print_receipt(receipt_text),
                width=150,
            )
            print_btn.pack(side="left", padx=5)

            close_btn = ctk.CTkButton(
                button_frame,
                text="Close",
                command=receipt_window.destroy,
                width=150,
            )
            close_btn.pack(side="right", padx=5)

        else:
            from tkinter import scrolledtext

            receipt_window = tk.Toplevel(self.parent_frame.master)
            receipt_window.title(f"Receipt - {receipt_data['order_number']}")
            receipt_window.geometry("500x600")

            text_widget = scrolledtext.ScrolledText(
                receipt_window,
                width=60,
                height=35,
                font=("Courier New", 9),
                bg="#1a1a2e",
                fg="white",
            )
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", receipt_text)
            text_widget.config(state="disabled")

            button_frame = tk.Frame(receipt_window, bg="#1a1a2e")
            button_frame.pack(fill="x", padx=10, pady=10)

            print_btn = tk.Button(
                button_frame,
                text="Print",
                command=lambda: self._print_receipt(receipt_text),
                width=15,
                bg="#28a745",
                fg="white",
            )
            print_btn.pack(side="left", padx=5)

            close_btn = tk.Button(
                button_frame,
                text="Close",
                command=receipt_window.destroy,
                width=15,
                bg="#dc3545",
                fg="white",
            )
            close_btn.pack(side="right", padx=5)

    def _print_receipt(self, receipt_text: str):
        """
        Print receipt to system printer.

        Args:
            receipt_text: Formatted receipt text.
        """
        try:
            import subprocess
            import tempfile
            import os

            # Create temporary receipt file
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                delete=False,
            ) as f:
                f.write(receipt_text)
                temp_path = f.name

            # Print on Windows
            try:
                subprocess.Popen([f"notepad.exe", "/p", temp_path])
                messagebox.showinfo("Success", "Receipt sent to printer")
            except Exception:
                # Fallback: Try generic print command
                messagebox.showinfo(
                    "Info",
                    f"Receipt not printed automatically.\nOpen this file to print:\n{temp_path}",
                )

        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print receipt: {e}")

    def refresh_products(self):
        """Refresh product list from database."""
        self._load_products()

    def get_daily_sales(self) -> Dict:
        """Get daily sales summary."""
        return self.service.get_daily_sales()

    def get_recent_orders(self, limit: int = 10):
        """Get recent orders."""
        return self.service.get_recent_orders(limit)
