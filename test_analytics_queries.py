#!/usr/bin/env python3
"""
Test analytics queries independently to troubleshoot issues
"""

from database.db_connector import get_db_connection
import mysql.connector

def test_analytics_queries():
    """Test each analytics query individually"""
    print("🔍 Testing Analytics Queries")
    print("=" * 50)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Test 1: Basic order count
        print("📊 Test 1: Basic order count")
        try:
            cursor.execute("SELECT COUNT(*) as total FROM orders")
            result = cursor.fetchone()
            print(f"   ✅ Total orders: {result['total']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Monthly sales (simplified)
        print("\n📊 Test 2: Monthly sales (simplified)")
        try:
            cursor.execute("""
                SELECT 
                    YEAR(created_at) as year,
                    MONTH(created_at) as month,
                    COUNT(*) as orders,
                    SUM(total_price) as revenue
                FROM orders 
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                GROUP BY YEAR(created_at), MONTH(created_at)
                ORDER BY year, month
            """)
            results = cursor.fetchall()
            print(f"   ✅ Monthly data: {len(results)} months")
            for row in results[:3]:
                print(f"      {row['year']}-{row['month']:02d}: {row['orders']} orders, ${row['revenue']:.2f}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Top products (simplified)
        print("\n📊 Test 3: Top products")
        try:
            cursor.execute("""
                SELECT p.name, COUNT(oi.id) as order_count
                FROM products p
                LEFT JOIN order_items oi ON p.id = oi.product_id
                GROUP BY p.id, p.name
                ORDER BY order_count DESC
                LIMIT 5
            """)
            results = cursor.fetchall()
            print(f"   ✅ Product data: {len(results)} products")
            for row in results:
                print(f"      {row['name']}: {row['order_count']} orders")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Order status (simple version)
        print("\n📊 Test 4: Order status distribution")
        try:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) as processing,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) AND created_at < DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) as shipped,
                    COUNT(CASE WHEN created_at < DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as delivered
                FROM orders
            """)
            result = cursor.fetchone()
            print(f"   ✅ Status distribution:")
            print(f"      Processing: {result['processing']}")
            print(f"      Shipped: {result['shipped']}")
            print(f"      Delivered: {result['delivered']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 5: Recent orders
        print("\n📊 Test 5: Recent orders")
        try:
            cursor.execute("""
                SELECT created_at, customer_name, total_price
                FROM orders 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            results = cursor.fetchall()
            print(f"   ✅ Recent orders: {len(results)} orders")
            for row in results:
                print(f"      {row['customer_name']}: ${row['total_price']:.2f} on {row['created_at']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    finally:
        conn.close()
    
    print("\n🎯 Diagnosis complete!")

if __name__ == "__main__":
    test_analytics_queries()
