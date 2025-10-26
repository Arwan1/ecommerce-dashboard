#!/usr/bin/env python3
"""
Standalone test for the comprehensive supplier analysis functionality
"""
import sys
sys.path.append('.')

def test_supplier_analysis():
    """Test the supplier analysis queries directly"""
    print("🧪 Testing Comprehensive Supplier Analysis...")
    
    try:
        from database.db_connector import get_db_connection
        
        conn = get_db_connection()
        if not conn:
            print("❌ Database connection failed")
            return
        
        cursor = conn.cursor()
        
        # Test finished products suppliers
        print("\n📦 Testing Finished Products Suppliers:")
        finished_query = """
            SELECT 
                p.ready_made_supplier as supplier_name,
                'Finished Products' as supplier_type,
                COUNT(DISTINCT p.id) as product_count,
                COUNT(DISTINCT oi.id) as total_ordered,
                COUNT(DISTINCT r.id) as total_returned,
                ROUND((COUNT(DISTINCT r.id) * 100.0 / NULLIF(COUNT(DISTINCT oi.id), 0)), 2) as return_percentage,
                ROUND(AVG(oi.quantity * oi.price), 2) as avg_order_value,
                COALESCE(SUM(r.refund_amount), 0) as total_refunded
            FROM products p
            LEFT JOIN order_items oi ON oi.product_id = p.id
            LEFT JOIN returns r ON r.product_id = p.id
            WHERE p.ready_made_supplier IS NOT NULL 
              AND p.ready_made_supplier != ''
              AND p.ready_made_supplier != 'NULL'
              AND p.is_ready_made = 1
            GROUP BY p.ready_made_supplier
            HAVING COUNT(DISTINCT oi.id) > 0
            ORDER BY return_percentage DESC
            LIMIT 5
        """
        
        cursor.execute(finished_query)
        finished_results = cursor.fetchall()
        
        print(f"Found {len(finished_results)} finished product suppliers:")
        for row in finished_results[:3]:
            supplier = row[0]
            products = row[2]
            ordered = row[3]
            returned = row[4]
            return_pct = row[5] if row[5] else 0.0
            refunded = row[7]
            print(f"  • {supplier}: {return_pct:.1f}% return rate ({returned}/{ordered} items) - ${refunded:.2f} refunded")
        
        # Test raw materials suppliers
        print("\n🏭 Testing Raw Materials Suppliers:")
        raw_query = """
            SELECT 
                p.ready_made_supplier as supplier_name,
                'Raw Materials' as supplier_type,
                COUNT(DISTINCT p.id) as product_count,
                COUNT(DISTINCT oi.id) as total_ordered,
                COUNT(DISTINCT r.id) as total_returned,
                ROUND((COUNT(DISTINCT r.id) * 100.0 / NULLIF(COUNT(DISTINCT oi.id), 0)), 2) as return_percentage,
                ROUND(AVG(oi.quantity * oi.price), 2) as avg_order_value,
                COALESCE(SUM(r.refund_amount), 0) as total_refunded
            FROM products p
            LEFT JOIN order_items oi ON oi.product_id = p.id
            LEFT JOIN returns r ON r.product_id = p.id
            WHERE p.ready_made_supplier IS NOT NULL 
              AND p.ready_made_supplier != ''
              AND p.ready_made_supplier != 'NULL'
              AND p.is_ready_made = 0
            GROUP BY p.ready_made_supplier
            HAVING COUNT(DISTINCT oi.id) > 0
            ORDER BY return_percentage DESC
            LIMIT 5
        """
        
        cursor.execute(raw_query)
        raw_results = cursor.fetchall()
        
        print(f"Found {len(raw_results)} raw material suppliers:")
        for row in raw_results[:3]:
            supplier = row[0]
            products = row[2]
            ordered = row[3]
            returned = row[4]
            return_pct = row[5] if row[5] else 0.0
            refunded = row[7]
            print(f"  • {supplier}: {return_pct:.1f}% return rate ({returned}/{ordered} items) - ${refunded:.2f} refunded")
        
        # Calculate overall statistics
        all_suppliers = finished_results + raw_results
        if all_suppliers:
            total_ordered = sum(row[3] for row in all_suppliers)
            total_returned = sum(row[4] for row in all_suppliers)
            total_refunded = sum(row[7] for row in all_suppliers)
            overall_return_rate = (total_returned / total_ordered * 100) if total_ordered > 0 else 0
            
            print(f"\n📊 OVERALL STATISTICS:")
            print(f"  • Total suppliers: {len(all_suppliers)}")
            print(f"  • Overall return rate: {overall_return_rate:.1f}%")
            print(f"  • Total items ordered: {total_ordered:,}")
            print(f"  • Total items returned: {total_returned:,}")
            print(f"  • Total refunded: ${total_refunded:,.2f}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Supplier analysis test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_supplier_analysis()
