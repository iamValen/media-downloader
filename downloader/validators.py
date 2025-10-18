from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_url(url):
    """Validate and clean URL string."""
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    
    url = url.strip()
    parsed = urlparse(url)
    
    if not parsed.scheme or not parsed.netloc:
        raise ValidationError("Invalid URL")
    
    return url


def validate_format(format_type, allowed_formats):
    """Validate format type or return default."""
    return format_type if format_type else 'mp3'


def validate_quality(quality, format_type):
    """Validate quality setting or return format-specific default."""
    return quality or ('192' if format_type == 'mp3' else 'best')


def validate_location(location, allowed_locations):
    """Validate location or return default."""
    return location if location in allowed_locations else 'default'