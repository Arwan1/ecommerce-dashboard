import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from database.db_operations import DBOperations
from database.db_connector import get_db_connection

class InventoryDashboard(tk.Frame):
    """
    Comprehensive GUI for managing inventory with products and raw materials.
    """
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.db_ops = DBOperations()
        self.create_widgets()
        self.load_dashboard_data()

    def create_widgets(self):
        """
        Creates the main inventory dashboard layout.
        """
        # Title
        title_label = tk.Label(self, text="Inventory Dashboard", font=("Arial", 20, "bold"))
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

        # Top section with charts
        charts_frame = ttk.LabelFrame(scrollable_frame, text="Inventory Overview", padding="10")
        charts_frame.pack(fill="x", pady=5)

        # Charts container
        charts_container = ttk.Frame(charts_frame)
        charts_container.pack(fill="x")

        # Create matplotlib figure for pie charts
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 6))
        self.fig.suptitle('Inventory Count Overview', fontsize=16, fontweight='bold')
        
        # Create canvas for matplotlib
        self.chart_canvas = FigureCanvasTkAgg(self.fig, charts_container)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

        # Low stock alerts section
        alerts_frame = ttk.LabelFrame(scrollable_frame, text="Low Stock Alerts", padding="10")
        alerts_frame.pack(fill="x", pady=5)

        # Low products section
        low_products_frame = ttk.Frame(alerts_frame)
        low_products_frame.pack(fill="x", pady=5)
        
        self.low_products_heading = ttk.Label(low_products_frame, text="Low Products:", font=("Arial", 12, "bold"))
        self.low_products_heading.pack(anchor="w")
        self.low_products_label = ttk.Label(low_products_frame, text="Loading...")
        self.low_products_label.pack(anchor="w", padx=20)

        # Low raw materials section
        low_materials_frame = ttk.Frame(alerts_frame)
        low_materials_frame.pack(fill="x", pady=5)
        
        self.low_materials_heading = ttk.Label(low_materials_frame, text="Low Raw Materials:", font=("Arial", 12, "bold"))
        self.low_materials_heading.pack(anchor="w")
        self.low_materials_label = ttk.Label(low_materials_frame, text="Loading...")
        self.low_materials_label.pack(anchor="w", padx=20)

        # Buttons section
        buttons_frame = ttk.LabelFrame(scrollable_frame, text="Inventory Management", padding="10")
        buttons_frame.pack(fill="x", pady=5)

        button_container = ttk.Frame(buttons_frame)
        button_container.pack()

        # Main management buttons
        ttk.Button(button_container, text="📦 Manage Products", 
                  command=self.open_products_manager, 
                  style="Accent.TButton").pack(side="left", padx=10, pady=5)
        
        ttk.Button(button_container, text="🔧 Manage Raw Materials", 
                  command=self.open_raw_materials_manager, 
                  style="Accent.TButton").pack(side="left", padx=10, pady=5)
        
        ttk.Button(button_container, text="🔄 Refresh Dashboard", 
                  command=self.load_dashboard_data).pack(side="left", padx=10, pady=5)

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def load_dashboard_data(self):
        """
        Load all dashboard data in background thread.
        """
        def load_in_background():
            try:
                # Get data from database
                products_data = self.get_products_data()
                materials_data = self.get_raw_materials_data()
                low_products = self.get_low_stock_products()
                low_materials = self.get_low_stock_materials()
                
                # Update UI in main thread
                self.after(0, lambda: self.update_dashboard(products_data, materials_data, low_products, low_materials))
            except Exception as e:
                self.after(0, lambda: self.handle_error(str(e)))
        
        thread = threading.Thread(target=load_in_background, daemon=True)
        thread.start()

    def update_dashboard(self, products_data, materials_data, low_products, low_materials):
        """
        Update the dashboard with loaded data.
        """
        # Update pie charts
        self.update_pie_charts(products_data, materials_data)
        
        # Update low stock alerts
        if low_products:
            # Update heading and text for low stock products
            self.low_products_heading.config(text="Low Products:", foreground="red")
            low_products_text = ", ".join([f"{p['name']} ({p['stock']} left)" for p in low_products[:5]])
            if len(low_products) > 5:
                low_products_text += f" +{len(low_products) - 5} more"
            self.low_products_label.config(text=low_products_text, foreground="red")
        else:
            # Update heading and text for well stocked products
            self.low_products_heading.config(text="Products Status:", foreground="green")
            low_products_text = "All products well stocked! ✅"
            self.low_products_label.config(text=low_products_text, foreground="green")
        
        if low_materials:
            # Update heading and text for low stock materials
            self.low_materials_heading.config(text="Low Raw Materials:", foreground="red")
            low_materials_text = ", ".join([f"{m['name']} ({m['quantity']:.1f} {m['unit']} left)" for m in low_materials[:5]])
            if len(low_materials) > 5:
                low_materials_text += f" +{len(low_materials) - 5} more"
            self.low_materials_label.config(text=low_materials_text, foreground="red")
        else:
            # Update heading and text for well stocked materials
            self.low_materials_heading.config(text="Raw Materials Status:", foreground="green")
            low_materials_text = "All raw materials well stocked! ✅"
            self.low_materials_label.config(text=low_materials_text, foreground="green")

    def update_pie_charts(self, products_data, materials_data):
        """
        Update the pie charts with current inventory counts.
        """
        # Clear all subplots
        for ax in [self.ax1, self.ax2]:
            ax.clear()

        # Chart 1: Products by Count/Stock
        if products_data:
            # Get product names and their stock quantities
            product_names = [p['name'][:15] + '...' if len(p['name']) > 15 else p['name'] for p in products_data[:8]]  # Top 8 products
            product_stocks = [p['stock'] for p in products_data[:8]]
            
            if len(products_data) > 8:
                remaining_stock = sum(p['stock'] for p in products_data[8:])
                product_names.append(f'Others ({len(products_data) - 8} items)')
                product_stocks.append(remaining_stock)
            
            if product_stocks:
                colors = plt.cm.Set3(range(len(product_stocks)))
                self.ax1.pie(product_stocks, labels=product_names, colors=colors, autopct='%1.0f', startangle=90)
            self.ax1.set_title('Products in Stock (Quantities)')

        # Chart 2: Raw Materials by Count/Quantity
        if materials_data:
            # Get material names and their quantities
            material_names = [m['name'][:15] + '...' if len(m['name']) > 15 else m['name'] for m in materials_data[:8]]  # Top 8 materials
            material_quantities = [m['quantity'] for m in materials_data[:8]]
            
            if len(materials_data) > 8:
                remaining_quantity = sum(m['quantity'] for m in materials_data[8:])
                material_names.append(f'Others ({len(materials_data) - 8} items)')
                material_quantities.append(remaining_quantity)
            
            if material_quantities:
                colors = plt.cm.Pastel1(range(len(material_quantities)))
                self.ax2.pie(material_quantities, labels=material_names, colors=colors, autopct='%1.1f', startangle=90)
            self.ax2.set_title('Raw Materials in Stock (Quantities)')

        # Refresh the canvas
        self.fig.tight_layout()
        self.chart_canvas.draw()

    def get_products_data(self):
        """Get products data using DBOperations."""
        return self.db_ops.get_products_data()

    def get_raw_materials_data(self):
        """Get raw materials data using DBOperations."""
        return self.db_ops.get_raw_materials_data()

    def get_low_stock_products(self):
        """Get products with low stock using DBOperations."""
        return self.db_ops.get_low_stock_products()

    def get_low_stock_materials(self):
        """Get raw materials with low stock using DBOperations."""
        return self.db_ops.get_low_stock_materials()

    def handle_error(self, error_message):
        """Handle errors in data loading."""
        messagebox.showerror("Error", f"Failed to load dashboard data: {error_message}")

    def open_products_manager(self):
        """Open the products management window."""
        ProductsManager(self)

    def open_raw_materials_manager(self):
        """Open the raw materials management window."""
        RawMaterialsManager(self)


class ProductsManager(tk.Toplevel):
    """
    Products management window with CRUD operations.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Products Management")
        self.geometry("1200x700")
        self.grab_set()  # Make it modal
        
        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        """Create the products management interface."""
        # Title
        title_label = tk.Label(self, text="Products Management", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)

        # Products treeview
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Name", "Price", "Stock", "Reorder", "Ready Made", "Supplier", "Raw Materials"), show="headings")
        
        # Configure headings
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Product Name")
        self.tree.heading("Price", text="Price ($)")
        self.tree.heading("Stock", text="Stock")
        self.tree.heading("Reorder", text="Reorder Level")
        self.tree.heading("Ready Made", text="Ready Made")
        self.tree.heading("Supplier", text="Supplier")
        self.tree.heading("Raw Materials", text="Raw Materials Required")

        # Configure column widths
        self.tree.column("ID", width=50)
        self.tree.column("Name", width=150)
        self.tree.column("Price", width=80)
        self.tree.column("Stock", width=80)
        self.tree.column("Reorder", width=100)
        self.tree.column("Ready Made", width=100)
        self.tree.column("Supplier", width=150)
        self.tree.column("Raw Materials", width=300)

        self.tree.pack(fill="both", expand=True)

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Add Product", command=self.add_product).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Edit Product", command=self.edit_product).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete Product", command=self.delete_product).pack(side="left", padx=5)
        ttk.Button(button_frame, text="View Details", command=self.view_details).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.load_products).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Close", command=self.destroy).pack(side="right", padx=5)

    def load_products(self):
        """Load products from database."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get products with raw materials info
            cursor.execute("""
                SELECT p.*, 
                       GROUP_CONCAT(CONCAT(rm.name, ' (', prm.quantity_required, ' ', rm.unit, ')') SEPARATOR ', ') as raw_materials
                FROM products p
                LEFT JOIN product_raw_materials prm ON p.id = prm.product_id
                LEFT JOIN raw_materials rm ON prm.raw_material_id = rm.id
                GROUP BY p.id
            """)
            
            products = cursor.fetchall()
            conn.close()

            for product in products:
                ready_made = "Yes" if product.get('is_ready_made') else "No"
                supplier = product.get('ready_made_supplier') or "N/A"
                raw_materials = product.get('raw_materials') or "None (Ready Made)" if product.get('is_ready_made') else "None"
                
                self.tree.insert("", "end", values=(
                    product['id'],
                    product['name'],
                    f"${product['price']:.2f}",
                    product['stock'],
                    product.get('reorder_level', 10),
                    ready_made,
                    supplier,
                    raw_materials
                ))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load products: {str(e)}")

    def add_product(self):
        """Open dialog to add new product."""
        ProductDialog(self, "Add Product")

    def edit_product(self):
        """Edit selected product."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a product to edit.")
            return
        
        product_id = self.tree.item(selected[0])['values'][0]
        ProductDialog(self, "Edit Product", product_id)

    def delete_product(self):
        """Delete selected product."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a product to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this product?"):
            try:
                product_id = self.tree.item(selected[0])['values'][0]
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "Product deleted successfully!")
                self.load_products()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product: {str(e)}")

    def view_details(self):
        """View detailed information about selected product."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a product to view details.")
            return
        
        product_id = self.tree.item(selected[0])['values'][0]
        ProductDetailsDialog(self, product_id)


class RawMaterialsManager(tk.Toplevel):
    """
    Raw materials management window with CRUD operations.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Raw Materials Management")
        self.geometry("1200x700")
        self.grab_set()  # Make it modal
        
        self.create_widgets()
        self.load_materials()

    def create_widgets(self):
        """Create the raw materials management interface."""
        # Title
        title_label = tk.Label(self, text="Raw Materials Management", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)

        # Materials treeview
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Name", "Quantity", "Unit", "Reorder", "Supplier", "Rating", "Cost"), show="headings")
        
        # Configure headings
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Material Name")
        self.tree.heading("Quantity", text="Quantity")
        self.tree.heading("Unit", text="Unit")
        self.tree.heading("Reorder", text="Reorder Level")
        self.tree.heading("Supplier", text="Supplier")
        self.tree.heading("Rating", text="Supplier Rating")
        self.tree.heading("Cost", text="Cost/Unit ($)")

        # Configure column widths
        self.tree.column("ID", width=50)
        self.tree.column("Name", width=150)
        self.tree.column("Quantity", width=100)
        self.tree.column("Unit", width=80)
        self.tree.column("Reorder", width=100)
        self.tree.column("Supplier", width=150)
        self.tree.column("Rating", width=100)
        self.tree.column("Cost", width=100)

        self.tree.pack(fill="both", expand=True)

        # Configure row colors based on stock levels
        self.tree.tag_configure('low_stock', background='#ffcdd2')  # Light red
        self.tree.tag_configure('normal_stock', background='#d4edda')  # Light green

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Add Material", command=self.add_material).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Edit Material", command=self.edit_material).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete Material", command=self.delete_material).pack(side="left", padx=5)
        ttk.Button(button_frame, text="View Details", command=self.view_details).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.load_materials).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Close", command=self.destroy).pack(side="right", padx=5)

    def load_materials(self):
        """Load raw materials from database."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM raw_materials ORDER BY name")
            materials = cursor.fetchall()
            conn.close()

            for material in materials:
                # Determine stock status
                tag = 'low_stock' if material['quantity'] <= material['reorder_level'] else 'normal_stock'
                
                self.tree.insert("", "end", values=(
                    material['id'],
                    material['name'],
                    f"{material['quantity']:.2f}",
                    material['unit'],
                    f"{material['reorder_level']:.2f}",
                    material['supplier'] or "N/A",
                    f"{material['supplier_rating']:.1f}/5.0",
                    f"${material['cost_per_unit']:.2f}"
                ), tags=(tag,))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load raw materials: {str(e)}")

    def add_material(self):
        """Open dialog to add new raw material."""
        MaterialDialog(self, "Add Raw Material")

    def edit_material(self):
        """Edit selected raw material."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a raw material to edit.")
            return
        
        material_id = self.tree.item(selected[0])['values'][0]
        MaterialDialog(self, "Edit Raw Material", material_id)

    def delete_material(self):
        """Delete selected raw material."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a raw material to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this raw material?"):
            try:
                material_id = self.tree.item(selected[0])['values'][0]
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM raw_materials WHERE id = %s", (material_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "Raw material deleted successfully!")
                self.load_materials()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete raw material: {str(e)}")

    def view_details(self):
        """View detailed information about selected raw material."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a raw material to view details.")
            return
        
        material_id = self.tree.item(selected[0])['values'][0]
        MaterialDetailsDialog(self, material_id)


class ProductDialog(tk.Toplevel):
    """Dialog for adding/editing products."""
    def __init__(self, parent, title, product_id=None):
        super().__init__(parent)
        self.parent = parent
        self.product_id = product_id
        self.title(title)
        self.geometry("600x700")
        self.grab_set()
        
        self.create_widgets()
        if product_id:
            self.load_product_data()

    def create_widgets(self):
        """Create the product dialog interface."""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Product basic info
        info_frame = ttk.LabelFrame(main_frame, text="Product Information", padding="10")
        info_frame.pack(fill="x", pady=5)

        ttk.Label(info_frame, text="Product Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(info_frame, text="Description:").grid(row=1, column=0, sticky="nw", pady=5)
        self.description_text = tk.Text(info_frame, width=40, height=3)
        self.description_text.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(info_frame, text="Price ($):").grid(row=2, column=0, sticky="w", pady=5)
        self.price_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.price_var, width=40).grid(row=2, column=1, sticky="ew", padx=5)

        ttk.Label(info_frame, text="Stock:").grid(row=3, column=0, sticky="w", pady=5)
        self.stock_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.stock_var, width=40).grid(row=3, column=1, sticky="ew", padx=5)

        ttk.Label(info_frame, text="Reorder Level:").grid(row=4, column=0, sticky="w", pady=5)
        self.reorder_var = tk.StringVar(value="10")
        ttk.Entry(info_frame, textvariable=self.reorder_var, width=40).grid(row=4, column=1, sticky="ew", padx=5)

        info_frame.columnconfigure(1, weight=1)

        # Ready made section
        ready_frame = ttk.LabelFrame(main_frame, text="Manufacturing Type", padding="10")
        ready_frame.pack(fill="x", pady=5)

        self.is_ready_made = tk.BooleanVar()
        ttk.Checkbutton(ready_frame, text="Ready Made Product", variable=self.is_ready_made, 
                       command=self.toggle_ready_made).pack(anchor="w")

        ttk.Label(ready_frame, text="Supplier (if ready made):").pack(anchor="w", pady=(10,0))
        self.supplier_var = tk.StringVar()
        self.supplier_entry = ttk.Entry(ready_frame, textvariable=self.supplier_var, width=50)
        self.supplier_entry.pack(fill="x", pady=5)

        # Raw materials section
        self.materials_frame = ttk.LabelFrame(main_frame, text="Raw Materials Required", padding="10")
        self.materials_frame.pack(fill="both", expand=True, pady=5)

        # Raw materials treeview
        self.materials_tree = ttk.Treeview(self.materials_frame, columns=("Material", "Quantity", "Unit"), show="headings", height=8)
        self.materials_tree.heading("Material", text="Raw Material")
        self.materials_tree.heading("Quantity", text="Quantity Required")
        self.materials_tree.heading("Unit", text="Unit")
        
        self.materials_tree.column("Material", width=200)
        self.materials_tree.column("Quantity", width=100)
        self.materials_tree.column("Unit", width=80)
        
        self.materials_tree.pack(fill="both", expand=True, pady=5)

        # Add material controls
        material_controls = ttk.Frame(self.materials_frame)
        material_controls.pack(fill="x", pady=5)

        ttk.Label(material_controls, text="Material:").pack(side="left")
        self.material_combo = ttk.Combobox(material_controls, width=20)
        self.material_combo.pack(side="left", padx=5)
        
        ttk.Label(material_controls, text="Quantity:").pack(side="left", padx=(10,0))
        self.quantity_var = tk.StringVar()
        ttk.Entry(material_controls, textvariable=self.quantity_var, width=10).pack(side="left", padx=5)

        ttk.Button(material_controls, text="Add Material", command=self.add_material).pack(side="left", padx=5)
        ttk.Button(material_controls, text="Remove Selected", command=self.remove_material).pack(side="left", padx=5)

        # Load available materials
        self.load_available_materials()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)

        ttk.Button(button_frame, text="Save", command=self.save_product).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="right")

    def toggle_ready_made(self):
        """Toggle ready made controls."""
        if self.is_ready_made.get():
            self.supplier_entry.config(state="normal")
            self.materials_frame.pack_forget()
        else:
            self.supplier_entry.config(state="disabled")
            self.materials_frame.pack(fill="both", expand=True, pady=5)

    def load_available_materials(self):
        """Load available raw materials for selection."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, unit FROM raw_materials ORDER BY name")
            materials = cursor.fetchall()
            conn.close()
            
            self.available_materials = {f"{m['name']} ({m['unit']})": m for m in materials}
            self.material_combo['values'] = list(self.available_materials.keys())
            
        except Exception as e:
            print(f"Error loading materials: {e}")

    def add_material(self):
        """Add selected material to the list."""
        selected_material = self.material_combo.get()
        quantity = self.quantity_var.get()
        
        if not selected_material or not quantity:
            messagebox.showerror("Error", "Please select a material and enter quantity.")
            return
        
        try:
            float(quantity)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return
        
        material_data = self.available_materials[selected_material]
        
        # Check if material already added
        for item in self.materials_tree.get_children():
            if self.materials_tree.item(item)['values'][0] == material_data['name']:
                messagebox.showerror("Error", "Material already added.")
                return
        
        self.materials_tree.insert("", "end", values=(
            material_data['name'],
            quantity,
            material_data['unit']
        ))
        
        self.quantity_var.set("")

    def remove_material(self):
        """Remove selected material from the list."""
        selected = self.materials_tree.selection()
        if selected:
            self.materials_tree.delete(selected[0])

    def load_product_data(self):
        """Load existing product data for editing."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Load product info
            cursor.execute("SELECT * FROM products WHERE id = %s", (self.product_id,))
            product = cursor.fetchone()
            
            if product:
                self.name_var.set(product['name'])
                self.description_text.insert("1.0", product.get('description', ''))
                self.price_var.set(str(product['price']))
                self.stock_var.set(str(product['stock']))
                self.reorder_var.set(str(product.get('reorder_level', 10)))
                self.is_ready_made.set(product.get('is_ready_made', False))
                self.supplier_var.set(product.get('ready_made_supplier', ''))
                
                self.toggle_ready_made()
                
                # Load raw materials if not ready made
                if not product.get('is_ready_made'):
                    cursor.execute("""
                        SELECT rm.name, prm.quantity_required, rm.unit
                        FROM product_raw_materials prm
                        JOIN raw_materials rm ON prm.raw_material_id = rm.id
                        WHERE prm.product_id = %s
                    """, (self.product_id,))
                    
                    materials = cursor.fetchall()
                    for material in materials:
                        self.materials_tree.insert("", "end", values=(
                            material['name'],
                            material['quantity_required'],
                            material['unit']
                        ))
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load product data: {str(e)}")

    def save_product(self):
        """Save the product data."""
        # Validate inputs
        name = self.name_var.get().strip()
        description = self.description_text.get("1.0", "end-1c").strip()
        
        try:
            price = float(self.price_var.get())
            stock = int(self.stock_var.get())
            reorder_level = int(self.reorder_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for price, stock, and reorder level.")
            return
        
        if not name:
            messagebox.showerror("Error", "Please enter a product name.")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.product_id:
                # Update existing product
                cursor.execute("""
                    UPDATE products 
                    SET name = %s, description = %s, price = %s, stock = %s, reorder_level = %s,
                        is_ready_made = %s, ready_made_supplier = %s
                    WHERE id = %s
                """, (name, description, price, stock, reorder_level, 
                      self.is_ready_made.get(), self.supplier_var.get() if self.is_ready_made.get() else None,
                      self.product_id))
                
                # Clear existing raw materials
                cursor.execute("DELETE FROM product_raw_materials WHERE product_id = %s", (self.product_id,))
                
            else:
                # Insert new product
                cursor.execute("""
                    INSERT INTO products (name, description, price, stock, reorder_level, is_ready_made, ready_made_supplier)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, description, price, stock, reorder_level, 
                      self.is_ready_made.get(), self.supplier_var.get() if self.is_ready_made.get() else None))
                
                self.product_id = cursor.lastrowid
            
            # Add raw materials if not ready made
            if not self.is_ready_made.get():
                for item in self.materials_tree.get_children():
                    values = self.materials_tree.item(item)['values']
                    material_name = values[0]
                    quantity = float(values[1])
                    
                    # Get material ID
                    cursor.execute("SELECT id FROM raw_materials WHERE name = %s", (material_name,))
                    material_result = cursor.fetchone()
                    
                    if material_result:
                        cursor.execute("""
                            INSERT INTO product_raw_materials (product_id, raw_material_id, quantity_required)
                            VALUES (%s, %s, %s)
                        """, (self.product_id, material_result[0], quantity))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Product saved successfully!")
            self.parent.load_products()
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save product: {str(e)}")


class MaterialDialog(tk.Toplevel):
    """Dialog for adding/editing raw materials."""
    def __init__(self, parent, title, material_id=None):
        super().__init__(parent)
        self.parent = parent
        self.material_id = material_id
        self.title(title)
        self.geometry("500x500")
        self.grab_set()
        
        self.create_widgets()
        if material_id:
            self.load_material_data()

    def create_widgets(self):
        """Create the material dialog interface."""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Material info
        info_frame = ttk.LabelFrame(main_frame, text="Material Information", padding="10")
        info_frame.pack(fill="x", pady=5)

        ttk.Label(info_frame, text="Material Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(info_frame, text="Description:").grid(row=1, column=0, sticky="nw", pady=5)
        self.description_text = tk.Text(info_frame, width=40, height=3)
        self.description_text.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(info_frame, text="Quantity:").grid(row=2, column=0, sticky="w", pady=5)
        self.quantity_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.quantity_var, width=40).grid(row=2, column=1, sticky="ew", padx=5)

        ttk.Label(info_frame, text="Unit:").grid(row=3, column=0, sticky="w", pady=5)
        self.unit_var = tk.StringVar()
        unit_combo = ttk.Combobox(info_frame, textvariable=self.unit_var, width=37)
        unit_combo['values'] = ["kg", "g", "m", "cm", "m2", "m3", "pcs", "L", "mL", "ton"]
        unit_combo.grid(row=3, column=1, sticky="ew", padx=5)

        ttk.Label(info_frame, text="Reorder Level:").grid(row=4, column=0, sticky="w", pady=5)
        self.reorder_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.reorder_var, width=40).grid(row=4, column=1, sticky="ew", padx=5)

        ttk.Label(info_frame, text="Cost per Unit ($):").grid(row=5, column=0, sticky="w", pady=5)
        self.cost_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.cost_var, width=40).grid(row=5, column=1, sticky="ew", padx=5)

        info_frame.columnconfigure(1, weight=1)

        # Supplier info
        supplier_frame = ttk.LabelFrame(main_frame, text="Supplier Information", padding="10")
        supplier_frame.pack(fill="x", pady=5)

        ttk.Label(supplier_frame, text="Supplier:").grid(row=0, column=0, sticky="w", pady=5)
        self.supplier_var = tk.StringVar()
        ttk.Entry(supplier_frame, textvariable=self.supplier_var, width=40).grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(supplier_frame, text="Supplier Rating (1-5):").grid(row=1, column=0, sticky="w", pady=5)
        self.rating_var = tk.StringVar(value="5.0")
        rating_scale = ttk.Scale(supplier_frame, from_=1.0, to=5.0, variable=self.rating_var, orient="horizontal")
        rating_scale.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.rating_label = ttk.Label(supplier_frame, text="5.0")
        self.rating_label.grid(row=1, column=2, padx=5)
        
        def update_rating_label(value):
            self.rating_label.config(text=f"{float(value):.1f}")
        
        rating_scale.config(command=update_rating_label)

        supplier_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)

        ttk.Button(button_frame, text="Save", command=self.save_material).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="right")

    def load_material_data(self):
        """Load existing material data for editing."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM raw_materials WHERE id = %s", (self.material_id,))
            material = cursor.fetchone()
            conn.close()
            
            if material:
                self.name_var.set(material['name'])
                self.description_text.insert("1.0", material.get('description', ''))
                self.quantity_var.set(str(material['quantity']))
                self.unit_var.set(material['unit'])
                self.reorder_var.set(str(material['reorder_level']))
                self.cost_var.set(str(material['cost_per_unit']))
                self.supplier_var.set(material.get('supplier', ''))
                self.rating_var.set(str(material['supplier_rating']))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load material data: {str(e)}")

    def save_material(self):
        """Save the material data."""
        # Validate inputs
        name = self.name_var.get().strip()
        description = self.description_text.get("1.0", "end-1c").strip()
        unit = self.unit_var.get().strip()
        supplier = self.supplier_var.get().strip()
        
        try:
            quantity = float(self.quantity_var.get())
            reorder_level = float(self.reorder_var.get())
            cost_per_unit = float(self.cost_var.get())
            supplier_rating = float(self.rating_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values.")
            return
        
        if not name or not unit:
            messagebox.showerror("Error", "Please enter material name and unit.")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.material_id:
                # Update existing material
                cursor.execute("""
                    UPDATE raw_materials 
                    SET name = %s, description = %s, quantity = %s, unit = %s, reorder_level = %s,
                        supplier = %s, supplier_rating = %s, cost_per_unit = %s
                    WHERE id = %s
                """, (name, description, quantity, unit, reorder_level, supplier, supplier_rating, cost_per_unit, self.material_id))
            else:
                # Insert new material
                cursor.execute("""
                    INSERT INTO raw_materials (name, description, quantity, unit, reorder_level, supplier, supplier_rating, cost_per_unit)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, description, quantity, unit, reorder_level, supplier, supplier_rating, cost_per_unit))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Material saved successfully!")
            self.parent.load_materials()
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save material: {str(e)}")


class ProductDetailsDialog(tk.Toplevel):
    """Dialog for viewing detailed product information."""
    def __init__(self, parent, product_id):
        super().__init__(parent)
        self.product_id = product_id
        self.title("Product Details")
        self.geometry("600x500")
        self.grab_set()
        
        self.create_widgets()
        self.load_product_details()

    def create_widgets(self):
        """Create the product details interface."""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Product info display
        self.info_text = tk.Text(main_frame, wrap="word", state="disabled")
        self.info_text.pack(fill="both", expand=True)

        # Scrollbar for text widget
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Close button
        ttk.Button(main_frame, text="Close", command=self.destroy).pack(pady=10)

    def load_product_details(self):
        """Load and display detailed product information."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get product details
            cursor.execute("SELECT * FROM products WHERE id = %s", (self.product_id,))
            product = cursor.fetchone()
            
            # Get raw materials
            cursor.execute("""
                SELECT rm.name, rm.unit, prm.quantity_required, rm.cost_per_unit,
                       (prm.quantity_required * rm.cost_per_unit) as total_cost
                FROM product_raw_materials prm
                JOIN raw_materials rm ON prm.raw_material_id = rm.id
                WHERE prm.product_id = %s
            """, (self.product_id,))
            materials = cursor.fetchall()
            
            conn.close()
            
            # Display information
            self.info_text.config(state="normal")
            self.info_text.delete("1.0", "end")
            
            if product:
                info = f"""PRODUCT DETAILS
{'='*50}

Basic Information:
• Product ID: {product['id']}
• Name: {product['name']}
• Description: {product.get('description', 'N/A')}
• Price: ${product['price']:.2f}
• Stock: {product['stock']} units
• Reorder Level: {product.get('reorder_level', 'N/A')} units

Manufacturing:
• Ready Made: {'Yes' if product.get('is_ready_made') else 'No'}
• Supplier: {product.get('ready_made_supplier', 'N/A')}

Financial Summary:
• Stock Value: ${product['stock'] * product['price']:.2f}
• Created: {product.get('created_at', 'N/A')}

"""
                
                if materials and not product.get('is_ready_made'):
                    info += f"""Raw Materials Required:
{'='*30}
"""
                    total_material_cost = 0
                    for material in materials:
                        info += f"• {material['name']}: {material['quantity_required']:.2f} {material['unit']} @ ${material['cost_per_unit']:.2f}/{material['unit']} = ${material['total_cost']:.2f}\n"
                        total_material_cost += material['total_cost']
                    
                    info += f"\nTotal Raw Material Cost per Unit: ${total_material_cost:.2f}\n"
                    info += f"Profit Margin per Unit: ${product['price'] - total_material_cost:.2f}\n"
                    info += f"Profit Margin %: {((product['price'] - total_material_cost) / product['price'] * 100):.1f}%\n"
                
                self.info_text.insert("1.0", info)
            
            self.info_text.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load product details: {str(e)}")


class MaterialDetailsDialog(tk.Toplevel):
    """Dialog for viewing detailed material information."""
    def __init__(self, parent, material_id):
        super().__init__(parent)
        self.material_id = material_id
        self.title("Material Details")
        self.geometry("500x400")
        self.grab_set()
        
        self.create_widgets()
        self.load_material_details()

    def create_widgets(self):
        """Create the material details interface."""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Material info display
        self.info_text = tk.Text(main_frame, wrap="word", state="disabled")
        self.info_text.pack(fill="both", expand=True)

        # Close button
        ttk.Button(main_frame, text="Close", command=self.destroy).pack(pady=10)

    def load_material_details(self):
        """Load and display detailed material information."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get material details
            cursor.execute("SELECT * FROM raw_materials WHERE id = %s", (self.material_id,))
            material = cursor.fetchone()
            
            # Get products using this material
            cursor.execute("""
                SELECT p.name, prm.quantity_required
                FROM product_raw_materials prm
                JOIN products p ON prm.product_id = p.id
                WHERE prm.raw_material_id = %s
            """, (self.material_id,))
            products = cursor.fetchall()
            
            conn.close()
            
            # Display information
            self.info_text.config(state="normal")
            self.info_text.delete("1.0", "end")
            
            if material:
                stock_status = "LOW STOCK" if material['quantity'] <= material['reorder_level'] else "OK"
                total_value = material['quantity'] * material['cost_per_unit']
                
                info = f"""MATERIAL DETAILS
{'='*50}

Basic Information:
• Material ID: {material['id']}
• Name: {material['name']}
• Description: {material.get('description', 'N/A')}
• Quantity: {material['quantity']:.2f} {material['unit']}
• Unit: {material['unit']}
• Reorder Level: {material['reorder_level']:.2f} {material['unit']}
• Stock Status: {stock_status}

Financial Information:
• Cost per Unit: ${material['cost_per_unit']:.2f}
• Total Stock Value: ${total_value:.2f}

Supplier Information:
• Supplier: {material.get('supplier', 'N/A')}
• Supplier Rating: {material['supplier_rating']:.1f}/5.0

Usage Information:
"""
                
                if products:
                    info += f"Used in {len(products)} product(s):\n"
                    for product in products:
                        info += f"• {product['name']}: {product['quantity_required']:.2f} {material['unit']} per unit\n"
                else:
                    info += "Not currently used in any products.\n"
                
                info += f"\nLast Updated: {material.get('updated_at', 'N/A')}\n"
                
                self.info_text.insert("1.0", info)
            
            self.info_text.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load material details: {str(e)}")
