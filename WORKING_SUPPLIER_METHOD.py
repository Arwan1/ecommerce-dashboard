# COPY THIS EXACT METHOD INTO YOUR returns_dashboard.py file
# Replace the entire create_supplier_chart method with this working version

def create_supplier_chart(self, time_period):
    """
    WORKING supplier returns chart implementation.
    """
    print(f"📊 Creating supplier chart for period: {time_period}")
    
    if not hasattr(self, 'supplier_section_frame'):
        print("❌ Supplier section frame not found")
        return
    
    try:
        # Clear existing widgets
        for widget in self.supplier_section_frame.winfo_children():
            widget.destroy()
        
        # Get data from database
        from database.db_connector import get_db_connection
        conn = get_db_connection()
        if not conn:
            ttk.Label(self.supplier_section_frame, text="Database connection failed", 
                     font=("Arial", 12), foreground="red").pack(pady=20)
            return
        
        cursor = conn.cursor()
        
        # Create date filter
        date_filter = ""
        if time_period == "Last 7 Days":
            date_filter = "AND r.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
        elif time_period == "Last 30 Days":
            date_filter = "AND r.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
        elif time_period == "Last 90 Days":
            date_filter = "AND r.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)"
        elif time_period == "Last Year":
            date_filter = "AND r.created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR)"
        
        # Working query
        query = f"""
            SELECT 
                p.ready_made_supplier as supplier_name,
                COUNT(DISTINCT r.id) as total_returns,
                COUNT(DISTINCT oi.id) as total_items_sold,
                ROUND((COUNT(DISTINCT r.id) * 100.0 / NULLIF(COUNT(DISTINCT oi.id), 0)), 2) as return_rate_percent,
                ROUND(AVG(r.refund_amount), 2) as avg_refund_amount,
                SUM(r.refund_amount) as total_refund_amount
            FROM products p
            LEFT JOIN returns r ON r.product_id = p.id {date_filter}
            LEFT JOIN order_items oi ON oi.product_id = p.id
            WHERE p.ready_made_supplier IS NOT NULL 
              AND p.ready_made_supplier != ''
            GROUP BY p.ready_made_supplier
            HAVING COUNT(DISTINCT oi.id) > 0
            ORDER BY return_rate_percent DESC
            LIMIT 15
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not results:
            ttk.Label(self.supplier_section_frame, text=f"No supplier data for {time_period}", 
                     font=("Arial", 12), foreground="gray").pack(pady=30)
            return
        
        # Create main container
        main_container = ttk.Frame(self.supplier_section_frame)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # LEFT SIDE - CHART
        chart_frame = ttk.LabelFrame(main_container, text="📈 Return Rates", padding="10")
        chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Chart data (top 8)
        chart_data = results[:8]
        names = [row[0][:12] + "..." if len(row[0]) > 12 else row[0] for row in chart_data]
        rates = [float(row[3]) if row[3] else 0.0 for row in chart_data]
        returns = [int(row[1]) for row in chart_data]
        
        # Create matplotlib chart
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('white')
        
        bars = ax.bar(range(len(names)), rates, color='lightcoral', alpha=0.8, 
                     edgecolor='darkred', linewidth=1)
        
        ax.set_xlabel('Suppliers', fontweight='bold')
        ax.set_ylabel('Return Rate (%)', fontweight='bold')
        ax.set_title(f'Supplier Return Rates - {time_period}', fontweight='bold')
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add labels on bars
        for bar, rate, ret_count in zip(bars, rates, returns):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{rate:.1f}%\\n({ret_count})', 
                   ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        
        # Embed chart
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        
        # RIGHT SIDE - TABLE
        table_frame = ttk.LabelFrame(main_container, text="📋 Data", padding="10")
        table_frame.pack(side="right", fill="both", expand=True)
        
        # Create table
        columns = ("Supplier", "Returns", "Items", "Rate %", "Avg Refund", "Total Refund")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor="center")
        
        tree.column("Supplier", width=120, anchor="w")
        
        # Add data
        for row in results:
            name = str(row[0])[:20]
            returns_count = int(row[1])
            items = int(row[2])
            rate = float(row[3]) if row[3] else 0.0
            avg_refund = float(row[4]) if row[4] else 0.0
            total_refund = float(row[5]) if row[5] else 0.0
            
            tree.insert("", "end", values=(
                name, returns_count, items, f"{rate:.1f}%",
                f"${avg_refund:.2f}", f"${total_refund:.2f}"
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Summary
        stats_frame = ttk.Frame(self.supplier_section_frame)
        stats_frame.pack(fill="x", pady=(10, 0))
        
        avg_rate = sum(float(row[3]) if row[3] else 0 for row in results) / len(results)
        total_refunds = sum(float(row[5]) if row[5] else 0 for row in results)
        
        summary = f"📊 {len(results)} suppliers | Avg rate: {avg_rate:.1f}% | Total refunds: ${total_refunds:,.2f}"
        ttk.Label(stats_frame, text=summary, font=("Arial", 10, "bold"), foreground="navy").pack(pady=5)
        
        print(f"✅ Supplier chart created with {len(results)} suppliers!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        ttk.Label(self.supplier_section_frame, text=f"Error: {str(e)[:50]}...",
                 font=("Arial", 10), foreground="red").pack(pady=20)
