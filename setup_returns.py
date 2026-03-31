from database.db_connector import get_db_connection
import mysql.connector


def column_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table_name, column_name)
    )
    return cursor.fetchone()[0] > 0


def index_exists(cursor, table_name, index_name):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME = %s
        """,
        (table_name, index_name)
    )
    return cursor.fetchone()[0] > 0


def ensure_column(cursor, table_name, column_name, definition):
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
        print(f"Added {table_name}.{column_name}")


def ensure_index(cursor, table_name, index_name, column_name):
    if not index_exists(cursor, table_name, index_name):
        cursor.execute(f"CREATE INDEX {index_name} ON {table_name} ({column_name})")
        print(f"Added index {index_name} on {table_name}({column_name})")


def ensure_supporting_columns(cursor):
    ensure_column(cursor, "orders", "status", "VARCHAR(30) DEFAULT 'Preparing'")
    ensure_column(cursor, "products", "reorder_level", "INT DEFAULT 10")
    ensure_column(cursor, "products", "is_ready_made", "TINYINT(1) DEFAULT 1")
    ensure_column(cursor, "products", "ready_made_supplier", "VARCHAR(100) NULL")
    ensure_column(cursor, "products", "supplier_rating", "DECIMAL(3, 2) NULL")


def ensure_returns_schema(cursor):
    cursor.execute(
        """
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
            CONSTRAINT fk_returns_product FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """
    )

    required_columns = {
        "order_id": "INT NOT NULL",
        "product_id": "INT NOT NULL",
        "reason": "VARCHAR(255) NOT NULL DEFAULT 'Unspecified'",
        "status": "VARCHAR(20) NOT NULL DEFAULT 'Pending'",
        "refund_amount": "DECIMAL(10, 2) DEFAULT 0.00",
        "admin_notes": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    }

    for column_name, definition in required_columns.items():
        ensure_column(cursor, "returns", column_name, definition)

    ensure_index(cursor, "returns", "idx_returns_order_id", "order_id")
    ensure_index(cursor, "returns", "idx_returns_product_id", "product_id")
    ensure_index(cursor, "returns", "idx_returns_status", "status")
    ensure_index(cursor, "returns", "idx_returns_created_at", "created_at")


def migrate_return_claims(cursor):
    if not column_exists(cursor, "return_claims", "order_id"):
        return 0

    cursor.execute(
        """
        INSERT INTO returns (
            order_id,
            product_id,
            reason,
            status,
            refund_amount,
            admin_notes,
            created_at,
            updated_at
        )
        SELECT
            rc.order_id,
            first_item.product_id,
            'Imported from return_claims',
            'Pending',
            0.00,
            'Auto-migrated from return_claims because a canonical returns row was missing.',
            rc.scan_timestamp,
            rc.scan_timestamp
        FROM return_claims rc
        INNER JOIN (
            SELECT order_id, MIN(product_id) AS product_id
            FROM order_items
            GROUP BY order_id
        ) first_item ON first_item.order_id = rc.order_id
        LEFT JOIN returns r ON r.order_id = rc.order_id
        WHERE r.id IS NULL
        """
    )
    return cursor.rowcount


def setup_returns_schema():
    conn = get_db_connection()
    if not conn:
        print("Could not connect to database.")
        return

    try:
        cursor = conn.cursor()
        ensure_supporting_columns(cursor)
        ensure_returns_schema(cursor)
        migrated_rows = migrate_return_claims(cursor)
        conn.commit()
        print(f"Returns schema is ready. Migrated {migrated_rows} return_claim rows into returns.")
    except mysql.connector.Error as exc:
        conn.rollback()
        print(f"Failed to set up returns schema: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    setup_returns_schema()
