#!/usr/bin/env python3
"""
Interview Prep Dashboard - Phase 1: Document Scanner & Profile Builder

Main entry point for the document scanning and career information extraction system.
"""

import sys
import signal
from backend import config
from backend.utils import setup_logger, validate_file, calculate_file_hash
from backend.document_scanner import scan_directory
from backend.document_parser import parse_document
from backend.claude_extractor import extract_career_info
from backend.data_manager import (
    load_profile,
    save_profile,
    merge_career_data,
    is_document_processed,
    mark_document_as_processed
)
from backend.file_watcher import start_watching, stop_watching

logger = setup_logger(__name__)

# Global variable to hold the observer
observer = None


def signal_handler(sig, frame):
    """
    Handle shutdown signals gracefully.
    """
    logger.info("Shutdown signal received, stopping...")
    if observer:
        stop_watching(observer)
    sys.exit(0)


def process_document(file_path):
    """
    Process a single document: validate, parse, extract, merge, save.

    Args:
        file_path: Path to document to process

    Returns:
        bool: True if successfully processed
    """
    logger.info(f"Processing document: {file_path}")

    # Step 1: Validate file
    validation = validate_file(file_path)
    if not validation["valid"]:
        logger.warning(f"File validation failed for {file_path}: {validation['error']}")
        return False

    logger.info(f"File validated: {validation['size_mb']:.2f} MB")

    # Step 2: Calculate file hash
    try:
        file_hash = calculate_file_hash(file_path)
    except Exception as e:
        logger.error(f"Failed to calculate file hash: {str(e)}")
        return False

    # Step 3: Check if already processed
    if is_document_processed(file_path, file_hash):
        logger.info(f"Document already processed (unchanged): {file_path}")
        return True  # Not an error, just skipping

    # Step 4: Parse document to extract text
    logger.info("Extracting text from document...")
    parse_result = parse_document(file_path)

    if not parse_result["success"]:
        logger.error(f"Failed to parse document: {parse_result['error']}")
        # Mark as processed but failed
        mark_document_as_processed(
            file_path,
            file_hash,
            {"document_category": "unknown"},
            {"success": False, "error": parse_result['error']}
        )
        return False

    logger.info(f"Extracted {parse_result['char_count']} characters")

    # Step 5: Send to Claude for intelligent extraction
    logger.info("Sending to Claude API for career information extraction...")

    from backend.document_scanner import get_document_type
    doc_type = get_document_type(file_path)

    extraction_result = extract_career_info(parse_result["text"], doc_type)

    if not extraction_result["success"]:
        logger.error(f"Failed to extract career info: {extraction_result['error']}")
        # Mark as processed but failed
        mark_document_as_processed(
            file_path,
            file_hash,
            {"document_category": doc_type},
            extraction_result
        )
        return False

    logger.info("Successfully extracted career information")

    # Step 6: Load existing profile
    profile = load_profile()

    # Step 7: Merge extracted data with existing profile
    logger.info("Merging extracted data with existing profile...")
    merged_profile = merge_career_data(profile, extraction_result["data"])

    # Step 8: Save updated profile
    if save_profile(merged_profile):
        logger.info("Profile updated successfully")
    else:
        logger.error("Failed to save profile")
        return False

    # Step 9: Mark document as processed
    mark_document_as_processed(
        file_path,
        file_hash,
        {"document_category": doc_type},
        extraction_result
    )

    logger.info(f"Successfully processed document: {file_path}")
    return True


def process_existing_documents():
    """
    Scan and process all existing documents in the monitored directory.

    Returns:
        int: Number of documents successfully processed
    """
    logger.info("Scanning for existing documents...")

    documents = scan_directory(config.DOCUMENTS_PATH)

    if not documents:
        logger.info("No existing documents found")
        return 0

    logger.info(f"Found {len(documents)} document(s), processing...")

    success_count = 0
    for doc in documents:
        try:
            if process_document(doc["file_path"]):
                success_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {doc['file_path']}: {str(e)}")

    logger.info(f"Processed {success_count}/{len(documents)} documents successfully")
    return success_count


def main():
    """
    Main entry point for the document scanner.
    """
    global observer

    print("=" * 60)
    print("Interview Prep Dashboard - Document Scanner")
    print("=" * 60)
    print()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Step 1: Validate configuration
    logger.info("Starting document scanner...")
    logger.info(f"Documents path: {config.DOCUMENTS_PATH}")
    logger.info(f"Data path: {config.DATA_PATH}")

    if not config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set in environment!")
        logger.error("Please set your API key in the .env file")
        print("\nERROR: ANTHROPIC_API_KEY not configured!")
        print("Please edit .env and add your API key from: https://console.anthropic.com/")
        sys.exit(1)

    logger.info("Configuration validated")

    # Step 2: Process existing documents
    print("\nScanning for existing documents...")
    process_existing_documents()

    # Step 3: Start file watcher
    print(f"\nNow monitoring: {config.DOCUMENTS_PATH}")
    print("Add documents to this folder and they will be processed automatically.")
    print("Press Ctrl+C to stop.\n")

    observer = start_watching(config.DOCUMENTS_PATH, process_document)

    if not observer:
        logger.error("Failed to start file watcher")
        sys.exit(1)

    # Step 4: Keep running until interrupted
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        if observer:
            stop_watching(observer)
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
