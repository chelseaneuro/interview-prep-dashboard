import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "/home/haysc/Documents")
DATA_PATH = os.getenv("DATA_PATH", "/home/haysc/interview-prep/data")
LOGS_PATH = os.getenv("LOGS_PATH", "/home/haysc/interview-prep/logs")

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"
CLAUDE_MAX_TOKENS = 4096
CLAUDE_TEMPERATURE = 0.3

# File Processing
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt"]
MAX_FILE_SIZE_MB = 50
DEBOUNCE_SECONDS = 2

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
