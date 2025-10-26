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
        self.db_ops = DBOperations()
        
        # Create UI
        self.create_widgets()
        
        # Load initial data
        self.load_returns_data()

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
        
        # Charts Section
        self.create_charts_section(scrollable_frame)
        
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

    def create_charts_section(self, parent):
        """Create charts section with matplotlib"""
        charts_frame = ttk.LabelFrame(parent, text="📊 Returns Analytics Charts", padding="10")
        charts_frame.pack(fill="both", expand=True, pady=5)

        # Create matplotlib figure with subplots matching the image layout
        # Increased figure size and adjusted layout for better spacing
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        self.fig.suptitle('Returns Analytics Dashboard', fontsize=16, fontweight='bold')
        
        # Adjust layout with more space for bottom charts
        # rect=[left, bottom, right, top] - increased bottom margin and adjusted top
        self.fig.tight_layout(rect=[0.05, 0.08, 0.95, 0.92], pad=3.0, h_pad=3.0, w_pad=2.0)
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, charts_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

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
                # Get selected filters
                time_period = self.period_var.get()
                view_type = self.view_type_var.get()
                
                # Get returns data
                returns_data = self.get_returns_data(time_period, view_type)
                
                # Get chart data
                chart_data = self.get_returns_chart_data(time_period)
                
                # Update UI in main thread
                self.after(0, lambda: self.update_dashboard(returns_data, chart_data))
            except Exception as e:
                error_msg = str(e)
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
        conn = get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(dictionary=True)
            date_filter = self.get_date_filter_sql(time_period)
            
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

            # 3. Supplier return analysis (bottom-left bar chart)
            try:
                cursor.execute(f"""
                    SELECT p.supplier, COUNT(*) as return_count
                    FROM returns r
                    JOIN products p ON r.product_id = p.id
                    WHERE 1=1 {date_filter.replace('created_at', 'r.created_at')}
                    GROUP BY p.supplier
                    ORDER BY return_count DESC
                    LIMIT 10
                """)
                supplier_returns = cursor.fetchall()
            except Exception as e:
                print(f"Error in supplier returns query: {e}")
                supplier_returns = []

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
        
        # Get time period for titles
        time_period = chart_data.get('time_period', 'All Time')
        
        # Clear all subplots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
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

        # Chart 3: Supplier Returns Analysis (bottom-left)
        if chart_data.get('supplier_returns') and len(chart_data['supplier_returns']) > 0:
            try:
                suppliers = [item['supplier'][:15] + '...' if len(item['supplier']) > 15 else item['supplier'] 
                           for item in chart_data['supplier_returns']]
                counts = [item['return_count'] for item in chart_data['supplier_returns']]
                
                bars = self.ax3.bar(suppliers, counts, color='#9C27B0', alpha=0.7)
                self.ax3.set_title(f'Returns by Supplier ({time_period})', fontweight='bold')
                self.ax3.set_ylabel('Return Count')
                self.ax3.tick_params(axis='x', rotation=45)
                
                # Add value labels on bars
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    self.ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                f'{count}', ha='center', va='bottom', fontsize=8)
                print("   ✅ Supplier returns chart updated")
            except Exception as e:
                print(f"   ❌ Supplier returns error: {e}")
                self.ax3.text(0.5, 0.5, 'No supplier data available', 
                             ha='center', va='center', transform=self.ax3.transAxes)
                self.ax3.set_title(f'Returns by Supplier ({time_period})', fontweight='bold')
        else:
            self.ax3.text(0.5, 0.5, 'No supplier data available', 
                         ha='center', va='center', transform=self.ax3.transAxes)
            self.ax3.set_title(f'Returns by Supplier ({time_period})', fontweight='bold')

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
        self.fig.tight_layout(rect=[0.05, 0.08, 0.95, 0.92], pad=3.0, h_pad=3.0, w_pad=2.0)
        self.canvas.draw()
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