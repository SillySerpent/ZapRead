import sys
import os
from supabase_client import get_supabase
from config import get_config
from flask import Flask

def make_user_admin(email):
    """
    Make a user admin by their email address
    
    Args:
        email (str): The email address of the user to make admin
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        supabase = get_supabase()
        
        # First, get the user's ID from their email
        response = supabase.table('users').select('id').eq('email', email).execute()
        
        if not response.data or len(response.data) == 0:
            print(f"No user found with email: {email}")
            return False
        
        user_id = response.data[0]['id']
        
        # Update the user's admin status
        update_response = supabase.table('users').update({
            'is_admin': True
        }).eq('id', user_id).execute()
        
        if update_response.data and len(update_response.data) > 0:
            print(f"✅ User {email} is now an admin!")
            return True
        else:
            print(f"Failed to update admin status for user: {email}")
            return False
    
    except Exception as e:
        print(f"Error making user admin: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    
    # Create a Flask app and push an application context
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    with app.app_context():
        make_user_admin(email) 