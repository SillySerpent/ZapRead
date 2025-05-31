from supabase_client import get_supabase

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
            'subscription_id': subscription_id
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
        response = supabase.table('users').select('subscription_id').eq('id', user_id).execute()
        data = response.data
        
        if data and len(data) > 0 and data[0].get('subscription_id'):
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