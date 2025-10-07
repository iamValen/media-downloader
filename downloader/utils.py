import os

def progress_hook(d, task_id, tasks_dict):
    task = tasks_dict.get(task_id)
    if not task:
        return

    if d['status'] == 'downloading':
        task.status = 'downloading'
        task.filename = os.path.basename(d.get('filename', 'Unknown'))
        task.total_size = d.get('total_bytes') or d.get('total_bytes_estimate')
        task.downloaded_size = d.get('downloaded_bytes', 0)
        task.speed = d.get('speed')
        task.eta = d.get('eta')
        if task.total_size:
            task.progress = (task.downloaded_size / task.total_size) * 100
    elif d['status'] == 'finished':
        task.status = 'processing'
        task.progress = 95
        task.filename = os.path.basename(d.get('filename', 'Unknown'))
        task.filepath = d.get('filename')
