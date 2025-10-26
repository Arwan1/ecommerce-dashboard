#!/usr/bin/env python3
"""
Test script for the User Dashboard functionality
"""

from backend.user_manager import UserManager
from database.db_operations import DBOperations

def test_user_operations():
    """Test user management operations"""
    print("🧪 Testing User Management Operations")
    print("=" * 50)
    
    user_manager = UserManager()
    
    # Test 1: Get all users
    print("📋 Test 1: Getting all users...")
    try:
        users = user_manager.get_all_users()
        print(f"✅ Found {len(users)} users in database")
        for user in users[:3]:  # Show first 3 users
            print(f"   - {user['username']} ({user['email']}) - {user['role']}")
        if len(users) > 3:
            print(f"   ... and {len(users) - 3} more users")
    except Exception as e:
        print(f"❌ Error getting users: {e}")
    
    # Test 2: Add a test user
    print("\n👤 Test 2: Adding a test user...")
    try:
        success = user_manager.add_user("test_user", "password123", "test@example.com", "user")
        if success:
            print("✅ Test user added successfully")
        else:
            print("❌ Failed to add test user (may already exist)")
    except Exception as e:
        print(f"❌ Error adding test user: {e}")
    
    # Test 3: Update a user (if test user exists)
    print("\n✏️ Test 3: Testing user update...")
    try:
        updated_users = user_manager.get_all_users()
        test_user = None
        for user in updated_users:
            if user['username'] == 'test_user':
                test_user = user
                break
        
        if test_user:
            success = user_manager.update_user(test_user['id'], email="updated_test@example.com")
            if success:
                print("✅ Test user updated successfully")
            else:
                print("❌ Failed to update test user")
        else:
            print("ℹ️ Test user not found, skipping update test")
    except Exception as e:
        print(f"❌ Error updating test user: {e}")
    
    # Test 4: Clean up - delete test user
    print("\n🗑️ Test 4: Cleaning up test user...")
    try:
        updated_users = user_manager.get_all_users()
        test_user = None
        for user in updated_users:
            if user['username'] == 'test_user':
                test_user = user
                break
        
        if test_user:
            success = user_manager.delete_user(test_user['id'])
            if success:
                print("✅ Test user deleted successfully")
            else:
                print("❌ Failed to delete test user")
        else:
            print("ℹ️ Test user not found, no cleanup needed")
    except Exception as e:
        print(f"❌ Error deleting test user: {e}")
    
    print("\n🎯 User management tests completed!")

if __name__ == "__main__":
    test_user_operations()
