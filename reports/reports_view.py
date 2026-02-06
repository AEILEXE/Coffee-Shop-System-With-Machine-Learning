"""
CAFÉCRAFT REPORTS DASHBOARD

Responsibilities:
- Reports interface with sales and analytics
- Date range filters (from/to dates)
- Sales transactions table
- Best-selling items table
- Matplotlib charts embedded in Tkinter
- Export functionality trigger

No calculation logic (uses callbacks for data).
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
import tkinter as tk
from tkinter import filedialog
from typing import Callable, Optional, List, Dict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config.settings import (
    COLOR_PRIMARY_BG,
    COLOR_SECONDARY_BG,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_TEXT_PRIMARY,
)


class ReportsView:
    """Reports dashboard for CAFÉCRAFT."""

    def __init__(
        self,
        parent,
        user_info: Dict,
        on_date_range_change: Optional[Callable[[str, str], None]] = None,
        on_export: Optional[Callable[[str, str], None]] = None,
    ):
        """
        Initialize reports view.

        Args:
            parent: Parent widget (content frame).
            user_info: Current user dict.
            on_date_range_change: Callback(from_date, to_date) when date filter changes.
            on_export: Callback(from_date, to_date) when export is clicked.
        """
        self.parent = parent
        self.user_info = user_info
        self.on_date_range_change = on_date_range_change
        self.on_export = on_export

        # Data
        self.sales_data = []
        self.best_sellers = []
        self.chart_data = {}

        # Default date range (last 30 days)
        self.to_date = datetime.now()
        self.from_date = self.to_date - timedelta(days=30)

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build reports interface layout."""
        if CTK_AVAILABLE:
            main_frame = ctk.CTkFrame(self.parent, fg_color=COLOR_PRIMARY_BG)
        else:
            main_frame = tk.Frame(self.parent, bg=COLOR_PRIMARY_BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Header
        self._build_header(main_frame)

        # Filters
        self._build_filters(main_frame)

        # Content (tabs for different views)
        self._build_content(main_frame)

    def _build_header(self, parent):
        """Build header section."""
        if CTK_AVAILABLE:
            header = ctk.CTkFrame(parent, fg_color="transparent")
        else:
            header = tk.Frame(parent, bg=COLOR_PRIMARY_BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        if CTK_AVAILABLE:
            title = ctk.CTkLabel(
                header,
                text="Sales Reports & Analytics",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            title = tk.Label(
                header,
                text="Sales Reports & Analytics",
                font=("Georgia", 18, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_PRIMARY_BG,
            )
        title.pack(anchor="w")

    def _build_filters(self, parent):
        """Build date filter section."""
        if CTK_AVAILABLE:
            filter_frame = ctk.CTkFrame(parent, fg_color=COLOR_SECONDARY_BG, corner_radius=10)
        else:
            filter_frame = tk.Frame(parent, bg=COLOR_SECONDARY_BG)
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_columnconfigure(4, weight=1)

        # From date
        if CTK_AVAILABLE:
            from_lbl = ctk.CTkLabel(
                filter_frame,
                text="From Date:",
                font=ctk.CTkFont(size=12),
            )
        else:
            from_lbl = tk.Label(
                filter_frame,
                text="From Date:",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_SECONDARY_BG,
            )
        from_lbl.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        if CTK_AVAILABLE:
            self.from_date_entry = ctk.CTkEntry(
                filter_frame,
                width=120,
                placeholder_text="YYYY-MM-DD",
            )
            self.from_date_entry.insert(0, self.from_date.strftime("%Y-%m-%d"))
        else:
            self.from_date_entry = tk.Entry(filter_frame, width=15)
            self.from_date_entry.insert(0, self.from_date.strftime("%Y-%m-%d"))
        self.from_date_entry.grid(row=0, column=1, padx=5, pady=15)

        # To date
        if CTK_AVAILABLE:
            to_lbl = ctk.CTkLabel(
                filter_frame,
                text="To Date:",
                font=ctk.CTkFont(size=12),
            )
        else:
            to_lbl = tk.Label(
                filter_frame,
                text="To Date:",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_SECONDARY_BG,
            )
        to_lbl.grid(row=0, column=2, padx=15, pady=15, sticky="w")

        if CTK_AVAILABLE:
            self.to_date_entry = ctk.CTkEntry(
                filter_frame,
                width=120,
                placeholder_text="YYYY-MM-DD",
            )
            self.to_date_entry.insert(0, self.to_date.strftime("%Y-%m-%d"))
        else:
            self.to_date_entry = tk.Entry(filter_frame, width=15)
            self.to_date_entry.insert(0, self.to_date.strftime("%Y-%m-%d"))
        self.to_date_entry.grid(row=0, column=3, padx=5, pady=15)

        # Apply button
        if CTK_AVAILABLE:
            apply_btn = ctk.CTkButton(
                filter_frame,
                text="Apply",
                width=100,
                fg_color=COLOR_ACCENT,
                command=self._apply_filters,
            )
        else:
            apply_btn = tk.Button(
                filter_frame,
                text="Apply",
                width=12,
                bg=COLOR_ACCENT,
                fg="#1a1a2e",
                relief="flat",
                command=self._apply_filters,
            )
        apply_btn.grid(row=0, column=4, padx=5, pady=15, sticky="e")

        # Export button
        if CTK_AVAILABLE:
            export_btn = ctk.CTkButton(
                filter_frame,
                text="Export",
                width=100,
                fg_color=COLOR_SUCCESS,
                hover_color="#1f7f1f",
                command=self._export_report,
            )
        else:
            export_btn = tk.Button(
                filter_frame,
                text="Export",
                width=12,
                bg=COLOR_SUCCESS,
                fg="white",
                relief="flat",
                command=self._export_report,
            )
        export_btn.grid(row=0, column=5, padx=(5, 15), pady=15)

    def _build_content(self, parent):
        """Build main content area with tabs."""
        if CTK_AVAILABLE:
            content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        else:
            content_frame = tk.Frame(parent, bg=COLOR_PRIMARY_BG)
        content_frame.grid(row=2, column=0, sticky="nsew")
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill="both", expand=True)

        # Sales tab
        sales_tab = tk.Frame(self.notebook, bg=COLOR_PRIMARY_BG)
        self.notebook.add(sales_tab, text="Sales Transactions")
        self._build_sales_tab(sales_tab)

        # Best sellers tab
        sellers_tab = tk.Frame(self.notebook, bg=COLOR_PRIMARY_BG)
        self.notebook.add(sellers_tab, text="Best Sellers")
        self._build_sellers_tab(sellers_tab)

        # Charts tab
        charts_tab = tk.Frame(self.notebook, bg=COLOR_PRIMARY_BG)
        self.notebook.add(charts_tab, text="Charts")
        self._build_charts_tab(charts_tab)

    def _build_sales_tab(self, parent):
        """Build sales transactions table."""
        if CTK_AVAILABLE:
            table_frame = ctk.CTkFrame(parent, fg_color=COLOR_SECONDARY_BG, corner_radius=10)
        else:
            table_frame = tk.Frame(parent, bg=COLOR_SECONDARY_BG)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        table_frame.pack_propagate(False)

        # Title
        if CTK_AVAILABLE:
            title = ctk.CTkLabel(
                table_frame,
                text="Sales Transactions",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            title = tk.Label(
                table_frame,
                text="Sales Transactions",
                font=("Georgia", 14, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
        title.pack(padx=10, pady=(10, 5), anchor="w")

        # Treeview
        columns = ("Date", "Order Name", "Amount", "Payment Method", "User")
        self.sales_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
        )

        self.sales_tree.heading("Date", text="Date")
        self.sales_tree.heading("Order Name", text="Order Name")
        self.sales_tree.heading("Amount", text="Amount")
        self.sales_tree.heading("Payment Method", text="Payment Method")
        self.sales_tree.heading("User", text="User")

        self.sales_tree.column("Date", width=150)
        self.sales_tree.column("Order Name", width=150)
        self.sales_tree.column("Amount", width=120, anchor="e")
        self.sales_tree.column("Payment Method", width=150)
        self.sales_tree.column("User", width=120)

        self.sales_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_sellers_tab(self, parent):
        """Build best sellers table."""
        if CTK_AVAILABLE:
            table_frame = ctk.CTkFrame(parent, fg_color=COLOR_SECONDARY_BG, corner_radius=10)
        else:
            table_frame = tk.Frame(parent, bg=COLOR_SECONDARY_BG)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        table_frame.pack_propagate(False)

        # Title
        if CTK_AVAILABLE:
            title = ctk.CTkLabel(
                table_frame,
                text="Best-Selling Items",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            title = tk.Label(
                table_frame,
                text="Best-Selling Items",
                font=("Georgia", 14, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
        title.pack(padx=10, pady=(10, 5), anchor="w")

        # Treeview
        columns = ("Rank", "Item", "Quantity Sold", "Revenue", "Avg Price")
        self.sellers_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
        )

        self.sellers_tree.heading("Rank", text="Rank")
        self.sellers_tree.heading("Item", text="Item")
        self.sellers_tree.heading("Quantity Sold", text="Qty Sold")
        self.sellers_tree.heading("Revenue", text="Revenue")
        self.sellers_tree.heading("Avg Price", text="Avg Price")

        self.sellers_tree.column("Rank", width=60, anchor="center")
        self.sellers_tree.column("Item", width=200)
        self.sellers_tree.column("Quantity Sold", width=120, anchor="e")
        self.sellers_tree.column("Revenue", width=120, anchor="e")
        self.sellers_tree.column("Avg Price", width=120, anchor="e")

        self.sellers_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_charts_tab(self, parent):
        """Build charts section."""
        if CTK_AVAILABLE:
            charts_frame = ctk.CTkFrame(parent, fg_color=COLOR_PRIMARY_BG)
        else:
            charts_frame = tk.Frame(parent, bg=COLOR_PRIMARY_BG)
        charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        charts_frame.grid_rowconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(1, weight=1)

        # Sales over time chart
        self.sales_chart_frame = tk.Frame(charts_frame, bg=COLOR_SECONDARY_BG)
        self.sales_chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))

        # Payment method pie chart
        self.payment_chart_frame = tk.Frame(charts_frame, bg=COLOR_SECONDARY_BG)
        self.payment_chart_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))

        # Top items bar chart
        self.items_chart_frame = tk.Frame(charts_frame, bg=COLOR_SECONDARY_BG)
        self.items_chart_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0, pady=(5, 0))

    def _apply_filters(self):
        """Apply date range filters."""
        try:
            from_date_str = self.from_date_entry.get()
            to_date_str = self.to_date_entry.get()

            # Validate dates
            self.from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
            self.to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

            if self.from_date > self.to_date:
                messagebox.showerror("Invalid Range", "From date must be before to date")
                return

            # Invoke callback
            if self.on_date_range_change:
                self.on_date_range_change(from_date_str, to_date_str)

        except ValueError:
            messagebox.showerror("Invalid Format", "Please use YYYY-MM-DD format")

    def _export_report(self):
        """Export report to CSV."""
        try:
            from_date_str = self.from_date_entry.get()
            to_date_str = self.to_date_entry.get()

            if self.on_export:
                self.on_export(from_date_str, to_date_str)
            else:
                messagebox.showinfo("Export", "Export functionality not configured")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def load_sales_data(self, sales: List[Dict]):
        """
        Load sales transactions data.

        Args:
            sales: List of transaction dicts with 'date', 'order_name', 'amount', 'payment_method', 'user'.
        """
        self.sales_data = sales

        # Clear tree
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)

        # Add items
        for sale in sales:
            values = (
                sale.get("date", ""),
                sale.get("order_name", ""),
                f"₱ {sale.get('amount', 0):.2f}",
                sale.get("payment_method", ""),
                sale.get("user", ""),
            )
            self.sales_tree.insert("", "end", values=values)

    def load_best_sellers(self, items: List[Dict]):
        """
        Load best-selling items data.

        Args:
            items: List of item dicts with 'rank', 'name', 'quantity', 'revenue', 'avg_price'.
        """
        self.best_sellers = items

        # Clear tree
        for item in self.sellers_tree.get_children():
            self.sellers_tree.delete(item)

        # Add items
        for item in items:
            values = (
                item.get("rank", ""),
                item.get("name", ""),
                f"{item.get('quantity', 0):.0f}",
                f"₱ {item.get('revenue', 0):.2f}",
                f"₱ {item.get('avg_price', 0):.2f}",
            )
            self.sellers_tree.insert("", "end", values=values)

    def load_chart_data(self, data: Dict):
        """
        Load data for charts.

        Args:
            data: Dict with 'sales_over_time', 'payment_methods', 'top_items'.
        """
        self.chart_data = data
        self._render_charts()

    def _render_charts(self):
        """Render all charts."""
        # Sales over time
        if "sales_over_time" in self.chart_data:
            self._render_sales_chart()

        # Payment methods pie chart
        if "payment_methods" in self.chart_data:
            self._render_payment_chart()

        # Top items bar chart
        if "top_items" in self.chart_data:
            self._render_items_chart()

    def _render_sales_chart(self):
        """Render sales over time line chart."""
        data = self.chart_data.get("sales_over_time", {})
        if not data:
            return

        # Clear frame
        for widget in self.sales_chart_frame.winfo_children():
            widget.destroy()

        # Create figure
        fig = Figure(figsize=(6, 4), dpi=80, facecolor=COLOR_SECONDARY_BG)
        ax = fig.add_subplot(111, facecolor=COLOR_SECONDARY_BG)

        dates = list(data.keys())
        amounts = list(data.values())

        ax.plot(dates, amounts, marker='o', color=COLOR_ACCENT, linewidth=2)
        ax.set_xlabel("Date", color=COLOR_TEXT_PRIMARY)
        ax.set_ylabel("Amount (₱)", color=COLOR_TEXT_PRIMARY)
        ax.set_title("Sales Over Time", color=COLOR_ACCENT, fontweight='bold')
        ax.tick_params(colors=COLOR_TEXT_PRIMARY)
        ax.grid(True, alpha=0.2)

        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.sales_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _render_payment_chart(self):
        """Render payment methods pie chart."""
        data = self.chart_data.get("payment_methods", {})
        if not data:
            return

        # Clear frame
        for widget in self.payment_chart_frame.winfo_children():
            widget.destroy()

        # Create figure
        fig = Figure(figsize=(6, 4), dpi=80, facecolor=COLOR_SECONDARY_BG)
        ax = fig.add_subplot(111, facecolor=COLOR_SECONDARY_BG)

        methods = list(data.keys())
        amounts = list(data.values())
        colors = [COLOR_ACCENT, COLOR_SUCCESS, COLOR_ERROR]

        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=methods,
            autopct='%1.1f%%',
            colors=colors[:len(methods)],
            textprops={'color': COLOR_TEXT_PRIMARY},
        )

        ax.set_title("Payment Methods", color=COLOR_ACCENT, fontweight='bold')

        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.payment_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _render_items_chart(self):
        """Render top items bar chart."""
        data = self.chart_data.get("top_items", {})
        if not data:
            return

        # Clear frame
        for widget in self.items_chart_frame.winfo_children():
            widget.destroy()

        # Create figure
        fig = Figure(figsize=(12, 4), dpi=80, facecolor=COLOR_SECONDARY_BG)
        ax = fig.add_subplot(111, facecolor=COLOR_SECONDARY_BG)

        items = list(data.keys())
        quantities = list(data.values())

        ax.bar(items, quantities, color=COLOR_ACCENT, edgecolor=COLOR_TEXT_PRIMARY)
        ax.set_xlabel("Item", color=COLOR_TEXT_PRIMARY)
        ax.set_ylabel("Quantity Sold", color=COLOR_TEXT_PRIMARY)
        ax.set_title("Top Selling Items", color=COLOR_ACCENT, fontweight='bold')
        ax.tick_params(colors=COLOR_TEXT_PRIMARY)
        ax.grid(True, alpha=0.2, axis='y')

        # Rotate labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        fig.tight_layout()

        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.items_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
