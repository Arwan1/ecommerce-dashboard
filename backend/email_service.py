import smtplib
from email.mime.text import MIMEText
from config import EMAIL_CONFIG

class EmailService:
    """
    Handles sending automated emails.
    """
    def send_email(self, recipient, subject, body):
        """
        Sends an email
        """
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = recipient

        try:
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
                server.send_message(msg)
                print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def send_low_stock_alert(self, item):
        """
        Sends a low stock alert to the supplier
        """
        # Get supplier email from database based on item
        # recipient = self.db_ops.get_supplier_email(item['supplier_id'])
        # subject = f"Low Stock Alert: {item['name']}"
        # body = f"Dear Supplier,\n\nThe stock for {item['name']} is running low. Please restock."
        # self.send_email(recipient, subject, body)
        pass
