import tkinter as tk
from tkinter import ttk, messagebox

class OrderDashboard(tk.Frame):
    """
    GUI for managing orders.
    """
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        """
        Creates widgets for the order dashboard.
        """
        # Title
        self.title_label = tk.Label(self, text="Order Dashboard", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=10)

        # Treeview to display orders
        self.tree = ttk.Treeview(self, columns=("ID", "Product", "Buyer", "Total"), show="headings")
        self.tree.heading("ID", text="Order ID")
        self.tree.heading("Product", text="Product")
        self.tree.heading("Buyer", text="Buyer Info")
        self.tree.heading("Total", text="Total Price")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Add, Edit, Delete buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10)

        self.add_button = tk.Button(self.button_frame, text="Add Order", command=self.add_order)
        self.add_button.pack(side="left", padx=10)

        self.edit_button = tk.Button(self.button_frame, text="Edit Order", command=self.edit_order)
        self.edit_button.pack(side="left", padx=10)

        self.delete_button = tk.Button(self.button_frame, text="Delete Order", command=self.delete_order)
        self.delete_button.pack(side="left", padx=10)

        # Back button
        self.back_button = tk.Button(self, text="Back", command=self.go_back)
        self.back_button.pack(pady=10)

    def add_order(self):
        """
        Handles adding a new order.
        """
        # Example: Open a new window or dialog for adding an order
        messagebox.showinfo("Add Order", "Add Order functionality goes here.")

    def edit_order(self):
        """
        Handles editing an existing order.
        """
        # Example: Check if an order is selected
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Edit Order", "Please select an order to edit.")
            return

        # Example: Open a new window or dialog for editing the selected order
        messagebox.showinfo("Edit Order", "Edit Order functionality goes here.")

    def delete_order(self):
        """
        Handles deleting an order.
        """
        # Example: Check if an order is selected
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Delete Order", "Please select an order to delete.")
            return

        # Example: Confirm deletion
        confirm = messagebox.askyesno("Delete Order", "Are you sure you want to delete this order?")
        if confirm:
            # Example: Remove the selected order from the treeview
            self.tree.delete(selected_item)
            messagebox.showinfo("Delete Order", "Order deleted successfully.")

    def go_back(self):
        """
        Returns to the previous window.
        """
        self.destroy()
        self.master.show_login_window()  # Replace with the appropriate method to go back