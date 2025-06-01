import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.services.supabase_service import get_supabase
from app.auth.models import User
from app.auth.decorators import login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Attempting to register user with email: {email}")
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/register.html')
        
        try:
            supabase = get_supabase()
            print(f"Calling supabase.auth.sign_up with email: {email}")
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": "ZapRead User",
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
                    flash('Registration successful! Please log in and subscribe to access premium features.', 'success')
                    return redirect(url_for('auth.login') + '?subscribe=1')
                else:
                    flash('Registration successful! Please check your email for verification, then log in.', 'success')
                    return redirect(url_for('auth.login'))
            else:
                flash('Registration failed. Please try again.', 'error')
                return render_template('auth/register.html')
        except Exception as e:
            print(f"Registration Error: {str(e)}")
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Attempting to log in user with email: {email}")
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
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
                
                return redirect(url_for('core.dashboard'))
            else:
                print(f"Login failed - invalid response: {auth_response}")
                flash('Invalid credentials', 'error')
                return render_template('auth/login.html')
        except Exception as e:
            print(f"Login Error: {str(e)}")
            flash(f'Invalid credentials: {str(e)}', 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
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
    
    return redirect(url_for('core.index'))

@auth_bp.route('/callback', methods=['GET'])
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
        return redirect(url_for('auth.login'))
    
    # Handle different callback types
    if type_param == 'recovery':
        flash('Password reset link clicked. Please enter a new password.', 'info')
        return redirect(url_for('auth.login'))
    elif type_param == 'signup' or type_param == 'magiclink' or type_param == 'invite':
        return render_template('auth/email_verified.html')
    else:
        flash('Email verification successful! You can now log in with your credentials.', 'success')
        return redirect(url_for('auth.login'))

@auth_bp.route('/verify-email', methods=['GET'])
@auth_bp.route('/verify', methods=['GET'])
def verify_email_redirect():
    """Handle email verification redirect."""
    return redirect(url_for('auth.auth_callback', **request.args))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page."""
    user_id = session['user']['id']
    user_email = session['user']['email']
    
    if request.method == 'POST':
        # Handle profile updates
        try:
            # Get form data
            full_name = request.form.get('full_name', '').strip()
            newsletter_opt_in = request.form.get('newsletter_opt_in') == 'on'
            
            # Notification preferences
            email_notifications = request.form.get('email_notifications') == 'on'
            processing_complete = request.form.get('processing_complete') == 'on'
            
            notification_preferences = {
                'email_notifications': email_notifications,
                'processing_complete': processing_complete
            }
            
            # Update profile data
            profile_data = {
                'full_name': full_name,
                'newsletter_opt_in': newsletter_opt_in,
                'notification_preferences': notification_preferences,
                'updated_at': 'now()'
            }
            
            # Update in database
            User.update_profile(user_id, profile_data)
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            flash('Error updating profile. Please try again.', 'error')
    
    # Get current user data
    try:
        user_data = User.get_by_id(user_id)
        if not user_data:
            user_data = {
                'full_name': '',
                'newsletter_opt_in': False,
                'notification_preferences': {
                    'email_notifications': True,
                    'processing_complete': True
                }
            }
    except Exception as e:
        print(f"Error getting user data: {str(e)}")
        user_data = {
            'full_name': '',
            'newsletter_opt_in': False,
            'notification_preferences': {
                'email_notifications': True,
                'processing_complete': True
            }
        }
    
    # Get file history
    file_history = User.get_file_history(user_id, limit=10)
    
    # Check subscription status
    has_subscription = User.has_active_subscription(user_id)
    
    # Get current usage for free users
    daily_uploads = 0
    if not has_subscription:
        daily_uploads = User.get_daily_upload_count(user_id)
    
    # Check if user is admin
    is_admin = False
    try:
        user_profile = User.get_by_id(user_id)
        is_admin = user_profile.get('is_admin', False) if user_profile else False
    except Exception as e:
        print(f"Error checking admin status: {str(e)}")
        is_admin = False

    return render_template('auth/profile.html', 
                         user_data=user_data, 
                         user_email=user_email,
                         file_history=file_history,
                         has_subscription=has_subscription,
                         daily_uploads=daily_uploads,
                         is_admin=is_admin)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('All password fields are required.', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        supabase = get_supabase()
        
        # Update password using Supabase Auth
        response = supabase.auth.update({'password': new_password})
        
        if response.user:
            flash('Password changed successfully!', 'success')
        else:
            flash('Failed to change password. Please try again.', 'error')
            
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        flash(f'Error changing password: {str(e)}', 'error')
    
    return redirect(url_for('auth.profile')) 