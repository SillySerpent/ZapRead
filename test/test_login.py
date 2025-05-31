#!/usr/bin/env python3
import requests
import os
import sys
import re
from pprint import pprint

def test_login():
    """Test user login functionality."""
    print("Testing ZapRead User Login")
    print("-" * 50)
    
    # Get the base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    # Prompt user for credentials to test login
    test_email = input("Enter email to test login (e.g. test_user_3547fa32@gmail.com): ")
    test_password = input("Enter password (default: TestPassword123!): ") or "TestPassword123!"
    
    # Get the login page to check if it's working
    print(f"Getting login page from {base_url}/login")
    try:
        resp = requests.get(f"{base_url}/login")
        if resp.status_code == 200:
            print(f"✓ Successfully accessed login page (Status: {resp.status_code})")
        else:
            print(f"✗ Failed to access login page (Status: {resp.status_code})")
            return
    except Exception as e:
        print(f"✗ Error accessing login page: {str(e)}")
        return
    
    # Attempt to login
    print(f"\nAttempting to login with email: {test_email}")
    try:
        resp = requests.post(
            f"{base_url}/login",
            data={"email": test_email, "password": test_password},
            allow_redirects=False  # Don't follow redirects to see the actual response
        )
        
        print(f"Login response status: {resp.status_code}")
        
        # Check if login was successful (usually 302 redirect to dashboard)
        if resp.status_code in [200, 302]:
            print(f"✓ Login request completed")
            
            # If it's a redirect, it usually means success
            if resp.status_code == 302:
                redirect_url = resp.headers.get('Location', '')
                print(f"  Redirected to: {redirect_url}")
                print("  ✓ Login was successful!")
            
            # If it returned 200, it might contain an error
            elif resp.status_code == 200:
                # Extract flash messages using regex
                flash_pattern = r'class="alert alert-(\w+)".*?>(.*?)<\/div>'
                flash_matches = re.findall(flash_pattern, resp.text, re.DOTALL)
                
                if flash_matches:
                    for flash_type, flash_msg in flash_matches:
                        flash_msg = flash_msg.strip()
                        print(f"  Flash message ({flash_type}): {flash_msg}")
                        
                        if flash_type == "success":
                            print("  ✓ Login appears to be successful")
                        elif flash_type == "error":
                            print("  ✗ Login failed with error message")
                else:
                    print("  No flash messages found in the response")
                    
                    # Look for any error text
                    if "error" in resp.text.lower() or "invalid" in resp.text.lower():
                        print("  ⚠ Response contains error indicators")
        else:
            print(f"✗ Login failed with status code: {resp.status_code}")
            print(f"Response content (first 200 chars): {resp.text[:200]}...")  # Show first 200 chars
    except Exception as e:
        print(f"✗ Error during login request: {str(e)}")
    
    print("\nLogin test completed")

if __name__ == "__main__":
    test_login() 