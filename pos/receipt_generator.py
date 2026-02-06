"""
CAFÉCRAFT RECEIPT GENERATOR

Responsibilities:
- Format receipts for printing/display
- Generate receipt text with order details
- Support for different receipt formats
"""

from datetime import datetime
from typing import Dict
from config.settings import APP_NAME


class ReceiptGenerator:
    """Generate formatted receipts for transactions."""

    RECEIPT_WIDTH = 50
    SEPARATOR_CHAR = "-"

    def __init__(self):
        """Initialize receipt generator."""
        pass

    def generate_receipt(self, receipt_data: Dict) -> str:
        """
        Generate a formatted receipt.

        Args:
            receipt_data: Receipt data dict with order info and items.

        Returns:
            Formatted receipt as string.
        """
        lines = []

        # Header
        lines.append(self._center(APP_NAME))
        lines.append(self._center("RECEIPT"))
        lines.append(self._separator())

        # Order info
        lines.append("")
        lines.append(f"Order #: {receipt_data['order_number']}")
        lines.append(f"Date/Time: {self._format_datetime(receipt_data['timestamp'])}")
        lines.append(f"Cashier: {receipt_data['cashier']}")
        lines.append(f"Payment: {receipt_data['payment_method']}")

        # Items
        lines.append("")
        lines.append(self._separator())
        lines.append(f"{'Item':<30} {'Qty':>5} {'Price':>12}")
        lines.append(self._separator())

        for item in receipt_data["items"]:
            name = item["name"][:30]
            qty = str(item["quantity"])
            subtotal = f"₱{item['subtotal']:.2f}"

            lines.append(f"{name:<30} {qty:>5} {subtotal:>12}")

        # Total section
        lines.append(self._separator())
        subtotal = receipt_data["subtotal"]
        total = receipt_data["total"]
        discount = subtotal - total

        lines.append(f"{'Subtotal':<30} {'₱' + str(f'{subtotal:.2f}'):>18}")

        if discount > 0:
            lines.append(f"{'Discount':<30} {'-₱' + str(f'{discount:.2f}'):>17}")

        lines.append(f"{'TOTAL':<30} {'₱' + str(f'{total:.2f}'):>18}")
        lines.append(self._separator())

        # Footer
        lines.append("")
        lines.append(self._center("Thank you for your purchase!"))
        lines.append("")
        lines.append(self._center(f"Processed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))

        return "\n".join(lines)

    def _center(self, text: str) -> str:
        """Center text within receipt width."""
        return text.center(self.RECEIPT_WIDTH)

    def _separator(self) -> str:
        """Create a separator line."""
        return self.SEPARATOR_CHAR * self.RECEIPT_WIDTH

    def _format_datetime(self, dt_string: str) -> str:
        """Format datetime string for display."""
        try:
            dt = datetime.fromisoformat(dt_string)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return dt_string

    def generate_receipt_html(self, receipt_data: Dict) -> str:
        """
        Generate receipt as HTML for printing.

        Args:
            receipt_data: Receipt data dict.

        Returns:
            HTML-formatted receipt.
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Receipt - {receipt_data['order_number']}</title>
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    width: 4in;
                    margin: 0.5in;
                    background-color: white;
                }}
                .header {{
                    text-align: center;
                    font-weight: bold;
                    font-size: 16px;
                    margin-bottom: 10px;
                }}
                .separator {{
                    border-top: 1px solid #000;
                    margin: 10px 0;
                }}
                .order-info {{
                    font-size: 12px;
                    margin-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                    margin: 10px 0;
                }}
                th {{
                    text-align: left;
                    border-bottom: 1px solid #000;
                    padding: 5px 0;
                }}
                td {{
                    padding: 3px 0;
                }}
                .item-name {{
                    text-align: left;
                }}
                .item-qty {{
                    text-align: right;
                    width: 30px;
                }}
                .item-price {{
                    text-align: right;
                    width: 60px;
                }}
                .total-row {{
                    font-weight: bold;
                    border-top: 1px solid #000;
                    border-bottom: 2px solid #000;
                }}
                .footer {{
                    text-align: center;
                    font-size: 11px;
                    margin-top: 20px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">{APP_NAME}</div>
            <div class="header">RECEIPT</div>

            <div class="separator"></div>

            <div class="order-info">
                <strong>Order #:</strong> {receipt_data['order_number']}<br>
                <strong>Date/Time:</strong> {self._format_datetime(receipt_data['timestamp'])}<br>
                <strong>Cashier:</strong> {receipt_data['cashier']}<br>
                <strong>Payment:</strong> {receipt_data['payment_method']}
            </div>

            <div class="separator"></div>

            <table>
                <tr>
                    <th class="item-name">Item</th>
                    <th class="item-qty">Qty</th>
                    <th class="item-price">Price</th>
                </tr>
        """

        for item in receipt_data["items"]:
            html += f"""
                <tr>
                    <td class="item-name">{item['name']}</td>
                    <td class="item-qty">{item['quantity']}</td>
                    <td class="item-price">₱{item['subtotal']:.2f}</td>
                </tr>
            """

        subtotal = receipt_data["subtotal"]
        total = receipt_data["total"]
        discount = subtotal - total

        html += f"""
            </table>

            <div class="separator"></div>

            <table>
                <tr>
                    <td><strong>Subtotal</strong></td>
                    <td style="text-align: right;">₱{subtotal:.2f}</td>
                </tr>
        """

        if discount > 0:
            html += f"""
                <tr>
                    <td><strong>Discount</strong></td>
                    <td style="text-align: right;">-₱{discount:.2f}</td>
                </tr>
            """

        html += f"""
                <tr class="total-row">
                    <td><strong>TOTAL</strong></td>
                    <td style="text-align: right; border-bottom: 2px solid #000;"><strong>₱{total:.2f}</strong></td>
                </tr>
            </table>

            <div class="footer">
                Thank you for your purchase!<br>
                Processed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </body>
        </html>
        """
        return html
