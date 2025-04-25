#!/usr/bin/env python3
"""
Installation script for the enhanced .clinerules logger system.
"""

import os
import sys
import subprocess
import importlib.util

def check_module(module_name):
    """Check if a Python module is installed."""
    return importlib.util.find_spec(module_name) is not None

def install_requirements():
    """Install required packages."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.join(current_dir, "requirements.txt")
    
    if not os.path.exists(requirements_path):
        print(f"Error: Requirements file not found at {requirements_path}")
        return False
    
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def initialize_database():
    """Initialize the database."""
    try:
        # Set up Python path to find the package
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Import modules using the correct path structure
        # First try with hyphen (directory structure)
        try:
            from memory_bank.clinerules_logger.db.manager import db_manager
            from memory_bank.clinerules_logger.trackers.context_window import context_tracker
            from memory_bank.clinerules_logger.backup.manager import backup_manager
        except ImportError:
            # Then try with underscore (Python package naming convention)
            try:
                from memory_bank.clinerules_logger.db.manager import db_manager
                from memory_bank.clinerules_logger.trackers.context_window import context_tracker
                from memory_bank.clinerules_logger.backup.manager import backup_manager
            except ImportError:
                # Last resort, try relative imports
                sys.path.insert(0, os.path.dirname(os.path.dirname(current_dir)))
                from memory_bank.clinerules_logger.db.manager import db_manager
                from memory_bank.clinerules_logger.trackers.context_window import context_tracker
                from memory_bank.clinerules_logger.backup.manager import backup_manager
        
        # Initialize data directory
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Import legacy log data
        db_manager.import_legacy_log()
        
        print("Database initialized successfully.")
        return True
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("\nTo fix import issues, try running the script as a module:")
        print("cd path/to/project/root")
        print("python -m memory_bank.clinerules_logger.install")
        return False
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def main():
    """Main installation function."""
    print("Enhanced .clinerules Logger System Installer")
    print("------------------------------------------")
    
    # Create necessary directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dirs_to_create = [
        os.path.join(current_dir, "data"),
        os.path.join(current_dir, "backup", "data")
    ]
    
    for directory in dirs_to_create:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Check for required modules
    required_modules = ["sqlalchemy", "schedule"]
    missing_modules = [module for module in required_modules if not check_module(module)]
    
    if missing_modules:
        print(f"Missing required modules: {', '.join(missing_modules)}")
        install_dependencies = input("Install missing dependencies? (y/n): ").strip().lower()
        
        if install_dependencies == 'y':
            if not install_requirements():
                print("Installation of dependencies failed. Please install them manually.")
                return False
        else:
            print("Please install the required dependencies manually.")
            return False
    
    # Initialize database
    print("\nInitializing the database...")
    success = initialize_database()
    if not success:
        print("\nAlternative initialization method:")
        print("1. Open Python interpreter in the project root")
        print("2. Run the following code:")
        print("   >>> from memory_bank.clinerules_logger.db.manager import db_manager")
        print("   >>> db_manager.import_legacy_log()")
        return False
    
    print("\nInstallation completed successfully!")
    print("\nYou can now use the enhanced .clinerules logger system. Try running:")
    print("python memory-bank/clinerules_logger/main.py")
    print("\nOr check out the SQLAlchemy integration guide:")
    print("memory-bank/clinerules_logger/SQLAlchemy_Integration_Guide.md")
    
    return True

if __name__ == "__main__":
    main()
