# Development server
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    app.run(debug=debug_mode, host='0.0.0.0', port=5000) 