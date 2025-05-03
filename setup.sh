#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt

# Set the OPENAI_API_KEY environment variable
export OPENAI_API_KEY='sk-krDgakZDZGiAMLYBNgNY1yXMiIvGCF2025wWCQByQeT3BlbkFJLQqZ3LsaD3EguAawmLOq-_HEs3rg3jaThWtpsBeroA'

# Start the FastAPI server
uvicorn app:app --host 0.0.0.0 --port 8000

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
