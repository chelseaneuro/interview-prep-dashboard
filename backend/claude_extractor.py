import json
import re
import time
from anthropic import Anthropic
from backend import config
from backend.utils import setup_logger

logger = setup_logger(__name__)


def extract_career_info(text, document_type="general"):
    """
    Main extraction function - sends text to Claude API for intelligent extraction.

    Args:
        text: Raw document text
        document_type: Type of document (resume, cover_letter, application, etc.)

    Returns:
        dict: {
            "success": bool,
            "data": dict (extracted career information),
            "error": str or None
        }
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for extraction")
        return {
            "success": False,
            "data": {},
            "error": "No text content to extract"
        }

    # Build the prompt
    prompt = build_extraction_prompt(text, document_type)

    # Call Claude API
    api_response = call_claude_api(prompt)

    if not api_response["success"]:
        return {
            "success": False,
            "data": {},
            "error": api_response["error"]
        }

    # Parse the response
    parsed_response = parse_claude_response(api_response["text"])

    return parsed_response


def build_extraction_prompt(text, document_type):
    """
    Create structured prompt for Claude API based on document type.

    Args:
        text: Document text
        document_type: Type of document

    Returns:
        str: Formatted prompt
    """
    base_prompt = f"""Analyze this {document_type} and extract structured career information.

Instructions:
- Extract ALL work experience with complete details (company, role, dates, responsibilities, achievements, technologies)
- Identify technical and soft skills
- Capture education with full details (degree, school, field, dates, gpa, honors)
- Find projects if mentioned (name, description, technologies, outcomes)
- For job applications, extract company, position, date applied, status
- For dates, use YYYY-MM format if month is known, otherwise YYYY
- For current positions, use null for end_date and set is_current: true
- If information is not present in the document, omit that field rather than guessing

Document text:
{text}

Return ONLY valid JSON matching this exact schema (omit empty arrays):
{{
  "work_experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or null",
      "is_current": false,
      "location": "City, State/Country",
      "responsibilities": ["responsibility 1", "responsibility 2"],
      "achievements": ["achievement 1", "achievement 2"],
      "technologies": ["tech1", "tech2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "field_of_study": "Major/Field",
      "school": "School Name",
      "location": "City, State/Country",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM",
      "gpa": "3.8",
      "honors": ["honor1", "honor2"],
      "relevant_coursework": ["course1", "course2"]
    }}
  ],
  "skills": {{
    "technical": {{
      "programming_languages": [],
      "frameworks": [],
      "databases": [],
      "cloud_platforms": [],
      "tools": [],
      "concepts": []
    }},
    "soft_skills": [],
    "languages": [
      {{"language": "English", "proficiency": "Native"}}
    ],
    "certifications": [
      {{
        "name": "Cert Name",
        "issuer": "Issuer",
        "date_obtained": "YYYY-MM",
        "expiry_date": "YYYY-MM or null"
      }}
    ]
  }},
  "projects": [
    {{
      "name": "Project Name",
      "description": "Brief description",
      "role": "Your role",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or null",
      "technologies": ["tech1", "tech2"],
      "outcomes": ["outcome1", "outcome2"],
      "github_url": "url or null",
      "demo_url": "url or null"
    }}
  ],
  "job_applications": [
    {{
      "company": "Company Name",
      "position": "Position Title",
      "date_applied": "YYYY-MM-DD",
      "status": "Applied/Interview/Offer/Rejected",
      "job_url": "url or null",
      "application_deadline": "YYYY-MM-DD or null",
      "notes": "Any notes"
    }}
  ],
  "personal_info": {{
    "name": "Full Name or null",
    "email": "email or null",
    "phone": "phone or null",
    "location": "City, State or null",
    "linkedin": "url or null",
    "github": "url or null",
    "portfolio": "url or null"
  }}
}}

Remember: Return ONLY the JSON object, no additional text or markdown formatting."""

    return base_prompt


def call_claude_api(prompt, max_retries=3):
    """
    Make API request to Claude with retry logic.

    Args:
        prompt: The prompt to send
        max_retries: Maximum number of retry attempts

    Returns:
        dict: {
            "success": bool,
            "text": str (response text),
            "error": str or None,
            "usage": dict or None
        }
    """
    if not config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set in environment")
        return {
            "success": False,
            "text": "",
            "error": "API key not configured",
            "usage": None
        }

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    for attempt in range(max_retries):
        try:
            logger.debug(f"Calling Claude API (attempt {attempt + 1}/{max_retries})")

            message = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=config.CLAUDE_MAX_TOKENS,
                temperature=config.CLAUDE_TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = message.content[0].text

            logger.info("Claude API call successful")
            logger.debug(f"Response length: {len(response_text)} characters")

            return {
                "success": True,
                "text": response_text,
                "error": None,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Claude API error (attempt {attempt + 1}/{max_retries}): {str(e)}")

            # If this was the last attempt, return error
            if attempt == max_retries - 1:
                return {
                    "success": False,
                    "text": "",
                    "error": str(e),
                    "usage": None
                }

            # Exponential backoff before retry
            wait_time = 2 ** attempt
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    return {
        "success": False,
        "text": "",
        "error": "Max retries exceeded",
        "usage": None
    }


def parse_claude_response(response_text):
    """
    Parse and validate Claude's JSON response.

    Args:
        response_text: Raw response from Claude

    Returns:
        dict: {
            "success": bool,
            "data": dict (parsed JSON),
            "error": str or None
        }
    """
    try:
        # Sometimes Claude includes markdown code blocks
        # Try to extract JSON from code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```',
                              response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text

        # Parse JSON
        data = json.loads(json_str)

        # Validate basic schema structure
        validate_extraction_schema(data)

        logger.info("Successfully parsed Claude response")
        return {
            "success": True,
            "data": data,
            "error": None
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        logger.debug(f"Response text: {response_text[:500]}")
        return {
            "success": False,
            "data": {},
            "error": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error parsing response: {str(e)}")
        return {
            "success": False,
            "data": {},
            "error": str(e)
        }


def validate_extraction_schema(data):
    """
    Validate that extracted data has expected structure.

    Args:
        data: Parsed JSON data

    Raises:
        ValueError: If schema is invalid
    """
    # Check that data is a dict
    if not isinstance(data, dict):
        raise ValueError("Response must be a JSON object")

    # Optional validation of expected fields
    # (we're lenient here - fields can be missing or empty)
    expected_keys = ["work_experience", "education", "skills", "projects", "job_applications"]

    # Log if expected keys are missing
    for key in expected_keys:
        if key not in data:
            logger.debug(f"Optional field '{key}' not present in extraction")


def merge_extractions(existing_data, new_data):
    """
    Intelligently merge new extraction data with existing profile.

    Note: This is a simple implementation. A production version would
    use more sophisticated deduplication and conflict resolution.

    Args:
        existing_data: Current profile data
        new_data: New extracted data

    Returns:
        dict: Merged data
    """
    # For now, we'll append new items to existing lists
    # This will be enhanced in data_manager.py

    merged = existing_data.copy()

    # Merge work experience
    if "work_experience" in new_data and new_data["work_experience"]:
        if "work_experience" not in merged:
            merged["work_experience"] = []
        merged["work_experience"].extend(new_data["work_experience"])

    # Merge education
    if "education" in new_data and new_data["education"]:
        if "education" not in merged:
            merged["education"] = []
        merged["education"].extend(new_data["education"])

    # Merge projects
    if "projects" in new_data and new_data["projects"]:
        if "projects" not in merged:
            merged["projects"] = []
        merged["projects"].extend(new_data["projects"])

    # Merge job applications
    if "job_applications" in new_data and new_data["job_applications"]:
        if "job_applications" not in merged:
            merged["job_applications"] = []
        merged["job_applications"].extend(new_data["job_applications"])

    # Merge skills (combine lists, remove duplicates)
    if "skills" in new_data and new_data["skills"]:
        if "skills" not in merged:
            merged["skills"] = {
                "technical": {},
                "soft_skills": [],
                "languages": [],
                "certifications": []
            }

        # Merge technical skills
        if "technical" in new_data["skills"]:
            for category, items in new_data["skills"]["technical"].items():
                if category not in merged["skills"]["technical"]:
                    merged["skills"]["technical"][category] = []
                if isinstance(items, list):
                    merged["skills"]["technical"][category].extend(items)
                    # Remove duplicates
                    merged["skills"]["technical"][category] = list(set(merged["skills"]["technical"][category]))

        # Merge soft skills
        if "soft_skills" in new_data["skills"]:
            merged["skills"]["soft_skills"].extend(new_data["skills"]["soft_skills"])
            merged["skills"]["soft_skills"] = list(set(merged["skills"]["soft_skills"]))

    # Update personal info (prefer non-empty values)
    if "personal_info" in new_data and new_data["personal_info"]:
        if "personal_info" not in merged:
            merged["personal_info"] = {}

        for key, value in new_data["personal_info"].items():
            if value and value != "null":
                merged["personal_info"][key] = value

    return merged
