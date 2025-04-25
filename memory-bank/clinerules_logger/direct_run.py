#!/usr/bin/env python3
"""
Direct execution wrapper for clinerules_logger.

This file provides a simple entry point for directly running the clinerules_logger
without package installation. It handles import paths and calls the main functionality.
"""

import os
import sys
import importlib.util

# Add the parent directory to sys.path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Function to load module from file path
def load_module_from_path(module_path, module_name):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not load spec for {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import main module directly from file
main_path = os.path.join(current_dir, "main.py")
main_module = load_module_from_path(main_path, "main")

# Fix import paths for key modules
db_dir = os.path.join(current_dir, "db")
trackers_dir = os.path.join(current_dir, "trackers")
utils_dir = os.path.join(current_dir, "utils")
integrations_dir = os.path.join(current_dir, "integrations")

for directory in [db_dir, trackers_dir, utils_dir, integrations_dir]:
    if os.path.exists(directory) and directory not in sys.path:
        sys.path.insert(0, directory)

if __name__ == "__main__":
    # Forward command-line arguments
    sys.argv = [sys.argv[0]] + sys.argv[1:]
    
    # Run the main function
    if hasattr(main_module, 'main'):
        main_module.main()
    else:
        print("Error: main function not found in main.py")
