from database.db_operations import DBOperations
from database.db_connector import get_db_connection
import mysql.connector

class AnalyticsManager:
    """
    Manages analytics data retrieval from the database.
    """
    def __init__(self):
        """
        Initializes the AnalyticsManager with a DBOperations instance.
        """
        self.db_ops = DBOperations()

    def get_total_orders(self):
        """
        Retrieves the total number of orders from database
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(id) FROM orders")
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting total orders: {e}")
            return 0
        finally:
            conn.close()

    def get_total_revenue(self):
        """
        Retrieves the total revenue from all orders.
        Assumes 'orders' table has a 'total_price' column.
        """
        conn = get_db_connection()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total_price) FROM orders")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0.0
        except mysql.connector.Error as e:
            print(f"Error getting total revenue: {e}")
            return 0.0
        finally:
            conn.close()

    def get_new_customers(self, days=30):
        """
        Retrieves the number of new customers in the last 'days' days.
        Assumes 'users' table has a 'created_at' column (DATETIME or similar).
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            # This query is for MySQL. Using DATE_SUB instead of SQLite's date function
            cursor.execute("SELECT COUNT(id) FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)", (days,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting new customers: {e}")
            # Fallback if the query fails (e.g., table/column doesn't exist)
            return 0
        finally:
            conn.close()

    def get_pending_orders(self):
        """
        Retrieves the number of recent orders (last 3 days) as "pending".
        Since there's no status column, we'll treat recent orders as potentially pending.
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(id) FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 3 DAY)")
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting pending orders: {e}")
            return 0
        finally:
            conn.close()

    def get_orders_this_week(self):
        """
        Retrieves the number of orders placed in the current week.
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(id) FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting orders this week: {e}")
            return 0
        finally:
            conn.close()

    def get_revenue_this_month(self):
        """
        Retrieves the total revenue for the current month.
        """
        conn = get_db_connection()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total_price) FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0.0
        except mysql.connector.Error as e:
            print(f"Error getting revenue this month: {e}")
            return 0.0
        finally:
            conn.close()

    def get_pending_returns(self):
        """
        Retrieves the number of pending return claims.
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(id) FROM return_claims")
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting pending returns: {e}")
            return 0
        finally:
            conn.close()

    def get_supplier_returns_data(self, time_period="Last 30 Days"):
        """
        Retrieves comprehensive supplier returns data for dashboard analytics.
        Returns data for chart visualization and table display.
        """
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Convert time period to SQL date filter
            date_filter = self._get_date_filter_for_period(time_period)
            
            # Query for supplier returns data with comprehensive metrics
            query = f"""
                SELECT 
                    p.ready_made_supplier as supplier_name,
                    COUNT(DISTINCT r.id) as total_returns,
                    COUNT(DISTINCT oi.id) as total_items_sold,
                    ROUND(
                        (COUNT(DISTINCT r.id) * 100.0 / NULLIF(COUNT(DISTINCT oi.id), 0)), 
                        2
                    ) as return_rate_percent,
                    ROUND(AVG(r.refund_amount), 2) as avg_refund_amount,
                    SUM(r.refund_amount) as total_refund_amount,
                    COUNT(CASE WHEN r.status = 'Pending' THEN 1 END) as pending_returns,
                    COUNT(CASE WHEN r.status = 'Approved' THEN 1 END) as approved_returns,
                    COUNT(CASE WHEN r.status = 'Rejected' THEN 1 END) as rejected_returns
                FROM products p
                LEFT JOIN returns r ON r.product_id = p.id {date_filter.replace('WHERE', 'AND') if date_filter else ''}
                LEFT JOIN order_items oi ON oi.product_id = p.id
                WHERE p.ready_made_supplier IS NOT NULL 
                  AND p.ready_made_supplier != ''
                  AND p.ready_made_supplier != 'NULL'
                GROUP BY p.ready_made_supplier
                HAVING COUNT(DISTINCT oi.id) > 0
                ORDER BY return_rate_percent DESC, total_returns DESC
                LIMIT 20
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convert results to list of dictionaries for easier use
            supplier_data = []
            for row in results:
                supplier_data.append({
                    'supplier_name': row[0],
                    'total_returns': row[1],
                    'total_items_sold': row[2],
                    'return_rate_percent': row[3] or 0.0,
                    'avg_refund_amount': row[4] or 0.0,
                    'total_refund_amount': row[5] or 0.0,
                    'pending_returns': row[6] or 0,
                    'approved_returns': row[7] or 0,
                    'rejected_returns': row[8] or 0
                })
            
            return supplier_data
            
        except mysql.connector.Error as e:
            print(f"Error getting supplier returns data: {e}")
            return []
        finally:
            conn.close()

    def _get_date_filter_for_period(self, time_period):
        """
        Convert time period string to SQL WHERE clause for date filtering.
        """
        date_filters = {
            "Last 7 Days": "WHERE r.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
            "Last 30 Days": "WHERE r.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
            "Last 90 Days": "WHERE r.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)",
            "Last Year": "WHERE r.created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR)",
            "All Time": ""
        }
        return date_filters.get(time_period, date_filters["Last 30 Days"])
