from urllib.parse import urlparse

class ValidationError(Exception):
    pass

def validate_url(url):
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    url = url.strip()
    result = urlparse(url)
    if not result.scheme or not result.netloc:
        raise ValidationError("Invalid URL")
    return url

def validate_format(format_type, allowed_formats):
    return format_type if format_type else 'mp3'

def validate_quality(quality, format_type):
    return quality or ('192' if format_type == 'mp3' else 'best')

def validate_location(location, allowed_locations):
    return location if location in allowed_locations else 'network'
