try:
    import mysql.connector
except ImportError:
    print("mysql-connector-python not installed. Installing now...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql-connector-python"])
    import mysql.connector

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'ecom_user',
    'password': 'dummypassword1234',
    'database': 'ecommerce_db'
}

#for sending automated emails
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'onyxecommercedashboard@gmail.com',
    'sender_password': 'larq wcbg hljz adci'
}

if __name__ == "__main__":
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("Connection successful!")
        conn.close()
    except Exception as e:
        print("Connection failed:", e)
