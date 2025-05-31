import os
import uuid
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import stripe

from config import get_config
from supabase_client import get_supabase, close_supabase
import stripe_client
import bionic_processor
from models import User, WebsiteContent, Analytics

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

# Analytics middleware to track page views
@app.before_request
def track_page_view():
    # Skip tracking for static files and certain endpoints
    if request.path.startswith('/static') or request.path == '/webhook' or request.path == '/favicon.ico':
        return
    
    # Get user ID if logged in
    user_id = session.get('user', {}).get('id', None)
    
    # Get metadata
    metadata = {
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string,
        'referrer': request.referrer,
        'method': request.method
    }
    
    # Track the page view
    try:
        Analytics.track_page_view(request.path, user_id, metadata)
    except Exception as e:
        # Don't fail the request if tracking fails
        print(f"Error tracking page view: {str(e)}")

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
    # Get dynamic content for the homepage
    try:
        testimonials = WebsiteContent.get_testimonials()
        # If no testimonials are found in the database, use default ones
        if not testimonials:
            testimonials = [
                {
                    'content': {
                        'text': 'ZapRead has completely transformed how I consume research papers. I can get through them 30% faster with better comprehension. It\'s a game-changer for academics.',
                        'author_name': 'Sarah Johnson',
                        'author_title': 'PhD Student',
                        'author_image': 'https://randomuser.me/api/portraits/women/32.jpg'
                    }
                },
                {
                    'content': {
                        'text': 'As someone with ADHD, focusing on text has always been a struggle. ZapRead has made reading so much easier by guiding my eye through the text. I\'m finally enjoying books again!',
                        'author_name': 'Michael Torres',
                        'author_title': 'Software Engineer',
                        'author_image': 'https://randomuser.me/api/portraits/men/54.jpg'
                    }
                },
                {
                    'content': {
                        'text': 'I have to read hundreds of pages of legal documents weekly. Since using ZapRead, I\'ve cut my review time by 20% while maintaining accuracy. Worth every penny!',
                        'author_name': 'Jennifer Miller',
                        'author_title': 'Corporate Lawyer',
                        'author_image': 'https://randomuser.me/api/portraits/women/68.jpg'
                    }
                }
            ]
    except Exception as e:
        print(f"Error loading testimonials: {str(e)}")
        testimonials = []
    
    return render_template('index.html', testimonials=testimonials)

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
                
                # If user is coming from guest upload and we have their processed file, 
                # save it to their account history
                if 'guest_processed_file' in session:
                    try:
                        # Create entry in file history
                        guest_file = session.get('guest_processed_file', {})
                        if guest_file.get('original_filename') and guest_file.get('file_type') and guest_file.get('processed_filename'):
                            User.add_file_to_history(
                                user_id,
                                guest_file.get('original_filename'),
                                guest_file.get('file_type'),
                                guest_file.get('processed_filename')
                            )
                            # Clear the guest file data
                            session.pop('guest_processed_file', None)
                    except Exception as e:
                        print(f"Error saving guest file to user history: {str(e)}")
                
                # Check if the user should be directed to subscribe (from URL parameter)
                plan = request.args.get('plan')
                if plan == 'premium':
                    flash('Registration successful! Let\'s set up your premium subscription.', 'success')
                    
                    # Auto login the user
                    session['user'] = {
                        'id': auth_response.user.id,
                        'email': auth_response.user.email,
                    }
                    return redirect(url_for('subscription'))
                else:
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
    
    # Check if plan parameter is passed to highlight premium option
    plan = request.args.get('plan')
    return render_template('register.html', premium_plan=(plan == 'premium'))

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
                
                # If user has guest processed file waiting, redirect to dashboard
                if 'guest_processed_file' in session:
                    try:
                        # Create entry in file history
                        guest_file = session.get('guest_processed_file', {})
                        if guest_file.get('original_filename') and guest_file.get('file_type') and guest_file.get('processed_filename'):
                            User.add_file_to_history(
                                auth_response.user.id,
                                guest_file.get('original_filename'),
                                guest_file.get('file_type'),
                                guest_file.get('processed_filename')
                            )
                            # Clear the guest file data
                            session.pop('guest_processed_file', None)
                            flash('Your guest document has been added to your account!', 'success')
                    except Exception as e:
                        print(f"Error saving guest file to user history: {str(e)}")
                
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
    
    # Check subscription status
    has_subscription = User.has_active_subscription(user_id)
    print(f"User {user_id} has subscription: {has_subscription}")
    
    # Get daily upload count for free users
    daily_uploads = 0
    can_upload_more = True
    
    if not has_subscription:
        daily_uploads = User.get_daily_upload_count(user_id)
        can_upload_more = daily_uploads < 5
    
    # Get the user's data directly to debug
    try:
        supabase = get_supabase()
        user_data = supabase.table('users').select('*').eq('id', user_id).execute().data
        if user_data and len(user_data) > 0:
            print(f"User data: {user_data[0]}")
    except Exception as e:
        print(f"Error getting user data: {str(e)}")
    
    return render_template(
        'dashboard.html', 
        user={
            'id': user_id,
            'email': user_email
        }, 
        file_history=file_history,
        has_subscription=has_subscription,
        daily_uploads=daily_uploads,
        can_upload_more=can_upload_more,
        max_uploads=5
    )

@app.route('/subscription')
@login_required
def subscription():
    """Subscription page route."""
    return render_template('subscription.html', config=config)

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
    # Get user ID from session
    user_id = session['user']['id']
    
    try:
        # In test mode, webhooks might not be received properly
        # So we'll directly update the user's subscription status
        # This serves as a backup to the webhook handler
        
        # Create a placeholder subscription ID if needed for testing
        test_subscription_id = f"test_sub_{uuid.uuid4()}"
        
        # Update the user's subscription status directly
        User.update_subscription(user_id, test_subscription_id)
        
        flash('Thank you for subscribing! You now have unlimited document conversions.', 'success')
    except Exception as e:
        print(f"Error updating subscription status: {str(e)}")
        flash('Your subscription was processed, but there was an issue updating your account. Please contact support.', 'warning')
    
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
    """File upload route for registered users."""
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
        
        # Get user ID from session
        user_id = session['user']['id']
        
        # Check subscription status and daily upload limit
        has_subscription = User.has_active_subscription(user_id)
        can_upload_more = True
        
        if not has_subscription:
            # Check if user has reached their daily upload limit
            can_upload_more = User.can_upload_more(user_id)
            
            if not can_upload_more:
                flash('You have reached your daily upload limit (5 documents). Please subscribe for unlimited uploads.', 'error')
                return redirect(url_for('subscription'))
        
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

@app.route('/guest-upload', methods=['GET', 'POST'])
def guest_upload():
    """File upload route for guest users."""
    # Check if guest already used their free conversion
    if session.get('guest_used_conversion'):
        return redirect(url_for('register_prompt'))
    
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
                
                # Store the guest file info in session for potential future registration
                session['guest_processed_file'] = {
                    'original_filename': filename,
                    'file_type': file_type,
                    'processed_filename': os.path.basename(processed_file_path)
                }
                
                # Mark that this guest has used their free conversion
                session['guest_used_conversion'] = True
                
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
                return redirect(url_for('guest_upload'))
    
    return render_template('guest_upload.html')

@app.route('/register-prompt')
def register_prompt():
    """Show prompt for guests to register after using their free conversion."""
    return render_template('register_prompt.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    """Stripe webhook endpoint."""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe_client.handle_webhook_event(payload, sig_header)
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session_data = event['data']['object']
            
            # Get the user ID from the client_reference_id
            user_id = session_data.get('client_reference_id')
            subscription_id = session_data.get('subscription')
            
            if user_id and subscription_id:
                # Update user's subscription status
                User.update_subscription(user_id, subscription_id)
        
        # Handle subscription cancellation
        elif event['type'] == 'customer.subscription.deleted':
            subscription_data = event['data']['object']
            subscription_id = subscription_data.get('id')
            
            # Find user with this subscription and update their status
            if subscription_id:
                # In a real implementation, you would look up the user by subscription ID
                # Here we'll use a placeholder approach
                supabase = get_supabase()
                response = supabase.table('users').select('id').eq('subscription_id', subscription_id).execute()
                users = response.data
                
                if users and len(users) > 0:
                    user_id = users[0]['id']
                    User.cancel_subscription(user_id)
            
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
    """Handle internal server errors."""
    return render_template('500.html'), 500

# Newsletter Routes
@app.route('/subscribe-newsletter', methods=['POST'])
def subscribe_newsletter():
    """Handle newsletter subscription."""
    email = request.form.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    
    try:
        supabase = get_supabase()
        
        # Check if email already exists
        response = supabase.table('newsletter_subscribers').select('*').eq('email', email).execute()
        
        if response.data and len(response.data) > 0:
            return jsonify({'success': True, 'message': 'You are already subscribed!'}), 200
        
        # Add new subscriber
        supabase.table('newsletter_subscribers').insert({
            'email': email,
            'subscribed_at': datetime.datetime.now().isoformat()
        }).execute()
        
        return jsonify({'success': True, 'message': 'Thank you for subscribing!'}), 200
    except Exception as e:
        print(f"Newsletter subscription error: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500

# Feedback Routes
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback submission."""
    feedback_type = request.form.get('feedback_type')
    message = request.form.get('message')
    email = request.form.get('email', '')
    
    if not feedback_type or not message:
        return jsonify({'success': False, 'message': 'Feedback type and message are required'}), 400
    
    try:
        supabase = get_supabase()
        
        # Get user ID if logged in
        user_id = session.get('user', {}).get('id', None)
        
        # Add feedback to database
        supabase.table('feedback').insert({
            'user_id': user_id,
            'feedback_type': feedback_type,
            'message': message,
            'email': email,
            'created_at': datetime.datetime.now().isoformat()
        }).execute()
        
        return jsonify({'success': True, 'message': 'Thank you for your feedback!'}), 200
    except Exception as e:
        print(f"Feedback submission error: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500

# Admin Routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is logged in
        if 'user' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        
        # Check if user is an admin
        user_id = session['user']['id']
        supabase = get_supabase()
        response = supabase.table('users').select('is_admin').eq('id', user_id).execute()
        
        if not response.data or not response.data[0].get('is_admin'):
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard page."""
    try:
        supabase = get_supabase()
        
        # Get statistics
        users_response = supabase.table('users').select('count', count='exact').execute()
        users_count = users_response.count if hasattr(users_response, 'count') else 0
        
        files_response = supabase.table('file_history').select('count', count='exact').execute()
        files_count = files_response.count if hasattr(files_response, 'count') else 0
        
        subscribers_response = supabase.table('newsletter_subscribers').select('count', count='exact').execute()
        subscribers_count = subscribers_response.count if hasattr(subscribers_response, 'count') else 0
        
        feedback_response = supabase.table('feedback').select('count', count='exact').execute()
        feedback_count = feedback_response.count if hasattr(feedback_response, 'count') else 0
        
        # Get recent users
        recent_users = supabase.table('users').select('*').order('created_at', desc=True).limit(5).execute()
        
        # Get recent files
        recent_files = supabase.table('file_history').select('*').order('created_at', desc=True).limit(5).execute()
        
        return render_template('admin/dashboard.html', 
                              users_count=users_count,
                              files_count=files_count,
                              subscribers_count=subscribers_count,
                              feedback_count=feedback_count,
                              recent_users=recent_users.data,
                              recent_files=recent_files.data)
    except Exception as e:
        print(f"Admin dashboard error: {str(e)}")
        flash('An error occurred while loading the admin dashboard', 'error')
        return redirect(url_for('dashboard'))

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin users page."""
    try:
        supabase = get_supabase()
        
        # Get all users
        users = supabase.table('users').select('*').order('created_at', desc=True).execute()
        
        return render_template('admin/users.html', users=users.data)
    except Exception as e:
        print(f"Admin users error: {str(e)}")
        flash('An error occurred while loading users', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    """Admin feedback page."""
    try:
        supabase = get_supabase()
        
        # Get all feedback
        feedback = supabase.table('feedback').select('*').order('created_at', desc=True).execute()
        
        return render_template('admin/feedback.html', feedback=feedback.data)
    except Exception as e:
        print(f"Admin feedback error: {str(e)}")
        flash('An error occurred while loading feedback', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/newsletter')
@admin_required
def admin_newsletter():
    """Admin newsletter page."""
    try:
        supabase = get_supabase()
        
        # Get all subscribers
        subscribers = supabase.table('newsletter_subscribers').select('*').order('subscribed_at', desc=True).execute()
        
        return render_template('admin/newsletter.html', subscribers=subscribers.data)
    except Exception as e:
        print(f"Admin newsletter error: {str(e)}")
        flash('An error occurred while loading subscribers', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/send-newsletter', methods=['GET', 'POST'])
@admin_required
def admin_send_newsletter():
    """Send newsletter to subscribers."""
    if request.method == 'POST':
        subject = request.form.get('subject')
        content = request.form.get('content')
        
        if not subject or not content:
            flash('Subject and content are required', 'error')
            return redirect(url_for('admin_send_newsletter'))
        
        try:
            # In a real implementation, you would integrate with an email service
            # For demonstration purposes, we'll just show a success message
            flash('Newsletter sent successfully!', 'success')
            return redirect(url_for('admin_newsletter'))
        except Exception as e:
            print(f"Send newsletter error: {str(e)}")
            flash('An error occurred while sending the newsletter', 'error')
            return redirect(url_for('admin_send_newsletter'))
    
    return render_template('admin/send_newsletter.html')

@app.route('/faq')
def faq():
    """FAQ page."""
    return render_template('faq.html')

@app.route('/feedback')
def feedback():
    """Feedback page."""
    return render_template('feedback.html')

@app.route('/admin/content')
@admin_required
def admin_content():
    """Admin content management page."""
    try:
        supabase = get_supabase()
        
        # Get all content sections
        website_content = supabase.table('website_content').select('*').order('section', desc=False).execute()
        
        # Organize content by section
        content_by_section = {}
        for item in website_content.data:
            section = item.get('section')
            if section not in content_by_section:
                content_by_section[section] = []
            content_by_section[section].append(item)
        
        return render_template('admin/content.html', content_by_section=content_by_section)
    except Exception as e:
        print(f"Admin content error: {str(e)}")
        flash('An error occurred while loading content', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/content/testimonials')
@admin_required
def admin_testimonials():
    """Admin testimonials management page."""
    try:
        # Get all testimonials
        testimonials = WebsiteContent.get_testimonials()
        
        return render_template('admin/testimonials.html', testimonials=testimonials)
    except Exception as e:
        print(f"Admin testimonials error: {str(e)}")
        flash('An error occurred while loading testimonials', 'error')
        return redirect(url_for('admin_content'))

@app.route('/admin/content/testimonials/add', methods=['POST'])
@admin_required
def admin_add_testimonial():
    """Add a new testimonial."""
    try:
        text = request.form.get('text')
        author_name = request.form.get('author_name')
        author_title = request.form.get('author_title')
        author_image = request.form.get('author_image')
        
        if not text or not author_name:
            flash('Testimonial text and author name are required', 'error')
            return redirect(url_for('admin_testimonials'))
        
        # Create testimonial data
        testimonial_data = {
            'text': text,
            'author_name': author_name,
            'author_title': author_title or '',
            'author_image': author_image or 'https://randomuser.me/api/portraits/lego/1.jpg'
        }
        
        # Add testimonial
        WebsiteContent.add_testimonial(testimonial_data)
        
        flash('Testimonial added successfully', 'success')
        return redirect(url_for('admin_testimonials'))
    except Exception as e:
        print(f"Admin add testimonial error: {str(e)}")
        flash('An error occurred while adding the testimonial', 'error')
        return redirect(url_for('admin_testimonials'))

@app.route('/admin/content/testimonials/edit/<testimonial_id>', methods=['POST'])
@admin_required
def admin_edit_testimonial(testimonial_id):
    """Edit a testimonial."""
    try:
        text = request.form.get('text')
        author_name = request.form.get('author_name')
        author_title = request.form.get('author_title')
        author_image = request.form.get('author_image')
        
        if not text or not author_name:
            flash('Testimonial text and author name are required', 'error')
            return redirect(url_for('admin_testimonials'))
        
        # Create testimonial data
        testimonial_data = {
            'text': text,
            'author_name': author_name,
            'author_title': author_title or '',
            'author_image': author_image or 'https://randomuser.me/api/portraits/lego/1.jpg'
        }
        
        # Update testimonial
        WebsiteContent.update_testimonial(testimonial_id, testimonial_data)
        
        flash('Testimonial updated successfully', 'success')
        return redirect(url_for('admin_testimonials'))
    except Exception as e:
        print(f"Admin edit testimonial error: {str(e)}")
        flash('An error occurred while updating the testimonial', 'error')
        return redirect(url_for('admin_testimonials'))

@app.route('/admin/content/testimonials/delete/<testimonial_id>', methods=['POST'])
@admin_required
def admin_delete_testimonial(testimonial_id):
    """Delete a testimonial."""
    try:
        # Delete testimonial
        WebsiteContent.delete_testimonial(testimonial_id)
        
        flash('Testimonial deleted successfully', 'success')
        return redirect(url_for('admin_testimonials'))
    except Exception as e:
        print(f"Admin delete testimonial error: {str(e)}")
        flash('An error occurred while deleting the testimonial', 'error')
        return redirect(url_for('admin_testimonials'))

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics page."""
    try:
        # Get analytics data
        daily_stats = Analytics.get_daily_stats(days=30)
        
        # Convert to format suitable for charts
        dates = sorted(daily_stats.keys())
        page_views = [daily_stats[date]['count'] for date in dates]
        unique_users = [daily_stats[date]['unique_users'] for date in dates]
        
        # Get top pages
        page_views_data = Analytics.get_page_views(days=30)
        
        # Count page views by page
        page_counts = {}
        for view in page_views_data:
            page = view['page']
            if page not in page_counts:
                page_counts[page] = 0
            page_counts[page] += 1
        
        # Sort by count (descending)
        top_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return render_template('admin/analytics.html', 
                              dates=dates,
                              page_views=page_views,
                              unique_users=unique_users,
                              top_pages=top_pages)
    except Exception as e:
        print(f"Admin analytics error: {str(e)}")
        flash('An error occurred while loading analytics data', 'error')
        return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=config.DEBUG) 