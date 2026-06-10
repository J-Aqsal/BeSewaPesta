from datetime import datetime

def parse_datetime(date_str):
    if not date_str:
        return None
    
    if isinstance(date_str, datetime):
        return date_str
        
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%dT%H:%M',
        '%Y-%m-%d',
    ]
    
    # Clean string from possible milliseconds/extra precision
    clean_str = date_str.split('.')[0].replace('Z', '')
    
    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt)
        except ValueError:
            continue
            
    return None
