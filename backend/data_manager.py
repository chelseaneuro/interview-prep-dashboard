import json
import os
import uuid
from datetime import datetime
from backend import config
from backend.utils import setup_logger, fuzzy_match_company

logger = setup_logger(__name__)


def load_profile():
    """
    Load existing profile.json or create new one.

    Returns:
        dict: Profile data
    """
    profile_path = os.path.join(config.DATA_PATH, "profile.json")

    try:
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = json.load(f)
                logger.info("Loaded existing profile")
                return profile
        else:
            logger.info("No existing profile found, creating new one")
            return create_empty_profile()

    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        logger.info("Creating new profile")
        return create_empty_profile()


def create_empty_profile():
    """
    Create empty profile structure.

    Returns:
        dict: Empty profile
    """
    return {
        "metadata": {
            "version": "1.0",
            "last_updated": None,
            "total_documents_processed": 0
        },
        "personal_info": {},
        "work_experience": [],
        "education": [],
        "skills": {
            "technical": {},
            "soft_skills": [],
            "languages": [],
            "certifications": []
        },
        "projects": [],
        "job_applications": []
    }


def save_profile(data):
    """
    Save profile data with atomic write.

    Args:
        data: Profile data to save

    Returns:
        bool: True if successful
    """
    profile_path = os.path.join(config.DATA_PATH, "profile.json")
    temp_path = profile_path + ".tmp"

    try:
        # Ensure data directory exists
        os.makedirs(config.DATA_PATH, exist_ok=True)

        # Update metadata
        data["metadata"]["last_updated"] = datetime.now().isoformat()

        # Write to temporary file first
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)

        # Atomic rename
        os.replace(temp_path, profile_path)

        logger.info("Profile saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving profile: {str(e)}")
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False


def load_processed_documents():
    """
    Get list of already processed documents.

    Returns:
        dict: Processed documents data
    """
    processed_path = os.path.join(config.DATA_PATH, "documents_processed.json")

    try:
        if os.path.exists(processed_path):
            with open(processed_path, 'r') as f:
                data = json.load(f)
                return data
        else:
            return {"documents": []}

    except Exception as e:
        logger.error(f"Error loading processed documents: {str(e)}")
        return {"documents": []}


def mark_document_as_processed(file_path, file_hash, metadata, extraction_result):
    """
    Track that a document has been processed.

    Args:
        file_path: Path to document
        file_hash: Hash of file contents
        metadata: Document metadata
        extraction_result: Results from extraction

    Returns:
        bool: True if successful
    """
    processed_path = os.path.join(config.DATA_PATH, "documents_processed.json")

    try:
        data = load_processed_documents()

        # Check if document already in list (update if so)
        existing_idx = None
        for idx, doc in enumerate(data["documents"]):
            if doc["file_path"] == file_path:
                existing_idx = idx
                break

        doc_entry = {
            "file_path": file_path,
            "file_hash": file_hash,
            "processed_date": datetime.now().isoformat(),
            "document_category": metadata.get("document_category", "general"),
            "extraction_success": extraction_result.get("success", False),
            "items_extracted": {}
        }

        # Count extracted items
        if extraction_result.get("success") and extraction_result.get("data"):
            extracted_data = extraction_result["data"]
            doc_entry["items_extracted"] = {
                "work_experience": len(extracted_data.get("work_experience", [])),
                "education": len(extracted_data.get("education", [])),
                "projects": len(extracted_data.get("projects", [])),
                "job_applications": len(extracted_data.get("job_applications", []))
            }

        if existing_idx is not None:
            data["documents"][existing_idx] = doc_entry
        else:
            data["documents"].append(doc_entry)

        # Save
        os.makedirs(config.DATA_PATH, exist_ok=True)
        with open(processed_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Marked document as processed: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error marking document as processed: {str(e)}")
        return False


def is_document_processed(file_path, file_hash):
    """
    Check if document has already been processed with this hash.

    Args:
        file_path: Path to document
        file_hash: Current file hash

    Returns:
        bool: True if already processed and unchanged
    """
    try:
        data = load_processed_documents()

        for doc in data["documents"]:
            if doc["file_path"] == file_path:
                # Check if hash matches (file unchanged)
                if doc["file_hash"] == file_hash:
                    return True
                else:
                    # File has changed, should reprocess
                    return False

        # Not in processed list
        return False

    except Exception as e:
        logger.error(f"Error checking if document processed: {str(e)}")
        return False


def merge_career_data(existing, new):
    """
    Intelligently merge new extraction with existing profile.

    Uses fuzzy matching to detect duplicates and merge intelligently.

    Args:
        existing: Current profile data
        new: New extracted data

    Returns:
        dict: Merged profile data
    """
    merged = existing.copy()

    # Merge work experience (with duplicate detection)
    if "work_experience" in new and new["work_experience"]:
        if "work_experience" not in merged:
            merged["work_experience"] = []

        for new_exp in new["work_experience"]:
            # Add unique ID if not present
            if "id" not in new_exp:
                new_exp["id"] = str(uuid.uuid4())

            # Add source and extraction metadata
            new_exp["extracted_date"] = datetime.now().isoformat()

            # Check for duplicates
            is_duplicate = False
            for existing_exp in merged["work_experience"]:
                if is_duplicate_work_experience(existing_exp, new_exp):
                    logger.info(f"Duplicate work experience found: {new_exp.get('company')} - {new_exp.get('role')}")
                    is_duplicate = True
                    break

            if not is_duplicate:
                merged["work_experience"].append(new_exp)
                logger.info(f"Added new work experience: {new_exp.get('company')} - {new_exp.get('role')}")

    # Merge education (with duplicate detection)
    if "education" in new and new["education"]:
        if "education" not in merged:
            merged["education"] = []

        for new_edu in new["education"]:
            if "id" not in new_edu:
                new_edu["id"] = str(uuid.uuid4())

            new_edu["extracted_date"] = datetime.now().isoformat()

            # Check for duplicates
            is_duplicate = False
            for existing_edu in merged["education"]:
                if is_duplicate_education(existing_edu, new_edu):
                    logger.info(f"Duplicate education found: {new_edu.get('degree')} from {new_edu.get('school')}")
                    is_duplicate = True
                    break

            if not is_duplicate:
                merged["education"].append(new_edu)
                logger.info(f"Added new education: {new_edu.get('degree')} from {new_edu.get('school')}")

    # Merge projects
    if "projects" in new and new["projects"]:
        if "projects" not in merged:
            merged["projects"] = []

        for new_proj in new["projects"]:
            if "id" not in new_proj:
                new_proj["id"] = str(uuid.uuid4())

            new_proj["extracted_date"] = datetime.now().isoformat()

            # Simple duplicate check by name
            is_duplicate = any(
                proj.get("name", "").lower() == new_proj.get("name", "").lower()
                for proj in merged["projects"]
            )

            if not is_duplicate:
                merged["projects"].append(new_proj)
                logger.info(f"Added new project: {new_proj.get('name')}")

    # Merge job applications
    if "job_applications" in new and new["job_applications"]:
        if "job_applications" not in merged:
            merged["job_applications"] = []

        for new_app in new["job_applications"]:
            if "id" not in new_app:
                new_app["id"] = str(uuid.uuid4())

            new_app["extracted_date"] = datetime.now().isoformat()

            # Check for duplicate by company and position
            is_duplicate = any(
                fuzzy_match_company(app.get("company", ""), new_app.get("company", "")) and
                app.get("position", "").lower() == new_app.get("position", "").lower()
                for app in merged["job_applications"]
            )

            if not is_duplicate:
                merged["job_applications"].append(new_app)
                logger.info(f"Added new job application: {new_app.get('position')} at {new_app.get('company')}")

    # Merge skills
    if "skills" in new and new["skills"]:
        if "skills" not in merged:
            merged["skills"] = {
                "technical": {},
                "soft_skills": [],
                "languages": [],
                "certifications": []
            }

        # Merge technical skills (by category)
        if "technical" in new["skills"] and isinstance(new["skills"]["technical"], dict):
            if "technical" not in merged["skills"]:
                merged["skills"]["technical"] = {}

            for category, items in new["skills"]["technical"].items():
                if category not in merged["skills"]["technical"]:
                    merged["skills"]["technical"][category] = []

                if isinstance(items, list):
                    # Add new items, remove duplicates (case-insensitive)
                    existing_lower = [s.lower() for s in merged["skills"]["technical"][category]]
                    for item in items:
                        if item and item.lower() not in existing_lower:
                            merged["skills"]["technical"][category].append(item)
                            existing_lower.append(item.lower())

        # Merge soft skills
        if "soft_skills" in new["skills"]:
            if "soft_skills" not in merged["skills"]:
                merged["skills"]["soft_skills"] = []

            existing_lower = [s.lower() for s in merged["skills"]["soft_skills"]]
            for skill in new["skills"]["soft_skills"]:
                if skill and skill.lower() not in existing_lower:
                    merged["skills"]["soft_skills"].append(skill)
                    existing_lower.append(skill.lower())

        # Merge languages
        if "languages" in new["skills"]:
            if "languages" not in merged["skills"]:
                merged["skills"]["languages"] = []

            for new_lang in new["skills"]["languages"]:
                # Check if language already exists
                exists = any(
                    lang.get("language", "").lower() == new_lang.get("language", "").lower()
                    for lang in merged["skills"]["languages"]
                )
                if not exists:
                    merged["skills"]["languages"].append(new_lang)

        # Merge certifications
        if "certifications" in new["skills"]:
            if "certifications" not in merged["skills"]:
                merged["skills"]["certifications"] = []

            for new_cert in new["skills"]["certifications"]:
                # Check for duplicate by name
                exists = any(
                    cert.get("name", "").lower() == new_cert.get("name", "").lower()
                    for cert in merged["skills"]["certifications"]
                )
                if not exists:
                    merged["skills"]["certifications"].append(new_cert)

    # Merge personal info (prefer non-null new values)
    if "personal_info" in new and new["personal_info"]:
        if "personal_info" not in merged:
            merged["personal_info"] = {}

        for key, value in new["personal_info"].items():
            if value and value != "null" and value != "":
                # Only update if we don't have this info yet, or new value seems more complete
                if key not in merged["personal_info"] or not merged["personal_info"][key]:
                    merged["personal_info"][key] = value

    # Update metadata
    merged["metadata"]["total_documents_processed"] = merged["metadata"].get("total_documents_processed", 0) + 1

    return merged


def is_duplicate_work_experience(exp1, exp2):
    """
    Check if two work experiences are duplicates.

    Args:
        exp1: First work experience
        exp2: Second work experience

    Returns:
        bool: True if likely duplicates
    """
    # Check company name (fuzzy match)
    if not fuzzy_match_company(exp1.get("company", ""), exp2.get("company", "")):
        return False

    # Check role (exact match, case-insensitive)
    role1 = exp1.get("role", "").lower().strip()
    role2 = exp2.get("role", "").lower().strip()
    if role1 != role2:
        return False

    # Check date overlap
    start1 = exp1.get("start_date", "")
    start2 = exp2.get("start_date", "")

    # If start dates are very similar, likely duplicate
    if start1 and start2 and start1[:7] == start2[:7]:  # Compare YYYY-MM
        return True

    return False


def is_duplicate_education(edu1, edu2):
    """
    Check if two education entries are duplicates.

    Args:
        edu1: First education entry
        edu2: Second education entry

    Returns:
        bool: True if likely duplicates
    """
    # Check school name (case-insensitive, contains match)
    school1 = edu1.get("school", "").lower().strip()
    school2 = edu2.get("school", "").lower().strip()

    if not (school1 in school2 or school2 in school1):
        return False

    # Check degree
    degree1 = edu1.get("degree", "").lower().strip()
    degree2 = edu2.get("degree", "").lower().strip()

    if degree1 and degree2 and degree1 != degree2:
        return False

    # If we get here, likely duplicate
    return True
