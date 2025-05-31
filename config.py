import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
    FLASK_APP = os.environ.get('FLASK_APP', 'app.py')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Supabase configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Stripe configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID')
    
    # Upload folder for temporary file storage
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')


class DevelopmentConfig(Config):
    """Development config."""
    DEBUG = True


class ProductionConfig(Config):
    """Production config."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing config."""
    TESTING = True


# Map config name to config class
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

# Get config by name or default to development
def get_config(config_name=None):
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(config_name, DevelopmentConfig) 