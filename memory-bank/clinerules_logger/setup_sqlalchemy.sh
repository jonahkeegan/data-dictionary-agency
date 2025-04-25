#!/bin/bash
# Setup script for clinerules_logger SQLAlchemy integration on Linux/macOS

echo "Setting up SQLAlchemy integration for clinerules_logger..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    echo "Please install Python 3.7 or later and try again."
    exit 1
fi

# Make sure the script is executable
chmod +x setup_sqlalchemy.py

# Run the Python setup script
python3 setup_sqlalchemy.py
if [ $? -ne 0 ]; then
    echo "Setup failed. Please check the error messages above."
    exit 1
fi

echo
echo "Setup completed successfully!"
echo
echo "To use the enhanced clinerules logger, you need to:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Run the logger: python memory-bank/clinerules_logger/main.py"
echo
