"""
CAFÉCRAFT INVENTORY MANAGEMENT INTERFACE

Responsibilities:
- Inventory table (Treeview) with stock levels
- Stock quantity display and update
- Low-stock indicators (visual warnings)
- Reorder threshold configuration
- Add, update, and remove ingredients
- Search and filter functionality

Uses CustomTkinter + Tkinter Treeview.
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
from typing import Callable, Optional, List, Dict
from config.settings import (
    COLOR_PRIMARY_BG,
    COLOR_SECONDARY_BG,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_WARNING,
    COLOR_TEXT_PRIMARY,
)


class InventoryView:
    """Inventory management interface for CAFÉCRAFT."""

    def __init__(
        self,
        parent,
        user_info: Dict,
        on_stock_update: Optional[Callable[[Dict], None]] = None,
        on_ingredient_added: Optional[Callable[[Dict], None]] = None,
    ):
        """
        Initialize inventory view.

        Args:
            parent: Parent widget (content frame).
            user_info: Current user dict.
            on_stock_update: Callback when stock is updated.
            on_ingredient_added: Callback when new ingredient added.
        """
        self.parent = parent
        self.user_info = user_info
        self.on_stock_update = on_stock_update
        self.on_ingredient_added = on_ingredient_added

        # Inventory data
        self.inventory = []  # List of ingredient dicts

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build inventory interface layout."""
        if CTK_AVAILABLE:
            main_frame = ctk.CTkFrame(self.parent, fg_color=COLOR_PRIMARY_BG)
        else:
            main_frame = tk.Frame(self.parent, bg=COLOR_PRIMARY_BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Header with controls
        self._build_header(main_frame)

        # Main inventory table
        self._build_inventory_table(main_frame)

    def _build_header(self, parent):
        """Build header with search and action buttons."""
        if CTK_AVAILABLE:
            header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        else:
            header_frame = tk.Frame(parent, bg=COLOR_PRIMARY_BG)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        if CTK_AVAILABLE:
            title = ctk.CTkLabel(
                header_frame,
                text="Inventory Management",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            title = tk.Label(
                header_frame,
                text="Inventory Management",
                font=("Georgia", 18, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_PRIMARY_BG,
            )
        title.grid(row=0, column=0, sticky="w")

        # Search bar
        if CTK_AVAILABLE:
            search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        else:
            search_frame = tk.Frame(header_frame, bg=COLOR_PRIMARY_BG)
        search_frame.grid(row=0, column=1, sticky="e", padx=(20, 0))

        if CTK_AVAILABLE:
            search_lbl = ctk.CTkLabel(
                search_frame,
                text="Search:",
                font=ctk.CTkFont(size=12),
            )
        else:
            search_lbl = tk.Label(
                search_frame,
                text="Search:",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_PRIMARY_BG,
            )
        search_lbl.pack(side="left", padx=(0, 5))

        if CTK_AVAILABLE:
            self.search_entry = ctk.CTkEntry(
                search_frame,
                placeholder_text="Ingredient name...",
                width=200,
            )
        else:
            self.search_entry = tk.Entry(search_frame, width=25)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_inventory())

        # Action buttons
        if CTK_AVAILABLE:
            btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        else:
            btn_frame = tk.Frame(header_frame, bg=COLOR_PRIMARY_BG)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        if CTK_AVAILABLE:
            add_btn = ctk.CTkButton(
                btn_frame,
                text="Add Ingredient",
                width=150,
                fg_color=COLOR_SUCCESS,
                hover_color="#1f7f1f",
                command=self._show_add_dialog,
            )
        else:
            add_btn = tk.Button(
                btn_frame,
                text="Add Ingredient",
                width=20,
                bg=COLOR_SUCCESS,
                fg="white",
                relief="flat",
                command=self._show_add_dialog,
            )
        add_btn.pack(side="left", padx=5)

        if CTK_AVAILABLE:
            update_btn = ctk.CTkButton(
                btn_frame,
                text="Update Stock",
                width=150,
                fg_color=COLOR_ACCENT,
                command=self._show_update_dialog,
            )
        else:
            update_btn = tk.Button(
                btn_frame,
                text="Update Stock",
                width=20,
                bg=COLOR_ACCENT,
                fg="#1a1a2e",
                relief="flat",
                command=self._show_update_dialog,
            )
        update_btn.pack(side="left", padx=5)

        if CTK_AVAILABLE:
            refresh_btn = ctk.CTkButton(
                btn_frame,
                text="Refresh",
                width=100,
                fg_color="#3a3a4e",
                command=self._refresh_inventory,
            )
        else:
            refresh_btn = tk.Button(
                btn_frame,
                text="Refresh",
                width=15,
                bg="#3a3a4e",
                fg="white",
                relief="flat",
                command=self._refresh_inventory,
            )
        refresh_btn.pack(side="left", padx=5)

    def _build_inventory_table(self, parent):
        """Build inventory Treeview table."""
        if CTK_AVAILABLE:
            table_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color=COLOR_SECONDARY_BG)
        else:
            table_frame = tk.Frame(parent, bg=COLOR_SECONDARY_BG)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.pack_propagate(False)
        table_frame.grid_propagate(False)

        # Title
        if CTK_AVAILABLE:
            table_title = ctk.CTkLabel(
                table_frame,
                text="Ingredient Stock Levels",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            table_title = tk.Label(
                table_frame,
                text="Ingredient Stock Levels",
                font=("Georgia", 14, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
        table_title.pack(padx=10, pady=(10, 5), anchor="w")

        # Treeview
        columns = ("Ingredient", "Unit", "Current Stock", "Reorder Level", "Status", "Actions")
        self.inventory_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20,
        )

        # Column headings
        self.inventory_tree.heading("Ingredient", text="Ingredient")
        self.inventory_tree.heading("Unit", text="Unit")
        self.inventory_tree.heading("Current Stock", text="Current Stock")
        self.inventory_tree.heading("Reorder Level", text="Reorder Level")
        self.inventory_tree.heading("Status", text="Status")
        self.inventory_tree.heading("Actions", text="Actions")

        # Column widths
        self.inventory_tree.column("Ingredient", width=200)
        self.inventory_tree.column("Unit", width=80, anchor="center")
        self.inventory_tree.column("Current Stock", width=120, anchor="center")
        self.inventory_tree.column("Reorder Level", width=120, anchor="center")
        self.inventory_tree.column("Status", width=120, anchor="center")
        self.inventory_tree.column("Actions", width=120, anchor="center")

        self.inventory_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Bind click for actions
        self.inventory_tree.bind("<Button-1>", self._on_tree_click)

    def _on_tree_click(self, event):
        """Handle clicks on tree (for action buttons)."""
        item = self.inventory_tree.selection()
        if not item:
            return

        col = self.inventory_tree.identify("column", event.x, event.y)

        # Check if clicking on Actions column
        if col == "#6":  # Actions column
            index = int(self.inventory_tree.index(item[0]))
            if index < len(self.inventory):
                ingredient = self.inventory[index]
                self._show_ingredient_options(ingredient)

    def _filter_inventory(self):
        """Filter inventory based on search query."""
        search_term = self.search_entry.get().lower()
        self._refresh_inventory_display(filter_term=search_term)

    def _refresh_inventory(self):
        """Refresh inventory display."""
        self._refresh_inventory_display()

    def _refresh_inventory_display(self, filter_term: str = ""):
        """
        Refresh the inventory table display.

        Args:
            filter_term: Optional search term to filter ingredients.
        """
        # Clear tree
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        # Add items
        for ingredient in self.inventory:
            # Apply filter
            if filter_term and filter_term not in ingredient["name"].lower():
                continue

            name = ingredient["name"]
            unit = ingredient["unit"]
            current = ingredient["quantity"]
            reorder = ingredient["reorder_level"]

            # Status indicator
            if current <= reorder:
                status = "LOW STOCK"
                tag = "low_stock"
            elif current < reorder * 1.5:
                status = "WARNING"
                tag = "warning"
            else:
                status = "OK"
                tag = "ok"

            values = (
                name,
                unit,
                f"{current:.2f}",
                f"{reorder:.2f}",
                status,
                "Edit",
            )

            self.inventory_tree.insert("", "end", values=values, tags=(tag,))

        # Configure row colors
        self.inventory_tree.tag_configure("low_stock", foreground=COLOR_ERROR, background="#3a2a2a")
        self.inventory_tree.tag_configure("warning", foreground=COLOR_WARNING, background="#3a3a2a")
        self.inventory_tree.tag_configure("ok", foreground=COLOR_SUCCESS)

    def _show_add_dialog(self):
        """Show dialog to add new ingredient."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Ingredient")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        dialog.grab_set()

        # Form fields
        fields = {}

        if CTK_AVAILABLE:
            form_frame = ctk.CTkFrame(dialog, fg_color=COLOR_PRIMARY_BG)
        else:
            form_frame = tk.Frame(dialog, bg=COLOR_PRIMARY_BG)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        labels = ["Ingredient Name:", "Unit:", "Reorder Level:"]
        for i, label_text in enumerate(labels):
            if CTK_AVAILABLE:
                lbl = ctk.CTkLabel(
                    form_frame,
                    text=label_text,
                    font=ctk.CTkFont(size=12),
                )
            else:
                lbl = tk.Label(
                    form_frame,
                    text=label_text,
                    font=("Sans", 12),
                    fg=COLOR_TEXT_PRIMARY,
                    bg=COLOR_PRIMARY_BG,
                )
            lbl.grid(row=i, column=0, sticky="w", pady=(0, 10))

            if CTK_AVAILABLE:
                entry = ctk.CTkEntry(form_frame, width=250)
            else:
                entry = tk.Entry(form_frame, width=30)
            entry.grid(row=i, column=1, sticky="ew", pady=(0, 10))

            field_key = label_text.split()[0].lower()
            fields[field_key] = entry

        # Save button
        def save_ingredient():
            name = fields["ingredient"].get().strip()
            unit = fields["unit"].get().strip()
            try:
                reorder_level = float(fields["reorder"].get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Reorder level must be a number")
                return

            if not name or not unit:
                messagebox.showwarning("Missing Fields", "Please fill all fields")
                return

            ingredient = {
                "name": name,
                "unit": unit,
                "quantity": 0,
                "reorder_level": reorder_level,
            }

            if self.on_ingredient_added:
                self.on_ingredient_added(ingredient)

            # Add to local list
            self.inventory.append(ingredient)
            self._refresh_inventory_display()

            messagebox.showinfo("Success", f"Ingredient '{name}' added")
            dialog.destroy()

        if CTK_AVAILABLE:
            save_btn = ctk.CTkButton(
                form_frame,
                text="Add Ingredient",
                width=250,
                fg_color=COLOR_SUCCESS,
                command=save_ingredient,
            )
        else:
            save_btn = tk.Button(
                form_frame,
                text="Add Ingredient",
                width=30,
                bg=COLOR_SUCCESS,
                fg="white",
                relief="flat",
                command=save_ingredient,
            )
        save_btn.grid(row=3, column=0, columnspan=2, pady=(20, 0))

    def _show_update_dialog(self):
        """Show dialog to update stock for selected ingredient."""
        selection = self.inventory_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an ingredient to update")
            return

        index = int(self.inventory_tree.index(selection[0]))
        ingredient = self.inventory[index]

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Update Stock - {ingredient['name']}")
        dialog.geometry("350x250")
        dialog.transient(self.parent)
        dialog.grab_set()

        if CTK_AVAILABLE:
            form_frame = ctk.CTkFrame(dialog, fg_color=COLOR_PRIMARY_BG)
        else:
            form_frame = tk.Frame(dialog, bg=COLOR_PRIMARY_BG)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Current stock display
        if CTK_AVAILABLE:
            current_lbl = ctk.CTkLabel(
                form_frame,
                text=f"Current Stock: {ingredient['quantity']:.2f} {ingredient['unit']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            current_lbl = tk.Label(
                form_frame,
                text=f"Current Stock: {ingredient['quantity']:.2f} {ingredient['unit']}",
                font=("Georgia", 12, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_PRIMARY_BG,
            )
        current_lbl.pack(pady=(0, 15))

        # New quantity input
        if CTK_AVAILABLE:
            qty_lbl = ctk.CTkLabel(
                form_frame,
                text="New Quantity:",
                font=ctk.CTkFont(size=12),
            )
        else:
            qty_lbl = tk.Label(
                form_frame,
                text="New Quantity:",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_PRIMARY_BG,
            )
        qty_lbl.pack(pady=(0, 5))

        if CTK_AVAILABLE:
            qty_entry = ctk.CTkEntry(form_frame, width=250)
        else:
            qty_entry = tk.Entry(form_frame, width=30)
        qty_entry.pack(pady=(0, 15))

        # Reorder level input
        if CTK_AVAILABLE:
            reorder_lbl = ctk.CTkLabel(
                form_frame,
                text="Reorder Level:",
                font=ctk.CTkFont(size=12),
            )
        else:
            reorder_lbl = tk.Label(
                form_frame,
                text="Reorder Level:",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_PRIMARY_BG,
            )
        reorder_lbl.pack(pady=(0, 5))

        if CTK_AVAILABLE:
            reorder_entry = ctk.CTkEntry(form_frame, width=250)
            reorder_entry.insert(0, str(ingredient["reorder_level"]))
        else:
            reorder_entry = tk.Entry(form_frame, width=30)
            reorder_entry.insert(0, str(ingredient["reorder_level"]))
        reorder_entry.pack(pady=(0, 15))

        # Update button
        def update_stock():
            try:
                new_qty = float(qty_entry.get())
                new_reorder = float(reorder_entry.get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Quantity and reorder level must be numbers")
                return

            # Update ingredient
            ingredient["quantity"] = new_qty
            ingredient["reorder_level"] = new_reorder

            # Invoke callback
            if self.on_stock_update:
                self.on_stock_update(ingredient)

            self._refresh_inventory_display()
            messagebox.showinfo("Success", f"Stock updated for {ingredient['name']}")
            dialog.destroy()

        if CTK_AVAILABLE:
            update_btn = ctk.CTkButton(
                form_frame,
                text="Update Stock",
                width=250,
                fg_color=COLOR_SUCCESS,
                command=update_stock,
            )
        else:
            update_btn = tk.Button(
                form_frame,
                text="Update Stock",
                width=30,
                bg=COLOR_SUCCESS,
                fg="white",
                relief="flat",
                command=update_stock,
            )
        update_btn.pack()

    def _show_ingredient_options(self, ingredient: Dict):
        """Show options for an ingredient."""
        menu = tk.Menu(self.parent, tearoff=0)
        menu.add_command(
            label="Update Stock",
            command=lambda: self._show_ingredient_update(ingredient),
        )
        menu.add_command(
            label="Set Reorder Level",
            command=lambda: self._show_reorder_dialog(ingredient),
        )
        menu.add_separator()
        menu.add_command(
            label="Remove",
            command=lambda: self._remove_ingredient(ingredient),
        )
        menu.post(self.parent.winfo_pointerx(), self.parent.winfo_pointery())

    def _show_ingredient_update(self, ingredient: Dict):
        """Quick update for ingredient stock."""
        value = tk.simpledialog.askfloat(
            "Update Stock",
            f"New quantity for {ingredient['name']} ({ingredient['unit']}):",
            initialvalue=ingredient["quantity"],
        )

        if value is not None:
            ingredient["quantity"] = value
            if self.on_stock_update:
                self.on_stock_update(ingredient)
            self._refresh_inventory_display()

    def _show_reorder_dialog(self, ingredient: Dict):
        """Show dialog to set reorder level."""
        value = tk.simpledialog.askfloat(
            "Set Reorder Level",
            f"Reorder level for {ingredient['name']}:",
            initialvalue=ingredient["reorder_level"],
        )

        if value is not None:
            ingredient["reorder_level"] = value
            self._refresh_inventory_display()
            messagebox.showinfo("Success", f"Reorder level updated")

    def _remove_ingredient(self, ingredient: Dict):
        """Remove an ingredient from inventory."""
        if messagebox.askyesno("Confirm", f"Remove '{ingredient['name']}'?"):
            self.inventory.remove(ingredient)
            self._refresh_inventory_display()

    def load_inventory(self, inventory_list: List[Dict]):
        """
        Load inventory data from external source.

        Args:
            inventory_list: List of ingredient dicts.
        """
        self.inventory = inventory_list
        self._refresh_inventory_display()

    def get_inventory(self) -> List[Dict]:
        """Get current inventory data."""
        return self.inventory.copy()
