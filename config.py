import os
from pathlib import Path


class Config:
    """Base configuration"""
    DEFAULT_DOWNLOAD_PATH = os.environ.get(
        'DEFAULT_DOWNLOAD_PATH', 
        str(Path.home() / 'Downloads' / 'media_downloader')
    )
    ALT_DOWNLOAD_PATH = os.environ.get(
        'ALT_DOWNLOAD_PATH', 
        str(Path.home() / 'Downloads' / 'media_downloader')
    )

    TASK_RETENTION_TIME = 60
    MAX_PLAYLIST_SIZE = 100
    DOWNLOAD_TIMEOUT = 3600
    
    ALLOWED_FORMATS = ['mp3', 'mp4']
    ALLOWED_LOCATIONS = ['default', 'alt']

    def validate_paths():
        """Create download directories if they don't exist"""
        try:
            Path(Config.DEFAULT_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
            Path(Config.ALT_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directories: {e}")
            return False


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False