"""
CAFÉCRAFT REPORTS MANAGER

Coordinates between Reports View and Service Layer
"""

from reports.reports_service import ReportsService
from reports.reports_view import ReportsView
from tkinter import messagebox
from typing import Dict, Optional, Callable
from datetime import datetime


class ReportsManager:
    """Manages reports and analytics."""

    def __init__(
        self,
        parent_frame,
        user_info: Dict,
        db_path: str = None,
    ):
        """
        Initialize reports manager.

        Args:
            parent_frame: Parent widget.
            user_info: Current user info.
            db_path: Database path.
        """
        self.parent_frame = parent_frame
        self.user_info = user_info
        self.db_path = db_path

        # Initialize service
        self.service = ReportsService(db_path)

        # Initialize view with data callbacks
        self.view = ReportsView(
            parent_frame,
            user_info,
            on_date_range_change=self._handle_date_range_change,
            on_export=self._handle_export,
        )

        # Load initial data
        self._load_reports()

    def _load_reports(self, start_date: str = None, end_date: str = None):
        """Load reports data."""
        try:
            if not start_date:
                start_date = datetime.now().strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            # Get all report data
            summary = self.service.get_sales_summary(start_date, end_date)
            best_sellers = self.service.get_best_sellers(start_date, end_date)
            payment_methods = self.service.get_sales_by_payment_method(start_date, end_date)
            transactions = self.service.get_all_transactions(start_date, end_date, limit=50)
            categories = self.service.get_category_performance(start_date, end_date)

            # Update view with data
            if hasattr(self.view, "update_reports"):
                self.view.update_reports(
                    summary=summary,
                    best_sellers=best_sellers,
                    payment_methods=payment_methods,
                    transactions=transactions,
                    categories=categories,
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load reports: {e}")

    def _handle_date_range_change(self, start_date: str, end_date: str):
        """Handle date range change."""
        self._load_reports(start_date, end_date)

    def _handle_export(self, from_date: str, to_date: str):
        """Handle report export."""
        try:
            messagebox.showinfo("Export", f"Export from {from_date} to {to_date} not yet implemented")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def get_sales_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get sales summary."""
        return self.service.get_sales_summary(start_date, end_date)

    def get_best_sellers(self, start_date: str = None, end_date: str = None, limit: int = 10):
        """Get best selling products."""
        return self.service.get_best_sellers(start_date, end_date, limit)

    def refresh(self):
        """Refresh all reports."""
        self._load_reports()
