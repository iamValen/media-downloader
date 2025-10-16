from flask import Blueprint, request, jsonify
from downloader.tasks import download_tasks, start_download
from downloader.validators import ValidationError
from config import Config


api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        url = data.get('url', '').strip()
        format_type = data.get('format', 'mp3')
        quality = data.get('quality', '192')
        location = data.get('location', 'network')
        
        task_id = start_download(url, format_type, quality, location)
        task = download_tasks.get(task_id)
        
        if task.status == 'error':
            return jsonify({'error': task.error}), 400
        
        return jsonify({'task_id': task_id}), 201
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@api_bp.route('/status/<task_id>', methods=['GET'])
def status(task_id):
    try:
        task = download_tasks.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify(task.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@api_bp.route('/config', methods=['GET'])
def config():
    return jsonify({
        'network_path': Config.NETWORK_DOWNLOAD_PATH,
        'temp_path': Config.TEMP_DOWNLOAD_PATH,
        'allowed_formats': Config.ALLOWED_FORMATS,
        'max_playlist_size': Config.MAX_PLAYLIST_SIZE,
    }), 200


@api_bp.errorhandler(400)
@api_bp.errorhandler(404)
@api_bp.errorhandler(500)
def handle_error(error):
    return jsonify({'error': str(error)}), error.code