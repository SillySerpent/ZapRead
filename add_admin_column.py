import sys
import os
import uuid
from supabase_client import get_supabase
from config import get_config
from flask import Flask

def add_admin_column():
    """
    Add the is_admin column to the users table
    """
    print("To add the is_admin column to the users table, you need to run the following SQL in the Supabase dashboard SQL Editor:")
    print("\nALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;")
    print("\nSince we can't execute this SQL directly through the Python API, please follow these steps:")
    print("1. Log in to your Supabase dashboard")
    print("2. Go to the SQL Editor")
    print("3. Create a new query")
    print("4. Paste the SQL above")
    print("5. Run the query")
    print("\nAfter adding the column, you can make a user admin with this script:")
    print("python make_admin.py <email>")
    
    # Try to verify if we can access the users table
    try:
        supabase = get_supabase()
        response = supabase.table('users').select('id, email').execute()
        
        print("\nCurrent users in the database:")
        
        if response.data and len(response.data) > 0:
            for idx, user in enumerate(response.data, 1):
                print(f"{idx}. ID: {user.get('id')} - Email: {user.get('email')}")
        else:
            print("No users found in the database")
    
    except Exception as e:
        print(f"\nError checking users table: {str(e)}")

if __name__ == "__main__":
    # Create a Flask app and push an application context
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    with app.app_context():
        add_admin_column() 