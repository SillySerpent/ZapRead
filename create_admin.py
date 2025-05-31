import sys
import os
import uuid
from supabase_client import get_supabase
from config import get_config
from flask import Flask

def create_admin_user(email):
    """
    Create an admin user directly in the users table
    
    Args:
        email (str): The email address for the admin user
    """
    try:
        supabase = get_supabase()
        
        # Generate a UUID for the user
        user_id = str(uuid.uuid4())
        
        # Create the user record without is_admin field (since it doesn't exist yet)
        user_data = {
            'id': user_id,
            'email': email,
            'subscription_status': 'active'  # Give the admin full access
        }
        
        # Insert or update the user
        response = supabase.table('users').upsert(user_data).execute()
        
        if response.data and len(response.data) > 0:
            print(f"✅ User created successfully: {email}")
            print(f"   User ID: {user_id}")
            print("\nIMPORTANT: You still need to add the is_admin column and set it to TRUE for this user.")
            print("Run these SQL commands in the Supabase dashboard SQL Editor:")
            print("\n-- First add the is_admin column")
            print("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;")
            print("\n-- Then make this specific user an admin")
            print(f"UPDATE users SET is_admin = TRUE WHERE email = '{email}';")
            return True
        else:
            print(f"Failed to create user: {email}")
            return False
    
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_admin.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    
    # Create a Flask app and push an application context
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    with app.app_context():
        create_admin_user(email) 