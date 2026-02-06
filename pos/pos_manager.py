from tkinter import messagebox, simpledialog
from typing import Dict, Optional, Callable

from pos.pos_service import POSService
from pos.pos_view import POSView
from pos.receipt_generator import ReceiptGenerator


class POSManager:
    def __init__(
        self,
        parent_frame,
        user_info: Dict,
        db_path: str = None,
        on_transaction_complete: Optional[Callable] = None,
    ):
        self.parent_frame = parent_frame
        self.user_info = user_info
        self.db_path = db_path
        self.on_transaction_complete = on_transaction_complete

        self.service = POSService(db_path)
        self.receipt_generator = ReceiptGenerator()

        self.view = POSView(
            parent_frame,
            user_info,
            on_transaction_complete=self._handle_transaction_complete,
        )

        self._load_products()

    def _load_products(self):
        try:
            products = self.service.get_all_products()
            categories = self.service.get_categories()
            self.view.populate_products(products, categories)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load products: {e}")

    def _handle_transaction_complete(self, transaction_data: Dict):
        user_role = (self.user_info.get("role") or "").lower()
        if user_role not in ["owner", "admin", "manager", "cashier", "employee"]:
            messagebox.showerror("Unauthorized", "Your role cannot process transactions.")
            return

        action = (transaction_data.get("action") or "checkout").lower()

        try:
            if action == "hold":
                self._hold_order(transaction_data)
                return

            if action == "finalize_draft":
                self._finalize_draft(transaction_data)
                return

            if action == "void":
                self._void_order(transaction_data)
                return

            self._checkout_order(transaction_data)

        except Exception as e:
            messagebox.showerror("Error", f"Transaction processing failed: {e}")

    def _checkout_order(self, transaction_data: Dict):
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

        receipt_data = self.service.generate_receipt_data(order_id)
        if receipt_data:
            receipt_text = self.receipt_generator.generate_receipt(receipt_data)
            self._show_receipt_dialog(receipt_text, receipt_data)

        if self.on_transaction_complete:
            self.on_transaction_complete(
                {"order_id": order_id, "transaction_data": transaction_data, "receipt_data": receipt_data}
            )

        order_number = receipt_data["order_number"] if receipt_data else str(order_id)
        messagebox.showinfo("Success", f"Transaction completed successfully!\nOrder: {order_number}")

    def _hold_order(self, transaction_data: Dict):
        order_id = self.service.create_draft_order(
            user_id=self.user_info["id"],
            items=transaction_data["items"],
            order_name=transaction_data.get("order_name", ""),
        )

        if not order_id:
            messagebox.showerror("Error", "Failed to hold (save draft) order.")
            return

        messagebox.showinfo("Held", f"Order saved as draft.\nDraft ID: {order_id}")

    def _finalize_draft(self, transaction_data: Dict):
        order_id = transaction_data.get("order_id")
        if not order_id:
            order_id = simpledialog.askinteger("Finalize Draft", "Enter Draft Order ID:")
        if not order_id:
            return

        ok = self.service.finalize_draft_order(
            order_id=int(order_id),
            user_id=self.user_info["id"],
            payment_method=(transaction_data.get("payment_method") or "cash").lower(),
            discount_percent=transaction_data.get("discount_percent", 0),
            reference=transaction_data.get("reference"),
        )

        if not ok:
            messagebox.showerror("Error", "Failed to finalize draft order.")
            return

        receipt_data = self.service.generate_receipt_data(int(order_id))
        if receipt_data:
            receipt_text = self.receipt_generator.generate_receipt(receipt_data)
            self._show_receipt_dialog(receipt_text, receipt_data)

        messagebox.showinfo("Success", f"Draft finalized successfully!\nOrder ID: {order_id}")

    def _void_order(self, transaction_data: Dict):
        role = (self.user_info.get("role") or "").lower()
        if role not in ["owner", "admin", "manager"]:
            messagebox.showerror("Unauthorized", "Only owner/admin/manager can void orders.")
            return

        order_id = transaction_data.get("order_id")
        if not order_id:
            order_id = simpledialog.askinteger("Void Order", "Enter Order ID to void:")
        if not order_id:
            return

        reason = simpledialog.askstring("Void Reason", "Enter reason for voiding this order:")
        if not reason:
            return

        restock = messagebox.askyesno("Restock Ingredients", "Restock ingredients from this order?")
        ok = self.service.void_order(
            order_id=int(order_id),
            performed_by=self.user_info["id"],
            reason=reason,
            restock_ingredients=bool(restock),
        )

        if not ok:
            messagebox.showerror("Error", "Failed to void order.")
            return

        messagebox.showinfo("Voided", f"Order voided successfully.\nOrder ID: {order_id}")

    def _show_receipt_dialog(self, receipt_text: str, receipt_data: Dict):
        try:
            import customtkinter as ctk
            CTK_AVAILABLE = True
        except ImportError:
            import tkinter as tk
            CTK_AVAILABLE = False

        from tkinter import scrolledtext

        if CTK_AVAILABLE:
            receipt_window = ctk.CTkToplevel(self.parent_frame.master)
            receipt_window.title(f"Receipt - {receipt_data['order_number']}")
            receipt_window.geometry("500x600")

            text_widget = scrolledtext.ScrolledText(
                receipt_window, width=60, height=35, font=("Courier New", 9), bg="#1a1a2e", fg="white"
            )
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", receipt_text)
            text_widget.config(state="disabled")

            button_frame = ctk.CTkFrame(receipt_window, fg_color="transparent")
            button_frame.pack(fill="x", padx=10, pady=10)

            ctk.CTkButton(button_frame, text="Close", command=receipt_window.destroy, width=150).pack(
                side="right", padx=5
            )
        else:
            receipt_window = tk.Toplevel(self.parent_frame.master)
            receipt_window.title(f"Receipt - {receipt_data['order_number']}")
            receipt_window.geometry("500x600")

            text_widget = scrolledtext.ScrolledText(
                receipt_window, width=60, height=35, font=("Courier New", 9), bg="#1a1a2e", fg="white"
            )
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", receipt_text)
            text_widget.config(state="disabled")

            tk.Button(receipt_window, text="Close", command=receipt_window.destroy, width=15).pack(pady=10)
