from functools import wraps
from flask import session, redirect, url_for, flash
from app.auth.models import User

def admin_required(f):
    """
    Decorator to require admin access for routes.
    
    This decorator checks if the user is logged in and has admin privileges.
    If not, redirects to the dashboard with an error message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is logged in
        if 'user' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user is admin
        user_id = session['user']['id']
        is_admin = User.is_admin(user_id)
        
        if not is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('core.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function 