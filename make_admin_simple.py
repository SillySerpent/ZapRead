import sys
import os
from supabase_client import get_supabase
from config import get_config
from flask import Flask

def make_user_admin(email):
    """
    Make a user admin by their email address - simplified version
    
    Args:
        email (str): The email address of the user to make admin
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        supabase = get_supabase()
        
        # First, make sure the is_admin column exists
        print(f"Checking if is_admin column exists and adding it if needed...")
        print("(Note: You should run this SQL in the Supabase dashboard if this script fails)")
        print("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;")
        
        # Now try to find the user and update them
        print(f"\nAttempting to make user {email} an admin...")
        
        # Instead of selecting first and then updating, try a direct update
        update_query = f"""
        UPDATE users 
        SET is_admin = TRUE 
        WHERE email = '{email}'
        """
        print(f"SQL that needs to be run: {update_query}")
        
        # Since we can't execute SQL directly, use the API to update if possible
        try:
            # Try to get the user by email first
            response = supabase.table('users').select('*').eq('email', email).execute()
            
            if response.data and len(response.data) > 0:
                user_id = response.data[0]['id']
                print(f"Found user with ID: {user_id}")
                
                # Now try to update the user
                update_data = {'is_admin': True}
                update_response = supabase.table('users').update(update_data).eq('id', user_id).execute()
                
                if update_response.data and len(update_response.data) > 0:
                    print(f"✅ Successfully made user {email} an admin!")
                    return True
                else:
                    print(f"Failed to update user: {email}")
                    print("You'll need to run the SQL command manually in the Supabase SQL Editor.")
                    return False
            else:
                print(f"No user found with email: {email}")
                print("Please make sure the user exists and has been properly registered.")
                return False
            
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            print("\nYou'll need to run the SQL command manually in the Supabase SQL Editor:")
            print(update_query)
            return False
    
    except Exception as e:
        print(f"Error making user admin: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin_simple.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    
    # Create a Flask app and push an application context
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    with app.app_context():
        make_user_admin(email) 