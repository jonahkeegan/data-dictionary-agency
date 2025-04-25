#!/bin/bash
# Setup script for the Enhanced .clinerules Logger System

echo "Setting up the Enhanced .clinerules Logger System..."
echo ""

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "Project root directory: $PROJECT_ROOT"
echo ""

# Make sure we're in the project root for proper module imports
cd "$PROJECT_ROOT"

echo "Installing dependencies..."
# Run the installation script as a module
python -m memory_bank.clinerules_logger.install

echo ""
echo "To test the system, run:"
echo "python -m memory_bank.clinerules_logger.examples"
echo ""
echo "To use the enhanced logger:"
echo "python -m memory_bank.clinerules_logger.main [command]"
echo ""
echo "Or use the backward-compatible interface:"
echo "python memory-bank/clinerules_logger.py"
