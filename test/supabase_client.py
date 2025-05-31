import os
from supabase import create_client, Client
from flask import session, g
from config import get_config

config = get_config()

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
        g.supabase = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_KEY,
            options={
                'storage': FlaskSessionStorage(),
                'auto_refresh_token': True,
                'persist_session': True,
            }
        )
    return g.supabase


def close_supabase(e=None):
    """Remove supabase client from g object."""
    supabase = g.pop('supabase', None)
    if supabase is not None:
        # Any cleanup if needed
        pass 