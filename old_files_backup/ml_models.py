import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np
from datetime import datetime, timedelta
from database import get_connection

class MLModels:
    def __init__(self):
        self.sales_model = None
        self.train_sales_model()

    def train_sales_model(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATE(created_at), SUM(total_amount) FROM transactions GROUP BY DATE(created_at) ORDER BY DATE(created_at)")
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            # Fallback to dummy
            dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
            sales = np.random.randint(100, 500, size=len(dates))
            df = pd.DataFrame({'date': dates, 'sales': sales})
        else:
            df = pd.DataFrame(data, columns=['date', 'sales'])
            df['date'] = pd.to_datetime(df['date'])
        
        df['day_of_year'] = df['date'].dt.dayofyear
        X = df[['day_of_year']]
        y = df['sales']
        if len(X) > 1:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            self.sales_model = LinearRegression()
            self.sales_model.fit(X_train, y_train)
        else:
            self.sales_model = None

    def predict_daily_sales(self, day_of_year):
        if self.sales_model:
            return self.sales_model.predict([[day_of_year]])[0]
        return 200  # Default

    def inventory_demand_forecast(self, item_name, category):
        conn = get_connection()
        cursor = conn.cursor()
        # Get current stock
        cursor.execute("SELECT quantity FROM inventory_items WHERE name = ? AND category = ?", (item_name, category))
        stock_row = cursor.fetchone()
        stock = stock_row[0] if stock_row else 0
        
        # Get avg daily sales from transactions
        cursor.execute("""
            SELECT AVG(qty) FROM (
                SELECT DATE(t.created_at), SUM(ti.quantity) as qty
                FROM transactions t
                JOIN transaction_items ti ON t.id = ti.transaction_id
                JOIN menu_items m ON ti.menu_item_id = m.id
                WHERE m.name = ? AND m.category = ?
                GROUP BY DATE(t.created_at)
            )
        """, (item_name, category))
        avg_sales = cursor.fetchone()[0] or 0
        conn.close()
        
        days = stock / avg_sales if avg_sales > 0 else 999
        return f"{item_name} likely to run out in {int(days)} days"

    def best_seller_prediction(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.name, SUM(ti.quantity) as total_qty
            FROM transaction_items ti
            JOIN menu_items m ON ti.menu_item_id = m.id
            GROUP BY m.id ORDER BY total_qty DESC LIMIT 5
        """)
        results = cursor.fetchall()
        conn.close()
        return results

    def smart_restock_recommendation(self, item_name, category):
        conn = get_connection()
        cursor = conn.cursor()
        # Current stock
        cursor.execute("SELECT quantity FROM inventory_items WHERE name = ? AND category = ?", (item_name, category))
        stock = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        # Avg daily sales
        cursor.execute("""
            SELECT AVG(qty) FROM (
                SELECT DATE(t.created_at), SUM(ti.quantity) as qty
                FROM transactions t
                JOIN transaction_items ti ON t.id = ti.transaction_id
                JOIN menu_items m ON ti.menu_item_id = m.id
                WHERE m.name = ? AND m.category = ?
                GROUP BY DATE(t.created_at)
            )
        """, (item_name, category))
        avg_sales = cursor.fetchone()[0] or 0
        conn.close()
        
        recommended = avg_sales * 7 - stock  # 7-day supply
        return max(0, recommended)
# Example: ml.predict_daily_sales(100)  # For day 100