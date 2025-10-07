from flask import Blueprint, request, jsonify
from downloader.tasks import download_tasks, start_download


api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'mp3')
    quality = data.get('quality', '192')
    location = data.get('location', 'network')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    task_id = start_download(url, format_type, quality, location)
    return jsonify({'task_id': task_id})


@api_bp.route('/status/<task_id>', methods=['GET'])
def status(task_id):
    task = download_tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task.to_dict())


@api_bp.route('/config', methods=['GET'])
def config():
    from config import Config
    return jsonify({
        'network_path': Config.NETWORK_DOWNLOAD_PATH,
        'temp_path': Config.TEMP_DOWNLOAD_PATH
    })
