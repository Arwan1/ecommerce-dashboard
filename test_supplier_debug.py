#!/usr/bin/env python3

from database.db_connector import get_db_connection

def test_chart_data_method():
    """Test the get_returns_chart_data method directly"""
    
    print("Testing get_returns_chart_data method...")
    
    # Create a minimal class to test the method
    class TestReturnsDashboard:
        def get_date_filter_sql(self, time_period):
            """Simple date filter for testing"""
            return ""
            
        def get_returns_chart_data(self, time_period):
            """Get data for returns charts - copied from actual dashboard"""
            print(f"🔍 get_returns_chart_data called with time_period: {time_period}")
            conn = get_db_connection()
            if not conn:
                return {}
            
            try:
                cursor = conn.cursor(dictionary=True)
                date_filter = self.get_date_filter_sql(time_period)
                print(f"🔍 Date filter: {date_filter}")
                
                # Initialize empty data
                returns_trend = []
                most_returned_items = []
                return_reasons = []
                
                # 3. Supplier return analysis (bottom-left bar chart)
                try:
                    print("🔍 Starting supplier returns query...")
                    supplier_query = f"""
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
                    print(f"🔍 Query: {supplier_query}")
                    cursor.execute(supplier_query)
                    supplier_returns = cursor.fetchall()
                    print(f"✅ Found {len(supplier_returns)} supplier records")
                    print(f"🔍 Data type: {type(supplier_returns)}")
                    if supplier_returns:
                        print(f"🔍 First item type: {type(supplier_returns[0])}")
                        print(f"🔍 First item: {supplier_returns[0]}")
                        print(f"🔍 Has keys method: {hasattr(supplier_returns[0], 'keys')}")
                    for item in supplier_returns:
                        print(f"   - {item}")
                except Exception as e:
                    print(f"❌ Error in supplier returns query: {e}")
                    import traceback
                    traceback.print_exc()
                    supplier_returns = []
                
                print(f"🔍 Returning chart data with supplier_returns: {len(supplier_returns) if supplier_returns else 0} items")
                if supplier_returns:
                    print(f"🔍 First supplier item before return: {supplier_returns[0]}")
                
                return {
                    'returns_trend': returns_trend,
                    'most_returned_items': most_returned_items,
                    'supplier_returns': supplier_returns,
                    'return_reasons': return_reasons,
                    'time_period': time_period
                }
            except Exception as e:
                print(f"Error getting chart data: {e}")
                return {}
            finally:
                conn.close()
    
    # Test the method
    dashboard = TestReturnsDashboard()
    chart_data = dashboard.get_returns_chart_data("Last 30 Days")
    
    print(f"\n📊 Final chart data keys: {list(chart_data.keys())}")
    supplier_data = chart_data.get('supplier_returns', [])
    print(f"📊 Supplier data in final result: {supplier_data}")
    
    # Test the exact chart condition
    condition = chart_data.get('supplier_returns') and len(chart_data['supplier_returns']) > 0
    print(f"📊 Chart display condition result: {condition}")

if __name__ == "__main__":
    test_chart_data_method()
