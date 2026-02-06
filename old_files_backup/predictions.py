"""
CAFÉCRAFT MACHINE LEARNING MODULE

TASK FOR COPILOT:
Implement offline ML-based decision support.

MODELS:
- Sales prediction using Linear Regression
- Inventory demand forecasting
- Best-seller prediction
- Smart restock recommendation

DATA:
- SQLite transaction data
- Inventory usage logs
"""
# TODO: Implement Linear Regression sales prediction
# TODO: Predict days until inventory depletion
# TODO: Rank best-selling items
# TODO: Generate restock recommendations

from database import get_connection
from datetime import datetime, timedelta
from collections import defaultdict
import math


def _linear_regression_predict(xs, ys, future_xs):
    """Simple linear regression (least squares) without external libs.
    xs, ys: lists of numbers (same length). future_xs: list of x values to predict.
    Returns list of predicted y values for future_xs.
    """
    n = len(xs)
    if n == 0:
        return [0 for _ in future_xs]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        slope = 0
    else:
        slope = num / den
    intercept = mean_y - slope * mean_x
    return [slope * x + intercept for x in future_xs]

def get_sales_forecast(days=7):
    """Sales forecast using simple linear regression on daily totals.
    Returns list of predicted totals for the next `days` days.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DATE(created_at) as d, COALESCE(SUM(total_amount),0) as s
        FROM transactions
        WHERE created_at >= DATE('now', '-90 days')
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    ''')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return [0] * days

    # Map dates to integer x (days since first date)
    xs = []
    ys = []
    first_date = datetime.strptime(rows[0][0], '%Y-%m-%d')
    for r in rows:
        d = datetime.strptime(r[0], '%Y-%m-%d')
        xs.append((d - first_date).days)
        ys.append(float(r[1] or 0))

    last_x = xs[-1]
    future_xs = [last_x + i + 1 for i in range(days)]
    preds = _linear_regression_predict(xs, ys, future_xs)
    return [round(max(0, p), 2) for p in preds]

def get_low_stock_predictions():
    """Predict when items will run out based on usage"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get inventory items
    cursor.execute("SELECT id, name, quantity FROM inventory_items")
    items = cursor.fetchall()
    
    predictions = []
    for item in items:
        # Get average daily usage (from inventory logs)
        cursor.execute('''
            SELECT AVG(ABS(change_amount))
            FROM inventory_logs
            WHERE inventory_item_id = ? AND change_type = 'remove'
            AND created_at >= DATE('now', '-14 days')
        ''', (item[0],))
        
        avg_usage = cursor.fetchone()[0] or 0
        
        if avg_usage > 0:
            days_until_empty = int(item[2] / avg_usage)
            predictions.append({
                "name": item[1],
                "current": item[2],
                "daily_usage": round(avg_usage, 2),
                "days_left": days_until_empty
            })
    
    conn.close()
    return sorted(predictions, key=lambda x: x["days_left"])


def get_restock_recommendations():
    """Suggest restock quantities based on average daily usage and reorder threshold."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, quantity, reorder_threshold FROM inventory_items')
    items = cur.fetchall()
    recs = []
    for it in items:
        iid, name, qty, reorder = it
        # average daily usage from logs (14 days)
        cur.execute('''
            SELECT AVG(ABS(change_amount)) FROM inventory_logs
            WHERE inventory_item_id=? AND change_type='remove' AND created_at >= DATE('now', '-14 days')
        ''', (iid,))
        avg = cur.fetchone()[0] or 0
        if avg <= 0:
            rec_qty = max(0, reorder - qty)
        else:
            # recommend enough for 7 days plus reorder buffer
            rec_qty = max(0, int(math.ceil(avg * 7 + reorder - qty)))
        recs.append({'name': name, 'current': qty, 'recommended': rec_qty, 'daily_usage': round(avg,2)})
    conn.close()
    return recs

def get_bestseller_analysis():
    """Analyze best selling items by time of day"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.name, m.category, 
               SUM(ti.quantity) as total_sold,
               SUM(ti.subtotal) as revenue
        FROM transaction_items ti
        JOIN menu_items m ON ti.menu_item_id = m.id
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE t.created_at >= DATE('now', '-30 days')
        GROUP BY m.id
        ORDER BY total_sold DESC
        LIMIT 10
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{"name": r[0], "category": r[1], "sold": r[2], "revenue": r[3]} 
            for r in results]
