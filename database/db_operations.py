try:
    import mysql.connector
except ImportError:
    print("❌ mysql-connector-python not found. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql-connector-python"])
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

    def add_user(self, username, password, email, role="user"):
        """Adds a new user to the database with email"""
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
                           (username, password, email, role))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error adding user: {err}")
            return False
        finally:
            conn.close()

    def get_all_users(self):
        """Retrieves all users from the database"""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()
            return users
        finally:
            conn.close()

    def update_user(self, user_id, username=None, email=None, password=None, role=None):
        """Updates user information"""
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            
            # Build dynamic update query
            fields = []
            values = []
            
            if username is not None:
                fields.append("username = %s")
                values.append(username)
            if email is not None:
                fields.append("email = %s")
                values.append(email)
            if password is not None:
                fields.append("password = %s")
                values.append(password)
            if role is not None:
                fields.append("role = %s")
                values.append(role)
            
            if not fields:
                return False
                
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
            
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"Error updating user: {err}")
            return False
        finally:
            conn.close()

    def delete_user(self, user_id):
        """Deletes a user from the database"""
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"Error deleting user: {err}")
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
            cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
            orders = cursor.fetchall()
            return orders
        finally:
            conn.close()

    def add_order(self, order_data):
        """Adds a new order to the database."""
        # Implementation would insert into the 'orders' table
        pass

    def delete_order_with_inventory_restore(self, order_id):
        """
        Deletes an order and restores inventory for non-dispatched orders.
        Returns True if successful, False otherwise.
        """
        conn = get_db_connection()
        if not conn: 
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check order status first
            cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
            result = cursor.fetchone()
            if not result:
                return False
                
            order_status = result[0]
            non_deletable_statuses = ['Dispatched', 'Delivered']
            if order_status in non_deletable_statuses:
                return False
            
            # Get order items to restore inventory
            cursor.execute("""
                SELECT product_id, quantity 
                FROM order_items 
                WHERE order_id = %s
            """, (order_id,))
            order_items = cursor.fetchall()
            
            # Restore inventory for each item
            for product_id, quantity in order_items:
                cursor.execute("""
                    UPDATE products 
                    SET stock = stock + %s 
                    WHERE id = %s
                """, (quantity, product_id))
            
            # Delete order items first (foreign key constraint)
            cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            
            # Delete the order
            cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error deleting order: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

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
            
    # --- Additional User Operations ---
    def get_user_by_id(self, user_id):
        """Retrieves a user's data from the database by user ID."""
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            return user
        finally:
            conn.close()
    
    # --- Order Items Operations ---
    def get_order_items(self, order_id):
        """Retrieves all items for a specific order."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT oi.*, p.name as product_name 
                FROM order_items oi
                LEFT JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """
            cursor.execute(query, (order_id,))
            items = cursor.fetchall()
            return items
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
                SELECT o.created_at, oi.product_id, p.name as product_name, oi.quantity, oi.price
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                WHERE o.created_at BETWEEN %s AND %s
            """
            cursor.execute(query, (start_date, end_date))
            sales_data = cursor.fetchall()
            return sales_data
        finally:
            conn.close()

    # --- Inventory Management Operations ---
    def get_products_data(self):
        """Get all products with inventory information."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, price, stock, reorder_level FROM products")
            products = cursor.fetchall()
            return products
        finally:
            conn.close()

    def get_raw_materials_data(self):
        """Get all raw materials with inventory information."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, quantity, unit, reorder_level, supplier_rating FROM raw_materials")
            materials = cursor.fetchall()
            return materials
        finally:
            conn.close()

    def get_low_stock_products(self):
        """Get products with stock below reorder level."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name, stock, reorder_level FROM products WHERE stock <= reorder_level")
            low_products = cursor.fetchall()
            return low_products
        finally:
            conn.close()

    def get_low_stock_materials(self):
        """Get raw materials with quantity below reorder level."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name, quantity, unit, reorder_level FROM raw_materials WHERE quantity <= reorder_level")
            low_materials = cursor.fetchall()
            return low_materials
        finally:
            conn.close()
