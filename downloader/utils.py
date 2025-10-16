import os
import time
from pathlib import Path

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