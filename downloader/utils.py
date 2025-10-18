import os
import time
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, error
from mutagen.mp3 import MP3
import requests

def apply_metadata(mp3_path, info, album=None):
    """Embed metadata + thumbnail into MP3 for Navidrome"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        try:
            audio.add_tags()
        except error:
            pass

        title = info.get('track') or info.get('title') or "Unknown Title"
        artist = info.get('artist') or info.get('uploader') or "Unknown Artist"
        album = info.get('album') or info.get('playlist_title') or "Misc"

        audio["TIT2"] = title
        audio["TPE1"] = artist
        audio["TALB"] = album

        thumb_url = info.get('thumbnail')
        if thumb_url:
            try:
                img_data = requests.get(thumb_url, timeout=10).content
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=img_data
                    )
                )
            except Exception as e:
                print(f"Failed to embed thumbnail: {e}")

        audio.save()
        print(f"Tagged: {mp3_path}")

    except Exception as e:
        print(f"Metadata tagging failed for {mp3_path}: {e}")


def progress_hook(d, task_id, tasks_dict):
    task = tasks_dict.get(task_id)
    if not task:
        return

    try:
        if d['status'] == 'downloading':
            task.status = 'downloading'
            task.filename = os.path.basename(d.get('filename', 'Unknown'))
            task.total_size = d.get('total_bytes') or d.get('total_bytes_estimate')
            task.downloaded_size = d.get('downloaded_bytes', 0)
            task.speed = d.get('speed')
            task.eta = d.get('eta')

            # progress for current video
            if task.total_size and task.total_size > 0:
                current_video_progress = (task.downloaded_size / task.total_size)
            else:
                current_video_progress = 0

            # playlist progress
            if task.playlist_total > 1:
                completed = max(task.playlist_index - 1, 0)
                overall_progress = (
                    (completed + current_video_progress) / task.playlist_total
                ) * 100
                task.progress = min(overall_progress, 99.9)
            else:
                task.progress = min(current_video_progress * 100, 99.9)

        elif d['status'] == 'finished':
            task.status = 'processing'
            task.filename = os.path.basename(d.get('filename', 'Unknown'))
            task.filepath = d.get('filename')

            if task.playlist_total > 1:
                completed = task.playlist_index
                task.progress = min((completed / task.playlist_total) * 100, 99.9)
            else:
                task.progress = 95

    except Exception as e:
        print(f"Error in progress hook: {e}")


def cleanup_task(task_id, tasks_dict, retention_minutes=60):
    """Remove task after retention period"""
    def delayed_cleanup():
        time.sleep(retention_minutes * 60)
        tasks_dict.pop(task_id, None)
    
    import threading
    thread = threading.Thread(target=delayed_cleanup, daemon=True)
    thread.start()

def is_valid_file_size(filepath, max_gb=5):
    try:
        if not os.path.exists(filepath):
            return False
        size = os.path.getsize(filepath)
        return size > 0 and size < (max_gb * 1024 * 1024 * 1024)
    except:
        return False