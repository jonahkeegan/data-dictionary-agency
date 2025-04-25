# Changelog

## v1.1.0 (2025-04-23)

### Added
- **Automatic file interaction tracking**
  - New `FileInteraction` table in database schema
  - File watcher module (`trackers/file_watcher.py`) to detect file operations
  - Automatic tracking of read, write, validate, and execute operations
  - File interaction metrics and statistics
  
- **VS Code Integration**
  - Server-side integration module (`integrations/vscode_integration.py`)
  - VS Code extension for client-side integration
  - Real-time file interaction logging within VS Code
  - Commands for checking status, logging interactions, and viewing recent activity

- **System Event Logging**
  - New `SystemEvent` table in database schema
  - Comprehensive system event tracking
  - Improved diagnostic capabilities

### Enhanced
- Main module with extended CLI commands:
  - `status` command for system status reporting
  - `toggle` command for enabling/disabling components
  
- Database schema:
  - JSON metadata support for interactions and events
  - Improved relationship modeling
  - Better query performance

- Configuration system:
  - More flexible options for file watcher
  - Integration settings
  - Better defaults for various environments

### Fixed
- Legacy log import handling
- Context window tracking edge cases
- Database connection handling
- Configuration file loading issues

## v1.0.0 (2025-03-01)

### Added
- Basic rule execution logging
- Context window tracking
- Rule and component detection
- Legacy log format support
- SQL-based storage
- Analytics and metrics
- Notification system for pattern detection
- Backup and restore functionality
