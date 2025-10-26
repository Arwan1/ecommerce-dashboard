#!/usr/bin/env python3

"""
Isolated test of the returns dashboard chart creation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_supplier_query():
    """Test just the supplier query part"""
    from database.db_connector import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test the exact query from the dashboard
        supplier_query = f"""
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
        
        print("Testing supplier query...")
        print(f"Query: {supplier_query}")
        cursor.execute(supplier_query)
        supplier_returns = cursor.fetchall()
        print(f"✅ Found {len(supplier_returns)} supplier records")
        for item in supplier_returns:
            print(f"   - {item}")
            
        cursor.close()
        conn.close()
        return supplier_returns
        
    except Exception as e:
        print(f"❌ Error in supplier returns query: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_chart_data_method():
    """Test the chart data method directly"""
    print("\n" + "="*50)
    print("Testing get_returns_chart_data method...")
    
    try:
        # Import fresh
        from gui.returns_dashboard import ReturnsDashboard
        import tkinter as tk
        
        # Create minimal instance
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        dashboard = ReturnsDashboard(root)
        
        # Call the method directly
        chart_data = dashboard.get_returns_chart_data()
        
        print("Chart data keys:", list(chart_data.keys()))
        
        if 'supplier_returns' in chart_data:
            supplier_data = chart_data['supplier_returns']
            print(f"Supplier returns data: {len(supplier_data)} items")
            for item in supplier_data:
                print(f"   - {item}")
        else:
            print("❌ No supplier_returns in chart data")
            
        root.destroy()
        
    except Exception as e:
        print(f"❌ Error testing chart data method: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Returns Dashboard Supplier Query Issue")
    print("="*60)
    
    # Test 1: Direct query
    print("Test 1: Direct database query")
    test_supplier_query()
    
    # Test 2: Through dashboard method
    print("\nTest 2: Through dashboard method")
    test_chart_data_method()
    
    print("\n✅ Test complete")
