#!/bin/bash
# Navigate to the python_microservice directory
cd /Users/benjaminfenison/Desktop/scalpel_app/python_microservice

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt

# Set the OPENAI_API_KEY environment variable
export OPENAI_API_KEY=sk-krDgakZDZGiAMLYBNgNY1yXMiIvGCF2025wWCQByQeT3BlbkFJLQqZ3LsaD3EguAawmLOq-_HEs3rg3jaThWtpsBeroA

# Start the FastAPI server
uvicorn app:app --host 0.0.0.0 --port 8000
