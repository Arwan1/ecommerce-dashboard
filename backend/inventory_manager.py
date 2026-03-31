from database.db_operations import DBOperations
from backend.email_service import EmailService
from database.db_connector import get_db_connection

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

    def _get_sql_time_condition(self, alias, time_period):
        """Build a reusable SQL date condition for the selected lookback period."""
        if time_period == "Last 7 Days":
            return f"{alias}.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
        if time_period == "Last 30 Days":
            return f"{alias}.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
        if time_period == "Last 90 Days":
            return f"{alias}.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)"
        if time_period == "Last Year":
            return f"{alias}.created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR)"
        return "1=1"

    def _get_supplier_type_clause(self, supplier_type):
        """Return the SQL predicate for the requested supplier category."""
        if supplier_type == "Finished Products":
            return "AND p.is_ready_made = 1"
        if supplier_type == "Raw Materials":
            return "AND p.is_ready_made = 0"
        return ""

    def _describe_supplier_status(self, rating):
        """Convert a numeric rating into a user-facing status label."""
        if rating >= 4.5:
            return "Excellent"
        if rating >= 4.0:
            return "Strong"
        if rating >= 3.2:
            return "Stable"
        if rating >= 2.5:
            return "Watch"
        return "At Risk"

    def _describe_rating_confidence(self, total_ordered):
        """Confidence improves as more fulfilled order lines are observed."""
        if total_ordered >= 40:
            return "High"
        if total_ordered >= 15:
            return "Moderate"
        return "Low"

    def _score_supplier_metrics(self, metrics):
        """Turn supplier performance metrics into a 1-5 quality rating."""
        total_ordered = int(metrics.get('total_ordered') or 0)
        total_returned = int(metrics.get('total_returned') or 0)
        quality_issue_returns = int(metrics.get('quality_issue_returns') or 0)
        total_sales_value = float(metrics.get('total_sales_value') or 0)
        total_refunded = float(metrics.get('total_refunded') or 0)

        return_rate = (total_returned / total_ordered * 100.0) if total_ordered else 0.0
        quality_issue_rate = (quality_issue_returns / total_ordered * 100.0) if total_ordered else 0.0
        refund_rate = (total_refunded / total_sales_value * 100.0) if total_sales_value else 0.0
        volume_bonus = min(total_ordered, 40) / 40 * 6

        score = 100.0
        score -= return_rate * 3.6
        score -= quality_issue_rate * 2.4
        score -= refund_rate * 1.2
        score += volume_bonus

        if total_ordered == 0 and total_returned == 0:
            score = 50.0

        score = max(20.0, min(98.0, score))
        rating = round(score / 20.0, 1)

        return {
            'rating': max(1.0, min(5.0, rating)),
            'score_percent': round(score, 1),
            'return_rate_percent': round(return_rate, 2),
            'quality_issue_rate_percent': round(quality_issue_rate, 2),
            'refund_rate_percent': round(refund_rate, 2),
            'confidence_label': self._describe_rating_confidence(total_ordered),
            'status_label': self._describe_supplier_status(rating)
        }

    def _score_raw_material_supplier_metrics(self, metrics):
        """Blend manual raw-material ratings with downstream product outcomes."""
        material_count = int(metrics.get('product_count') or 0)
        total_ordered = int(metrics.get('total_ordered') or 0)
        total_returned = int(metrics.get('total_returned') or 0)
        quality_issue_returns = int(metrics.get('quality_issue_returns') or 0)
        total_sales_value = float(metrics.get('total_sales_value') or 0)
        total_refunded = float(metrics.get('total_refunded') or 0)
        avg_manual_rating = float(metrics.get('avg_manual_rating') or 0.0)

        manual_rating = avg_manual_rating if avg_manual_rating > 0 else 3.0
        return_rate = (total_returned / total_ordered * 100.0) if total_ordered else 0.0
        quality_issue_rate = (quality_issue_returns / total_ordered * 100.0) if total_ordered else 0.0
        refund_rate = (total_refunded / total_sales_value * 100.0) if total_sales_value else 0.0

        score = manual_rating * 20.0
        score -= return_rate * 1.8
        score -= quality_issue_rate * 1.2
        score -= refund_rate * 0.8
        score += min(material_count, 12) * 0.6

        score = max(20.0, min(98.0, score))
        rating = round(score / 20.0, 1)

        confidence_source = max(total_ordered, material_count * 4)
        return {
            'rating': max(1.0, min(5.0, rating)),
            'score_percent': round(score, 1),
            'return_rate_percent': round(return_rate, 2),
            'quality_issue_rate_percent': round(quality_issue_rate, 2),
            'refund_rate_percent': round(refund_rate, 2),
            'confidence_label': self._describe_rating_confidence(confidence_source),
            'status_label': self._describe_supplier_status(rating)
        }

    def _build_supplier_snapshot(self, row, rating_snapshot):
        """Normalize supplier dictionaries for the dashboards."""
        return {
            'supplier_name': row['supplier_name'],
            'supplier_type': row['supplier_type'],
            'product_count': int(row.get('product_count') or 0),
            'total_ordered': int(row.get('total_ordered') or 0),
            'total_units_sold': int(round(float(row.get('total_units_sold') or 0))),
            'total_returned': int(row.get('total_returned') or 0),
            'quality_issue_returns': int(row.get('quality_issue_returns') or 0),
            'avg_order_value': float(row.get('avg_order_value') or 0.0),
            'avg_refund_amount': float(row.get('avg_refund_amount') or 0.0),
            'total_refunded': float(row.get('total_refunded') or 0.0),
            'total_sales_value': float(row.get('total_sales_value') or 0.0),
            'rating': rating_snapshot['rating'],
            'score_percent': rating_snapshot['score_percent'],
            'return_rate_percent': rating_snapshot['return_rate_percent'],
            'quality_issue_rate_percent': rating_snapshot['quality_issue_rate_percent'],
            'refund_rate_percent': rating_snapshot['refund_rate_percent'],
            'confidence_label': rating_snapshot['confidence_label'],
            'status_label': rating_snapshot['status_label']
        }

    def _get_finished_product_supplier_overview(self, time_period):
        """Supplier overview for ready-made product suppliers."""
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            order_condition = self._get_sql_time_condition("o", time_period)
            return_condition = self._get_sql_time_condition("r", time_period)
            query = f"""
                SELECT
                    p.ready_made_supplier AS supplier_name,
                    'Finished Products' AS supplier_type,
                    COUNT(DISTINCT p.id) AS product_count,
                    COALESCE(SUM(order_metrics.total_ordered), 0) AS total_ordered,
                    COALESCE(SUM(order_metrics.total_units_sold), 0) AS total_units_sold,
                    COALESCE(SUM(order_metrics.total_sales_value), 0) AS total_sales_value,
                    ROUND(AVG(NULLIF(order_metrics.avg_order_value, 0)), 2) AS avg_order_value,
                    COALESCE(SUM(return_metrics.total_returned), 0) AS total_returned,
                    COALESCE(SUM(return_metrics.quality_issue_returns), 0) AS quality_issue_returns,
                    ROUND(AVG(NULLIF(return_metrics.avg_refund_amount, 0)), 2) AS avg_refund_amount,
                    COALESCE(SUM(return_metrics.total_refunded), 0) AS total_refunded
                FROM products p
                LEFT JOIN (
                    SELECT
                        oi.product_id,
                        COUNT(DISTINCT oi.id) AS total_ordered,
                        COALESCE(SUM(oi.quantity), 0) AS total_units_sold,
                        COALESCE(SUM(oi.quantity * oi.price), 0) AS total_sales_value,
                        ROUND(COALESCE(AVG(oi.quantity * oi.price), 0), 2) AS avg_order_value
                    FROM order_items oi
                    JOIN orders o ON o.id = oi.order_id
                    WHERE {order_condition}
                    GROUP BY oi.product_id
                ) order_metrics ON order_metrics.product_id = p.id
                LEFT JOIN (
                    SELECT
                        r.product_id,
                        COUNT(DISTINCT r.id) AS total_returned,
                        COUNT(DISTINCT CASE
                            WHEN LOWER(COALESCE(r.reason, '')) REGEXP 'damag|defect|fault|quality|wrong item'
                            THEN r.id
                        END) AS quality_issue_returns,
                        ROUND(COALESCE(AVG(r.refund_amount), 0), 2) AS avg_refund_amount,
                        COALESCE(SUM(r.refund_amount), 0) AS total_refunded
                    FROM returns r
                    WHERE {return_condition}
                    GROUP BY r.product_id
                ) return_metrics ON return_metrics.product_id = p.id
                WHERE p.ready_made_supplier IS NOT NULL
                  AND p.ready_made_supplier != ''
                  AND p.ready_made_supplier != 'NULL'
                  AND p.is_ready_made = 1
                GROUP BY p.ready_made_supplier
                HAVING COALESCE(SUM(order_metrics.total_ordered), 0) > 0
                    OR COALESCE(SUM(return_metrics.total_returned), 0) > 0
                ORDER BY p.ready_made_supplier ASC
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            return [self._build_supplier_snapshot(row, self._score_supplier_metrics(row)) for row in rows]
        finally:
            conn.close()

    def _get_raw_material_supplier_overview(self, time_period):
        """Supplier overview for raw-material vendors using material ratings plus downstream outcomes."""
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            order_condition = self._get_sql_time_condition("o", time_period)
            return_condition = self._get_sql_time_condition("r", time_period)
            query = f"""
                SELECT
                    rm.supplier AS supplier_name,
                    'Raw Materials' AS supplier_type,
                    COUNT(DISTINCT rm.id) AS product_count,
                    COALESCE(SUM(usage_metrics.total_ordered), 0) AS total_ordered,
                    COALESCE(SUM(usage_metrics.total_units_sold), 0) AS total_units_sold,
                    COALESCE(SUM(usage_metrics.total_sales_value), 0) AS total_sales_value,
                    ROUND(AVG(NULLIF(usage_metrics.avg_order_value, 0)), 2) AS avg_order_value,
                    COALESCE(SUM(return_metrics.total_returned), 0) AS total_returned,
                    COALESCE(SUM(return_metrics.quality_issue_returns), 0) AS quality_issue_returns,
                    ROUND(AVG(NULLIF(return_metrics.avg_refund_amount, 0)), 2) AS avg_refund_amount,
                    COALESCE(SUM(return_metrics.total_refunded), 0) AS total_refunded,
                    ROUND(AVG(COALESCE(rm.supplier_rating, 0)), 2) AS avg_manual_rating
                FROM raw_materials rm
                LEFT JOIN (
                    SELECT
                        prm.raw_material_id,
                        COUNT(DISTINCT oi.id) AS total_ordered,
                        COALESCE(SUM(oi.quantity * prm.quantity_required), 0) AS total_units_sold,
                        COALESCE(SUM(oi.quantity * oi.price), 0) AS total_sales_value,
                        ROUND(COALESCE(AVG(oi.quantity * oi.price), 0), 2) AS avg_order_value
                    FROM product_raw_materials prm
                    JOIN products p ON p.id = prm.product_id
                    JOIN order_items oi ON oi.product_id = p.id
                    JOIN orders o ON o.id = oi.order_id
                    WHERE {order_condition}
                    GROUP BY prm.raw_material_id
                ) usage_metrics ON usage_metrics.raw_material_id = rm.id
                LEFT JOIN (
                    SELECT
                        prm.raw_material_id,
                        COUNT(DISTINCT r.id) AS total_returned,
                        COUNT(DISTINCT CASE
                            WHEN LOWER(COALESCE(r.reason, '')) REGEXP 'damag|defect|fault|quality|wrong item'
                            THEN r.id
                        END) AS quality_issue_returns,
                        ROUND(COALESCE(AVG(r.refund_amount), 0), 2) AS avg_refund_amount,
                        COALESCE(SUM(r.refund_amount), 0) AS total_refunded
                    FROM product_raw_materials prm
                    JOIN products p ON p.id = prm.product_id
                    JOIN returns r ON r.product_id = p.id
                    WHERE {return_condition}
                    GROUP BY prm.raw_material_id
                ) return_metrics ON return_metrics.raw_material_id = rm.id
                WHERE rm.supplier IS NOT NULL
                  AND rm.supplier != ''
                  AND rm.supplier != 'NULL'
                GROUP BY rm.supplier
                ORDER BY rm.supplier ASC
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            return [self._build_supplier_snapshot(row, self._score_raw_material_supplier_metrics(row)) for row in rows]
        finally:
            conn.close()

    def get_supplier_quality_overview(self, time_period="Last 30 Days", supplier_type="All Suppliers"):
        """
        Build supplier performance metrics and a live quality rating.
        """
        overview = []
        if supplier_type in ["All Suppliers", "Finished Products"]:
            overview.extend(self._get_finished_product_supplier_overview(time_period))
        if supplier_type in ["All Suppliers", "Raw Materials"]:
            overview.extend(self._get_raw_material_supplier_overview(time_period))

        overview.sort(
            key=lambda item: (
                -item['rating'],
                item['return_rate_percent'],
                item['supplier_name'].lower()
            )
        )
        return overview

    def get_raw_material_supplier_rating(self, supplier_name, time_period="All Time"):
        """Return the live supplier snapshot for a raw-material supplier."""
        supplier_name = (supplier_name or "").strip()
        if not supplier_name:
            return None

        for supplier in self._get_raw_material_supplier_overview(time_period):
            if supplier['supplier_name'].strip().lower() == supplier_name.lower():
                return supplier
        return None

    def get_supplier_quality_rating(self, supplier_id, time_period="Last 30 Days", supplier_type="All Suppliers"):
        """
        Return the live supplier quality snapshot for a supplier name.
        """
        supplier_name = (supplier_id or "").strip()
        if not supplier_name:
            return None

        for supplier in self.get_supplier_quality_overview(time_period, supplier_type):
            if supplier['supplier_name'].strip().lower() == supplier_name.lower():
                return supplier
        return None

    def get_predicted_product_surges(self, limit=6):
        """
        Predict near-term demand surges for products using recent sales velocity.
        """
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    p.id,
                    p.name,
                    p.stock,
                    COALESCE(p.reorder_level, 0) AS reorder_level,
                    COALESCE(SUM(CASE
                        WHEN o.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                        THEN oi.quantity ELSE 0 END), 0) AS units_last_7,
                    COALESCE(SUM(CASE
                        WHEN o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                        THEN oi.quantity ELSE 0 END), 0) AS units_last_30
                FROM products p
                LEFT JOIN order_items oi ON oi.product_id = p.id
                LEFT JOIN orders o ON o.id = oi.order_id
                GROUP BY p.id, p.name, p.stock, p.reorder_level
                HAVING units_last_30 > 0
                ORDER BY units_last_7 DESC, units_last_30 DESC
            """)
            rows = cursor.fetchall()

            surge_items = []
            for row in rows:
                weekly_units = float(row.get('units_last_7') or 0)
                monthly_units = float(row.get('units_last_30') or 0)
                baseline_weekly = monthly_units / 4 if monthly_units else 0
                growth_ratio = (weekly_units / baseline_weekly) if baseline_weekly else (2.0 if weekly_units > 0 else 0.0)
                predicted_next_7 = max(0, round((weekly_units * 0.7) + (baseline_weekly * 0.6)))
                stock = float(row.get('stock') or 0)
                reorder_level = float(row.get('reorder_level') or 0)
                stock_coverage_weeks = (stock / predicted_next_7) if predicted_next_7 else None

                if growth_ratio >= 1.15 or (predicted_next_7 > stock and predicted_next_7 > 0):
                    if predicted_next_7 > stock:
                        urgency = "Critical"
                    elif stock_coverage_weeks is not None and stock_coverage_weeks < 2:
                        urgency = "High"
                    else:
                        urgency = "Medium"

                    surge_items.append({
                        'product_id': row['id'],
                        'product_name': row['name'],
                        'stock': int(stock),
                        'reorder_level': int(reorder_level),
                        'units_last_7': int(round(weekly_units)),
                        'units_last_30': int(round(monthly_units)),
                        'growth_ratio': round(growth_ratio, 2),
                        'predicted_next_7': int(predicted_next_7),
                        'stock_coverage_weeks': round(stock_coverage_weeks, 1) if stock_coverage_weeks is not None else None,
                        'urgency': urgency
                    })

            urgency_rank = {"Critical": 0, "High": 1, "Medium": 2}
            surge_items.sort(
                key=lambda item: (
                    urgency_rank.get(item['urgency'], 9),
                    -item['growth_ratio'],
                    -item['predicted_next_7']
                )
            )
            return surge_items[:limit]
        finally:
            conn.close()
