try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    import tkinter as tk
    from tkinter import messagebox, ttk
    CTK_AVAILABLE = False

if CTK_AVAILABLE:
    import tkinter as tk
    from tkinter import messagebox, ttk

from datetime import datetime
from typing import Callable, Optional, List, Dict, Any

from config.settings import (
    COLOR_PRIMARY_BG,
    COLOR_SECONDARY_BG,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_TEXT_PRIMARY,
)
from reports.reports_service import ReportsService


class POSView:
    def __init__(
        self,
        parent,
        user_info: Dict,
        on_transaction_complete: Optional[Callable[[Dict], None]] = None,
        on_pos_action: Optional[Callable[[Dict], Any]] = None,
    ):
        self.parent = parent
        self.user_info = user_info
        self.on_transaction_complete = on_transaction_complete
        self.on_pos_action = on_pos_action

        self.cart: List[Dict] = []
        self.discount_percent = 0.0
        self.order_name = ""
        self.payment_method = "Cash"
        self.action = "checkout"

        self.products: List[Dict] = []
        self.categories = ["All"]

        self.reports_service = ReportsService()
        self.reports = []

        self.selected_draft_id: Optional[int] = None
        self.draft_cache: List[Dict] = []

        role = (self.user_info.get("role") or "").lower()
        self.can_void = role in {"owner", "admin", "manager"}

        self._build_ui()

    def _build_ui(self):
        if CTK_AVAILABLE:
            main_frame = ctk.CTkFrame(self.parent, fg_color=COLOR_PRIMARY_BG)
        else:
            main_frame = tk.Frame(self.parent, bg=COLOR_PRIMARY_BG)

        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=0)
        main_frame.grid_columnconfigure(2, weight=0)
        main_frame.grid_rowconfigure(0, weight=1)

        self._build_products_section(main_frame)
        self._build_order_section(main_frame)
        self._build_payment_section(main_frame)

    def _build_products_section(self, parent):
        if CTK_AVAILABLE:
            products_frame = ctk.CTkFrame(parent, fg_color=COLOR_SECONDARY_BG, corner_radius=10)
        else:
            products_frame = tk.Frame(parent, bg=COLOR_SECONDARY_BG)

        products_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        products_frame.grid_rowconfigure(2, weight=1)

        if CTK_AVAILABLE:
            header = ctk.CTkLabel(
                products_frame,
                text="Products",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            header = tk.Label(
                products_frame,
                text="Products",
                font=("Georgia", 16, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
        header.pack(padx=10, pady=(10, 5))

        if CTK_AVAILABLE:
            cat_lbl = ctk.CTkLabel(products_frame, text="Category:", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_PRIMARY)
        else:
            cat_lbl = tk.Label(products_frame, text="Category:", font=("Sans", 11), fg=COLOR_TEXT_PRIMARY, bg=COLOR_SECONDARY_BG)
        cat_lbl.pack(padx=10, pady=(5, 0), anchor="w")

        if CTK_AVAILABLE:
            self.category_var = ctk.StringVar(value="All")
            self.category_combo = ctk.CTkComboBox(
                products_frame,
                values=["All"],
                variable=self.category_var,
                command=self._on_category_changed,
                width=200,
            )
        else:
            self.category_var = tk.StringVar(value="All")
            self.category_combo = tk.OptionMenu(products_frame, self.category_var, "All", command=self._on_category_changed)
        self.category_combo.pack(padx=10, pady=(0, 10), fill="x")

        if CTK_AVAILABLE:
            tree_frame = ctk.CTkFrame(products_frame, fg_color="transparent")
        else:
            tree_frame = tk.Frame(products_frame, bg=COLOR_SECONDARY_BG)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("Product", "Price", "Add")
        self.products_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
        self.products_tree.heading("Product", text="Product")
        self.products_tree.heading("Price", text="Price")
        self.products_tree.heading("Add", text="+")
        self.products_tree.column("Product", width=140)
        self.products_tree.column("Price", width=60)
        self.products_tree.column("Add", width=35, anchor="center")
        self.products_tree.pack(fill="both", expand=True)
        self.products_tree.bind("<Button-1>", self._on_product_click)

        if CTK_AVAILABLE:
            qty_lbl = ctk.CTkLabel(products_frame, text="Qty:", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_PRIMARY)
        else:
            qty_lbl = tk.Label(products_frame, text="Qty:", font=("Sans", 11), fg=COLOR_TEXT_PRIMARY, bg=COLOR_SECONDARY_BG)
        qty_lbl.pack(padx=10, pady=(10, 0), anchor="w")

        if CTK_AVAILABLE:
            self.quantity_entry = ctk.CTkEntry(products_frame, width=200)
            self.quantity_entry.insert(0, "1")
        else:
            self.quantity_entry = tk.Entry(products_frame, width=25)
            self.quantity_entry.insert(0, "1")
        self.quantity_entry.pack(padx=10, pady=(0, 10), fill="x")

    def _on_product_click(self, event):
        item = self.products_tree.selection()
        if not item:
            return

        col = self.products_tree.identify("column", event.x, event.y)
        if col != "#3":
            return

        values = self.products_tree.item(item[0])["values"]
        product_name = values[0]
        price_str = str(values[1]).replace("₱", "").strip()

        try:
            price = float(price_str)
            qty_str = self.quantity_entry.get().strip()
            qty = int(qty_str) if qty_str else 1
            product_id = self.products_tree.item(item[0])["text"]
            self.add_item_to_cart(int(product_id), product_name, price, qty)
            self.quantity_entry.delete(0, "end")
            self.quantity_entry.insert(0, "1")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add item: {e}")

    def _on_category_changed(self, _choice):
        self._refresh_products_display()

    def populate_products(self, products: List[Dict], categories: List[str]):
        self.products = products
        self.categories = ["All"] + categories

        if CTK_AVAILABLE:
            self.category_combo.configure(values=self.categories)
        else:
            menu = self.category_combo["menu"]
            menu.delete(0, "end")
            for cat in self.categories:
                menu.add_command(label=cat, command=lambda c=cat: (self.category_var.set(c), self._on_category_changed(c)))

        self._refresh_products_display()

    def _refresh_products_display(self):
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        selected_cat = self.category_var.get()
        filtered = self.products if selected_cat == "All" else [p for p in self.products if p.get("category") == selected_cat]

        for product in filtered:
            values = (product["name"], f"₱ {float(product['price']):.2f}", "Add")
            self.products_tree.insert("", "end", iid=str(product["id"]), text=str(product["id"]), values=values)

    def _build_order_section(self, parent):
        if CTK_AVAILABLE:
            left_frame = ctk.CTkFrame(parent, fg_color="transparent")
        else:
            left_frame = tk.Frame(parent, bg=COLOR_PRIMARY_BG)

        left_frame.grid(row=0, column=1, sticky="nsew", padx=10)
        left_frame.grid_rowconfigure(2, weight=1)

        if CTK_AVAILABLE:
            header = ctk.CTkLabel(left_frame, text="Current Order", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLOR_ACCENT)
        else:
            header = tk.Label(left_frame, text="Current Order", font=("Georgia", 18, "bold"), fg=COLOR_ACCENT, bg=COLOR_PRIMARY_BG)
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        if CTK_AVAILABLE:
            name_lbl = ctk.CTkLabel(left_frame, text="Order Name:", font=ctk.CTkFont(size=12))
        else:
            name_lbl = tk.Label(left_frame, text="Order Name:", font=("Sans", 12), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PRIMARY_BG)
        name_lbl.grid(row=1, column=0, sticky="w")

        if CTK_AVAILABLE:
            self.order_name_entry = ctk.CTkEntry(left_frame, width=200)
        else:
            self.order_name_entry = tk.Entry(left_frame, width=25)
        self.order_name_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        if CTK_AVAILABLE:
            cart_frame = ctk.CTkFrame(left_frame, corner_radius=10, fg_color=COLOR_SECONDARY_BG)
        else:
            cart_frame = tk.Frame(left_frame, bg=COLOR_SECONDARY_BG)

        cart_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=10)
        cart_frame.grid_rowconfigure(1, weight=1)

        if CTK_AVAILABLE:
            cart_header = ctk.CTkLabel(cart_frame, text="Items in Cart", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT)
        else:
            cart_header = tk.Label(cart_frame, text="Items in Cart", font=("Georgia", 14, "bold"), fg=COLOR_ACCENT, bg=COLOR_SECONDARY_BG)
        cart_header.pack(padx=10, pady=(10, 5))

        if CTK_AVAILABLE:
            tree_frame = ctk.CTkFrame(cart_frame, fg_color="transparent")
        else:
            tree_frame = tk.Frame(cart_frame, bg=COLOR_SECONDARY_BG)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("Item", "Qty", "Price", "Subtotal", "Remove")
        self.cart_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
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
        self.cart_tree.bind("<Button-1>", self._on_cart_click)

        if CTK_AVAILABLE:
            btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        else:
            btn_frame = tk.Frame(left_frame, bg=COLOR_PRIMARY_BG)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        if CTK_AVAILABLE:
            clear_btn = ctk.CTkButton(btn_frame, text="Clear Cart", width=100, fg_color=COLOR_ERROR, hover_color="#a02020", command=self._clear_cart)
        else:
            clear_btn = tk.Button(btn_frame, text="Clear Cart", width=15, bg=COLOR_ERROR, fg="white", relief="flat", command=self._clear_cart)
        clear_btn.pack(side="left", padx=5)

    def _build_payment_section(self, parent):
        if CTK_AVAILABLE:
            right_frame = ctk.CTkFrame(parent, fg_color="transparent")
        else:
            right_frame = tk.Frame(parent, bg=COLOR_PRIMARY_BG)

        right_frame.grid(row=0, column=2, sticky="nsew")
        right_frame.grid_rowconfigure(3, weight=1)

        if CTK_AVAILABLE:
            header = ctk.CTkLabel(right_frame, text="Payment", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLOR_ACCENT)
        else:
            header = tk.Label(right_frame, text="Payment", font=("Georgia", 18, "bold"), fg=COLOR_ACCENT, bg=COLOR_PRIMARY_BG)
        header.grid(row=0, column=0, sticky="w", pady=(0, 15), columnspan=2)

        if CTK_AVAILABLE:
            discount_lbl = ctk.CTkLabel(right_frame, text="Discount (%):", font=ctk.CTkFont(size=12))
        else:
            discount_lbl = tk.Label(right_frame, text="Discount (%):", font=("Sans", 12), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PRIMARY_BG)
        discount_lbl.grid(row=1, column=0, sticky="w", pady=(0, 5))

        if CTK_AVAILABLE:
            self.discount_entry = ctk.CTkEntry(right_frame, width=150)
            self.discount_entry.insert(0, "0")
        else:
            self.discount_entry = tk.Entry(right_frame, width=20)
            self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0))
        self.discount_entry.bind("<KeyRelease>", lambda _e: self._update_total())

        if CTK_AVAILABLE:
            payment_lbl = ctk.CTkLabel(right_frame, text="Payment Method:", font=ctk.CTkFont(size=12))
        else:
            payment_lbl = tk.Label(right_frame, text="Payment Method:", font=("Sans", 12), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PRIMARY_BG)
        payment_lbl.grid(row=2, column=0, sticky="w", pady=(15, 5))

        if CTK_AVAILABLE:
            self.payment_var = ctk.StringVar(value="Cash")
            payment_combo = ctk.CTkComboBox(right_frame, values=["Cash", "GCash", "Bank Transfer"], variable=self.payment_var, width=150)
        else:
            self.payment_var = tk.StringVar(value="Cash")
            payment_combo = tk.OptionMenu(right_frame, self.payment_var, "Cash", "GCash", "Bank Transfer")
        payment_combo.grid(row=2, column=1, sticky="ew", padx=(5, 0))
        self.payment_var.trace("w", lambda *_args: self._on_payment_changed())

        if CTK_AVAILABLE:
            self.reference_lbl = ctk.CTkLabel(right_frame, text="Reference #:", font=ctk.CTkFont(size=12), text_color="#999999")
        else:
            self.reference_lbl = tk.Label(right_frame, text="Reference #:", font=("Sans", 12), fg="#999999", bg=COLOR_PRIMARY_BG)
        self.reference_lbl.grid(row=3, column=0, sticky="w", pady=(15, 5))

        if CTK_AVAILABLE:
            self.reference_entry = ctk.CTkEntry(right_frame, width=150)
        else:
            self.reference_entry = tk.Entry(right_frame, width=20)
        self.reference_entry.grid(row=3, column=1, sticky="ew", padx=(5, 0))
        self.reference_lbl.grid_remove()
        self.reference_entry.grid_remove()

        if CTK_AVAILABLE:
            spacer = ctk.CTkFrame(right_frame, fg_color="transparent", height=20)
        else:
            spacer = tk.Frame(right_frame, bg=COLOR_PRIMARY_BG, height=20)
        spacer.grid(row=4, column=0, columnspan=2, sticky="ew")

        if CTK_AVAILABLE:
            total_frame = ctk.CTkFrame(right_frame, corner_radius=10, fg_color=COLOR_SECONDARY_BG)
        else:
            total_frame = tk.Frame(right_frame, bg=COLOR_SECONDARY_BG)
        total_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        if CTK_AVAILABLE:
            self.subtotal_var = ctk.StringVar(value="0.00")
            self.discount_display_var = ctk.StringVar(value="0.00")
            self.total_var = ctk.StringVar(value="0.00")
        else:
            self.subtotal_var = tk.StringVar(value="0.00")
            self.discount_display_var = tk.StringVar(value="0.00")
            self.total_var = tk.StringVar(value="0.00")

        if CTK_AVAILABLE:
            ctk.CTkLabel(total_frame, text="Subtotal:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15, pady=(10, 0))
            ctk.CTkLabel(total_frame, textvariable=self.subtotal_var, font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=15, pady=(0, 10))
            ctk.CTkLabel(total_frame, text="Discount:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15, pady=(10, 0))
            ctk.CTkLabel(total_frame, textvariable=self.discount_display_var, font=ctk.CTkFont(size=14), text_color=COLOR_ERROR).pack(anchor="w", padx=15, pady=(0, 10))
            ctk.CTkLabel(total_frame, text="Total Amount:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 0))
            ctk.CTkLabel(total_frame, textvariable=self.total_var, font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_SUCCESS).pack(anchor="w", padx=15, pady=(0, 15))
        else:
            tk.Label(total_frame, text="Subtotal:", font=("Sans", 12), fg=COLOR_TEXT_PRIMARY, bg=COLOR_SECONDARY_BG).pack(anchor="w", padx=15, pady=(10, 0))
            tk.Label(total_frame, textvariable=self.subtotal_var, font=("Georgia", 14, "bold"), fg=COLOR_ACCENT, bg=COLOR_SECONDARY_BG).pack(anchor="w", padx=15, pady=(0, 10))
            tk.Label(total_frame, text="Discount:", font=("Sans", 12), fg=COLOR_TEXT_PRIMARY, bg=COLOR_SECONDARY_BG).pack(anchor="w", padx=15, pady=(10, 0))
            tk.Label(total_frame, textvariable=self.discount_display_var, font=("Georgia", 14), fg=COLOR_ERROR, bg=COLOR_SECONDARY_BG).pack(anchor="w", padx=15, pady=(0, 10))
            tk.Label(total_frame, text="Total Amount:", font=("Georgia", 14, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_SECONDARY_BG).pack(anchor="w", padx=15, pady=(15, 0))
            tk.Label(total_frame, textvariable=self.total_var, font=("Georgia", 28, "bold"), fg=COLOR_SUCCESS, bg=COLOR_SECONDARY_BG).pack(anchor="w", padx=15, pady=(0, 15))

        if CTK_AVAILABLE:
            complete_btn = ctk.CTkButton(
                right_frame,
                text="Checkout (Enter)",
                width=250,
                height=45,
                fg_color=COLOR_SUCCESS,
                hover_color="#1f7f1f",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda: self._complete_transaction(action="checkout"),
            )
        else:
            complete_btn = tk.Button(
                right_frame,
                text="Checkout (Enter)",
                width=30,
                height=2,
                bg=COLOR_SUCCESS,
                fg="white",
                font=("Georgia", 14, "bold"),
                relief="flat",
                command=lambda: self._complete_transaction(action="checkout"),
            )
        complete_btn.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 8))

        # --- NEW: 3 buttons right under Checkout ---
        if CTK_AVAILABLE:
            hold_btn = ctk.CTkButton(
                right_frame,
                text="Hold Order (Draft)",
                width=250,
                fg_color="#444a6e",
                hover_color="#565d8a",
                command=lambda: self._complete_transaction(action="hold"),
            )
            hold_btn.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 8))

            finalize_btn = ctk.CTkButton(
                right_frame,
                text="Finalize Draft",
                width=250,
                fg_color="#3a3a4e",
                hover_color="#4a4a5e",
                command=lambda: self._complete_transaction(action="finalize_draft"),
            )
            finalize_btn.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 8))

            void_btn = ctk.CTkButton(
                right_frame,
                text="Void Order",
                width=250,
                fg_color=COLOR_ERROR,
                hover_color="#b02a2a",
                command=lambda: self._complete_transaction(action="void"),
            )
            void_btn.grid(row=9, column=0, columnspan=2, sticky="ew")
        else:
            # Fallback tkinter buttons (keep functional parity)
            hold_btn = tk.Button(
                right_frame,
                text="Hold Order (Draft)",
                width=30,
                height=2,
                bg="#444a6e",
                fg="white",
                relief="flat",
                command=lambda: self._complete_transaction(action="hold"),
            )
            hold_btn.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 8))

            finalize_btn = tk.Button(
                right_frame,
                text="Finalize Draft",
                width=30,
                height=2,
                bg="#3a3a4e",
                fg="white",
                relief="flat",
                command=lambda: self._complete_transaction(action="finalize_draft"),
            )
            finalize_btn.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 8))

            void_btn = tk.Button(
                right_frame,
                text="Void Order",
                width=30,
                height=2,
                bg=COLOR_ERROR,
                fg="white",
                relief="flat",
                command=lambda: self._complete_transaction(action="void"),
            )
            void_btn.grid(row=9, column=0, columnspan=2, sticky="ew")

        # Enter key should checkout
        self.parent.bind("<Return>", lambda _e: self._complete_transaction(action="checkout"))

    def _on_cart_click(self, event):
        item = self.cart_tree.selection()
        if not item:
            return
        col = self.cart_tree.identify("column", event.x, event.y)
        if col == "#5":
            index = int(self.cart_tree.index(item[0]))
            if 0 <= index < len(self.cart):
                self.cart.pop(index)
                self._refresh_cart_display()
                self._update_total()

    def _clear_cart(self):
        self.cart.clear()
        self._refresh_cart_display()
        self._update_total()

    def _refresh_cart_display(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        for item_dict in self.cart:
            values = (
                item_dict["name"],
                item_dict["quantity"],
                f"₱ {float(item_dict['price']):.2f}",
                f"₱ {float(item_dict['subtotal']):.2f}",
                "Remove",
            )
            self.cart_tree.insert("", "end", values=values)

    def _on_payment_changed(self):
        method = self.payment_var.get()
        if method == "Bank Transfer":
            self.reference_lbl.grid()
            self.reference_entry.grid()
        else:
            self.reference_lbl.grid_remove()
            self.reference_entry.grid_remove()

    def _update_total(self):
        subtotal = sum(float(item["subtotal"]) for item in self.cart)
        self.subtotal_var.set(f"{subtotal:.2f}")

        try:
            discount_percent = float(self.discount_entry.get())
        except Exception:
            discount_percent = 0.0

        discount_amount = subtotal * (discount_percent / 100.0)
        self.discount_display_var.set(f"{discount_amount:.2f}")

        total = subtotal - discount_amount
        self.total_var.set(f"{total:.2f}")

    def _validate_common_fields(self) -> Optional[Dict]:
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to the cart")
            return None

        order_name = self.order_name_entry.get().strip()
        if not order_name:
            messagebox.showwarning("Missing Order Name", "Please enter an order name")
            self.order_name_entry.focus()
            return None

        payment_method = self.payment_var.get()
        reference = None
        if payment_method == "Bank Transfer":
            reference = self.reference_entry.get().strip()
            if not reference:
                messagebox.showwarning("Missing Reference", "Please enter a bank reference number")
                self.reference_entry.focus()
                return None

        try:
            discount_percent = float(self.discount_entry.get() or "0")
        except Exception:
            discount_percent = 0.0

        return {
            "order_name": order_name,
            "items": self.cart,
            "subtotal": float(self.subtotal_var.get()),
            "discount_percent": float(discount_percent),
            "discount_amount": float(self.discount_display_var.get()),
            "total": float(self.total_var.get()),
            "payment_method": payment_method,
            "reference": reference,
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_info["id"],
        }

    def _fire_action(self, payload: Dict) -> Any:
        if self.on_pos_action:
            return self.on_pos_action(payload)
        if self.on_transaction_complete:
            return self.on_transaction_complete(payload)
        return None

    # --- NEW unified action dispatcher ---
    def _complete_transaction(self, action: str = "checkout"):
        # Checkout / Hold: send full transaction
        if action in ("checkout", "hold"):
            tx = self._validate_common_fields()
            if not tx:
                return
            tx["action"] = action
            self._fire_action(tx)
            self._after_success_reset()
            return

        # Finalize draft: select draft + payment details
        if action == "finalize_draft":
            draft = self._select_draft_dialog()
            if not draft:
                return

            order_id = int(draft["id"])
            payment_method = self.payment_var.get()

            reference = None
            if payment_method == "Bank Transfer":
                reference = self.reference_entry.get().strip()
                if not reference:
                    messagebox.showwarning("Missing Reference", "Please enter a bank reference number")
                    self.reference_entry.focus()
                    return

            try:
                discount_percent = float(self.discount_entry.get() or "0")
            except Exception:
                discount_percent = 0.0

            payload = {
                "action": "finalize_draft",
                "order_id": order_id,
                "payment_method": payment_method,
                "reference": reference,
                "discount_percent": float(discount_percent),
            }
            self._fire_action(payload)
            return

        # Void: require permission + pick order (including completed)
        if action == "void":
            if not self.can_void:
                messagebox.showerror("Unauthorized", "Only owner/admin/manager can void orders.")
                return

            draft = self._select_draft_dialog(include_completed=True)
            if not draft:
                return

            payload = {"action": "void", "order_id": int(draft["id"])}
            self._fire_action(payload)
            return

    def _after_success_reset(self):
        self._clear_cart()
        self.order_name_entry.delete(0, "end")
        self.discount_entry.delete(0, "end")
        self.discount_entry.insert(0, "0")
        self.payment_var.set("Cash")
        self.reference_entry.delete(0, "end")

    def _select_draft_dialog(self, include_completed: bool = False) -> Optional[Dict]:
        drafts = self._fetch_drafts(include_completed=include_completed)
        if not drafts:
            messagebox.showinfo("No Orders", "No draft/pending orders found.")
            return None

        items = [f"{d['id']} | {d.get('order_number','')} | {d.get('status','')} | {d.get('order_name','') or ''}" for d in drafts]

        selected = {"value": None}

        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.parent)
            win.title("Select Order")
            win.geometry("520x220")

            lbl = ctk.CTkLabel(win, text="Select an order:", font=ctk.CTkFont(size=14, weight="bold"))
            lbl.pack(padx=15, pady=(15, 10), anchor="w")

            var = ctk.StringVar(value=items[0])
            combo = ctk.CTkComboBox(win, values=items, variable=var, width=480)
            combo.pack(padx=15, pady=10)

            def on_ok():
                selected["value"] = var.get()
                win.destroy()

            btn = ctk.CTkButton(win, text="OK", command=on_ok, width=120)
            btn.pack(pady=10)

            win.grab_set()
            win.wait_window()
        else:
            win = tk.Toplevel(self.parent)
            win.title("Select Order")
            win.geometry("520x220")

            tk.Label(win, text="Select an order:", font=("Arial", 12, "bold")).pack(padx=15, pady=(15, 10), anchor="w")

            var = tk.StringVar(value=items[0])
            combo = ttk.Combobox(win, textvariable=var, values=items, width=65, state="readonly")
            combo.pack(padx=15, pady=10)

            def on_ok():
                selected["value"] = var.get()
                win.destroy()

            tk.Button(win, text="OK", command=on_ok, width=12).pack(pady=10)

            win.grab_set()
            win.wait_window()

        if not selected["value"]:
            return None

        chosen = selected["value"].split("|")[0].strip()
        for d in drafts:
            if str(d["id"]) == chosen:
                return d

        return None

    def _fetch_drafts(self, include_completed: bool = False) -> List[Dict]:
        payload = {"action": "list_drafts", "include_completed": bool(include_completed)}
        res = self._fire_action(payload)
        if isinstance(res, list):
            return res
        return []

    def _fetch_draft_items(self, order_id: int) -> Optional[List[Dict]]:
        payload = {"action": "get_order_items", "order_id": int(order_id)}
        res = self._fire_action(payload)
        if isinstance(res, list):
            return res
        messagebox.showerror("Error", "Could not load draft items.")
        return None

    def _load_items_into_cart(self, items: List[Dict]):
        self.cart = []
        for it in items:
            pid = int(it["id"])
            name = str(it["name"])
            price = float(it["price"])
            qty = int(it["quantity"])
            self.cart.append(
                {
                    "id": pid,
                    "name": name,
                    "price": price,
                    "quantity": qty,
                    "subtotal": float(qty * price),
                }
            )
        self._refresh_cart_display()
        self._update_total()

    def add_item_to_cart(self, item_id: int, item_name: str, price: float, quantity: int = 1):
        for item in self.cart:
            if int(item["id"]) == int(item_id):
                item["quantity"] += int(quantity)
                item["subtotal"] = float(item["quantity"]) * float(item["price"])
                self._refresh_cart_display()
                self._update_total()
                return

        self.cart.append(
            {
                "id": int(item_id),
                "name": item_name,
                "price": float(price),
                "quantity": int(quantity),
                "subtotal": float(quantity) * float(price),
            }
        )
        self._refresh_cart_display()
        self._update_total()

    def get_cart(self) -> List[Dict]:
        return self.cart.copy()

    def get_total(self) -> float:
        try:
            return float(self.total_var.get())
        except Exception:
            return 0.0
