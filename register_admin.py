import sys
import os
from supabase_client import get_supabase
from config import get_config
from flask import Flask

def register_admin_user(email, password):
    """
    Register a new admin user through Supabase Auth
    
    Args:
        email (str): The email address for the admin user
        password (str): The password for the admin user
    """
    try:
        supabase = get_supabase()
        
        print(f"Attempting to register user: {email}")
        
        # Sign up the user through Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": "Admin User",
                    "app_metadata": {
                        "provider": "email"
                    }
                }
            }
        })
        
        if hasattr(auth_response, 'user') and auth_response.user:
            print(f"✅ User registered successfully with ID: {auth_response.user.id}")
            print(f"   Email: {auth_response.user.email}")
            
            print("\nIMPORTANT: You still need to add the is_admin column and set it to TRUE for this user.")
            print("Run these SQL commands in the Supabase dashboard SQL Editor:")
            print("\n-- First add the is_admin column if it doesn't exist")
            print("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;")
            print("\n-- Then make this specific user an admin")
            print(f"UPDATE users SET is_admin = TRUE WHERE email = '{email}';")
            
            return True
        else:
            print("❌ Failed to register user. No user data returned.")
            return False
    
    except Exception as e:
        print(f"Error registering user: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python register_admin.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    # Create a Flask app and push an application context
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    with app.app_context():
        register_admin_user(email, password) 