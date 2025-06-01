from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.auth.decorators import login_required
from app.auth.models import User
from app.services.payment_service import PaymentService

subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscription')

@subscription_bp.route('/')
@login_required
def subscription():
    """Subscription management page."""
    user_id = session['user']['id']
    has_subscription = User.has_active_subscription(user_id)
    
    return render_template('subscription/subscription.html', has_subscription=has_subscription)

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription."""
    user_id = session['user']['id']
    plan = request.form.get('plan', 'premium')
    
    # Get price ID based on plan
    price_ids = PaymentService.get_price_ids()
    price_id = price_ids.get(plan)
    
    if not price_id:
        flash('Invalid subscription plan selected.', 'error')
        return redirect(url_for('subscription.subscription'))
    
    # Create checkout session
    result = PaymentService.create_checkout_session(
        user_id=user_id,
        price_id=price_id,
        success_url=url_for('subscription.subscription_success', _external=True),
        cancel_url=url_for('subscription.subscription_cancel', _external=True)
    )
    
    if result['success']:
        return redirect(result['checkout_url'])
    else:
        flash(f'Error creating checkout session: {result["error"]}', 'error')
        return redirect(url_for('subscription.subscription'))

@subscription_bp.route('/success')
@login_required
def subscription_success():
    """Handle successful subscription."""
    user_id = session['user']['id']
    
    # Verify the user now has an active subscription
    if User.has_active_subscription(user_id):
        flash('Subscription activated successfully! You now have unlimited access.', 'success')
    else:
        flash('Subscription is being processed. Please wait a moment and refresh the page.', 'info')
    
    return render_template('subscription/success.html')

@subscription_bp.route('/cancel')
@login_required
def subscription_cancel():
    """Handle cancelled subscription."""
    flash('Subscription cancelled. You can try again anytime.', 'info')
    return render_template('subscription/cancel.html')

@subscription_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhooks."""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        return jsonify({'error': 'Missing signature'}), 400
    
    # Verify webhook signature
    verification_result = PaymentService.verify_webhook_signature(payload, sig_header)
    
    if not verification_result['success']:
        print(f"Webhook signature verification failed: {verification_result['error']}")
        return jsonify({'error': verification_result['error']}), 400
    
    event = verification_result['event']
    
    # Handle the event
    result = PaymentService.handle_webhook_event(event)
    
    if result['success']:
        return jsonify({'status': 'success'}), 200
    else:
        print(f"Webhook handling failed: {result['error']}")
        return jsonify({'error': result['error']}), 400 