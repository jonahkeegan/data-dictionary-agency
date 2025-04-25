#!/usr/bin/env python3
"""
Simplified setup script for clinerules_logger SQLAlchemy integration.
This script handles the basic setup requirements with minimal user interaction.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(message):
    """Print a formatted header message."""
    print(f"\n{message}")
    print("-" * len(message))

def setup_sqlalchemy():
    """Set up the SQLAlchemy integration with minimal steps."""
    print_header("Setting up SQLAlchemy integration for clinerules_logger")
    
    # Determine paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Create data directories
    print("Creating data directories...")
    os.makedirs(os.path.join(current_dir, "data"), exist_ok=True)
    os.makedirs(os.path.join(current_dir, "backup", "data"), exist_ok=True)
    
    # Install dependencies
    print_header("Installing dependencies")
    requirements_path = os.path.join(current_dir, "requirements.txt")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print("Please try installing the dependencies manually:")
        print(f"pip install -r {requirements_path}")
        return False
    
    # Initialize database
    print_header("Initializing database")
    
    # Add project root to Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        # Create a temporary script for database initialization
        init_script = os.path.join(current_dir, "_temp_init_db.py")
        
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
        
        # Execute the temporary script
        subprocess.check_call([sys.executable, init_script])
        
        # Clean up the temporary script
        os.remove(init_script)
        
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        print("\nYou may need to manually initialize the database:")
        print("1. Make sure your PYTHONPATH includes the project root")
        print("2. Run the following Python code:")
        print("   from memory_bank.clinerules_logger.db.schema import Base, create_tables")
        print("   from memory_bank.clinerules_logger.db.manager import db_manager")
        print("   create_tables(db_manager._engine)")
        print("   db_manager.import_legacy_log()")
        return False
    
    print_header("Setup complete!")
    print("You can now use the enhanced clinerules logger with SQLAlchemy integration.")
    print("\nUsage examples:")
    print("1. Command line: python memory-bank/clinerules_logger/main.py")
    print("2. Python import: from memory_bank.clinerules_logger.main import log_execution")
    print("\nFor more detailed information, see the SQLAlchemy_Integration_Guide.md")
    
    return True

if __name__ == "__main__":
    setup_sqlalchemy()
