import stripe
from flask import current_app, url_for
from app.auth.models import User

class PaymentService:
    """Service for handling payment operations with Stripe."""
    
    @classmethod
    def initialize_stripe(cls):
        """Initialize Stripe with the secret key."""
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    @classmethod
    def create_checkout_session(cls, user_id, price_id, success_url, cancel_url):
        """
        Create a Stripe checkout session for subscription.
        
        Args:
            user_id: User ID
            price_id: Stripe price ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            
        Returns:
            dict: Result containing session URL or error
        """
        try:
            cls.initialize_stripe()
            
            # Get user email
            user = User.get_by_id(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user.get('email'),
                metadata={
                    'user_id': str(user_id)
                }
            )
            
            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create checkout session: {str(e)}'
            }
    
    @classmethod
    def handle_webhook_event(cls, event):
        """
        Handle Stripe webhook events.
        
        Args:
            event: Stripe event object
            
        Returns:
            dict: Result of handling the event
        """
        try:
            event_type = event['type']
            
            if event_type == 'checkout.session.completed':
                return cls._handle_checkout_completed(event['data']['object'])
            elif event_type == 'invoice.payment_succeeded':
                return cls._handle_payment_succeeded(event['data']['object'])
            elif event_type == 'invoice.payment_failed':
                return cls._handle_payment_failed(event['data']['object'])
            elif event_type == 'customer.subscription.deleted':
                return cls._handle_subscription_cancelled(event['data']['object'])
            else:
                print(f"Unhandled webhook event type: {event_type}")
                return {'success': True, 'message': 'Event ignored'}
                
        except Exception as e:
            print(f"Error handling webhook event: {str(e)}")
            return {
                'success': False,
                'error': f'Webhook handling failed: {str(e)}'
            }
    
    @classmethod
    def _handle_checkout_completed(cls, session):
        """Handle successful checkout completion."""
        try:
            user_id = session.get('metadata', {}).get('user_id')
            if not user_id:
                print("No user_id in checkout session metadata")
                return {'success': False, 'error': 'No user ID found'}
            
            subscription_id = session.get('subscription')
            customer_id = session.get('customer')
            
            # Update user subscription status
            success = User.update_subscription_status(
                user_id, 
                True, 
                subscription_id=subscription_id,
                customer_id=customer_id
            )
            
            if success:
                print(f"Subscription activated for user {user_id}")
                return {'success': True, 'message': 'Subscription activated'}
            else:
                print(f"Failed to activate subscription for user {user_id}")
                return {'success': False, 'error': 'Failed to update user subscription'}
                
        except Exception as e:
            print(f"Error in checkout completed handler: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def _handle_payment_succeeded(cls, invoice):
        """Handle successful payment."""
        try:
            subscription_id = invoice.get('subscription')
            if subscription_id:
                # Find user by subscription ID and ensure their subscription is active
                user = User.get_by_subscription_id(subscription_id)
                if user:
                    User.update_subscription_status(user['id'], True)
                    print(f"Payment succeeded for subscription {subscription_id}")
                    return {'success': True, 'message': 'Payment processed'}
            
            return {'success': True, 'message': 'Payment succeeded but no user found'}
            
        except Exception as e:
            print(f"Error in payment succeeded handler: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def _handle_payment_failed(cls, invoice):
        """Handle failed payment."""
        try:
            subscription_id = invoice.get('subscription')
            if subscription_id:
                # Find user by subscription ID and mark subscription as inactive
                user = User.get_by_subscription_id(subscription_id)
                if user:
                    User.update_subscription_status(user['id'], False)
                    print(f"Payment failed for subscription {subscription_id}")
                    return {'success': True, 'message': 'Subscription deactivated due to payment failure'}
            
            return {'success': True, 'message': 'Payment failed but no user found'}
            
        except Exception as e:
            print(f"Error in payment failed handler: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def _handle_subscription_cancelled(cls, subscription):
        """Handle subscription cancellation."""
        try:
            subscription_id = subscription.get('id')
            if subscription_id:
                # Find user by subscription ID and mark subscription as inactive
                user = User.get_by_subscription_id(subscription_id)
                if user:
                    User.update_subscription_status(user['id'], False)
                    print(f"Subscription cancelled: {subscription_id}")
                    return {'success': True, 'message': 'Subscription cancelled'}
            
            return {'success': True, 'message': 'Subscription cancelled but no user found'}
            
        except Exception as e:
            print(f"Error in subscription cancelled handler: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def get_price_ids(cls):
        """Get configured Stripe price IDs."""
        return {
            'premium': current_app.config.get('STRIPE_PREMIUM_PRICE_ID'),
            'basic': current_app.config.get('STRIPE_BASIC_PRICE_ID')
        }
    
    @classmethod
    def verify_webhook_signature(cls, payload, signature):
        """
        Verify Stripe webhook signature.
        
        Args:
            payload: Raw request payload
            signature: Stripe signature header
            
        Returns:
            dict: Stripe event object or error
        """
        try:
            webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
            if not webhook_secret:
                return {
                    'success': False,
                    'error': 'Webhook secret not configured'
                }
            
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            
            return {
                'success': True,
                'event': event
            }
            
        except ValueError:
            return {
                'success': False,
                'error': 'Invalid payload'
            }
        except stripe.error.SignatureVerificationError:
            return {
                'success': False,
                'error': 'Invalid signature'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Webhook verification failed: {str(e)}'
            } 