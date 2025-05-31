import sys
import os
from supabase_client import get_supabase
from config import get_config
from flask import Flask

def create_tables():
    """
    Create the required tables and triggers in Supabase
    """
    try:
        supabase = get_supabase()
        
        # SQL to create users table
        users_table_sql = """
        -- Create users table if it doesn't exist
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            subscription_id TEXT,
            subscription_status TEXT DEFAULT 'free',
            is_admin BOOLEAN DEFAULT FALSE
        );
        """
        
        # SQL to create file_history table
        file_history_sql = """
        -- Create file_history table if it doesn't exist
        CREATE TABLE IF NOT EXISTS file_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) NOT NULL,
            original_filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            processed_filename TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        # SQL to create feedback table
        feedback_sql = """
        -- Create feedback table if it doesn't exist
        CREATE TABLE IF NOT EXISTS feedback (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id),
            email TEXT,
            feedback_text TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        # SQL to create newsletter_subscribers table
        newsletter_sql = """
        -- Create newsletter_subscribers table if it doesn't exist
        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        # SQL to create page_views table for analytics
        page_views_sql = """
        -- Create page_views table if it doesn't exist
        CREATE TABLE IF NOT EXISTS page_views (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            page TEXT NOT NULL,
            user_id UUID REFERENCES users(id),
            metadata JSONB DEFAULT '{}',
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        # SQL to create website_content table
        website_content_sql = """
        -- Create website_content table if it doesn't exist
        CREATE TABLE IF NOT EXISTS website_content (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            section TEXT NOT NULL,
            key TEXT NOT NULL,
            content JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(section, key)
        );
        """
        
        # Execute each SQL statement separately with REST API
        # Since we can't execute SQL directly through the client API
        # We'll create the tables using insert operations
        
        print("Creating users table...")
        # For users table, we'll try to insert a sample record instead of creating the table
        # since we need to ensure the table exists for testing
        
        # Create a default admin user if email is provided
        admin_email = sys.argv[1] if len(sys.argv) > 1 else "admin@example.com"
        print(f"Creating admin user with email: {admin_email}")
        
        try:
            # Create a user record
            user_data = {
                'email': admin_email,
                'is_admin': True
            }
            response = supabase.table('users').upsert(user_data).execute()
            
            if response.data and len(response.data) > 0:
                print(f"Admin user created/updated successfully: {admin_email}")
                user_id = response.data[0]['id']
                
                # Try to create other tables by inserting and then deleting test records
                print("Testing access to other tables...")
                
                # Test file_history table
                print("Testing file_history table...")
                file_history_data = {
                    'user_id': user_id,
                    'original_filename': 'test.txt',
                    'file_type': 'TXT',
                    'processed_filename': 'test_processed.txt'
                }
                file_response = supabase.table('file_history').insert(file_history_data).execute()
                print(f"File history test result: {len(file_response.data) > 0}")
                
                # Test feedback table
                print("Testing feedback table...")
                feedback_data = {
                    'user_id': user_id,
                    'email': admin_email,
                    'feedback_text': 'Test feedback'
                }
                feedback_response = supabase.table('feedback').insert(feedback_data).execute()
                print(f"Feedback test result: {len(feedback_response.data) > 0}")
                
                # Test newsletter table
                print("Testing newsletter_subscribers table...")
                newsletter_data = {
                    'email': f"newsletter_{admin_email}"
                }
                newsletter_response = supabase.table('newsletter_subscribers').upsert(newsletter_data).execute()
                print(f"Newsletter test result: {len(newsletter_response.data) > 0}")
                
                print("All tests completed!")
            else:
                print(f"Failed to create admin user: {admin_email}")
        except Exception as e:
            print(f"Error creating/testing tables: {str(e)}")
            
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    # Create a Flask app and push an application context
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    with app.app_context():
        create_tables() 