#!/usr/bin/env python3
"""
Run script for ZapRead Flask application.
"""
import argparse
from app import app
from config import get_config

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the ZapRead Flask application')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the application on')
    args = parser.parse_args()
    
    config = get_config()
    
    # Use the port from command line arguments
    print(f"Starting ZapRead on http://{args.host}:{args.port}")
    app.run(debug=config.DEBUG, host=args.host, port=args.port) 