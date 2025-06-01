from app.services.supabase_service import get_supabase
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
    def is_admin(user_id):
        """
        Check if a user has admin privileges.
        
        Args:
            user_id (str): The user ID.
            
        Returns:
            bool: True if the user is an admin, False otherwise.
        """
        try:
            supabase = get_supabase()
            # Check if user exists in the users table with is_admin flag
            response = supabase.table('users').select('is_admin').eq('id', user_id).execute()
            data = response.data
            
            if data and len(data) > 0:
                return data[0].get('is_admin', False)
            
            # If user not found in users table, check auth.users metadata
            auth_response = supabase.table('auth.users').select('raw_user_meta_data').eq('id', user_id).execute()
            auth_data = auth_response.data
            
            if auth_data and len(auth_data) > 0:
                metadata = auth_data[0].get('raw_user_meta_data', {})
                return metadata.get('is_admin', False)
            
            return False
            
        except Exception as e:
            print(f"Error checking admin status for user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_all_users(limit=100, offset=0):
        """
        Get all users with pagination.
        
        Args:
            limit (int): Maximum number of users to return.
            offset (int): Number of users to skip.
            
        Returns:
            list: List of user data.
        """
        try:
            supabase = get_supabase()
            # Get users from users table only (which has the necessary data)
            response = supabase.table('users').select('*').range(offset, offset + limit - 1).order('created_at', desc=True).execute()
            
            users = response.data if response.data else []
            
            # Format the data to match expected structure
            formatted_users = []
            for user in users:
                formatted_user = {
                    'id': user.get('id'),
                    'email': user.get('email'),
                    'created_at': user.get('created_at'),
                    'subscription_status': user.get('subscription_status', 'none'),
                    'subscription_id': user.get('subscription_id'),
                    'is_admin': user.get('is_admin', False),
                    'full_name': user.get('full_name', ''),
                    'newsletter_opt_in': user.get('newsletter_opt_in', True)
                }
                formatted_users.append(formatted_user)
            
            return formatted_users
            
        except Exception as e:
            print(f"Error getting all users: {str(e)}")
            return []
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """
        Update user profile data.
        
        Args:
            user_id (str): The user ID.
            profile_data (dict): The profile data to update.
            
        Returns:
            dict: The updated user data.
        """
        supabase = get_supabase()
        response = supabase.table('users').update(profile_data).eq('id', user_id).execute()
        return response.data
    
    @staticmethod
    def update_notification_preferences(user_id, preferences):
        """
        Update user notification preferences.
        
        Args:
            user_id (str): The user ID.
            preferences (dict): The notification preferences.
            
        Returns:
            dict: The updated user data.
        """
        supabase = get_supabase()
        response = supabase.table('users').update({
            'notification_preferences': preferences
        }).eq('id', user_id).execute()
        return response.data
    
    @staticmethod
    def update_newsletter_preference(user_id, opt_in):
        """
        Update user newsletter opt-in preference.
        
        Args:
            user_id (str): The user ID.
            opt_in (bool): Whether the user opts in to the newsletter.
            
        Returns:
            dict: The updated user data.
        """
        supabase = get_supabase()
        response = supabase.table('users').update({
            'newsletter_opt_in': opt_in
        }).eq('id', user_id).execute()
        return response.data
    
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
        
        return response.count if response.count else 0
    
    @staticmethod
    def can_upload_more(user_id):
        """
        Check if a user can upload more files today.
        
        Args:
            user_id (str): The user ID.
            
        Returns:
            bool: True if the user can upload more files, False otherwise.
        """
        # Check if user has an active subscription
        if User.has_active_subscription(user_id):
            return True  # Unlimited uploads for subscribers
        
        # For free users, limit to 3 uploads per day
        daily_count = User.get_daily_upload_count(user_id)
        return daily_count < 3 