import os
from supabase import create_client, Client
from flask import session, g, current_app

class FlaskSessionStorage:
    """Storage adapter for Supabase that uses Flask session."""
    
    def __init__(self):
        self.storage = session
    
    def get_item(self, key):
        return self.storage.get(key)
    
    def set_item(self, key, value):
        self.storage[key] = value
    
    def remove_item(self, key):
        if key in self.storage:
            del self.storage[key]


def get_supabase() -> Client:
    """
    Get or create a Supabase client.
    
    Returns:
        Client: The Supabase client.
    """
    if 'supabase' not in g:
        # Check if SUPABASE_URL and SUPABASE_KEY are set
        if not current_app.config['SUPABASE_URL'] or not current_app.config['SUPABASE_KEY']:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        # Create client with options properly formatted for version 2.1.0
        g.supabase = create_client(
            current_app.config['SUPABASE_URL'],
            current_app.config['SUPABASE_KEY']
        )
    return g.supabase


def close_supabase(e=None):
    """Remove supabase client from g object."""
    supabase = g.pop('supabase', None)
    if supabase is not None:
        # Any cleanup if needed
        pass 