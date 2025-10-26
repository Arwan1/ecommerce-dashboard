import sys
sys.path.append('.')
from gui.returns_dashboard import ReturnsDashboard
import tkinter as tk

print('Testing returns dashboard chart data...')

# Create a temporary dashboard instance to test the data fetching
class TestDashboard:
    def __init__(self):
        self.period_var = tk.StringVar(value='Last 30 Days')
        
    def get_date_filter_sql(self, time_period):
        if time_period == 'All Time':
            return ''
        elif time_period == 'Last 7 Days':
            return 'AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)'
        elif time_period == 'Last 30 Days':
            return 'AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)'
        elif time_period == 'Last 90 Days':
            return 'AND created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)'
        elif time_period == 'Last Year':
            return 'AND created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR)'
        else:
            return ''

dashboard = TestDashboard()

# Test the supplier returns part of get_returns_chart_data
from database.db_connector import get_db_connection
conn = get_db_connection()
if conn:
    cursor = conn.cursor(dictionary=True)
    date_filter = dashboard.get_date_filter_sql('Last 30 Days')
    
    print(f'Date filter: {date_filter}')
    
    try:
        query = f"""
            SELECT p.ready_made_supplier as supplier, COUNT(*) as return_count
            FROM returns r
            JOIN products p ON r.product_id = p.id
            WHERE 1=1 {date_filter.replace('created_at', 'r.created_at')}
              AND p.ready_made_supplier IS NOT NULL 
              AND p.ready_made_supplier != ''
            GROUP BY p.ready_made_supplier
            ORDER BY return_count DESC
            LIMIT 10
        """
        cursor.execute(query)
        supplier_returns = cursor.fetchall()
        print(f'Supplier returns data: {len(supplier_returns)} items')
        for item in supplier_returns:
            print(f'  {item["supplier"]}: {item["return_count"]}')
    except Exception as e:
        print(f'Error: {e}')
    
    conn.close()
