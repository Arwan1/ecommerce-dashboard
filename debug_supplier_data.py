#!/usr/bin/env python3

"""
Test the actual data returned by get_returns_chart_data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_chart_data():
    """Test what get_returns_chart_data actually returns"""
    from database.db_connector import get_db_connection
    
    # Test direct query first
    print("=== DIRECT QUERY TEST ===")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        supplier_query = """
            SELECT p.ready_made_supplier as supplier, COUNT(*) as return_count
            FROM returns r
            JOIN products p ON r.product_id = p.id
            WHERE p.ready_made_supplier IS NOT NULL 
              AND p.ready_made_supplier != ''
            GROUP BY p.ready_made_supplier
            ORDER BY return_count DESC
            LIMIT 10
        """
        
        cursor.execute(supplier_query)
        results = cursor.fetchall()
        print(f"Query results type: {type(results)}")
        print(f"Results count: {len(results)}")
        if results:
            print(f"First item type: {type(results[0])}")
            print(f"First item: {results[0]}")
            print(f"First item keys: {list(results[0].keys()) if hasattr(results[0], 'keys') else 'No keys'}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Direct query error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== DASHBOARD METHOD TEST ===")
    # Test through the dashboard method
    try:
        # Import the dashboard method directly  
        import sys
        from gui.returns_dashboard import ReturnsDashboard
        
        # Create a minimal test instance without UI
        class TestDashboard:
            def get_date_filter_sql(self, time_period):
                # Simple implementation for testing
                return ""
                
            def get_returns_chart_data(self, time_period):
                from database.db_connector import get_db_connection
                
                conn = get_db_connection()
                if not conn:
                    return {}
                
                try:
                    cursor = conn.cursor(dictionary=True)
                    
                    # Supplier query
                    supplier_query = f"""
                        SELECT p.ready_made_supplier as supplier, COUNT(*) as return_count
                        FROM returns r
                        JOIN products p ON r.product_id = p.id
                        WHERE p.ready_made_supplier IS NOT NULL 
                          AND p.ready_made_supplier != ''
                        GROUP BY p.ready_made_supplier
                        ORDER BY return_count DESC
                        LIMIT 10
                    """
                    
                    cursor.execute(supplier_query)
                    supplier_returns = cursor.fetchall()
                    
                    print(f"Dashboard method - supplier_returns type: {type(supplier_returns)}")
                    print(f"Dashboard method - count: {len(supplier_returns)}")
                    if supplier_returns:
                        print(f"Dashboard method - first item: {supplier_returns[0]}")
                        print(f"Dashboard method - first item type: {type(supplier_returns[0])}")
                    
                    return {
                        'supplier_returns': supplier_returns,
                    }
                    
                except Exception as e:
                    print(f"Dashboard method error: {e}")
                    import traceback
                    traceback.print_exc()
                    return {}
                finally:
                    conn.close()
        
        test_dashboard = TestDashboard()
        chart_data = test_dashboard.get_returns_chart_data("Last 30 Days")
        
        print(f"Chart data keys: {list(chart_data.keys())}")
        supplier_data = chart_data.get('supplier_returns', [])
        print(f"Supplier data: {supplier_data}")
        
        # Test the exact condition from the chart code
        condition_result = chart_data.get('supplier_returns') and len(chart_data['supplier_returns']) > 0
        print(f"Chart condition result: {condition_result}")
        
    except Exception as e:
        print(f"Dashboard method test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chart_data()
