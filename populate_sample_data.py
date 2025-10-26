import mysql.connector
from database.db_connector import get_db_connection
import random
from datetime import datetime, timedelta
import hashlib

def populate_sample_data():
    """
    Populates the database with sample data for the past year with an upward trend.
    """
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("🗑️ Clearing existing sample data...")
        cursor.execute("DELETE FROM return_claims")
        cursor.execute("DELETE FROM order_items") 
        cursor.execute("DELETE FROM orders WHERE id > 0")  # Keep any existing orders you want
        cursor.execute("DELETE FROM products WHERE id > 0")  # Keep any existing products you want
        cursor.execute("DELETE FROM users WHERE id > 1")  # Keep the first user (admin)
        
        # Insert sample products
        print("📦 Creating sample products...")
        products = [
            ("Wireless Headphones", "High-quality wireless headphones with noise cancellation", 99.99, 50),
            ("Smartphone Case", "Protective case for smartphones", 19.99, 100),
            ("Laptop Stand", "Adjustable laptop stand for better ergonomics", 49.99, 30),
            ("USB Cable", "High-speed USB-C cable", 12.99, 200),
            ("Bluetooth Speaker", "Portable Bluetooth speaker with excellent sound", 79.99, 40),
            ("Wireless Mouse", "Ergonomic wireless mouse", 29.99, 75),
            ("Power Bank", "10000mAh portable power bank", 39.99, 60),
            ("Screen Protector", "Tempered glass screen protector", 9.99, 150),
            ("Desk Lamp", "LED desk lamp with adjustable brightness", 59.99, 25),
            ("Webcam", "HD webcam for video calls", 89.99, 35)
        ]
        
        product_ids = []
        for product in products:
            cursor.execute("""
                INSERT INTO products (name, description, price, stock) 
                VALUES (%s, %s, %s, %s)
            """, product)
            product_ids.append(cursor.lastrowid)
        
        # Insert sample users (employees/admins only)
        print("👥 Creating sample employees...")
        users = [
            ("john_manager", "password123", "john.manager@company.com", "admin"),
            ("jane_sales", "password123", "jane.sales@company.com", "user"),
            ("mike_warehouse", "password123", "mike.warehouse@company.com", "user"),
            ("sarah_support", "password123", "sarah.support@company.com", "user")
        ]
        
        user_ids = []
        for user in users:
            # Hash the password (simple hash for demo)
            hashed_password = hashlib.sha256(user[1].encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO users (username, password, email, role) 
                VALUES (%s, %s, %s, %s)
            """, (user[0], hashed_password, user[2], user[3]))
            user_ids.append(cursor.lastrowid)
        
        # Random customer names for orders
        customer_names = [
            "Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson", 
            "Emma Brown", "Frank Miller", "Grace Lee", "Henry Taylor",
            "Isabella Martinez", "Jack Anderson", "Karen Thompson", "Liam Garcia",
            "Mia Rodriguez", "Noah Williams", "Olivia Jones", "Paul Davis",
            "Quinn Wilson", "Rachel Moore", "Sam Jackson", "Tina White",
            "Uma Patel", "Victor Chen", "Wendy Kumar", "Xavier Lopez",
            "Yara Hassan", "Zoe Martin", "Aaron Scott", "Bella Clark",
            "Carlos Rivera", "Diana Kim", "Ethan Park", "Fiona Walsh"
        ]
        
        # Generate orders for the past year with upward trend
        print("📈 Generating orders with upward trend...")
        
        start_date = datetime.now() - timedelta(days=365)
        current_date = start_date
        order_id_list = []
        
        # Base number of orders per week (will increase over time)
        base_orders_per_week = 5
        
        week_count = 0
        while current_date <= datetime.now():
            # Calculate trend multiplier (gradual increase over the year)
            progress = week_count / 52  # 52 weeks in a year
            trend_multiplier = 1 + (progress * 1.5)  # 150% increase over the year
            
            # Orders for this week
            orders_this_week = int(base_orders_per_week * trend_multiplier) + random.randint(-2, 3)
            orders_this_week = max(1, orders_this_week)  # At least 1 order per week
            
            for _ in range(orders_this_week):
                # Random date within this week
                order_date = current_date + timedelta(days=random.randint(0, 6))
                if order_date > datetime.now():
                    break
                    
                # Random customer name
                customer_name = random.choice(customer_names)
                
                # Random number of items (1-4 items per order)
                items_count = random.randint(1, 4)
                total_price = 0
                
                # Calculate total price first
                order_items = []
                for _ in range(items_count):
                    product_id = random.choice(product_ids)
                    quantity = random.randint(1, 3)
                    # Get product price
                    cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
                    price = cursor.fetchone()[0]
                    total_price += price * quantity
                    order_items.append((product_id, quantity, price))
                
                # Insert order with customer name and realistic status
                # Determine status based on order age
                days_old = (datetime.now() - order_date).days
                
                if days_old <= 2:
                    # Recent orders (0-2 days) - mix of preparing/dispatched
                    status = random.choices(['Preparing', 'Dispatched'], weights=[70, 30])[0]
                elif days_old <= 7:
                    # Orders from last week (3-7 days) - mostly dispatched, some delivered
                    status = random.choices(['Dispatched', 'Delivered'], weights=[60, 40])[0]
                else:
                    # Older orders (8+ days) - mostly delivered, some dispatched
                    status = random.choices(['Dispatched', 'Delivered'], weights=[20, 80])[0]
                
                cursor.execute("""
                    INSERT INTO orders (customer_name, total_price, status, created_at) 
                    VALUES (%s, %s, %s, %s)
                """, (customer_name, total_price, status, order_date))
                
                order_id = cursor.lastrowid
                order_id_list.append(order_id)
                
                # Insert order items
                for product_id, quantity, price in order_items:
                    cursor.execute("""
                        INSERT INTO order_items (order_id, product_id, quantity, price) 
                        VALUES (%s, %s, %s, %s)
                    """, (order_id, product_id, quantity, price))
            
            current_date += timedelta(weeks=1)
            week_count += 1
        
        # Generate some return claims (about 5% of orders)
        print("🔄 Generating return claims...")
        sample_orders = random.sample(order_id_list, min(len(order_id_list) // 20, len(order_id_list)))  # 5% return rate
        
        for order_id in sample_orders:
            # Random return date (within 30 days of order)
            cursor.execute("SELECT created_at FROM orders WHERE id = %s", (order_id,))
            order_date = cursor.fetchone()[0]
            return_date = order_date + timedelta(days=random.randint(1, 30))
            
            if return_date <= datetime.now():
                cursor.execute("""
                    INSERT INTO return_claims (order_id, scan_timestamp) 
                    VALUES (%s, %s)
                """, (order_id, return_date))
        
        conn.commit()
        print("✅ Sample data populated successfully!")
        
        # Print summary
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total_price) FROM orders")
        total_revenue = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM return_claims")
        total_returns = cursor.fetchone()[0]
        
        print(f"""
📊 Data Summary:
   • Total Orders: {total_orders}
   • Total Revenue: ${total_revenue:,.2f}
   • Return Claims: {total_returns}
   • Products: {len(products)}
   • Customers: {len(users)}
        """)
        
    except mysql.connector.Error as e:
        print(f"❌ Error populating data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting database population...")
    populate_sample_data()
    print("🎉 Database population complete!")
