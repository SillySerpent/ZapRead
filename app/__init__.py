"""
Flask Application Factory

This module creates and configures the Flask application instance.
It registers all blueprints and configures the application for production use.
"""

import os
from flask import Flask
from app.config.config import Config
from app.auth.routes import auth_bp
from app.core.routes import core_bp
from app.admin.routes import admin_bp
from app.subscription.routes import subscription_bp

def create_app(config_class=Config):
    """
    Application factory function to create and configure Flask app.
    
    Args:
        config_class: Configuration class to use for the app
        
    Returns:
        Flask app instance
    """
    # Get the path to the app templates and static directories
    app_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(app_dir, 'templates')
    static_dir = os.path.join(app_dir, 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # Load configuration values
    app.config.from_object(config_class)

    # Give the Config class a chance to perform any runtime initialization (e.g.,
    # converting relative paths to absolute ones).
    if hasattr(config_class, 'init_app') and callable(getattr(config_class, 'init_app')):
        config_class.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(subscription_bp, url_prefix='/subscription')

    return app 