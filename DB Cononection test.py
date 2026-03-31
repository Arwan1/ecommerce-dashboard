#!/usr/bin/env python3

# Simple test script
from database.db_connector import get_db_connection

print("Testing data format...")

try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT p.ready_made_supplier as supplier, COUNT(*) as return_count
        FROM returns r
        JOIN products p ON r.product_id = p.id
        WHERE p.ready_made_supplier IS NOT NULL 
          AND p.ready_made_supplier != ''
        GROUP BY p.ready_made_supplier
        ORDER BY return_count DESC
        LIMIT 3
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"Results: {results}")
    print(f"Type: {type(results)}")
    
    if results:
        first_item = results[0]
        print(f"First item: {first_item}")
        print(f"First item type: {type(first_item)}")
        
        # Test the exact access pattern from the chart
        try:
            supplier = first_item['supplier']
            count = first_item['return_count'] 
            print(f"Accessing data works: supplier={supplier}, count={count}")
        except Exception as e:
            print(f"Error accessing data: {e}")
            print(f"Available keys: {list(first_item.keys()) if hasattr(first_item, 'keys') else 'No keys method'}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Test complete.")
