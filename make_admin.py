#!/usr/bin/env python3
"""
Script to make a user an admin in the ZapRead application.

This script connects to the Supabase database and updates the user's admin status.
It also ensures the necessary database schema is in place.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '.'))

def ensure_users_table_schema():
    """Ensure the users table has the necessary columns."""
    try:
        from app import create_app
        from app.services.supabase_service import get_supabase
        
        app = create_app()
        with app.app_context():
            supabase = get_supabase()
            
            # Check if users table exists and has is_admin column
            print("Checking users table schema...")
            
            # Try to select from users table to see if it exists
            try:
                response = supabase.table('users').select('id, is_admin').limit(1).execute()
                print("✓ Users table exists with is_admin column")
            except Exception as e:
                print(f"Users table may need schema update: {str(e)}")
                print("Please ensure your users table has the following columns:")
                print("- id (UUID, primary key)")
                print("- email (text)")
                print("- is_admin (boolean, default false)")
                print("- subscription_status (text)")
                print("- subscription_id (text)")
                print("- created_at (timestamp)")
                print("- updated_at (timestamp)")
                
    except Exception as e:
        print(f"Error checking database schema: {str(e)}")

def make_user_admin(email):
    """
    Make a user an admin by their email address.
    
    Args:
        email (str): The email address of the user to make admin.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        from app import create_app
        from app.services.supabase_service import get_supabase
        
        app = create_app()
        with app.app_context():
            supabase = get_supabase()
            
            # First, find the user by email in auth.users
            print(f"Looking for user with email: {email}")
            auth_response = supabase.table('auth.users').select('id, email').eq('email', email).execute()
            
            if not auth_response.data:
                print(f"❌ User with email {email} not found in auth.users")
                return False
            
            user_id = auth_response.data[0]['id']
            print(f"✓ Found user with ID: {user_id}")
            
            # Check if user exists in users table
            users_response = supabase.table('users').select('id, is_admin').eq('id', user_id).execute()
            
            if users_response.data:
                # Update existing user record
                print("Updating existing user record...")
                update_response = supabase.table('users').update({
                    'is_admin': True
                }).eq('id', user_id).execute()
                
                if update_response.data:
                    print(f"✅ Successfully made {email} an admin!")
                    return True
                else:
                    print(f"❌ Failed to update user admin status")
                    return False
            else:
                # Create new user record in users table
                print("Creating new user record in users table...")
                insert_response = supabase.table('users').insert({
                    'id': user_id,
                    'email': email,
                    'is_admin': True,
                    'subscription_status': 'inactive'
                }).execute()
                
                if insert_response.data:
                    print(f"✅ Successfully created user record and made {email} an admin!")
                    return True
                else:
                    print(f"❌ Failed to create user record")
                    return False
                
    except Exception as e:
        print(f"❌ Error making user admin: {str(e)}")
        return False

def list_admin_users():
    """List all admin users."""
    try:
        from app import create_app
        from app.services.supabase_service import get_supabase
        
        app = create_app()
        with app.app_context():
            supabase = get_supabase()
            
            print("\n📋 Current admin users:")
            print("-" * 50)
            
            # Get all admin users
            response = supabase.table('users').select('id, email, is_admin').eq('is_admin', True).execute()
            
            if response.data:
                for user in response.data:
                    print(f"✓ {user.get('email', 'No email')} (ID: {user['id']})")
            else:
                print("No admin users found.")
                
    except Exception as e:
        print(f"Error listing admin users: {str(e)}")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email> [--list]")
        print("       python make_admin.py --list")
        print("\nExamples:")
        print("  python make_admin.py user@example.com")
        print("  python make_admin.py --list")
        sys.exit(1)
    
    # Check database schema first
    ensure_users_table_schema()
    
    if sys.argv[1] == '--list':
        list_admin_users()
    else:
        email = sys.argv[1]
        
        if '@' not in email:
            print("❌ Please provide a valid email address")
            sys.exit(1)
        
        success = make_user_admin(email)
        
        if success:
            print("\n📋 Updated admin users:")
            list_admin_users()
        else:
            print("\n❌ Failed to make user admin. Please check the error messages above.")
            sys.exit(1)

if __name__ == '__main__':
    main() 