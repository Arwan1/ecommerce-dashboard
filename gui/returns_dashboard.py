import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from database.db_connector import get_db_connection
from database.db_operations import DBOperations
import datetime

class ReturnsDashboard(tk.Frame):
    """
    Comprehensive Returns Dashboard with analytics and management features.
    """
    def __init__(self, master, user=None):
        super().__init__(master)
        self.user = user
        self.pack(fill="both", expand=True)
        
        # Initialize data
        # self.db_ops = DBOperations()  # Temporarily disabled for debugging
        
        # Create UI
        self.create_widgets()
        
        # Add supplier table immediately after UI creation
        self.after(200, self.add_simple_supplier_table)
        
        # Load initial data with delay to ensure UI is ready
        self.after(100, self.load_returns_data)
        
        # Ensure supplier table is created after everything else
        self.after(500, self.ensure_supplier_table)

    def create_widgets(self):
        """Create the main dashboard interface"""
        # Main container with scrolling
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Control Panel Section (moved to top)
        self.create_control_panel(scrollable_frame)

        # KPI Cards Section
        self.create_kpi_section(scrollable_frame)
        
        # Comprehensive Supplier Analysis Section (NEW)
        self.create_comprehensive_supplier_section(scrollable_frame)
        
        # Charts Section
        self.create_charts_section(scrollable_frame)
        
        # Supplier Returns Table Section (NEW)
        self.create_supplier_table_section(scrollable_frame)
        
        # Recent Returns Section
        self.create_recent_returns_section(scrollable_frame)

    def create_control_panel(self, parent):
        """Create control panel at the top"""
        control_frame = ttk.LabelFrame(parent, text="🔄 Returns Control Panel", padding="15")
        control_frame.pack(fill="x", pady=(0, 10))

        # Main controls frame
        controls_frame = ttk.Frame(control_frame)
        controls_frame.pack(fill="x", pady=(0, 10))

        # First row - Time period and view type
        row1_frame = ttk.Frame(controls_frame)
        row1_frame.pack(fill="x", pady=(0, 10))

        # Time period selection
        period_frame = ttk.LabelFrame(row1_frame, text="📅 Time Period", padding="8")
        period_frame.pack(side="left", padx=(0, 15))
        
        self.period_var = tk.StringVar(value="Last 30 Days")
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, width=20, font=("Arial", 10))
        period_combo['values'] = ("Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "All Time")
        period_combo.pack(pady=2)
        
        # Bind period change to refresh data
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.load_returns_data())

        # View type selection
        view_frame = ttk.LabelFrame(row1_frame, text="📋 View Type", padding="8")
        view_frame.pack(side="left", padx=(0, 15))
        
        self.view_type_var = tk.StringVar(value="All Returns")
        view_combo = ttk.Combobox(view_frame, textvariable=self.view_type_var, width=20, font=("Arial", 10))
        view_combo['values'] = ("All Returns", "Pending Returns", "Approved Returns", "Rejected Returns")
        view_combo.pack(pady=2)
        view_combo.bind('<<ComboboxSelected>>', lambda e: self.load_returns_data())

        # Quick stats display
        stats_frame = ttk.LabelFrame(row1_frame, text="📊 Quick Stats", padding="8")
        stats_frame.pack(side="left", fill="x", expand=True)
        
        self.quick_stats_label = ttk.Label(stats_frame, text="Select a time period to view statistics", 
                                          font=("Arial", 9), foreground="#666666")
        self.quick_stats_label.pack(pady=2)

        # Second row - Action buttons
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill="x")

        # Create action buttons
        self.refresh_btn = tk.Button(buttons_frame, text="🔄 Refresh Data", 
                                    command=self.load_returns_data, 
                                    bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                    padx=20, pady=8, relief="raised", borderwidth=2)
        self.refresh_btn.pack(side="left", padx=(0, 10))

        self.manage_btn = tk.Button(buttons_frame, text="📋 Manage Returns", 
                                   command=self.open_returns_manager, 
                                   bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                   padx=20, pady=8, relief="raised", borderwidth=2)
        self.manage_btn.pack(side="left", padx=(0, 10))

        self.export_btn = tk.Button(buttons_frame, text="📊 Export CSV", 
                                   command=self.export_returns_csv, 
                                   bg="#9C27B0", fg="white", font=("Arial", 10, "bold"),
                                   padx=20, pady=8, relief="raised", borderwidth=2)
        self.export_btn.pack(side="left", padx=(0, 10))

        self.process_btn = tk.Button(buttons_frame, text="⚡ Process Return", 
                                    command=self.quick_process_return, 
                                    bg="#FF5722", fg="white", font=("Arial", 10, "bold"),
                                    padx=20, pady=8, relief="raised", borderwidth=2)
        self.process_btn.pack(side="left", padx=(0, 10))

        # Add separator line
        separator = ttk.Separator(control_frame, orient='horizontal')
        separator.pack(fill="x", pady=(10, 0))

    def create_kpi_section(self, parent):
        """Create Key Performance Indicator cards for returns"""
        kpi_frame = ttk.LabelFrame(parent, text="📈 Returns Key Performance Indicators", padding="10")
        kpi_frame.pack(fill="x", pady=5)

        # KPI Cards Container
        cards_container = ttk.Frame(kpi_frame)
        cards_container.pack(fill="x")

        # Create KPI cards in a grid
        self.kpi_cards = {}
        kpi_data = [
            ("Total Returns", "total_returns", "#F44336"),
            ("Return Rate %", "return_rate", "#FF9800"),
            ("Pending Returns", "pending_returns", "#2196F3"),
            ("Damaged Items", "damaged_items", "#9C27B0"),
            ("Avg Return Value", "avg_return_value", "#4CAF50"),
            ("Processing Time", "avg_processing_time", "#607D8B")
        ]

        for i, (title, key, color) in enumerate(kpi_data):
            card_frame = ttk.Frame(cards_container, style="Card.TFrame")
            card_frame.grid(row=i//3, column=i%3, padx=10, pady=5, sticky="ew")

            # Title
            title_label = ttk.Label(card_frame, text=title, font=("Arial", 10, "bold"))
            title_label.pack(pady=(5, 0))

            # Value
            value_label = ttk.Label(card_frame, text="Loading...", font=("Arial", 14, "bold"), foreground=color)
            value_label.pack(pady=(0, 5))

            self.kpi_cards[key] = value_label

        # Configure grid weights
        for i in range(3):
            cards_container.columnconfigure(i, weight=1)

    def create_comprehensive_supplier_section(self, parent):
        """Create comprehensive supplier analysis table with raw materials vs finished products"""
        supplier_frame = ttk.LabelFrame(parent, text="🏭 Comprehensive Supplier Analysis", padding="10")
        supplier_frame.pack(fill="both", expand=True, pady=5)
        
        # Create control frame for filters
        control_frame = ttk.Frame(supplier_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Time period filter
        period_label = ttk.Label(control_frame, text="Time Period:", font=("Arial", 9, "bold"))
        period_label.pack(side="left", padx=(0, 5))
        
        self.supplier_period_var = tk.StringVar(value="Last 30 Days")
        period_combo = ttk.Combobox(control_frame, textvariable=self.supplier_period_var, width=15)
        period_combo['values'] = ("Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "All Time")
        period_combo.pack(side="left", padx=(0, 15))
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.load_supplier_analysis())
        
        # Supplier type filter
        type_label = ttk.Label(control_frame, text="Supplier Type:", font=("Arial", 9, "bold"))
        type_label.pack(side="left", padx=(0, 5))
        
        self.supplier_type_var = tk.StringVar(value="All Suppliers")
        type_combo = ttk.Combobox(control_frame, textvariable=self.supplier_type_var, width=15)
        type_combo['values'] = ("All Suppliers", "Raw Materials", "Finished Products")
        type_combo.pack(side="left", padx=(0, 15))
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.load_supplier_analysis())
        
        # Refresh button
        refresh_btn = tk.Button(control_frame, text="🔄 Refresh", command=self.load_supplier_analysis,
                               bg="#2196F3", fg="white", font=("Arial", 9, "bold"), 
                               padx=15, pady=5, relief="raised")
        refresh_btn.pack(side="left", padx=(10, 0))
        
        # Create main table frame
        table_main_frame = ttk.Frame(supplier_frame)
        table_main_frame.pack(fill="both", expand=True)
        
        # Create TreeView for supplier data
        columns = ("Supplier", "Type", "Products", "Ordered", "Returned", "Return %", "Avg Order", "Total Refunded", "Status")
        self.supplier_tree = ttk.Treeview(table_main_frame, columns=columns, show="headings", height=12)
        
        # Configure column headings and widths
        column_config = {
            "Supplier": (150, "w"),
            "Type": (100, "center"), 
            "Products": (80, "center"),
            "Ordered": (80, "center"),
            "Returned": (80, "center"),
            "Return %": (80, "center"),
            "Avg Order": (90, "center"),
            "Total Refunded": (110, "center"),
            "Status": (90, "center")
        }
        
        for col, (width, anchor) in column_config.items():
            self.supplier_tree.heading(col, text=col, anchor="center")
            self.supplier_tree.column(col, width=width, minwidth=70, anchor=anchor)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(table_main_frame, orient="vertical", command=self.supplier_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_main_frame, orient="horizontal", command=self.supplier_tree.xview)
        self.supplier_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack table and scrollbars
        self.supplier_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        # Summary statistics frame
        summary_frame = ttk.Frame(supplier_frame)
        summary_frame.pack(fill="x", pady=(10, 0))
        
        self.supplier_summary_label = ttk.Label(summary_frame, 
                                              text="Loading supplier analysis...", 
                                              font=("Arial", 10, "bold"), 
                                              foreground="navy")
        self.supplier_summary_label.pack(pady=5)
        
        # Store frame reference for later updates
        self.supplier_analysis_frame = supplier_frame
        
        # Load initial data
        self.after(300, self.load_supplier_analysis)

    def load_supplier_analysis(self):
        """Load and display comprehensive supplier analysis data"""
        try:
            print("🔄 Loading supplier analysis...")
            
            # Clear existing data
            for item in self.supplier_tree.get_children():
                self.supplier_tree.delete(item)
            
            # Get filter values
            time_period = self.supplier_period_var.get()
            supplier_type = self.supplier_type_var.get()
            
            # Create date filter
            date_filter = ""
            if time_period == "Last 7 Days":
                date_filter = "AND (r.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) OR r.created_at IS NULL)"
            elif time_period == "Last 30 Days":
                date_filter = "AND (r.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) OR r.created_at IS NULL)"
            elif time_period == "Last 90 Days":
                date_filter = "AND (r.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY) OR r.created_at IS NULL)"
            elif time_period == "Last Year":
                date_filter = "AND (r.created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR) OR r.created_at IS NULL)"
            
            # Get database connection
            from database.db_connector import get_db_connection
            conn = get_db_connection()
            if not conn:
                self.supplier_summary_label.config(text="❌ Database connection failed")
                return
            
            cursor = conn.cursor()
            
            # Query for finished products (is_ready_made = 1)
            finished_query = f"""
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
                LEFT JOIN returns r ON r.product_id = p.id {date_filter}
                WHERE p.ready_made_supplier IS NOT NULL 
                  AND p.ready_made_supplier != ''
                  AND p.ready_made_supplier != 'NULL'
                  AND p.is_ready_made = 1
                GROUP BY p.ready_made_supplier
                HAVING COUNT(DISTINCT oi.id) > 0
            """
            
            # Query for raw materials (is_ready_made = 0)
            raw_query = f"""
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
                LEFT JOIN returns r ON r.product_id = p.id {date_filter}
                WHERE p.ready_made_supplier IS NOT NULL 
                  AND p.ready_made_supplier != ''
                  AND p.ready_made_supplier != 'NULL'
                  AND p.is_ready_made = 0
                GROUP BY p.ready_made_supplier
                HAVING COUNT(DISTINCT oi.id) > 0
            """
            
            all_suppliers = []
            
            # Execute finished products query
            if supplier_type in ["All Suppliers", "Finished Products"]:
                cursor.execute(finished_query)
                finished_results = cursor.fetchall()
                all_suppliers.extend(finished_results)
            
            # Execute raw materials query
            if supplier_type in ["All Suppliers", "Raw Materials"]:
                cursor.execute(raw_query)
                raw_results = cursor.fetchall()
                all_suppliers.extend(raw_results)
            
            cursor.close()
            conn.close()
            
            if not all_suppliers:
                self.supplier_summary_label.config(text=f"📊 No supplier data found for {time_period}")
                return
            
            # Sort by return percentage (descending)
            all_suppliers.sort(key=lambda x: float(x[5]) if x[5] else 0, reverse=True)
            
            # Populate table
            total_ordered = 0
            total_returned = 0
            total_refunded = 0
            
            for supplier_data in all_suppliers:
                supplier_name = str(supplier_data[0])[:25]
                supplier_type_name = supplier_data[1]
                product_count = int(supplier_data[2])
                ordered = int(supplier_data[3])
                returned = int(supplier_data[4])
                return_pct = float(supplier_data[5]) if supplier_data[5] else 0.0
                avg_order = float(supplier_data[6]) if supplier_data[6] else 0.0
                refunded = float(supplier_data[7]) if supplier_data[7] else 0.0
                
                # Determine status based on return percentage
                if return_pct >= 15:
                    status = "🔴 HIGH"
                elif return_pct >= 8:
                    status = "🟡 MEDIUM"
                elif return_pct >= 3:
                    status = "🟢 LOW"
                else:
                    status = "✅ EXCELLENT"
                
                # Insert row
                self.supplier_tree.insert("", "end", values=(
                    supplier_name,
                    supplier_type_name,
                    product_count,
                    ordered,
                    returned,
                    f"{return_pct:.1f}%",
                    f"${avg_order:.2f}",
                    f"${refunded:.2f}",
                    status
                ))
                
                # Accumulate totals
                total_ordered += ordered
                total_returned += returned
                total_refunded += refunded
            
            # Update summary
            overall_return_rate = (total_returned / total_ordered * 100) if total_ordered > 0 else 0
            supplier_count = len(all_suppliers)
            
            summary_text = (f"📊 {supplier_count} suppliers | "
                          f"Overall return rate: {overall_return_rate:.1f}% | "
                          f"Total ordered: {total_ordered:,} | "
                          f"Total returned: {total_returned:,} | "
                          f"Total refunded: ${total_refunded:,.2f}")
            
            self.supplier_summary_label.config(text=summary_text)
            
            print(f"✅ Supplier analysis loaded: {len(all_suppliers)} suppliers")
            
        except Exception as e:
            print(f"❌ Error loading supplier analysis: {e}")
            import traceback
            traceback.print_exc()
            self.supplier_summary_label.config(text=f"❌ Error: {str(e)[:50]}...")

    def create_charts_section(self, parent):
        """Create charts section with matplotlib and supplier table"""
        charts_frame = ttk.LabelFrame(parent, text="📊 Returns Analytics", padding="10")
        charts_frame.pack(fill="both", expand=True, pady=5)

        # Create main container for charts and table
        main_container = ttk.Frame(charts_frame)
        main_container.pack(fill="both", expand=True)
        
        # Top row - two charts
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        # Create matplotlib figure for top charts (1x2 layout)
        self.fig_top, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(16, 6))
        self.fig_top.suptitle('Returns Trend & Top Returned Items', fontsize=14, fontweight='bold')
        self.fig_top.tight_layout(rect=[0.05, 0.08, 0.95, 0.92], pad=2.0)
        
        # Embed top charts in tkinter
        self.canvas_top = FigureCanvasTkAgg(self.fig_top, top_frame)
        self.canvas_top.get_tk_widget().pack(fill="both", expand=True)

        # Bottom row - table and chart
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(fill="both", expand=True)
        
        # Left side - Supplier table
        table_frame = ttk.LabelFrame(bottom_frame, text="📋 Returns by Supplier", padding="5")
        table_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Create supplier table
        self.supplier_table_frame = table_frame
        
        # Right side - Return reasons chart
        chart_frame = ttk.Frame(bottom_frame)
        chart_frame.pack(side="right", fill="both", expand=True)
        
        # Create matplotlib figure for return reasons chart
        self.fig_bottom, self.ax4 = plt.subplots(1, 1, figsize=(8, 6))
        self.fig_bottom.suptitle('Return Reasons Distribution', fontsize=14, fontweight='bold')
        self.fig_bottom.tight_layout(rect=[0.05, 0.08, 0.95, 0.92], pad=2.0)
        
        # Embed bottom chart in tkinter
        self.canvas_bottom = FigureCanvasTkAgg(self.fig_bottom, chart_frame)
        self.canvas_bottom.get_tk_widget().pack(fill="both", expand=True)

    def create_supplier_table_section(self, parent):
        """Create standalone supplier returns table section"""
        print("🔧 Creating supplier table section...")
        supplier_section = ttk.LabelFrame(parent, text="📊 Returns by Supplier", padding="10")
        supplier_section.pack(fill="both", expand=True, pady=5)
        
        # Create frame for the table
        table_frame = ttk.Frame(supplier_section)
        table_frame.pack(fill="both", expand=True)
        
        # Store reference for later use
        self.supplier_section_frame = table_frame
        print(f"🔧 Supplier section frame created: {table_frame}")
        
        # Create initial empty message
        self.supplier_loading_label = ttk.Label(table_frame, text="Loading supplier data...", 
                                              font=("Arial", 10), foreground="gray")
        self.supplier_loading_label.pack(pady=20)
        print("🔧 Supplier table section created successfully!")
    
    def ensure_supplier_table(self):
        """Ensure the supplier table is created and visible"""
        print("🔧 ensure_supplier_table called")
        if hasattr(self, 'supplier_section_frame'):
            print("🔧 Supplier section frame found, creating table...")
            self.create_supplier_chart('Last 30 Days')
        else:
            print("🔧 Supplier section frame NOT found!")
    
    def add_simple_supplier_table(self):
        """Add a simple, direct supplier table to the main frame"""
        print("🔧 Adding simple supplier table...")
        
        # Find the main scrollable frame
        main_frame = None
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Canvas):
                        canvas = child
                        for canvas_child in canvas.winfo_children():
                            if isinstance(canvas_child, ttk.Frame):
                                main_frame = canvas_child
                                break
                        break
                break
        
        if not main_frame:
            print("❌ Could not find main frame")
            return
        
        print("✅ Found main frame, creating supplier table...")
        
        # Create supplier section at the top
        supplier_frame = ttk.LabelFrame(main_frame, text="📊 Returns by Supplier", padding="10")
        supplier_frame.pack(fill="x", pady=5, before=main_frame.winfo_children()[0] if main_frame.winfo_children() else None)
        
        try:
            # Get data from database
            from database.db_connector import get_db_connection
            conn = get_db_connection()
            if not conn:
                ttk.Label(supplier_frame, text="Database connection failed").pack(pady=10)
                return
            
            cursor = conn.cursor()
            query = '''
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
                LIMIT 8
            '''
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not results:
                ttk.Label(supplier_frame, text="No supplier data available").pack(pady=10)
                return
            
            # Create table
            columns = ("Supplier", "Returns", "Total Orders", "Return Rate %")
            tree = ttk.Treeview(supplier_frame, columns=columns, show="headings", height=6)
            
            for col in columns:
                tree.heading(col, text=col)
            
            tree.column("Supplier", width=180)
            tree.column("Returns", width=80, anchor="center")
            tree.column("Total Orders", width=100, anchor="center")
            tree.column("Return Rate %", width=100, anchor="center")
            
            for row in results:
                tree.insert("", "end", values=(
                    str(row[0]), int(row[1]), int(row[2]), f"{float(row[3])}%"
                ))
            
            scrollbar = ttk.Scrollbar(supplier_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            print(f"✅ Simple supplier table added with {len(results)} suppliers!")
            
        except Exception as e:
            print(f"❌ Error adding supplier table: {e}")
            ttk.Label(supplier_frame, text=f"Error: {str(e)[:40]}...").pack(pady=10)

    def create_recent_returns_section(self, parent):
        """Create recent returns activity section"""
        returns_frame = ttk.LabelFrame(parent, text="🕒 Recent Returns Activity", padding="10")
        returns_frame.pack(fill="x", pady=5)

        # Recent returns treeview
        columns = ("Return ID", "Product", "Order ID", "Date", "Reason", "Status", "Value")
        self.returns_tree = ttk.Treeview(returns_frame, columns=columns, show="headings", height=8)
        
        # Configure columns
        column_widths = {"Return ID": 80, "Product": 150, "Order ID": 80, "Date": 100, 
                        "Reason": 120, "Status": 80, "Value": 80}
        
        for col in columns:
            self.returns_tree.heading(col, text=col)
            self.returns_tree.column(col, width=column_widths.get(col, 100))
        
        # Add scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(returns_frame, orient="vertical", command=self.returns_tree.yview)
        self.returns_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.returns_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

    def load_returns_data(self):
        """Load returns data in background thread"""
        def load_in_background():
            try:
                # Get selected filters with fallbacks
                time_period = getattr(self, 'period_var', None)
                time_period = time_period.get() if time_period else "Last 30 Days"
                
                view_type = getattr(self, 'view_type_var', None)
                view_type = view_type.get() if view_type else "All Returns"
                
                print(f"🔍 Loading data with time_period: {time_period}, view_type: {view_type}")
                
                # Get returns data
                returns_data = self.get_returns_data(time_period, view_type)
                
                # Get chart data
                chart_data = self.get_returns_chart_data(time_period)
                
                # Update UI in main thread
                self.after(0, lambda: self.update_dashboard(returns_data, chart_data))
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error in load_in_background: {e}")
                import traceback
                traceback.print_exc()
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to load returns data: {error_msg}"))
        
        # Show loading state
        if hasattr(self, 'kpi_cards'):
            for card in self.kpi_cards.values():
                card.config(text="Loading...")
        
        thread = threading.Thread(target=load_in_background)
        thread.daemon = True
        thread.start()

    def get_date_filter_sql(self, time_period):
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

    def get_returns_data(self, time_period, view_type):
        """Get returns KPI data"""
        conn = get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(dictionary=True)
            date_filter = self.get_date_filter_sql(time_period)
            
            # Status filter
            status_filter = ""
            if view_type == "Pending Returns":
                status_filter = "AND status = 'Pending'"
            elif view_type == "Approved Returns":
                status_filter = "AND status = 'Approved'"
            elif view_type == "Rejected Returns":
                status_filter = "AND status = 'Rejected'"
            
            # Total returns
            cursor.execute(f"""
                SELECT COUNT(*) as total_returns,
                       AVG(CASE WHEN status IN ('Approved', 'Rejected') 
                           THEN DATEDIFF(updated_at, created_at) END) as avg_processing_days
                FROM returns 
                WHERE 1=1 {date_filter} {status_filter}
            """)
            result = cursor.fetchone()
            total_returns = result['total_returns'] or 0
            avg_processing_days = result['avg_processing_days'] or 0
            
            # Return rate (returns vs total orders)
            cursor.execute(f"""
                SELECT COUNT(DISTINCT o.id) as total_orders
                FROM orders o
                WHERE 1=1 {date_filter}
            """)
            total_orders = cursor.fetchone()['total_orders'] or 1
            return_rate = (total_returns / total_orders) * 100 if total_orders > 0 else 0
            
            # Pending returns
            cursor.execute(f"""
                SELECT COUNT(*) as pending_returns
                FROM returns 
                WHERE status = 'Pending' {date_filter}
            """)
            pending_returns = cursor.fetchone()['pending_returns'] or 0
            
            # Damaged items (assuming 'Damaged' is a return reason)
            cursor.execute(f"""
                SELECT COUNT(*) as damaged_items
                FROM returns 
                WHERE reason LIKE '%damage%' OR reason LIKE '%broken%' OR reason LIKE '%defect%'
                {date_filter} {status_filter}
            """)
            damaged_items = cursor.fetchone()['damaged_items'] or 0
            
            # Average return value
            cursor.execute(f"""
                SELECT AVG(r.refund_amount) as avg_return_value
                FROM returns r
                WHERE r.refund_amount IS NOT NULL {date_filter} {status_filter}
            """)
            avg_return_value = cursor.fetchone()['avg_return_value'] or 0
            
            return {
                'total_returns': total_returns,
                'return_rate': return_rate,
                'pending_returns': pending_returns,
                'damaged_items': damaged_items,
                'avg_return_value': avg_return_value,
                'avg_processing_time': avg_processing_days
            }
        except Exception as e:
            print(f"Error getting returns data: {e}")
            return {}
        finally:
            conn.close()

    def get_returns_chart_data(self, time_period):
        """Get data for returns charts"""
        print(f"🔍 get_returns_chart_data called with time_period: {time_period}")
        conn = get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(dictionary=True)
            date_filter = self.get_date_filter_sql(time_period)
            print(f"🔍 Date filter: {date_filter}")
            
            # 1. Returns trend over time (top-left chart)
            try:
                if time_period in ["Last 7 Days", "Last 30 Days"]:
                    # Daily data for short periods
                    cursor.execute(f"""
                        SELECT 
                            DATE(r.created_at) as period,
                            COUNT(*) as returns_count,
                            COUNT(DISTINCT o.id) as orders_count
                        FROM returns r
                        JOIN orders o ON DATE(r.created_at) = DATE(o.created_at)
                        WHERE 1=1 {date_filter.replace('created_at', 'r.created_at')}
                        GROUP BY DATE(r.created_at)
                        ORDER BY DATE(r.created_at)
                    """)
                else:
                    # Monthly data for longer periods
                    cursor.execute(f"""
                        SELECT 
                            YEAR(r.created_at) as year,
                            MONTH(r.created_at) as month,
                            COUNT(*) as returns_count,
                            COUNT(DISTINCT DATE(o.created_at)) as orders_count
                        FROM returns r
                        LEFT JOIN orders o ON YEAR(r.created_at) = YEAR(o.created_at) 
                                            AND MONTH(r.created_at) = MONTH(o.created_at)
                        WHERE 1=1 {date_filter.replace('created_at', 'r.created_at')}
                        GROUP BY YEAR(r.created_at), MONTH(r.created_at)
                        ORDER BY YEAR(r.created_at), MONTH(r.created_at)
                    """)
                    raw_trend = cursor.fetchall()
                    # Format periods
                    returns_trend = []
                    for row in raw_trend:
                        formatted_row = {
                            'period': f"{row['year']}-{row['month']:02d}",
                            'returns_count': row['returns_count'],
                            'orders_count': row['orders_count'] or 1
                        }
                        returns_trend.append(formatted_row)
                    
                if time_period in ["Last 7 Days", "Last 30 Days"]:
                    returns_trend = cursor.fetchall()
            except Exception as e:
                print(f"Error in returns trend query: {e}")
                returns_trend = []

            # 2. Most returned items (top-right pie chart)
            try:
                cursor.execute(f"""
                    SELECT p.name, COUNT(*) as return_count
                    FROM returns r
                    JOIN products p ON r.product_id = p.id
                    WHERE 1=1 {date_filter.replace('created_at', 'r.created_at')}
                    GROUP BY p.id, p.name
                    ORDER BY return_count DESC
                    LIMIT 5
                """)
                most_returned_items = cursor.fetchall()
            except Exception as e:
                print(f"Error in most returned items query: {e}")
                most_returned_items = []

            # 3. Supplier return analysis - handled separately by create_supplier_chart()
            supplier_returns = []  # Empty since we handle this separately

            # 4. Return reasons distribution (bottom-right)
            try:
                cursor.execute(f"""
                    SELECT 
                        CASE 
                            WHEN reason LIKE '%damage%' OR reason LIKE '%broken%' OR reason LIKE '%defect%' THEN 'Damaged/Defective'
                            WHEN reason LIKE '%size%' OR reason LIKE '%fit%' THEN 'Size/Fit Issue'
                            WHEN reason LIKE '%wrong%' OR reason LIKE '%incorrect%' THEN 'Wrong Item'
                            WHEN reason LIKE '%quality%' THEN 'Quality Issue'
                            ELSE 'Other'
                        END as reason_category,
                        COUNT(*) as count
                    FROM returns r
                    WHERE 1=1 {date_filter.replace('created_at', 'r.created_at')}
                    GROUP BY reason_category
                    ORDER BY count DESC
                """)
                return_reasons = cursor.fetchall()
            except Exception as e:
                print(f"Error in return reasons query: {e}")
                return_reasons = []

            print(f"🔍 Returning chart data with supplier_returns: {len(supplier_returns) if supplier_returns else 0} items")
            if supplier_returns:
                print(f"🔍 First supplier item before return: {supplier_returns[0]}")
            
            return {
                'returns_trend': returns_trend,
                'most_returned_items': most_returned_items,
                'supplier_returns': supplier_returns,
                'return_reasons': return_reasons,
                'time_period': time_period
            }
        except Exception as e:
            print(f"Error getting chart data: {e}")
            return {}
        finally:
            conn.close()

    def update_dashboard(self, returns_data, chart_data):
        """Update dashboard with loaded data"""
        # Update KPI cards
        if hasattr(self, 'kpi_cards'):
            self.kpi_cards['total_returns'].config(text=f"{returns_data.get('total_returns', 0):,}")
            self.kpi_cards['return_rate'].config(text=f"{returns_data.get('return_rate', 0):.1f}%")
            self.kpi_cards['pending_returns'].config(text=f"{returns_data.get('pending_returns', 0):,}")
            self.kpi_cards['damaged_items'].config(text=f"{returns_data.get('damaged_items', 0):,}")
            self.kpi_cards['avg_return_value'].config(text=f"${returns_data.get('avg_return_value', 0):.2f}")
            self.kpi_cards['avg_processing_time'].config(text=f"{returns_data.get('avg_processing_time', 0):.1f} days")
        # Update quick stats
        self.update_quick_stats(returns_data, chart_data)
        # Update charts
        self.update_charts(chart_data)
        # Create supplier table in new section
        self.create_supplier_chart(chart_data.get('time_period', 'Last 30 Days'))
        # Update recent returns
        self.update_recent_returns()
    def update_quick_stats(self, returns_data, chart_data):
        """Update the quick stats display"""
        try:
            time_period = self.period_var.get()
            total_returns = returns_data.get('total_returns', 0)
            return_rate = returns_data.get('return_rate', 0)
            stats_text = f"{time_period}: {total_returns:,} returns • {return_rate:.1f}% return rate"
            self.quick_stats_label.config(text=stats_text, foreground="#F44336")
            
        except Exception as e:
            self.quick_stats_label.config(text="Error calculating stats", foreground="#F44336")
            print(f"Quick stats error: {e}")

    def update_charts(self, chart_data):
        """Update matplotlib charts"""
        print("📊 Updating returns charts...")
        print(f"📊 Chart data keys: {list(chart_data.keys())}")
        print(f"📊 Supplier returns in chart_data: {chart_data.get('supplier_returns')}")
        
        # Get time period for titles
        time_period = chart_data.get('time_period', 'All Time')
        
        # Clear all subplots (now only 3 matplotlib charts)
        for ax in [self.ax1, self.ax2, self.ax4]:
            ax.clear()

        # Chart 1: Returns/Orders Trend (top-left)
        if chart_data.get('returns_trend') and len(chart_data['returns_trend']) > 0:
            try:
                periods = [item['period'] for item in chart_data['returns_trend']]
                returns_counts = [item['returns_count'] for item in chart_data['returns_trend']]
                orders_counts = [item['orders_count'] for item in chart_data['returns_trend']]
                
                # Calculate return rate for each period
                return_rates = [r/o * 100 if o > 0 else 0 for r, o in zip(returns_counts, orders_counts)]
                
                self.ax1.plot(periods, return_rates, marker='o', linewidth=2, markersize=6, color='#F44336')
                title = f'Return Rate Trend ({time_period})'
                self.ax1.set_title(title, fontweight='bold')
                self.ax1.set_ylabel('Return Rate (%)')
                self.ax1.tick_params(axis='x', rotation=45)
                self.ax1.grid(True, alpha=0.3)
                print("   ✅ Return rate trend chart updated")
            except Exception as e:
                print(f"   ❌ Return rate trend error: {e}")
                self.ax1.text(0.5, 0.5, 'No trend data available', 
                             ha='center', va='center', transform=self.ax1.transAxes)
                self.ax1.set_title(f'Return Rate Trend ({time_period})', fontweight='bold')
        else:
            self.ax1.text(0.5, 0.5, 'No trend data available', 
                         ha='center', va='center', transform=self.ax1.transAxes)
            self.ax1.set_title(f'Return Rate Trend ({time_period})', fontweight='bold')

        # Chart 2: Most Returned Items (top-right pie chart)
        if chart_data.get('most_returned_items') and len(chart_data['most_returned_items']) > 0:
            try:
                items = [item['name'][:20] + '...' if len(item['name']) > 20 else item['name'] 
                        for item in chart_data['most_returned_items']]
                counts = [item['return_count'] for item in chart_data['most_returned_items']]
                
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                
                wedges, texts, autotexts = self.ax2.pie(counts, labels=items, autopct='%1.1f%%', 
                                                       colors=colors[:len(counts)], startangle=90)
                self.ax2.set_title(f'Most Returned Items ({time_period})', fontweight='bold')
                
                # Improve text readability
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(8)
                
                print("   ✅ Most returned items chart updated")
            except Exception as e:
                print(f"   ❌ Most returned items error: {e}")
                self.ax2.text(0.5, 0.5, 'No returned items data', 
                             ha='center', va='center', transform=self.ax2.transAxes)
                self.ax2.set_title(f'Most Returned Items ({time_period})', fontweight='bold')
        else:
            self.ax2.text(0.5, 0.5, 'No returned items data', 
                         ha='center', va='center', transform=self.ax2.transAxes)
            self.ax2.set_title(f'Most Returned Items ({time_period})', fontweight='bold')

        # Chart 3: Supplier Returns Table (bottom-left) - REPLACED CHART WITH TABLE
        print("🔍 About to call create_supplier_chart...")
        print(f"🔍 supplier_table_frame exists: {hasattr(self, 'supplier_table_frame')}")
        if hasattr(self, 'supplier_table_frame'):
            print(f"🔍 supplier_table_frame is: {self.supplier_table_frame}")
        self.create_supplier_chart(time_period)

        # Chart 4: Return Reasons Distribution (bottom-right)
        if chart_data.get('return_reasons') and len(chart_data['return_reasons']) > 0:
            try:
                reasons = [item['reason_category'] for item in chart_data['return_reasons']]
                counts = [item['count'] for item in chart_data['return_reasons']]
                
                colors = ['#FF9800', '#2196F3', '#4CAF50', '#E91E63', '#795548']
                
                bars = self.ax4.bar(reasons, counts, color=colors[:len(reasons)], alpha=0.8)
                self.ax4.set_title(f'Return Reasons ({time_period})', fontweight='bold')
                self.ax4.set_ylabel('Count')
                self.ax4.tick_params(axis='x', rotation=45)
                
                # Add value labels on bars
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    self.ax4.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                f'{count}', ha='center', va='bottom', fontsize=8)
                
                print("   ✅ Return reasons chart updated")
            except Exception as e:
                print(f"   ❌ Return reasons error: {e}")
                self.ax4.text(0.5, 0.5, 'No return reasons data', 
                             ha='center', va='center', transform=self.ax4.transAxes)
                self.ax4.set_title(f'Return Reasons ({time_period})', fontweight='bold')
        else:
            self.ax4.text(0.5, 0.5, 'No return reasons data', 
                         ha='center', va='center', transform=self.ax4.transAxes)
            self.ax4.set_title(f'Return Reasons ({time_period})', fontweight='bold')

        # Refresh the canvas with layout adjustment
        self.fig_top.tight_layout(rect=[0.05, 0.08, 0.95, 0.92], pad=3.0, h_pad=3.0, w_pad=2.0)
        self.fig_bottom.tight_layout(rect=[0.05, 0.08, 0.95, 0.92], pad=3.0, h_pad=3.0, w_pad=2.0)
        self.canvas_top.draw()
        self.canvas_bottom.draw()
        print("📊 Returns charts update completed")

    def update_recent_returns(self):
        """Update recent returns activity list"""
        try:
            conn = get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor(dictionary=True)
            
            # Get recent returns with product and order info
            cursor.execute("""
                SELECT r.id, r.created_at, r.reason, r.status, r.refund_amount,
                       p.name as product_name, r.order_id
                FROM returns r
                LEFT JOIN products p ON r.product_id = p.id
                ORDER BY r.created_at DESC
                LIMIT 20
            """)
            recent_returns = cursor.fetchall()
            
            # Clear existing items
            for item in self.returns_tree.get_children():
                self.returns_tree.delete(item)
            
            # Add recent returns to treeview
            for return_item in recent_returns:
                date_str = return_item['created_at'].strftime('%Y-%m-%d') if return_item['created_at'] else 'N/A'
                self.returns_tree.insert('', 'end', values=(
                    return_item.get('id', 'N/A'),
                    return_item.get('product_name', 'Unknown')[:20],
                    return_item.get('order_id', 'N/A'),
                    date_str,
                    return_item.get('reason', 'No reason')[:15],
                    return_item.get('status', 'Unknown'),
                    f"${return_item.get('refund_amount', 0):.2f}"
                ))
            
            conn.close()
            
        except Exception as e:
            print(f"Error updating recent returns: {e}")

    def open_returns_manager(self):
        """Open the spreadsheet-like returns manager window"""
        try:
            # Create new window
            manager_window = tk.Toplevel(self.master)
            manager_window.title("Returns Manager")
            manager_window.geometry("1200x700")
            manager_window.transient(self.master)
            
            # Create main frame
            main_frame = ttk.Frame(manager_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create toolbar
            toolbar = ttk.Frame(main_frame)
            toolbar.pack(fill="x", pady=(0, 10))
            
            # Toolbar buttons
            ttk.Button(toolbar, text="🔄 Refresh", command=lambda: self.refresh_returns_manager(tree)).pack(side="left", padx=5)
            ttk.Button(toolbar, text="✅ Approve Selected", command=lambda: self.bulk_action(tree, "Approved")).pack(side="left", padx=5)
            ttk.Button(toolbar, text="❌ Reject Selected", command=lambda: self.bulk_action(tree, "Rejected")).pack(side="left", padx=5)
            ttk.Button(toolbar, text="📊 Export", command=lambda: self.export_selected_returns(tree)).pack(side="left", padx=5)
            
            # Search frame
            search_frame = ttk.Frame(toolbar)
            search_frame.pack(side="right")
            
            ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20)
            search_entry.pack(side="left", padx=5)
            search_entry.bind('<KeyRelease>', lambda e: self.search_returns(tree, search_var.get()))
            
            # Create treeview with detailed columns
            columns = ("ID", "Date", "Product", "Reason", "Status", "Value", "Order ID")
            tree = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode="extended")
            
            # Configure columns
            column_config = {
                "ID": 60, "Date": 100, "Product": 200,
                "Reason": 150, "Status": 80, "Value": 80, "Order ID": 80
            }
            
            for col in columns:
                tree.heading(col, text=col, command=lambda c=col: self.sort_returns(tree, c))
                tree.column(col, width=column_config.get(col, 100))
            
            # Add scrollbars
            v_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
            h_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Pack everything
            tree.pack(side="left", fill="both", expand=True)
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar.pack(side="bottom", fill="x")
            
            # Context menu
            context_menu = tk.Menu(manager_window, tearoff=0)
            context_menu.add_command(label="View Details", command=lambda: self.view_return_details(tree))
            context_menu.add_command(label="Approve", command=lambda: self.update_return_status(tree, "Approved"))
            context_menu.add_command(label="Reject", command=lambda: self.update_return_status(tree, "Rejected"))
            
            def show_context_menu(event):
                try:
                    context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    context_menu.grab_release()
            
            tree.bind("<Button-3>", show_context_menu)  # Right-click
            
            # Load data
            self.refresh_returns_manager(tree)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open returns manager: {str(e)}")
    def refresh_returns_manager(self, tree):
        """Refresh the returns manager data"""
        try:
            conn = get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor(dictionary=True)
            # Get all returns with detailed information
            cursor.execute("""
                SELECT r.id, r.created_at, r.reason, r.status, r.refund_amount,
                       r.order_id, p.name as product_name
                FROM returns r
                LEFT JOIN products p ON r.product_id = p.id
                ORDER BY r.created_at DESC
            """)
            returns = cursor.fetchall()
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
            # Add returns to treeview
            for return_item in returns:
                date_str = return_item['created_at'].strftime('%Y-%m-%d %H:%M') if return_item['created_at'] else 'N/A'
                # Color coding based on status
                status = return_item.get('status', 'Unknown')
                tags = ()
                if status == 'Pending':
                    tags = ('pending',)
                elif status == 'Approved':
                    tags = ('approved',)
                elif status == 'Rejected':
                    tags = ('rejected',)
                tree.insert('', 'end', values=(
                    return_item.get('id', 'N/A'),
                    date_str,
                    return_item.get('product_name', 'Unknown'),
                    return_item.get('reason', 'No reason'),
                    status,
                    f"${return_item.get('refund_amount', 0):.2f}",
                    return_item.get('order_id', 'N/A')
                ), tags=tags)
            # Configure tags for color coding
            tree.tag_configure('pending', background='#FFF3E0')
            tree.tag_configure('approved', background='#E8F5E8')
            tree.tag_configure('rejected', background='#FFEBEE')
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh returns data: {str(e)}")
    def export_returns_csv(self):
        """Export returns data to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Export Returns Data"
            )
            
            if not filename:
                return

            import csv
            
            conn = get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor(dictionary=True)
            
            # Get returns data with filters
            date_filter = self.get_date_filter_sql(self.period_var.get())
            cursor.execute(f"""
                SELECT r.id, r.created_at, r.reason, r.status, r.refund_amount,
                       r.order_id, p.name as product_name
                FROM returns r
                LEFT JOIN products p ON r.product_id = p.id
                WHERE 1=1 {date_filter.replace('created_at', 'r.created_at')}
                ORDER BY r.created_at DESC
            """)
            returns = cursor.fetchall()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Return ID', 'Date', 'Product', 'Reason', 'Status', 'Refund Amount', 'Order ID'])
                
                for return_item in returns:
                    date_str = return_item['created_at'].strftime('%Y-%m-%d %H:%M:%S') if return_item['created_at'] else 'N/A'
                    writer.writerow([
                        return_item.get('id', 'N/A'),
                        date_str,
                        return_item.get('product_name', 'Unknown'),
                        return_item.get('reason', 'No reason'),
                        return_item.get('status', 'Unknown'),
                        return_item.get('refund_amount', 0),
                        return_item.get('order_id', 'N/A')
                    ])
            conn.close()
            messagebox.showinfo("Success", f"Returns data exported successfully: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export returns data: {str(e)}")
    def quick_process_return(self):
        """Quick return processing dialog"""
        try:
            # Create dialog window
            dialog = tk.Toplevel(self.master)
            dialog.title("Quick Return Processing")
            dialog.geometry("400x300")
            dialog.transient(self.master)
            dialog.grab_set()
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            # Create form
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill="both", expand=True)
            ttk.Label(main_frame, text="Quick Return Processing", font=("Arial", 14, "bold")).pack(pady=(0, 20))
            # Return ID
            ttk.Label(main_frame, text="Return ID:").pack(anchor="w")
            return_id_var = tk.StringVar()
            ttk.Entry(main_frame, textvariable=return_id_var, width=30).pack(fill="x", pady=(0, 10))
            # Action
            ttk.Label(main_frame, text="Action:").pack(anchor="w")
            action_var = tk.StringVar(value="Approve")
            action_combo = ttk.Combobox(main_frame, textvariable=action_var, values=["Approve", "Reject"], width=30)
            action_combo.pack(fill="x", pady=(0, 10))
            
            # Notes
            ttk.Label(main_frame, text="Notes:").pack(anchor="w")
            notes_text = tk.Text(main_frame, height=4, width=30)
            notes_text.pack(fill="x", pady=(0, 20))
            
            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x")
            
            def process_return():
                return_id = return_id_var.get().strip()
                action = action_var.get()
                notes = notes_text.get("1.0", tk.END).strip()
                
                if not return_id:
                    messagebox.showerror("Error", "Please enter a Return ID")
                    return
                
                try:
                    # Update return status in database
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        status = "Approved" if action == "Approve" else "Rejected"
                        cursor.execute("""
                            UPDATE returns 
                            SET status = %s, updated_at = NOW(), admin_notes = %s
                            WHERE id = %s
                        """, (status, notes, return_id))
                        
                        if cursor.rowcount > 0:
                            conn.commit()
                            messagebox.showinfo("Success", f"Return {return_id} has been {status.lower()}")
                            dialog.destroy()
                            self.load_returns_data()  # Refresh dashboard
                        else:
                            messagebox.showerror("Error", f"Return ID {return_id} not found")
                        
                        conn.close()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to process return: {str(e)}")
            ttk.Button(button_frame, text="Process", command=process_return).pack(side="right", padx=(5, 0))
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open quick processing dialog: {str(e)}")
    # Additional helper methods for the returns manager
    def bulk_action(self, tree, action):
        """Perform bulk action on selected returns"""
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select returns to process")
            return
        if messagebox.askyesno("Confirm", f"{action} {len(selected_items)} selected returns?"):
            try:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    for item in selected_items:
                        return_id = tree.item(item)['values'][0]
                        cursor.execute("""
                            UPDATE returns 
                            SET status = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (action, return_id))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Success", f"{len(selected_items)} returns {action.lower()}")
                    self.refresh_returns_manager(tree)
                    self.load_returns_data()  # Refresh dashboard  
            except Exception as e:
                messagebox.showerror("Error", f"Failed to perform bulk action: {str(e)}")
    def search_returns(self, tree, search_term):
        """Search returns in the manager"""
        if not search_term:
            self.refresh_returns_manager(tree)
            return
        # Filter visible items based on search term
        for item in tree.get_children():
            values = tree.item(item)['values']
            # Search in product, reason, and order ID (columns 2, 3, 6)
            if any(search_term.lower() in str(val).lower() for val in [values[2], values[3], values[6]]):
                tree.item(item, tags=('match',))
            else:
                tree.delete(item)
    def sort_returns(self, tree, column):
        """Sort returns by column"""
        # This is a placeholder for sorting functionality
        pass
    def view_return_details(self, tree):
        """View detailed return information"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a return to view details")
            return
        
        return_id = tree.item(selected[0])['values'][0]
        messagebox.showinfo("Return Details", f"Detailed view for Return ID: {return_id}\n(Feature to be implemented)")

    def update_return_status(self, tree, status):
        """Update return status from context menu"""
        selected = tree.selection()
        if not selected:
            return 
        return_id = tree.item(selected[0])['values'][0]
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE returns 
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s
                """, (status, return_id))
                
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", f"Return {return_id} status updated to {status}")
                self.refresh_returns_manager(tree)
                self.load_returns_data()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update return status: {str(e)}")

    def export_selected_returns(self, tree):
        """Export selected returns from manager"""
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select returns to export")
            return
        
        messagebox.showinfo("Export", f"Exporting {len(selected_items)} selected returns\n(Feature to be implemented)")

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
