from functools import wraps
from flask import session, flash, redirect, url_for
from app.services.supabase_service import get_supabase
from app.auth.models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is in session
        if 'user' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
            
        # Additional check with Supabase to validate the session if needed
        try:
            supabase = get_supabase()
            user = supabase.auth.get_user()
            if not user:
                # Clear invalid session
                session.pop('user', None)
                flash('Your session has expired. Please log in again.', 'error')
                return redirect(url_for('auth.login'))
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
            return redirect(url_for('auth.login'))
        
        # Check if user has an active subscription
        user_id = session['user']['id']
        if not User.has_active_subscription(user_id):
            flash('You need a subscription to access this feature', 'error')
            return redirect(url_for('subscription.subscription'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is logged in
        if 'user' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user is admin
        user_id = session['user']['id']
        user_data = User.get_by_id(user_id)
        
        if not user_data or not user_data.get('is_admin', False):
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('core.index'))
        
        return f(*args, **kwargs)
    return decorated_function 