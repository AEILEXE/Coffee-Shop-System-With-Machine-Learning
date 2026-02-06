"""
CAFÉCRAFT REPORTS SERVICE LAYER

Responsibilities:
- Generate sales reports
- Analyze transaction data
- Calculate profitability metrics
- Track best-selling items
- Time-period analysis (daily, weekly, monthly)
- Export capabilities
"""

from database.db import get_db_connection
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta


class ReportsService:
    """Handle reports and analytics."""

    def __init__(self, db_path: str = None):
        """Initialize reports service."""
        self.db_path = db_path

    def get_sales_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get sales summary for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD). Defaults to today.
            end_date: End date (YYYY-MM-DD). Defaults to today.

        Returns:
            Dict with sales metrics.
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        try:
            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()

            with db_connection as db:
                # Total sales
                query_sales = """
                    SELECT COUNT(id), SUM(total_amount)
                    FROM orders
                    WHERE DATE(created_at) BETWEEN ? AND ? AND status = 'completed'
                """
                sales_row = db.execute_fetch_one(query_sales, (start_date, end_date))

                # Total cost
                query_cost = """
                    SELECT SUM(oi.quantity * p.cost)
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE DATE(o.created_at) BETWEEN ? AND ? AND o.status = 'completed'
                """
                cost_row = db.execute_fetch_one(query_cost, (start_date, end_date))

                order_count = sales_row[0] or 0
                total_sales = sales_row[1] or 0.0
                total_cost = cost_row[0] or 0.0
                profit = total_sales - total_cost

                return {
                    "start_date": start_date,
                    "end_date": end_date,
                    "order_count": order_count,
                    "total_sales": total_sales,
                    "total_cost": total_cost,
                    "profit": profit,
                    "profit_margin": (profit / total_sales * 100) if total_sales > 0 else 0,
                    "average_order_value": total_sales / order_count if order_count > 0 else 0,
                }

        except Exception as e:
            print(f"Error generating sales summary: {e}")
            return {
                "start_date": start_date,
                "end_date": end_date,
                "order_count": 0,
                "total_sales": 0.0,
                "total_cost": 0.0,
                "profit": 0.0,
                "profit_margin": 0,
                "average_order_value": 0,
            }

    def get_best_sellers(self, start_date: str = None, end_date: str = None, limit: int = 10) -> List[Dict]:
        """
        Get best-selling products in date range.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            limit: Number of items to return.

        Returns:
            List of product sales dicts.
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        query = """
            SELECT p.id, p.name, p.category, SUM(oi.quantity) as total_qty, 
                   SUM(oi.subtotal) as total_sales, p.price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) BETWEEN ? AND ? AND o.status = 'completed'
            GROUP BY p.id, p.name, p.category
            ORDER BY total_qty DESC
            LIMIT ?
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query, (start_date, end_date, limit))
            else:
                with get_db_connection() as db:
                    rows = db.execute_fetch_all(query, (start_date, end_date, limit))

            return [
                {
                    "product_id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "quantity_sold": row[3],
                    "total_sales": row[4],
                    "unit_price": row[5],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching best sellers: {e}")
            return []

    def get_sales_by_payment_method(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get sales breakdown by payment method.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            List of dicts with payment method and amounts.
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        query = """
            SELECT payment_method, COUNT(id), SUM(total_amount)
            FROM orders
            WHERE DATE(created_at) BETWEEN ? AND ? AND status = 'completed'
            GROUP BY payment_method
            ORDER BY SUM(total_amount) DESC
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query, (start_date, end_date))
            else:
                with get_db_connection() as db:
                    rows = db.execute_fetch_all(query, (start_date, end_date))

            return [
                {
                    "payment_method": row[0],
                    "transaction_count": row[1],
                    "total_amount": row[2],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching payment methods: {e}")
            return []

    def get_hourly_sales(self, date: str = None) -> List[Dict]:
        """
        Get sales data broken down by hour.

        Args:
            date: Date (YYYY-MM-DD). Defaults to today.

        Returns:
            List of hourly sales dicts.
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        query = """
            SELECT STRFTIME('%H', created_at) as hour, COUNT(id), SUM(total_amount)
            FROM orders
            WHERE DATE(created_at) = ? AND status = 'completed'
            GROUP BY hour
            ORDER BY hour
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query, (date,))
            else:
                with get_db_connection() as db:
                    rows = db.execute_fetch_all(query, (date,))

            return [
                {
                    "hour": row[0],
                    "order_count": row[1],
                    "total_sales": row[2],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching hourly sales: {e}")
            return []

    def get_monthly_trend(self, months: int = 12) -> List[Dict]:
        """
        Get sales trend over last N months.

        Args:
            months: Number of months to include.

        Returns:
            List of monthly sales dicts.
        """
        query = """
            SELECT STRFTIME('%Y-%m', created_at) as month, COUNT(id), SUM(total_amount)
            FROM orders
            WHERE status = 'completed'
            GROUP BY month
            ORDER BY month DESC
            LIMIT ?
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query, (months,))
            else:
                with get_db_connection() as db:
                    rows = db.execute_fetch_all(query, (months,))

            return [
                {
                    "month": row[0],
                    "order_count": row[1],
                    "total_sales": row[2],
                }
                for row in reversed(rows)  # Reverse to chronological order
            ]
        except Exception as e:
            print(f"Error fetching monthly trend: {e}")
            return []

    def get_all_transactions(self, start_date: str = None, end_date: str = None, limit: int = 100) -> List[Dict]:
        """
        Get all transactions in date range.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            limit: Max results to return.

        Returns:
            List of transaction dicts.
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        query = """
            SELECT t.id, t.type, t.quantity, t.unit_price, t.total_amount, 
                   COALESCE(p.name, i.name, 'General') as item_name,
                   u.full_name as user_name, t.created_at, t.notes
            FROM transactions t
            LEFT JOIN products p ON t.product_id = p.id
            LEFT JOIN ingredients i ON t.ingredient_id = i.id
            LEFT JOIN users u ON t.user_id = u.id
            WHERE DATE(t.created_at) BETWEEN ? AND ?
            ORDER BY t.created_at DESC
            LIMIT ?
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query, (start_date, end_date, limit))
            else:
                with get_db_connection() as db:
                    rows = db.execute_fetch_all(query, (start_date, end_date, limit))

            return [
                {
                    "id": row[0],
                    "type": row[1],
                    "quantity": row[2],
                    "unit_price": row[3],
                    "total_amount": row[4],
                    "item_name": row[5],
                    "user_name": row[6],
                    "timestamp": row[7],
                    "notes": row[8],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return []

    def get_category_performance(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get sales performance by product category.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            List of category performance dicts.
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        query = """
            SELECT p.category, COUNT(DISTINCT o.id) as order_count, 
                   SUM(oi.quantity) as total_qty, SUM(oi.subtotal) as total_sales
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) BETWEEN ? AND ? AND o.status = 'completed'
            GROUP BY p.category
            ORDER BY total_sales DESC
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query, (start_date, end_date))
            else:
                with get_db_connection() as db:
                    rows = db.execute_fetch_all(query, (start_date, end_date))

            return [
                {
                    "category": row[0],
                    "order_count": row[1],
                    "total_quantity": row[2],
                    "total_sales": row[3],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching category performance: {e}")
            return []
