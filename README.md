# Job Search Interview Prep Dashboard - Phase 1

Automated career document scanner that uses Claude AI to extract and structure information from resumes, cover letters, and job applications.

## Overview

This system automatically monitors your Documents folder, extracts career-related information using Claude's AI, and stores it as structured JSON data. It intelligently processes PDFs, DOCX files, and text documents to build a comprehensive profile of your work experience, education, skills, projects, and job applications.

## Features

- **Automatic Document Scanning**: Monitors ~/Documents for new career-related files
- **Intelligent AI Extraction**: Uses Claude API to understand and structure document content
- **Multi-Format Support**: Handles PDF, DOCX, and TXT files
- **Real-Time Monitoring**: Automatically processes new documents as they're added
- **Duplicate Detection**: Smart merging prevents duplicate entries
- **Structured Data Storage**: Saves everything as clean, queryable JSON
- **Comprehensive Logging**: Tracks all processing with detailed logs

## Prerequisites

- **Python 3.12+**
- **Anthropic API Key**: Get yours at [console.anthropic.com](https://console.anthropic.com/)

## Quick Start

### 1. Run Setup

```bash
cd /home/haysc/interview-prep
bash setup.sh
```

This will:
- Install Python dependencies
- Create necessary directories
- Initialize data files
- Create a .env configuration file

### 2. Configure API Key

Edit the `.env` file and add your Anthropic API key:

```bash
nano .env
```

Update this line:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### 3. Start the Scanner

```bash
python3 backend/main.py
```

The scanner will:
1. Process any existing documents in ~/Documents
2. Start monitoring for new documents
3. Automatically extract and save career information

### 4. Add Documents

Simply copy your career documents to ~/Documents:
- Resumes (PDF, DOCX, TXT)
- Cover letters
- Job application records
- Project descriptions

The system will automatically detect and process them!

## Project Structure

```
interview-prep/
├── backend/
│   ├── main.py              # Main entry point
│   ├── config.py            # Configuration management
│   ├── utils.py             # Helper utilities
│   ├── document_scanner.py  # File discovery
│   ├── document_parser.py   # Text extraction
│   ├── claude_extractor.py  # AI extraction
│   ├── data_manager.py      # JSON storage
│   └── file_watcher.py      # Auto-monitoring
├── data/
│   ├── profile.json         # Your structured career data
│   ├── documents_processed.json  # Processing history
│   └── raw_extractions/     # Optional raw data
├── logs/
│   └── scanner.log          # Application logs
├── .env                     # Configuration (API keys)
├── .env.example             # Configuration template
├── requirements.txt         # Python dependencies
├── setup.sh                 # Setup script
└── README.md                # This file
```

## Data Schema

Your extracted career information is saved in `data/profile.json`:

```json
{
  "metadata": {
    "version": "1.0",
    "last_updated": "2025-01-01T12:00:00Z",
    "total_documents_processed": 5
  },
  "personal_info": {
    "name": "Your Name",
    "email": "your.email@example.com",
    "phone": "+1-234-567-8900",
    "location": "City, State",
    "linkedin": "linkedin.com/in/yourprofile",
    "github": "github.com/yourusername"
  },
  "work_experience": [
    {
      "id": "unique-id",
      "company": "Company Name",
      "role": "Job Title",
      "start_date": "2020-06",
      "end_date": "2023-08",
      "is_current": false,
      "location": "City, State",
      "responsibilities": ["..."],
      "achievements": ["..."],
      "technologies": ["Python", "React", "AWS"],
      "extracted_date": "2025-01-01T12:00:00Z"
    }
  ],
  "education": [...],
  "skills": {
    "technical": {
      "programming_languages": ["Python", "JavaScript"],
      "frameworks": ["React", "FastAPI"],
      "databases": ["PostgreSQL", "MongoDB"],
      "cloud_platforms": ["AWS", "GCP"],
      "tools": ["Docker", "Git"],
      "concepts": ["Microservices", "CI/CD"]
    },
    "soft_skills": ["Leadership", "Communication"],
    "languages": [{"language": "English", "proficiency": "Native"}],
    "certifications": [...]
  },
  "projects": [...],
  "job_applications": [...]
}
```

## Configuration

Edit `.env` to customize settings:

```bash
# Claude API Configuration
ANTHROPIC_API_KEY=your_api_key_here

# Paths
DOCUMENTS_PATH=/home/haysc/Documents
DATA_PATH=/home/haysc/interview-prep/data
LOGS_PATH=/home/haysc/interview-prep/logs

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## How It Works

### Document Processing Pipeline

1. **File Detection**: Watchdog monitors ~/Documents for new/modified files
2. **Validation**: Checks file type, size, and readability
3. **Text Extraction**:
   - PDFs: PyPDF2 extracts text
   - DOCX: python-docx reads content
   - TXT: Direct file read
4. **AI Analysis**: Claude API intelligently extracts structured information
5. **Smart Merging**: Detects duplicates and merges new data with existing profile
6. **Storage**: Saves updated profile to JSON with atomic writes

### Duplicate Detection

The system intelligently prevents duplicates:
- **Work Experience**: Matches by company name (fuzzy) + role + dates
- **Education**: Matches by school + degree
- **Skills**: Deduplicates by name (case-insensitive)
- **Projects**: Matches by project name

### Error Handling

- Corrupt files: Logged and skipped
- API failures: Retried with exponential backoff
- Processing errors: Logged but don't stop the system
- File conflicts: Detected via hash comparison

## Viewing Your Data

### Pretty-print your profile:
```bash
python3 -m json.tool data/profile.json
```

### Check processing history:
```bash
cat data/documents_processed.json
```

### View logs:
```bash
tail -f logs/scanner.log
```

## Troubleshooting

### "ANTHROPIC_API_KEY not configured!"
- Make sure you've edited `.env` and added your API key
- Verify there are no extra spaces around the key

### "No module named 'PyPDF2'" or similar
- Run `bash setup.sh` again to install dependencies
- Or manually: `python3 -m pip install --break-system-packages -r requirements.txt`

### Documents not being processed
- Check file extensions (.pdf, .docx, .txt only)
- Verify files are in ~/Documents (or configured path)
- Check logs: `tail -f logs/scanner.log`
- Ensure API key is valid

### "File too large" warnings
- Default limit is 50MB
- Adjust in config.py: `MAX_FILE_SIZE_MB`

### Extraction quality issues
- The system learns from document structure
- Well-formatted resumes work best
- Check extracted data in `data/profile.json`
- Prompts can be refined in `claude_extractor.py`

## Next Steps - Phase 2 & 3

This completes Phase 1: Document Scanner & Profile Builder.

**Phase 2 (Planned)**: React web dashboard to visualize and interact with your data

**Phase 3 (Planned)**: Interview preparation features:
- Generate practice interview questions based on your profile
- Craft tailored responses using your actual experiences
- Job-specific response customization

## API Costs

Typical usage with Claude 3.5 Sonnet:
- ~$0.01-0.03 per document processed
- Input: $3 per million tokens
- Output: $15 per million tokens

A typical resume uses ~1,000-3,000 input tokens and generates ~1,000-2,000 output tokens.

## Support

For issues or questions:
- Check logs in `logs/scanner.log`
- Review error messages in console output
- Verify .env configuration
- Ensure API key has sufficient credits

## License

This is a personal project. Adapt and use as needed for your job search!

---

Built with Claude 3.5 Sonnet | Phase 1 Complete
