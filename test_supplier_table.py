#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from database.db_connector import get_db_connection

def test_supplier_table():
    """Test creating the supplier table directly"""
    print("🧪 Testing direct supplier table creation...")
    
    root = tk.Tk()
    root.title("Supplier Table Test")
    root.geometry("600x400")
    
    # Create main frame
    main_frame = ttk.LabelFrame(root, text="📋 Returns by Supplier", padding="10")
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    try:
        # Get data from database
        conn = get_db_connection()
        if not conn:
            error_label = ttk.Label(main_frame, text="Database connection failed")
            error_label.pack(pady=20)
            root.mainloop()
            return
        
        cursor = conn.cursor()
        
        # Query supplier data
        query = """
            SELECT 
                p.ready_made_supplier as supplier,
                COUNT(DISTINCT r.id) as return_count,
                COUNT(DISTINCT oi.id) as total_orders,
                ROUND((COUNT(DISTINCT r.id) * 100.0 / COUNT(DISTINCT oi.id)), 1) as return_rate
            FROM products p
            LEFT JOIN returns r ON r.product_id = p.id
            LEFT JOIN order_items oi ON oi.product_id = p.id
            WHERE p.ready_made_supplier IS NOT NULL 
              AND p.ready_made_supplier != ''
            GROUP BY p.ready_made_supplier
            HAVING COUNT(DISTINCT oi.id) > 0
            ORDER BY return_count DESC
            LIMIT 15
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not results:
            no_data_label = ttk.Label(main_frame, text="No supplier data available")
            no_data_label.pack(pady=20)
            root.mainloop()
            return
        
        print(f"📊 Found {len(results)} suppliers")
        
        # Create TreeView table
        columns = ("Supplier", "Returns", "Total Orders", "Return Rate %")
        supplier_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=12)
        
        # Configure columns
        supplier_tree.heading("Supplier", text="Supplier Name")
        supplier_tree.heading("Returns", text="Returns")
        supplier_tree.heading("Total Orders", text="Total Orders")
        supplier_tree.heading("Return Rate %", text="Return Rate %")
        
        supplier_tree.column("Supplier", width=200, minwidth=150)
        supplier_tree.column("Returns", width=80, minwidth=60, anchor="center")
        supplier_tree.column("Total Orders", width=100, minwidth=80, anchor="center")
        supplier_tree.column("Return Rate %", width=100, minwidth=80, anchor="center")
        
        # Add data to table
        for row in results:
            supplier_name = str(row[0])
            return_count = int(row[1])
            total_orders = int(row[2])
            return_rate = float(row[3])
            
            supplier_tree.insert("", "end", values=(
                supplier_name, 
                return_count, 
                total_orders,
                f"{return_rate}%"
            ))
            print(f"📋 Added: {supplier_name} - {return_count} returns / {total_orders} orders = {return_rate}%")
        
        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=supplier_tree.yview)
        supplier_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Pack table and scrollbar
        supplier_tree.pack(side="left", fill="both", expand=True, padx=(0, 5))
        tree_scrollbar.pack(side="right", fill="y")
        
        print("✅ Supplier table created successfully!")
        
        # Add close button
        close_button = ttk.Button(root, text="Close", command=root.destroy)
        close_button.pack(pady=5)
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error creating supplier table: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error label
        error_label = ttk.Label(main_frame, 
                              text=f"Error loading supplier data: {str(e)[:50]}...")
        error_label.pack(pady=20)
        
        root.mainloop()

if __name__ == "__main__":
    test_supplier_table()
