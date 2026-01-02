import os
import hashlib
import logging
from backend import config


def setup_logger(name):
    """
    Configure logging with file and console handlers.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    os.makedirs(config.LOGS_PATH, exist_ok=True)

    # File handler
    log_file = os.path.join(config.LOGS_PATH, "scanner.log")
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(config.LOG_FORMAT)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def validate_file(file_path):
    """
    Check if file exists, is readable, and within size limits.

    Args:
        file_path: Path to file to validate

    Returns:
        dict: {
            "valid": bool,
            "error": str or None,
            "size_mb": float
        }
    """
    # Check file exists
    if not os.path.exists(file_path):
        return {
            "valid": False,
            "error": "File does not exist",
            "size_mb": 0
        }

    # Check if it's a file (not directory)
    if not os.path.isfile(file_path):
        return {
            "valid": False,
            "error": "Path is not a file",
            "size_mb": 0
        }

    # Check readable
    if not os.access(file_path, os.R_OK):
        return {
            "valid": False,
            "error": "File is not readable",
            "size_mb": 0
        }

    # Check file size
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > config.MAX_FILE_SIZE_MB:
        return {
            "valid": False,
            "error": f"File size ({size_mb:.2f}MB) exceeds maximum ({config.MAX_FILE_SIZE_MB}MB)",
            "size_mb": size_mb
        }

    # Check file extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in config.SUPPORTED_EXTENSIONS:
        return {
            "valid": False,
            "error": f"Unsupported file extension: {ext}",
            "size_mb": size_mb
        }

    return {
        "valid": True,
        "error": None,
        "size_mb": size_mb
    }


def calculate_file_hash(file_path):
    """
    Generate SHA-256 hash of file to detect changes.

    Args:
        file_path: Path to file

    Returns:
        str: Hex digest of file hash
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def fuzzy_match_company(company1, company2, threshold=0.8):
    """
    Simple fuzzy matching for company names to detect duplicates.

    Args:
        company1: First company name
        company2: Second company name
        threshold: Similarity threshold (0-1)

    Returns:
        bool: True if companies are likely the same
    """
    # Normalize companies (lowercase, remove common suffixes)
    def normalize(company):
        if not company:
            return ""
        company = company.lower().strip()
        # Remove common company suffixes
        suffixes = [" inc", " inc.", " llc", " ltd", " ltd.", " corp", " corp.", " co", " co.", " company"]
        for suffix in suffixes:
            if company.endswith(suffix):
                company = company[:-len(suffix)].strip()
        return company

    norm1 = normalize(company1)
    norm2 = normalize(company2)

    # If one is contained in the other, likely the same
    if norm1 in norm2 or norm2 in norm1:
        return True

    # Simple character-based similarity (Levenshtein would be better but this is simpler)
    if norm1 == norm2:
        return True

    return False


def format_date(date_string):
    """
    Normalize date formats to YYYY-MM or YYYY.

    Args:
        date_string: Date in various formats

    Returns:
        str: Normalized date string
    """
    if not date_string:
        return None

    # Already in correct format
    if len(date_string) == 7 and date_string[4] == '-':  # YYYY-MM
        return date_string
    if len(date_string) == 4:  # YYYY
        return date_string

    # Add more parsing logic as needed
    return date_string
