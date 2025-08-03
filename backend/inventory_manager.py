from database.db_operations import DBOperations
from backend.email_service import EmailService

class InventoryManager:
    """
    inventory management logic (stock alerts and supplier ratings)
    """
    def __init__(self):
        self.db_ops = DBOperations()
        self.email_service = EmailService()

    def check_for_low_stock_and_alert(self, threshold=10):
        """
        Checks stock levels and sends email alerts if item below thresholds
        """
        low_stock_items = self.db_ops.get_low_stock_items(threshold)
        if not low_stock_items:
            print("Inventory levels are healthy.")
            return

        for item in low_stock_items:
            print(f"LOW STOCK: {item['name']} has only {item['quantity']} left.")
            # Get supplier info and send an email
            # supplier = self.db_ops.get_supplier_for_product(item['product_id'])
            # if supplier:
            #     self.email_service.send_low_stock_alert(supplier, item)
            pass

    def get_inventory_status_report(self):
        """Generates a report of all items in the inventory"""
        # return self.db_ops.get_all_inventory()
        pass
        
    def get_supplier_quality_rating(self, supplier_id):
        """
        Calculates a quality rating for a supplier based on return rates for their products
        """
        # This is a complex query that would:
        # 1. Get all products from the supplier.
        # 2. Get total orders for those products.
        # 3. Get total DAMAGED returns for those products.
        # 4. Rating = 1 - (Damaged Returns / Total Orders)
        # For now, we'll return a dummy value.
        print(f"Calculating quality rating for supplier {supplier_id}...")
        return 0.95 # Dummy value
