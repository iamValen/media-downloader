import os
import uuid
import threading
import requests
import yt_dlp
from datetime import datetime
from typing import Optional, Dict, Any, List
from .utils import progress_hook, cleanup_task, apply_metadata
from config import Config

download_tasks: Dict[str, "DownloadProgress"] = {}


class DownloadProgress:
    def __init__(self, task_id: str) -> None:
        self.task_id: str = task_id
        self.status: str = 'pending'
        self.progress: float = 0.0
        self.filename: Optional[str] = None
        self.error: Optional[str] = None
        self.total_size: Optional[int] = None
        self.downloaded_size: Optional[int] = None
        self.speed: Optional[float] = None
        self.eta: Optional[float] = None
        self.filepath: Optional[str] = None
        self.created_at: str = datetime.now().isoformat()
        self.failed_items: List[str] = []
        self.success_count: int = 0
        self.playlist_total: int = 0
        self.playlist_index: int = 0
        self.playlist_title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


def _sanitize_name(name: Optional[str]) -> str:
    """Make filesystem-safe filenames"""
    if not name:
        return "Unknown"
    return "".join(c for c in name if c.isalnum() or c in " .-_").strip()


def download_media(url: str, format_type: str, quality: Optional[str], download_location: str, task_id: str, is_album: bool) -> None:
    task: Optional[DownloadProgress] = download_tasks.get(task_id)
    if not task:
        return

    try:
        output_path: str = (
            Config.DEFAULT_DOWNLOAD_PATH
            if download_location == 'default'
            else Config.ALT_DOWNLOAD_PATH
        )
        os.makedirs(output_path, exist_ok=True)

        base_opts: Dict[str, Any] = {
            'progress_hooks': [lambda d: progress_hook(d, task_id, download_tasks)],
            'quiet': False,
            'ignoreerrors': True,
            'socket_timeout': 30,
            'skip_unavailable_fragments': True,
            'fragment_retries': 3,
        }

        if format_type == 'mp3':
            base_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality or '192',
                }],
            })
        else:
            base_opts.update({
                'format': f"bestvideo[height<={quality}]+bestaudio/best"
                if quality not in ('best', None)
                else "bestvideo+bestaudio/best",
            })

        with yt_dlp.YoutubeDL(base_opts) as ydl:
            info: Dict[str, Any] = ydl.extract_info(url, download=False)
        # choose single or playlist
        entries: List[Dict[str, Any]] = info.get('entries') or [info]
        task.playlist_total = len(entries)
        task.playlist_index = 0
        playlist_title: Optional[str] = (
            info.get('title', 'Unknown Playlist') if len(entries) > 1 else None
        )
        task.playlist_title = playlist_title

        for idx, entry in enumerate(entries, start=1):
            task.playlist_index = idx
            try:
                # Extract metadata
                title: str = entry.get('track') or entry.get('title') or f"Track {idx}"
                artist: str = entry.get('artist') or entry.get('uploader') or "Unknown Artist"
                album: str = playlist_title if is_album and playlist_title else "Single"

                # Create folders
                artist_folder: str = os.path.join(output_path, _sanitize_name(artist))
                album_folder: str = os.path.join(artist_folder, _sanitize_name(album))
                os.makedirs(album_folder, exist_ok=True)


                entry_opts: Dict[str, Any] = base_opts.copy()
                ext: str = 'mp3' if format_type == 'mp3' else 'mp4'
                entry_opts['outtmpl'] = os.path.join(album_folder, f"{_sanitize_name(title)}.%(ext)s")

                with yt_dlp.YoutubeDL(entry_opts) as entry_ydl:
                    entry_ydl.download([entry.get('webpage_url') or url])

                # Apply metadata
                final_file: str = os.path.join(album_folder, f"{_sanitize_name(title)}.{ext}")
                if os.path.exists(final_file) and format_type == 'mp3':
                    entry['album'] = album
                    entry['playlist_title'] = album
                    apply_metadata(final_file, entry, album=album)

                task.success_count += 1
            except Exception as e:
                print(f"Failed to download item {idx}: {e}")
                task.failed_items.append(str(e))

        # Final task update
        task.status = 'completed'
        task.progress = 100.0
        task.filename = info.get('title', 'Unknown')
        cleanup_task(task_id, download_tasks, Config.TASK_RETENTION_TIME)

    except yt_dlp.DownloadError as e:
        task.status = 'error'
        task.error = f"Download failed: {str(e)}"
        print(f"Download error for task {task_id}: {e}")
        cleanup_task(task_id, download_tasks, Config.TASK_RETENTION_TIME)
    except requests.exceptions.RequestException as e:
        task.status = 'error'
        task.error = f"Network error: {str(e)}"
        print(f"Network error for task {task_id}: {e}")
        cleanup_task(task_id, download_tasks, Config.TASK_RETENTION_TIME)
    except Exception as e:
        task.status = 'error'
        task.error = f"Unexpeceted Error: {str(e)}"
        print(f"Unexpeceted error for task {task_id}: {e}")
        cleanup_task(task_id, download_tasks, Config.TASK_RETENTION_TIME)


def start_download(url: str, format_type: str, quality: Optional[str], download_location: str, is_album: bool = False) -> str:
    """Starts a threaded download task and returns the task ID."""
    task_id: str = str(uuid.uuid4())
    task = DownloadProgress(task_id)
    download_tasks[task_id] = task

    t = threading.Thread(
        target=download_media,
        args=(url, format_type, quality, download_location, task_id, is_album),
        daemon=True
    )
    t.start()

    return task_id