import os
from typing import List
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


def validate_url(url: str) -> str:
    """Validate and clean URL string"""
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    
    url = url.strip()
    parsed = urlparse(url)
    
    if not parsed.scheme or not parsed.netloc:
        raise ValidationError("Invalid URL")
    
    return url


def validate_format(format_type: str, allowed_formats: List[str]) -> str:
    """Validate format type or return default"""
    return format_type if format_type else 'mp3'


def validate_quality(quality: str, format_type: str) -> str:
    """Validate quality setting or return format-specific default"""
    return quality or ('192' if format_type == 'mp3' else 'best')


def validate_location(location: str, allowed_locations: List[str]) -> str:
    """Validate location or return default"""
    return location if location in allowed_locations else 'default'


def validate_file_size(filepath: str, max_gb: int = 5) -> bool:
    """Check if file exists and size is within acceptable range"""
    try:
        if not os.path.exists(filepath):
            return False
        
        size: int = os.path.getsize(filepath)
        max_bytes: int = max_gb * 1024 * 1024 * 1024
        return 0 < size < max_bytes
    except Exception:
        return False
