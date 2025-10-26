# User Management Dashboard

## Overview
The User Management Dashboard provides administrators with a comprehensive Excel-like interface to manage all users who have access to the business management system. This feature is only available to users with admin privileges.

## Features

### 📊 Excel-like Spreadsheet View
- **Tabular Display**: Users are displayed in a clean, spreadsheet-style table with the following columns:
  - User ID
  - Username  
  - Email Address
  - Role (Admin/User)
  - Created Date

### 🎨 Visual Indicators
- **Role-based Color Coding**:
  - Admin users: Light red background
  - Regular users: Light green background

### 🛠️ User Management Operations

#### ➕ Add New User
- Create new user accounts with username, email, password, and role
- Input validation for email format and password strength
- Automatic password hashing for security

#### ✏️ Edit User Information
- Update username, email, and role for existing users
- Double-click on any user row for quick editing
- Optional password change during editing

#### 🔐 Change Password
- Dedicated password change functionality
- Secure password input with masking
- Minimum password length enforcement

#### 🗑️ Delete User
- Remove users from the system
- Protection against deleting the primary admin user
- Confirmation dialog to prevent accidental deletions

### 🔒 Security Features
- **Admin-Only Access**: User tab only appears for admin users
- **Password Protection**: All passwords are securely hashed
- **Primary Admin Protection**: Cannot delete the main admin account
- **Input Validation**: Email format and password strength validation

### 🔄 Real-time Updates
- **Asynchronous Loading**: User data loads in background threads
- **Refresh Functionality**: Manual refresh button to reload user data
- **Automatic Updates**: List refreshes after add/edit/delete operations

## Usage

### For Administrators:
1. **Access**: Log in with an admin account to see the "Users" tab
2. **View Users**: All system users are displayed in the spreadsheet view
3. **Add Users**: Click "Add User" to create new accounts for employees
4. **Edit Users**: Double-click any user or use "Edit User" button
5. **Manage Passwords**: Use "Change Password" for password resets
6. **Remove Users**: Select and delete users who no longer need access

### User Roles:
- **Admin**: Full system access including user management
- **User**: Standard access to orders, inventory, analytics, and returns

## Database Structure
The user management system uses the following database table structure:

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Considerations
- Passwords are hashed using secure algorithms
- Username and email uniqueness is enforced
- Admin privileges are required for all user management operations
- Primary admin account cannot be deleted to maintain system access

## Integration
The User Dashboard integrates seamlessly with:
- **Authentication System**: Created users can immediately log in
- **Role-based Access Control**: User roles determine tab visibility
- **Audit Trail**: User creation dates are tracked
- **Security Manager**: Password hashing and validation
