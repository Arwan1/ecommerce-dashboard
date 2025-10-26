#!/usr/bin/env python3
"""
Simple standalone supplier table widget test
"""
import tkinter as tk
from tkinter import ttk
from database.db_connector import get_db_connection

class SimpleSupplierTable:
    def __init__(self, parent):
        self.parent = parent
        self.create_supplier_widget()
    
    def create_supplier_widget(self):
        """Create a simple supplier table widget"""
        print("🔧 Creating simple supplier widget...")
        
        # Create main frame
        main_frame = ttk.LabelFrame(self.parent, text="📊 Returns by Supplier", padding="10")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        try:
            # Get data from database
            conn = get_db_connection()
            if not conn:
                ttk.Label(main_frame, text="Database connection failed").pack(pady=20)
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
                LIMIT 10
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not results:
                ttk.Label(main_frame, text="No supplier data available").pack(pady=20)
                return
            
            print(f"✅ Found {len(results)} suppliers")
            
            # Create TreeView table
            columns = ("Supplier", "Returns", "Total Orders", "Return Rate %")
            tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=10)
            
            # Configure columns
            tree.heading("Supplier", text="Supplier Name")
            tree.heading("Returns", text="Returns")  
            tree.heading("Total Orders", text="Total Orders")
            tree.heading("Return Rate %", text="Return Rate %")
            
            tree.column("Supplier", width=200)
            tree.column("Returns", width=100, anchor="center")
            tree.column("Total Orders", width=120, anchor="center")
            tree.column("Return Rate %", width=120, anchor="center")
            
            # Add data
            for row in results:
                tree.insert("", "end", values=(
                    str(row[0]), 
                    int(row[1]), 
                    int(row[2]),
                    f"{float(row[3])}%"
                ))
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            print("✅ Supplier widget created successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            ttk.Label(main_frame, text=f"Error: {str(e)[:50]}...").pack(pady=20)

def main():
    root = tk.Tk()
    root.title("Supplier Table Test")
    root.geometry("700x400")
    
    # Create supplier table
    supplier_table = SimpleSupplierTable(root)
    
    # Add close button
    ttk.Button(root, text="Close", command=root.destroy).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
