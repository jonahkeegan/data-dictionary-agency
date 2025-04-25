#!/usr/bin/env python3
"""
Test script to verify SQLAlchemy integration is properly set up.
This performs a series of checks to ensure all components are working correctly.
"""

import os
import sys
import importlib.util
import platform
from pathlib import Path

def print_header(message):
    """Print a header with formatting."""
    print(f"\n{'=' * 70}")
    print(f" {message}")
    print(f"{'=' * 70}")

def print_result(test_name, result, details=None):
    """Print a test result with formatting."""
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status} | {test_name}")
    if details and not result:
        print(f"       {details}")

def check_python_version():
    """Check if Python version is adequate."""
    version = sys.version_info
    result = version.major >= 3 and version.minor >= 7
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print_result(
        f"Python version {version_str} (3.7+ required)", 
        result,
        "Please upgrade to Python 3.7 or later"
    )
    return result

def check_module_installed(module_name):
    """Check if a Python module is installed."""
    is_installed = importlib.util.find_spec(module_name) is not None
    print_result(
        f"Module '{module_name}' is installed", 
        is_installed,
        f"Install with: pip install {module_name}"
    )
    return is_installed

def check_python_path():
    """Check if the project root is in the Python path."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    result = project_root in sys.path
    print_result(
        f"Project root is in Python path", 
        result,
        f"Add with: sys.path.insert(0, '{project_root}')"
    )
    return result, project_root

def load_module_from_path(module_path, module_name):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not load spec for {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def check_import_paths():
    """Check if imports can be resolved."""
    import_success = True
    error_details = []
    
    # Try importing key modules
    try:
        import sqlalchemy
    except ImportError as e:
        import_success = False
        error_details.append(f"SQLAlchemy import error: {e}")
    
    # Try multiple import approaches
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    db_dir = os.path.join(current_dir, "db")
    schema_path = os.path.join(db_dir, "schema.py")
    manager_path = os.path.join(db_dir, "manager.py")
    
    schema_imported = False
    manager_imported = False
    
    # Try approach #1: Direct module imports
    try:
        from memory_bank.clinerules_logger.db import schema
        from memory_bank.clinerules_logger.db import manager
        schema_imported = True
        manager_imported = True
    except ImportError as e:
        pass
    
    # Try approach #2: Direct file loads
    if not schema_imported and os.path.exists(schema_path):
        try:
            schema = load_module_from_path(schema_path, "schema")
            schema_imported = True
        except Exception as e:
            error_details.append(f"Schema file load error: {e}")
    
    if not manager_imported and os.path.exists(manager_path):
        try:
            manager = load_module_from_path(manager_path, "manager")
            manager_imported = True
        except Exception as e:
            error_details.append(f"Manager file load error: {e}")
    
    # Try approach #3: System path modification
    if not schema_imported or not manager_imported:
        try:
            # Add directories to path
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            if db_dir not in sys.path:
                sys.path.insert(0, db_dir)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Now try simple imports
            if not schema_imported:
                try:
                    import schema
                    schema_imported = True
                except ImportError:
                    pass
            
            if not manager_imported:
                try:
                    import manager
                    manager_imported = True
                except ImportError:
                    pass
        except Exception as e:
            error_details.append(f"Path-modified import error: {e}")
    
    import_success = schema_imported and manager_imported and import_success
    
    if not schema_imported:
        error_details.append("Failed to import schema module")
    if not manager_imported:
        error_details.append("Failed to import manager module")
    
    print_result(
        "Import paths can be resolved", 
        import_success,
        "; ".join(error_details) if error_details else None
    )
    return import_success

def check_database():
    """Check if database can be accessed."""
    db_success = False
    error_detail = None
    db_manager = None
    
    try:
        # Add project root to path if needed
        path_ok, project_root = check_python_path()
        if not path_ok:
            sys.path.insert(0, project_root)
        
        # Try multiple import approaches
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.join(current_dir, "db")
        manager_path = os.path.join(db_dir, "manager.py")
        
        # Try approach #1: Direct module import
        try:
            from memory_bank.clinerules_logger.db.manager import db_manager
        except ImportError:
            # Try approach #2: Direct file load
            if os.path.exists(manager_path):
                try:
                    manager = load_module_from_path(manager_path, "manager")
                    db_manager = manager.db_manager
                except Exception as e:
                    error_detail = f"Manager file load error: {e}"
            
            # Try approach #3: System path modification
            if not db_manager:
                try:
                    # Add directories to path
                    if current_dir not in sys.path:
                        sys.path.insert(0, current_dir)
                    if db_dir not in sys.path:
                        sys.path.insert(0, db_dir)
                    
                    # Now try simple import
                    try:
                        import manager
                        db_manager = manager.db_manager
                    except ImportError as e:
                        error_detail = f"Path-modified import error: {e}"
                except Exception as e:
                    error_detail = f"Path modification error: {e}"
        
        # If db_manager was loaded, try to connect
        if db_manager:
            # Get a session and run a simple query
            session = db_manager.get_session()
            try:
                # Import SQLAlchemy text function if needed
                try:
                    from sqlalchemy import text
                except ImportError:
                    # Create a simple text wrapper if SQLAlchemy import fails
                    def text(sql):
                        return sql
                
                # Just try any simple query to test the connection
                result = session.execute(text("SELECT 1")).scalar()
                db_success = (result == 1)
            except Exception as e:
                error_detail = f"Database query error: {e}"
            finally:
                db_manager.close_session(session)
        else:
            if not error_detail:
                error_detail = "Could not load db_manager module"
    except Exception as e:
        error_detail = f"Unexpected error: {e}"
    
    print_result(
        "Database connection works", 
        db_success,
        error_detail
    )
    return db_success

def check_data_directories():
    """Check if required data directories exist."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define required directories
    required_dirs = [
        os.path.join(current_dir, "data"),
        os.path.join(current_dir, "backup", "data")
    ]
    
    missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
    
    print_result(
        "Data directories exist", 
        len(missing_dirs) == 0,
        f"Missing directories: {', '.join(missing_dirs)}" if missing_dirs else None
    )
    return len(missing_dirs) == 0

def run_self_test():
    """Run all self tests and summarize results."""
    print_header("SQLAlchemy Integration Self Test")
    
    results = []
    
    # Run tests in sequence, ordered by dependencies
    results.append(check_python_version())
    results.append(check_module_installed("sqlalchemy"))
    results.append(check_module_installed("schedule"))
    path_ok, _ = check_python_path()
    results.append(path_ok)
    results.append(check_data_directories())
    results.append(check_import_paths())
    results.append(check_database())
    
    # Summarize results
    passed = results.count(True)
    total = len(results)
    
    print_header(f"Test Summary: {passed}/{total} Tests Passed")
    
    if all(results):
        print("\nSQLAlchemy integration is properly set up and working!")
        print("\nYou can now use the enhanced features:")
        print("1. Run the example: python migration_example.py")
        print("2. Read the guide: SQLAlchemy_Integration_Guide.md")
    else:
        print("\nSome tests failed. Please address the issues above.")
        print("\nFor detailed setup instructions, refer to:")
        print("- SQLAlchemy_Integration_Guide.md")
        print("- README_SQLAlchemy.md")
        print("\nOr try running one of the setup scripts:")
        print("- setup_sqlalchemy.py (Python)")
        print("- setup_sqlalchemy.bat (Windows)")
        print("- setup_sqlalchemy.sh (Linux/macOS)")
    
    return all(results)

if __name__ == "__main__":
    run_self_test()
