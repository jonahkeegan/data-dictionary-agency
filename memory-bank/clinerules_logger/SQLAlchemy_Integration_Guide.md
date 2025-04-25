# SQLAlchemy Integration Guide for .clinerules Logger

This guide provides detailed instructions for setting up and using the enhanced .clinerules Logger with SQLAlchemy integration.

## Table of Contents

1. [Benefits of SQLAlchemy Integration](#benefits-of-sqlalchemy-integration)
2. [Environment Setup](#environment-setup)
   - [Windows Setup](#windows-setup)
   - [Linux/macOS Setup](#linuxmacos-setup)
   - [Manual Setup](#manual-setup)
3. [Transitioning from Standalone to Full Implementation](#transitioning-from-standalone-to-full-implementation)
4. [Usage Examples](#usage-examples)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)

## Benefits of SQLAlchemy Integration

The full implementation with SQLAlchemy offers significant advantages over the standalone version:

| Feature | Standalone Logger | SQLAlchemy Integration |
|---------|------------------|------------------------|
| Data Storage | Simple text files | SQLite database with ORM |
| Query Capabilities | Limited text parsing | Full SQL query support |
| Relationship Tracking | None | Complete relationship modeling |
| Pattern Detection | Basic counting | Sophisticated analytics |
| Backup System | Manual file copying | Scheduled backups with retention |
| Context Window Tracking | Limited | Complete tracking with metrics |
| Performance | Slows with large logs | Scales well with growing data |

## Environment Setup

### Windows Setup

1. Open a Command Prompt in the project directory
2. Navigate to the clinerules_logger directory:
   ```
   cd memory-bank\clinerules_logger
   ```
3. Run the setup script:
   ```
   setup_sqlalchemy.bat
   ```
4. Follow the on-screen instructions to complete the setup
5. Activate the virtual environment:
   ```
   .\venv\Scripts\activate
   ```
6. Test the installation:
   ```
   python main.py --version
   ```

### Linux/macOS Setup

1. Open a Terminal in the project directory
2. Navigate to the clinerules_logger directory:
   ```
   cd memory-bank/clinerules_logger
   ```
3. Make the setup script executable:
   ```
   chmod +x setup_sqlalchemy.sh
   ```
4. Run the setup script:
   ```
   ./setup_sqlalchemy.sh
   ```
5. Follow the on-screen instructions to complete the setup
6. Activate the virtual environment:
   ```
   source .venv/bin/activate
   ```
7. Test the installation:
   ```
   python main.py --version
   ```

### Manual Setup

If the automated scripts don't work for your environment, you can perform a manual setup:

1. Create a virtual environment:
   ```
   python -m venv venv  # Windows
   python3 -m venv .venv  # Linux/macOS
   ```

2. Activate the virtual environment:
   ```
   .\venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/macOS
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Add the project root to your Python path:
   ```
   # Windows (in PowerShell)
   $env:PYTHONPATH = "$env:PYTHONPATH;C:\path\to\project\root"
   
   # Linux/macOS
   export PYTHONPATH=$PYTHONPATH:/path/to/project/root
   ```

5. Initialize the database:
   ```python
   from memory_bank.clinerules_logger.db.schema import Base, create_tables
   from memory_bank.clinerules_logger.db.manager import db_manager
   
   # Create tables
   create_tables(db_manager._engine)
   
   # Import legacy log data
   db_manager.import_legacy_log()
   ```

## Transitioning from Standalone to Full Implementation

If you've been using the standalone logger, follow these steps to transition to the full SQLAlchemy implementation:

1. Complete the [Environment Setup](#environment-setup) above
2. During setup, choose "Yes" when asked to import legacy log data
3. Update your import statements in existing code:

   **Old (Standalone) Code:**
   ```python
   from memory_bank.clinerules_logger.standalone_example import SimpleLogger
   
   logger = SimpleLogger()
   logger.log_execution("rule-name", "component-name", "task-document")
   ```

   **New (SQLAlchemy) Code:**
   ```python
   from memory_bank.clinerules_logger.main import log_execution
   
   log_execution("rule-name", "component-name", "task-document")
   ```

4. If you need direct database access:
   ```python
   from memory_bank.clinerules_logger.db.manager import db_manager
   
   # Get a session
   session = db_manager.get_session()
   
   try:
       # Use the session for database operations
       # ...
       
       # Commit changes
       db_manager.commit_session(session)
   finally:
       # Always close the session
       db_manager.close_session(session)
   ```

## Usage Examples

### Basic Logging

```python
from memory_bank.clinerules_logger.main import log_execution

# Log a rule execution
log_execution(
    rule_name="05-new-task",
    component_name="Update GitHub Repository",
    task_document="Task_002",
    context_window_usage="65%"
)
```

### Command Line Usage

```bash
# Interactive mode
python memory-bank/clinerules_logger/main.py

# Direct command line mode
python memory-bank/clinerules_logger/main.py log --rule-name "05-new-task" --component-name "Update GitHub Repository" --task-document "Task_002"
```

### Context Window Tracking

```python
from memory_bank.clinerules_logger.trackers.context_window import context_tracker

# Start tracking a context window session
session_id = "unique-session-id"
context_tracker.start_session(session_id)

# Update token count during the session
context_tracker.update_token_count(session_id, 75000)

# End the session
context_tracker.end_session(session_id)
```

### Analytics and Metrics

```python
from memory_bank.clinerules_logger.analytics.metrics import generate_metrics_report

# Generate a report for the last 30 days
report = generate_metrics_report(days=30)

# Export to JSON
report.export_to_json("metrics_report.json")

# Get the most frequently used rules
top_rules = report.get_top_rules(limit=5)
for rule in top_rules:
    print(f"{rule.rule_name}: {rule.execution_count} executions")
```

## Advanced Features

### Scheduled Backups

The SQLAlchemy integration includes a backup system that automatically maintains database backups:

```python
from memory_bank.clinerules_logger.backup.manager import backup_manager

# Configure backup schedule (daily at 3 AM)
backup_manager.schedule_backup(hour=3, minute=0)

# Start the backup scheduler
backup_manager.start_scheduler()

# Create a manual backup
backup_file = backup_manager.create_backup()
print(f"Backup created at: {backup_file}")

# Restore from a backup
backup_manager.restore_from_backup(backup_file)
```

### Pattern Detection

The system can automatically detect patterns in rule usage:

```python
from memory_bank.clinerules_logger.notification.detector import pattern_detector

# Detect frequent rule usage patterns
patterns = pattern_detector.detect_frequent_rules(threshold=5, days=7)

# Get rules that are commonly used together
related_rules = pattern_detector.detect_related_rules("05-new-task")
```

## Troubleshooting

### Import Errors

If you encounter import errors like `ImportError: No module named 'memory_bank'`:

1. Verify your virtual environment is activated
2. Check your Python path:
   ```python
   import sys
   print(sys.path)
   ```
3. Add the project root to your Python path:
   ```python
   import sys
   import os
   
   # Add project root to path
   project_root = "path/to/project/root"
   if project_root not in sys.path:
       sys.path.insert(0, project_root)
   ```

### Database Connection Issues

If you encounter database connection errors:

1. Check the database path in the config:
   ```python
   from memory_bank.clinerules_logger.utils.config import config
   
   db_path = config.get('database', 'path')
   print(f"Database path: {db_path}")
   ```

2. Ensure the data directory exists:
   ```python
   import os
   
   data_dir = os.path.dirname(db_path)
   os.makedirs(data_dir, exist_ok=True)
   ```

3. Try re-initializing the database:
   ```python
   from memory_bank.clinerules_logger.db.schema import Base, create_tables
   from sqlalchemy import create_engine
   
   engine = create_engine(f'sqlite:///{db_path}')
   create_tables(engine)
   ```

### Performance Issues

If the logger becomes slow with large datasets:

1. Optimize query performance:
   ```python
   from memory_bank.clinerules_logger.db.manager import db_manager
   
   # Use limit and specific column selection
   session = db_manager.get_session()
   try:
       # Query only what you need
       results = session.query(Rule.rule_name, Rule.execution_count).\
                 filter(Rule.execution_count > 10).\
                 limit(100).all()
   finally:
       db_manager.close_session(session)
   ```

2. Consider database maintenance:
   ```
   # In a terminal/command prompt
   sqlite3 path/to/clinerules.db "VACUUM;"
   ```

### Thread Safety Issues

If you encounter errors related to SQLite and thread safety:

1. Ensure proper session handling in multi-threaded code:
   ```python
   from memory_bank.clinerules_logger.db.manager import db_manager
   
   # Get a new session for each thread
   session = db_manager.get_session()
   try:
       # Use the session in the current thread only
       # ...
       
       # Commit changes
       db_manager.commit_session(session)
   finally:
       # Always close the session
       db_manager.close_session(session)
   ```

---

## Additional Resources

- SQLAlchemy Documentation: [https://docs.sqlalchemy.org/](https://docs.sqlalchemy.org/)
- SQLite Documentation: [https://www.sqlite.org/docs.html](https://www.sqlite.org/docs.html)
- Project README: [memory-bank/clinerules_logger_README.md](../clinerules_logger_README.md)
