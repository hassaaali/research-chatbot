import os
import aiofiles
from pathlib import Path
from typing import Dict, Any
from fastapi import UploadFile

from app.core.config import settings

async def save_upload_file(file: UploadFile, content: bytes, file_id: str) -> Path:
    """Save uploaded file to disk"""
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_PATH)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate file path
    file_extension = Path(file.filename).suffix
    file_path = upload_dir / f"{file_id}{file_extension}"
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    return file_path

def validate_file(file: UploadFile) -> Dict[str, Any]:
    """Validate uploaded file"""
    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        return {
            "valid": False,
            "error": f"File type {file_extension} not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        }
    
    # Check file size (this is approximate since we haven't read the content yet)
    if hasattr(file, 'size') and file.size and file.size > settings.MAX_FILE_SIZE:
        return {
            "valid": False,
            "error": f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        }
    
    return {"valid": True}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"