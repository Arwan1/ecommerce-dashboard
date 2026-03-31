import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from backend.user_manager import UserManager
from datetime import datetime

class UserDashboard(tk.Frame):
    """
    GUI for managing users with Excel-like spreadsheet functionality.
    """
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.user_manager = UserManager()
        self.user_rows = []
        self.create_widgets()
        self.load_users_async()

    def create_widgets(self):
        """
        Creates widgets for the user dashboard.
        """
        # Create main container
        self.users_frame = ttk.Frame(self)
        self.users_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_users_tab()

    def create_users_tab(self):
        """
        Create the users list tab with Excel-like functionality.
        """
        # Title
        self.title_label = tk.Label(self.users_frame, text="User Management Dashboard", 
                                   font=("Arial", 20, "bold"))
        self.title_label.pack(pady=10)

        search_frame = ttk.Frame(self.users_frame)
        search_frame.pack(fill="x", padx=10, pady=(0, 5))

        ttk.Label(search_frame, text="Search Users:").pack(side="left")
        self.user_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.user_search_var, width=40)
        search_entry.pack(side="left", padx=(8, 8))
        search_entry.bind("<KeyRelease>", lambda event: self.apply_user_filter())

        ttk.Button(search_frame, text="Clear", command=self.clear_user_search).pack(side="left")

        # Treeview to display users in spreadsheet format
        self.tree = ttk.Treeview(self.users_frame, 
                                columns=("ID", "Username", "Email", "Role", "Created Date"), 
                                show="headings")
        
        # Configure headings
        self.tree.heading("ID", text="User ID")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Email", text="Email Address")
        self.tree.heading("Role", text="Role")
        self.tree.heading("Created Date", text="Created Date")
        
        # Configure column widths
        self.tree.column("ID", width=80)
        self.tree.column("Username", width=150)
        self.tree.column("Email", width=250)
        self.tree.column("Role", width=100)
        self.tree.column("Created Date", width=150)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure role-based row colors
        self.tree.tag_configure('admin', background='#ffcdd2')  # Light red for admins
        self.tree.tag_configure('user', background='#e8f5e8')   # Light green for users

        # Add scrollbar for the treeview
        scrollbar = ttk.Scrollbar(self.users_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Button frame
        self.button_frame = tk.Frame(self.users_frame)
        self.button_frame.pack(pady=10)

        # Add, Edit, Delete buttons
        self.add_button = tk.Button(self.button_frame, text="Add User", 
                                   command=self.add_user, bg="#2196F3", fg="white")
        self.add_button.pack(side="left", padx=10)

        self.refresh_button = tk.Button(self.button_frame, text="Refresh", 
                                       command=self.load_users_async, bg="#2196F3", fg="white")
        self.refresh_button.pack(side="left", padx=10)

        self.edit_button = tk.Button(self.button_frame, text="Edit User", 
                                    command=self.edit_user, bg="#2196F3", fg="white")
        self.edit_button.pack(side="left", padx=10)

        self.change_password_button = tk.Button(self.button_frame, text="Change Password", 
                                               command=self.change_password, bg="#F44336", fg="white")
        self.change_password_button.pack(side="left", padx=10)

        self.delete_button = tk.Button(self.button_frame, text="Delete User", 
                                      command=self.delete_user, bg="#F44336", fg="white")
        self.delete_button.pack(side="left", padx=10)

        # Bind double-click to edit
        self.tree.bind("<Double-1>", lambda event: self.edit_user())

    def show_loading_users(self):
        """
        Show loading indicator for users.
        """
        # Clear existing items and show loading
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.tree.insert("", "end", values=("", "Loading users...", "", "", ""))

    def load_users_async(self):
        """
        Load users in background thread.
        """
        self.show_loading_users()
        
        def load_in_background():
            try:
                users = self.user_manager.get_all_users()
                # Update UI in main thread
                self.after(0, lambda: self.populate_users(users))
            except Exception as e:
                self.after(0, lambda: self.show_error_loading_users(str(e)))
        
        thread = threading.Thread(target=load_in_background)
        thread.daemon = True
        thread.start()

    def populate_users(self, users):
        """
        Populate the treeview with user data.
        """
        self.user_rows = []

        if not users:
            self.render_user_rows([])
            return

        for user in users:
            # Format created date
            created_date = user.get('created_at', '')
            if created_date:
                if isinstance(created_date, str):
                    created_date = created_date.split(' ')[0]  # Get date part only
                else:
                    created_date = created_date.strftime('%Y-%m-%d')

            # Determine tag for row coloring
            tag = user.get('role', 'user')

            values = (
                user.get('id', ''),
                user.get('username', ''),
                user.get('email', ''),
                user.get('role', '').title(),
                created_date
            )
            search_text = " ".join(str(value).lower() for value in values)

            self.user_rows.append({
                "values": values,
                "tags": (tag,),
                "search_text": search_text,
            })

        self.apply_user_filter()

    def show_error_loading_users(self, error_message):
        """
        Show error when loading users fails.
        """
        self.user_rows = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.tree.insert("", "end", values=("", f"Error loading users: {error_message}", "", "", ""))

    def render_user_rows(self, rows):
        """Render user rows into the treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not rows:
            empty_message = "No matching users found" if self.user_search_var.get().strip() else "No users found"
            self.tree.insert("", "end", values=("", empty_message, "", "", ""))
            return

        for row in rows:
            self.tree.insert("", "end", values=row["values"], tags=row["tags"])

    def apply_user_filter(self):
        """Filter users using the current search term."""
        search_term = self.user_search_var.get().strip().lower()
        if not search_term:
            self.render_user_rows(self.user_rows)
            return

        filtered_rows = [
            row for row in self.user_rows
            if search_term in row["search_text"]
        ]
        self.render_user_rows(filtered_rows)

    def clear_user_search(self):
        """Reset the user search field."""
        self.user_search_var.set("")
        self.apply_user_filter()

    def add_user(self):
        """
        Open dialog to add a new user.
        """
        dialog = UserDialog(self, "Add New User")
        if dialog.result:
            self.load_users_async()

    def edit_user(self):
        """
        Edit selected user.
        """
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a user to edit.")
            return

        user_data = self.tree.item(selected[0])['values']
        if len(user_data) < 5 or not user_data[0]:
            messagebox.showerror("Error", "Invalid user selected.")
            return

        user_id = user_data[0]
        dialog = UserDialog(self, "Edit User", user_id=user_id, 
                           username=user_data[1], email=user_data[2], 
                           role=user_data[3].lower())
        if dialog.result:
            self.load_users_async()

    def change_password(self):
        """
        Change password for selected user.
        """
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a user to change password.")
            return

        user_data = self.tree.item(selected[0])['values']
        if len(user_data) < 5 or not user_data[0]:
            messagebox.showerror("Error", "Invalid user selected.")
            return

        user_id = user_data[0]
        username = user_data[1]

        # Confirm action
        if not messagebox.askyesno("Confirm", f"Change password for user '{username}'?"):
            return

        # Get new password
        new_password = simpledialog.askstring("New Password", 
                                             f"Enter new password for {username}:", 
                                             show='*')
        if not new_password:
            return

        if len(new_password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long.")
            return

        # Update password
        if self.user_manager.update_user(user_id, password=new_password):
            messagebox.showinfo("Success", f"Password updated successfully for user '{username}'.")
        else:
            messagebox.showerror("Error", "Failed to update password.")

    def delete_user(self):
        """
        Delete selected user.
        """
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a user to delete.")
            return

        user_data = self.tree.item(selected[0])['values']
        if len(user_data) < 5 or not user_data[0]:
            messagebox.showerror("Error", "Invalid user selected.")
            return

        user_id = user_data[0]
        username = user_data[1]

        # Prevent deleting admin user
        if user_id == 1:
            messagebox.showerror("Error", "Cannot delete the primary admin user.")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion", 
                                  f"Are you sure you want to delete user '{username}'?\n\n"
                                  "This action cannot be undone."):
            return

        # Delete user
        if self.user_manager.delete_user(user_id):
            messagebox.showinfo("Success", f"User '{username}' deleted successfully.")
            self.load_users_async()
        else:
            messagebox.showerror("Error", "Failed to delete user.")


class UserDialog(tk.Toplevel):
    """
    Dialog for adding/editing users.
    """
    def __init__(self, parent, title, user_id=None, username="", email="", role="user"):
        super().__init__(parent)
        self.parent = parent
        self.user_manager = UserManager()
        self.user_id = user_id
        self.result = False
        
        self.title(title)
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets(username, email, role)
        
        # Focus on username field
        self.username_entry.focus()

    def create_widgets(self, username, email, role):
        """
        Create dialog widgets.
        """
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Username
        ttk.Label(main_frame, text="Username:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(main_frame, width=30)
        self.username_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        self.username_entry.insert(0, username)

        # Email
        ttk.Label(main_frame, text="Email:").grid(row=1, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(main_frame, width=30)
        self.email_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        self.email_entry.insert(0, email)

        # Password (only for new users or if changing)
        ttk.Label(main_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(main_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        if self.user_id:
            # Edit mode - password is optional
            password_note = ttk.Label(main_frame, text="(Leave blank to keep current password)", 
                                     font=("Arial", 8))
            password_note.grid(row=3, column=1, sticky="w", padx=(10, 0))

        # Role
        ttk.Label(main_frame, text="Role:").grid(row=4, column=0, sticky="w", pady=5)
        self.role_var = tk.StringVar(value=role)
        role_frame = ttk.Frame(main_frame)
        role_frame.grid(row=4, column=1, sticky="w", pady=5, padx=(10, 0))
        
        ttk.Radiobutton(role_frame, text="User", variable=self.role_var, 
                       value="user").pack(side="left")
        ttk.Radiobutton(role_frame, text="Admin", variable=self.role_var, 
                       value="admin").pack(side="left", padx=(20, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.save_user).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

        # Bind Enter key to save
        self.bind('<Return>', lambda event: self.save_user())
        self.bind('<Escape>', lambda event: self.destroy())

    def save_user(self):
        """
        Save user data.
        """
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        role = self.role_var.get()

        # Validate inputs
        if not username:
            messagebox.showerror("Error", "Username is required.")
            return
        
        if not email:
            messagebox.showerror("Error", "Email is required.")
            return
        
        if "@" not in email:
            messagebox.showerror("Error", "Please enter a valid email address.")
            return

        # Password validation
        if not self.user_id and not password:  # New user
            messagebox.showerror("Error", "Password is required for new users.")
            return
        
        if password and len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long.")
            return

        try:
            if self.user_id:
                # Update existing user
                success = self.user_manager.update_user(
                    self.user_id, 
                    username=username, 
                    email=email, 
                    password=password if password else None, 
                    role=role
                )
                action = "updated"
            else:
                # Add new user
                success = self.user_manager.add_user(username, password, email, role)
                action = "added"

            if success:
                messagebox.showinfo("Success", f"User {action} successfully.")
                self.result = True
                self.destroy()
            else:
                messagebox.showerror("Error", f"Failed to {action.replace('ed', '')} user. "
                                             "Username or email might already exist.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
