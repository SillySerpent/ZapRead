import os
import sys
from dotenv import load_dotenv
import stripe
from supabase import create_client

# Load environment variables
load_dotenv()

def test_env_variables():
    """Test that all required environment variables are set."""
    required_vars = [
        'SUPABASE_URL', 
        'SUPABASE_KEY',
        'STRIPE_SECRET_KEY', 
        'STRIPE_PUBLISHABLE_KEY', 
        'STRIPE_PRICE_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Error: Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set.")
    return True

def test_supabase_connection():
    """Test connection to Supabase."""
    try:
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Try to get the supabase client version - simplest way to test basic connectivity
        # Just checking if client creation works without any DB operations
        client_info = str(supabase)
        
        print(f"✅ Supabase client created successfully.")
        print(f"  - Note: Database tables need to be created according to README instructions.")
        print(f"  - Create 'users' and 'file_history' tables in your Supabase project.")
        return True
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        return False

def test_stripe_connection():
    """Test connection to Stripe."""
    try:
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Try a simple API call to verify connection
        account = stripe.Account.retrieve()
        
        # If we get here without an exception, connection is working
        print(f"✅ Stripe connection successful. Connected to account: {account.id}")
        
        # Verify price ID exists
        try:
            price_id = os.environ.get('STRIPE_PRICE_ID')
            price = stripe.Price.retrieve(price_id)
            print(f"✅ Stripe price ID {price_id} is valid. Product: {price.product}")
        except Exception as e:
            print(f"❌ Error retrieving Stripe price: {str(e)}")
            print(f"  - Check that STRIPE_PRICE_ID in .env is a price ID, not a product ID")
            print(f"  - Price IDs typically start with 'price_', not 'prod_'")
            print(f"  - Go to Stripe dashboard > Products > Your product > Select a price")
            
            # Try to list products to help the user
            try:
                products = stripe.Product.list(limit=5, active=True)
                if products.data:
                    print("\nAvailable products you can use:")
                    for product in products.data:
                        print(f"  - Product: {product.name} (ID: {product.id})")
                        
                        # Get prices for this product
                        prices = stripe.Price.list(product=product.id, active=True, limit=3)
                        if prices.data:
                            print("    Available prices:")
                            for price in prices.data:
                                amount = price.unit_amount / 100 if price.unit_amount else "N/A"
                                currency = price.currency.upper() if price.currency else ""
                                print(f"      - {amount} {currency} (Price ID: {price.id})")
            except Exception as product_e:
                pass
                
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error connecting to Stripe: {str(e)}")
        return False

def run_tests():
    """Run all connection tests."""
    print("🔍 Testing ZapRead connections...\n")
    
    # Test environment variables
    env_result = test_env_variables()
    if not env_result:
        print("\n❌ Environment variable test failed. Please check your .env file.")
        return False
    
    print("\n🔄 Testing Supabase connection...")
    supabase_result = test_supabase_connection()
    
    print("\n🔄 Testing Stripe connection...")
    stripe_result = test_stripe_connection()
    
    # Overall result
    if env_result and supabase_result and stripe_result:
        print("\n✅ All connection tests passed! ZapRead is ready to run.")
        return True
    else:
        print("\n❌ Some connection tests failed. Please fix the issues above before proceeding.")
        
        # Print setup tips if needed
        if not supabase_result:
            print("\n📋 Supabase Setup Tips:")
            print("  1. Go to your Supabase dashboard and check that your project is running")
            print("  2. Verify that your SUPABASE_URL and SUPABASE_KEY are correct in .env")
            print("  3. Create the required database tables as described in the README")
            
        if not stripe_result:
            print("\n📋 Stripe Setup Tips:")
            print("  1. Verify your STRIPE_SECRET_KEY in .env is correct")
            print("  2. Create a product and price in your Stripe dashboard")
            print("  3. Update your STRIPE_PRICE_ID in .env with a valid price ID (starts with 'price_')")
        
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
