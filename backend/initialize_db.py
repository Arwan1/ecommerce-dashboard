import mysql.connector
from mysql.connector import Error

def create_tables():
    """
    Creates the necessary tables 
    """
    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host="localhost",  # database host
            user="ecom_user",  # Use the new user
            password="dummypassword1234",  # Use the new password
            database="ecommerce_db"  #  database name
        )

        if connection.is_connected():
            print("✅ Connection successful!")

            cursor = connection.cursor()

            # Create Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                role VARCHAR(20) DEFAULT 'user',
                public_key TEXT,
                confirmation_code INT,        -- Added confirmation_code column
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create Products table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                stock INT NOT NULL,
                reorder_level INT DEFAULT 10,
                is_ready_made TINYINT(1) DEFAULT 1,
                ready_made_supplier VARCHAR(100),
                supplier_rating DECIMAL(3, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create Orders table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                user_id INT,
                total_price DECIMAL(10, 2) NOT NULL,
                status VARCHAR(30) DEFAULT 'Preparing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)

            # Create OrderItems table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
            """)

            # Create ReturnClaims table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS return_claims (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
            """)

            # Create canonical Returns table used by dashboards/analytics
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                reason VARCHAR(255) NOT NULL DEFAULT 'Unspecified',
                status VARCHAR(20) NOT NULL DEFAULT 'Pending',
                refund_amount DECIMAL(10, 2) DEFAULT 0.00,
                admin_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_returns_order FOREIGN KEY (order_id) REFERENCES orders(id),
                CONSTRAINT fk_returns_product FOREIGN KEY (product_id) REFERENCES products(id),
                INDEX idx_returns_order_id (order_id),
                INDEX idx_returns_product_id (product_id),
                INDEX idx_returns_status (status),
                INDEX idx_returns_created_at (created_at)
            )
            """)

            # Insert default admin user
            cursor.execute("""
            INSERT IGNORE INTO users (username, password, email, role)
            VALUES ('admin', SHA2('admin123', 256), 'admin@example.com', 'admin')
            """)

            connection.commit()
            print("✅ Tables created successfully, and default admin user added.")

    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ Connection closed.")

if __name__ == "__main__":
    create_tables()
