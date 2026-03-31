import tkinter as tk
from tkinter import messagebox
import random

import re
from config import DB_CONFIG
from backend.user_manager import UserManager
from backend.security_manager import SecurityManager

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("❌ mysql-connector-python not found. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql-connector-python"])
    import mysql.connector
    from mysql.connector import Error
import hashlib

class User:
    """Simple user class to hold user data"""
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.role = user_data.get('role')
        self.created_at = user_data.get('created_at')

class LoginWindow(tk.Frame):
    """
    Login window with an option to register.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.user_manager = UserManager()
        self.configure(bg="white")

        # Fullscreen setup
        self.pack(fill="both", expand=True)

        # Create login form
        self.create_login_form()

    def create_login_form(self):
        # Centering frame
        form_frame = tk.Frame(self, bg="white")
        form_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        tk.Label(form_frame, text="Login", font=("Arial", 24), bg="white").pack(pady=20)

        # Email input
        tk.Label(form_frame, text="Email:", font=("Arial", 14), bg="white").pack(pady=5)
        self.email_entry = tk.Entry(form_frame, font=("Arial", 14))
        self.email_entry.pack(pady=5)
        self.email_entry.bind('<Return>', lambda event: self.login())

        # Password input
        tk.Label(form_frame, text="Password:", font=("Arial", 14), bg="white").pack(pady=5)
        self.password_entry = tk.Entry(form_frame, font=("Arial", 14), show="*")
        self.password_entry.pack(pady=5)
        self.password_entry.bind('<Return>', lambda event: self.login())

        # Show password checkbox
        self.show_password_var = tk.BooleanVar()
        show_password_checkbox = tk.Checkbutton(
            form_frame, text="Show Password", variable=self.show_password_var, bg="white",
            command=self.toggle_password_visibility
        )
        show_password_checkbox.pack(pady=5)

        # Login button
        tk.Button(form_frame, text="Login", font=("Arial", 14), bg="#4CAF50", fg="white", command=self.login).pack(pady=10)

        # Register button
        tk.Button(form_frame, text="Register", font=("Arial", 14), bg="#2196F3", fg="white", command=self.show_register_form).pack(pady=10)

    def is_valid_email(self, email):
        # Check for format name@url.domain using regex
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password.")
            return

        if not self.is_valid_email(email):
            messagebox.showerror("Invalid Email", "Please enter a valid email address (e.g., user@example.com).")
            return

        try:
            # Connect to the database and validate credentials
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            # Hash the entered password
            hashed_password = SecurityManager().hash_password(password)

            # Query the database for matching credentials
            cursor.execute(
                "SELECT * FROM users WHERE email=%s AND password=%s", (email, hashed_password)
            )

            user_data = cursor.fetchone()
            cursor.close()
            conn.close()

            if user_data:
                user = User(user_data)
                print(f"Debug: Logged in user: {user.username}, Role: {user.role}")  # For debugging in the console
                # Clear the login window and move on to the main GUI
                self.parent.show_main_gui(user)
            else:
                messagebox.showerror("Login Failed", "Invalid email or password.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to login: {e}")

    def show_register_form(self):
        # Clear the current form
        for widget in self.winfo_children():
            widget.destroy()

        # Centering frame
        form_frame = tk.Frame(self, bg="white")
        form_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        tk.Label(form_frame, text="Register", font=("Arial", 24), bg="white").pack(pady=20)

        # Email input
        tk.Label(form_frame, text="Email:", font=("Arial", 14), bg="white").pack(pady=5)
        self.new_email_entry = tk.Entry(form_frame, font=("Arial", 14))
        self.new_email_entry.pack(pady=5)
        self.new_email_entry.bind('<Return>', lambda event: self.register())

        # Password input
        tk.Label(form_frame, text="Password:", font=("Arial", 14), bg="white").pack(pady=5)
        self.new_password_entry = tk.Entry(form_frame, font=("Arial", 14), show="*")
        self.new_password_entry.pack(pady=5)
        self.new_password_entry.bind('<Return>', lambda event: self.register())

        # Show password checkbox
        self.show_new_password_var = tk.BooleanVar()
        show_password_checkbox = tk.Checkbutton(
            form_frame, text="Show Password", variable=self.show_new_password_var, bg="white",
            command=self.toggle_new_password_visibility
        )
        show_password_checkbox.pack(pady=5)

        # Register button
        tk.Button(form_frame, text="Submit Registration", font=("Arial", 14), bg="#FF5722", fg="white", command=self.register).pack(pady=10)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def toggle_new_password_visibility(self):
        if self.show_new_password_var.get():
            self.new_password_entry.config(show="")
        else:
            self.new_password_entry.config(show="*")

    def register(self):
        new_email = self.new_email_entry.get()
        new_password = self.new_password_entry.get()

        if not self.is_valid_email(new_email):
            messagebox.showerror("Invalid Email", "Please enter a valid email address (e.g., user@example.com).")
            return

        # Generate a random confirmation code
        confirmation_code = random.randint(100000, 999999)

        # Send the confirmation code via email
        send_email(
            to_email=new_email,
            subject="Your Confirmation Code",
            message=f"Your confirmation code is: {confirmation_code}"
        )

        # Save the user to the database with admin rights
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Hash the new password
            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

            cursor.execute(
                "INSERT INTO users (email, password, admin, confirmation_code) VALUES (%s, %s, %s, %s)",
                (new_email, hashed_password, True, confirmation_code)
            )
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Register", f"Registered {new_email}. A confirmation code has been sent to your email.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to register: {e}")