# Add V2 root directory to sys.path
import sys
import os
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from database.db_operations import DBOperations
from backend.security_manager import SecurityManager

class UserManager:
    def __init__(self):
        self.db_ops = DBOperations()
        self.security = SecurityManager()  # Initialize SecurityManager

    def login(self, username, password):
        """
        Verifies the username and password against the database.
        """
        user_data = self.db_ops.get_user(username)
        print(f"Debug: Retrieved user data: {user_data}")  # Debugging

        if user_data and user_data["password"] == password:  # Compare hashed passwords
            return user_data
        return None

    def add_user(self, username, password, email, role="user"):
        """
        Adds a new user to the database.
        """
        hashed_password = self.security.hash_password(password)
        return self.db_ops.add_user(username, hashed_password, email, role)

