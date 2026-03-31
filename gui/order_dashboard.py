import tkinter as tk
from tkinter import ttk, messagebox
import threading
from backend.order_service import OrderService
from database.db_operations import DBOperations
from datetime import datetime, timedelta
from utils.csv_handler import CSVHandler

class OrderDashboard(tk.Frame):
    """
    GUI for managing orders.
    """
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.db_ops = DBOperations()
        self.order_rows = []
        self.create_widgets()
        self.load_orders_async()  # Load orders asynchronously

    def create_widgets(self):
        """
        Creates widgets for the order dashboard.
        """
        # Create main container - no tabs needed, just orders
        self.orders_frame = ttk.Frame(self)
        self.orders_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_orders_tab()

    def create_orders_tab(self):
        """
        Create the orders list tab.
        """
        # Title
        self.title_label = tk.Label(self.orders_frame, text="Order Dashboard", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=10)

        search_frame = ttk.Frame(self.orders_frame)
        search_frame.pack(fill="x", padx=10, pady=(0, 5))

        ttk.Label(search_frame, text="Search Orders:").pack(side="left")
        self.order_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.order_search_var, width=40)
        search_entry.pack(side="left", padx=(8, 8))
        search_entry.bind("<KeyRelease>", lambda event: self.apply_order_filter())

        ttk.Button(search_frame, text="Clear", command=self.clear_order_search).pack(side="left")

        # Frame for Treeview and scrollbars
        tree_frame = ttk.Frame(self.orders_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview to display orders
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Customer", "Date", "Total", "Items", "Status"), show="headings")
        self.tree.heading("ID", text="Order ID")
        self.tree.heading("Customer", text="Customer")
        self.tree.heading("Date", text="Order Date")
        self.tree.heading("Total", text="Total Price")
        self.tree.heading("Items", text="Items")
        self.tree.heading("Status", text="Status")

        # Configure column widths
        self.tree.column("ID", width=80)
        self.tree.column("Customer", width=150)
        self.tree.column("Date", width=120)
        self.tree.column("Total", width=100)
        self.tree.column("Items", width=180)
        self.tree.column("Status", width=100)

        # Configure status-based row colors
        self.tree.tag_configure('Preparing', background='#ffcdd2')  # Light red
        self.tree.tag_configure('Dispatched', background='#fff3cd')  # Light yellow  
        self.tree.tag_configure('Delivered', background='#d4edda')  # Light green

        # Add vertical and horizontal scrollbars for the treeview
        vscrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hscrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)

        # Grid placement for proper alignment
        self.tree.grid(row=0, column=0, sticky="nsew")
        vscrollbar.grid(row=0, column=1, sticky="ns")
        hscrollbar.grid(row=1, column=0, sticky="ew")

        # Make the treeview expandable
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Add, Edit, Delete buttons
        self.button_frame = tk.Frame(self.orders_frame)
        self.button_frame.pack(pady=10)

        self.add_button = tk.Button(
            self.button_frame, text="➕ Add Order", command=self.add_order,
            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
            padx=20, pady=8, relief="raised", borderwidth=2
        )
        self.add_button.pack(side="left", padx=(0, 10))

        self.refresh_button = tk.Button(
            self.button_frame, text="🔄 Refresh", command=self.load_orders_async,
            bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
            padx=20, pady=8, relief="raised", borderwidth=2
        )
        self.refresh_button.pack(side="left", padx=(0, 10))

        self.import_button = tk.Button(
            self.button_frame, text="📥 Import CSV", command=self.import_orders_csv,
            bg="#00897B", fg="white", font=("Arial", 10, "bold"),
            padx=20, pady=8, relief="raised", borderwidth=2
        )
        self.import_button.pack(side="left", padx=(0, 10))

        self.export_button = tk.Button(
            self.button_frame, text="📤 Export CSV", command=self.export_orders_csv,
            bg="#3F51B5", fg="white", font=("Arial", 10, "bold"),
            padx=20, pady=8, relief="raised", borderwidth=2
        )
        self.export_button.pack(side="left", padx=(0, 10))

        self.edit_button = tk.Button(
            self.button_frame, text="👁️ View Details", command=self.view_order_details,
            bg="#9C27B0", fg="white", font=("Arial", 10, "bold"),
            padx=20, pady=8, relief="raised", borderwidth=2
        )
        self.edit_button.pack(side="left", padx=(0, 10))

        self.edit_details_button = tk.Button(
            self.button_frame, text="✏️ Edit Details", command=self.edit_order_details,
            bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
            padx=20, pady=8, relief="raised", borderwidth=2
        )
        self.edit_details_button.pack(side="left", padx=(0, 10))

        self.delete_button = tk.Button(
            self.button_frame, text="🗑️ Delete Order", command=self.delete_order,
            bg="#F44336", fg="white", font=("Arial", 10, "bold"),
            padx=20, pady=8, relief="raised", borderwidth=2
        )
        self.delete_button.pack(side="left", padx=(0, 10))

    def show_loading_orders(self):
        """
        Show loading indicator for orders.
        """
        # Clear existing items and show loading
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree.insert("", "end", values=("", "Loading orders...", "", "", "", ""))

    def load_orders_async(self):
        """
        Load orders in background thread.
        """
        self.show_loading_orders()
        
        def load_in_background():
            try:
                orders = self.db_ops.get_all_orders()
                # Update UI in main thread
                self.after(0, lambda: self.display_orders(orders))
            except Exception as e:
                self.after(0, lambda: self.handle_orders_error(str(e)))
        
        thread = threading.Thread(target=load_in_background, daemon=True)
        thread.start()

    def display_orders(self, orders):
        """
        Display the loaded orders in the treeview.
        """
        self.order_rows = []

        for order in orders:
            order_id = order['id']
            customer_name = order.get('customer_name', 'Unknown Customer')
            total_price = order['total_price']
            created_at = order['created_at']
            status = order.get('status', 'Preparing')  # Default to Preparing if no status
            
            # Get order items for this order
            items_text = self.get_order_items_text(order_id)
            
            # Format date
            date_str = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "N/A"

            values = (
                order_id,
                customer_name,
                date_str,
                f"${total_price:.2f}",
                items_text,
                status
            )
            search_text = " ".join(str(value).lower() for value in values)

            self.order_rows.append({
                "values": values,
                "tags": (status,),
                "search_text": search_text,
            })

        self.apply_order_filter()

    def handle_orders_error(self, error_message):
        """
        Handle error when loading orders.
        """
        self.order_rows = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.tree.insert("", "end", values=("", f"Error: {error_message}", "", "", "", ""))
        messagebox.showerror("Error", f"Failed to load orders: {error_message}")

    def render_order_rows(self, rows):
        """Render order rows into the treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not rows:
            empty_message = "No matching orders found" if self.order_search_var.get().strip() else "No orders found"
            self.tree.insert("", "end", values=("", empty_message, "", "", "", ""))
            return

        for row in rows:
            self.tree.insert("", "end", values=row["values"], tags=row["tags"])

    def apply_order_filter(self):
        """Filter orders using the current search term."""
        search_term = self.order_search_var.get().strip().lower()
        if not search_term:
            self.render_order_rows(self.order_rows)
            return

        filtered_rows = [
            row for row in self.order_rows
            if search_term in row["search_text"]
        ]
        self.render_order_rows(filtered_rows)

    def clear_order_search(self):
        """Reset the order search field."""
        self.order_search_var.set("")
        self.apply_order_filter()

    def get_order_items_text(self, order_id):
        """
        Get a summary of items in an order.
        """
        try:
            items = self.db_ops.get_order_items(order_id)
            if not items:
                return "No items"
            
            # Create a summary of items
            item_summary = []
            for item in items[:3]:  # Show first 3 items
                product_name = item.get('product_name', f"Product {item['product_id']}")
                quantity = item['quantity']
                item_summary.append(f"{product_name} ({quantity})")
            
            result = ", ".join(item_summary)
            if len(items) > 3:
                result += f" +{len(items) - 3} more"
            
            return result
        except:
            return "Error loading items"

    def add_order(self):
        """
        Opens an improved dialog to add a new order with better UX.
        """
        # Create add order window
        add_window = tk.Toplevel(self)
        add_window.title("Add New Order")
        add_window.geometry("800x700")
        add_window.grab_set()  # Make it modal
        
        # Customer input
        customer_frame = ttk.LabelFrame(add_window, text="Customer Information", padding="10")
        customer_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(customer_frame, text="Customer Name:").pack(anchor="w")
        customer_var = tk.StringVar()
        customer_entry = ttk.Entry(customer_frame, textvariable=customer_var, width=40)
        customer_entry.pack(fill="x", pady=5)
        customer_entry.focus()
        
        # Create notebook for two sections
        notebook = ttk.Notebook(add_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Products selection tab
        products_frame = ttk.Frame(notebook)
        notebook.add(products_frame, text="Available Products")
        
        # Products treeview
        products_tree = ttk.Treeview(products_frame, columns=("ID", "Name", "Price", "Stock"), show="headings", height=12)
        products_tree.heading("ID", text="ID")
        products_tree.heading("Name", text="Product Name")
        products_tree.heading("Price", text="Price")
        products_tree.heading("Stock", text="Available Stock")
        
        # Configure column widths
        products_tree.column("ID", width=60)
        products_tree.column("Name", width=250)
        products_tree.column("Price", width=100)
        products_tree.column("Stock", width=100)
        
        products_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add product controls
        add_controls_frame = ttk.Frame(products_frame)
        add_controls_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(add_controls_frame, text="Quantity:").pack(side="left")
        qty_var = tk.StringVar(value="1")
        qty_entry = ttk.Entry(add_controls_frame, textvariable=qty_var, width=10)
        qty_entry.pack(side="left", padx=5)
        
        # Selected items tab
        selected_frame = ttk.Frame(notebook)
        notebook.add(selected_frame, text="Selected Items")
        
        # Selected items treeview
        selected_tree = ttk.Treeview(selected_frame, columns=("Name", "Quantity", "Price", "Subtotal"), show="headings", height=12)
        selected_tree.heading("Name", text="Product Name")
        selected_tree.heading("Quantity", text="Quantity")
        selected_tree.heading("Price", text="Unit Price")
        selected_tree.heading("Subtotal", text="Subtotal")
        
        # Configure column widths
        selected_tree.column("Name", width=250)
        selected_tree.column("Quantity", width=100)
        selected_tree.column("Price", width=100)
        selected_tree.column("Subtotal", width=100)
        
        selected_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Selected items controls
        selected_controls_frame = ttk.Frame(selected_frame)
        selected_controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Store selected items data
        selected_items = {}  # product_id: {'name': str, 'quantity': int, 'price': float}
        
        def add_to_order():
            selected = products_tree.selection()
            if not selected:
                messagebox.showerror("Error", "Please select a product to add.")
                return
            
            try:
                quantity = int(qty_var.get())
                if quantity <= 0:
                    messagebox.showerror("Error", "Quantity must be greater than 0.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid quantity.")
                return
            
            # Get selected product details
            item_values = products_tree.item(selected[0])['values']
            product_id = int(item_values[0])
            product_name = item_values[1]
            price = float(item_values[2].replace('$', ''))
            stock = int(item_values[3])
            
            # Check if enough stock
            current_qty = selected_items.get(product_id, {}).get('quantity', 0)
            total_qty = current_qty + quantity
            
            if total_qty > stock:
                messagebox.showerror("Error", f"Not enough stock. Available: {stock}, Requested: {total_qty}")
                return
            
            # Add or update selected items
            if product_id in selected_items:
                selected_items[product_id]['quantity'] = total_qty
            else:
                selected_items[product_id] = {
                    'name': product_name,
                    'quantity': quantity,
                    'price': price
                }
            
            refresh_selected_items()
            qty_var.set("1")  # Reset quantity
        
        def remove_from_order():
            selected = selected_tree.selection()
            if not selected:
                messagebox.showerror("Error", "Please select an item to remove.")
                return
            
            # Get product name from selection
            item_values = selected_tree.item(selected[0])['values']
            product_name = item_values[0]
            
            # Find and remove the product
            product_id_to_remove = None
            for pid, item_data in selected_items.items():
                if item_data['name'] == product_name:
                    product_id_to_remove = pid
                    break
            
            if product_id_to_remove:
                del selected_items[product_id_to_remove]
                refresh_selected_items()
        
        def refresh_selected_items():
            # Clear the selected items tree
            for item in selected_tree.get_children():
                selected_tree.delete(item)
            
            total = 0
            # Populate with current selected items
            for product_id, item_data in selected_items.items():
                subtotal = item_data['quantity'] * item_data['price']
                total += subtotal
                selected_tree.insert("", "end", values=(
                    item_data['name'],
                    item_data['quantity'],
                    f"${item_data['price']:.2f}",
                    f"${subtotal:.2f}"
                ))
            
            # Update total
            total_var.set(f"Total: ${total:.2f}")
        
        ttk.Button(add_controls_frame, text="Add to Order", command=add_to_order).pack(side="left", padx=5)
        ttk.Button(selected_controls_frame, text="Remove Selected", command=remove_from_order).pack(side="left", padx=5)
        ttk.Button(selected_controls_frame, text="Clear All", command=lambda: [selected_items.clear(), refresh_selected_items()]).pack(side="left", padx=5)
        
        # Load products
        try:
            products = self.get_all_products()
            for product in products:
                products_tree.insert("", "end", values=(
                    product['id'],
                    product['name'],
                    f"${product['price']:.2f}",
                    product['stock']
                ))
        except Exception as e:
            ttk.Label(products_frame, text=f"Error loading products: {e}").pack()
            return
        
        # Total and buttons
        bottom_frame = ttk.Frame(add_window)
        bottom_frame.pack(fill="x", padx=10, pady=10)
        
        total_var = tk.StringVar(value="Total: $0.00")
        total_label = ttk.Label(bottom_frame, textvariable=total_var, font=("Arial", 14, "bold"))
        total_label.pack(side="left")
        
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(side="right")
        
        def create_order():
            # Validate customer name
            customer_name = customer_var.get().strip()
            if not customer_name:
                messagebox.showerror("Error", "Please enter a customer name.")
                return
            
            if not selected_items:
                messagebox.showerror("Error", "Please add at least one product to the order.")
                return
            
            # Convert selected items to order format
            order_items = []
            total_price = 0
            
            for product_id, item_data in selected_items.items():
                order_items.append({
                    'product_id': product_id,
                    'quantity': item_data['quantity'],
                    'price': item_data['price']
                })
                total_price += item_data['quantity'] * item_data['price']
            
            # Create the order
            try:
                success = self.create_order_in_db(customer_name, order_items, total_price)
                if success:
                    messagebox.showinfo("Success", "Order created successfully!")
                    add_window.destroy()
                    self.load_orders_async()  # Refresh the orders list
                else:
                    messagebox.showerror("Error", "Failed to create order.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create order: {str(e)}")
        
        ttk.Button(button_frame, text="Create Order", command=create_order).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=add_window.destroy).pack(side="right")
    
    def get_all_products(self):
        """Get all available products using backend service."""
        return OrderService.get_all_products()
    
    def create_order_in_db(self, customer_name, order_items, total_price):
        """Create a new order using backend service."""
        return OrderService.create_order_in_db(customer_name, order_items, total_price)

    def import_orders_csv(self):
        """Import orders from a line-item CSV file."""
        file_path = CSVHandler.choose_import_file("Import Orders CSV")
        if not file_path:
            return

        try:
            summary = OrderService.import_orders_from_csv(file_path)
            imported_orders = summary.get("imported_orders", 0)
            imported_rows = summary.get("imported_rows", 0)
            failed_orders = summary.get("failed_orders", 0)
            errors = summary.get("errors", [])

            if imported_orders:
                self.load_orders_async()

            details = (
                f"Imported {imported_orders} orders from {imported_rows} line items."
            )
            if failed_orders:
                preview = "\n".join(errors[:5])
                details += (
                    f"\n\nFailed groups: {failed_orders}"
                    f"\n{preview}"
                )
                if len(errors) > 5:
                    details += f"\n...and {len(errors) - 5} more."
                messagebox.showwarning("Orders CSV Import", details)
            else:
                messagebox.showinfo("Orders CSV Import", details)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import orders CSV: {str(e)}")

    def export_orders_csv(self):
        """Export selected orders or the full order list to CSV."""
        selected_items = self.tree.selection()
        order_ids = [self.tree.item(item)["values"][0] for item in selected_items] if selected_items else None
        file_path = CSVHandler.choose_export_file(
            title="Export Orders CSV",
            default_name="orders_export.csv",
        )
        if not file_path:
            return

        try:
            row_count = OrderService.export_orders_to_csv(file_path, order_ids=order_ids)
            scope_label = f"{len(order_ids)} selected orders" if order_ids else "all orders"
            messagebox.showinfo(
                "Orders CSV Export",
                f"Exported {row_count} rows for {scope_label} to:\n{file_path}",
            )
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export orders CSV: {str(e)}")

    def view_order_details(self):
        """
        Show detailed information about the selected order.
        """
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("View Details", "Please select an order to view details.")
            return

        # Get order ID from selected item
        order_id = self.tree.item(selected_item[0])['values'][0]
        
        try:
            # Get order details
            orders = self.db_ops.get_all_orders()
            order = next((o for o in orders if o['id'] == order_id), None)
            
            if not order:
                messagebox.showerror("Error", "Order not found.")
                return
            
            # Get order items
            items = self.db_ops.get_order_items(order_id)
            
            # Create details window
            details_window = tk.Toplevel(self)
            details_window.title(f"Order #{order_id} Details")
            details_window.geometry("500x400")
            
            # Order info
            info_frame = ttk.LabelFrame(details_window, text="Order Information", padding="10")
            info_frame.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(info_frame, text=f"Order ID: {order['id']}").pack(anchor="w")
            ttk.Label(info_frame, text=f"Customer ID: {order['user_id']}").pack(anchor="w")
            ttk.Label(info_frame, text=f"Total: ${order['total_price']:.2f}").pack(anchor="w")
            ttk.Label(info_frame, text=f"Date: {order['created_at']}").pack(anchor="w")
            
            # Items info
            items_frame = ttk.LabelFrame(details_window, text="Order Items", padding="10")
            items_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Items treeview
            items_tree = ttk.Treeview(items_frame, columns=("Product", "Quantity", "Price"), show="headings")
            items_tree.heading("Product", text="Product")
            items_tree.heading("Quantity", text="Quantity")
            items_tree.heading("Price", text="Unit Price")
            
            for item in items:
                product_name = item.get('product_name', f"Product {item['product_id']}")
                items_tree.insert("", "end", values=(
                    product_name,
                    item['quantity'],
                    f"${item['price']:.2f}"
                ))
            
            items_tree.pack(fill="both", expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load order details: {str(e)}")

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
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Delete Order", "Please select an order to delete.")
            return

        # Get order details from the treeview
        item_values = self.tree.item(selected_item[0])['values']
        order_id = item_values[0]
        order_status = item_values[5]  # Status column

        # Check if order can be deleted (not dispatched/delivered)
        non_deletable_statuses = ['Dispatched', 'Delivered']
        if order_status in non_deletable_statuses:
            messagebox.showerror("Cannot Delete", 
                               f"Cannot delete order with status '{order_status}'. "
                               f"Only orders with 'Preparing' status can be deleted.")
            return

        # Confirm deletion
        confirm = messagebox.askyesno("Delete Order", 
                                    f"Are you sure you want to delete order #{order_id}?\n"
                                    f"Preparing orders can be removed safely before inventory is deducted.")
        if not confirm:
            return

        try:
            success = OrderService.delete_order_and_restore_inventory(order_id)
            if success:
                self.tree.delete(selected_item)
                messagebox.showinfo("Order Deleted", 
                                  f"Order #{order_id} deleted successfully.")
            else:
                messagebox.showerror("Error", f"Failed to delete order.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete order: {str(e)}")

    def edit_order_details(self):
        """
        Edit all details of the selected order.
        """
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Edit Details", "Please select an order to edit.")
            return

        # Get order ID from selected item
        item_values = self.tree.item(selected_item[0])['values']
        order_id = item_values[0]

        try:
            order = OrderService.get_order_details(order_id)
            if not order:
                messagebox.showerror("Error", "Order not found in database.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load order details: {str(e)}")
            return

        # Create edit window
        edit_window = tk.Toplevel(self)
        edit_window.title(f"Edit Order #{order_id}")
        edit_window.geometry("400x350")
        edit_window.grab_set()  # Make it modal

        # Main frame with padding
        main_frame = ttk.Frame(edit_window, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Order ID (read-only)
        ttk.Label(main_frame, text="Order ID:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(main_frame, text=str(order['id']), font=("Arial", 10)).grid(row=0, column=1, sticky="w", padx=10)

        # Customer Name
        ttk.Label(main_frame, text="Customer Name:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        customer_var = tk.StringVar(value=order.get('customer_name', ''))
        customer_entry = ttk.Entry(main_frame, textvariable=customer_var, width=30)
        customer_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # Total Price
        ttk.Label(main_frame, text="Total Price ($):", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        total_var = tk.StringVar(value=str(order.get('total_price', '0.00')))
        total_entry = ttk.Entry(main_frame, textvariable=total_var, width=30)
        total_entry.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        # Status
        ttk.Label(main_frame, text="Status:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        status_var = tk.StringVar(value=order.get('status', 'Preparing'))
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=1, sticky="w", padx=10, pady=5)

        status_options = ["Preparing", "Dispatched", "Delivered"]
        for i, status in enumerate(status_options):
            ttk.Radiobutton(status_frame, text=status, variable=status_var, value=status).grid(row=0, column=i, padx=5)

        # Created Date (read-only)
        ttk.Label(main_frame, text="Created Date:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        created_date = order.get('created_at', '')
        date_str = created_date.strftime("%Y-%m-%d %H:%M:%S") if created_date else "N/A"
        ttk.Label(main_frame, text=date_str, font=("Arial", 10)).grid(row=4, column=1, sticky="w", padx=10)

        # Notes section (you can add this to database later if needed)
        ttk.Label(main_frame, text="Notes:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="nw", pady=5)
        notes_text = tk.Text(main_frame, width=30, height=4)
        notes_text.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        notes_text.insert("1.0", "Additional notes can be added here...")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        def save_changes():
            # Validate inputs
            customer_name = customer_var.get().strip()
            if not customer_name:
                messagebox.showerror("Error", "Customer name cannot be empty.")
                return

            try:
                total_price = float(total_var.get())
                if total_price < 0:
                    messagebox.showerror("Error", "Total price cannot be negative.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid total price.")
                return

            new_status = status_var.get()

            try:
                success = OrderService.update_order_details(order_id, customer_name, total_price, new_status)
                if success:
                    messagebox.showinfo("Success", "Order details updated successfully!")
                    edit_window.destroy()
                    self.load_orders_async()  # Refresh the orders list
                else:
                    messagebox.showerror("Error", "Failed to update order.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update order: {str(e)}")

        def cancel_edit():
            edit_window.destroy()

        ttk.Button(button_frame, text="Save Changes", command=save_changes).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Cancel", command=cancel_edit).pack(side="left", padx=10)
