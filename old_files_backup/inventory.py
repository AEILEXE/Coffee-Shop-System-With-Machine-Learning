"""
CAFÉCRAFT INVENTORY MODULE

TASK FOR COPILOT:
Manage ingredient-based inventory.

REQUIREMENTS:
- Manual stock adjustments
- Auto-deduction from POS
- Low-stock alerts
- Reorder threshold
- Inventory usage logging
"""
# TODO: Prevent negative inventory values
# TODO: Highlight low-stock items
# TODO: Generate inventory usage reports

import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection

class InventoryFrame:
    def __init__(self, parent, user):
        self.parent = parent
        self.user = user
        self.setup_ui()
        self.load_inventory()
    
    def setup_ui(self):
        main = tk.Frame(self.parent, bg="#1a1a2e")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="Inventory Management", font=("Georgia", 24, "bold"),
                 fg="white", bg="#1a1a2e").pack(anchor="w")
        
        # Treeview for inventory
        columns = ("ID", "Name", "Category", "Quantity", "Unit", "Cost", "Minimum Stock Level")
        self.tree = ttk.Treeview(main, columns=columns, show="headings", height=15)
        
        # Update header text for clarity and better column sizing
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor='center')

        # Style for readability
        style = ttk.Style()
        style.configure('Treeview', rowheight=24, fieldbackground='#1a1a1a', background='#1a1a1a', foreground='white')
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))
        
        self.tree.pack(fill="both", expand=True, pady=20)
        
        # Action buttons
        btn_frame = tk.Frame(main, bg="#1a1a2e")
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="Add Stock", bg="#28a745", fg="white",
                  command=self.add_stock).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Remove Stock", bg="#dc3545", fg="white",
                  command=self.remove_stock).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Add New Item", bg="#007bff", fg="white",
                  command=self.add_item).pack(side="left", padx=5)
    
    def load_inventory(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory_items ORDER BY name")
        
        for row in cursor.fetchall():
            # row: (id, name, category, quantity, unit, cost_per_unit, reorder_threshold, updated_at)
            reorder = row[6] if len(row) > 6 else 10
            tags = ("low",) if row[3] <= reorder else ()
            values = (row[0], row[1], row[2], row[3], row[4], row[5], reorder)
            self.tree.insert("", tk.END, values=values, tags=tags)
        
        self.tree.tag_configure("low", background="#dc3545")
        # Show low-stock alert if any
        low_items = [self.tree.item(i)['values'][1] for i in self.tree.get_children() if 'low' in self.tree.item(i)['tags']]
        if low_items:
            messagebox.showwarning('Low Stock', 'Low stock for: ' + ', '.join(low_items))
        conn.close()
    
    def add_stock(self):
        self._adjust_stock("add")
    
    def remove_stock(self):
        self._adjust_stock("remove")
    
    def _adjust_stock(self, action):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select Item", "Please select an inventory item")
            return
        
        item_id = self.tree.item(selection[0])["values"][0]
        
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"{'Add' if action == 'add' else 'Remove'} Stock")
        dialog.geometry("300x150")
        
        tk.Label(dialog, text="Quantity:").pack(pady=10)
        qty_entry = tk.Entry(dialog)
        qty_entry.pack()
        
        def confirm():
            try:
                qty = float(qty_entry.get())
                if action == "remove":
                    qty = -qty
                conn = get_connection()
                cursor = conn.cursor()
                # Check current quantity to prevent negatives
                cursor.execute('SELECT quantity FROM inventory_items WHERE id = ?', (item_id,))
                row = cursor.fetchone()
                if row is None:
                    conn.close()
                    messagebox.showerror('Error', 'Inventory item not found')
                    return
                current_qty = row[0]
                new_qty = current_qty + qty
                if new_qty < 0:
                    conn.close()
                    messagebox.showerror('Error', 'Operation would result in negative inventory')
                    return

                cursor.execute(
                    "UPDATE inventory_items SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_qty, item_id)
                )
                cursor.execute('''
                    INSERT INTO inventory_logs (inventory_item_id, user_id, change_amount, change_type)
                    VALUES (?, ?, ?, ?)
                ''', (item_id, self.user['id'], abs(qty), action))
                conn.commit()
                conn.close()

                dialog.destroy()
                self.load_inventory()
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity")
        
        tk.Button(dialog, text="Confirm", command=confirm).pack(pady=20)
    
    def add_item(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add New Item")
        dialog.geometry("350x350")
        
        fields = ["Name", "Category", "Unit", "Quantity", "Cost per Unit", "Price", "Minimum Stock Level"]
        entries = {}
        
        for field in fields:
            tk.Label(dialog, text=f"{field}:").pack()
            if field == "Category":
                entries[field] = ttk.Combobox(dialog, values=["Coffee", "Tea", "Pastry", "Snack", "Other"])
                entries[field].set("Coffee")
            else:
                entries[field] = tk.Entry(dialog)
            entries[field].pack()
        
        def confirm():
            name = entries["Name"].get().strip()
            category = entries["Category"].get().strip()
            if not name or not category:
                messagebox.showerror("Error", "Name and Category are required")
                return
            
            # Check duplicate
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM inventory_items WHERE name = ? AND category = ?", (name, category))
            if cursor.fetchone():
                conn.close()
                messagebox.showerror("Duplicate", "Item with this name and category already exists")
                return
            
            try:
                qty = float(entries["Quantity"].get() or 0)
                cost = float(entries["Cost per Unit"].get() or 0)
                price = float(entries["Price"].get() or 0)
                min_stock = float(entries["Minimum Stock Level"].get() or 10)
                unit = entries["Unit"].get().strip()
                
                # Insert inventory
                cursor.execute('''
                    INSERT INTO inventory_items (name, category, unit, quantity, cost_per_unit, reorder_threshold)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, category, unit, qty, cost, min_stock))
                inv_id = cursor.lastrowid
                
                # Insert menu if not exists
                cursor.execute("SELECT id FROM menu_items WHERE name = ? AND category = ?", (name, category))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO menu_items (name, category, price, is_available)
                        VALUES (?, ?, ?, 1)
                    ''', (name, category, price))
                
                conn.commit()
                conn.close()
                dialog.destroy()
                self.load_inventory()
                # Refresh POS menu if possible, but since separate, perhaps reload pos
                messagebox.showinfo("Success", "Item added and synced to POS menu")
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric values")
        
        tk.Button(dialog, text="Add Item", command=confirm).pack(pady=20)
