from datetime import datetime

from database.db_connector import get_db_connection
from utils.csv_handler import CSVHandler


def _normalize_key(value):
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_row(raw_row):
    normalized = {}
    for key, value in raw_row.items():
        normalized[_normalize_key(key)] = str(value or "").strip()
    return normalized


def _first_value(row, *keys):
    for key in keys:
        value = row.get(_normalize_key(key), "")
        if value:
            return value
    return ""


def _parse_datetime(value):
    value = str(value or "").strip()
    if not value:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Unsupported date format: {value}") from exc


def _parse_int(value, field_name):
    value = str(value or "").strip()
    if not value:
        raise ValueError(f"{field_name} is required.")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a whole number.") from exc


def _parse_float(value, field_name, allow_blank=False):
    value = str(value or "").strip().replace("$", "").replace(",", "")
    if not value:
        if allow_blank:
            return None
        raise ValueError(f"{field_name} is required.")
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number.") from exc


class OrderService:
    INVENTORY_COMMITTED_STATUSES = {"dispatched", "delivered"}
    ORDER_EXPORT_COLUMNS = [
        "order_id",
        "customer_name",
        "status",
        "created_at",
        "total_price",
        "product_id",
        "product_name",
        "quantity",
        "unit_price",
        "line_subtotal",
    ]
    ORDER_STATUS_ALIASES = {
        "preparing": "Preparing",
        "pending": "Preparing",
        "new": "Preparing",
        "draft": "Preparing",
        "dispatched": "Dispatched",
        "shipped": "Dispatched",
        "in_transit": "Dispatched",
        "delivered": "Delivered",
        "fulfilled": "Delivered",
        "complete": "Delivered",
        "completed": "Delivered",
    }

    @staticmethod
    def _status_commits_inventory(status):
        """Return True when an order status should consume stock."""
        return str(status or "").strip().lower() in OrderService.INVENTORY_COMMITTED_STATUSES

    @staticmethod
    def _normalize_status(status):
        normalized = _normalize_key(status)
        return OrderService.ORDER_STATUS_ALIASES.get(normalized, "Preparing")

    @staticmethod
    def _get_order_items(cursor, order_id):
        """Load the products attached to an order for inventory operations."""
        cursor.execute(
            """
            SELECT oi.product_id, oi.quantity, p.name, p.stock
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = %s
            """,
            (order_id,),
        )
        return cursor.fetchall()

    @staticmethod
    def _ensure_inventory_available(order_items):
        """Fail fast when an order cannot move into a stock-consuming status."""
        shortages = []
        for item in order_items:
            available_stock = int(item.get("stock") or 0)
            required_quantity = int(item.get("quantity") or 0)
            product_name = item.get("name") or f"Product {item['product_id']}"
            if required_quantity > available_stock:
                shortages.append(
                    f"{product_name} "
                    f"(need {required_quantity}, have {available_stock})"
                )

        if shortages:
            raise ValueError(
                "Insufficient stock to dispatch this order: " + ", ".join(shortages)
            )

    @staticmethod
    def _apply_inventory_delta(cursor, order_items, multiplier):
        """Apply an inventory change for each line item in an order."""
        for item in order_items:
            quantity_delta = int(item.get("quantity") or 0) * multiplier
            cursor.execute(
                """
                UPDATE products
                SET stock = stock + %s
                WHERE id = %s
                """,
                (quantity_delta, item["product_id"]),
            )

    @staticmethod
    def _resolve_product(cursor, product_id_value="", product_name_value=""):
        product_id_value = str(product_id_value or "").strip()
        product_name_value = str(product_name_value or "").strip()

        if product_id_value:
            cursor.execute(
                """
                SELECT id, name, price, stock
                FROM products
                WHERE id = %s
                """,
                (product_id_value,),
            )
            product = cursor.fetchone()
            if product:
                return product

        if product_name_value:
            cursor.execute(
                """
                SELECT id, name, price, stock
                FROM products
                WHERE LOWER(TRIM(name)) = %s
                LIMIT 1
                """,
                (product_name_value.lower(),),
            )
            product = cursor.fetchone()
            if product:
                return product

        raise ValueError(
            f"Could not match product '{product_name_value or product_id_value}'."
        )

    @staticmethod
    def _insert_order(cursor, customer_name, total_price, status, created_at=None):
        if created_at:
            cursor.execute(
                """
                INSERT INTO orders (customer_name, total_price, status, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (customer_name, total_price, status, created_at),
            )
        else:
            cursor.execute(
                """
                INSERT INTO orders (customer_name, total_price, status, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (customer_name, total_price, status),
            )
        return cursor.lastrowid

    @staticmethod
    def get_all_products():
        """Get all available products."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, price, stock FROM products WHERE stock > 0")
            products = cursor.fetchall()
            conn.close()
            return products
        except Exception as e:
            print(f"Error getting products: {e}")
            return []

    @staticmethod
    def create_order_in_db(customer_name, order_items, total_price):
        """Create a new order in the database."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            for item in order_items:
                cursor.execute(
                    """
                    SELECT id, name, stock
                    FROM products
                    WHERE id = %s
                    """,
                    (item["product_id"],),
                )
                product = cursor.fetchone()
                if not product:
                    raise ValueError(f"Product {item['product_id']} does not exist.")
                if int(item["quantity"]) <= 0:
                    raise ValueError(f"Quantity must be greater than 0 for {product['name']}.")
                if int(item["quantity"]) > int(product.get("stock") or 0):
                    raise ValueError(
                        f"Not enough stock for {product['name']}. "
                        f"Requested {item['quantity']}, available {product.get('stock', 0)}."
                    )

            order_id = OrderService._insert_order(
                cursor, customer_name, total_price, "Preparing"
            )

            for item in order_items:
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, item["product_id"], item["quantity"], item["price"]),
                )
            conn.commit()
            conn.close()
            return True
        except ValueError:
            if conn:
                conn.rollback()
                conn.close()
            raise
        except Exception as e:
            print(f"Error creating order: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    @staticmethod
    def delete_order_and_restore_inventory(order_id):
        """Delete an order and restore inventory when it had already been dispatched."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
            order = cursor.fetchone()
            if not order:
                conn.close()
                return False

            order_items = OrderService._get_order_items(cursor, order_id)
            if OrderService._status_commits_inventory(order.get("status")):
                OrderService._apply_inventory_delta(cursor, order_items, 1)

            cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting order: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    @staticmethod
    def get_order_details(order_id):
        """Get full order details from the database."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = cursor.fetchone()
            conn.close()
            return order
        except Exception as e:
            print(f"Error getting order details: {e}")
            return None

    @staticmethod
    def update_order_details(order_id, customer_name, total_price, status):
        """Update order details and keep inventory aligned with status transitions."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, status
                FROM orders
                WHERE id = %s
                """,
                (order_id,),
            )
            existing_order = cursor.fetchone()
            if not existing_order:
                conn.close()
                return False

            previous_status = existing_order.get("status")
            normalized_status = OrderService._normalize_status(status)
            order_items = OrderService._get_order_items(cursor, order_id)
            was_inventory_committed = OrderService._status_commits_inventory(previous_status)
            is_inventory_committed = OrderService._status_commits_inventory(normalized_status)

            if not was_inventory_committed and is_inventory_committed:
                OrderService._ensure_inventory_available(order_items)
                OrderService._apply_inventory_delta(cursor, order_items, -1)
            elif was_inventory_committed and not is_inventory_committed:
                OrderService._apply_inventory_delta(cursor, order_items, 1)

            cursor.execute(
                """
                UPDATE orders
                SET customer_name = %s, total_price = %s, status = %s
                WHERE id = %s
                """,
                (customer_name, total_price, normalized_status, order_id),
            )
            conn.commit()
            conn.close()
            return True
        except ValueError:
            if conn:
                conn.rollback()
                conn.close()
            raise
        except Exception as e:
            print(f"Error updating order: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    @staticmethod
    def get_orders_for_csv(order_ids=None):
        """Return order rows in a line-item CSV-friendly format."""
        if order_ids is not None and not order_ids:
            return []

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    o.id AS order_id,
                    o.customer_name,
                    o.status,
                    o.created_at,
                    o.total_price,
                    oi.product_id,
                    oi.quantity,
                    oi.price,
                    p.name AS product_name
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.id
                LEFT JOIN products p ON p.id = oi.product_id
            """
            params = []

            if order_ids is not None:
                placeholders = ", ".join(["%s"] * len(order_ids))
                query += f" WHERE o.id IN ({placeholders})"
                params.extend(order_ids)

            query += " ORDER BY o.created_at DESC, o.id DESC, oi.id ASC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            export_rows = []
            for row in rows:
                quantity = int(row.get("quantity") or 0)
                unit_price = float(row.get("price") or 0.0)
                line_subtotal = quantity * unit_price if row.get("product_id") else ""
                created_at = row.get("created_at")

                export_rows.append(
                    {
                        "order_id": row.get("order_id", ""),
                        "customer_name": row.get("customer_name", ""),
                        "status": row.get("status", "Preparing"),
                        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if created_at
                        else "",
                        "total_price": f"{float(row.get('total_price') or 0.0):.2f}",
                        "product_id": row.get("product_id", "") or "",
                        "product_name": row.get("product_name", "") or "",
                        "quantity": quantity if row.get("product_id") else "",
                        "unit_price": f"{unit_price:.2f}" if row.get("product_id") else "",
                        "line_subtotal": f"{line_subtotal:.2f}"
                        if row.get("product_id")
                        else "",
                    }
                )

            return export_rows
        finally:
            if conn:
                conn.close()

    @staticmethod
    def export_orders_to_csv(file_path, order_ids=None):
        """Write selected orders to a CSV file."""
        rows = OrderService.get_orders_for_csv(order_ids=order_ids)
        CSVHandler.write_dict_rows(file_path, OrderService.ORDER_EXPORT_COLUMNS, rows)
        return len(rows)

    @staticmethod
    def import_orders_from_csv(file_path):
        """Import orders from a line-item CSV format."""
        raw_rows = CSVHandler.load_dict_rows(file_path)
        grouped_orders = {}

        for row_number, raw_row in enumerate(raw_rows, start=2):
            row = _normalize_row(raw_row)
            if not any(row.values()):
                continue

            customer_name = _first_value(
                row,
                "customer_name",
                "customer",
                "customer_full_name",
                "buyer",
                "buyer_name",
            )
            if not customer_name:
                raise ValueError(f"Row {row_number}: customer name is required.")

            group_key = _first_value(
                row,
                "external_order_id",
                "external_id",
                "order_group",
                "order_reference",
                "reference",
                "order_number",
                "order_id",
            ) or f"row-{row_number}"

            quantity = _parse_int(
                _first_value(row, "quantity", "qty", "item_quantity"),
                f"Row {row_number} quantity",
            )
            if quantity <= 0:
                raise ValueError(f"Row {row_number}: quantity must be greater than 0.")

            grouped_order = grouped_orders.setdefault(
                group_key,
                {
                    "customer_name": customer_name,
                    "status": _first_value(row, "status", "order_status"),
                    "created_at": _first_value(row, "created_at", "order_date", "date"),
                    "total_price": _first_value(row, "total_price", "order_total", "total"),
                    "items": [],
                },
            )

            if grouped_order["customer_name"] != customer_name:
                raise ValueError(
                    f"Row {row_number}: order group '{group_key}' mixes multiple customers."
                )

            grouped_order["items"].append(
                {
                    "row_number": row_number,
                    "product_id": _first_value(row, "product_id", "item_id", "sku"),
                    "product_name": _first_value(
                        row, "product_name", "product", "item", "item_name"
                    ),
                    "quantity": quantity,
                    "unit_price": _first_value(
                        row, "unit_price", "price", "item_price", "sale_price"
                    ),
                }
            )

        if not grouped_orders:
            raise ValueError("The selected CSV file does not contain any importable orders.")

        conn = None
        imported_orders = 0
        imported_rows = 0
        errors = []

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            for group_key, order_data in grouped_orders.items():
                try:
                    prepared_items = []
                    for item in order_data["items"]:
                        product = OrderService._resolve_product(
                            cursor,
                            product_id_value=item["product_id"],
                            product_name_value=item["product_name"],
                        )
                        unit_price = _parse_float(
                            item["unit_price"],
                            f"Row {item['row_number']} unit price",
                            allow_blank=True,
                        )
                        prepared_items.append(
                            {
                                "product_id": product["id"],
                                "name": product["name"],
                                "stock": product.get("stock", 0),
                                "quantity": item["quantity"],
                                "price": unit_price
                                if unit_price is not None
                                else float(product.get("price") or 0.0),
                            }
                        )

                    status = OrderService._normalize_status(order_data["status"])
                    if OrderService._status_commits_inventory(status):
                        OrderService._ensure_inventory_available(prepared_items)

                    computed_total = sum(
                        float(item["price"]) * int(item["quantity"])
                        for item in prepared_items
                    )
                    total_price = _parse_float(
                        order_data["total_price"],
                        f"Order group {group_key} total price",
                        allow_blank=True,
                    )
                    if total_price is None:
                        total_price = computed_total

                    created_at = _parse_datetime(order_data["created_at"])
                    order_id = OrderService._insert_order(
                        cursor,
                        order_data["customer_name"],
                        total_price,
                        status,
                        created_at=created_at,
                    )

                    for item in prepared_items:
                        cursor.execute(
                            """
                            INSERT INTO order_items (order_id, product_id, quantity, price)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                order_id,
                                item["product_id"],
                                item["quantity"],
                                item["price"],
                            ),
                        )

                    if OrderService._status_commits_inventory(status):
                        OrderService._apply_inventory_delta(cursor, prepared_items, -1)

                    conn.commit()
                    imported_orders += 1
                    imported_rows += len(prepared_items)
                except Exception as exc:
                    conn.rollback()
                    errors.append(f"{group_key}: {exc}")

            return {
                "imported_orders": imported_orders,
                "imported_rows": imported_rows,
                "failed_orders": len(errors),
                "errors": errors,
            }
        finally:
            if conn:
                conn.close()
