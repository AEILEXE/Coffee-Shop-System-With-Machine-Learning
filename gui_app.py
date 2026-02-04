"""
CaféCraft Modern GUI

A modern, modular Tkinter GUI for the CaféCraft application.

Features included in this file:
- Modern-styled UI using `customtkinter` when available (falls back to `tkinter` + `ttk`).
- Separate page classes: DashboardPage, MenuPage, OrdersPage, CustomersPage, AdminPage.
- Sidebar navigation with role-aware placeholders.
- Cart, order management, and checkout with receipt save.
- Comments and clear class-based structure for extensibility.

Usage:
    python gui_app.py

Note: This GUI connects to the existing SQLite database via `database.get_connection()`.
If `customtkinter` is not installed the UI will use standard ttk widgets with a simpler style.
"""

import os
import sqlite3
from datetime import datetime
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except Exception:
    import tkinter as tk
    from tkinter import ttk
    CTK_AVAILABLE = False

from tkinter import messagebox, filedialog
from database import init_database, get_connection, hash_password


# ---------------------------
# Utility helpers
# ---------------------------
def resource_path(name):
    """Return path to resource if exists, else None."""
    base = os.path.dirname(__file__)
    path = os.path.join(base, 'assets', name)
    return path if os.path.exists(path) else None


# ---------------------------
# Base App
# ---------------------------
class CafeCraftGUI:
    """Main application class. Creates window, sidebar, and page container."""

    def __init__(self):
        init_database()
        if CTK_AVAILABLE:
            ctk.set_appearance_mode('Dark')
            ctk.set_default_color_theme('dark-blue')
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()

        self.root.title('CaféCraft — Modern POS')
        self.root.geometry('1200x800')

        # Simple state
        self.current_user = {'id': 1, 'name': 'Administrator', 'role': 'admin'}
        self.cart = []  # list of {'id', 'name', 'price', 'qty'}

        # Layout: sidebar + content
        self._build_ui()

    def _build_ui(self):
        if CTK_AVAILABLE:
            self.sidebar = ctk.CTkFrame(self.root, width=220, corner_radius=10)
            self.sidebar.pack(side='left', fill='y', padx=12, pady=12)
            self.content = ctk.CTkFrame(self.root, corner_radius=10)
            self.content.pack(side='right', fill='both', expand=True, padx=12, pady=12)
        else:
            self.sidebar = tk.Frame(self.root, width=220, bg='#2f2f2f')
            self.sidebar.pack(side='left', fill='y')
            self.content = tk.Frame(self.root, bg='#1a1a1a')
            self.content.pack(side='right', fill='both', expand=True)

        self.pages = {}
        self._build_sidebar()
        self.show_page('dashboard')

    def _build_sidebar(self):
        # Header
        if CTK_AVAILABLE:
            lbl = ctk.CTkLabel(self.sidebar, text='CaféCraft', font=ctk.CTkFont(size=20, weight='bold'))
            lbl.pack(pady=(12, 8))
            user_lbl = ctk.CTkLabel(self.sidebar, text=f"{self.current_user['name']}", fg_color=None)
            user_lbl.pack(pady=(0, 16))
        else:
            lbl = tk.Label(self.sidebar, text='CaféCraft', fg='white', bg='#2f2f2f', font=('Sans', 16, 'bold'))
            lbl.pack(pady=(12, 8))
            user_lbl = tk.Label(self.sidebar, text=f"{self.current_user['name']}", fg='white', bg='#2f2f2f')
            user_lbl.pack(pady=(0, 16))

        # Nav buttons
        nav = [
            ('dashboard', 'Dashboard', self.show_page),
            ('menu', 'Menu', self.show_page),
            ('orders', 'Orders', self.show_page),
            ('customers', 'Customers', self.show_page),
            ('admin', 'Admin', self.show_page),
        ]

        for key, text, cmd in nav:
            if CTK_AVAILABLE:
                btn = ctk.CTkButton(self.sidebar, text=text, corner_radius=8, command=lambda k=key: cmd(k))
                btn.pack(fill='x', padx=12, pady=6)
            else:
                btn = tk.Button(self.sidebar, text=text, relief='flat', bg='#3a3a3a', fg='white',
                                activebackground='#555', command=lambda k=key: cmd(k))
                btn.pack(fill='x', padx=12, pady=6)

        # Spacer and logout
        if CTK_AVAILABLE:
            spacer = ctk.CTkLabel(self.sidebar, text='')
            spacer.pack(expand=True)
            ctk.CTkButton(self.sidebar, text='Logout', fg_color='#d9534f', command=self._logout).pack(fill='x', padx=12, pady=8)
        else:
            tk.Label(self.sidebar, text='', bg='#2f2f2f').pack(expand=True)
            tk.Button(self.sidebar, text='Logout', bg='#b22222', fg='white', command=self._logout).pack(fill='x', padx=12, pady=8)

    def _logout(self):
        messagebox.showinfo('Logout', 'Logged out (demo): returning to Dashboard')
        self.show_page('dashboard')

    def show_page(self, name):
        # Destroy current content and load requested page
        for w in self.content.winfo_children():
            w.destroy()

        page = None
        if name == 'dashboard':
            page = DashboardPage(self.content, self)
        elif name == 'menu':
            page = MenuPage(self.content, self)
        elif name == 'orders':
            page = OrdersPage(self.content, self)
        elif name == 'customers':
            page = CustomersPage(self.content, self)
        elif name == 'admin':
            page = AdminPage(self.content, self)
        else:
            page = DashboardPage(self.content, self)

        page.pack(fill='both', expand=True)
        self.pages[name] = page

    def run(self):
        self.root.mainloop()


# ---------------------------
# Pages
# ---------------------------
class DashboardPage((ctk.CTkFrame if CTK_AVAILABLE else tk.Frame)):
    """Home / Dashboard with quick stats and shortcuts."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        header = self._make_header('Dashboard')
        header.pack(fill='x', padx=20, pady=10)

        stats_frame = (ctk.CTkFrame(self) if CTK_AVAILABLE else tk.Frame(self, bg='#222'))
        stats_frame.pack(fill='x', padx=20, pady=10)

        # Simple stats: total sales today, transactions, active items
        conn = get_connection()
        cur = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cur.execute("SELECT COALESCE(SUM(total_amount),0) FROM transactions WHERE DATE(created_at)=?", (today,))
        sales_today = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM transactions")
        total_trans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM menu_items WHERE is_available=1")
        active_items = cur.fetchone()[0]
        conn.close()

        self._stat_card(stats_frame, 'Today Sales', f'${sales_today:.2f}').pack(side='left', padx=12, pady=12, expand=True)
        self._stat_card(stats_frame, 'Transactions', str(total_trans)).pack(side='left', padx=12, pady=12, expand=True)
        self._stat_card(stats_frame, 'Items Available', str(active_items)).pack(side='left', padx=12, pady=12, expand=True)

    def _make_header(self, title):
        if CTK_AVAILABLE:
            return ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=24, weight='bold'))
        else:
            return tk.Label(self, text=title, fg='white', bg='#1a1a1a', font=('Sans', 20, 'bold'))

    def _stat_card(self, parent, title, value):
        if CTK_AVAILABLE:
            frame = ctk.CTkFrame(parent, corner_radius=8, height=100)
            lbl_t = ctk.CTkLabel(frame, text=title, fg_color=None)
            lbl_v = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=18, weight='bold'))
            lbl_t.pack(pady=(12, 0))
            lbl_v.pack(pady=(6, 12))
            return frame
        else:
            frame = tk.Frame(parent, bg='#2b2b2b', height=100)
            tk.Label(frame, text=title, bg='#2b2b2b', fg='#ccc').pack(pady=(12, 0))
            tk.Label(frame, text=value, bg='#2b2b2b', fg='#ffd28a', font=('Sans', 14, 'bold')).pack(pady=(6, 12))
            return frame


class MenuPage((ctk.CTkFrame if CTK_AVAILABLE else tk.Frame)):
    """Menu display with categories and add-to-cart actions."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.category = 'All'
        self._build()

    def _build(self):
        header = self._make_header('Menu')
        header.pack(fill='x', padx=20, pady=10)

        controls = (ctk.CTkFrame(self) if CTK_AVAILABLE else tk.Frame(self, bg='#111'))
        controls.pack(fill='x', padx=20, pady=6)

        # Category dropdown
        cats = ['All', 'Coffee', 'Tea', 'Pastry', 'Snack']
        if CTK_AVAILABLE:
            self.cat_combo = ctk.CTkComboBox(controls, values=cats, command=self._on_cat)
            self.cat_combo.set('All')
            self.cat_combo.pack(side='left', padx=6)
        else:
            self.cat_var = tk.StringVar(value='All')
            ttk.Combobox(controls, textvariable=self.cat_var, values=cats).pack(side='left', padx=6)

        # Menu grid
        self.grid_frame = (ctk.CTkFrame(self) if CTK_AVAILABLE else tk.Frame(self, bg='#1a1a1a'))
        self.grid_frame.pack(fill='both', expand=True, padx=20, pady=10)
        self._load_menu()

    def _make_header(self, title):
        if CTK_AVAILABLE:
            return ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=20, weight='bold'))
        else:
            return tk.Label(self, text=title, fg='white', bg='#1a1a1a', font=('Sans', 16, 'bold'))

    def _on_cat(self, val):
        self.category = val
        self._load_menu()

    def _load_menu(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        conn = get_connection()
        cur = conn.cursor()
        if self.category == 'All':
            cur.execute('SELECT id, name, category, price, is_available FROM menu_items WHERE is_available=1')
        else:
            cur.execute('SELECT id, name, category, price, is_available FROM menu_items WHERE is_available=1 AND category=?', (self.category,))
        rows = cur.fetchall()
        conn.close()

        # Simple card grid
        for i, r in enumerate(rows):
            frame = (ctk.CTkFrame(self.grid_frame, corner_radius=8) if CTK_AVAILABLE else tk.Frame(self.grid_frame, bg='#222'))
            frame.grid(row=i//3, column=i%3, padx=8, pady=8, sticky='nsew')
            title = r[1]
            price = r[3]
            if CTK_AVAILABLE:
                ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=14, weight='bold')).pack(padx=8, pady=6)
                ctk.CTkLabel(frame, text=f'${price:.2f}').pack(padx=8)
                ctk.CTkButton(frame, text='Add', command=lambda row=r: self._add_to_cart(row)).pack(pady=8)
            else:
                tk.Label(frame, text=title, bg='#222', fg='white').pack(padx=8, pady=6)
                tk.Label(frame, text=f'${price:.2f}', bg='#222', fg='#ffd28a').pack(padx=8)
                tk.Button(frame, text='Add', command=lambda row=r: self._add_to_cart(row)).pack(pady=8)

    def _add_to_cart(self, row):
        # row: (id, name, category, price, is_available)
        for it in self.app.cart:
            if it['id'] == row[0]:
                it['qty'] += 1
                messagebox.showinfo('Cart', f"Added another {row[1]}")
                return
        self.app.cart.append({'id': row[0], 'name': row[1], 'price': row[3], 'qty': 1})
        messagebox.showinfo('Cart', f"Added {row[1]} to cart")


class OrdersPage((ctk.CTkFrame if CTK_AVAILABLE else tk.Frame)):
    """Order management: view cart, edit quantities, checkout."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        header = self._make_header('Orders')
        header.pack(fill='x', padx=20, pady=10)

        body = (ctk.CTkFrame(self) if CTK_AVAILABLE else tk.Frame(self, bg='#111'))
        body.pack(fill='both', expand=True, padx=20, pady=10)

        # Cart list
        if CTK_AVAILABLE:
            self.listbox = ctk.CTkTextbox(body, width=600, height=300)
            self.listbox.pack(side='left', padx=12, pady=6)
        else:
            self.listbox = tk.Text(body, width=60, height=20)
            self.listbox.pack(side='left', padx=12, pady=6)

        controls = (ctk.CTkFrame(body) if CTK_AVAILABLE else tk.Frame(body, bg='#111'))
        controls.pack(side='right', fill='y', padx=12)

        if CTK_AVAILABLE:
            ctk.CTkButton(controls, text='Refresh', command=self.render_cart).pack(pady=6)
            ctk.CTkButton(controls, text='Checkout', fg_color='#28a745', command=self.checkout).pack(pady=6)
        else:
            tk.Button(controls, text='Refresh', command=self.render_cart).pack(pady=6)
            tk.Button(controls, text='Checkout', bg='#28a745', fg='white', command=self.checkout).pack(pady=6)

        self.render_cart()

    def _make_header(self, title):
        if CTK_AVAILABLE:
            return ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=20, weight='bold'))
        else:
            return tk.Label(self, text=title, fg='white', bg='#1a1a1a', font=('Sans', 16, 'bold'))

    def render_cart(self):
        self.listbox.config(state='normal')
        self.listbox.delete('1.0', 'end')
        total = 0
        for it in self.app.cart:
            line = f"{it['name']} x{it['qty']} @ ${it['price']:.2f} = ${it['qty']*it['price']:.2f}\n"
            self.listbox.insert('end', line)
            total += it['qty']*it['price']
        self.listbox.insert('end', '\n')
        self.listbox.insert('end', f'Total: ${total:.2f}')
        self.listbox.config(state='disabled')

    def checkout(self):
        if not self.app.cart:
            messagebox.showwarning('Empty', 'Cart is empty')
            return

        total = sum(it['qty']*it['price'] for it in self.app.cart)
        if not messagebox.askyesno('Confirm', f'Proceed to payment for ${total:.2f}?'):
            return

        # Write transaction to DB (simple)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO transactions (cashier_id, total_amount, discount_amount, payment_method) VALUES (?, ?, ?, ?)', (self.app.current_user['id'], total, 0, 'cash'))
        txid = cur.lastrowid
        for it in self.app.cart:
            cur.execute('INSERT INTO transaction_items (transaction_id, menu_item_id, quantity, unit_price, subtotal) VALUES (?, ?, ?, ?, ?)', (txid, it['id'], it['qty'], it['price'], it['qty']*it['price']))
        conn.commit()
        conn.close()

        # Save a receipt file
        receipt = self._build_receipt(txid, total)
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text files','*.txt')])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(receipt)

        messagebox.showinfo('Done', f'Checkout complete (Transaction {txid})')
        self.app.cart = []
        self.render_cart()

    def _build_receipt(self, txid, total):
        lines = ["CaféCraft Receipt", f'Transaction: {txid}', f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', '-'*30]
        for it in self.app.cart:
            lines.append(f"{it['name']} x{it['qty']} = ${it['qty']*it['price']:.2f}")
        lines.append('-'*30)
        lines.append(f'Total: ${total:.2f}')
        return '\n'.join(lines)


class CustomersPage((ctk.CTkFrame if CTK_AVAILABLE else tk.Frame)):
    """Customer details and simple order history lookup."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        header = self._make_header('Customers')
        header.pack(fill='x', padx=20, pady=10)

        # For demo: show recent transactions
        frame = (ctk.CTkFrame(self) if CTK_AVAILABLE else tk.Frame(self))
        frame.pack(fill='both', expand=True, padx=20, pady=10)

        cols = ('ID', 'Date', 'Amount', 'Payment')
        if CTK_AVAILABLE:
            txt = ctk.CTkTextbox(frame)
            txt.pack(fill='both', expand=True)
        else:
            txt = tk.Text(frame)
            txt.pack(fill='both', expand=True)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, created_at, total_amount, payment_method FROM transactions ORDER BY created_at DESC LIMIT 20')
        for r in cur.fetchall():
            txt.insert('end', f'{r[0]} | {r[1][:16]} | ${r[2]:.2f} | {r[3]}\n')
        conn.close()

    def _make_header(self, title):
        if CTK_AVAILABLE:
            return ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=20, weight='bold'))
        else:
            return tk.Label(self, text=title, fg='white', bg='#1a1a1a', font=('Sans', 16, 'bold'))


class AdminPage((ctk.CTkFrame if CTK_AVAILABLE else tk.Frame)):
    """Admin panel for adding/removing menu items and viewing sales summary."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        header = self._make_header('Admin')
        header.pack(fill='x', padx=20, pady=10)

        self.form = (ctk.CTkFrame(self) if CTK_AVAILABLE else tk.Frame(self))
        self.form.pack(fill='x', padx=20, pady=6)

        # Simple form to add menu items
        if CTK_AVAILABLE:
            self.name_entry = ctk.CTkEntry(self.form, placeholder_text='Name')
            self.cat_entry = ctk.CTkEntry(self.form, placeholder_text='Category')
            self.price_entry = ctk.CTkEntry(self.form, placeholder_text='Price')
            self.name_entry.pack(side='left', padx=6)
            self.cat_entry.pack(side='left', padx=6)
            self.price_entry.pack(side='left', padx=6)
            ctk.CTkButton(self.form, text='Add Item', command=self.add_item).pack(side='left', padx=6)
        else:
            self.name_entry = tk.Entry(self.form)
            self.cat_entry = tk.Entry(self.form)
            self.price_entry = tk.Entry(self.form)
            self.name_entry.pack(side='left', padx=6)
            self.cat_entry.pack(side='left', padx=6)
            self.price_entry.pack(side='left', padx=6)
            tk.Button(self.form, text='Add Item', command=self.add_item).pack(side='left', padx=6)

        # Sales summary area
        self.summary = (ctk.CTkTextbox(self) if CTK_AVAILABLE else tk.Text(self))
        self.summary.pack(fill='both', expand=True, padx=20, pady=10)
        self.load_summary()

        # User management area (employees/admins)
        um_frame = (ctk.CTkFrame(self) if CTK_AVAILABLE else tk.Frame(self))
        um_frame.pack(fill='x', padx=20, pady=6)

        if CTK_AVAILABLE:
            ctk.CTkLabel(um_frame, text='User Management', font=ctk.CTkFont(size=14, weight='bold')).pack(anchor='w')
            row = ctk.CTkFrame(um_frame)
            row.pack(fill='x', pady=6)
            self.new_username = ctk.CTkEntry(row, placeholder_text='Username')
            self.new_role = ctk.CTkComboBox(row, values=['owner','admin','manager','cashier','inventory_staff','employee'])
            self.new_fullname = ctk.CTkEntry(row, placeholder_text='Full name')
            self.new_password = ctk.CTkEntry(row, placeholder_text='Password', show='*')
            self.new_username.pack(side='left', padx=6)
            self.new_role.pack(side='left', padx=6)
            self.new_fullname.pack(side='left', padx=6)
            self.new_password.pack(side='left', padx=6)
            ctk.CTkButton(row, text='Create User', command=self._create_user).pack(side='left', padx=6)
        else:
            tk.Label(um_frame, text='User Management', bg='#1a1a1a', fg='white').pack(anchor='w')
            row = tk.Frame(um_frame)
            row.pack(fill='x', pady=6)
            self.new_username = tk.Entry(row)
            self.new_role_var = tk.StringVar(value='cashier')
            self.new_role = ttk.Combobox(row, textvariable=self.new_role_var, values=['owner','admin','manager','cashier','inventory_staff','employee'])
            self.new_fullname = tk.Entry(row)
            self.new_password = tk.Entry(row, show='*')
            self.new_username.pack(side='left', padx=6)
            self.new_role.pack(side='left', padx=6)
            self.new_fullname.pack(side='left', padx=6)
            self.new_password.pack(side='left', padx=6)
            tk.Button(row, text='Create User', command=self._create_user).pack(side='left', padx=6)

        # Load user list
        self.user_list = (ctk.CTkTextbox(self) if CTK_AVAILABLE else tk.Text(self, height=6))
        self.user_list.pack(fill='x', padx=20, pady=6)
        self._load_users()

    def add_item(self):
        name = self.name_entry.get() if CTK_AVAILABLE else self.name_entry.get()
        cat = self.cat_entry.get() if CTK_AVAILABLE else self.cat_entry.get()
        try:
            price = float(self.price_entry.get())
        except Exception:
            messagebox.showerror('Error', 'Invalid price')
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO menu_items (name, category, price, is_available) VALUES (?, ?, ?, 1)', (name, cat, price))
        conn.commit()
        conn.close()
        messagebox.showinfo('Added', f'Added {name} to menu')
        self.load_summary()

    def _create_user(self):
        # Create user via auth module
        try:
            from auth import create_user
        except Exception:
            messagebox.showerror('Error', 'Auth module not available')
            return

        username = self.new_username.get() if CTK_AVAILABLE else self.new_username.get()
        role = self.new_role.get() if CTK_AVAILABLE else self.new_role.get()
        full = self.new_fullname.get() if CTK_AVAILABLE else self.new_fullname.get()
        pwd = self.new_password.get() if CTK_AVAILABLE else self.new_password.get()
        try:
            uid = create_user(username, pwd, role, full)
            messagebox.showinfo('Created', f'User {username} created (id {uid})')
            self._load_users()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _load_users(self):
        self.user_list.delete('1.0', 'end')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, username, full_name, role, created_at FROM users ORDER BY id DESC')
        for r in cur.fetchall():
            self.user_list.insert('end', f'{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}\n')
        conn.close()

    def load_summary(self):
        self.summary.delete('1.0', 'end')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT DATE(created_at), COALESCE(SUM(total_amount),0) FROM transactions GROUP BY DATE(created_at) ORDER BY DATE(created_at) DESC LIMIT 14')
        for r in cur.fetchall():
            self.summary.insert('end', f'{r[0]} | ${r[1]:.2f}\n')
        conn.close()

    def _make_header(self, title):
        if CTK_AVAILABLE:
            return ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=20, weight='bold'))
        else:
            return tk.Label(self, text=title, fg='white', bg='#1a1a1a', font=('Sans', 16, 'bold'))


# ---------------------------
# Run
# ---------------------------
if __name__ == '__main__':
    app = CafeCraftGUI()
    app.run()
