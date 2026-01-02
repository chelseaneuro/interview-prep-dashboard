#!/bin/bash
set -e

echo "=== Interview Prep Dashboard - Phase 1 Setup ==="

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Error: Python 3 not found"; exit 1; }

# Create directory structure
echo "Creating project structure..."
mkdir -p /home/haysc/interview-prep/{backend,data/raw_extractions,logs,tests}
mkdir -p /home/haysc/Documents

# Create __init__.py files
touch /home/haysc/interview-prep/backend/__init__.py
touch /home/haysc/interview-prep/tests/__init__.py

# Install dependencies
echo "Installing Python dependencies..."
cd /home/haysc/interview-prep
python3 -m pip install --break-system-packages -r requirements.txt

# Create .env from example if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
    echo "Get your API key from: https://console.anthropic.com/"
else
    echo ".env file already exists"
fi

# Initialize data files
echo "Initializing data files..."
cat > data/profile.json <<'EOF'
{
  "metadata": {
    "version": "1.0",
    "last_updated": null,
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
EOF

cat > data/documents_processed.json <<'EOF'
{
  "documents": []
}
EOF

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your ANTHROPIC_API_KEY"
echo "   -> Get your API key from: https://console.anthropic.com/"
echo "2. Run the scanner: python3 backend/main.py"
echo "3. Add documents to ~/Documents to start processing"
echo ""
