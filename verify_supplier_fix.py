"""
Quick test to verify the returns dashboard supplier chart data is working
"""
from database.db_connector import get_db_connection

def test_supplier_returns_data():
    """Test the supplier returns chart data query"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Test the exact query from the dashboard
        date_filter = "AND r.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
        
        cursor.execute(f"""
            SELECT p.ready_made_supplier as supplier, COUNT(*) as return_count
            FROM returns r
            JOIN products p ON r.product_id = p.id
            WHERE 1=1 {date_filter}
              AND p.ready_made_supplier IS NOT NULL 
              AND p.ready_made_supplier != ''
            GROUP BY p.ready_made_supplier
            ORDER BY return_count DESC
            LIMIT 10
        """)
        
        supplier_returns = cursor.fetchall()
        
        if len(supplier_returns) > 0:
            print("✅ Supplier returns data successfully retrieved!")
            print(f"📊 Found {len(supplier_returns)} suppliers with returns:")
            for item in supplier_returns:
                print(f"   • {item['supplier']}: {item['return_count']} returns")
            return True
        else:
            print("⚠️  No supplier returns data found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing supplier returns: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 Testing Returns Dashboard Supplier Chart Fix...")
    success = test_supplier_returns_data()
    if success:
        print("\n✅ Fix successful! The 'Returns by Supplier' chart should now display data.")
    else:
        print("\n❌ Issue detected. Please check the database setup.")
