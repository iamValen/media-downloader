from flask import Blueprint, request, jsonify
from config import Config
from downloader.tasks import download_tasks, start_download
from downloader.validators import *



api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/download', methods=['POST'])
def download():
    """Start a new download task."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        url = validate_url(data.get('url', '').strip())
        format_type = validate_format(data.get('format', 'mp3'), Config.ALLOWED_FORMATS)
        quality = validate_quality(data.get('quality', '192'), format_type)
        location = validate_location(data.get('location', 'default'), Config.ALLOWED_LOCATIONS)
        is_album = data.get('isAlbum', False)
        
        task_id = start_download(url, format_type, quality, location, is_album)
        task = download_tasks.get(task_id)
        
        if task.status == 'error':
            return jsonify({'error': task.error}), 400
        
        return jsonify({'task_id': task_id}), 201
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@api_bp.route('/status/<task_id>', methods=['GET'])
def status(task_id):
    """Get status of a download task."""
    try:
        task = download_tasks.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify(task.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@api_bp.route('/config', methods=['GET'])
def config():
    """Get application configuration."""
    return jsonify({
        'default_path': Config.DEFAULT_DOWNLOAD_PATH,
        'alt_path': Config.ALT_DOWNLOAD_PATH,
        'allowed_formats': Config.ALLOWED_FORMATS,
        'max_playlist_size': Config.MAX_PLAYLIST_SIZE,
    }), 200


@api_bp.errorhandler(400)
@api_bp.errorhandler(404)
@api_bp.errorhandler(500)
def handle_error(error):
    """Handle HTTP errors."""
    return jsonify({'error': str(error)}), error.code