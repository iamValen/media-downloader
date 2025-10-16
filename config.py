import os
from pathlib import Path

class Config:
    NETWORK_DOWNLOAD_PATH = os.environ.get(
        'NETWORK_DOWNLOAD_PATH', 
        str(Path.home() / 'Downloads' / 'media_downloader')
    )
    TEMP_DOWNLOAD_PATH = os.environ.get(
        'TEMP_DOWNLOAD_PATH', 
        str(Path.home() / '.cache' / 'media_downloader')
    )
    
    TASK_RETENTION_TIME = 60
    
    MAX_PLAYLIST_SIZE = 100
    DOWNLOAD_TIMEOUT = 3600
    
    ALLOWED_FORMATS = ['mp3', 'mp4']
    ALLOWED_LOCATIONS = ['network', 'temp']
    
    @classmethod
    def validate_paths(cls):
        try:
            Path(cls.NETWORK_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
            Path(cls.TEMP_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directories: {e}")
            return False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False