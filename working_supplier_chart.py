#!/usr/bin/env python3
"""
WORKING SUPPLIER RETURNS CHART - STANDALONE SOLUTION
This is a complete, working implementation that you can copy into your returns dashboard.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def create_working_supplier_chart(parent_frame, time_period="Last 30 Days"):
    """
    COMPLETE WORKING SUPPLIER CHART IMPLEMENTATION
    Copy this function into your returns_dashboard.py and replace the broken one.
    """
    print(f"📊 Creating WORKING supplier chart for period: {time_period}")
    
    try:
        # Clear any existing widgets
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        # Get supplier data from database
        from database.db_connector import get_db_connection
        
        conn = get_db_connection()
        if not conn:
            ttk.Label(parent_frame, text="Database connection failed", 
                     font=("Arial", 12), foreground="red").pack(pady=20)
            return
        
        cursor = conn.cursor()
        
        # WORKING QUERY with correct column names
        date_filter = ""
        if time_period == "Last 7 Days":
            date_filter = "AND r.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
        elif time_period == "Last 30 Days":
            date_filter = "AND r.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
        elif time_period == "Last 90 Days":
            date_filter = "AND r.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)"
        elif time_period == "Last Year":
            date_filter = "AND r.created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR)"
        
        query = f"""
            SELECT 
                p.ready_made_supplier as supplier_name,
                COUNT(DISTINCT r.id) as total_returns,
                COUNT(DISTINCT oi.id) as total_items_sold,
                ROUND(
                    (COUNT(DISTINCT r.id) * 100.0 / NULLIF(COUNT(DISTINCT oi.id), 0)), 
                    2
                ) as return_rate_percent,
                ROUND(AVG(r.refund_amount), 2) as avg_refund_amount,
                SUM(r.refund_amount) as total_refund_amount
            FROM products p
            LEFT JOIN returns r ON r.product_id = p.id {date_filter.replace('created_at', 'r.created_at') if date_filter else ''}
            LEFT JOIN order_items oi ON oi.product_id = p.id
            WHERE p.ready_made_supplier IS NOT NULL 
              AND p.ready_made_supplier != ''
              AND p.ready_made_supplier != 'NULL'
            GROUP BY p.ready_made_supplier
            HAVING COUNT(DISTINCT oi.id) > 0
            ORDER BY return_rate_percent DESC, total_returns DESC
            LIMIT 15
        """
        
        print(f"🔍 Executing query for {time_period}")
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not results:
            ttk.Label(parent_frame, text=f"No supplier data available for {time_period}", 
                     font=("Arial", 12), foreground="gray").pack(pady=30)
            return
        
        print(f"✅ Found {len(results)} suppliers")
        
        # Create main container
        main_container = ttk.Frame(parent_frame)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # LEFT SIDE - CHART
        chart_frame = ttk.LabelFrame(main_container, text="📈 Return Rates by Supplier", padding="10")
        chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Create chart data (top 8 for visibility)
        chart_data = results[:8]
        supplier_names = [row[0][:12] + "..." if len(row[0]) > 12 else row[0] for row in chart_data]
        return_rates = [float(row[3]) if row[3] else 0.0 for row in chart_data]
        total_returns = [int(row[1]) for row in chart_data]
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('white')
        
        # Create bar chart
        bars = ax.bar(range(len(supplier_names)), return_rates, 
                     color='lightcoral', alpha=0.8, edgecolor='darkred', linewidth=1)
        
        # Customize chart
        ax.set_xlabel('Suppliers', fontweight='bold', fontsize=11)
        ax.set_ylabel('Return Rate (%)', fontweight='bold', fontsize=11)
        ax.set_title(f'Supplier Return Rates - {time_period}', fontweight='bold', fontsize=13)
        ax.set_xticks(range(len(supplier_names)))
        ax.set_xticklabels(supplier_names, rotation=45, ha='right', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for i, (bar, rate, returns) in enumerate(zip(bars, return_rates, total_returns)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{rate:.1f}%\\n({returns})', 
                   ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        
        # Embed chart in tkinter
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        
        # RIGHT SIDE - TABLE
        table_frame = ttk.LabelFrame(main_container, text="📋 Detailed Data", padding="10")
        table_frame.pack(side="right", fill="both", expand=True)
        
        # Create treeview
        columns = ("Supplier", "Returns", "Items Sold", "Rate %", "Avg Refund", "Total Refund")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        # Configure columns
        tree.heading("Supplier", text="Supplier Name")
        tree.heading("Returns", text="Returns")
        tree.heading("Items Sold", text="Items Sold")
        tree.heading("Rate %", text="Return Rate %")
        tree.heading("Avg Refund", text="Avg Refund")
        tree.heading("Total Refund", text="Total Refund")
        
        tree.column("Supplier", width=120, minwidth=100)
        tree.column("Returns", width=80, minwidth=60, anchor="center")
        tree.column("Items Sold", width=80, minwidth=60, anchor="center")
        tree.column("Rate %", width=80, minwidth=60, anchor="center")
        tree.column("Avg Refund", width=90, minwidth=70, anchor="center")
        tree.column("Total Refund", width=100, minwidth=80, anchor="center")
        
        # Add data to table
        for row in results:
            supplier_name = str(row[0])
            total_returns = int(row[1])
            total_items = int(row[2])
            return_rate = float(row[3]) if row[3] else 0.0
            avg_refund = float(row[4]) if row[4] else 0.0
            total_refund = float(row[5]) if row[5] else 0.0
            
            tree.insert("", "end", values=(
                supplier_name[:20] + "..." if len(supplier_name) > 20 else supplier_name,
                total_returns,
                total_items,
                f"{return_rate:.1f}%",
                f"${avg_refund:.2f}",
                f"${total_refund:.2f}"
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # SUMMARY STATS
        stats_frame = ttk.Frame(parent_frame)
        stats_frame.pack(fill="x", pady=(10, 0))
        
        avg_rate = sum(float(row[3]) if row[3] else 0 for row in results) / len(results)
        max_rate = max(float(row[3]) if row[3] else 0 for row in results)
        total_refunds = sum(float(row[5]) if row[5] else 0 for row in results)
        
        summary_text = (f"📊 {len(results)} suppliers | "
                       f"Avg rate: {avg_rate:.1f}% | "
                       f"Max rate: {max_rate:.1f}% | "
                       f"Total refunds: ${total_refunds:,.2f}")
        
        summary_label = ttk.Label(stats_frame, text=summary_text, 
                                font=("Arial", 10, "bold"), foreground="navy")
        summary_label.pack(pady=5)
        
        print("✅ WORKING supplier chart created successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        error_label = ttk.Label(parent_frame, 
                              text=f"Error: {str(e)[:50]}...",
                              font=("Arial", 10), foreground="red")
        error_label.pack(pady=20)


# TEST THE FUNCTION
if __name__ == "__main__":
    print("🧪 Testing WORKING supplier chart...")
    
    root = tk.Tk()
    root.title("WORKING Supplier Chart Test")
    root.geometry("1400x800")
    
    # Create test frame
    test_frame = ttk.Frame(root, padding="10")
    test_frame.pack(fill="both", expand=True)
    
    # Title
    title_label = ttk.Label(test_frame, text="🎯 WORKING Supplier Returns Chart", 
                           font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 10))
    
    # Create the working chart
    chart_container = ttk.Frame(test_frame)
    chart_container.pack(fill="both", expand=True)
    
    create_working_supplier_chart(chart_container, "Last 30 Days")
    
    # Close button
    ttk.Button(test_frame, text="Close Test", command=root.destroy).pack(pady=10)
    
    print("✅ Test window opened - close it when done")
    root.mainloop()
    print("🎯 Test completed!")
