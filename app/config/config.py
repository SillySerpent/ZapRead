"""
Application Configuration

This module contains configuration classes for the Flask application.
It loads environment variables and configures the app for different environments.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Upload Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Supabase Configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Stripe Configuration
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Price IDs for different subscription tiers
    STRIPE_PRICE_ID_MONTHLY = os.environ.get('STRIPE_PRICE_ID_MONTHLY')
    STRIPE_PRICE_ID_YEARLY = os.environ.get('STRIPE_PRICE_ID_YEARLY')
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Debug Configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'on']
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Ensure UPLOAD_FOLDER is an absolute path. If it is a relative path, make it
        # relative to the project root (the parent directory of the Flask package).
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')

        # Convert to absolute path if necessary
        if not os.path.isabs(upload_folder):
            # The application root (app.root_path) points to the `app/` package directory.
            # We want uploads to reside alongside the package, i.e. project root.
            from pathlib import Path
            project_root = Path(app.root_path).parent
            upload_folder = str(project_root / upload_folder)

        # Update the configuration so the rest of the app always sees an absolute path
        app.config['UPLOAD_FOLDER'] = upload_folder

        # Finally, make sure the directory actually exists
        os.makedirs(upload_folder, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 