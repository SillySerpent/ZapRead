"""
Flask Application Factory

This module creates and configures the Flask application instance.
It registers all blueprints and configures the application for production use.
"""

import os
from flask import Flask
from config.config import Config
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
    # Get the path to the root templates and static directories
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(root_dir, 'templates')
    static_dir = os.path.join(root_dir, 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(subscription_bp, url_prefix='/subscription')

    return app 