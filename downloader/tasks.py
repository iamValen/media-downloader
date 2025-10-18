import os
import uuid
import threading
import yt_dlp
from datetime import datetime
from .utils import progress_hook, cleanup_task, apply_metadata
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


def _sanitize_filename(name):
    if not name:
        return "Unknown"
    return "".join(c for c in name if c.isalnum() or c in " .-_").strip()


def _build_output_path(base_path, artist, album):
    artist_folder = os.path.join(base_path, _sanitize_filename(artist))
    album_folder = os.path.join(artist_folder, _sanitize_filename(album))
    os.makedirs(album_folder, exist_ok=True)
    return album_folder


def _get_metadata(entry, default_title="Unknown Title"):
    title = entry.get('track') or entry.get('title') or default_title
    artist = entry.get('artist') or entry.get('uploader') or "Unknown Artist"
    album = entry.get('album') or entry.get('playlist_title') or "Singles"
    return title, artist, album


def _create_base_opts(task_id):
    return {
        'progress_hooks': [lambda d: progress_hook(d, task_id, download_tasks)],
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': True,
        'socket_timeout': 30,
        'skip_unavailable_fragments': True,
        'fragment_retries': 3,
        'postprocessors': [],
    }


def _configure_format_opts(base_opts, format_type, quality):
    if format_type == 'mp3':
        base_opts['format'] = 'bestaudio/best'
        base_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality or '192',
        })
    else:
        if quality and quality != 'best':
            base_opts['format'] = f"bestvideo[height<={quality}]+bestaudio/best"
        else:
            base_opts['format'] = "bestvideo+bestaudio/best"
    return base_opts


def _add_metadata_processors(opts):
    opts['writethumbnail'] = True
    opts['postprocessors'].extend([
        {'key': 'EmbedThumbnail'},
        {'key': 'FFmpegMetadata', 'add_metadata': True},
    ])
    return opts


def _download_playlist_item(entry, idx, output_folder, playlist_title, artist, use_album_tag, ydl_opts):
    title, entry_artist, _ = _get_metadata(entry, f"Track {idx}")
    
    item_opts = ydl_opts.copy()
    item_opts['outtmpl'] = os.path.join(output_folder, f"{_sanitize_filename(title)}.%(ext)s")
    
    album_name = playlist_title if use_album_tag else "Singles"
    
    item_opts['postprocessor_args'] = {
        'ffmpeg': [
            '-metadata', f'album={album_name}',
            '-metadata', f'artist={artist}',
            '-metadata', f'title={title}'
        ]
    }
    
    with yt_dlp.YoutubeDL(item_opts) as entry_ydl:
        entry_ydl.download([entry['webpage_url']])
    
    final_path = os.path.join(output_folder, f"{_sanitize_filename(title)}.mp3")
    if os.path.exists(final_path):
        apply_metadata(final_path, entry, album=album_name)
    
    return title


def download_media(url, format_type, quality, download_location, use_album_tag, task_id):
    task = download_tasks.get(task_id)
    if not task:
        return

    try:
        output_path = (
            Config.NETWORK_DOWNLOAD_PATH
            if download_location == 'network'
            else Config.TEMP_DOWNLOAD_PATH
        )

        base_opts = _create_base_opts(task_id)
        base_opts = _configure_format_opts(base_opts, format_type, quality)
        ydl_opts = _add_metadata_processors(base_opts)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info and info['entries']:
                entries = [e for e in info['entries'] if e]
                task.playlist_total = len(entries)
                playlist_title = info.get('title', 'Unknown Playlist')
                task.playlist_title = playlist_title

                first_artist = entries[0].get('artist') or entries[0].get('uploader') or "Unknown Artist"
                output_folder = _build_output_path(output_path, first_artist, playlist_title)

                for idx, entry in enumerate(entries, start=1):
                    task.playlist_index = idx
                    try:
                        _download_playlist_item(
                            entry, idx, output_folder, playlist_title, 
                            first_artist, use_album_tag, ydl_opts
                        )
                        task.success_count += 1
                    except Exception as e:
                        print(f"Failed item {idx}: {e}")
                        task.failed_items.append(str(e))
            else:
                title, artist, album = _get_metadata(info)
                output_folder = _build_output_path(output_path, artist, album)

                ydl_opts['outtmpl'] = os.path.join(output_folder, f"{_sanitize_filename(title)}.%(ext)s")
                ydl_opts['postprocessor_args'] = {
                    'ffmpeg': [
                        '-metadata', f'album={album}',
                        '-metadata', f'artist={artist}',
                        '-metadata', f'title={title}'
                    ]
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    ydl2.download([url])

                final_path = os.path.join(output_folder, f"{_sanitize_filename(title)}.mp3")
                if os.path.exists(final_path):
                    apply_metadata(final_path, info, album=album)

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


def start_download(url, format_type, quality, download_location, use_album_tag=False):
    task_id = str(uuid.uuid4())
    task = DownloadProgress(task_id)
    download_tasks[task_id] = task

    thread = threading.Thread(
        target=download_media,
        args=(url, format_type, quality, download_location, use_album_tag, task_id),
        daemon=True
    )
    thread.start()

    return task_id