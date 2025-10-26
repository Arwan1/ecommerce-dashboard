import tkinter as tk
from tkinter import ttk
import threading
from backend.analytics_manager import AnalyticsManager

class MainDashboard(tk.Frame):
    """
    The main dashboard screen, showing key stats and navigation buttons.
    """
    def __init__(self, master, notebook, user):
        super().__init__(master)
        self.notebook = notebook
        self.user = user
        self.analytics_manager = AnalyticsManager()

        # StringVars to hold the statistics
        self.total_orders_var = tk.StringVar(value="Loading...")
        self.pending_orders_var = tk.StringVar(value="Loading...")
        self.orders_this_week_var = tk.StringVar(value="Loading...")
        self.revenue_this_month_var = tk.StringVar(value="Loading...")
        self.pending_returns_var = tk.StringVar(value="Loading...")

        self.create_widgets()
        self.show_loading()
        # Load stats in background thread to avoid UI hanging
        self.load_stats_async()

    def create_widgets(self):
        """
        Create the widgets for the main dashboard.
        """
        # Main container frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")

        # Title
        title_label = ttk.Label(main_frame, text="Main Dashboard", font=("Helvetica", 24, "bold"))
        title_label.pack(pady=(0, 20))

        # Key Statistics Section
        stats_frame = ttk.LabelFrame(main_frame, text="Key Statistics", padding="15")
        stats_frame.pack(fill="x", expand=True, pady=(0, 20))

        # Labels with StringVars
        ttk.Label(stats_frame, textvariable=self.total_orders_var, font=("Helvetica", 14)).pack(anchor="w", pady=5)
        ttk.Label(stats_frame, textvariable=self.pending_orders_var, font=("Helvetica", 14)).pack(anchor="w", pady=5)
        ttk.Label(stats_frame, textvariable=self.orders_this_week_var, font=("Helvetica", 14)).pack(anchor="w", pady=5)
        ttk.Label(stats_frame, textvariable=self.revenue_this_month_var, font=("Helvetica", 14)).pack(anchor="w", pady=5)
        ttk.Label(stats_frame, textvariable=self.pending_returns_var, font=("Helvetica", 14)).pack(anchor="w", pady=5)

        # Quick Actions Section
        actions_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding="15")
        actions_frame.pack(fill="x", expand=True)

        # Buttons to navigate to other tabs
        button_style = {"pady": 5}

        ttk.Button(actions_frame, text="Go to Orders", command=lambda: self.notebook.select(1)).pack(fill="x", **button_style)
        ttk.Button(actions_frame, text="Go to Inventory", command=lambda: self.notebook.select(2)).pack(fill="x", **button_style)
        ttk.Button(actions_frame, text="Go to Analytics", command=lambda: self.notebook.select(3)).pack(fill="x", **button_style)
        ttk.Button(actions_frame, text="Go to Returns", command=lambda: self.notebook.select(4)).pack(fill="x", **button_style)

        if self.user.role == "admin":
            ttk.Button(actions_frame, text="Go to Users", command=lambda: self.notebook.select(5)).pack(fill="x", **button_style)

    def show_loading(self):
        """
        Show loading animation while data is being fetched.
        """
        # Create loading frame over the stats
        self.loading_frame = ttk.Frame(self)
        self.loading_frame.place(relx=0.5, rely=0.3, anchor="center")
        
        # Loading label
        self.loading_label = ttk.Label(self.loading_frame, text="Loading dashboard data...", 
                                      font=("Helvetica", 12))
        self.loading_label.pack(pady=10)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.loading_frame, mode='indeterminate', length=300)
        self.progress_bar.pack(pady=10)
        self.progress_bar.start(10)  # Start animation
        
        # Status label for individual operations
        self.status_label = ttk.Label(self.loading_frame, text="Initializing...", 
                                     font=("Helvetica", 10))
        self.status_label.pack(pady=5)

    def hide_loading(self):
        """
        Hide the loading animation.
        """
        if hasattr(self, 'loading_frame'):
            self.progress_bar.stop()
            self.loading_frame.destroy()

    def update_loading_status(self, message):
        """
        Update the loading status message.
        """
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
            self.update_idletasks()  # Force UI update

    def load_stats_async(self):
        """
        Load statistics in a background thread to avoid blocking the UI.
        """
        def load_in_background():
            try:
                self.after(0, lambda: self.update_loading_status("Loading total orders..."))
                total_orders = self.analytics_manager.get_total_orders()
                
                self.after(0, lambda: self.update_loading_status("Loading pending orders..."))
                pending_orders = self.analytics_manager.get_pending_orders()
                
                self.after(0, lambda: self.update_loading_status("Loading weekly statistics..."))
                orders_this_week = self.analytics_manager.get_orders_this_week()
                
                self.after(0, lambda: self.update_loading_status("Calculating revenue..."))
                revenue_this_month = self.analytics_manager.get_revenue_this_month()
                
                self.after(0, lambda: self.update_loading_status("Loading return claims..."))
                pending_returns = self.analytics_manager.get_pending_returns()
                
                # Update UI in main thread
                self.after(0, lambda: self.update_stats_display(
                    total_orders, pending_orders, orders_this_week, 
                    revenue_this_month, pending_returns
                ))
                
            except Exception as e:
                self.after(0, lambda: self.handle_loading_error(str(e)))
        
        # Start background thread
        thread = threading.Thread(target=load_in_background, daemon=True)
        thread.start()

    def update_stats_display(self, total_orders, pending_orders, orders_this_week, 
                           revenue_this_month, pending_returns):
        """
        Update the statistics display with loaded data.
        """
        self.total_orders_var.set(f"Total Orders: {total_orders}")
        self.pending_orders_var.set(f"Pending Orders: {pending_orders}")
        self.orders_this_week_var.set(f"Orders This Week: {orders_this_week}")
        self.revenue_this_month_var.set(f"Revenue This Month: ${revenue_this_month:,.2f}")
        self.pending_returns_var.set(f"Pending Returns: {pending_returns}")
        
        # Hide loading animation
        self.hide_loading()

    def handle_loading_error(self, error_message):
        """
        Handle errors during data loading.
        """
        self.total_orders_var.set("Total Orders: Error")
        self.pending_orders_var.set("Pending Orders: Error")
        self.orders_this_week_var.set("Orders This Week: Error")
        self.revenue_this_month_var.set("Revenue This Month: Error")
        self.pending_returns_var.set("Pending Returns: Error")
        
        print(f"Error loading dashboard stats: {error_message}")
        self.hide_loading()

    def load_stats(self):
        """
        Load statistics from the database and update the labels.
        """
        try:
            total_orders = self.analytics_manager.get_total_orders()
            pending_orders = self.analytics_manager.get_pending_orders()
            orders_this_week = self.analytics_manager.get_orders_this_week()
            revenue_this_month = self.analytics_manager.get_revenue_this_month()
            pending_returns = self.analytics_manager.get_pending_returns()

            self.total_orders_var.set(f"Total Orders: {total_orders}")
            self.pending_orders_var.set(f"Pending Orders: {pending_orders}")
            self.orders_this_week_var.set(f"Orders This Week: {orders_this_week}")
            self.revenue_this_month_var.set(f"Revenue This Month: ${revenue_this_month:,.2f}")
            self.pending_returns_var.set(f"Pending Returns: {pending_returns}")
        except Exception as e:
            self.total_orders_var.set("Total Orders: Error")
            self.pending_orders_var.set("Pending Orders: Error")
            self.orders_this_week_var.set("Orders This Week: Error")
            self.revenue_this_month_var.set("Revenue This Month: Error")
            self.pending_returns_var.set("Pending Returns: Error")
            print(f"Error loading dashboard stats: {e}")
