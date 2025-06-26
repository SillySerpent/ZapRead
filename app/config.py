# Configuration management
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') 