"""
CAFÉCRAFT POS MODULE

TASK FOR COPILOT:
Complete the point-of-sale system.

REQUIREMENTS:
- Menu item selection
- Quantity & price calculation
- Discounts
- Transaction logging to SQLite
- Automatic receipt generation
- Automatic inventory deduction per sale

DATABASE:
- menu_items
- transactions
- transaction_items
- inventory_items
- menu_recipes (menu_item_id, inventory_item_id, quantity_required)
"""
# TODO: Create menu_recipes table
# TODO: Validate inventory before sale
# TODO: Deduct ingredients automatically after payment
# TODO: Generate receipt popup
# TODO: Save receipt as .txt file


import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import get_connection
from tkinter import filedialog
try:
    # Optional PDF export
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

class POSFrame:
    def __init__(self, parent, user):
        self.parent = parent
        self.user = user
        self.cart = []  # List of {"item": row, "quantity": int}
        self.discount = 0
        
        self.setup_ui()
        self.load_menu_items()
    
    def setup_ui(self):
        # Main container
        main = tk.Frame(self.parent, bg="#1a1a2e")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main, text="Point of Sale", font=("Georgia", 24, "bold"),
                 fg="white", bg="#1a1a2e").pack(anchor="w")
        
        # Content area
        content = tk.Frame(main, bg="#1a1a2e")
        content.pack(fill="both", expand=True, pady=20)
        
        # Left: Menu items
        left = tk.Frame(content, bg="#1a1a2e")
        left.pack(side="left", fill="both", expand=True)
        
        # Category filter
        cat_frame = tk.Frame(left, bg="#1a1a2e")
        cat_frame.pack(fill="x", pady=10)
        
        self.category_var = tk.StringVar(value="All")
        for cat in ["All", "Coffee", "Tea", "Pastry", "Snack"]:
            tk.Radiobutton(cat_frame, text=cat, variable=self.category_var,
                          value=cat, bg="#1a1a2e", fg="white", selectcolor="#16213e",
                          command=self.filter_items).pack(side="left", padx=5)
        
        # Menu items grid
        self.menu_frame = tk.Frame(left, bg="#1a1a2e")
        self.menu_frame.pack(fill="both", expand=True)
        
        # Right: Cart
        right = tk.Frame(content, bg="#16213e", width=350)
        right.pack(side="right", fill="y", padx=(20, 0))
        right.pack_propagate(False)
        
        tk.Label(right, text="Current Order", font=("Georgia", 16, "bold"),
                 fg="white", bg="#16213e").pack(pady=15)
        
        # Cart items list
        self.cart_listbox = tk.Listbox(right, font=("Arial", 11), height=15,
                                        bg="#1a1a2e", fg="white", selectbackground="#d4a574")
        self.cart_listbox.pack(fill="x", padx=10, pady=5)
        
        # Remove button
        tk.Button(right, text="Remove Item", bg="#dc3545", fg="white",
                  command=self.remove_from_cart).pack(pady=5)
        
        # Void Order button
        tk.Button(right, text="Void Order", bg="#8B4513", fg="white",
                  command=self.void_order).pack(pady=5)
        
        # Discount
        disc_frame = tk.Frame(right, bg="#16213e")
        disc_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(disc_frame, text="Discount %:", fg="white", bg="#16213e").pack(side="left")
        self.discount_entry = tk.Entry(disc_frame, width=5)
        self.discount_entry.insert(0, "0")
        self.discount_entry.pack(side="left", padx=5)
        
        # Totals
        self.totals_label = tk.Label(right, text="Total: $0.00", 
                                      font=("Arial", 18, "bold"),
                                      fg="#d4a574", bg="#16213e")
        self.totals_label.pack(pady=15)
        
        # Customer money and change
        money_frame = tk.Frame(right, bg="#16213e")
        money_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(money_frame, text="Customer Money:", fg="white", bg="#16213e").pack(side="left")
        self.customer_money_entry = tk.Entry(money_frame, width=10)
        self.customer_money_entry.pack(side="left", padx=5)
        self.change_label = tk.Label(money_frame, text="Change: $0.00", fg="white", bg="#16213e")
        self.change_label.pack(side="left", padx=10)
        
        # Update change when customer money changes
        self.customer_money_entry.bind('<KeyRelease>', self.update_change)
        
        # Payment buttons
        btn_frame = tk.Frame(right, bg="#16213e")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="Cash", font=("Arial", 12),
                  bg="#28a745", fg="white", width=12,
                  command=lambda: self.process_payment("cash")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Online Payment", font=("Arial", 12),
                  bg="#007bff", fg="white", width=15,
                  command=lambda: self.process_payment("online")).pack(side="left", padx=5)
    
    def load_menu_items(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        category = self.category_var.get()
        if category == "All":
            cursor.execute("SELECT * FROM menu_items WHERE is_available = 1")
        else:
            cursor.execute("SELECT * FROM menu_items WHERE is_available = 1 AND category = ?", 
                          (category,))
        
        items = cursor.fetchall()
        
        # Get stock for each item
        stock_dict = {}
        for item in items:
            cursor2 = conn.cursor()
            cursor2.execute("SELECT quantity FROM inventory_items WHERE name = ? AND category = ?", (item[1], item[2]))
            stock_row = cursor2.fetchone()
            stock_dict[item[0]] = stock_row[0] if stock_row else 0
        
        conn.close()
        
        for i, item in enumerate(items):
            row, col = divmod(i, 4)
            stock = stock_dict.get(item[0], 0)
            stock_color = "red" if stock < 10 else "green"
            btn_text = f"{item[1]}\n${item[3]:.2f}\nStock: {stock}"
            btn = tk.Button(self.menu_frame, text=btn_text,
                           font=("Arial", 10), bg="#2d3748", fg=stock_color,
                           width=15, height=4,
                           command=lambda it=item: self.add_to_cart(it))
            btn.grid(row=row, column=col, padx=5, pady=5)
    
    def filter_items(self):
        self.load_menu_items()
    
    def add_to_cart(self, item):
        # Check if already in cart
        for cart_item in self.cart:
            if cart_item["item"][0] == item[0]:
                cart_item["quantity"] += 1
                self.update_cart_display()
                return
        
        self.cart.append({"item": item, "quantity": 1})
        self.update_cart_display()
    
    def remove_from_cart(self):
        selection = self.cart_listbox.curselection()
        if selection:
            del self.cart[selection[0]]
            self.update_cart_display()
    
    def update_cart_display(self):
        self.cart_listbox.delete(0, tk.END)
        subtotal = 0
        
        for cart_item in self.cart:
            item = cart_item["item"]
            qty = cart_item["quantity"]
            line_total = item[3] * qty
            subtotal += line_total
            self.cart_listbox.insert(tk.END, f"{item[1]} x{qty} - ${line_total:.2f}")
        
        try:
            discount_pct = float(self.discount_entry.get())
        except:
            discount_pct = 0
        
        discount_amt = subtotal * (discount_pct / 100)
        total = subtotal - discount_amt
        
        self.totals_label.config(text=f"Total: ${total:.2f}")
        self.update_change()
    
    def update_change(self, event=None):
        try:
            total_text = self.totals_label.cget("text")
            total = float(total_text.split("$")[1])
            customer_money = float(self.customer_money_entry.get() or 0)
            change = customer_money - total
            self.change_label.config(text=f"Change: ${change:.2f}" if change >= 0 else "Change: Insufficient")
        except:
            self.change_label.config(text="Change: $0.00")
    
    def void_order(self):
        self.cart = []
        self.discount = 0
        self.customer_money_entry.delete(0, tk.END)
        self.discount_entry.delete(0, tk.END)
        self.update_cart_display()
        messagebox.showinfo("Order Voided", "Current order has been cleared.")
    
    def process_payment(self, method):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add items to cart first")
            return
        
        try:
            discount_pct = float(self.discount_entry.get())
        except:
            discount_pct = 0
        
        subtotal = sum(c["item"][3] * c["quantity"] for c in self.cart)
        discount_amt = subtotal * (discount_pct / 100)
        total = subtotal - discount_amt
        
        if method == "online":
            # Choose type
            type_window = tk.Toplevel(self.parent)
            type_window.title("Select Payment Type")
            type_window.geometry("200x100")
            tk.Label(type_window, text="Choose payment type:").pack(pady=5)
            type_var = tk.StringVar(value="gcash")
            tk.Radiobutton(type_window, text="GCash", variable=type_var, value="gcash").pack()
            tk.Radiobutton(type_window, text="Bank Transfer", variable=type_var, value="bank_transfer").pack()
            def select_type():
                nonlocal method
                method = type_var.get()
                type_window.destroy()
            tk.Button(type_window, text="OK", command=select_type).pack(pady=5)
            type_window.wait_window()
        
        # For cash, check customer money
        if method == "cash":
            try:
                customer_money = float(self.customer_money_entry.get())
                if customer_money < total:
                    messagebox.showerror("Insufficient Funds", "Customer money is less than total")
                    return
            except:
                messagebox.showerror("Invalid Amount", "Enter valid customer money")
                return
        
        payment_details = None
        status = 'completed'
        
        if method == "gcash":
            # Create a simple dialog for GCash payment
            gcash_window = tk.Toplevel(self.parent)
            gcash_window.title("GCash Payment")
            gcash_window.geometry("300x200")
            
            tk.Label(gcash_window, text="Amount Received:").pack(pady=5)
            amount_entry = tk.Entry(gcash_window)
            amount_entry.pack(pady=5)
            amount_entry.insert(0, str(total))
            
            tk.Label(gcash_window, text="GCash Number:").pack(pady=5)
            ref_entry = tk.Entry(gcash_window)
            ref_entry.pack(pady=5)
            
            status_var = tk.StringVar(value="pending")
            tk.Radiobutton(gcash_window, text="Pending", variable=status_var, value="pending").pack()
            tk.Radiobutton(gcash_window, text="Completed", variable=status_var, value="completed").pack()
            
            def confirm_gcash():
                nonlocal payment_details, status
                amt = amount_entry.get()
                ref = ref_entry.get()
                if not amt or not ref:
                    messagebox.showerror("Error", "Enter amount and number")
                    return
                payment_details = f"Amount: {amt}, GCash: {ref}"
                status = status_var.get()
                gcash_window.destroy()
            
            tk.Button(gcash_window, text="Confirm", command=confirm_gcash).pack(pady=10)
            gcash_window.wait_window()
        elif method == "bank_transfer":
            # Create a simple dialog for bank payment
            bank_window = tk.Toplevel(self.parent)
            bank_window.title("Bank Payment")
            bank_window.geometry("300x200")
            
            tk.Label(bank_window, text="Amount Received:").pack(pady=5)
            amount_entry = tk.Entry(bank_window)
            amount_entry.pack(pady=5)
            amount_entry.insert(0, str(total))
            
            tk.Label(bank_window, text="Reference Number:").pack(pady=5)
            ref_entry = tk.Entry(bank_window)
            ref_entry.pack(pady=5)
            
            status_var = tk.StringVar(value="pending")
            tk.Radiobutton(bank_window, text="Pending", variable=status_var, value="pending").pack()
            tk.Radiobutton(bank_window, text="Completed", variable=status_var, value="completed").pack()
            
            def confirm_bank():
                nonlocal payment_details, status
                amt = amount_entry.get()
                ref = ref_entry.get()
                if not amt or not ref:
                    messagebox.showerror("Error", "Enter amount and reference")
                    return
                payment_details = f"Amount: {amt}, Ref: {ref}"
                status = status_var.get()
                bank_window.destroy()
            
            tk.Button(bank_window, text="Confirm", command=confirm_bank).pack(pady=10)
            bank_window.wait_window()
        
        conn = get_connection()
        cursor = conn.cursor()

        # Validate inventory for each menu item using recipes
        for cart_item in self.cart:
            item = cart_item['item']
            qty = cart_item['quantity']
            # Get recipe ingredients
            cursor.execute('''
                SELECT inventory_item_id, quantity_required FROM menu_recipes WHERE menu_item_id = ?
            ''', (item[0],))
            recipe = cursor.fetchall()
            for ing in recipe:
                inv_id, per_unit_required = ing
                required_total = per_unit_required * qty
                cursor.execute('SELECT quantity, name FROM inventory_items WHERE id = ?', (inv_id,))
                row = cursor.fetchone()
                if row is None:
                    conn.close()
                    messagebox.showerror('Inventory Error', f'Inventory item {inv_id} not found for recipe')
                    return
                available = row[0]
                if available < required_total:
                    conn.close()
                    messagebox.showerror('Out of Stock', f"Not enough '{row[1]}' for {item[1]} (need {required_total}, have {available})")
                    return

        # Insert transaction
        cursor.execute(
            '''
            INSERT INTO transactions (cashier_id, total_amount, discount_amount, payment_method, status, payment_details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.user['id'], total, discount_amt, method, status, payment_details))

        transaction_id = cursor.lastrowid

        # Insert transaction items and deduct inventory only for completed payments
        if status == 'completed':
            for cart_item in self.cart:
                item = cart_item['item']
                qty = cart_item['quantity']
                cursor.execute('''
                    INSERT INTO transaction_items 
                    (transaction_id, menu_item_id, quantity, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (transaction_id, item[0], qty, item[3], item[3] * qty))

                # Deduct ingredients
                cursor.execute('''
                    SELECT inventory_item_id, quantity_required FROM menu_recipes WHERE menu_item_id = ?
                ''', (item[0],))
                recipe = cursor.fetchall()
                for ing in recipe:
                    inv_id, per_unit_required = ing
                    required_total = per_unit_required * qty
                    # Ensure we don't go negative; double-check
                    cursor.execute('SELECT quantity FROM inventory_items WHERE id = ?', (inv_id,))
                    cur_qty = cursor.fetchone()[0]
                    new_qty = cur_qty - required_total
                    if new_qty < 0:
                        conn.rollback()
                        conn.close()
                        messagebox.showerror('Inventory Error', 'Insufficient inventory during deduction')
                        return
                    cursor.execute('UPDATE inventory_items SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_qty, inv_id))
                    cursor.execute('''
                        INSERT INTO inventory_logs (inventory_item_id, user_id, change_amount, change_type, notes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (inv_id, self.user['id'], abs(required_total), 'remove', f'Removed for transaction {transaction_id}'))

        conn.commit()
        conn.close()

        # Ask for optional customer name
        cust_name = None
        try:
            cust_name = tk.simpledialog.askstring('Customer', 'Enter customer name (optional):')
        except Exception:
            # simpledialog might not be available/imported depending on environment
            cust_name = None

        # Generate receipt text and popup
        receipt_lines = []
        receipt_lines.append('CaféCraft Receipt')
        receipt_lines.append(f'Transaction ID: {transaction_id}')
        if cust_name:
            receipt_lines.append(f'Customer: {cust_name}')
        receipt_lines.append(f'Cashier: {self.user.get("name")}')
        receipt_lines.append(f'Date: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        receipt_lines.append('-' * 30)
        for cart_item in self.cart:
            it = cart_item['item']
            q = cart_item['quantity']
            line = f"{it[1]} x{q} @ ${it[3]:.2f} = ${it[3]*q:.2f}"
            receipt_lines.append(line)
        receipt_lines.append('-' * 30)
        receipt_lines.append(f'Subtotal: ${subtotal:.2f}')
        receipt_lines.append(f'Discount: ${discount_amt:.2f}')
        receipt_lines.append(f'Total: ${total:.2f}')
        receipt_lines.append(f'Payment Method: {method}')
        if payment_details:
            receipt_lines.append(f'Payment Details: {payment_details}')
        receipt_lines.append(f'Status: {status}')

        # Show receipt popup with option to save (text or PDF)
        receipt_text = '\n'.join(receipt_lines)
        self._show_receipt_popup(receipt_text, allow_pdf=REPORTLAB_AVAILABLE)

        if status == 'completed':
            messagebox.showinfo("Success", f"Payment processed!\nTotal: ${total:.2f}\nMethod: {method}")
        else:
            messagebox.showinfo("Pending Payment", f"Transaction recorded as pending.\nTotal: ${total:.2f}\nMethod: {method}\nAwaiting verification.")

        # Clear cart
        self.cart = []
        self.discount_entry.delete(0, tk.END)
        self.discount_entry.insert(0, "0")
        self.customer_money_entry.delete(0, tk.END)
        self.update_cart_display()

    def _show_receipt_popup(self, text, allow_pdf=False):
        win = tk.Toplevel(self.parent)
        win.title('Receipt')
        win.geometry('400x500')
        txt = tk.Text(win, wrap='none')
        txt.insert('1.0', text)
        txt.config(state='disabled')
        txt.pack(fill='both', expand=True)

        def save():
            path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text files','*.txt'), ('PDF files','*.pdf')])
            if path:
                if path.lower().endswith('.pdf') and allow_pdf:
                    try:
                        c = canvas.Canvas(path, pagesize=letter)
                        y = 750
                        for line in text.split('\n'):
                            c.drawString(40, y, line)
                            y -= 14
                            if y < 40:
                                c.showPage()
                                y = 750
                        c.save()
                        messagebox.showinfo('Saved', f'Receipt saved to {path}')
                    except Exception as e:
                        messagebox.showerror('Error', f'Failed to save PDF: {e}')
                else:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    messagebox.showinfo('Saved', f'Receipt saved to {path}')

        tk.Button(win, text='Save Receipt', command=save).pack(pady=10)
