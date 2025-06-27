# Flask app factory
from flask import Flask
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions here when ready
    
    # Register blueprints here when ready
    
    return app 