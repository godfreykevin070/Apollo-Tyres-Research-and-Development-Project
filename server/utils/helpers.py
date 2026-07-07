import os
import re
import json
from datetime import datetime
from typing import Any, Dict, Optional

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to remove invalid characters"""
    # Remove any path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    # Remove any other invalid characters
    filename = re.sub(r'[<>:"|?*]', '', filename)
    return filename.strip()

def ensure_directory(path: str) -> str:
    """Ensure a directory exists, create if not"""
    os.makedirs(path, exist_ok=True)
    return path

def parse_parameters_file(content: str) -> Dict[str, str]:
    """
    Parse a parameters.inc file and return key-value pairs
    
    Args:
        content: File content as string
    
    Returns:
        Dictionary of parameter key-value pairs
    """
    parameters = {}
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        # Skip comments and empty lines
        if line.startswith('!') or not line:
            continue
        
        # Parse parameter=value
        match = re.match(r'^(\w+)\s*=\s*(.+)$', line)
        if match:
            key = match.group(1)
            value = match.group(2)
            # Remove trailing comments
            if '!' in value:
                value = value.split('!')[0].strip()
            parameters[key] = value
    
    return parameters

def generate_unique_id(prefix: str = "USR") -> str:
    """
    Generate a unique ID with prefix and random alphanumeric suffix
    
    Args:
        prefix: Prefix for the ID (e.g., 'USR', 'PROJ')
    
    Returns:
        Unique ID string
    """
    import random
    import string
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{suffix}"

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a timestamp as ISO string"""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()

def safe_json_loads(data: str) -> Dict[str, Any]:
    """Safely parse JSON data"""
    try:
        if isinstance(data, dict):
            return data
        if isinstance(data, str) and data.strip():
            return json.loads(data)
        return {}
    except json.JSONDecodeError:
        return {}

def safe_json_dumps(data: Dict[str, Any]) -> str:
    """Safely convert data to JSON string"""
    try:
        return json.dumps(data)
    except Exception:
        return '{}'

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    if not filename:
        return ''
    parts = filename.rsplit('.', 1)
    return parts[-1].lower() if len(parts) > 1 else ''

def is_valid_odb_file(filename: str) -> bool:
    """Check if filename is a valid ODB file"""
    return get_file_extension(filename) == 'odb'

def is_valid_tydex_file(filename: str) -> bool:
    """Check if filename is a valid Tydex file"""
    return get_file_extension(filename) in ['tdx', 'txt']

def is_valid_inp_file(filename: str) -> bool:
    """Check if filename is a valid Abaqus input file"""
    return get_file_extension(filename) == 'inp'

def is_valid_fortran_file(filename: str) -> bool:
    """Check if filename is a valid Fortran source file"""
    return get_file_extension(filename) in ['f', 'for', 'f90']