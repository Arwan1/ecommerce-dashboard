import mysql.connector
from mysql.connector import Error

def update_inventory_schema():
    """
    Add inventory-related tables for raw materials and product relationships.
    """
    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host="localhost",
            user="ecom_user",
            password="dummypassword1234",
            database="ecommerce_db"
        )

        if connection.is_connected():
            print("✅ Connection successful!")

            cursor = connection.cursor()

            # Create Raw Materials table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_materials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
                unit VARCHAR(20) NOT NULL DEFAULT 'pcs',
                reorder_level DECIMAL(10, 2) NOT NULL DEFAULT 10,
                supplier VARCHAR(100),
                supplier_rating DECIMAL(3, 2) DEFAULT 5.00,
                cost_per_unit DECIMAL(10, 2) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """)

            # Create Product Raw Materials relationship table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_raw_materials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                raw_material_id INT NOT NULL,
                quantity_required DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (raw_material_id) REFERENCES raw_materials(id) ON DELETE CASCADE,
                UNIQUE KEY unique_product_material (product_id, raw_material_id)
            )
            """)

            # Add additional columns to products table if not exists
            cursor.execute("SHOW COLUMNS FROM products LIKE 'is_ready_made'")
            if not cursor.fetchone():
                cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN is_ready_made BOOLEAN DEFAULT FALSE,
                ADD COLUMN ready_made_supplier VARCHAR(100) DEFAULT NULL,
                ADD COLUMN reorder_level INT DEFAULT 10
                """)
                print("✅ Added new columns to products table")

            connection.commit()
            print("✅ Inventory schema updated successfully!")

            # Insert sample raw materials
            print("📦 Creating sample raw materials...")
            raw_materials = [
                ("Steel", "High-grade steel sheets", 500.0, "kg", 50.0, "SteelCorp Industries", 4.5, 2.50),
                ("Aluminum", "Lightweight aluminum bars", 300.0, "kg", 30.0, "MetalWorks Ltd", 4.2, 3.75),
                ("Plastic", "Durable plastic pellets", 1000.0, "kg", 100.0, "PlasticSource Co", 4.8, 1.25),
                ("Fabric", "High-quality cotton fabric", 200.0, "m", 20.0, "TextilePlus", 4.6, 8.50),
                ("Electronics", "Circuit boards and components", 150.0, "pcs", 15.0, "TechSupply Inc", 4.3, 15.00),
                ("Glass", "Tempered glass panels", 80.0, "pcs", 10.0, "GlassMaster", 4.7, 12.00),
                ("Wood", "Premium hardwood planks", 250.0, "m", 25.0, "WoodCraft Supplies", 4.4, 6.75),
                ("Leather", "Genuine leather sheets", 120.0, "m2", 12.0, "LeatherWorld", 4.1, 18.50),
            ]

            for material in raw_materials:
                cursor.execute("""
                INSERT IGNORE INTO raw_materials (name, description, quantity, unit, reorder_level, supplier, supplier_rating, cost_per_unit) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, material)

            # Create sample product-raw material relationships
            print("🔗 Creating product-raw material relationships...")
            
            # Get product IDs
            cursor.execute("SELECT id FROM products LIMIT 10")
            products = cursor.fetchall()
            
            cursor.execute("SELECT id FROM raw_materials")
            materials = cursor.fetchall()
            
            if products and materials:
                # Example relationships (you can customize these)
                relationships = [
                    (products[0][0], materials[0][0], 2.5),  # First product uses 2.5kg steel
                    (products[0][0], materials[2][0], 0.5),  # First product uses 0.5kg plastic
                    (products[1][0], materials[1][0], 1.8),  # Second product uses 1.8kg aluminum
                    (products[1][0], materials[4][0], 2.0),  # Second product uses 2 electronic components
                    (products[2][0], materials[3][0], 1.2),  # Third product uses 1.2m fabric
                    (products[2][0], materials[7][0], 0.8),  # Third product uses 0.8m2 leather
                ]
                
                for rel in relationships:
                    cursor.execute("""
                    INSERT IGNORE INTO product_raw_materials (product_id, raw_material_id, quantity_required) 
                    VALUES (%s, %s, %s)
                    """, rel)
                
                # Mark some products as ready-made
                if len(products) > 5:
                    cursor.execute("UPDATE products SET is_ready_made = TRUE, ready_made_supplier = 'ReadyMade Supplies Inc' WHERE id = %s", (products[5][0],))
                    cursor.execute("UPDATE products SET is_ready_made = TRUE, ready_made_supplier = 'QuickProducts Ltd' WHERE id = %s", (products[6][0],))

            connection.commit()
            print("✅ Sample inventory data created successfully!")

    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ Connection closed.")

if __name__ == "__main__":
    update_inventory_schema()
