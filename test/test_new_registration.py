#!/usr/bin/env python3
import requests
import os
import sys
import re
import time
import uuid
from pprint import pprint

def test_registration():
    """Test user registration functionality with a unique email."""
    print("Testing ZapRead User Registration")
    print("-" * 50)
    
    # Get the base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    # Generate a unique email to avoid rate limiting issues
    unique_id = str(uuid.uuid4())[:8]
    test_email = f"test_user_{unique_id}@gmail.com"
    test_password = "TestPassword123!"
    
    print(f"Using unique email: {test_email}")
    
    # Get the registration page to check if it's working
    print(f"Getting registration page from {base_url}/register")
    try:
        resp = requests.get(f"{base_url}/register")
        if resp.status_code == 200:
            print(f"✓ Successfully accessed registration page (Status: {resp.status_code})")
        else:
            print(f"✗ Failed to access registration page (Status: {resp.status_code})")
            return
    except Exception as e:
        print(f"✗ Error accessing registration page: {str(e)}")
        return
    
    # Attempt to register a new user
    print(f"\nAttempting to register user with email: {test_email}")
    try:
        resp = requests.post(
            f"{base_url}/register",
            data={"email": test_email, "password": test_password},
            allow_redirects=False  # Don't follow redirects to see the actual response
        )
        
        print(f"Registration response status: {resp.status_code}")
        
        # Check if registration was successful (usually 302 redirect to login)
        if resp.status_code in [200, 302]:
            print(f"✓ Registration request completed")
            
            # If it's a redirect, it usually means success
            if resp.status_code == 302:
                redirect_url = resp.headers.get('Location', '')
                print(f"  Redirected to: {redirect_url}")
                print("  ✓ Registration was successful!")
            
            # If it returned 200, it might contain a success message or error
            elif resp.status_code == 200:
                # Extract flash messages using regex
                flash_pattern = r'class="alert alert-(\w+)".*?>(.*?)<\/div>'
                flash_matches = re.findall(flash_pattern, resp.text, re.DOTALL)
                
                if flash_matches:
                    for flash_type, flash_msg in flash_matches:
                        flash_msg = flash_msg.strip()
                        print(f"  Flash message ({flash_type}): {flash_msg}")
                        
                        if flash_type == "success":
                            print("  ✓ Registration appears to be successful")
                        elif flash_type == "error":
                            print("  ✗ Registration failed with error message")
                else:
                    print("  No flash messages found in the response")
                    
                    # Look for any error text
                    if "error" in resp.text.lower():
                        print("  ⚠ Response contains error indicators")
                        
                # Print part of the HTML response to diagnose
                print("\nResponse HTML excerpt:")
                print("-" * 50)
                # Find the body content
                body_match = re.search(r'<body.*?>(.*?)</body>', resp.text, re.DOTALL)
                if body_match:
                    body_content = body_match.group(1)
                    # Clean up whitespace for easier reading
                    body_content = re.sub(r'\s+', ' ', body_content)
                    print(body_content[:1000] + "..." if len(body_content) > 1000 else body_content)
                else:
                    # If can't find body, just print a portion of the response
                    print(resp.text[:1000] + "..." if len(resp.text) > 1000 else resp.text)
        else:
            print(f"✗ Registration failed with status code: {resp.status_code}")
            print(f"Response content (first 200 chars): {resp.text[:200]}...")  # Show first 200 chars
    except Exception as e:
        print(f"✗ Error during registration request: {str(e)}")
    
    print("\nRegistration test completed")

if __name__ == "__main__":
    test_registration() 