import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify, current_app
from werkzeug.utils import secure_filename
from app.auth.decorators import login_required, subscription_required
from app.auth.models import User
from app.core.models import WebsiteContent, Feedback
from app.services.supabase_service import get_supabase
from app.services.file_service import FileService
import app.bionic.processor as bionic_processor

core_bp = Blueprint('core', __name__)

@core_bp.route('/')
def index():
    """Homepage route with testimonials."""
    # Sample testimonials data (in production, this might come from a database)
    testimonials = [
        {
            'name': 'Sarah Johnson',
            'role': 'Graduate Student',
            'content': 'ZapRead has revolutionized how I process research papers. I can now read through academic articles 30% faster with better comprehension.',
            'rating': 5
        },
        {
            'name': 'Mike Chen',
            'role': 'Business Analyst',
            'content': 'The bionic reading format helps me get through reports much quicker. It\'s become an essential tool for my daily workflow.',
            'rating': 5
        },
        {
            'name': 'Dr. Emily Rodriguez',
            'role': 'Professor',
            'content': 'I recommend ZapRead to all my students. It particularly helps those with reading difficulties like dyslexia.',
            'rating': 5
        }
    ]
    
    return render_template('core/index.html', testimonials=testimonials)

@core_bp.route('/about')
def about():
    """About page route."""
    return render_template('core/about.html')

@core_bp.route('/pricing')
def pricing():
    """Pricing page route."""
    return render_template('core/pricing.html')

@core_bp.route('/privacy')
def privacy():
    """Privacy policy page route."""
    return render_template('core/privacy.html')

@core_bp.route('/terms')
def terms():
    """Terms of service page route."""
    return render_template('core/terms.html')

@core_bp.route('/contact')
def contact():
    """Contact page route."""
    return render_template('core/contact.html')

@core_bp.route('/features')
def features():
    """Features page route."""
    return render_template('core/features.html')

@core_bp.route('/help')
def help():
    """Help page route."""
    return render_template('core/help.html')

@core_bp.route('/dashboard')
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
    
    return render_template(
        'core/dashboard.html', 
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

@core_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """File upload route for authenticated users."""
    if request.method == 'POST':
        user_id = session['user']['id']
        
        # Check if user can upload more files
        if not User.can_upload_more(user_id):
            flash('You have reached your daily upload limit. Please upgrade to premium for unlimited uploads.', 'error')
            return redirect(url_for('subscription.subscription'))
        
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file:
            # Extract processing options from form
            processing_options = {
                'intensity': float(request.form.get('intensity', 40)) / 100.0,  # Convert percentage to decimal
                'reading_profile': request.form.get('reading_profile', 'standard'),
                'output_format': request.form.get('output_format', 'html'),
                'processing_strategy': request.form.get('processing_strategy', 'balanced'),
                'preserve_formatting': request.form.get('preserve_formatting') == 'on',
                'skip_technical': request.form.get('skip_technical') == 'on'
            }
            
            # Use FileService for complete workflow with processing options
            result = FileService.handle_file_upload_and_process(
                file, user_id, add_to_history=True, processing_options=processing_options
            )
            
            if result['success']:
                flash('File processed successfully!', 'success')
                # Store result in session for the result page
                session['processing_result'] = result
                return redirect(url_for('core.result'))
            else:
                flash(f'Error processing file: {result["error"]}', 'error')
                return redirect(request.url)
    
    return render_template('core/upload.html')

@core_bp.route('/guest-upload', methods=['GET', 'POST'])
def guest_upload():
    """Guest file upload route."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file:
            # Get processing options from form
            processing_options = {
                'bionic_intensity': float(request.form.get('bionic_intensity', 0.4)),
                'output_format': request.form.get('output_format', 'html'),
                'processing_strategy': request.form.get('processing_strategy', 'balanced'),
                'preserve_formatting': request.form.get('preserve_formatting') == 'on',
                'skip_technical': request.form.get('skip_technical') == 'on'
            }
            
            # Use FileService for complete workflow with processing options
            result = FileService.handle_file_upload_and_process(
                file, user_id=None, add_to_history=False, processing_options=processing_options
            )
            
            if result['success']:
                flash('File processed successfully!', 'success')
                # Store result in session for the result page
                session['processing_result'] = result
                return redirect(url_for('core.result'))
            else:
                flash(f'Error processing file: {result["error"]}', 'error')
                return redirect(request.url)
    
    return render_template('core/guest_upload.html')

@core_bp.route('/result')
def result():
    """Display processing result with preview and download options."""
    # Get result from session
    result = session.pop('processing_result', None)
    if not result:
        flash('No processing result found. Please upload a file first.', 'error')
        if session.get('user'):
            return redirect(url_for('core.upload_file'))
        else:
            return redirect(url_for('core.guest_upload'))
    
    # Create download URL
    download_url = url_for('core.download_file', 
                          filename=os.path.basename(result['output_path']),
                          original_name=result['original_filename'])
    
    return render_template('core/result.html',
                         original_filename=result['original_filename'],
                         file_type=result.get('file_type', 'unknown'),
                         processed_filename=result.get('processed_filename', os.path.basename(result['output_path'])),
                         method_used=result.get('method_used', 'Standard'),
                         processing_time=result.get('processing_time', 0),
                         processor_metadata=result.get('processor_metadata', {}),
                         download_url=download_url)

@core_bp.route('/download/<filename>')
def download_file(filename):
    """Serve processed files for download and preview."""
    original_name = request.args.get('original_name', filename)
    
    # Try to find the file in temp directories
    import tempfile
    import glob
    
    # Search for the file in temporary directories
    temp_pattern = os.path.join(tempfile.gettempdir(), '*', filename)
    matching_files = glob.glob(temp_pattern)
    
    if not matching_files:
        # Also check the configured UPLOAD_FOLDER (now absolute) for fallback
        uploads_root = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        # Ensure we are working with an absolute path – Config.init_app already guarantees this,
        # but we enforce it defensively in case of mis-configuration.
        if not os.path.isabs(uploads_root):
            uploads_root = os.path.abspath(uploads_root)

        uploads_pattern = os.path.join(uploads_root, '**', filename)
        matching_files = glob.glob(uploads_pattern, recursive=True)
    
    if matching_files:
        file_path = matching_files[0]  # Use the first match
        
        # Determine appropriate download name
        if original_name and original_name != filename:
            base_name, _ = os.path.splitext(original_name)
            file_ext = os.path.splitext(filename)[1]
            download_name = f"bionic_{base_name}{file_ext}"
        else:
            download_name = filename
            
        return send_file(file_path, 
                        as_attachment=False,  # Don't force download for preview
                        download_name=download_name)
    else:
        flash('File not found or has expired.', 'error')
        return redirect(url_for('core.index'))

@core_bp.route('/faq')
def faq():
    """FAQ page route."""
    return render_template('core/faq.html')

@core_bp.route('/feedback')
def feedback():
    """Feedback page route."""
    return render_template('core/feedback.html')

@core_bp.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback form."""
    try:
        # Get form data
        feedback_type = request.form.get('feedback_type', 'other').strip()
        message = request.form.get('message', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validation
        if not message:
            flash('Message is required', 'error')
            return redirect(url_for('core.feedback'))
        
        if not feedback_type:
            feedback_type = 'other'
        
        # Get user ID if logged in
        user_id = None
        if 'user' in session and 'id' in session['user']:
            user_id = session['user']['id']
        
        # Create feedback entry
        feedback_data = {
            'feedback_type': feedback_type,
            'message': message
        }
        
        if email:
            feedback_data['email'] = email
            
        if user_id:
            feedback_data['user_id'] = user_id
        
        # Use direct Supabase insert for better error handling
        supabase = get_supabase()
        result = supabase.table('feedback').insert(feedback_data).execute()
        
        if result.data:
            flash('Thank you for your feedback! We will review it soon.', 'success')
        else:
            flash('Error submitting feedback. Please try again.', 'error')
            
    except Exception as e:
        print(f"Error submitting feedback: {str(e)}")
        flash('Error submitting feedback. Please try again.', 'error')
    
    # Use explicit redirect with 303 status to force GET request
    response = redirect(url_for('core.feedback'), code=303)
    return response

@core_bp.route('/subscribe-newsletter', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter."""
    try:
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Email is required', 'error')
            return redirect(url_for('core.index'))
        
        # Store newsletter subscription
        supabase = get_supabase()
        newsletter_data = {
            'email': email,
            'subscribed': True,
            'created_at': 'now()'
        }
        
        response = supabase.table('newsletter_subscribers').insert(newsletter_data).execute()
        
        if response.data:
            flash('Thank you for subscribing to our newsletter!', 'success')
        else:
            flash('Error subscribing to newsletter. Please try again.', 'error')
            
    except Exception as e:
        print(f"Error subscribing to newsletter: {str(e)}")
        flash('Error subscribing to newsletter. Please try again.', 'error')
    
    return redirect(url_for('core.index'))

@core_bp.route('/register-prompt')
def register_prompt():
    """Registration prompt page for guest users."""
    return render_template('core/register_prompt.html')

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('shared/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('shared/500.html'), 500 