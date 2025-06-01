from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.admin.decorators import admin_required
from app.auth.models import User
from app.core.models import WebsiteContent, Feedback, NewsletterSubscription
from app.services.supabase_service import get_supabase
from app.services.email_service import EmailService

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_required
def admin_dashboard():
    """Admin dashboard with key metrics."""
    try:
        supabase = get_supabase()
        
        # Get total user count from users table
        users_response = supabase.table('users').select('id').execute()
        total_users = len(users_response.data) if users_response.data else 0
        
        # Get total files processed from file_history
        files_response = supabase.table('file_history').select('id').execute()
        total_files = len(files_response.data) if files_response.data else 0
        
        # Get recent user registrations (last 7 days) from users table
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent_users_response = supabase.table('users').select('id').gte('created_at', week_ago).execute()
        recent_users = len(recent_users_response.data) if recent_users_response.data else 0
        
        # Get newsletter subscribers count
        subscribers_response = supabase.table('newsletter_subscribers').select('id').eq('is_active', True).execute()
        subscribers_count = len(subscribers_response.data) if subscribers_response.data else 0
        
        # Get feedback count
        feedback_response = supabase.table('feedback').select('id').execute()
        feedback_count = len(feedback_response.data) if feedback_response.data else 0
        
        # Get recent users for display
        recent_users_list = []
        try:
            recent_response = supabase.table('users').select('email, created_at, subscription_status').order('created_at', desc=True).limit(5).execute()
            recent_users_list = recent_response.data if recent_response.data else []
        except Exception as e:
            print(f"Error getting recent users: {str(e)}")
        
        stats = {
            'users_count': total_users,
            'files_count': total_files,
            'subscribers_count': subscribers_count,
            'feedback_count': feedback_count,
            'recent_users': recent_users_list
        }
        
    except Exception as e:
        print(f"Error loading admin stats: {str(e)}")
        stats = {
            'users_count': 0,
            'files_count': 0,
            'subscribers_count': 0,
            'feedback_count': 0,
            'recent_users': []
        }
    
    return render_template('admin/dashboard.html', **stats)

@admin_bp.route('/users')
@admin_required
def admin_users():
    """Admin user management page."""
    try:
        users = User.get_all_users()
    except Exception as e:
        print(f"Error loading users: {str(e)}")
        users = []
        flash('Error loading users', 'error')
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/feedback')
@admin_required
def admin_feedback():
    """Admin feedback management page."""
    try:
        feedback_list = Feedback.get_all()
    except Exception as e:
        print(f"Error loading feedback: {str(e)}")
        feedback_list = []
        flash('Error loading feedback', 'error')
    
    return render_template('admin/feedback.html', feedback=feedback_list)

@admin_bp.route('/newsletter')
@admin_required
def admin_newsletter():
    """Admin newsletter management page."""
    try:
        subscribers = NewsletterSubscription.get_all()
    except Exception as e:
        print(f"Error loading newsletter subscribers: {str(e)}")
        subscribers = []
        flash('Error loading newsletter subscribers', 'error')
    
    return render_template('admin/newsletter.html', subscribers=subscribers)

@admin_bp.route('/send-newsletter', methods=['GET', 'POST'])
@admin_required
def admin_send_newsletter():
    """Send newsletter to all subscribers."""
    if request.method == 'POST':
        subject = request.form.get('subject')
        content = request.form.get('content')
        
        if not subject or not content:
            flash('Subject and content are required', 'error')
            return render_template('admin/send_newsletter.html')
        
        try:
            result = EmailService.send_newsletter(subject, content)
            if result['success']:
                flash(f'Newsletter sent successfully to {result["sent_count"]} subscribers!', 'success')
            else:
                flash(f'Error sending newsletter: {result["error"]}', 'error')
        except Exception as e:
            flash(f'Error sending newsletter: {str(e)}', 'error')
        
        return redirect(url_for('admin.admin_newsletter'))
    
    return render_template('admin/send_newsletter.html')

@admin_bp.route('/content')
@admin_required
def admin_content():
    """Admin content management page."""
    return render_template('admin/content.html')

@admin_bp.route('/content/testimonials')
@admin_required
def admin_testimonials():
    """Admin testimonials management page."""
    try:
        testimonials = WebsiteContent.get_testimonials()
    except Exception as e:
        print(f"Error loading testimonials: {str(e)}")
        testimonials = []
        flash('Error loading testimonials', 'error')
    
    return render_template('admin/testimonials.html', testimonials=testimonials)

@admin_bp.route('/content/testimonials/add', methods=['POST'])
@admin_required
def admin_add_testimonial():
    """Add a new testimonial."""
    text = request.form.get('text')
    author_name = request.form.get('author_name')
    author_title = request.form.get('author_title')
    author_image = request.form.get('author_image')
    
    if not all([text, author_name, author_title]):
        flash('Text, author name, and author title are required', 'error')
        return redirect(url_for('admin.admin_testimonials'))
    
    try:
        success = WebsiteContent.add_testimonial(text, author_name, author_title, author_image)
        if success:
            flash('Testimonial added successfully!', 'success')
        else:
            flash('Error adding testimonial', 'error')
    except Exception as e:
        print(f"Error adding testimonial: {str(e)}")
        flash('Error adding testimonial', 'error')
    
    return redirect(url_for('admin.admin_testimonials'))

@admin_bp.route('/content/testimonials/edit/<testimonial_id>', methods=['POST'])
@admin_required
def admin_edit_testimonial(testimonial_id):
    """Edit an existing testimonial."""
    text = request.form.get('text')
    author_name = request.form.get('author_name')
    author_title = request.form.get('author_title')
    author_image = request.form.get('author_image')
    
    if not all([text, author_name, author_title]):
        flash('Text, author name, and author title are required', 'error')
        return redirect(url_for('admin.admin_testimonials'))
    
    try:
        success = WebsiteContent.update_testimonial(testimonial_id, text, author_name, author_title, author_image)
        if success:
            flash('Testimonial updated successfully!', 'success')
        else:
            flash('Error updating testimonial', 'error')
    except Exception as e:
        print(f"Error updating testimonial: {str(e)}")
        flash('Error updating testimonial', 'error')
    
    return redirect(url_for('admin.admin_testimonials'))

@admin_bp.route('/content/testimonials/delete/<testimonial_id>', methods=['POST'])
@admin_required
def admin_delete_testimonial(testimonial_id):
    """Delete a testimonial."""
    try:
        success = WebsiteContent.delete_testimonial(testimonial_id)
        if success:
            flash('Testimonial deleted successfully!', 'success')
        else:
            flash('Error deleting testimonial', 'error')
    except Exception as e:
        print(f"Error deleting testimonial: {str(e)}")
        flash('Error deleting testimonial', 'error')
    
    return redirect(url_for('admin.admin_testimonials'))

@admin_bp.route('/analytics')
@admin_required
def admin_analytics():
    """Admin analytics page."""
    try:
        supabase = get_supabase()
        
        # Get page view analytics
        analytics_response = supabase.table('page_views').select('*').execute()
        page_views = analytics_response.data if analytics_response.data else []
        
        # Process analytics data for charts
        analytics_data = {
            'total_page_views': len(page_views),
            'recent_activity': page_views[-10:] if page_views else []
        }
        
    except Exception as e:
        print(f"Error loading analytics: {str(e)}")
        analytics_data = {
            'total_page_views': 0,
            'recent_activity': []
        }
        flash('Error loading analytics data', 'error')
    
    return render_template('admin/analytics.html', analytics=analytics_data)

@admin_bp.route('/user/<user_id>')
@admin_required
def view_user(user_id):
    """View user details."""
    try:
        user = User.get_by_id(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Get user's file history
        file_history = User.get_file_history(user_id, limit=20)
        
        return jsonify({
            'success': True,
            'user': user,
            'file_history': file_history
        })
        
    except Exception as e:
        print(f"Error viewing user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error loading user details'
        }), 500

@admin_bp.route('/user/<user_id>/edit', methods=['POST'])
@admin_required
def edit_user(user_id):
    """Edit user details."""
    try:
        user = User.get_by_id(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Get form data
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        subscription_status = request.form.get('subscription_status', 'none')
        is_admin = bool(request.form.get('is_admin'))
        newsletter_opt_in = bool(request.form.get('newsletter_opt_in'))
        
        # Validation
        if not email:
            flash('Email is required', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Update user data
        supabase = get_supabase()
        update_data = {
            'full_name': full_name,
            'email': email,
            'subscription_status': subscription_status,
            'is_admin': is_admin,
            'newsletter_opt_in': newsletter_opt_in
        }
        
        result = supabase.table('users').update(update_data).eq('id', user_id).execute()
        
        if result.data:
            flash('User updated successfully!', 'success')
        else:
            flash('Error updating user', 'error')
            
    except Exception as e:
        print(f"Error editing user {user_id}: {str(e)}")
        flash('Error updating user', 'error')
    
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/user/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user."""
    try:
        user = User.get_by_id(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Prevent deleting admin users
        if user.get('is_admin', False):
            flash('Cannot delete admin users', 'error')
            return redirect(url_for('admin.admin_users'))
        
        supabase = get_supabase()
        
        # Delete user's file history first
        supabase.table('file_history').delete().eq('user_id', user_id).execute()
        
        # Delete user
        result = supabase.table('users').delete().eq('id', user_id).execute()
        
        if result.data:
            flash('User deleted successfully!', 'success')
        else:
            flash('Error deleting user', 'error')
            
    except Exception as e:
        print(f"Error deleting user {user_id}: {str(e)}")
        flash('Error deleting user', 'error')
    
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/user/<user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_user_admin(user_id):
    """Toggle user admin status."""
    try:
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        current_admin_status = user.get('is_admin', False)
        new_admin_status = not current_admin_status
        
        supabase = get_supabase()
        result = supabase.table('users').update({
            'is_admin': new_admin_status
        }).eq('id', user_id).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'is_admin': new_admin_status
            })
        else:
            return jsonify({'success': False, 'error': 'Update failed'}), 500
            
    except Exception as e:
        print(f"Error toggling admin status for user {user_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

# Additional admin routes will be added later 