from database.db_operations import DBOperations

class OrderManager:
    """
    Handles all logic related to order management.
    """
    def __init__(self):
        self.db_ops = DBOperations()

    def get_all_orders(self):
        """Retrieves all orders."""
        return self.db_ops.get_all_orders()

    def create_order(self, customer_info, product_list):
        """
        Creates a new order and updates inventory.
        1. Check if all products are in stock.
        2. Create the order record.
        3. Deduct items from inventory.
        """
        # Step 1: Check stock (pseudo-code)
        # for product in product_list:
        #     if not self.inventory_manager.is_in_stock(product['id'], product['quantity']):
        #         raise ValueError(f"Not enough stock for {product['name']}")

        # Step 2: Create order record
        order_data = { "customer": customer_info, "products": product_list, "status": "Pending" }
        order_id = self.db_ops.add_order(order_data)

        # Step 3: Update inventory
        # for product in product_list:
        #     self.db_ops.update_inventory_quantity(product['id'], -product['quantity'])
        
        print(f"Order {order_id} created successfully.")
        return order_id

    def update_order_status(self, order_id, new_status):
        """Updates the status of an order (e.g., 'Shipped', 'Delivered')."""
        # return self.db_ops.update_order(order_id, {"status": new_status})
        pass

    def search_orders(self, search_term):
        """Searches for orders based on ID, buyer info, etc."""
        # return self.db_ops.search_orders(search_term)
        pass
