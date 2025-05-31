#!/usr/bin/env python3
"""
Test script for Supabase authentication
"""
import os
from pprint import pprint
from supabase import create_client, Client
from config import get_config

config = get_config()

def main():
    print("Testing Supabase Authentication")
    print("-" * 50)
    
    # Get Supabase credentials
    supabase_url = config.SUPABASE_URL
    supabase_key = config.SUPABASE_KEY
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        return
    
    print(f"Supabase URL: {supabase_url}")
    print(f"Supabase Key: {supabase_key[:5]}...{supabase_key[-5:]}")
    
    # Initialize Supabase client
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("✓ Supabase client initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing Supabase client: {str(e)}")
        return
    
    # Test user credentials
    test_email = "test_user456@gmail.com"
    test_password = "TestPassword123!"
    
    # Try to sign up a new user
    try:
        print(f"\nTesting sign up with email: {test_email}")
        auth_response = supabase.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        print(f"Response type: {type(auth_response)}")
        print("Response data:")
        pprint(vars(auth_response))
        
        if hasattr(auth_response, 'user') and auth_response.user:
            print("\n✓ User created successfully:")
            print(f"  User ID: {auth_response.user.id}")
            print(f"  Email: {auth_response.user.email}")
        else:
            print("\n✗ Failed to create user")
            
    except Exception as e:
        print(f"\n✗ Error during sign up: {str(e)}")
    
    print("\nTest completed")

if __name__ == "__main__":
    main() 