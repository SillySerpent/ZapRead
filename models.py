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