import mysql.connector
from database.db_connector import get_db_connection

def clear_sample_data():
    """
    Clears all sample data from the database while preserving the admin user and table structure.
    """
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        print("🗑️ Starting database cleanup...")
        
        # Disable foreign key checks temporarily to avoid constraint issues
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Clear all data from tables (in correct order to respect foreign keys)
        print("   Clearing return claims...")
        cursor.execute("DELETE FROM return_claims")
        
        print("   Clearing order items...")
        cursor.execute("DELETE FROM order_items")
        
        print("   Clearing orders...")
        cursor.execute("DELETE FROM orders")
        
        print("   Clearing products...")
        cursor.execute("DELETE FROM products")
        
        print("   Clearing sample users (keeping admin)...")
        # Keep the first user (usually admin) and remove the rest
        cursor.execute("DELETE FROM users WHERE id > 1")
        
        # Reset auto-increment counters to start fresh
        print("   Resetting auto-increment counters...")
        cursor.execute("ALTER TABLE return_claims AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE order_items AUTO_INCREMENT = 1") 
        cursor.execute("ALTER TABLE orders AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE products AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE users AUTO_INCREMENT = 2")  # Start from 2 to preserve admin
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        conn.commit()
        print("✅ Database cleared successfully!")
        
        # Show what remains
        cursor.execute("SELECT COUNT(*) FROM users")
        remaining_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        remaining_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products")
        remaining_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM return_claims")
        remaining_returns = cursor.fetchone()[0]
        
        print(f"""
📊 Database Status After Cleanup:
   • Users: {remaining_users} (admin user preserved)
   • Orders: {remaining_orders}
   • Products: {remaining_products}
   • Return Claims: {remaining_returns}
   
🎯 Database is now clean and ready for fresh data!
        """)
        
    except mysql.connector.Error as e:
        print(f"❌ Error clearing database: {e}")
        conn.rollback()
    finally:
        conn.close()

def confirm_and_clear():
    """
    Asks for confirmation before clearing the database.
    """
    print("⚠️  WARNING: This will delete ALL sample data from the database!")
    print("   • All orders and order items will be removed")
    print("   • All products will be removed") 
    print("   • All customer accounts will be removed (admin preserved)")
    print("   • All return claims will be removed")
    print("   • Only the database structure and admin user will remain")
    print()
    
    confirm = input("Are you sure you want to proceed? (yes/no): ").lower().strip()
    
    if confirm in ['yes', 'y']:
        clear_sample_data()
    elif confirm in ['no', 'n']:
        print("❌ Operation cancelled.")
    else:
        print("❌ Invalid input. Operation cancelled.")

if __name__ == "__main__":
    print("🧹 Database Cleanup Tool")
    print("=" * 50)
    confirm_and_clear()
