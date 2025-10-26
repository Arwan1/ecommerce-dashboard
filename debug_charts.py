#!/usr/bin/env python3
"""
Debug script to check chart data structure for different time periods
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_connector import get_db_connection

def debug_chart_queries():
    """Debug the chart data queries for different time periods"""
    
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        print("🐛 Debugging Chart Data Queries")
        print("=" * 50)
        
        # Test different time period filters
        time_periods = ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "All Time"]
        
        def get_date_filter_sql(time_period):
            """Get SQL date filter based on selected time period"""
            if time_period == "All Time":
                return ""
            elif time_period == "Last 7 Days":
                return "AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
            elif time_period == "Last 30 Days":
                return "AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
            elif time_period == "Last 90 Days":
                return "AND created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)"
            elif time_period == "Last Year":
                return "AND created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR)"
            else:
                return ""
        
        for time_period in time_periods:
            print(f"\n📅 Testing: {time_period}")
            print("-" * 40)
            
            date_filter = get_date_filter_sql(time_period)
            print(f"   Date filter: {date_filter}")
            
            # Test the actual query used in the charts
            try:
                if time_period == "Last 7 Days":
                    # Daily data for last 7 days
                    query = f"""
                        SELECT 
                            DATE(created_at) as period,
                            COUNT(*) as orders, 
                            SUM(total_price) as revenue
                        FROM orders 
                        WHERE 1=1 {date_filter}
                        GROUP BY DATE(created_at)
                        ORDER BY DATE(created_at)
                    """
                elif time_period == "Last 30 Days":
                    # Daily data for last 30 days
                    query = f"""
                        SELECT 
                            DATE(created_at) as period,
                            COUNT(*) as orders, 
                            SUM(total_price) as revenue
                        FROM orders 
                        WHERE 1=1 {date_filter}
                        GROUP BY DATE(created_at)
                        ORDER BY DATE(created_at)
                    """
                else:
                    # Monthly data for longer periods
                    query = f"""
                        SELECT 
                            CONCAT(YEAR(created_at), '-', LPAD(MONTH(created_at), 2, '0')) as period,
                            COUNT(*) as orders, 
                            SUM(total_price) as revenue
                        FROM orders 
                        WHERE 1=1 {date_filter}
                        GROUP BY YEAR(created_at), MONTH(created_at)
                        ORDER BY YEAR(created_at), MONTH(created_at)
                    """
                
                print(f"   Query: {query.strip()}")
                cursor.execute(query)
                results = cursor.fetchall()
                
                print(f"   ✅ Results: {len(results)} rows")
                if results:
                    print(f"   📊 Sample data:")
                    for i, row in enumerate(results[:3]):  # Show first 3 rows
                        print(f"      {i+1}. Period: {row['period']}, Orders: {row['orders']}, Revenue: ${row['revenue'] or 0:.2f}")
                    if len(results) > 3:
                        print(f"      ... and {len(results) - 3} more rows")
                else:
                    print("   ⚠️  No data returned!")
                    
            except Exception as e:
                print(f"   ❌ Query error: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n✅ Chart data debugging completed!")
        
    except Exception as e:
        print(f"❌ Debugging error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    debug_chart_queries()
