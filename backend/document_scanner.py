import os
from datetime import datetime
from backend import config
from backend.utils import setup_logger

logger = setup_logger(__name__)


def scan_directory(path):
    """
    Recursively scan directory for relevant documents.

    Args:
        path: Directory path to scan

    Returns:
        list: List of document metadata dictionaries
    """
    documents = []

    if not os.path.exists(path):
        logger.warning(f"Directory does not exist: {path}")
        return documents

    if not os.path.isdir(path):
        logger.warning(f"Path is not a directory: {path}")
        return documents

    try:
        for root, dirs, files in os.walk(path):
            for filename in files:
                file_path = os.path.join(root, filename)
                _, ext = os.path.splitext(filename)

                # Check if file extension is supported
                if ext.lower() in config.SUPPORTED_EXTENSIONS:
                    metadata = {
                        "file_path": file_path,
                        "file_name": filename,
                        "file_type": ext.lower().replace(".", ""),
                        "document_category": get_document_type(filename),
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                        "file_size": os.path.getsize(file_path)
                    }
                    documents.append(metadata)

        logger.info(f"Found {len(documents)} documents in {path}")
        return documents

    except Exception as e:
        logger.error(f"Error scanning directory {path}: {str(e)}")
        return documents


def get_document_type(file_name):
    """
    Categorize document by filename patterns.

    Args:
        file_name: Name of the file

    Returns:
        str: Document category (resume, cover_letter, application, general)
    """
    file_name_lower = file_name.lower()

    # Resume patterns
    resume_keywords = ['resume', 'cv', 'curriculum', 'vitae']
    if any(keyword in file_name_lower for keyword in resume_keywords):
        return "resume"

    # Cover letter patterns
    cover_keywords = ['cover', 'letter', 'coverletter']
    if any(keyword in file_name_lower for keyword in cover_keywords):
        return "cover_letter"

    # Job application patterns
    application_keywords = ['application', 'job', 'apply', 'applied']
    if any(keyword in file_name_lower for keyword in application_keywords):
        return "application"

    # Projects or portfolio
    project_keywords = ['project', 'portfolio', 'work']
    if any(keyword in file_name_lower for keyword in project_keywords):
        return "project"

    # Default to general career document
    return "general"


def is_career_related(file_path):
    """
    Determine if a file is career-related based on name and location.

    Note: Currently returns True for all files in the monitored directory.
    Can be enhanced with more sophisticated filtering.

    Args:
        file_path: Path to file

    Returns:
        bool: True if file is likely career-related
    """
    # For now, we assume all documents in the monitored folder are career-related
    # Can add more sophisticated logic here if needed
    return True
