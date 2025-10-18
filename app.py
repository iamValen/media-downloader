from flask import Flask
from flask_cors import CORS
from config import Config, DevelopmentConfig
from routes.api import api_bp
from routes.web import web_bp


def create_app(config=None):
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    app.config.from_object(config or DevelopmentConfig)
    
    if not Config.validate_paths():
        print("WARNING: Failed to create download directories")
    
    CORS(app)
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)
    
    return app


if __name__ == "__main__":
    app = create_app()
    
    print("=" * 60)
    print("Media Downloader Server Starting...")
    print("=" * 60)
    print(f"Network path: {Config.NETWORK_DOWNLOAD_PATH}")
    print(f"Temp path: {Config.TEMP_DOWNLOAD_PATH}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)