from app.services.supabase_service import get_supabase

class WebsiteContent:
    """Model for managing website content like testimonials."""
    
    @staticmethod
    def get_content(section, key=None):
        """
        Get content for a specific section.
        
        Args:
            section (str): The section name.
            key (str, optional): Specific key within the section.
            
        Returns:
            list: Content data.
        """
        supabase = get_supabase()
        
        query = supabase.table('website_content').select('*').eq('section', section)
        
        if key:
            query = query.eq('key', key)
        
        response = query.execute()
        return response.data
    
    @staticmethod
    def update_content(section, key, content_data):
        """
        Update content for a specific section and key.
        
        Args:
            section (str): The section name.
            key (str): The key within the section.
            content_data (dict): The content data to update.
            
        Returns:
            dict: The updated content.
        """
        supabase = get_supabase()
        
        # First check if the content exists
        existing = supabase.table('website_content').select('*').eq('section', section).eq('key', key).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing content
            response = supabase.table('website_content').update({
                'content': content_data
            }).eq('section', section).eq('key', key).execute()
        else:
            # Create new content
            response = supabase.table('website_content').insert({
                'section': section,
                'key': key,
                'content': content_data
            }).execute()
        
        return response.data
    
    @staticmethod
    def delete_content(section, key):
        """
        Delete content for a specific section and key.
        
        Args:
            section (str): The section name.
            key (str): The key within the section.
            
        Returns:
            dict: The deleted content.
        """
        supabase = get_supabase()
        response = supabase.table('website_content').delete().eq('section', section).eq('key', key).execute()
        return response.data
    
    @staticmethod
    def get_testimonials():
        """Get all testimonials."""
        try:
            supabase = get_supabase()
            response = supabase.table('website_content').select('*').eq('section', 'testimonials').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting testimonials: {str(e)}")
            return []
    
    @staticmethod
    def update_testimonial(testimonial_id, text, author_name, author_title, author_image=None):
        """
        Update a testimonial.
        
        Args:
            testimonial_id (str): The testimonial ID.
            text (str): The testimonial text.
            author_name (str): The author name.
            author_title (str): The author title.
            author_image (str, optional): The author image URL.
            
        Returns:
            dict: The updated testimonial.
        """
        supabase = get_supabase()
        
        testimonial_data = {
            'text': text,
            'author_name': author_name,
            'author_title': author_title
        }
        
        if author_image:
            testimonial_data['author_image'] = author_image
        
        response = supabase.table('website_content').update({
            'content': testimonial_data
        }).eq('id', testimonial_id).execute()
        
        return response.data
    
    @staticmethod
    def add_testimonial(text, author_name, author_title, author_image=None):
        """
        Add a new testimonial.
        
        Args:
            text (str): The testimonial text.
            author_name (str): The author name.
            author_title (str): The author title.
            author_image (str, optional): The author image URL.
            
        Returns:
            dict: The created testimonial.
        """
        supabase = get_supabase()
        
        testimonial_data = {
            'text': text,
            'author_name': author_name,
            'author_title': author_title
        }
        
        if author_image:
            testimonial_data['author_image'] = author_image
        
        response = supabase.table('website_content').insert({
            'section': 'testimonials',
            'key': f'testimonial_{len(WebsiteContent.get_testimonials()) + 1}',
            'content': testimonial_data
        }).execute()
        
        return response.data
    
    @staticmethod
    def delete_testimonial(testimonial_id):
        """
        Delete a testimonial.
        
        Args:
            testimonial_id (str): The testimonial ID.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            supabase = get_supabase()
            response = supabase.table('website_content').delete().eq('id', testimonial_id).execute()
            return response.data is not None
        except Exception as e:
            print(f"Error deleting testimonial: {str(e)}")
            return False

class Feedback:
    """Model for handling user feedback."""
    
    @staticmethod
    def get_all(limit=100, offset=0):
        """
        Get all feedback submissions with pagination.
        
        Args:
            limit (int): Maximum number of feedback entries to return.
            offset (int): Number of entries to skip.
            
        Returns:
            list: List of feedback data.
        """
        try:
            supabase = get_supabase()
            response = supabase.table('feedback').select('*').order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting feedback: {str(e)}")
            return []
    
    @staticmethod
    def create(feedback_type, message, email=None, user_id=None):
        """
        Create a new feedback entry.
        
        Args:
            feedback_type (str): The type of feedback (suggestion, bug, question, other).
            message (str): The feedback message.
            email (str, optional): The email address.
            user_id (str, optional): The user ID if authenticated.
            
        Returns:
            dict: The created feedback data.
        """
        try:
            supabase = get_supabase()
            feedback_data = {
                'feedback_type': feedback_type,
                'message': message
            }
            
            if email:
                feedback_data['email'] = email
                
            if user_id:
                feedback_data['user_id'] = user_id
            
            response = supabase.table('feedback').insert(feedback_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating feedback: {str(e)}")
            return None
    
    @staticmethod
    def get_by_type(feedback_type, limit=100):
        """
        Get feedback by type.
        
        Args:
            feedback_type (str): The feedback type to filter by.
            limit (int): Maximum number of entries to return.
            
        Returns:
            list: List of feedback data.
        """
        try:
            supabase = get_supabase()
            response = supabase.table('feedback').select('*').eq('feedback_type', feedback_type).order('created_at', desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting feedback by type: {str(e)}")
            return []
    
    @staticmethod
    def delete_feedback(feedback_id):
        """
        Delete a feedback entry.
        
        Args:
            feedback_id (str): The feedback ID.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            supabase = get_supabase()
            response = supabase.table('feedback').delete().eq('id', feedback_id).execute()
            return response.data is not None
        except Exception as e:
            print(f"Error deleting feedback: {str(e)}")
            return False

class NewsletterSubscription:
    """Model for handling newsletter subscriptions."""
    
    @staticmethod
    def get_all():
        """Get all newsletter subscribers."""
        try:
            supabase = get_supabase()
            response = supabase.table('newsletter_subscribers').select('*').eq('is_active', True).order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting newsletter subscriptions: {str(e)}")
            return []
    
    @staticmethod
    def subscribe(email, name=None):
        """Subscribe an email to the newsletter."""
        try:
            supabase = get_supabase()
            
            # Check if already subscribed
            existing = supabase.table('newsletter_subscribers').select('id').eq('email', email).eq('is_active', True).execute()
            if existing.data:
                return {'success': False, 'message': 'Email already subscribed'}
            
            subscription_data = {
                'email': email,
                'is_active': True
            }
            
            response = supabase.table('newsletter_subscribers').insert(subscription_data).execute()
            return {'success': True, 'data': response.data[0]} if response.data else {'success': False, 'message': 'Failed to subscribe'}
        except Exception as e:
            print(f"Error subscribing to newsletter: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def unsubscribe(email):
        """Unsubscribe an email from the newsletter."""
        try:
            supabase = get_supabase()
            response = supabase.table('newsletter_subscribers').update({'is_active': False}).eq('email', email).execute()
            return response.data is not None
        except Exception as e:
            print(f"Error unsubscribing from newsletter: {str(e)}")
            return False
    
    @staticmethod
    def get_active_count():
        """Get the count of active newsletter subscribers."""
        try:
            supabase = get_supabase()
            response = supabase.table('newsletter_subscribers').select('count', count='exact').eq('is_active', True).execute()
            return response.count if response.count else 0
        except Exception as e:
            print(f"Error getting active subscriber count: {str(e)}")
            return 0 