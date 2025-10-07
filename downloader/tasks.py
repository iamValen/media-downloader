import os
import uuid
import threading
import yt_dlp
from .utils import progress_hook
from config import Config

download_tasks = {}

class DownloadProgress:
    def __init__(self, task_id):
        self.task_id = task_id
        self.status = 'pending'
        self.progress = 0
        self.filename = None
        self.error = None
        self.total_size = None
        self.downloaded_size = None
        self.speed = None
        self.eta = None
        self.filepath = None

    def to_dict(self):
        return self.__dict__

def download_media(url, format_type, quality, download_location, task_id):
    task = download_tasks[task_id]

    try:
        output_path = Config.NETWORK_DOWNLOAD_PATH if download_location == 'network' else Config.TEMP_DOWNLOAD_PATH

        # yt-dlp config
        ydl_opts = {
            'progress_hooks': [lambda d: progress_hook(d, task_id, download_tasks)],
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }

        if format_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
            })
        else:  # mp4
            if quality == 'best':
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            else:
                ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info:
                task.filename = f"Playlist: {info.get('title', 'Unknown')} ({len(info['entries'])} items)"
            else:
                task.filename = info.get('title', 'Unknown')
            task.status = 'completed'
            task.progress = 100

    except Exception as e:
        task.status = 'error'
        task.error = str(e)
        print(f"Download error: {e}")

def start_download(url, format_type='mp3', quality='192', location='network'):
    task_id = str(uuid.uuid4())
    task = DownloadProgress(task_id)
    download_tasks[task_id] = task

    thread = threading.Thread(
        target=download_media,
        args=(url, format_type, quality, location, task_id)
    )
    thread.daemon = True
    thread.start()

    return task_id
