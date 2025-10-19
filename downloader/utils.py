import os
import time
import threading
import imghdr
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, error
import requests


def apply_metadata(mp3_path, info, album=None):
    """Embed metadata and thumbnail into MP3 file for Navidrome"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        
        try:
            audio.add_tags()
        except error:
            pass

        title = info.get('track') or info.get('title') or "Unknown Title"
        artist = info.get('artist') or info.get('uploader') or "Unknown Artist"
        album_name = info.get('album') or info.get('playlist_title') or "Misc"

        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist))
        audio.tags.add(TALB(encoding=3, text=album_name))

        thumb_url = info.get('thumbnail')
        if thumb_url:
            _embed_thumbnail(audio, thumb_url)

        audio.save()
        print(f"Tagged: {mp3_path}")

    except Exception as e:
        print(f"Metadata tagging failed for {mp3_path}: {e}")


def _embed_thumbnail(audio, thumb_url):
    """Embed thumbnail image into audio file"""
    try:
        img_data = requests.get(thumb_url, timeout=10).content
        mime_type = f'image/{imghdr.what(None, img_data) or "jpeg"}'
        audio.tags.add(
            APIC(
                encoding=3,
                mime=mime_type,
                type=3,
                desc='Cover',
                data=img_data
            )
        )
    except Exception as e:
        print(f"Failed to embed thumbnail: {e}")


def progress_hook(d, task_id, tasks_dict):
    """Update task progress based on download status"""
    task = tasks_dict.get(task_id)
    if not task:
        return

    try:
        if d['status'] == 'downloading':
            _update_downloading_progress(d, task)
        elif d['status'] == 'finished':
            _update_finished_progress(d, task)
    except Exception as e:
        print(f"Error in progress hook: {e}")


def _update_downloading_progress(d, task):
    """Update task progress during download."""
    task.status = 'downloading'
    task.filename = os.path.basename(d.get('filename', 'Unknown'))
    task.total_size = d.get('total_bytes') or d.get('total_bytes_estimate')
    task.downloaded_size = d.get('downloaded_bytes', 0)
    task.speed = d.get('speed')
    task.eta = d.get('eta')

    current_video_progress = 0
    if task.total_size and task.total_size > 0:
        current_video_progress = task.downloaded_size / task.total_size

    if task.playlist_total > 1:
        completed = max(task.playlist_index - 1, 0)
        overall_progress = (completed + current_video_progress) / task.playlist_total
        task.progress = min(overall_progress * 100, 100)
    else:
        task.progress = min(current_video_progress * 100, 100)


def _update_finished_progress(d, task):
    """Update task progress after download finishes"""
    task.status = 'processing'
    task.filename = os.path.basename(d.get('filename', 'Unknown'))
    task.filepath = d.get('filename')

    if task.playlist_total > 1:
        task.progress = min((task.playlist_index / task.playlist_total) * 100, 100)
    else:
        task.progress = 95


def cleanup_task(task_id, tasks_dict, retention_minutes=60):
    """Remove task after retention period"""
    def delayed_cleanup():
        time.sleep(retention_minutes * 60)
        tasks_dict.pop(task_id, None)
    
    thread = threading.Thread(target=delayed_cleanup, daemon=True)
    thread.start()