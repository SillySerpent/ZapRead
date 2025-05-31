import stripe
from config import get_config

config = get_config()

# Set up Stripe API key
stripe.api_key = config.STRIPE_SECRET_KEY

def create_checkout_session(user_id, success_url, cancel_url):
    """
    Create a Stripe checkout session for subscription.
    
    Args:
        user_id (str): The user ID to associate with the checkout session.
        success_url (str): The URL to redirect to after successful checkout.
        cancel_url (str): The URL to redirect to if checkout is cancelled.
        
    Returns:
        dict: The created checkout session.
    """
    try:
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=user_id,
            success_url=success_url,
            cancel_url=cancel_url,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": config.STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ]
        )
        return checkout_session
    except Exception as e:
        # Log the error
        print(f"Error creating checkout session: {str(e)}")
        raise


def handle_webhook_event(payload, signature):
    """
    Verify and handle a webhook event from Stripe.
    
    Args:
        payload (str): The raw request payload.
        signature (str): The Stripe signature header.
        
    Returns:
        dict: The parsed webhook event.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, config.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError as e:
        # Invalid payload
        print(f"Invalid payload: {str(e)}")
        raise
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"Invalid signature: {str(e)}")
        raise


def get_subscription(subscription_id):
    """
    Get a subscription by ID.
    
    Args:
        subscription_id (str): The Stripe subscription ID.
        
    Returns:
        dict: The subscription object.
    """
    try:
        return stripe.Subscription.retrieve(subscription_id)
    except Exception as e:
        print(f"Error retrieving subscription: {str(e)}")
        raise 