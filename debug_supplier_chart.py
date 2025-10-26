"""
Debug the returns dashboard supplier chart data loading
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_connector import get_db_connection

def debug_returns_chart_data():
    """Debug the exact chart data loading process"""
    print("🔍 Debugging Returns Dashboard Chart Data Loading...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Test different time periods
        time_periods = [
            ("All Time", ""),
            ("Last 30 Days", "AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"),
            ("Last 90 Days", "AND created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)")
        ]
        
        for period_name, date_filter in time_periods:
            print(f"\n📊 Testing {period_name}:")
            print(f"   Date filter: {date_filter}")
            
            # Test supplier returns query
            try:
                if date_filter:
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
                else:
                    query = """
                        SELECT p.ready_made_supplier as supplier, COUNT(*) as return_count
                        FROM returns r
                        JOIN products p ON r.product_id = p.id
                        WHERE p.ready_made_supplier IS NOT NULL 
                          AND p.ready_made_supplier != ''
                        GROUP BY p.ready_made_supplier
                        ORDER BY return_count DESC
                        LIMIT 10
                    """
                
                cursor.execute(query)
                supplier_returns = cursor.fetchall()
                
                if supplier_returns:
                    print(f"   ✅ Found {len(supplier_returns)} suppliers:")
                    for item in supplier_returns:
                        print(f"      • {item['supplier']}: {item['return_count']} returns")
                else:
                    print("   ⚠️  No supplier data found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Check if there are any returns at all
        print(f"\n📋 Checking overall returns data:")
        cursor.execute("SELECT COUNT(*) as total_returns FROM returns")
        total_returns = cursor.fetchone()['total_returns']
        print(f"   Total returns in database: {total_returns}")
        
        # Check products with supplier data
        cursor.execute("""
            SELECT COUNT(*) as products_with_suppliers 
            FROM products 
            WHERE ready_made_supplier IS NOT NULL AND ready_made_supplier != ''
        """)
        products_with_suppliers = cursor.fetchone()['products_with_suppliers']
        print(f"   Products with supplier data: {products_with_suppliers}")
        
        # Check returns linked to products with suppliers
        cursor.execute("""
            SELECT COUNT(*) as returns_with_suppliers
            FROM returns r
            JOIN products p ON r.product_id = p.id
            WHERE p.ready_made_supplier IS NOT NULL AND p.ready_made_supplier != ''
        """)
        returns_with_suppliers = cursor.fetchone()['returns_with_suppliers']
        print(f"   Returns linked to products with suppliers: {returns_with_suppliers}")
        
    except Exception as e:
        print(f"❌ Debugging error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_returns_chart_data()
