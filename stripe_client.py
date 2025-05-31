import stripe
from config import get_config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info(f"Creating checkout session for user {user_id}")
        
        # Add metadata to track the user better
        metadata = {
            "user_id": user_id,
            "plan_type": "premium"
        }
        
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=user_id,
            success_url=success_url,
            cancel_url=cancel_url,
            payment_method_types=["card"],
            mode="subscription",
            metadata=metadata,
            line_items=[
                {
                    "price": config.STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ]
        )
        logger.info(f"Checkout session created: {checkout_session.id}")
        return checkout_session
    except Exception as e:
        # Log the error
        logger.error(f"Error creating checkout session for user {user_id}: {str(e)}")
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
        logger.info(f"Webhook event received: {event['type']}")
        return event
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid webhook payload: {str(e)}")
        raise
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid webhook signature: {str(e)}")
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
        logger.info(f"Retrieving subscription {subscription_id}")
        return stripe.Subscription.retrieve(subscription_id)
    except Exception as e:
        logger.error(f"Error retrieving subscription {subscription_id}: {str(e)}")
        raise


def cancel_subscription(subscription_id):
    """
    Cancel a subscription.
    
    Args:
        subscription_id (str): The Stripe subscription ID.
        
    Returns:
        dict: The cancelled subscription object.
    """
    try:
        logger.info(f"Cancelling subscription {subscription_id}")
        return stripe.Subscription.delete(subscription_id)
    except Exception as e:
        logger.error(f"Error cancelling subscription {subscription_id}: {str(e)}")
        raise


def create_customer(email, name=None, metadata=None):
    """
    Create a Stripe customer.
    
    Args:
        email (str): The customer's email.
        name (str, optional): The customer's name.
        metadata (dict, optional): Additional metadata.
        
    Returns:
        dict: The created customer object.
    """
    try:
        logger.info(f"Creating customer for {email}")
        customer_data = {
            "email": email
        }
        
        if name:
            customer_data["name"] = name
            
        if metadata:
            customer_data["metadata"] = metadata
            
        return stripe.Customer.create(**customer_data)
    except Exception as e:
        logger.error(f"Error creating customer for {email}: {str(e)}")
        raise


def update_subscription(subscription_id, new_price_id=None, cancel_at_period_end=None):
    """
    Update a subscription.
    
    Args:
        subscription_id (str): The Stripe subscription ID.
        new_price_id (str, optional): The new price ID to change to.
        cancel_at_period_end (bool, optional): Whether to cancel at period end.
        
    Returns:
        dict: The updated subscription object.
    """
    try:
        logger.info(f"Updating subscription {subscription_id}")
        
        update_data = {}
        
        if new_price_id:
            update_data["items"] = [{
                "id": subscription_id,
                "price": new_price_id
            }]
            
        if cancel_at_period_end is not None:
            update_data["cancel_at_period_end"] = cancel_at_period_end
            
        return stripe.Subscription.modify(subscription_id, **update_data)
    except Exception as e:
        logger.error(f"Error updating subscription {subscription_id}: {str(e)}")
        raise 