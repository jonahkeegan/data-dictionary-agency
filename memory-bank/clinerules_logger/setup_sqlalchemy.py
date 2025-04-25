#!/usr/bin/env python3
"""
Setup script for clinerules_logger SQLAlchemy integration.
This script creates a virtual environment, installs required dependencies,
configures Python paths, and initializes the SQLite database.
"""

import os
import sys
import subprocess
import platform
import site
import shutil
from pathlib import Path

# Determine the current script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# Environment directory names by platform
VENV_DIRS = {
    "Windows": "venv",
    "Linux": ".venv",
    "Darwin": ".venv"  # macOS
}

# Python executables by platform
PYTHON_EXES = {
    "Windows": "python.exe",
    "Linux": "python",
    "Darwin": "python"  # macOS
}

def print_step(message):
    """Print a step message with formatting."""
    print(f"\n{'=' * 80}")
    print(f"  {message}")
    print(f"{'=' * 80}\n")

def create_virtual_environment():
    """Create a Python virtual environment."""
    print_step("Creating virtual environment")
    
    system = platform.system()
    venv_dir = VENV_DIRS.get(system, ".venv")
    venv_path = os.path.join(SCRIPT_DIR, venv_dir)
    
    # Check if virtual environment already exists
    if os.path.exists(venv_path):
        response = input(f"Virtual environment already exists at {venv_path}. Recreate? (y/n): ")
        if response.lower() == 'y':
            shutil.rmtree(venv_path)
        else:
            print(f"Using existing virtual environment at {venv_path}")
            return venv_path
    
    try:
        # Create virtual environment
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])
        print(f"Virtual environment created at: {venv_path}")
        return venv_path
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

def install_dependencies(venv_path):
    """Install required dependencies in the virtual environment."""
    print_step("Installing dependencies")
    
    system = platform.system()
    python_exe = os.path.join(venv_path, "Scripts" if system == "Windows" else "bin", PYTHON_EXES.get(system, "python"))
    requirements_path = os.path.join(SCRIPT_DIR, "requirements.txt")
    
    try:
        # Upgrade pip
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install dependencies from requirements.txt
        subprocess.check_call([python_exe, "-m", "pip", "install", "-r", requirements_path])
        
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def create_pth_file(venv_path):
    """Create a .pth file to add project root to Python path."""
    print_step("Configuring Python path")
    
    system = platform.system()
    if system == "Windows":
        site_packages = os.path.join(venv_path, "Lib", "site-packages")
    else:
        # For Linux and macOS, the directory structure is different
        # Get python version in the format 'python3.x'
        python_exe = os.path.join(venv_path, "bin", "python")
        python_version = subprocess.check_output(
            [python_exe, "-c", "import sys; print(f'python{sys.version_info.major}.{sys.version_info.minor}')"],
            universal_newlines=True
        ).strip()
        site_packages = os.path.join(venv_path, "lib", python_version, "site-packages")
    
    # Ensure the site-packages directory exists
    if not os.path.exists(site_packages):
        print(f"Site-packages directory not found at: {site_packages}")
        return False
    
    # Create a .pth file with the project root
    pth_file = os.path.join(site_packages, "clinerules_logger.pth")
    
    with open(pth_file, "w") as f:
        f.write(PROJECT_ROOT)
    
    print(f"Python path configured via: {pth_file}")
    return True

def initialize_database(venv_path):
    """Initialize the SQLite database."""
    print_step("Initializing database")
    
    system = platform.system()
    python_exe = os.path.join(venv_path, "Scripts" if system == "Windows" else "bin", PYTHON_EXES.get(system, "python"))
    
    # Prepare data directories
    data_dir = os.path.join(SCRIPT_DIR, "data")
    backup_dir = os.path.join(SCRIPT_DIR, "backup", "data")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create a temporary initialization script
    init_script = os.path.join(SCRIPT_DIR, "_temp_init_db.py")
    
    with open(init_script, "w") as f:
        f.write("""
import sys
import os
import importlib.util
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Get absolute paths to other needed modules
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
schema_path = os.path.join(db_dir, "schema.py")
manager_path = os.path.join(db_dir, "manager.py")

# Function to load python modules from file paths
def load_module_from_path(module_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not load spec for {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

try:
    # Dynamically load modules
    print("Loading schema module...")
    schema = load_module_from_path(schema_path, "schema")
    
    print("Loading manager module...")
    # First delay-load utils.config that manager depends on
    utils_dir = os.path.join(current_dir, "utils")
    config_path = os.path.join(utils_dir, "config.py")
    config_module = load_module_from_path(config_path, "config")
    sys.modules["config"] = config_module
    
    # Now load manager with config already loaded
    manager = load_module_from_path(manager_path, "manager")
    
    # Initialize database
    print("Creating database tables...")
    schema.create_tables(manager.db_manager._engine)
    
    # Import legacy log data if available
    print("Importing legacy log data...")
    manager.db_manager.import_legacy_log()
    
    print("Database initialization complete.")
except Exception as e:
    print(f"Error initializing database: {e}")
    print("\\nDebug information:")
    print(f"Project root: {project_root}")
    print(f"DB directory: {db_dir}")
    print(f"Schema path: {schema_path}")
    print(f"Manager path: {manager_path}")
    print(f"Python version: {sys.version}")
    print(f"sys.path: {sys.path}")
    # Include traceback for better debugging
    import traceback
    traceback.print_exc()
""")
    
    try:
        # Run the initialization script
        subprocess.check_call([python_exe, init_script])
        
        # Clean up
        os.remove(init_script)
        
        print("Database initialized successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error initializing database: {e}")
        # Clean up even if there's an error
        if os.path.exists(init_script):
            os.remove(init_script)
        return False

def print_activation_instructions(venv_path):
    """Print instructions for activating the virtual environment."""
    print_step("Activation Instructions")
    
    system = platform.system()
    if system == "Windows":
        activate_script = os.path.join(venv_path, "Scripts", "activate")
        print(f"To activate the virtual environment, run:\n\n    {activate_script}\n")
    else:
        activate_script = os.path.join(venv_path, "bin", "activate")
        print(f"To activate the virtual environment, run:\n\n    source {activate_script}\n")
    
    print("After activation, you can run the enhanced clinerules logger:")
    print("    python memory-bank/clinerules_logger/main.py\n")
    print("Or import it in your Python code:")
    print("    from memory_bank.clinerules_logger.db.manager import db_manager\n")

def main():
    """Main setup function."""
    print_step("SQLAlchemy Integration Setup for clinerules_logger")
    
    # Verify Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("Error: Python 3.7 or later is required.")
        sys.exit(1)
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    
    # Install dependencies
    if not install_dependencies(venv_path):
        print("Error: Failed to install dependencies.")
        sys.exit(1)
    
    # Configure Python path
    if not create_pth_file(venv_path):
        print("Warning: Failed to configure Python path. You may need to set PYTHONPATH manually.")
    
    # Initialize database
    if not initialize_database(venv_path):
        print("Error: Failed to initialize database.")
        sys.exit(1)
    
    # Print activation instructions
    print_activation_instructions(venv_path)
    
    print_step("Setup complete!")
    print("You can now use the enhanced clinerules logger with SQLAlchemy integration.")

if __name__ == "__main__":
    main()
