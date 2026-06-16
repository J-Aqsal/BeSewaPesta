from datetime import datetime
from django.utils import timezone
from django.utils.timezone import make_aware, is_aware, localtime, get_current_timezone


def parse_datetime(date_str):
    """
    Parses a string or datetime into a timezone-aware (Jakarta) datetime object.
    """
    if not date_str:
        return None
    
    if isinstance(date_str, datetime):
        if not is_aware(date_str):
            # We treat it as Jakarta time.
            return make_aware(date_str, get_current_timezone())
        return localtime(date_str)
        
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%dT%H:%M',
        '%Y-%m-%d',
    ]
    
    clean_str = str(date_str).split('.')[0].replace('Z', '')
    
    for fmt in formats:
        try:
            dt = datetime.strptime(clean_str, fmt)
            return make_aware(dt)
        except ValueError:
            continue
            
    return None

def to_local_time(dt):
    """
    Converts any datetime to local Jakarta time string.
    """
    if dt is None:
        return None
        
    if not is_aware(dt):
        dt = make_aware(dt, get_current_timezone())
    
    return localtime(dt)
