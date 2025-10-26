from database.db_connector import get_db_connection

conn = get_db_connection()
if conn:
    cursor = conn.cursor(dictionary=True)
    print('=== TESTING FIXED SUPPLIER RETURNS QUERY ===')
    cursor.execute("""
        SELECT p.ready_made_supplier as supplier, COUNT(*) as return_count
        FROM returns r
        JOIN products p ON r.product_id = p.id
        WHERE p.ready_made_supplier IS NOT NULL 
          AND p.ready_made_supplier != ''
        GROUP BY p.ready_made_supplier
        ORDER BY return_count DESC
        LIMIT 10
    """)
    results = cursor.fetchall()
    print(f'Found {len(results)} supplier groups:')
    for row in results:
        print(f'  {row["supplier"]}: {row["return_count"]} returns')
    conn.close()
else:
    print('Failed to connect to database')
