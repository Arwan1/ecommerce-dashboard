import smtplib
from config import EMAIL_CONFIG

def send_email(to_email, subject, message):
    """
    Sends an email using the SMTP server configured in EMAIL_CONFIG.
    """
    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()  # Start TLS encryption
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])

        # Create the email
        email_message = f"Subject: {subject}\n\n{message}"

        # Send the email
        server.sendmail(EMAIL_CONFIG["sender_email"], to_email, email_message)
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")