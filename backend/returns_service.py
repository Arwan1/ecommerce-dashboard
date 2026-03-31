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


class ReturnsService:
    RETURN_EXPORT_COLUMNS = [
        "return_id",
        "order_id",
        "product_id",
        "product_name",
        "reason",
        "status",
        "refund_amount",
        "admin_notes",
        "created_at",
        "updated_at",
    ]
    RETURN_STATUS_ALIASES = {
        "pending": "Pending",
        "new": "Pending",
        "open": "Pending",
        "approved": "Approved",
        "accept": "Approved",
        "accepted": "Approved",
        "rejected": "Rejected",
        "reject": "Rejected",
        "denied": "Rejected",
    }

    @staticmethod
    def _normalize_status(status):
        normalized = _normalize_key(status)
        return ReturnsService.RETURN_STATUS_ALIASES.get(normalized, "Pending")

    @staticmethod
    def _resolve_product(cursor, product_id_value="", product_name_value=""):
        product_id_value = str(product_id_value or "").strip()
        product_name_value = str(product_name_value or "").strip()

        if product_id_value:
            cursor.execute(
                """
                SELECT id, name
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
                SELECT id, name
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
    def get_returns_for_csv(return_ids=None):
        """Load returns in a CSV-friendly format."""
        if return_ids is not None and not return_ids:
            return []

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    r.id AS return_id,
                    r.order_id,
                    r.product_id,
                    p.name AS product_name,
                    r.reason,
                    r.status,
                    r.refund_amount,
                    r.admin_notes,
                    r.created_at,
                    r.updated_at
                FROM returns r
                LEFT JOIN products p ON p.id = r.product_id
            """
            params = []

            if return_ids is not None:
                placeholders = ", ".join(["%s"] * len(return_ids))
                query += f" WHERE r.id IN ({placeholders})"
                params.extend(return_ids)

            query += " ORDER BY r.created_at DESC, r.id DESC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            export_rows = []
            for row in rows:
                created_at = row.get("created_at")
                updated_at = row.get("updated_at")
                export_rows.append(
                    {
                        "return_id": row.get("return_id", ""),
                        "order_id": row.get("order_id", ""),
                        "product_id": row.get("product_id", ""),
                        "product_name": row.get("product_name", "") or "",
                        "reason": row.get("reason", "") or "",
                        "status": row.get("status", "Pending"),
                        "refund_amount": f"{float(row.get('refund_amount') or 0.0):.2f}",
                        "admin_notes": row.get("admin_notes", "") or "",
                        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if created_at
                        else "",
                        "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S")
                        if updated_at
                        else "",
                    }
                )

            return export_rows
        finally:
            if conn:
                conn.close()

    @staticmethod
    def export_returns_to_csv(file_path, return_ids=None):
        """Write returns to a CSV file."""
        rows = ReturnsService.get_returns_for_csv(return_ids=return_ids)
        CSVHandler.write_dict_rows(file_path, ReturnsService.RETURN_EXPORT_COLUMNS, rows)
        return len(rows)

    @staticmethod
    def import_returns_from_csv(file_path):
        """Import returns from a CSV file."""
        raw_rows = CSVHandler.load_dict_rows(file_path)
        if not raw_rows:
            raise ValueError("The selected CSV file does not contain any data rows.")

        conn = None
        imported_returns = 0
        errors = []

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            for row_number, raw_row in enumerate(raw_rows, start=2):
                row = _normalize_row(raw_row)
                if not any(row.values()):
                    continue

                try:
                    order_id = _parse_int(
                        _first_value(row, "order_id", "order_number", "reference_order_id"),
                        f"Row {row_number} order ID",
                    )
                    cursor.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
                    order = cursor.fetchone()
                    if not order:
                        raise ValueError(f"Order {order_id} does not exist.")

                    product = ReturnsService._resolve_product(
                        cursor,
                        product_id_value=_first_value(row, "product_id", "item_id", "sku"),
                        product_name_value=_first_value(
                            row, "product_name", "product", "item", "item_name"
                        ),
                    )
                    reason = _first_value(row, "reason", "return_reason") or "Unspecified"
                    status = ReturnsService._normalize_status(
                        _first_value(row, "status", "return_status")
                    )
                    refund_amount = _parse_float(
                        _first_value(row, "refund_amount", "refund", "refund_value"),
                        f"Row {row_number} refund amount",
                        allow_blank=True,
                    )
                    admin_notes = _first_value(row, "admin_notes", "notes", "comment")
                    created_at = _parse_datetime(
                        _first_value(row, "created_at", "date", "return_date")
                    )
                    updated_at = _parse_datetime(
                        _first_value(row, "updated_at", "last_updated")
                    )
                    if created_at and not updated_at:
                        updated_at = created_at

                    if created_at and updated_at:
                        cursor.execute(
                            """
                            INSERT INTO returns (
                                order_id, product_id, reason, status, refund_amount,
                                admin_notes, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                order_id,
                                product["id"],
                                reason,
                                status,
                                refund_amount if refund_amount is not None else 0.0,
                                admin_notes or None,
                                created_at,
                                updated_at,
                            ),
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO returns (
                                order_id, product_id, reason, status, refund_amount, admin_notes
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                order_id,
                                product["id"],
                                reason,
                                status,
                                refund_amount if refund_amount is not None else 0.0,
                                admin_notes or None,
                            ),
                        )

                    conn.commit()
                    imported_returns += 1
                except Exception as exc:
                    conn.rollback()
                    errors.append(f"Row {row_number}: {exc}")

            return {
                "imported_returns": imported_returns,
                "failed_returns": len(errors),
                "errors": errors,
            }
        finally:
            if conn:
                conn.close()
