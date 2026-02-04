"""
CAFÉCRAFT REPORTS MODULE

TASK FOR COPILOT:
Generate analytics and visualizations.

REQUIREMENTS:
- Daily sales report
- Weekly sales report
- Monthly sales report
- Best-selling items
- Inventory usage

VISUALS:
- Tables (Treeview)
- Charts using matplotlib embedded in Tkinter
"""
# TODO: Add date range selector
# TODO: Calculate weekly and monthly sales
# TODO: Create matplotlib sales chart
# TODO: Create bestseller bar chart


import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import get_connection
from datetime import datetime, timedelta
try:
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False

from ml_models import MLModels

class ReportsFrame:
    def __init__(self, parent):
        self.parent = parent
        self.ml = MLModels()
        self.setup_ui()
    
    def setup_ui(self):
        main = tk.Frame(self.parent, bg="#1a1a2e")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="Sales Reports", font=("Georgia", 24, "bold"),
                 fg="white", bg="#1a1a2e").pack(anchor="w")
        
        # Summary cards
        cards = tk.Frame(main, bg="#1a1a2e")
        cards.pack(fill="x", pady=20)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Today's sales
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COALESCE(SUM(total_amount), 0) FROM transactions WHERE DATE(created_at) = ?",
            (today,)
        )
        today_sales = cursor.fetchone()[0]
        
        # Total transactions
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_trans = cursor.fetchone()[0]
        
        # Top selling item
        cursor.execute('''
            SELECT m.name, SUM(ti.quantity) as qty
            FROM transaction_items ti
            JOIN menu_items m ON ti.menu_item_id = m.id
            GROUP BY m.id ORDER BY qty DESC LIMIT 1
        ''')
        top_item = cursor.fetchone()
        
        conn.close()
        
        self._create_card(cards, "Today's Sales", f"${today_sales:.2f}", 0)
        self._create_card(cards, "Total Transactions", str(total_trans), 1)
        self._create_card(cards, "Top Seller", top_item[0] if top_item else "N/A", 2)
        
        # Recent transactions table
        tk.Label(main, text="Recent Transactions", font=("Georgia", 16),
                 fg="white", bg="#1a1a2e").pack(anchor="w", pady=(20, 10))
        
        scroll_frame = tk.Frame(main, bg="#1a1a2e")
        scroll_frame.pack(fill="both", expand=True)
        
        columns = ("ID", "Date", "Amount", "Payment")
        tree = ttk.Treeview(scroll_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            tree.heading(col, text=col)
        
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        tree.configure(yscrollcommand=scrollbar.set)
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, created_at, total_amount, payment_method FROM transactions ORDER BY created_at DESC LIMIT 20"
        )
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=(row[0], row[1][:16], f"${row[2]:.2f}", row[3]))
        conn.close()
        
        tree.pack(fill="both", expand=True)
        self.tree = tree
        # Bind double-click to open receipt view
        tree.bind('<Double-1>', lambda e: self._on_transaction_double_click())

        # ML Predictions
        ml_frame = tk.Frame(main, bg="#1a1a2e")
        ml_frame.pack(fill="x", pady=10)
        
        tk.Label(ml_frame, text="Machine Learning Predictions", font=("Georgia", 16),
                 fg="white", bg="#1a1a2e").pack(anchor="w", pady=(0,10))
        
        btn_frame = tk.Frame(ml_frame, bg="#1a1a2e")
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="Predict Daily Sales", bg="#8B4513", fg="white",
                  command=self.predict_sales).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Inventory Forecast", bg="#8B4513", fg="white",
                  command=self.inventory_forecast).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Best Sellers", bg="#8B4513", fg="white",
                  command=self.best_sellers).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Restock Recommendations", bg="#8B4513", fg="white",
                  command=self.restock_recommend).pack(side="left", padx=5)

        # Date range selector and charts
        dr_frame = tk.Frame(main, bg="#1a1a2e")
        dr_frame.pack(fill="x", pady=10)

        tk.Label(dr_frame, text="Start (YYYY-MM-DD):", fg="white", bg="#1a1a2e").pack(side="left")
        self.start_entry = tk.Entry(dr_frame)
        self.start_entry.pack(side="left", padx=5)
        tk.Label(dr_frame, text="End (YYYY-MM-DD):", fg="white", bg="#1a1a2e").pack(side="left")
        self.end_entry = tk.Entry(dr_frame)
        self.end_entry.pack(side="left", padx=5)
        tk.Button(dr_frame, text="Generate", command=self.generate_charts).pack(side="left", padx=10)

        # Placeholder for charts
        self.chart_frame = tk.Frame(main, bg="#1a1a2e")
        self.chart_frame.pack(fill="both", expand=True, pady=10)

    def generate_charts(self):
        # Parse dates
        try:
            if self.start_entry.get():
                start = datetime.strptime(self.start_entry.get(), "%Y-%m-%d")
            else:
                start = datetime.now() - timedelta(days=30)
        except Exception:
            start = datetime.now() - timedelta(days=30)

        try:
            if self.end_entry.get():
                end = datetime.strptime(self.end_entry.get(), "%Y-%m-%d")
            else:
                end = datetime.now()
        except Exception:
            end = datetime.now()

        # Clear chart frame
        for w in self.chart_frame.winfo_children():
            w.destroy()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DATE(created_at) as d, COALESCE(SUM(total_amount),0) FROM transactions
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY d ORDER BY d
        ''', (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))
        rows = cursor.fetchall()

        dates = [r[0] for r in rows]
        totals = [r[1] or 0 for r in rows]

        # Bestseller
        cursor.execute('''
            SELECT m.name, SUM(ti.quantity) as qty
            FROM transaction_items ti
            JOIN transactions t ON ti.transaction_id = t.id
            JOIN menu_items m ON ti.menu_item_id = m.id
            WHERE DATE(t.created_at) BETWEEN ? AND ?
            GROUP BY m.id ORDER BY qty DESC LIMIT 10
        ''', (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))
        bests = cursor.fetchall()
        conn.close()

        if not HAS_MATPLOTLIB:
            tk.Label(self.chart_frame, text="matplotlib not available; install it to see charts.", fg="white", bg="#1a1a2e").pack()
            return

        # Draw charts using matplotlib
        fig = Figure(figsize=(8, 4))
        ax = fig.add_subplot(121)
        if dates:
            ax.plot(dates, totals, marker='o')
            ax.set_title('Sales')
            ax.tick_params(axis='x', rotation=45)
        else:
            ax.text(0.5, 0.5, 'No data', ha='center')

        ax2 = fig.add_subplot(122)
        if bests:
            names = [b[0] for b in bests]
            qtys = [b[1] for b in bests]
            ax2.barh(names[::-1], qtys[::-1])
            ax2.set_title('Top Sellers')
        else:
            ax2.text(0.5, 0.5, 'No bestseller data', ha='center')

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()

    def _on_transaction_double_click(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        txid = item['values'][0]
        self._show_receipt(txid)

    def _show_receipt(self, txid):
        # Reconstruct receipt from DB and allow download
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, cashier_id, total_amount, discount_amount, payment_method, created_at FROM transactions WHERE id=?', (txid,))
        tx = cur.fetchone()
        if not tx:
            conn.close()
            messagebox.showerror('Error', 'Transaction not found')
            return
        cur.execute('SELECT menu_item_id, quantity, unit_price, subtotal FROM transaction_items WHERE transaction_id=?', (txid,))
        items = cur.fetchall()
        # Get cashier name
        cur.execute('SELECT full_name FROM users WHERE id=?', (tx[1],))
        cashier = cur.fetchone()
        cashier_name = cashier[0] if cashier else 'Unknown'
        conn.close()

        lines = []
        lines.append('CaféCraft Receipt')
        lines.append(f'Transaction ID: {tx[0]}')
        lines.append(f'Cashier: {cashier_name}')
        lines.append(f'Date: {tx[5]}')
        lines.append('-'*30)
        total = 0
        for it in items:
            # get item name
            conn2 = get_connection()
            c2 = conn2.cursor()
            c2.execute('SELECT name FROM menu_items WHERE id=?', (it[0],))
            row = c2.fetchone()
            name = row[0] if row else f'Item {it[0]}'
            conn2.close()
            lines.append(f'{name} x{it[1]} @ ${it[2]:.2f} = ${it[3]:.2f}')
            total += it[3]
        lines.append('-'*30)
        lines.append(f'Total: ${total:.2f}')
        lines.append(f'Payment: {tx[4]}')

        text = '\n'.join(lines)
        # popup
        win = tk.Toplevel(self.parent)
        win.title(f'Receipt {txid}')
        txt = tk.Text(win)
        txt.insert('1.0', text)
        txt.config(state='disabled')
        txt.pack(fill='both', expand=True)

        def save():
            path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text files','*.txt'), ('PDF files','*.pdf')])
            if path:
                if path.lower().endswith('.pdf'):
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
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
                else:
                    with open(path, 'w') as f:
                        f.write(text)
                    messagebox.showinfo('Saved', f'Receipt saved to {path}')

        btn = tk.Button(win, text='Download Receipt', command=save)
        btn.pack(pady=6)
    
    def _create_card(self, parent, title, value, col):
        card = tk.Frame(parent, bg="#16213e", padx=20, pady=15)
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        parent.columnconfigure(col, weight=1)
        
        tk.Label(card, text=title, fg="#888", bg="#16213e").pack()
        tk.Label(card, text=value, font=("Arial", 20, "bold"),
                 fg="#d4a574", bg="#16213e").pack()

    def predict_sales(self):
        today = datetime.now().timetuple().tm_yday
        prediction = self.ml.predict_daily_sales(today)
        messagebox.showinfo("Sales Prediction", f"Predicted sales for today: ${prediction:.2f}")

    def inventory_forecast(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, category FROM inventory_items")
        items = cursor.fetchall()
        conn.close()
        forecasts = [self.ml.inventory_demand_forecast(name, cat) for name, cat in items[:5]]  # Limit to 5
        messagebox.showinfo("Inventory Forecast", "\n".join(forecasts))

    def best_sellers(self):
        best = self.ml.best_seller_prediction()
        msg = "\n".join([f"{name}: {qty} sold" for name, qty in best])
        messagebox.showinfo("Best Sellers", msg or "No data")

    def restock_recommend(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, category FROM inventory_items")
        items = cursor.fetchall()
        conn.close()
        recommends = [f"{name}: Restock {self.ml.smart_restock_recommendation(name, cat):.0f} units" for name, cat in items[:5]]
        messagebox.showinfo("Restock Recommendations", "\n".join(recommends))
