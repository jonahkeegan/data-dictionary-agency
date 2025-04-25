# SQLAlchemy Integration for .clinerules Logger

## Overview

This directory contains the enhanced .clinerules Logger system with SQLAlchemy integration. The integration provides significant improvements over the standalone version, including robust data storage, relationship tracking, sophisticated querying, and automated backups.

## Key Files

| File | Description |
|------|-------------|
| `setup_sqlalchemy.py` | Main Python setup script for SQLAlchemy integration |
| `setup_sqlalchemy.bat` | Windows batch script for easy setup |
| `setup_sqlalchemy.sh` | Linux/macOS shell script for easy setup |
| `simple_sqlalchemy_setup.py` | Simplified setup script with minimal user interaction |
| `SQLAlchemy_Integration_Guide.md` | Comprehensive guide to using the SQLAlchemy integration |
| `migration_example.py` | Example script demonstrating migration from standalone to SQLAlchemy |
| `db/schema.py` | Database schema definition using SQLAlchemy ORM |
| `db/manager.py` | Database connection and session management |
| `trackers/context_window.py` | Context window tracking functionality |
| `backup/manager.py` | Automated backup system |
| `analytics/metrics.py` | Enhanced analytics capabilities |
| `standalone_example.py` | Basic logger without SQLAlchemy (for comparison) |

## Quick Start

### Windows

```batch
cd memory-bank\clinerules_logger
setup_sqlalchemy.bat
```

### Linux/macOS

```bash
cd memory-bank/clinerules_logger
chmod +x setup_sqlalchemy.sh
./setup_sqlalchemy.sh
```

### Python (Cross-Platform)

```bash
cd memory-bank/clinerules_logger
python setup_sqlalchemy.py
```

## Features Comparison

| Feature | Standalone Logger | SQLAlchemy Integration |
|---------|------------------|------------------------|
| Data Storage | Simple text files | SQLite database with ORM |
| Query Capabilities | Limited text parsing | Full SQL query support |
| Relationship Tracking | None | Complete relationship modeling |
| Pattern Detection | Basic counting | Sophisticated analytics |
| Backup System | Manual file copying | Scheduled backups with retention |
| Context Window Tracking | Limited | Complete tracking with metrics |
| Performance | Slows with large logs | Scales well with growing data |

## Basic Usage

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

## Migration from Standalone Logger

If you've been using the standalone logger, you can easily migrate:

```python
# Old (Standalone) Code:
from memory_bank.clinerules_logger.standalone_example import SimpleLogger

logger = SimpleLogger()
logger.log_execution("rule-name", "component-name", "task-document")

# New (SQLAlchemy) Code:
from memory_bank.clinerules_logger.main import log_execution

log_execution("rule-name", "component-name", "task-document")
```

See `migration_example.py` for a complete example of migrating from standalone to SQLAlchemy.

## Troubleshooting

If you encounter issues with installation or usage:

1. **Import Errors**: Check your Python path configuration and ensure the project root is in your path.
2. **Database Issues**: Check database paths in `utils/config.py` and ensure data directories exist.
3. **Missing Dependencies**: Run `pip install -r requirements.txt` to install required packages.

For more detailed information, see the `SQLAlchemy_Integration_Guide.md`.

## Advanced Features

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

### Automated Backups

```python
from memory_bank.clinerules_logger.backup.manager import backup_manager

# Configure backup schedule (daily at 3 AM)
backup_manager.schedule_backup(hour=3, minute=0)

# Start the backup scheduler
backup_manager.start_scheduler()
```

### Analytics and Metrics

```python
from memory_bank.clinerules_logger.analytics.metrics import generate_metrics_report

# Generate a report for the last 30 days
report = generate_metrics_report(days=30)

# Export to JSON
report.export_to_json("metrics_report.json")
```

## References

- Full README: [clinerules_logger_README.md](clinerules_logger_README.md)
- SQLAlchemy Documentation: [https://docs.sqlalchemy.org/](https://docs.sqlalchemy.org/)
- SQLite Documentation: [https://www.sqlite.org/docs.html](https://www.sqlite.org/docs.html)
