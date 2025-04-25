#!/usr/bin/env python3
"""
Example script demonstrating migration from standalone logger to SQLAlchemy implementation.
This shows how to transition your existing code to use the enhanced features.
"""

import os
import sys
import datetime

# Determine the current script directory and project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# Add project root to Python path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def demonstrate_standalone_logger():
    """Demonstrate the standalone logger usage."""
    print("\n" + "=" * 50)
    print("STANDALONE LOGGER EXAMPLE")
    print("=" * 50)
    
    try:
        from memory_bank.clinerules_logger.standalone_example import SimpleLogger
        
        logger = SimpleLogger()
        
        # Basic logging
        print("\n1. Basic Logging:")
        logger.log_execution(
            rule_name="04-mkdir",
            component_name="Directory Creation Workflow",
            task_document="Task_001",
            context_window_usage="30%"
        )
        
        # Analytics
        print("\n2. Simple Analytics:")
        logger.analyze_usage()
        
        # Backup
        print("\n3. Manual Backup:")
        logger.backup_log()
        
        print("\nStandalone logger demonstration complete.")
        return True
    except Exception as e:
        print(f"Error demonstrating standalone logger: {e}")
        return False

def demonstrate_sqlalchemy_logger():
    """Demonstrate the SQLAlchemy logger usage."""
    print("\n" + "=" * 50)
    print("SQLALCHEMY INTEGRATION EXAMPLE")
    print("=" * 50)
    
    try:
        # Try importing the required modules
        try:
            from memory_bank.clinerules_logger.db.manager import db_manager
            from memory_bank.clinerules_logger.trackers.context_window import context_tracker
            from memory_bank.clinerules_logger.main import log_execution
        except ImportError as e:
            print(f"SQLAlchemy imports failed: {e}")
            print("\nPlease set up the SQLAlchemy integration first:")
            print("1. Run: python setup_sqlalchemy.py")
            print("2. Follow the setup instructions")
            return False
        
        # 1. Basic logging
        print("\n1. Enhanced Logging:")
        log_execution(
            rule_name="04-mkdir",
            component_name="Directory Creation Workflow",
            task_document="Task_001",
            context_window_usage="30%"
        )
        
        # 2. Context window tracking
        print("\n2. Context Window Tracking:")
        session_id = f"demo-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        context_tracker.start_session(session_id)
        context_tracker.update_token_count(session_id, 60000)
        context_tracker.end_session(session_id)
        print(f"Created and tracked context window session: {session_id}")
        
        # 3. Database queries
        print("\n3. Database Queries:")
        session = db_manager.get_session()
        try:
            # Get rules
            from memory_bank.clinerules_logger.db.schema import Rule
            rules = session.query(Rule).all()
            
            print(f"Found {len(rules)} rules in the database:")
            for rule in rules[:5]:  # Show at most 5 rules
                print(f"  - {rule.rule_name}: {rule.execution_count} executions")
        finally:
            db_manager.close_session(session)
        
        print("\nSQLAlchemy integration demonstration complete.")
        return True
    except Exception as e:
        print(f"Error demonstrating SQLAlchemy logger: {e}")
        return False

def show_migration_code():
    """Show code examples for migrating from standalone to SQLAlchemy."""
    print("\n" + "=" * 50)
    print("MIGRATION CODE EXAMPLES")
    print("=" * 50)
    
    print("""
# Old Standalone Code:
from memory_bank.clinerules_logger.standalone_example import SimpleLogger

logger = SimpleLogger()
logger.log_execution(
    rule_name="05-new-task",
    component_name="Update GitHub Repository",
    task_document="Task_002"
)

# New SQLAlchemy Code:
from memory_bank.clinerules_logger.main import log_execution

log_execution(
    rule_name="05-new-task", 
    component_name="Update GitHub Repository", 
    task_document="Task_002"
)

# Advanced SQLAlchemy Usage:
from memory_bank.clinerules_logger.db.manager import db_manager
from memory_bank.clinerules_logger.db.schema import Rule, Component

# Get a session
session = db_manager.get_session()
try:
    # Query rules used more than 5 times
    popular_rules = session.query(Rule).filter(Rule.execution_count > 5).all()
    
    # Work with relationships
    for rule in popular_rules:
        print(f"Rule: {rule.rule_name}")
        for component in rule.components:
            print(f"  - Component: {component.component_name}")
finally:
    # Always close the session
    db_manager.close_session(session)
""")

def main():
    """Run the migration example."""
    print("Clinerules Logger Migration Example")
    print("This script demonstrates the transition from standalone to SQLAlchemy.\n")
    
    # Try the standalone logger first
    standalone_success = demonstrate_standalone_logger()
    
    # Then try the SQLAlchemy implementation
    sqlalchemy_success = demonstrate_sqlalchemy_logger()
    
    # Show migration code examples
    show_migration_code()
    
    # Summarize
    print("\n" + "=" * 50)
    print("MIGRATION SUMMARY")
    print("=" * 50)
    
    if standalone_success and sqlalchemy_success:
        print("\nBoth loggers are working correctly!")
        print("You can gradually transition your code from standalone to SQLAlchemy.")
    elif standalone_success and not sqlalchemy_success:
        print("\nOnly the standalone logger is working.")
        print("To use the SQLAlchemy implementation, you need to:")
        print("1. Run: python setup_sqlalchemy.py")
        print("2. Follow the setup instructions")
    elif not standalone_success and not sqlalchemy_success:
        print("\nNeither logger is working correctly.")
        print("Please check your installation and Python path.")
    
    print("\nFor more details, see the SQLAlchemy Integration Guide:")
    print("memory-bank/clinerules_logger/SQLAlchemy_Integration_Guide.md")

if __name__ == "__main__":
    main()
