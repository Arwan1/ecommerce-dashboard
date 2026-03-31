from database.db_operations import DBOperations
from database.db_connector import get_db_connection
import mysql.connector
from datetime import datetime, timedelta
from statistics import mean

class AnalyticsManager:
    """
    Manages analytics data retrieval from the database.
    """
    def __init__(self):
        """
        Initializes the AnalyticsManager with a DBOperations instance.
        """
        self.db_ops = DBOperations()

    def get_total_orders(self):
        """
        Retrieves the total number of orders from database
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(id) FROM orders")
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting total orders: {e}")
            return 0
        finally:
            conn.close()

    def get_total_revenue(self):
        """
        Retrieves the total revenue from all orders.
        Assumes 'orders' table has a 'total_price' column.
        """
        conn = get_db_connection()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total_price) FROM orders")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0.0
        except mysql.connector.Error as e:
            print(f"Error getting total revenue: {e}")
            return 0.0
        finally:
            conn.close()

    def get_new_customers(self, days=30):
        """
        Retrieves the number of new customers in the last 'days' days.
        Assumes 'users' table has a 'created_at' column (DATETIME or similar).
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            # This query is for MySQL. Using DATE_SUB instead of SQLite's date function
            cursor.execute("SELECT COUNT(id) FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)", (days,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting new customers: {e}")
            # Fallback if the query fails (e.g., table/column doesn't exist)
            return 0
        finally:
            conn.close()

    def get_pending_orders(self):
        """
        Retrieves the number of recent orders (last 3 days) as "pending".
        Since there's no status column, we'll treat recent orders as potentially pending.
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(id) FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 3 DAY)")
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting pending orders: {e}")
            return 0
        finally:
            conn.close()

    def get_orders_this_week(self):
        """
        Retrieves the number of orders placed in the current week.
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(id) FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting orders this week: {e}")
            return 0
        finally:
            conn.close()

    def get_revenue_this_month(self):
        """
        Retrieves the total revenue for the current month.
        """
        conn = get_db_connection()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total_price) FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0.0
        except mysql.connector.Error as e:
            print(f"Error getting revenue this month: {e}")
            return 0.0
        finally:
            conn.close()

    def get_pending_returns(self):
        """
        Retrieves the number of pending returns from the canonical returns table.
        """
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(id) FROM returns WHERE status = 'Pending'")
            except mysql.connector.Error:
                cursor.execute("SELECT COUNT(id) FROM return_claims")
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as e:
            print(f"Error getting pending returns: {e}")
            return 0
        finally:
            conn.close()

    def get_supplier_returns_data(self, time_period="Last 30 Days"):
        """
        Retrieves comprehensive supplier returns data for dashboard analytics.
        Returns data for chart visualization and table display.
        """
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Convert time period to SQL date filter
            date_filter = self._get_date_filter_for_period(time_period)
            
            # Query for supplier returns data with comprehensive metrics
            query = f"""
                SELECT 
                    p.ready_made_supplier as supplier_name,
                    COUNT(DISTINCT r.id) as total_returns,
                    COUNT(DISTINCT oi.id) as total_items_sold,
                    ROUND(
                        (COUNT(DISTINCT r.id) * 100.0 / NULLIF(COUNT(DISTINCT oi.id), 0)), 
                        2
                    ) as return_rate_percent,
                    ROUND(AVG(r.refund_amount), 2) as avg_refund_amount,
                    SUM(r.refund_amount) as total_refund_amount,
                    COUNT(CASE WHEN r.status = 'Pending' THEN 1 END) as pending_returns,
                    COUNT(CASE WHEN r.status = 'Approved' THEN 1 END) as approved_returns,
                    COUNT(CASE WHEN r.status = 'Rejected' THEN 1 END) as rejected_returns
                FROM products p
                LEFT JOIN returns r ON r.product_id = p.id {date_filter.replace('WHERE', 'AND') if date_filter else ''}
                LEFT JOIN order_items oi ON oi.product_id = p.id
                WHERE p.ready_made_supplier IS NOT NULL 
                  AND p.ready_made_supplier != ''
                  AND p.ready_made_supplier != 'NULL'
                GROUP BY p.ready_made_supplier
                HAVING COUNT(DISTINCT oi.id) > 0
                ORDER BY return_rate_percent DESC, total_returns DESC
                LIMIT 20
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convert results to list of dictionaries for easier use
            supplier_data = []
            for row in results:
                supplier_data.append({
                    'supplier_name': row[0],
                    'total_returns': row[1],
                    'total_items_sold': row[2],
                    'return_rate_percent': row[3] or 0.0,
                    'avg_refund_amount': row[4] or 0.0,
                    'total_refund_amount': row[5] or 0.0,
                    'pending_returns': row[6] or 0,
                    'approved_returns': row[7] or 0,
                    'rejected_returns': row[8] or 0
                })
            
            return supplier_data
            
        except mysql.connector.Error as e:
            print(f"Error getting supplier returns data: {e}")
            return []
        finally:
            conn.close()

    def _get_date_filter_for_period(self, time_period):
        """
        Convert time period string to SQL WHERE clause for date filtering.
        """
        date_filters = {
            "Last 7 Days": "WHERE r.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
            "Last 30 Days": "WHERE r.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
            "Last 90 Days": "WHERE r.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)",
            "Last Year": "WHERE r.created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR)",
            "All Time": ""
        }
        return date_filters.get(time_period, date_filters["Last 30 Days"])

    def build_sales_prediction(self, chart_data, time_period="Last 30 Days"):
        """
        Build a lightweight sales forecast from recent order history.
        """
        sales_history = chart_data.get('monthly_sales', []) if chart_data else []
        top_products = chart_data.get('top_products', []) if chart_data else []

        if not sales_history:
            return {
                'forecast_period_label': self._get_forecast_period_label(time_period),
                'forecast_horizon': self._get_forecast_horizon(time_period),
                'predicted_revenue': 0.0,
                'predicted_orders': 0,
                'confidence_score': 0,
                'confidence_label': 'Low confidence',
                'trend_direction': 'Insufficient data',
                'summary': "Not enough sales history is available yet to generate a reliable prediction.",
                'recommendations': [
                    "Capture a longer sales history before using the forecast for planning.",
                    "Refresh analytics after additional orders are recorded to improve confidence."
                ],
                'forecast_series': []
            }

        revenue_series = [float(item.get('revenue') or 0) for item in sales_history]
        order_series = [int(item.get('orders') or 0) for item in sales_history]
        horizon = self._get_forecast_horizon(time_period)

        forecast_revenues = self._forecast_series(revenue_series, horizon)
        forecast_orders = self._forecast_series(order_series, horizon)
        forecast_periods = self._build_future_periods(
            [item.get('period') for item in sales_history],
            time_period,
            horizon
        )

        forecast_series = []
        for period, revenue, orders in zip(forecast_periods, forecast_revenues, forecast_orders):
            forecast_series.append({
                'period': period,
                'revenue': round(revenue, 2),
                'orders': max(0, int(round(orders)))
            })

        total_predicted_revenue = sum(item['revenue'] for item in forecast_series)
        total_predicted_orders = sum(item['orders'] for item in forecast_series)
        confidence_score = self._calculate_confidence(revenue_series, horizon)
        confidence_label = self._describe_confidence(confidence_score)
        trend_direction = self._describe_trend(revenue_series, forecast_series)
        recommendations = self._build_prediction_recommendations(
            trend_direction,
            confidence_score,
            top_products,
            self._get_forecast_period_label(time_period)
        )

        return {
            'forecast_period_label': self._get_forecast_period_label(time_period),
            'forecast_horizon': horizon,
            'predicted_revenue': round(total_predicted_revenue, 2),
            'predicted_orders': total_predicted_orders,
            'confidence_score': confidence_score,
            'confidence_label': confidence_label,
            'trend_direction': trend_direction,
            'summary': (
                f"Projected {trend_direction.lower()} sales for the next "
                f"{self._get_forecast_period_label(time_period).lower()} with {confidence_label.lower()}."
            ),
            'recommendations': recommendations,
            'forecast_series': forecast_series
        }

    def _forecast_series(self, values, horizon):
        clean_values = [max(0, float(value or 0)) for value in values]
        if not clean_values:
            return [0.0] * horizon

        recent_values = clean_values[-3:]
        if len(recent_values) == 1:
            base_value = recent_values[0]
        elif len(recent_values) == 2:
            base_value = (recent_values[-1] * 0.65) + (recent_values[-2] * 0.35)
        else:
            base_value = (
                recent_values[-1] * 0.5 +
                recent_values[-2] * 0.3 +
                recent_values[-3] * 0.2
            )

        if len(clean_values) > 1:
            differences = [
                clean_values[index] - clean_values[index - 1]
                for index in range(1, len(clean_values))
            ]
            recent_differences = differences[-3:]
            trend = mean(recent_differences) if recent_differences else 0.0
        else:
            trend = 0.0

        forecast = []
        next_value = base_value
        for step in range(horizon):
            dampening = max(0.35, 1 - (step * 0.12))
            next_value = max(0.0, next_value + (trend * dampening))
            forecast.append(next_value)
        return forecast

    def _calculate_confidence(self, values, horizon):
        clean_values = [float(value or 0) for value in values if value is not None]
        if len(clean_values) < 2:
            return 35

        avg_value = mean(clean_values) or 1
        avg_change = mean(abs(clean_values[index] - clean_values[index - 1]) for index in range(1, len(clean_values)))
        volatility_ratio = min(avg_change / avg_value, 1.5)
        data_bonus = min(len(clean_values) * 4, 20)
        horizon_penalty = max(0, (horizon - 3) * 4)
        score = 78 + data_bonus - int(volatility_ratio * 28) - horizon_penalty
        return max(35, min(92, score))

    def _describe_confidence(self, score):
        if score >= 80:
            return "High confidence"
        if score >= 60:
            return "Moderate confidence"
        return "Low confidence"

    def _describe_trend(self, history, forecast_series):
        recent_avg = mean(history[-3:]) if history else 0
        predicted_avg = mean(item['revenue'] for item in forecast_series) if forecast_series else 0

        if recent_avg <= 0 and predicted_avg <= 0:
            return "Stable"

        change_ratio = ((predicted_avg - recent_avg) / recent_avg) if recent_avg else 0
        if change_ratio > 0.08:
            return "Growth"
        if change_ratio < -0.08:
            return "Softening"
        return "Stable"

    def _build_prediction_recommendations(self, trend_direction, confidence_score, top_products, forecast_label):
        lead_product = top_products[0]['name'] if top_products else None
        recommendations = []

        if trend_direction == "Growth":
            recommendations.append(
                f"Prepare inventory and fulfillment capacity for an uptick over the next {forecast_label.lower()}."
            )
        elif trend_direction == "Softening":
            recommendations.append("Plan a promotion or retention campaign to counter the predicted slowdown.")
        else:
            recommendations.append("Keep purchasing and staffing close to current run-rate while monitoring new demand signals.")

        if lead_product:
            recommendations.append(f"Prioritize stock availability and merchandising for {lead_product}, which is currently leading sales.")

        if confidence_score < 60:
            recommendations.append("Treat this forecast as directional only and validate it against new orders during the next refresh cycle.")
        else:
            recommendations.append("Use the forecast to guide short-term purchasing, campaign timing, and stakeholder updates.")

        return recommendations[:3]

    def _get_forecast_horizon(self, time_period):
        return {
            "Last 7 Days": 3,
            "Last 30 Days": 7,
            "Last 90 Days": 3,
            "Last Year": 3,
            "All Time": 3
        }.get(time_period, 3)

    def _get_forecast_period_label(self, time_period):
        return {
            "Last 7 Days": "3 days",
            "Last 30 Days": "7 days",
            "Last 90 Days": "3 months",
            "Last Year": "3 months",
            "All Time": "3 months"
        }.get(time_period, "3 periods")

    def _build_future_periods(self, periods, time_period, horizon):
        if not periods:
            return [f"Forecast {index + 1}" for index in range(horizon)]

        last_period = periods[-1]
        if isinstance(last_period, datetime):
            last_dt = last_period
        else:
            try:
                last_dt = datetime.strptime(str(last_period), "%Y-%m-%d")
            except ValueError:
                try:
                    last_dt = datetime.strptime(str(last_period), "%Y-%m")
                except ValueError:
                    last_dt = None

        future_periods = []
        if time_period in ["Last 7 Days", "Last 30 Days"] and last_dt:
            for offset in range(1, horizon + 1):
                future_periods.append((last_dt + timedelta(days=offset)).strftime("%Y-%m-%d"))
            return future_periods

        if last_dt:
            year = last_dt.year
            month = last_dt.month
            for _ in range(horizon):
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                future_periods.append(f"{year}-{month:02d}")
            return future_periods

        return [f"Forecast {index + 1}" for index in range(horizon)]
