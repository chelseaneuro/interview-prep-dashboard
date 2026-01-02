import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from backend import config
from backend.utils import setup_logger

logger = setup_logger(__name__)


class CareerDocumentHandler(FileSystemEventHandler):
    """
    Event handler for file system events in monitored directory.
    """

    def __init__(self, callback):
        """
        Initialize handler with callback function.

        Args:
            callback: Function to call when a relevant file is created/modified
        """
        super().__init__()
        self.callback = callback
        self.last_processed = {}  # Track last processing time for debouncing

    def on_created(self, event):
        """
        Handle file creation events.

        Args:
            event: FileSystemEvent object
        """
        if event.is_directory:
            return

        file_path = event.src_path

        if self.should_process(file_path):
            logger.info(f"New file detected: {file_path}")
            self.debounce_and_process(file_path)

    def on_modified(self, event):
        """
        Handle file modification events.

        Args:
            event: FileSystemEvent object
        """
        if event.is_directory:
            return

        file_path = event.src_path

        if self.should_process(file_path):
            logger.debug(f"File modified: {file_path}")
            self.debounce_and_process(file_path)

    def should_process(self, file_path):
        """
        Check if file should be processed.

        Args:
            file_path: Path to file

        Returns:
            bool: True if file should be processed
        """
        # Check if file has supported extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in config.SUPPORTED_EXTENSIONS:
            return False

        # Check if file exists and is readable
        if not os.path.exists(file_path):
            return False

        if not os.path.isfile(file_path):
            return False

        return True

    def debounce_and_process(self, file_path):
        """
        Debounce file processing to avoid processing incomplete files.

        Waits for DEBOUNCE_SECONDS after last modification before processing.

        Args:
            file_path: Path to file
        """
        current_time = time.time()
        last_time = self.last_processed.get(file_path, 0)

        # If we processed this file recently, skip
        if current_time - last_time < config.DEBOUNCE_SECONDS:
            logger.debug(f"Debouncing {file_path}")
            return

        # Update last processed time
        self.last_processed[file_path] = current_time

        # Wait for debounce period to ensure file is fully written
        logger.debug(f"Waiting {config.DEBOUNCE_SECONDS} seconds before processing {file_path}")
        time.sleep(config.DEBOUNCE_SECONDS)

        # Call the callback to process the file
        try:
            self.callback(file_path)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")


def start_watching(documents_path, callback):
    """
    Start watching directory for new/modified documents.

    Args:
        documents_path: Path to directory to watch
        callback: Function to call when a document needs processing

    Returns:
        Observer: watchdog Observer instance (call .stop() to stop watching)
    """
    if not os.path.exists(documents_path):
        logger.warning(f"Directory does not exist, creating: {documents_path}")
        try:
            os.makedirs(documents_path, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {documents_path}: {str(e)}")
            return None

    event_handler = CareerDocumentHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, documents_path, recursive=True)

    try:
        observer.start()
        logger.info(f"Started watching directory: {documents_path}")
        return observer
    except Exception as e:
        logger.error(f"Failed to start file watcher: {str(e)}")
        return None


def stop_watching(observer):
    """
    Stop watching directory.

    Args:
        observer: watchdog Observer instance
    """
    if observer:
        try:
            observer.stop()
            observer.join(timeout=5)
            logger.info("Stopped watching directory")
        except Exception as e:
            logger.error(f"Error stopping file watcher: {str(e)}")
