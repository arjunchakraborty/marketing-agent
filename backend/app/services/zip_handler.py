"""Utility functions for handling zip file uploads and extraction."""
import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def extract_zip_file(zip_file_path: str, extract_to: Optional[str] = None) -> str:
    """
    Extract a zip file to a temporary directory.
    
    Args:
        zip_file_path: Path to the zip file
        extract_to: Optional destination directory. If None, creates a temp directory.
        
    Returns:
        Path to the extracted directory
    """
    zip_path = Path(zip_file_path)
    
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_file_path}")
    
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"File is not a valid zip file: {zip_file_path}")
    
    # Create extraction directory
    if extract_to:
        extract_dir = Path(extract_to)
        extract_dir.mkdir(parents=True, exist_ok=True)
    else:
        extract_dir = Path(tempfile.mkdtemp(prefix="zip_extract_"))
    
    logger.info(f"Extracting zip file {zip_file_path} to {extract_dir}")
    
    # Extract zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    logger.info(f"Extracted {len(zip_ref.namelist())} files to {extract_dir}")
    
    return str(extract_dir)


def cleanup_directory(directory_path: str) -> None:
    """
    Remove a directory and all its contents.
    
    Args:
        directory_path: Path to the directory to remove
    """
    dir_path = Path(directory_path)
    
    if dir_path.exists() and dir_path.is_dir():
        logger.info(f"Cleaning up directory: {directory_path}")
        shutil.rmtree(dir_path)
        logger.info(f"Directory removed: {directory_path}")
    elif dir_path.exists():
        logger.warning(f"Path exists but is not a directory: {directory_path}")


def cleanup_file(file_path: str) -> None:
    """
    Remove a file.
    
    Args:
        file_path: Path to the file to remove
    """
    file = Path(file_path)
    
    if file.exists() and file.is_file():
        logger.info(f"Cleaning up file: {file_path}")
        file.unlink()
        logger.info(f"File removed: {file_path}")
    elif file.exists():
        logger.warning(f"Path exists but is not a file: {file_path}")


def find_file_in_directory(directory: str, pattern: str, recursive: bool = True) -> Optional[str]:
    """
    Find a file matching a pattern in a directory.
    
    Args:
        directory: Directory to search in
        pattern: File pattern to match (e.g., "*.csv", "email_campaigns.csv")
        recursive: Whether to search recursively
        
    Returns:
        Path to the first matching file, or None if not found
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return None
    
    if recursive:
        matches = list(dir_path.rglob(pattern))
    else:
        matches = list(dir_path.glob(pattern))
    
    if matches:
        return str(matches[0])
    
    return None


def find_directory_in_directory(directory: str, name: str, recursive: bool = True) -> Optional[str]:
    """
    Find a subdirectory with a specific name.
    
    Args:
        directory: Directory to search in
        name: Name of the directory to find
        recursive: Whether to search recursively
        
    Returns:
        Path to the directory, or None if not found
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return None
    
    if recursive:
        matches = [d for d in dir_path.rglob("*") if d.is_dir() and d.name == name]
    else:
        matches = [d for d in dir_path.glob("*") if d.is_dir() and d.name == name]
    
    if matches:
        return str(matches[0])
    
    return None






