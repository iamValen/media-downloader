import os
import uuid
import threading
import yt_dlp
from datetime import datetime
from .utils import progress_hook, cleanup_task, is_valid_file_size
from .validators import ValidationError
from config import Config

download_tasks = {}

class DownloadProgress:
    """Track download progress and metadata"""
    def __init__(self, task_id):
        self.task_id = task_id
        self.status = 'pending'  # pending, downloading, processing, completed, error
        self.progress = 0
        self.filename = None
        self.error = None
        self.total_size = None
        self.downloaded_size = None
        self.speed = None
        self.eta = None
        self.filepath = None
        self.created_at = datetime.now().isoformat()
        self.failed_items = []
        self.success_count = 0

        self.playlist_total = 0
        self.playlist_index = 0
        self.playlist_title = None
    
    def to_dict(self):
        return self.__dict__


def download_media(url, format_type, quality, download_location, task_id):
    """Execute download with comprehensive error handling"""
    task = download_tasks.get(task_id)
    if not task:
        return
    
    try:
        output_path = (
            Config.NETWORK_DOWNLOAD_PATH 
            if download_location == 'network' 
            else Config.TEMP_DOWNLOAD_PATH
        )
        
        os.makedirs(output_path, exist_ok=True)
        
        ydl_opts = {
            'progress_hooks': [
                lambda d: progress_hook(d, task_id, download_tasks)
            ],
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 30,
            'ignoreerrors': True,  # Continue on errors for playlists
            'skip_unavailable_fragments': True,
            'fragment_retries': 3,
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
        elif format_type == 'mp4':
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best' 
                if quality == 'best' 
                else f'bestvideo[height<={quality}]+bestaudio/best',
            })
        
        task.status = 'downloading'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Detect if it's a playlist
            if 'entries' in info and info['entries']:
                entries = [e for e in info['entries'] if e]
                task.playlist_total = len(entries)
                task.playlist_title = info.get('title', 'Unknown Playlist')

                for idx, entry in enumerate(entries, start=1):
                    task.playlist_index = idx
                    try:
                        ydl.process_ie_result(entry, download=True)
                        task.success_count += 1
                    except Exception as e:
                        print(f"Failed to download item {idx}: {e}")
                        task.failed_items.append(str(e))
            else:
                # Single video
                info = ydl.process_ie_result(info, download=True)
                task.playlist_total = 1
                task.playlist_index = 1
                task.success_count = 1

        
        if not info:
            raise ValueError("Failed to retrieve media information")
        
        if 'entries' in info:
            # Playlist handling
            entries = info['entries']
            successful = [e for e in entries if e]
            failed = len(entries) - len(successful)
            
            task.success_count = len(successful)
            task.failed_items = failed
            
            if failed > 0:
                task.filename = (
                    f"Playlist: {info.get('title', 'Unknown')} "
                    f"({len(successful)} items) - {failed} failed"
                )
            else:
                task.filename = (
                    f"Playlist: {info.get('title', 'Unknown')} "
                    f"({len(successful)} items)"
                )
        else:
            # Single item
            task.filename = info.get('title', 'Unknown')
        
        task.status = 'completed'
        task.progress = 100
        cleanup_task(task_id, download_tasks, Config.TASK_RETENTION_TIME)
    
    except Exception as e:
        task.status = 'error'
        task.error = str(e)
        print(f"Download error for task {task_id}: {e}")
        cleanup_task(task_id, download_tasks, Config.TASK_RETENTION_TIME)

def start_download(url, format_type='mp3', quality='192', location='network'):
    """Start download in background thread with validation"""
    try:
        from .validators import (
            validate_url, validate_format, validate_quality, validate_location
        )
        
        url = validate_url(url)
        format_type = validate_format(format_type, Config.ALLOWED_FORMATS)
        quality = validate_quality(quality, format_type)
        location = validate_location(location, Config.ALLOWED_LOCATIONS)
        
    except ValidationError as e:
        task_id = str(uuid.uuid4())
        error_task = DownloadProgress(task_id)
        error_task.status = 'error'
        error_task.error = str(e)
        download_tasks[task_id] = error_task
        return task_id
    
    task_id = str(uuid.uuid4())
    task = DownloadProgress(task_id)
    download_tasks[task_id] = task
    
    thread = threading.Thread(
        target=download_media,
        args=(url, format_type, quality, location, task_id),
        daemon=True,
        name=f"download-{task_id[:8]}"
    )
    thread.start()
    
    return task_id
