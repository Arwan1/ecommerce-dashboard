import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from datetime import datetime, timedelta
import os
from backend.analytics_manager import AnalyticsManager
from database.db_operations import DBOperations
from database.db_connector import get_db_connection

# PDF generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.lib.colors import HexColor
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ ReportLab not available. PDF generation will be disabled.")

class AnalyticsDashboard(tk.Frame):
    """
    Comprehensive GUI for displaying sales analytics, forecasts, and generating PDF reports.
    """
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.analytics_manager = AnalyticsManager()
        self.db_ops = DBOperations()
        self.create_widgets()
        self.load_analytics_data()

    def create_widgets(self):
        """
        Creates widgets for the analytics dashboard.
        """
        # Title
        title_label = tk.Label(self, text="Analytics & Business Intelligence Dashboard", 
                              font=("Arial", 20, "bold"))
        title_label.pack(pady=10)

        # Main container with scrollbar
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

        # Report Generation Section (moved to top)
        self.create_report_section(scrollable_frame)

        # KPI Cards Section
        self.create_kpi_section(scrollable_frame)
        
        # Charts Section
        self.create_charts_section(scrollable_frame)
        
        # Recent Activity Section
        self.create_recent_activity_section(scrollable_frame)

    def create_kpi_section(self, parent):
        """Create Key Performance Indicator cards"""
        kpi_frame = ttk.LabelFrame(parent, text="Key Performance Indicators", padding="10")
        kpi_frame.pack(fill="x", pady=5)

        # KPI Cards Container
        cards_container = ttk.Frame(kpi_frame)
        cards_container.pack(fill="x")

        # Create KPI cards in a grid
        self.kpi_cards = {}
        kpi_data = [
            ("Total Orders", "orders", "#2196F3"),
            ("Total Revenue", "revenue", "#4CAF50"),
            ("This Week Orders", "week_orders", "#FF9800"),
            ("Monthly Revenue", "month_revenue", "#9C27B0"),
            ("New Customers", "customers", "#00BCD4"),
            ("Pending Returns", "returns", "#F44336")
        ]

        for i, (title, key, color) in enumerate(kpi_data):
            row = i // 3
            col = i % 3
            
            card_frame = tk.Frame(cards_container, bg=color, relief="raised", bd=2)
            card_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
            
            # Title
            title_label = tk.Label(card_frame, text=title, font=("Arial", 10, "bold"), 
                                 bg=color, fg="white")
            title_label.pack(pady=(10, 5))
            
            # Value
            value_label = tk.Label(card_frame, text="Loading...", font=("Arial", 16, "bold"), 
                                 bg=color, fg="white")
            value_label.pack(pady=(0, 10))
            
            self.kpi_cards[key] = value_label

        # Configure grid weights
        for i in range(3):
            cards_container.columnconfigure(i, weight=1)

    def create_charts_section(self, parent):
        """Create charts section with matplotlib"""
        charts_frame = ttk.LabelFrame(parent, text="Analytics Charts", padding="10")
        charts_frame.pack(fill="both", expand=True, pady=5)

        # Create matplotlib figure
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle('Business Analytics Overview', fontsize=16, fontweight='bold')
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, charts_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_recent_activity_section(self, parent):
        """Create recent activity section"""
        activity_frame = ttk.LabelFrame(parent, text="Recent Activity", padding="10")
        activity_frame.pack(fill="x", pady=5)

        # Recent orders treeview
        columns = ("Date", "Customer", "Amount", "Status")
        self.activity_tree = ttk.Treeview(activity_frame, columns=columns, show="headings", height=6)
        
        for col in columns:
            self.activity_tree.heading(col, text=col)
            self.activity_tree.column(col, width=150)
        
        self.activity_tree.pack(fill="x", pady=5)

    def create_report_section(self, parent):
        """Create report generation section at the top"""
        report_frame = ttk.LabelFrame(parent, text="📊 Analytics Control Panel", padding="15")
        report_frame.pack(fill="x", pady=(0, 10))

        # Main controls frame
        controls_frame = ttk.Frame(report_frame)
        controls_frame.pack(fill="x", pady=(0, 10))

        # First row - Time period and report type
        row1_frame = ttk.Frame(controls_frame)
        row1_frame.pack(fill="x", pady=(0, 10))

        # Date range selection (larger and more prominent)
        date_frame = ttk.LabelFrame(row1_frame, text="📅 Time Period", padding="8")
        date_frame.pack(side="left", padx=(0, 15))
        
        self.period_var = tk.StringVar(value="Last 30 Days")
        period_combo = ttk.Combobox(date_frame, textvariable=self.period_var, width=20, font=("Arial", 10))
        period_combo['values'] = ("Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "All Time")
        period_combo.pack(pady=2)
        
        # Bind period change to refresh data
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.load_analytics_data())

        # Report type selection
        type_frame = ttk.LabelFrame(row1_frame, text="📋 Report Type", padding="8")
        type_frame.pack(side="left", padx=(0, 15))
        
        self.report_type_var = tk.StringVar(value="Summary Report")
        type_combo = ttk.Combobox(type_frame, textvariable=self.report_type_var, width=20, font=("Arial", 10))
        type_combo['values'] = ("Summary Report", "Sales Report", "Customer Report", "Inventory Report")
        type_combo.pack(pady=2)

        # Quick stats display
        stats_frame = ttk.LabelFrame(row1_frame, text="📈 Quick Stats", padding="8")
        stats_frame.pack(side="left", fill="x", expand=True)
        
        self.quick_stats_label = ttk.Label(stats_frame, text="Select a time period to view statistics", 
                                          font=("Arial", 9), foreground="#666666")
        self.quick_stats_label.pack(pady=2)

        # Second row - Action buttons (larger and more prominent)
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill="x")

        # Create larger, more prominent buttons
        self.refresh_btn = tk.Button(buttons_frame, text="🔄 Refresh Data", 
                                    command=self.load_analytics_data, 
                                    bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                    padx=20, pady=8, relief="raised", borderwidth=2)
        self.refresh_btn.pack(side="left", padx=(0, 10))

        if PDF_AVAILABLE:
            self.pdf_btn = tk.Button(buttons_frame, text="📄 Generate PDF Report", 
                                   command=self.generate_pdf_report, 
                                   bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                   padx=20, pady=8, relief="raised", borderwidth=2)
            self.pdf_btn.pack(side="left", padx=(0, 10))
        else:
            self.install_btn = tk.Button(buttons_frame, text="📦 Install ReportLab for PDF", 
                                       command=self.install_reportlab, 
                                       bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
                                       padx=20, pady=8, relief="raised", borderwidth=2)
            self.install_btn.pack(side="left", padx=(0, 10))

        self.export_btn = tk.Button(buttons_frame, text="📊 Export to CSV", 
                                   command=self.export_to_csv, 
                                   bg="#9C27B0", fg="white", font=("Arial", 10, "bold"),
                                   padx=20, pady=8, relief="raised", borderwidth=2)
        self.export_btn.pack(side="left", padx=(0, 10))

        # Add a help button
        self.help_btn = tk.Button(buttons_frame, text="❓ Help", 
                                 command=self.show_help, 
                                 bg="#607D8B", fg="white", font=("Arial", 10, "bold"),
                                 padx=20, pady=8, relief="raised", borderwidth=2)
        self.help_btn.pack(side="right")

        # Add separator line
        separator = ttk.Separator(report_frame, orient='horizontal')
        separator.pack(fill="x", pady=(10, 0))

    def load_analytics_data(self):
        """Load analytics data in background thread"""
        def load_in_background():
            try:
                # Get selected time period
                time_period = self.period_var.get()
                
                # Get KPI data
                kpi_data = {
                    'orders': self.analytics_manager.get_total_orders(),
                    'revenue': self.analytics_manager.get_total_revenue(),
                    'week_orders': self.analytics_manager.get_orders_this_week(),
                    'month_revenue': self.analytics_manager.get_revenue_this_month(),
                    'customers': self.analytics_manager.get_new_customers(),
                    'returns': self.analytics_manager.get_pending_returns()
                }
                
                # Get chart data with time period filter
                chart_data = self.get_chart_data(time_period)
                
                # Get recent activity
                recent_orders = self.get_recent_orders()
                
                # Update UI in main thread
                self.after(0, lambda: self.update_dashboard(kpi_data, chart_data, recent_orders))
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to load data: {error_msg}"))
        
        # Show loading state
        for card in self.kpi_cards.values():
            card.config(text="Loading...")
        
        thread = threading.Thread(target=load_in_background)
        thread.daemon = True
        thread.start()

    def update_dashboard(self, kpi_data, chart_data, recent_orders):
        """Update dashboard with loaded data"""
        # Update KPI cards
        self.kpi_cards['orders'].config(text=f"{kpi_data['orders']:,}")
        self.kpi_cards['revenue'].config(text=f"${kpi_data['revenue']:,.2f}")
        self.kpi_cards['week_orders'].config(text=f"{kpi_data['week_orders']:,}")
        self.kpi_cards['month_revenue'].config(text=f"${kpi_data['month_revenue']:,.2f}")
        self.kpi_cards['customers'].config(text=f"{kpi_data['customers']:,}")
        self.kpi_cards['returns'].config(text=f"{kpi_data['returns']:,}")
        
        # Update quick stats in control panel
        self.update_quick_stats(chart_data)
        
        # Update charts
        self.update_charts(chart_data)
        
        # Update recent activity
        self.update_recent_activity(recent_orders)

    def update_quick_stats(self, chart_data):
        """Update the quick stats display in the control panel"""
        try:
            time_period = self.period_var.get()
            
            # Calculate stats from chart data
            total_orders = 0
            total_revenue = 0
            
            if chart_data.get('monthly_sales'):
                for period_data in chart_data['monthly_sales']:
                    total_orders += period_data.get('orders', 0)
                    total_revenue += period_data.get('revenue', 0) or 0
            
            # Update the quick stats label
            if total_orders > 0:
                avg_order_value = total_revenue / total_orders
                stats_text = f"{time_period}: {total_orders:,} orders • ${total_revenue:,.2f} revenue • ${avg_order_value:.2f} avg"
            else:
                stats_text = f"{time_period}: No data available"
            
            self.quick_stats_label.config(text=stats_text, foreground="#2196F3")
            
        except Exception as e:
            self.quick_stats_label.config(text="Error calculating stats", foreground="#F44336")
            print(f"Quick stats error: {e}")

    def get_chart_data(self, time_period=None):
        """Get data for charts with optional time period filter"""
        conn = get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("📊 Loading chart data...")
            
            # Get date filter based on time period
            if time_period is None:
                time_period = self.period_var.get()
            date_filter = self.get_date_filter_sql(time_period)
            
            # Sales by month - adjusted for time period
            try:
                if time_period == "Last 7 Days":
                    # Daily data for last 7 days
                    cursor.execute(f"""
                        SELECT 
                            DATE(created_at) as period,
                            COUNT(*) as orders, 
                            SUM(total_price) as revenue
                        FROM orders 
                        WHERE 1=1 {date_filter}
                        GROUP BY DATE(created_at)
                        ORDER BY DATE(created_at)
                    """)
                    monthly_sales = cursor.fetchall()
                elif time_period == "Last 30 Days":
                    # Daily data for last 30 days
                    cursor.execute(f"""
                        SELECT 
                            DATE(created_at) as period,
                            COUNT(*) as orders, 
                            SUM(total_price) as revenue
                        FROM orders 
                        WHERE 1=1 {date_filter}
                        GROUP BY DATE(created_at)
                        ORDER BY DATE(created_at)
                    """)
                    monthly_sales = cursor.fetchall()
                else:
                    # Monthly data for longer periods - Simplified approach
                    cursor.execute(f"""
                        SELECT 
                            YEAR(created_at) as year,
                            MONTH(created_at) as month,
                            COUNT(*) as orders, 
                            SUM(total_price) as revenue
                        FROM orders 
                        WHERE 1=1 {date_filter}
                        GROUP BY YEAR(created_at), MONTH(created_at)
                        ORDER BY YEAR(created_at), MONTH(created_at)
                    """)
                    raw_monthly_sales = cursor.fetchall()
                    # Format the period in Python
                    monthly_sales = []
                    for row in raw_monthly_sales:
                        formatted_row = {
                            'period': f"{row['year']}-{row['month']:02d}",
                            'orders': row['orders'],
                            'revenue': row['revenue']
                        }
                        monthly_sales.append(formatted_row)
                print(f"   Sales data: {len(monthly_sales)} periods for {time_period}")
            except Exception as e:
                print(f"   Error in sales query: {e}")
                monthly_sales = []
            
            # Top products - with time filter
            try:
                cursor.execute(f"""
                    SELECT p.name, SUM(oi.quantity) as total_sold
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE 1=1 {date_filter.replace('created_at', 'o.created_at')}
                    GROUP BY p.id, p.name
                    ORDER BY total_sold DESC
                    LIMIT 10
                """)
                top_products = cursor.fetchall()
                print(f"   Top products data: {len(top_products)} products for {time_period}")
            except Exception as e:
                print(f"   Error in top products query: {e}")
                top_products = []
            
            # Order status distribution - with time filter
            try:
                cursor.execute(f"""
                    SELECT 'Processing' as status, 
                           COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) as count
                    FROM orders
                    WHERE 1=1 {date_filter}
                    UNION ALL
                    SELECT 'Shipped' as status,
                           COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
                                      AND created_at < DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) as count
                    FROM orders
                    WHERE 1=1 {date_filter}
                    UNION ALL
                    SELECT 'Delivered' as status,
                           COUNT(CASE WHEN created_at < DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as count
                    FROM orders
                    WHERE 1=1 {date_filter}
                """)
                order_status = cursor.fetchall()
                # Filter out zero counts for cleaner display
                order_status = [item for item in order_status if item['count'] > 0]
                print(f"   Order status data: {len(order_status)} statuses for {time_period}")
            except Exception as e:
                print(f"   Error in order status query: {e}")
                order_status = []
            
            return {
                'monthly_sales': monthly_sales,
                'top_products': top_products,
                'order_status': order_status,
                'time_period': time_period
            }
            
        except Exception as e:
            print(f"📊 Chart data error: {e}")
            return {}
        finally:
            conn.close()
    
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

    def update_charts(self, chart_data):
        """Update matplotlib charts"""
        print("📈 Updating charts...")
        
        # Get time period for titles
        time_period = chart_data.get('time_period', 'All Time')
        
        # Clear all subplots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.clear()

        # Chart 1: Sales Trend (Monthly or Daily based on period)
        if chart_data.get('monthly_sales') and len(chart_data['monthly_sales']) > 0:
            try:
                periods = [item['period'] for item in chart_data['monthly_sales']]
                revenues = [float(item['revenue'] or 0) for item in chart_data['monthly_sales']]
                
                self.ax1.plot(periods, revenues, marker='o', linewidth=2, markersize=6, color='#2196F3')
                
                # Dynamic title based on time period
                if time_period in ["Last 7 Days", "Last 30 Days"]:
                    title = f'Daily Revenue Trend ({time_period})'
                else:
                    title = f'Monthly Revenue Trend ({time_period})'
                
                self.ax1.set_title(title, fontweight='bold')
                self.ax1.set_ylabel('Revenue ($)')
                self.ax1.tick_params(axis='x', rotation=45)
                self.ax1.grid(True, alpha=0.3)
                print("   ✅ Revenue chart updated")
            except Exception as e:
                print(f"   ❌ Revenue chart error: {e}")
                self.ax1.text(0.5, 0.5, 'No revenue data available', 
                             ha='center', va='center', transform=self.ax1.transAxes)
                self.ax1.set_title(f'Revenue Trend ({time_period})', fontweight='bold')
        else:
            self.ax1.text(0.5, 0.5, 'No revenue data available', 
                         ha='center', va='center', transform=self.ax1.transAxes)
            self.ax1.set_title(f'Revenue Trend ({time_period})', fontweight='bold')

        # Chart 2: Top Products
        if chart_data.get('top_products') and len(chart_data['top_products']) > 0:
            try:
                products = [item['name'][:15] + '...' if len(item['name']) > 15 else item['name'] 
                           for item in chart_data['top_products'][:8]]
                quantities = [int(item['total_sold'] or 0) for item in chart_data['top_products'][:8]]
                
                bars = self.ax2.bar(products, quantities, color='#4CAF50', alpha=0.7)
                self.ax2.set_title(f'Top Selling Products ({time_period})', fontweight='bold')
                self.ax2.set_ylabel('Quantity Sold')
                self.ax2.tick_params(axis='x', rotation=45)
                
                # Add value labels on bars
                for bar, qty in zip(bars, quantities):
                    height = bar.get_height()
                    self.ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                                f'{qty}', ha='center', va='bottom', fontsize=8)
                print("   ✅ Top products chart updated")
            except Exception as e:
                print(f"   ❌ Top products chart error: {e}")
                self.ax2.text(0.5, 0.5, 'No product data available', 
                             ha='center', va='center', transform=self.ax2.transAxes)
                self.ax2.set_title(f'Top Selling Products ({time_period})', fontweight='bold')
        else:
            self.ax2.text(0.5, 0.5, 'No product data available', 
                         ha='center', va='center', transform=self.ax2.transAxes)
            self.ax2.set_title(f'Top Selling Products ({time_period})', fontweight='bold')

        # Chart 3: Order Status Distribution
        if chart_data.get('order_status') and len(chart_data['order_status']) > 0:
            try:
                statuses = [item['status'] for item in chart_data['order_status']]
                counts = [int(item['count'] or 0) for item in chart_data['order_status']]
                colors = ['#FF9800', '#2196F3', '#4CAF50']
                
                if sum(counts) > 0:  # Only create pie chart if there's data
                    wedges, texts, autotexts = self.ax3.pie(counts, labels=statuses, autopct='%1.1f%%', 
                                                           colors=colors[:len(counts)], startangle=90)
                    self.ax3.set_title(f'Order Status Distribution ({time_period})', fontweight='bold')
                    print("   ✅ Order status chart updated")
                else:
                    self.ax3.text(0.5, 0.5, 'No order status data', 
                                 ha='center', va='center', transform=self.ax3.transAxes)
                    self.ax3.set_title(f'Order Status Distribution ({time_period})', fontweight='bold')
            except Exception as e:
                print(f"   ❌ Order status chart error: {e}")
                self.ax3.text(0.5, 0.5, 'No order status data', 
                             ha='center', va='center', transform=self.ax3.transAxes)
                self.ax3.set_title(f'Order Status Distribution ({time_period})', fontweight='bold')
        else:
            self.ax3.text(0.5, 0.5, 'No order status data', 
                         ha='center', va='center', transform=self.ax3.transAxes)
            self.ax3.set_title(f'Order Status Distribution ({time_period})', fontweight='bold')

        # Chart 4: Orders Count (Daily/Monthly based on period)
        if chart_data.get('monthly_sales') and len(chart_data['monthly_sales']) > 0:
            try:
                periods = [item['period'] for item in chart_data['monthly_sales']]
                orders = [int(item['orders'] or 0) for item in chart_data['monthly_sales']]
                
                self.ax4.bar(periods, orders, color='#9C27B0', alpha=0.7)
                
                # Dynamic title based on time period
                if time_period in ["Last 7 Days", "Last 30 Days"]:
                    title = f'Daily Orders Count ({time_period})'
                else:
                    title = f'Monthly Orders Count ({time_period})'
                
                self.ax4.set_title(title, fontweight='bold')
                self.ax4.set_ylabel('Number of Orders')
                self.ax4.tick_params(axis='x', rotation=45)
                print("   ✅ Orders count chart updated")
            except Exception as e:
                print(f"   ❌ Orders count chart error: {e}")
                self.ax4.text(0.5, 0.5, 'No order count data', 
                             ha='center', va='center', transform=self.ax4.transAxes)
                self.ax4.set_title(f'Orders Count ({time_period})', fontweight='bold')
        else:
            self.ax4.text(0.5, 0.5, 'No order count data', 
                         ha='center', va='center', transform=self.ax4.transAxes)
            self.ax4.set_title(f'Orders Count ({time_period})', fontweight='bold')
            self.ax4.set_title('Monthly Orders Count', fontweight='bold')

        # Adjust layout and refresh
        try:
            self.fig.tight_layout()
            self.canvas.draw()
            print("📈 Charts update completed")
        except Exception as e:
            print(f"📈 Chart rendering error: {e}")

    def get_recent_orders(self):
        """Get recent orders for activity section"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT created_at, customer_name, total_price,
                       CASE 
                           WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 'Processing'
                           WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Shipped'
                           ELSE 'Delivered'
                       END as status
                FROM orders 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            return cursor.fetchall()
        finally:
            conn.close()

    def update_recent_activity(self, orders):
        """Update recent activity treeview"""
        # Clear existing items
        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
        
        # Add recent orders
        for order in orders:
            date_str = order['created_at'].strftime('%Y-%m-%d %H:%M') if order['created_at'] else 'N/A'
            self.activity_tree.insert("", "end", values=(
                date_str,
                order.get('customer_name', 'Unknown'),
                f"${order.get('total_price', 0):.2f}",
                order.get('status', 'Unknown')
            ))

    def generate_pdf_report(self):
        """Generate comprehensive PDF report"""
        if not PDF_AVAILABLE:
            messagebox.showerror("Error", "ReportLab is required for PDF generation.")
            return

        try:
            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save Analytics Report"
            )
            
            if not filename:
                return

            # Get current data
            kpi_data = {
                'orders': self.analytics_manager.get_total_orders(),
                'revenue': self.analytics_manager.get_total_revenue(),
                'week_orders': self.analytics_manager.get_orders_this_week(),
                'month_revenue': self.analytics_manager.get_revenue_this_month(),
                'customers': self.analytics_manager.get_new_customers(),
                'returns': self.analytics_manager.get_pending_returns()
            }
            
            chart_data = self.get_chart_data()
            recent_orders = self.get_recent_orders()

            # Create PDF
            self.create_pdf_report(filename, kpi_data, chart_data, recent_orders)
            
            messagebox.showinfo("Success", f"Report generated successfully: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")

    def create_pdf_report(self, filename, kpi_data, chart_data, recent_orders):
        """Create the actual PDF report"""
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#2196F3'),
            spaceAfter=30
        )
        story.append(Paragraph("Business Analytics Report", title_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # KPI Summary Table
        story.append(Paragraph("Key Performance Indicators", styles['Heading2']))
        kpi_table_data = [
            ['Metric', 'Value'],
            ['Total Orders', f"{kpi_data['orders']:,}"],
            ['Total Revenue', f"${kpi_data['revenue']:,.2f}"],
            ['Orders This Week', f"{kpi_data['week_orders']:,}"],
            ['Revenue This Month', f"${kpi_data['month_revenue']:,.2f}"],
            ['New Customers (30 days)', f"{kpi_data['customers']:,}"],
            ['Pending Returns', f"{kpi_data['returns']:,}"]
        ]
        
        kpi_table = Table(kpi_table_data, colWidths=[3*inch, 2*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 20))

        # Recent Orders Table
        if recent_orders:
            story.append(Paragraph("Recent Orders", styles['Heading2']))
            orders_data = [['Date', 'Customer', 'Amount', 'Status']]
            for order in recent_orders[:10]:
                date_str = order['created_at'].strftime('%Y-%m-%d') if order['created_at'] else 'N/A'
                orders_data.append([
                    date_str,
                    order.get('customer_name', 'Unknown')[:20],
                    f"${order.get('total_price', 0):.2f}",
                    order.get('status', 'Unknown')
                ])
            
            orders_table = Table(orders_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch])
            orders_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            story.append(orders_table)

        # Build PDF
        doc.build(story)

    def export_to_csv(self):
        """Export analytics data to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Export Analytics Data"
            )
            
            if not filename:
                return

            import csv
            
            # Get data
            recent_orders = self.get_recent_orders()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Date', 'Customer', 'Amount', 'Status'])
                
                for order in recent_orders:
                    date_str = order['created_at'].strftime('%Y-%m-%d %H:%M:%S') if order['created_at'] else 'N/A'
                    writer.writerow([
                        date_str,
                        order.get('customer_name', 'Unknown'),
                        order.get('total_price', 0),
                        order.get('status', 'Unknown')
                    ])
            
            messagebox.showinfo("Success", f"Data exported successfully: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def install_reportlab(self):
        """Install ReportLab package"""
        try:
            import subprocess
            import sys
            
            messagebox.showinfo("Installing", "Installing ReportLab... This may take a moment.")
            
            result = subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "ReportLab installed successfully! Please restart the application.")
            else:
                messagebox.showerror("Error", f"Failed to install ReportLab: {result.stderr}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Installation failed: {str(e)}")

    def show_help(self):
        """Show help dialog with usage instructions"""
        help_text = """
📊 Analytics Dashboard Help

🔧 Control Panel:
• Time Period: Select date range for all charts and statistics
• Report Type: Choose the type of report to generate
• Refresh Data: Reload all analytics data
• Generate PDF: Create a professional PDF report
• Export CSV: Save data to spreadsheet format

📈 Charts:
• Revenue Trend: Shows sales over time (daily/monthly based on period)
• Top Products: Best-selling items for selected period
• Order Status: Distribution of order statuses
• Order Count: Number of orders over time

💡 Tips:
• Charts automatically update when you change the time period
• PDF reports include all current data and charts
• CSV export contains recent order details
• Use different time periods to analyze trends

🎯 Quick Actions:
• Change time period to see historical data
• Click refresh if data seems outdated
• Generate reports for stakeholder meetings
• Export data for further analysis
        """
        
        help_window = tk.Toplevel(self.master)
        help_window.title("Analytics Dashboard Help")
        help_window.geometry("500x600")
        help_window.resizable(False, False)
        
        # Center the window
        help_window.transient(self.master)
        help_window.grab_set()
        
        # Create scrolled text widget
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 10), 
                             bg="#f8f9fa", relief="flat", padx=15, pady=15)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")
        
        # Close button
        close_btn = tk.Button(help_window, text="Close", command=help_window.destroy,
                             bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                             padx=30, pady=5)
        close_btn.pack(pady=(0, 20))
