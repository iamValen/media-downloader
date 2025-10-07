import os
from pathlib import Path

class Config:
    NETWORK_DOWNLOAD_PATH = os.environ.get('NETWORK_DOWNLOAD_PATH', '/home/vln/Desktop/test')
    TEMP_DOWNLOAD_PATH = os.environ.get('TEMP_DOWNLOAD_PATH', './downloads/temp')

    Path(NETWORK_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
    Path(TEMP_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
