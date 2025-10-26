#!/usr/bin/env python3
"""
Test the fixed chart queries for longer time periods
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_connector import get_db_connection

def test_fixed_queries():
    """Test the fixed queries for longer time periods"""
    
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        print("🔧 Testing Fixed Chart Queries")
        print("=" * 50)
        
        # Test the problematic time periods
        time_periods = ["Last 90 Days", "Last Year", "All Time"]
        
        def get_date_filter_sql(time_period):
            """Get SQL date filter based on selected time period"""
            if time_period == "All Time":
                return ""
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
            
            # Test the fixed query approach
            try:
                query = f"""
                    SELECT 
                        YEAR(created_at) as year,
                        MONTH(created_at) as month,
                        COUNT(*) as orders, 
                        SUM(total_price) as revenue
                    FROM orders 
                    WHERE 1=1 {date_filter}
                    GROUP BY YEAR(created_at), MONTH(created_at)
                    ORDER BY YEAR(created_at), MONTH(created_at)
                """
                
                print(f"   Query: {query.strip()}")
                cursor.execute(query)
                raw_results = cursor.fetchall()
                
                # Format the results like the dashboard does
                formatted_results = []
                for row in raw_results:
                    formatted_row = {
                        'period': f"{row['year']}-{row['month']:02d}",
                        'orders': row['orders'],
                        'revenue': row['revenue']
                    }
                    formatted_results.append(formatted_row)
                
                print(f"   ✅ Results: {len(formatted_results)} months")
                if formatted_results:
                    print(f"   📊 Sample data:")
                    for i, row in enumerate(formatted_results[:3]):  # Show first 3 rows
                        print(f"      {i+1}. Period: {row['period']}, Orders: {row['orders']}, Revenue: ${row['revenue'] or 0:.2f}")
                    if len(formatted_results) > 3:
                        print(f"      ... and {len(formatted_results) - 3} more rows")
                else:
                    print("   ⚠️  No data returned!")
                    
            except Exception as e:
                print(f"   ❌ Query error: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n✅ Fixed query testing completed!")
        
    except Exception as e:
        print(f"❌ Testing error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    test_fixed_queries()
