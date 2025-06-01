import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, session
from app.bionic.processor import process_file
from app.auth.models import User

class FileService:
    """Service for handling file operations including upload and processing."""
    
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
    
    @classmethod
    def allowed_file(cls, filename):
        """Check if a file has an allowed extension."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def secure_filename_with_extension(cls, filename):
        """Create a secure filename while preserving the original extension."""
        if not filename:
            return None
        
        # Get the file extension
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            ext = ext.lower()
        else:
            name = filename
            ext = ''
        
        # Create a secure version of the name
        secure_name = secure_filename(name)
        
        # If secure_filename strips everything, use a default
        if not secure_name:
            secure_name = 'file'
        
        # Add a UUID to ensure uniqueness
        unique_name = f"{secure_name}_{uuid.uuid4().hex[:8]}"
        
        # Add back the extension
        if ext:
            return f"{unique_name}.{ext}"
        else:
            return unique_name
    
    @classmethod
    def save_uploaded_file(cls, file, user_id=None):
        """
        Save an uploaded file and return the file path.
        
        Args:
            file: Flask uploaded file object
            user_id: Optional user ID for organizing files
            
        Returns:
            dict: Result containing success status and file info
        """
        if not file or not file.filename:
            return {
                'success': False,
                'error': 'No file provided'
            }
        
        if not cls.allowed_file(file.filename):
            return {
                'success': False,
                'error': 'File type not allowed. Please upload a TXT, PDF, or DOCX file.'
            }
        
        try:
            # Generate secure filename
            secure_name = cls.secure_filename_with_extension(file.filename)
            
            # Create user-specific directory if user_id provided
            if user_id:
                user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
                os.makedirs(user_dir, exist_ok=True)
                file_path = os.path.join(user_dir, secure_name)
            else:
                # Guest uploads go to a general guest directory
                guest_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'guest')
                os.makedirs(guest_dir, exist_ok=True)
                file_path = os.path.join(guest_dir, secure_name)
            
            # Save the file
            file.save(file_path)
            
            return {
                'success': True,
                'file_path': file_path,
                'original_filename': file.filename,
                'secure_filename': secure_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error saving file: {str(e)}'
            }
    
    @classmethod
    def process_bionic_file(cls, file_path, original_filename):
        """
        Process a file for bionic reading.
        
        Args:
            file_path: Path to the uploaded file
            original_filename: Original filename for display
            
        Returns:
            dict: Processing result with success status and output path
        """
        try:
            result = process_file(file_path)
            
            if result.get('success'):
                return {
                    'success': True,
                    'output_path': result['output_path'],
                    'file_type': result['file_type'],
                    'original_filename': original_filename
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Processing failed'),
                    'file_type': result.get('file_type', 'unknown')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Processing error: {str(e)}',
                'file_type': 'unknown'
            }
    
    @classmethod
    def handle_file_upload_and_process(cls, file, user_id=None, add_to_history=True):
        """
        Complete file upload and processing workflow.
        
        Args:
            file: Flask uploaded file object
            user_id: Optional user ID
            add_to_history: Whether to add to user's file history
            
        Returns:
            dict: Complete processing result
        """
        # Save the uploaded file
        save_result = cls.save_uploaded_file(file, user_id)
        if not save_result['success']:
            return save_result
        
        file_path = save_result['file_path']
        original_filename = save_result['original_filename']
        
        try:
            # Process the file for bionic reading
            process_result = cls.process_bionic_file(file_path, original_filename)
            
            if process_result['success']:
                # Add to user history if requested and user is logged in
                if add_to_history and user_id:
                    try:
                        User.add_file_to_history(
                            user_id,
                            original_filename,
                            process_result['file_type'],
                            os.path.basename(process_result['output_path'])
                        )
                    except Exception as e:
                        print(f"Error adding file to history: {str(e)}")
                        # Don't fail the whole process if history fails
                
                # Store in session for guest users
                if not user_id:
                    session['guest_processed_file'] = {
                        'original_filename': original_filename,
                        'file_type': process_result['file_type'],
                        'processed_filename': os.path.basename(process_result['output_path']),
                        'output_path': process_result['output_path']
                    }
                
                return {
                    'success': True,
                    'output_path': process_result['output_path'],
                    'file_type': process_result['file_type'],
                    'original_filename': original_filename,
                    'processed_filename': os.path.basename(process_result['output_path'])
                }
            else:
                return process_result
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Processing failed: {str(e)}'
            }
        finally:
            # Clean up the uploaded file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error cleaning up uploaded file: {str(e)}")
    
    @classmethod
    def get_file_extension(cls, filename):
        """Get the file extension from a filename."""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ''
    
    @classmethod
    def is_supported_file_type(cls, filename):
        """Check if a file type is supported for bionic processing."""
        ext = cls.get_file_extension(filename)
        return ext in {'txt', 'pdf', 'docx', 'doc'} 