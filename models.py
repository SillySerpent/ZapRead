from supabase_client import get_supabase
import datetime

class User:
    """User model for interacting with Supabase auth and user data."""
    
    @staticmethod
    def get_by_id(user_id):
        """
        Get a user by ID.
        
        Args:
            user_id (str): The user ID.
            
        Returns:
            dict: User data or None if not found.
        """
        supabase = get_supabase()
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        data = response.data
        
        if data and len(data) > 0:
            return data[0]
        return None
    
    @staticmethod
    def update_subscription(user_id, subscription_id):
        """
        Update a user's subscription ID.
        
        Args:
            user_id (str): The user ID.
            subscription_id (str): The Stripe subscription ID.
            
        Returns:
            dict: The updated user data.
        """
        supabase = get_supabase()
        response = supabase.table('users').update({
            'subscription_id': subscription_id,
            'subscription_status': 'active'
        }).eq('id', user_id).execute()
        
        return response.data

    @staticmethod
    def cancel_subscription(user_id):
        """
        Cancel a user's subscription.
        
        Args:
            user_id (str): The user ID.
            
        Returns:
            dict: The updated user data.
        """
        supabase = get_supabase()
        response = supabase.table('users').update({
            'subscription_status': 'canceled'
        }).eq('id', user_id).execute()
        
        return response.data

    @staticmethod
    def has_active_subscription(user_id):
        """
        Check if a user has an active subscription.
        
        Args:
            user_id (str): The user ID.
            
        Returns:
            bool: True if the user has an active subscription, False otherwise.
        """
        supabase = get_supabase()
        response = supabase.table('users').select('subscription_id, subscription_status').eq('id', user_id).execute()
        data = response.data
        
        if data and len(data) > 0:
            user_data = data[0]
            # In test mode, just having a subscription_id or status 'active' might be enough
            if (user_data.get('subscription_id') and user_data.get('subscription_status') == 'active') or \
               (user_data.get('subscription_status') == 'active'):
                return True
        return False

    @staticmethod
    def get_file_history(user_id, limit=10):
        """
        Get a user's file processing history.
        
        Args:
            user_id (str): The user ID.
            limit (int, optional): The maximum number of records to return. Defaults to 10.
            
        Returns:
            list: The user's file processing history.
        """
        supabase = get_supabase()
        response = supabase.table('file_history').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        
        return response.data
    
    @staticmethod
    def add_file_to_history(user_id, original_filename, file_type, processed_filename):
        """
        Add a file to a user's processing history.
        
        Args:
            user_id (str): The user ID.
            original_filename (str): The original filename.
            file_type (str): The file type.
            processed_filename (str): The processed filename.
            
        Returns:
            dict: The created history record.
        """
        supabase = get_supabase()
        response = supabase.table('file_history').insert({
            'user_id': user_id,
            'original_filename': original_filename,
            'file_type': file_type,
            'processed_filename': processed_filename
        }).execute()
        
        return response.data

    @staticmethod
    def get_daily_upload_count(user_id):
        """
        Get the number of uploads a user has made today.
        
        Args:
            user_id (str): The user ID.
            
        Returns:
            int: The number of uploads made today.
        """
        supabase = get_supabase()
        
        # Get current date in ISO format
        today = datetime.datetime.now().date().isoformat()
        
        # Query for uploads made today
        response = supabase.table('file_history').select('count', count='exact') \
            .eq('user_id', user_id) \
            .gte('created_at', f"{today}T00:00:00") \
            .lte('created_at', f"{today}T23:59:59") \
            .execute()
        
        # Return the count
        return response.count if hasattr(response, 'count') else 0
    
    @staticmethod
    def can_upload_more(user_id):
        """
        Check if a user can upload more files today.
        
        Args:
            user_id (str): The user ID.
            
        Returns:
            bool: True if the user can upload more files, False otherwise.
        """
        # If the user has an active subscription, they can always upload
        if User.has_active_subscription(user_id):
            return True
        
        # Otherwise, check the daily upload count
        daily_count = User.get_daily_upload_count(user_id)
        return daily_count < 5  # Allow up to 5 uploads per day for regular users 


class WebsiteContent:
    """Website content model for managing editable website content."""
    
    @staticmethod
    def get_content(section, key=None):
        """
        Get website content by section and optional key.
        
        Args:
            section (str): The section name (e.g., 'hero', 'testimonials', 'features').
            key (str, optional): Specific key within the section. Defaults to None.
            
        Returns:
            dict or list: The content data.
        """
        supabase = get_supabase()
        
        if key:
            # Get specific content by section and key
            response = supabase.table('website_content').select('*').eq('section', section).eq('key', key).execute()
        else:
            # Get all content for a section
            response = supabase.table('website_content').select('*').eq('section', section).execute()
        
        return response.data
    
    @staticmethod
    def update_content(section, key, content_data):
        """
        Update website content.
        
        Args:
            section (str): The section name.
            key (str): The content key.
            content_data (dict): The content data.
            
        Returns:
            dict: The updated content.
        """
        supabase = get_supabase()
        
        # First check if content exists
        response = supabase.table('website_content').select('id').eq('section', section).eq('key', key).execute()
        
        if response.data and len(response.data) > 0:
            # Update existing content
            content_id = response.data[0]['id']
            update_data = {
                'content': content_data,
                'updated_at': datetime.datetime.now().isoformat()
            }
            update_response = supabase.table('website_content').update(update_data).eq('id', content_id).execute()
            return update_response.data
        else:
            # Create new content
            insert_data = {
                'section': section,
                'key': key,
                'content': content_data,
                'created_at': datetime.datetime.now().isoformat(),
                'updated_at': datetime.datetime.now().isoformat()
            }
            insert_response = supabase.table('website_content').insert(insert_data).execute()
            return insert_response.data
    
    @staticmethod
    def delete_content(section, key):
        """
        Delete website content.
        
        Args:
            section (str): The section name.
            key (str): The content key.
            
        Returns:
            bool: True if deleted, False otherwise.
        """
        supabase = get_supabase()
        response = supabase.table('website_content').delete().eq('section', section).eq('key', key).execute()
        
        return len(response.data) > 0
    
    @staticmethod
    def get_testimonials():
        """
        Get all testimonials.
        
        Returns:
            list: List of testimonials.
        """
        return WebsiteContent.get_content('testimonials')
    
    @staticmethod
    def update_testimonial(testimonial_id, data):
        """
        Update a testimonial.
        
        Args:
            testimonial_id (str): The testimonial ID.
            data (dict): The testimonial data.
            
        Returns:
            dict: The updated testimonial.
        """
        return WebsiteContent.update_content('testimonials', testimonial_id, data)
    
    @staticmethod
    def add_testimonial(data):
        """
        Add a new testimonial.
        
        Args:
            data (dict): The testimonial data.
            
        Returns:
            dict: The created testimonial.
        """
        # Generate a unique ID for the testimonial
        testimonial_id = f"testimonial_{datetime.datetime.now().timestamp()}"
        return WebsiteContent.update_content('testimonials', testimonial_id, data)
    
    @staticmethod
    def delete_testimonial(testimonial_id):
        """
        Delete a testimonial.
        
        Args:
            testimonial_id (str): The testimonial ID.
            
        Returns:
            bool: True if deleted, False otherwise.
        """
        return WebsiteContent.delete_content('testimonials', testimonial_id)


class Analytics:
    """Analytics model for tracking and retrieving website analytics."""
    
    @staticmethod
    def track_page_view(page, user_id=None, metadata=None):
        """
        Track a page view.
        
        Args:
            page (str): The page path.
            user_id (str, optional): The user ID if logged in. Defaults to None.
            metadata (dict, optional): Additional metadata. Defaults to None.
            
        Returns:
            dict: The created page view record.
        """
        supabase = get_supabase()
        
        data = {
            'page': page,
            'user_id': user_id,
            'metadata': metadata or {},
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        response = supabase.table('page_views').insert(data).execute()
        return response.data
    
    @staticmethod
    def get_page_views(days=30, page=None):
        """
        Get page views for the specified period.
        
        Args:
            days (int, optional): The number of days to look back. Defaults to 30.
            page (str, optional): Filter by specific page. Defaults to None.
            
        Returns:
            list: Page view records.
        """
        supabase = get_supabase()
        
        # Calculate the date range
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Build the query
        query = supabase.table('page_views').select('*').gte('timestamp', start_date.isoformat())
        
        if page:
            query = query.eq('page', page)
        
        response = query.order('timestamp', desc=True).execute()
        return response.data
    
    @staticmethod
    def get_daily_stats(days=30):
        """
        Get daily statistics for the specified period.
        
        Args:
            days (int, optional): The number of days to look back. Defaults to 30.
            
        Returns:
            dict: Daily statistics.
        """
        # In a real implementation, this would query the database for aggregated statistics
        # For now, we'll return dummy data
        supabase = get_supabase()
        
        # This is a placeholder - in a real implementation, you would
        # use SQL to aggregate the data by day
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Get all views in the date range
        views = supabase.table('page_views').select('*')\
            .gte('timestamp', start_date.isoformat())\
            .lte('timestamp', end_date.isoformat())\
            .execute().data
        
        # Manually aggregate by day (this is inefficient but serves as a demonstration)
        daily_stats = {}
        for view in views:
            date = view['timestamp'].split('T')[0]  # Extract date part
            if date not in daily_stats:
                daily_stats[date] = {'count': 0, 'unique_users': set()}
            
            daily_stats[date]['count'] += 1
            if view['user_id']:
                daily_stats[date]['unique_users'].add(view['user_id'])
        
        # Convert sets to counts
        for date in daily_stats:
            daily_stats[date]['unique_users'] = len(daily_stats[date]['unique_users'])
        
        return daily_stats 