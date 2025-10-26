import mysql.connector
from database.db_connector import get_db_connection

def update_database_schema():
    """
    Updates the database schema to add customer_name to orders table.
    """
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        print("🔧 Updating database schema...")
        
        # Check if customer_name column already exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'orders' 
            AND column_name = 'customer_name'
            AND table_schema = DATABASE()
        """)
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            print("   Adding customer_name column to orders table...")
            cursor.execute("""
                ALTER TABLE orders 
                ADD COLUMN customer_name VARCHAR(100) NOT NULL DEFAULT 'Unknown Customer'
            """)
            
            print("   Making user_id nullable (for employee who processed order)...")
            cursor.execute("""
                ALTER TABLE orders 
                MODIFY COLUMN user_id INT NULL
            """)
            
            conn.commit()
            print("✅ Database schema updated successfully!")
        else:
            print("✅ Database schema is already up to date!")
        
        # Update existing orders with random customer names if they don't have them
        cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_name = 'Unknown Customer'")
        orders_to_update = cursor.fetchone()[0]
        
        if orders_to_update > 0:
            print(f"   Updating {orders_to_update} orders with random customer names...")
            
            # List of random customer names
            customer_names = [
                "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis",
                "David Wilson", "Jessica Garcia", "Christopher Miller", "Ashley Anderson",
                "Matthew Taylor", "Amanda Thomas", "Joshua Jackson", "Stephanie White",
                "Andrew Harris", "Nicole Martin", "Daniel Thompson", "Melissa Garcia",
                "James Rodriguez", "Rebecca Lewis", "Robert Lee", "Laura Walker",
                "Kevin Hall", "Jennifer Allen", "Brian Young", "Lisa King",
                "William Wright", "Kimberly Lopez", "Mark Hill", "Michelle Scott",
                "Steven Green", "Angela Adams", "Kenneth Baker", "Cynthia Nelson",
                "Paul Carter", "Carol Mitchell", "Edward Perez", "Janet Roberts",
                "Jason Turner", "Helen Phillips", "Ryan Campbell", "Sandra Parker"
            ]
            
            cursor.execute("SELECT id FROM orders WHERE customer_name = 'Unknown Customer'")
            order_ids = [row[0] for row in cursor.fetchall()]
            
            import random
            for order_id in order_ids:
                random_name = random.choice(customer_names)
                cursor.execute("""
                    UPDATE orders 
                    SET customer_name = %s 
                    WHERE id = %s
                """, (random_name, order_id))
            
            conn.commit()
            print(f"✅ Updated {len(order_ids)} orders with random customer names!")
        
    except mysql.connector.Error as e:
        print(f"❌ Error updating database schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Database Schema Update Tool")
    print("=" * 50)
    update_database_schema()
