import tkinter as tk
from tkinter import ttk
from gui.order_dashboard import OrderDashboard
from gui.inventory_dashboard import InventoryDashboard
from gui.user_dashboard import UserDashboard
from gui.analytics_dashboard import AnalyticsDashboard
from gui.returns_dashboard import ReturnsDashboard
from gui.main_dashboard import MainDashboard

class MainWindow(tk.Frame):
    """
    Main window of the application after login.
    """
    def __init__(self, master, user):
        super().__init__(master)
        self.master = master
        self.user = user
        self.master.title("Business Management Dashboard")
        self.master.geometry("1200x800")

        self.create_widgets()

    def create_widgets(self):
        """
        Main widgets for the dashboard.
        """
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both")

        # Create the main dashboard tab first
        main_dashboard_frame = MainDashboard(self.notebook, self.notebook, self.user)
        self.notebook.add(main_dashboard_frame, text="Main")

        # Create the other dashboards as tabs
        order_frame = OrderDashboard(self.notebook)
        inventory_frame = InventoryDashboard(self.notebook)
        analytics_frame = AnalyticsDashboard(self.notebook)
        returns_frame = ReturnsDashboard(self.notebook)

        # Add tabs conditionally based on user role
        self.notebook.add(order_frame, text="Orders")
        self.notebook.add(inventory_frame, text="Inventory")
        self.notebook.add(analytics_frame, text="Analytics")
        self.notebook.add(returns_frame, text="Returns")

        if self.user.role == "admin":  # Check if the user is an admin
            user_frame = UserDashboard(self.notebook)
            self.notebook.add(user_frame, text="Users")
