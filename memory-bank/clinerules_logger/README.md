# ClinerRules Logger

A comprehensive logging and analytics system for Cline AI's .clinerules files. This enhanced system automatically tracks all interactions with .clinerules files, associates them with context windows, and provides analytics on rule usage patterns.

## New Features

- **Automatic file interaction tracking**: Detects and logs all read, write, validation, and execution operations on .clinerules files
- **VS Code integration**: Direct integration with VS Code through an extension to track rule interactions within the editor
- **SQL-based storage**: Robust SQLite database for storing all interaction data
- **Context window association**: Automatically links file interactions with Cline AI context windows
- **Analytics and patterns**: Detects usage patterns and generates insights about rule usage
- **Multiple interfaces**: CLI, Python API, and VS Code UI for comprehensive interaction

## Installation

1. Install the package:

```bash
cd memory-bank/clinerules_logger
pip install -r requirements.txt
python setup.py install
```

2. Install the VS Code extension:

```bash
cd memory-bank/clinerules_logger/integrations/vscode_extension
npm install
npm run build
```

## Usage

### Command Line Interface

```bash
# Log a rule execution
python -m clinerules_logger log --rule-name "05-new-task" --component-name "Update GitHub"

# Show system status
python -m clinerules_logger status

# Toggle file watcher
python -m clinerules_logger toggle file_watcher on

# Generate metrics
python -m clinerules_logger metrics --days 30 --output metrics.json

# Detect patterns
python -m clinerules_logger patterns

# Create a backup
python -m clinerules_logger backup
```

### Python API

```python
from memory_bank.clinerules_logger.trackers.file_watcher import file_watcher
from memory_bank.clinerules_logger.trackers.context_window import context_tracker
from memory_bank.clinerules_logger.db.manager import db_manager

# Log file interaction
file_watcher.log_manual_interaction(
    rule_name="05-new-task", 
    interaction_type="read",
    metadata={"source": "custom_script"}
)

# Get recent interactions
interactions = db_manager.get_recent_interactions(limit=10)
for interaction in interactions:
    print(f"{interaction.rule.rule_name}: {interaction.interaction_type}")

# Get statistics
stats = db_manager.get_interaction_statistics(days=7)
print(stats)
```

### VS Code Extension

Once installed, the VS Code extension will automatically track interactions with .clinerules files. You can also use the following commands:

- `ClinerRules: Check Logger Status` - Check if the logger server is running
- `ClinerRules: Log Manual Interaction` - Manually log an interaction
- `ClinerRules: Show Recent Interactions` - Show recent interactions with .clinerules files

## Architecture

The system consists of several components:

- **Database Layer**: SQL schemas and database manager for storing and retrieving data
- **Trackers**: Components that detect and track various events
  - `file_watcher.py`: Watches for file system operations on .clinerules files
  - `context_window.py`: Tracks Cline AI context windows
  - `rule_detector.py`: Analyzes and detects rule components
- **Integrations**: External system integrations
  - `vscode_integration.py`: Server-side code for VS Code integration
  - `vscode_extension/`: VS Code extension for client-side integration
- **Analytics**: Components for generating insights from the collected data
  - `metrics.py`: Calculates metrics and statistics
- **Notifications**: Components for alerting on important patterns
  - `detector.py`: Detects interesting patterns in rule usage

## Data Retention and Privacy

- All data is stored locally in an SQLite database at `data/clinerules.db`
- Automatic backups are created based on configuration settings
- No data is sent to external servers

## Customization

You can customize the logger's behavior through the configuration system:

```python
from memory_bank.clinerules_logger.utils.config import config

# Enable/disable file watcher
config.set('file_watcher', 'enabled', True)

# Change backup interval
config.set('database', 'backup_interval_hours', 12)

# Configure VS Code integration port
config.set('integrations', 'vscode_port', 5678)

# Save configuration
config.save()
```

## License

Apache License 2.0
