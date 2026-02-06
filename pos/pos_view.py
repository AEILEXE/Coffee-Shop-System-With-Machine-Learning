"""
CAFÉCRAFT POS INTERFACE

Responsibilities:
- Point of Sale screen
- Menu item display with quantities
- Order management (add, remove items)
- Discount support
- Order name input
- Payment method selection (Cash, GCash, Bank Transfer)
- Enter key confirms transaction
- Real-time total calculation
- Receipt generation trigger

Uses CustomTkinter widgets.
No direct database queries (should use service layer).
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    import tkinter as tk
    from tkinter import messagebox, ttk
    CTK_AVAILABLE = False

if CTK_AVAILABLE:
    from tkinter import messagebox, ttk
from datetime import datetime
from typing import Callable, Optional, List, Dict
from config.settings import (
    COLOR_PRIMARY_BG,
    COLOR_SECONDARY_BG,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_TEXT_PRIMARY,
    FONT_HEADING,
    FONT_NORMAL,
)


class POSView:
    """Point of Sale interface for CAFÉCRAFT."""

    def __init__(
        self,
        parent,
        user_info: Dict,
        on_transaction_complete: Optional[Callable[[Dict], None]] = None,
    ):
        """
        Initialize POS view.

        Args:
            parent: Parent widget (content frame).
            user_info: Current user dict with 'id', 'name', 'role'.
            on_transaction_complete: Callback when transaction completes.
        """
        self.parent = parent
        self.user_info = user_info
        self.on_transaction_complete = on_transaction_complete

        # POS state
        self.cart = []  # List of {'id', 'name', 'price', 'quantity', 'subtotal'}
        self.discount_percent = 0.0
        self.order_name = ""
        self.payment_method = "Cash"

        # Build POS interface
        self._build_ui()

    def _build_ui(self):
        """Build the POS interface layout."""
        if CTK_AVAILABLE:
            main_frame = ctk.CTkFrame(self.parent, fg_color=COLOR_PRIMARY_BG)
        else:
            main_frame = tk.Frame(self.parent, bg=COLOR_PRIMARY_BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left side - Order items
        self._build_order_section(main_frame)

        # Right side - Payment & Total
        self._build_payment_section(main_frame)

    def _build_order_section(self, parent):
        """Build left side with order items and controls."""
        if CTK_AVAILABLE:
            left_frame = ctk.CTkFrame(parent, fg_color="transparent")
        else:
            left_frame = tk.Frame(parent, bg=COLOR_PRIMARY_BG)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_rowconfigure(2, weight=1)

        # Header
        if CTK_AVAILABLE:
            header = ctk.CTkLabel(
                left_frame,
                text="Current Order",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            header = tk.Label(
                left_frame,
                text="Current Order",
                font=("Georgia", 18, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_PRIMARY_BG,
            )
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Order name input
        if CTK_AVAILABLE:
            name_lbl = ctk.CTkLabel(
                left_frame,
                text="Order Name:",
                font=ctk.CTkFont(size=12),
            )
        else:
            name_lbl = tk.Label(
                left_frame,
                text="Order Name:",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_PRIMARY_BG,
            )
        name_lbl.grid(row=1, column=0, sticky="w")

        if CTK_AVAILABLE:
            self.order_name_entry = ctk.CTkEntry(left_frame, width=200)
        else:
            self.order_name_entry = tk.Entry(left_frame, width=25)
        self.order_name_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        # Cart items frame
        if CTK_AVAILABLE:
            cart_frame = ctk.CTkFrame(left_frame, corner_radius=10, fg_color=COLOR_SECONDARY_BG)
        else:
            cart_frame = tk.Frame(left_frame, bg=COLOR_SECONDARY_BG)
        cart_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=10)
        cart_frame.grid_rowconfigure(1, weight=1)

        # Cart header
        if CTK_AVAILABLE:
            cart_header = ctk.CTkLabel(
                cart_frame,
                text="Items in Cart",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            cart_header = tk.Label(
                cart_frame,
                text="Items in Cart",
                font=("Georgia", 14, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
        cart_header.pack(padx=10, pady=(10, 5))

        # Cart tree/table
        if CTK_AVAILABLE:
            tree_frame = ctk.CTkFrame(cart_frame, fg_color="transparent")
        else:
            tree_frame = tk.Frame(cart_frame, bg=COLOR_SECONDARY_BG)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview columns
        columns = ("Item", "Qty", "Price", "Subtotal", "Remove")
        self.cart_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=10,
        )

        # Define column headings and widths
        self.cart_tree.heading("Item", text="Item")
        self.cart_tree.heading("Qty", text="Qty")
        self.cart_tree.heading("Price", text="Price")
        self.cart_tree.heading("Subtotal", text="Subtotal")
        self.cart_tree.heading("Remove", text="X")

        self.cart_tree.column("Item", width=150)
        self.cart_tree.column("Qty", width=50, anchor="center")
        self.cart_tree.column("Price", width=80)
        self.cart_tree.column("Subtotal", width=100)
        self.cart_tree.column("Remove", width=40, anchor="center")

        self.cart_tree.pack(fill="both", expand=True)

        # Bind click to remove button
        self.cart_tree.bind("<Button-1>", self._on_cart_click)

        # Action buttons
        if CTK_AVAILABLE:
            btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        else:
            btn_frame = tk.Frame(left_frame, bg=COLOR_PRIMARY_BG)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        if CTK_AVAILABLE:
            clear_btn = ctk.CTkButton(
                btn_frame,
                text="Clear Cart",
                width=100,
                fg_color=COLOR_ERROR,
                hover_color="#a02020",
                command=self._clear_cart,
            )
        else:
            clear_btn = tk.Button(
                btn_frame,
                text="Clear Cart",
                width=15,
                bg=COLOR_ERROR,
                fg="white",
                relief="flat",
                command=self._clear_cart,
            )
        clear_btn.pack(side="left", padx=5)

    def _build_payment_section(self, parent):
        """Build right side with payment and total."""
        if CTK_AVAILABLE:
            right_frame = ctk.CTkFrame(parent, fg_color="transparent")
        else:
            right_frame = tk.Frame(parent, bg=COLOR_PRIMARY_BG)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(3, weight=1)

        # Header
        if CTK_AVAILABLE:
            header = ctk.CTkLabel(
                right_frame,
                text="Payment",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            header = tk.Label(
                right_frame,
                text="Payment",
                font=("Georgia", 18, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_PRIMARY_BG,
            )
        header.grid(row=0, column=0, sticky="w", pady=(0, 15))

        # Discount input
        if CTK_AVAILABLE:
            discount_lbl = ctk.CTkLabel(
                right_frame,
                text="Discount (%):",
                font=ctk.CTkFont(size=12),
            )
        else:
            discount_lbl = tk.Label(
                right_frame,
                text="Discount (%):",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_PRIMARY_BG,
            )
        discount_lbl.grid(row=1, column=0, sticky="w", pady=(0, 5))

        if CTK_AVAILABLE:
            self.discount_entry = ctk.CTkEntry(right_frame, width=150)
            self.discount_entry.insert(0, "0")
        else:
            self.discount_entry = tk.Entry(right_frame, width=20)
            self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0))
        self.discount_entry.bind("<KeyRelease>", lambda e: self._update_total())

        # Payment method
        if CTK_AVAILABLE:
            payment_lbl = ctk.CTkLabel(
                right_frame,
                text="Payment Method:",
                font=ctk.CTkFont(size=12),
            )
        else:
            payment_lbl = tk.Label(
                right_frame,
                text="Payment Method:",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_PRIMARY_BG,
            )
        payment_lbl.grid(row=2, column=0, sticky="w", pady=(15, 5))

        if CTK_AVAILABLE:
            self.payment_var = ctk.StringVar(value="Cash")
            payment_combo = ctk.CTkComboBox(
                right_frame,
                values=["Cash", "GCash", "Bank Transfer"],
                variable=self.payment_var,
                width=150,
            )
        else:
            self.payment_var = tk.StringVar(value="Cash")
            payment_combo = tk.OptionMenu(
                right_frame,
                self.payment_var,
                "Cash",
                "GCash",
                "Bank Transfer",
            )
        payment_combo.grid(row=2, column=1, sticky="ew", padx=(5, 0))
        self.payment_var.trace("w", lambda *args: self._on_payment_changed())

        # Bank reference (shown only for Bank Transfer)
        if CTK_AVAILABLE:
            self.reference_lbl = ctk.CTkLabel(
                right_frame,
                text="Reference #:",
                font=ctk.CTkFont(size=12),
                text_color="#999999",
            )
        else:
            self.reference_lbl = tk.Label(
                right_frame,
                text="Reference #:",
                font=("Sans", 12),
                fg="#999999",
                bg=COLOR_PRIMARY_BG,
            )
        self.reference_lbl.grid(row=3, column=0, sticky="w", pady=(15, 5))

        if CTK_AVAILABLE:
            self.reference_entry = ctk.CTkEntry(right_frame, width=150)
        else:
            self.reference_entry = tk.Entry(right_frame, width=20)
        self.reference_entry.grid(row=3, column=1, sticky="ew", padx=(5, 0))
        self.reference_entry.grid_remove()  # Hidden by default

        # Spacer
        if CTK_AVAILABLE:
            spacer = ctk.CTkFrame(right_frame, fg_color="transparent", height=20)
        else:
            spacer = tk.Frame(right_frame, bg=COLOR_PRIMARY_BG, height=20)
        spacer.grid(row=4, column=0, columnspan=2, sticky="ew")

        # Total section
        if CTK_AVAILABLE:
            total_frame = ctk.CTkFrame(right_frame, corner_radius=10, fg_color=COLOR_SECONDARY_BG)
        else:
            total_frame = tk.Frame(right_frame, bg=COLOR_SECONDARY_BG)
        total_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        # Subtotal
        if CTK_AVAILABLE:
            subtotal_lbl = ctk.CTkLabel(
                total_frame,
                text="Subtotal:",
                font=ctk.CTkFont(size=12),
            )
        else:
            subtotal_lbl = tk.Label(
                total_frame,
                text="Subtotal:",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_SECONDARY_BG,
            )
        subtotal_lbl.pack(anchor="w", padx=15, pady=(10, 0))

        if CTK_AVAILABLE:
            self.subtotal_var = ctk.StringVar(value="0.00")
            self.subtotal_display = ctk.CTkLabel(
                total_frame,
                textvariable=self.subtotal_var,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            self.subtotal_var = tk.StringVar(value="0.00")
            self.subtotal_display = tk.Label(
                total_frame,
                textvariable=self.subtotal_var,
                font=("Georgia", 14, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
        self.subtotal_display.pack(anchor="w", padx=15, pady=(0, 10))

        # Discount display
        if CTK_AVAILABLE:
            discount_disp_lbl = ctk.CTkLabel(
                total_frame,
                text="Discount:",
                font=ctk.CTkFont(size=12),
            )
        else:
            discount_disp_lbl = tk.Label(
                total_frame,
                text="Discount:",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_SECONDARY_BG,
            )
        discount_disp_lbl.pack(anchor="w", padx=15, pady=(10, 0))

        if CTK_AVAILABLE:
            self.discount_display_var = ctk.StringVar(value="0.00")
            self.discount_display = ctk.CTkLabel(
                total_frame,
                textvariable=self.discount_display_var,
                font=ctk.CTkFont(size=14),
                text_color=COLOR_ERROR,
            )
        else:
            self.discount_display_var = tk.StringVar(value="0.00")
            self.discount_display = tk.Label(
                total_frame,
                textvariable=self.discount_display_var,
                font=("Georgia", 14),
                fg=COLOR_ERROR,
                bg=COLOR_SECONDARY_BG,
            )
        self.discount_display.pack(anchor="w", padx=15, pady=(0, 10))

        # Total amount
        if CTK_AVAILABLE:
            total_lbl = ctk.CTkLabel(
                total_frame,
                text="Total Amount:",
                font=ctk.CTkFont(size=14, weight="bold"),
            )
        else:
            total_lbl = tk.Label(
                total_frame,
                text="Total Amount:",
                font=("Georgia", 14, "bold"),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_SECONDARY_BG,
            )
        total_lbl.pack(anchor="w", padx=15, pady=(15, 0))

        if CTK_AVAILABLE:
            self.total_var = ctk.StringVar(value="0.00")
            self.total_display = ctk.CTkLabel(
                total_frame,
                textvariable=self.total_var,
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=COLOR_SUCCESS,
            )
        else:
            self.total_var = tk.StringVar(value="0.00")
            self.total_display = tk.Label(
                total_frame,
                textvariable=self.total_var,
                font=("Georgia", 28, "bold"),
                fg=COLOR_SUCCESS,
                bg=COLOR_SECONDARY_BG,
            )
        self.total_display.pack(anchor="w", padx=15, pady=(0, 15))

        # Complete transaction button
        if CTK_AVAILABLE:
            complete_btn = ctk.CTkButton(
                right_frame,
                text="Complete Transaction (Enter)",
                width=250,
                height=50,
                fg_color=COLOR_SUCCESS,
                hover_color="#1f7f1f",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=self._complete_transaction,
            )
        else:
            complete_btn = tk.Button(
                right_frame,
                text="Complete Transaction (Enter)",
                width=30,
                height=3,
                bg=COLOR_SUCCESS,
                fg="white",
                font=("Georgia", 14, "bold"),
                relief="flat",
                command=self._complete_transaction,
            )
        complete_btn.grid(row=6, column=0, columnspan=2, sticky="ew", pady=15)

        # Bind Enter key
        self.parent.bind("<Return>", lambda e: self._complete_transaction())

    def _on_cart_click(self, event):
        """Handle clicks on cart tree (for removing items)."""
        item = self.cart_tree.selection()
        if not item:
            return

        # Click on "Remove" column (rightmost)
        col = self.cart_tree.identify("column", event.x, event.y)
        if col == "#5":  # Remove column
            index = int(self.cart_tree.index(item[0]))
            self.cart.pop(index)
            self._refresh_cart_display()
            self._update_total()

    def _clear_cart(self):
        """Clear all items from cart."""
        self.cart.clear()
        self._refresh_cart_display()
        self._update_total()

    def _refresh_cart_display(self):
        """Refresh the cart tree display."""
        # Clear tree
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        # Add items
        for item_dict in self.cart:
            values = (
                item_dict["name"],
                item_dict["quantity"],
                f"₱ {item_dict['price']:.2f}",
                f"₱ {item_dict['subtotal']:.2f}",
                "Remove",
            )
            self.cart_tree.insert("", "end", values=values)

    def _on_payment_changed(self):
        """Handle payment method change."""
        method = self.payment_var.get()
        if method == "Bank Transfer":
            self.reference_lbl.grid()
            self.reference_entry.grid()
        else:
            self.reference_lbl.grid_remove()
            self.reference_entry.grid_remove()

    def _update_total(self):
        """Update total amount based on cart and discount."""
        # Calculate subtotal
        subtotal = sum(item["subtotal"] for item in self.cart)
        self.subtotal_var.set(f"{subtotal:.2f}")

        # Get discount percentage
        try:
            discount_percent = float(self.discount_entry.get())
        except ValueError:
            discount_percent = 0

        # Calculate discount amount
        discount_amount = subtotal * (discount_percent / 100)
        self.discount_display_var.set(f"{discount_amount:.2f}")

        # Calculate total
        total = subtotal - discount_amount
        self.total_var.set(f"{total:.2f}")

    def _complete_transaction(self):
        """Complete the transaction."""
        # Validate
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to the cart")
            return

        order_name = self.order_name_entry.get().strip()
        if not order_name:
            messagebox.showwarning("Missing Order Name", "Please enter an order name")
            self.order_name_entry.focus()
            return

        payment_method = self.payment_var.get()
        reference = None

        if payment_method == "Bank Transfer":
            reference = self.reference_entry.get().strip()
            if not reference:
                messagebox.showwarning("Missing Reference", "Please enter a bank reference number")
                self.reference_entry.focus()
                return

        # Build transaction dict
        transaction = {
            "order_name": order_name,
            "items": self.cart,
            "subtotal": float(self.subtotal_var.get()),
            "discount_percent": float(self.discount_entry.get()),
            "discount_amount": float(self.discount_display_var.get()),
            "total": float(self.total_var.get()),
            "payment_method": payment_method,
            "reference": reference,
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_info["id"],
        }

        # Invoke callback
        if self.on_transaction_complete:
            self.on_transaction_complete(transaction)

        # Clear for next transaction
        self._clear_cart()
        self.order_name_entry.delete(0, "end")
        self.discount_entry.delete(0, "end")
        self.discount_entry.insert(0, "0")
        self.payment_var.set("Cash")
        self.reference_entry.delete(0, "end")

        messagebox.showinfo("Success", f"Transaction completed for {order_name}")

    def add_item_to_cart(
        self,
        item_id: int,
        item_name: str,
        price: float,
        quantity: int = 1,
    ):
        """
        Add an item to the cart.

        Args:
            item_id: Product ID.
            item_name: Product name.
            price: Product price.
            quantity: Quantity (default 1).
        """
        # Check if item exists
        for item in self.cart:
            if item["id"] == item_id:
                item["quantity"] += quantity
                item["subtotal"] = item["quantity"] * item["price"]
                self._refresh_cart_display()
                self._update_total()
                return

        # Add new item
        self.cart.append({
            "id": item_id,
            "name": item_name,
            "price": price,
            "quantity": quantity,
            "subtotal": quantity * price,
        })

        self._refresh_cart_display()
        self._update_total()

    def get_cart(self) -> List[Dict]:
        """Get current cart items."""
        return self.cart.copy()

    def get_total(self) -> float:
        """Get current total amount."""
        try:
            return float(self.total_var.get())
        except ValueError:
            return 0.0
