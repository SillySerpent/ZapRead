"""
Main Application Entry Point

This module serves as the entry point for the Flask application.
It creates the app instance using the application factory pattern.
"""

import os
import sys
import socket

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config.config import config

def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

# Get configuration environment from environment variable
config_name = os.environ.get('FLASK_CONFIG') or 'default'
app = create_app(config[config_name])

if __name__ == '__main__':
    # Initialize application configuration
    app.config['UPLOAD_FOLDER'] = app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Get port from command line arguments or find available port
    port = 5000
    if len(sys.argv) > 1 and sys.argv[1] == '--port' and len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("Invalid port number, using default port 5000")
            port = 5000
    
    # Check if the port is available, if not find an alternative
    if is_port_in_use(port):
        if port == 5000:
            print(f"Port {port} is in use (likely by macOS AirPlay Receiver).")
            print("Tip: You can disable AirPlay Receiver in System Preferences > Sharing")
        else:
            print(f"Port {port} is in use.")
        
        alternative_port = find_available_port(port)
        if alternative_port:
            port = alternative_port
            print(f"Using alternative port: {port}")
        else:
            print("Could not find an available port. Please specify a different port with --port")
            sys.exit(1)
    
    # Run the application
    debug_mode = app.config.get('DEBUG', False)
    print(f"Starting ZapRead on http://localhost:{port}")
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 