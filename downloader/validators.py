from urllib.parse import urlparse
import re

class ValidationError(Exception):
    """Custom validation exception"""
    pass

def validate_url(url):
    """Validate URL format and scheme"""
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    
    url = url.strip()
    if len(url) > 2048:
        raise ValidationError("URL is too long")
    
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError("Invalid URL format")
        if result.scheme not in ['http', 'https']:
            raise ValidationError("Only HTTP(S) URLs are supported")
        return url
    except Exception:
        raise ValidationError("Invalid URL format")

def validate_format(format_type, allowed_formats):
    """Validate requested format"""
    if format_type not in allowed_formats:
        raise ValidationError(f"Format must be one of: {', '.join(allowed_formats)}")
    return format_type

def validate_quality(quality, format_type):
    """Validate quality parameter"""
    if format_type == 'mp3':
        valid_mp3_qualities = ['128', '192', '256', '320']
        if quality not in valid_mp3_qualities:
            raise ValidationError(f"MP3 quality must be one of: {', '.join(valid_mp3_qualities)}")
    elif format_type == 'mp4':
        valid_mp4_qualities = ['360', '480', '720', '1080', 'best']
        if quality not in valid_mp4_qualities:
            raise ValidationError(f"MP4 quality must be one of: {', '.join(valid_mp4_qualities)}")
    return quality

def validate_location(location, allowed_locations):
    """Validate download location"""
    if location not in allowed_locations:
        raise ValidationError(f"Location must be one of: {', '.join(allowed_locations)}")
    return location