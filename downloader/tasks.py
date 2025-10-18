import os
import uuid
import threading
import yt_dlp
from datetime import datetime
from .utils import progress_hook, cleanup_task, apply_metadata
from .validators import ValidationError
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
        self.created_at = datetime.now().isoformat()
        self.failed_items = []
        self.success_count = 0
        self.playlist_total = 0
        self.playlist_index = 0
        self.playlist_title = None

    def to_dict(self):
        return self.__dict__

def _sanitize_name(name):
    """Make filesystem-safe filenames"""
    if not name:
        return "Unknown"
    return "".join(c for c in name if c.isalnum() or c in " .-_").strip()

def download_media(url, format_type, quality, download_location, task_id, is_album):
    task = download_tasks.get(task_id)
    if not task:
        return

    try:
        output_path = (
            Config.DEFAULT_DOWNLOAD_PATH
            if download_location == 'default'
            else Config.ALT_DOWNLOAD_PATH
        )
        os.makedirs(output_path, exist_ok=True)

        base_opts = {
            'progress_hooks': [lambda d: progress_hook(d, task_id, download_tasks)],
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'socket_timeout': 30,
            'skip_unavailable_fragments': True,
            'fragment_retries': 3,
            'postprocessors': [],
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

        # Embed metadata and thumbnail
        ydl_opts = base_opts.copy()
        ydl_opts.update({
            'writethumbnail': False,
            'writeinfojson': False,
            'postprocessors': base_opts.get('postprocessors', []) + [
                {'key': 'EmbedThumbnail'},
                {'key': 'FFmpegMetadata', 'add_metadata': True},
            ],
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Playlist handling
            if 'entries' in info and info['entries']:
                entries = [e for e in info['entries'] if e]
                task.playlist_total = len(entries)
                playlist_title = info.get('title', 'Unknown Playlist')
                task.playlist_title = playlist_title

                for idx, entry in enumerate(entries, start=1):
                    task.playlist_index = idx
                    try:
                        artist = entry.get('artist') or entry.get('uploader') or "Unknown Artist"
                        title = entry.get('track') or entry.get('title') or f"Track {idx}"

                        # Determine album name based on checkbox
                        if is_album:
                            album = playlist_title
                        else:
                            album = "Single"

                        # Folder structure: Artist/Album/
                        artist_folder = os.path.join(output_path, _sanitize_name(artist))
                        album_folder = os.path.join(artist_folder, _sanitize_name(album))
                        os.makedirs(album_folder, exist_ok=True)

                        entry_opts = ydl_opts.copy()
                        entry_opts['outtmpl'] = os.path.join(album_folder, f"{_sanitize_name(title)}.%(ext)s")
                        
                        # Set album metadata
                        entry_opts['postprocessor_args'] = {
                            'ffmpeg': [
                                '-metadata', f'album={album}',
                                '-metadata', f'artist={artist}',
                                '-metadata', f'title={title}'
                            ]
                        }

                        with yt_dlp.YoutubeDL(entry_opts) as entry_ydl:
                            entry_ydl.download([entry['webpage_url']])

                        final_mp3 = os.path.join(album_folder, f"{_sanitize_name(title)}.mp3")
                        if os.path.exists(final_mp3):
                            entry['album'] = album
                            entry['playlist_title'] = album
                            apply_metadata(final_mp3, entry, album=album)

                        task.success_count += 1
                    except Exception as e:
                        print(f"Failed to download item {idx}: {e}")
                        task.failed_items.append(str(e))
            else:
                # Single video
                title = info.get('track') or info.get('title') or "Unknown Title"
                artist = info.get('artist') or info.get('uploader') or "Unknown Artist"
                
                # Determine album name based on checkbox
                if is_album:
                    album = info.get('album') or info.get('playlist_title') or "Unknown Album"
                else:
                    album = "Single"

                artist_folder = os.path.join(output_path, _sanitize_name(artist))
                album_folder = os.path.join(artist_folder, _sanitize_name(album))
                os.makedirs(album_folder, exist_ok=True)

                ydl_opts['outtmpl'] = os.path.join(album_folder, f"{_sanitize_name(title)}.%(ext)s")
                
                # Add metadata for single videos
                ydl_opts['postprocessor_args'] = {
                    'ffmpeg': [
                        '-metadata', f'album={album}',
                        '-metadata', f'artist={artist}',
                        '-metadata', f'title={title}'
                    ]
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    ydl2.download([url])

                final_mp3 = os.path.join(album_folder, f"{_sanitize_name(title)}.mp3")
                if os.path.exists(final_mp3):
                    apply_metadata(final_mp3, info, album=album)

                task.success_count = 1

        task.filename = info.get('title', 'Unknown')
        task.status = 'completed'
        task.progress = 100
        cleanup_task(task_id, download_tasks, Config.TASK_RETENTION_TIME)

    except Exception as e:
        task.status = 'error'
        task.error = str(e)
        print(f"Download error for task {task_id}: {e}")
        cleanup_task(task_id, download_tasks, Config.TASK_RETENTION_TIME)


def start_download(url, format_type, quality, download_location, is_album=False):
    """Starts a threaded download task and returns the task ID."""
    import threading
    task_id = str(uuid.uuid4())
    task = DownloadProgress(task_id)
    download_tasks[task_id] = task

    t = threading.Thread(
        target=download_media,
        args=(url, format_type, quality, download_location, task_id, is_album),
        daemon=True
    )
    t.start()

    return task_id