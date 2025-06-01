from flask import request, session
from app.services.supabase_service import get_supabase
import datetime

def track_page_view():
    """Analytics middleware to track page views."""
    # Skip tracking for static files and certain endpoints
    if request.path.startswith('/static') or request.path == '/webhook' or request.path == '/favicon.ico':
        return
    
    # Get user ID if logged in
    user_id = session.get('user', {}).get('id', None)
    
    # Get metadata
    metadata = {
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string,
        'referrer': request.referrer,
        'method': request.method
    }
    
    # Track the page view
    try:
        Analytics.track_page_view(request.path, user_id, metadata)
    except Exception as e:
        # Don't fail the request if tracking fails
        print(f"Error tracking page view: {str(e)}")


class Analytics:
    """Analytics model for tracking page views and user behavior."""
    
    @staticmethod
    def track_page_view(page, user_id=None, metadata=None):
        """
        Track a page view.
        
        Args:
            page (str): The page that was viewed.
            user_id (str, optional): The user ID if logged in.
            metadata (dict, optional): Additional metadata.
            
        Returns:
            dict: The created analytics record.
        """
        supabase = get_supabase()
        
        analytics_data = {
            'page': page,
            'user_id': user_id,
            'metadata': metadata or {},
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        
        response = supabase.table('analytics').insert(analytics_data).execute()
        return response.data
    
    @staticmethod
    def get_page_views(days=30, page=None):
        """
        Get page view statistics.
        
        Args:
            days (int, optional): Number of days to look back. Defaults to 30.
            page (str, optional): Specific page to filter by.
            
        Returns:
            list: Page view statistics.
        """
        supabase = get_supabase()
        
        # Calculate date threshold
        cutoff_date = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()
        
        query = supabase.table('analytics').select('*').gte('timestamp', cutoff_date)
        
        if page:
            query = query.eq('page', page)
        
        response = query.order('timestamp', desc=True).execute()
        return response.data
    
    @staticmethod
    def get_daily_stats(days=30):
        """
        Get daily statistics for the dashboard.
        
        Args:
            days (int, optional): Number of days to look back. Defaults to 30.
            
        Returns:
            dict: Daily statistics.
        """
        supabase = get_supabase()
        
        # Calculate date threshold
        cutoff_date = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()
        
        # Get page views for the period
        response = supabase.table('analytics').select('*').gte('timestamp', cutoff_date).execute()
        page_views = response.data
        
        # Process the data to get daily counts
        daily_stats = {}
        for view in page_views:
            date = view['timestamp'][:10]  # Extract date part
            if date not in daily_stats:
                daily_stats[date] = {'views': 0, 'unique_users': set()}
            
            daily_stats[date]['views'] += 1
            if view.get('user_id'):
                daily_stats[date]['unique_users'].add(view['user_id'])
        
        # Convert sets to counts
        for date in daily_stats:
            daily_stats[date]['unique_users'] = len(daily_stats[date]['unique_users'])
        
        return daily_stats 