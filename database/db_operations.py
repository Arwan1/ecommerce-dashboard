import mysql.connector
from database.db_connector import get_db_connection

class DBOperations:
    """
    all the methods for database CRUD (Create, Read, Update, Delete) 
    class interfaces directly with the MySQL database
    """

    # --- User Operations ---
    def get_user(self, username):
        """Retrieves a user's data from the database by username."""
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            return user
        finally:
            conn.close()

    def add_user(self, username, password, role, public_key):
        """Adds a new user to the database"""
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, role, public_key) VALUES (%s, %s, %s, %s)",
                           (username, password, role, public_key))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error adding user: {err}")
            return False
        finally:
            conn.close()

    # --- Order Operations ---
    def get_all_orders(self):
        """Retrieves all orders from the database"""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM orders ORDER BY order_date DESC")
            orders = cursor.fetchall()
            return orders
        finally:
            conn.close()

    def add_order(self, order_data):
        """Adds a new order to the database."""
        # Implementation would insert into the 'orders' table
        pass

    # --- Inventory & Product Operations ---
    def get_low_stock_items(self, threshold=10):
        """Retrieves items from inventory that are below a certain stock threshold."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM inventory WHERE quantity < %s", (threshold,))
            low_stock_items = cursor.fetchall()
            return low_stock_items
        finally:
            conn.close()

    def update_inventory_quantity(self, product_id, quantity_change):
        """Updates the quantity of a product in the inventory. Use negative for deduction."""
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE inventory SET quantity = quantity + %s WHERE product_id = %s",
                           (quantity_change, product_id))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error updating inventory: {err}")
            return False
        finally:
            conn.close()

    # --- Return Claims Operations ---
    def add_return_scan(self, order_id, timestamp):
        """Stores the timestamp of when a return was scanned."""
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO return_claims (order_id, scan_timestamp) VALUES (%s, %s)",
                           (order_id, timestamp))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error adding return scan: {err}")
            return False
        finally:
            conn.close()

    def get_return_scan_timestamp(self, order_id):
        """Retrieves the scan timestamp for a given return order ID."""
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT scan_timestamp FROM return_claims WHERE order_id = %s", (order_id,))
            result = cursor.fetchone()
            return result['scan_timestamp'] if result else None
        finally:
            conn.close()
            
    # --- Data for Analytics ---
    def get_sales_data(self, start_date, end_date):
        """Retrieves sales data within a specific date range for analysis."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            # This query would join orders and order_items tables
            query = """
                SELECT o.order_date, oi.product_id, p.product_name, oi.quantity, oi.price
                FROM orders o
                JOIN order_items oi ON o.order_id = oi.order_id
                JOIN products p ON oi.product_id = p.product_id
                WHERE o.order_date BETWEEN %s AND %s
            """
            cursor.execute(query, (start_date, end_date))
            sales_data = cursor.fetchall()
            return sales_data
        finally:
            conn.close()
