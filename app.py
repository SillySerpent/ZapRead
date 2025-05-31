import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import stripe

from config import get_config
from supabase_client import get_supabase, close_supabase
import stripe_client
import bionic_processor
from models import User

# Initialize Flask app
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Set up Stripe
stripe.api_key = config.STRIPE_SECRET_KEY

# Register close_supabase function to be called when app context ends
app.teardown_appcontext(close_supabase)

# Authentication helper functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is in session
        if 'user' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
            
        # Additional check with Supabase to validate the session if needed
        try:
            supabase = get_supabase()
            user = supabase.auth.get_user()
            if not user:
                # Clear invalid session
                session.pop('user', None)
                flash('Your session has expired. Please log in again.', 'error')
                return redirect(url_for('login'))
        except Exception as e:
            # On error, we'll still allow access if we have a session
            print(f"Session validation error: {str(e)}")
            
        return f(*args, **kwargs)
    return decorated_function

def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is logged in
        if 'user' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        
        # Check if user has an active subscription
        user_id = session['user']['id']
        if not User.has_active_subscription(user_id):
            flash('You need a subscription to access this feature', 'error')
            return redirect(url_for('subscription'))
        
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Home page route."""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Attempting to register user with email: {email}")
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('register.html')
        
        try:
            supabase = get_supabase()
            print(f"Supabase URL: {config.SUPABASE_URL}")
            print(f"Supabase Key (first/last 5 chars): {config.SUPABASE_KEY[:5]}...{config.SUPABASE_KEY[-5:]}")
            
            # Create user in Supabase Auth with proper data structure
            # Supabase v2 requires additional data fields for sign up
            print(f"Calling supabase.auth.sign_up with email: {email}")
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": "ZapRead User",  # Default values that can be updated later
                        "app_metadata": {
                            "provider": "email"
                        }
                    }
                }
            })
            
            print(f"Auth Response Type: {type(auth_response)}")
            print(f"Auth Response: {auth_response}")
            
            # Check if user was created
            if auth_response.user:
                user_id = auth_response.user.id
                print(f"User created successfully with ID: {user_id}")
                flash('Registration successful! Please check your email to verify your account.', 'success')
                return redirect(url_for('login'))
            else:
                print("Auth response does not contain user data")
                flash('Registration failed. Please try again.', 'error')
                return render_template('register.html')
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Registration Error: {str(e)}")
            print(error_details)
            flash(f'Error during registration: {str(e)}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Attempting to log in user with email: {email}")
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        try:
            supabase = get_supabase()
            # Sign in user with Supabase Auth
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user and auth_response.session:
                # Store user session in Flask session for authentication
                session['user'] = {
                    'id': auth_response.user.id,
                    'email': auth_response.user.email,
                }
                print(f"Login successful for user: {email}")
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                print(f"Login failed - invalid response: {auth_response}")
                flash('Invalid credentials', 'error')
                return render_template('login.html')
        except Exception as e:
            print(f"Login Error: {str(e)}")
            flash(f'Invalid credentials: {str(e)}', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/auth/callback', methods=['GET'])
def auth_callback():
    """Handle authentication callbacks from Supabase."""
    # Extract parameters that might be sent by Supabase
    token = request.args.get('token')
    type_param = request.args.get('type')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    print(f"Auth callback received: type={type_param}, token={token[:10]+'...' if token else 'None'}")
    
    # If there's an error, display it
    if error or error_description:
        error_msg = error_description or error or "Unknown authentication error"
        flash(f"Authentication error: {error_msg}", "error")
        return redirect(url_for('login'))
    
    # Handle different callback types
    if type_param == 'recovery':
        flash('Password reset link clicked. Please enter a new password.', 'info')
        # In a real implementation, you would handle password reset here
        return redirect(url_for('login'))
    elif type_param == 'signup' or type_param == 'magiclink' or type_param == 'invite':
        # For email verification, show the custom verification success page
        return render_template('email_verified.html')
    else:
        # Default success message for any other verification
        flash('Email verification successful! You can now log in with your credentials.', 'success')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """User logout route."""
    try:
        # Clear the Flask session
        session.clear()
        
        # Also sign out from Supabase
        supabase = get_supabase()
        supabase.auth.sign_out()
        
        flash('You have been logged out successfully', 'success')
    except Exception as e:
        flash(f'Error during logout: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route."""
    # Get user ID from session
    user_id = session['user']['id']
    user_email = session['user']['email']
    
    # Get user's file history
    file_history = User.get_file_history(user_id)
    
    has_subscription = User.has_active_subscription(user_id)
    
    return render_template(
        'dashboard.html', 
        user={
            'id': user_id,
            'email': user_email
        }, 
        file_history=file_history,
        has_subscription=has_subscription
    )

@app.route('/subscription')
@login_required
def subscription():
    """Subscription page route."""
    return render_template('subscription.html')

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session."""
    user_id = session['user']['id']
    
    try:
        # Set success and cancel URLs
        success_url = url_for('subscription_success', _external=True)
        cancel_url = url_for('subscription_cancel', _external=True)
        
        # Create Stripe checkout session
        checkout_session = stripe_client.create_checkout_session(
            user_id, 
            success_url, 
            cancel_url
        )
        
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/subscription/success')
@login_required
def subscription_success():
    """Subscription success page."""
    flash('Thank you for subscribing!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/subscription/cancel')
@login_required
def subscription_cancel():
    """Subscription cancellation page."""
    flash('Subscription process was cancelled.', 'info')
    return redirect(url_for('subscription'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """File upload route."""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        # Check subscription status
        user_id = session['user']['id']
        has_subscription = User.has_active_subscription(user_id)
        
        if file:
            # Generate a unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            try:
                # Process the file
                processed_content, file_type, temp_dir = bionic_processor.process_file(file_path)
                
                # Save processed content
                processed_file_path = bionic_processor.save_processed_file(
                    processed_content, 
                    filename, 
                    file_type,
                    temp_dir
                )
                
                # Save to file history
                User.add_file_to_history(
                    user_id, 
                    filename, 
                    file_type, 
                    os.path.basename(processed_file_path)
                )
                
                # Clean up the original file
                os.remove(file_path)
                
                # Get file extension to determine how to serve it
                _, ext = os.path.splitext(processed_file_path)
                
                # For HTML files (converted from text), display in browser
                if ext.lower() == '.html':
                    # Serve HTML directly in the browser with proper content type
                    return send_file(
                        processed_file_path,
                        mimetype='text/html',
                        as_attachment=False,  # Display in browser
                        download_name=os.path.basename(processed_file_path)
                    )
                else:
                    # For other file types (PDF, DOCX), offer as download
                    return send_file(
                        processed_file_path,
                        as_attachment=True,
                        download_name=os.path.basename(processed_file_path)
                    )
            except Exception as e:
                # Clean up in case of error
                if os.path.exists(file_path):
                    os.remove(file_path)
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(url_for('dashboard'))
    
    return render_template('upload.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    """Stripe webhook endpoint."""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe_client.handle_webhook_event(payload, sig_header)
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Get the user ID from the client_reference_id
            user_id = session.get('client_reference_id')
            subscription_id = session.get('subscription')
            
            if user_id and subscription_id:
                # Update user's subscription status
                User.update_subscription(user_id, subscription_id)
        
        # Handle subscription cancellation
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            
            # Find user with this subscription and update their status
            # This would require a lookup by subscription ID, which might
            # need additional database querying logic
            
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/verify-email', methods=['GET'])
@app.route('/verify', methods=['GET'])
def verify_email_redirect():
    """Catch-all route for email verification links that don't use the standard callback URL."""
    return redirect(url_for('auth_callback', **request.args))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=config.DEBUG) 