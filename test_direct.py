#!/usr/bin/env python3

"""
Direct test of supplier data functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_supplier_data_direct():
    """Test supplier data retrieval directly"""
    print("=== TESTING SUPPLIER DATA FUNCTIONALITY ===")
    
    from database.db_connector import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Test the exact query from the dashboard
        supplier_query = """
            SELECT p.ready_made_supplier as supplier, COUNT(*) as return_count
            FROM returns r
            JOIN products p ON r.product_id = p.id
            WHERE 1=1 
              AND p.ready_made_supplier IS NOT NULL 
              AND p.ready_made_supplier != ''
            GROUP BY p.ready_made_supplier
            ORDER BY return_count DESC
            LIMIT 10
        """
        
        print("Executing supplier query...")
        cursor.execute(supplier_query)
        supplier_returns = cursor.fetchall()
        
        print(f"✅ Query successful! Found {len(supplier_returns)} suppliers")
        print(f"📊 Data type: {type(supplier_returns)}")
        
        if supplier_returns:
            print(f"📊 First item: {supplier_returns[0]}")
            print(f"📊 First item type: {type(supplier_returns[0])}")
            
            # Test the chart access pattern
            try:
                first_supplier = supplier_returns[0]['supplier']
                first_count = supplier_returns[0]['return_count']
                print(f"✅ Data access works: {first_supplier} = {first_count} returns")
            except Exception as e:
                print(f"❌ Data access failed: {e}")
                print(f"Available keys: {list(supplier_returns[0].keys())}")
        
        # Test the chart condition
        chart_data = {'supplier_returns': supplier_returns}
        condition = chart_data.get('supplier_returns') and len(chart_data['supplier_returns']) > 0
        print(f"📊 Chart condition result: {condition}")
        
        # Test chart data processing
        if condition:
            suppliers = [item['supplier'][:15] + '...' if len(item['supplier']) > 15 else item['supplier'] 
                        for item in chart_data['supplier_returns']]
            counts = [item['return_count'] for item in chart_data['supplier_returns']]
            print(f"📊 Chart suppliers: {suppliers}")
            print(f"📊 Chart counts: {counts}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_supplier_data_direct()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
