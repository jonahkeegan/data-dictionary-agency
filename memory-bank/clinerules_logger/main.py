#!/usr/bin/env python3
"""
Main entry point for the enhanced .clinerules logger system.

This module provides initialization and management of the clinerules logger system,
including automatic file interaction tracking, VS Code integration, and analytics.
"""

import os
import sys
import argparse
import json
import threading
import importlib.util
from datetime import datetime
from pathlib import Path

# Define module loading function
def load_module_from_path(module_path, module_name):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not load spec for {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Setup import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
trackers_dir = os.path.join(current_dir, "trackers")
utils_dir = os.path.join(current_dir, "utils")
backup_dir = os.path.join(current_dir, "backup")
notification_dir = os.path.join(current_dir, "notification")
analytics_dir = os.path.join(current_dir, "analytics")
integrations_dir = os.path.join(current_dir, "integrations")

# Add directories to path
for directory in [db_dir, trackers_dir, utils_dir, backup_dir, notification_dir, analytics_dir, integrations_dir]:
    if os.path.exists(directory) and directory not in sys.path:
        sys.path.insert(0, directory)

# Try direct imports first, then fallback to module loading
# Import core components
try:
    # Try relative import
    from .db.manager import db_manager
    from .trackers.context_window import context_tracker
    from .trackers.rule_detector import rule_detector
    from .backup.manager import backup_manager
    from .notification.detector import detect_patterns, check_unread_notifications, mark_notification_read
    from .analytics.metrics import MetricsCalculator
    from .utils.config import config
except ImportError:
    # Fall back to direct import via module loading
    try:
        # Load config first
        config_path = os.path.join(utils_dir, "config.py")
        config_module = load_module_from_path(config_path, "config")
        config = config_module.config
        
        # Load other modules
        manager_path = os.path.join(db_dir, "manager.py")
        manager_module = load_module_from_path(manager_path, "manager")
        db_manager = manager_module.db_manager
        
        context_window_path = os.path.join(trackers_dir, "context_window.py")
        context_window_module = load_module_from_path(context_window_path, "context_window")
        context_tracker = context_window_module.context_tracker
        
        rule_detector_path = os.path.join(trackers_dir, "rule_detector.py")
        rule_detector_module = load_module_from_path(rule_detector_path, "rule_detector")
        rule_detector = rule_detector_module.rule_detector
        
        backup_manager_path = os.path.join(backup_dir, "manager.py")
        backup_module = load_module_from_path(backup_manager_path, "backup_manager")
        backup_manager = backup_module.backup_manager
        
        notification_path = os.path.join(notification_dir, "detector.py")
        notification_module = load_module_from_path(notification_path, "detector")
        detect_patterns = notification_module.detect_patterns
        check_unread_notifications = notification_module.check_unread_notifications
        mark_notification_read = notification_module.mark_notification_read
        
        metrics_path = os.path.join(analytics_dir, "metrics.py")
        metrics_module = load_module_from_path(metrics_path, "metrics")
        MetricsCalculator = metrics_module.MetricsCalculator
    except Exception as e:
        # If all else fails
        print(f"Error importing core modules: {e}")
        print("This might be due to running the script directly instead of as a module.")
        print("Try using direct_run.py instead.")
        sys.exit(1)

# Dynamically import optional components
try:
    # Try relative import
    from .trackers.file_watcher import file_watcher
except ImportError:
    try:
        # Try direct import via module loading
        file_watcher_path = os.path.join(trackers_dir, "file_watcher.py")
        if os.path.exists(file_watcher_path):
            file_watcher_module = load_module_from_path(file_watcher_path, "file_watcher")
            file_watcher = file_watcher_module.file_watcher
        else:
            file_watcher = None
            print("Warning: file_watcher module not available")
    except Exception:
        file_watcher = None
        print("Warning: file_watcher module not available")

try:
    # Try relative import
    from .integrations.vscode_integration import vscode_integration
except ImportError:
    try:
        # Try direct import via module loading
        vscode_integration_path = os.path.join(integrations_dir, "vscode_integration.py")
        if os.path.exists(vscode_integration_path):
            vscode_integration_module = load_module_from_path(vscode_integration_path, "vscode_integration")
            vscode_integration = vscode_integration_module.vscode_integration
        else:
            vscode_integration = None
            print("Warning: vscode_integration module not available")
    except Exception:
        vscode_integration = None
        print("Warning: vscode_integration module not available")

def initialize_system():
    """Initialize all components of the system."""
    print("Initializing .clinerules logger system...")
    
    # Import legacy log data if configured
    if config.get('legacy', 'import_on_startup'):
        print("Importing legacy log data...")
        db_manager.import_legacy_log()
    
    # Start backup scheduler
    if config.get('database', 'backup_interval_hours', 0) > 0:
        print("Starting backup scheduler...")
        backup_manager.start_scheduler()
    
    # Initialize file watcher if available and enabled
    if file_watcher and config.get('file_watcher', 'enabled', True):
        print("Starting file watcher...")
        if not file_watcher.is_running():
            try:
                file_watcher.start()
                print("File watcher started successfully.")
            except Exception as e:
                print(f"Error starting file watcher: {e}")
    
    # Initialize VSCode integration if available and enabled
    if vscode_integration and config.get('integrations', 'vscode_enabled', True):
        print("Starting VSCode integration...")
        if not vscode_integration.is_running():
            try:
                # VSCode integration starts automatically in __init__
                print("VSCode integration active:", vscode_integration.is_running())
            except Exception as e:
                print(f"Error with VSCode integration: {e}")
    
    # Detect patterns if notifications are enabled
    if config.get('notification', 'enabled'):
        print("Checking for patterns...")
        patterns = detect_patterns()
        
        # Check for unread notifications
        notifications = check_unread_notifications()
        if notifications:
            print(f"\nYou have {len(notifications)} unread notifications:")
            for i, notification in enumerate(notifications, 1):
                print(f"{i}. {notification.title} ({notification.creation_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    # Log system initialization
    try:
        db_manager.log_system_event(
            "system_initialized",
            "main",
            {
                "timestamp": datetime.now().isoformat(),
                "modules": {
                    "file_watcher": file_watcher is not None,
                    "vscode_integration": vscode_integration is not None,
                }
            }
        )
    except Exception as e:
        print(f"Error logging system initialization: {e}")
    
    print("System initialized successfully.")
    return True

def log_execution(args):
    """Log a rule execution."""
    rule_name = args.rule_name
    component_name = args.component_name
    task_document = args.task_document
    
    # Get the current context window
    context_window_id = context_tracker.get_current_context_window_id()
    
    # Log execution
    result = rule_detector.log_rule_execution(
        rule_name=rule_name, 
        component_name=component_name,
        task_document=task_document
    )
    
    # Update context window from environment if provided
    if args.environment:
        context_tracker.update_from_environment(args.environment)
    
    if result:
        print(f"Logged execution of {rule_name} > {component_name}")
        return True
    else:
        print(f"Error logging execution")
        return False

def interactive_log():
    """Interactive logging function similar to the legacy interface."""
    print("=== Enhanced .clinerules Task Execution Logger ===")
    
    # Get task context document
    task_document = input("Task Context Document (e.g., Task_002): ")
    
    # Get referenced .clinerule
    rule_name = input("Referenced .clinerule (e.g., 05-new-task): ")
    
    # Get referenced component
    component_name = input("Referenced Component (e.g., 'Update the GitHub repository'): ")
    
    # Log execution
    result = rule_detector.log_rule_execution(
        rule_name=rule_name,
        component_name=component_name,
        task_document=task_document
    )
    
    if result:
        print(f"\nExecution logged successfully for {rule_name} > {component_name}")
        return True
    else:
        print(f"\nError logging execution")
        return False

def export_metrics(args):
    """Export analytics metrics."""
    days = args.days
    output_file = args.output
    
    if not output_file:
        # Create default filename with timestamp
        output_file = f"clinerules_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Export metrics
    metrics = MetricsCalculator.export_metrics_to_json(output_file, days=days)
    
    if metrics:
        print(f"Metrics exported to {output_file}")
        
        # Print summary
        rule_summary = metrics['rule_usage']['summary']
        component_summary = metrics['component_usage']['summary']
        session_summary = metrics['sessions']['summary']
        
        print("\nMetrics Summary:")
        print(f"- Time period: Last {days} days")
        print(f"- Rules tracked: {rule_summary['total_rules']}")
        print(f"- Rule executions: {rule_summary['total_executions']}")
        print(f"- Components tracked: {component_summary['total_components']}")
        print(f"- Component executions: {component_summary['total_executions']}")
        print(f"- Context window sessions: {session_summary['total_sessions']}")
        
        if session_summary['total_sessions'] > 0:
            print(f"- Average rules per session: {session_summary['average_rules_per_session']:.2f}")
            print(f"- Average components per session: {session_summary['average_components_per_session']:.2f}")
        
        return True
    else:
        print("Error exporting metrics")
        return False

def detect_and_print_patterns(args):
    """Detect and print patterns."""
    patterns = detect_patterns()
    
    print("\nDetected Patterns:")
    
    # Frequent rules
    if patterns['frequent_rules']:
        print("\nFrequently Used Rules:")
        for rule in patterns['frequent_rules']:
            print(f"- {rule['rule_name']}: {rule['execution_count']} executions in the last {rule['time_window_hours']} hours")
    else:
        print("\nNo frequently used rules detected.")
    
    # Frequent components
    if patterns['frequent_components']:
        print("\nFrequently Used Components:")
        for component in patterns['frequent_components']:
            print(f"- {component['component_name']} (from {component['rule_name']}): {component['execution_count']} executions")
    else:
        print("\nNo frequently used components detected.")
    
    # Co-occurrences
    if patterns['rule_co_occurrences']:
        print("\nRule Co-occurrences:")
        for pair in patterns['rule_co_occurrences']:
            print(f"- {pair['rule1']} & {pair['rule2']}: {pair['co_occurrence_count']} co-occurrences")
    else:
        print("\nNo significant rule co-occurrences detected.")
    
    return True

def list_backups(args):
    """List available backups."""
    backups = backup_manager.list_available_backups()
    
    if not backups:
        print("No backups found.")
        return False
    
    print("\nAvailable Backups:")
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup['name']} ({backup['date']}, {backup['size_mb']} MB)")
    
    return True

def create_backup(args):
    """Create a backup."""
    result = backup_manager.create_backup()
    
    if result:
        print("Backup created successfully.")
        return True
    else:
        print("Error creating backup.")
        return False

def restore_backup(args):
    """Restore from a backup."""
    backup_path = args.path
    
    if not os.path.exists(backup_path):
        print(f"Backup file not found: {backup_path}")
        return False
    
    print(f"Restoring from backup: {backup_path}")
    print("WARNING: This will overwrite the current database. Are you sure? (y/n)")
    confirmation = input("> ").strip().lower()
    
    if confirmation == 'y':
        result = backup_manager.restore_from_backup(backup_path)
        
        if result:
            print("Database restored successfully.")
            return True
        else:
            print("Error restoring database.")
            return False
    else:
        print("Restore cancelled.")
        return False

def legacy_mode(args):
    """Legacy mode for backwards compatibility."""
    # If arguments provided
    if len(args) >= 3:
        task_context = args[0]
        clinerule = args[1]
        component = args[2]
        
        # Log execution
        result = rule_detector.log_rule_execution(
            rule_name=clinerule,
            component_name=component,
            task_document=task_context
        )
        
        if result:
            print(f"Logged execution of {clinerule} > {component}")
        else:
            print("Error logging execution")
            
        return True
    else:
        # Interactive mode
        return interactive_log()

def show_status(args):
    """Show system status."""
    print("\n===== ClinerRules Logger System Status =====")
    print(f"Database: {config.get('database', 'path')}")
    print(f"File Watcher: {'Active' if file_watcher and file_watcher.is_running() else 'Inactive'}")
    print(f"VSCode Integration: {'Active' if vscode_integration and vscode_integration.is_running() else 'Inactive'}")
    
    # Show statistics
    try:
        stats = db_manager.get_interaction_statistics(days=7)
        print("\nLast 7 Days Statistics:")
        print(f"- Rule executions: {sum(stats.get('interaction_counts', {}).values())}")
        print("- Top rules:")
        for rule in stats.get('active_rules', [])[:3]:
            print(f"  - {rule['rule']}: {rule['count']} interactions")
    except Exception as e:
        print(f"Error getting statistics: {e}")
    
    print("\nNotifications:")
    notifications = check_unread_notifications()
    if notifications:
        print(f"- {len(notifications)} unread notifications")
    else:
        print("- No unread notifications")
    
    print("=========================================")

def toggle_component(args):
    """Toggle a component on or off."""
    component = args.component
    new_status = args.status == 'on'
    
    if component == 'file_watcher':
        if not file_watcher:
            print("File watcher module not available")
            return
            
        if new_status and not file_watcher.is_running():
            file_watcher.start()
            print("File watcher started")
        elif not new_status and file_watcher.is_running():
            file_watcher.stop()
            print("File watcher stopped")
        else:
            print(f"File watcher already {'running' if new_status else 'stopped'}")
            
        # Update config
        config.set('file_watcher', 'enabled', new_status)
        
    elif component == 'vscode':
        if not vscode_integration:
            print("VSCode integration module not available")
            return
            
        if new_status and not vscode_integration.is_running():
            print("Starting VSCode integration (server will initialize)")
            # VSCode integration requires restart
            config.set('integrations', 'vscode_enabled', True)
            print("VSCode integration enabled in config, restart required for changes to take effect")
        elif not new_status and vscode_integration.is_running():
            vscode_integration.stop()
            config.set('integrations', 'vscode_enabled', False)
            print("VSCode integration stopped and disabled in config")
        else:
            print(f"VSCode integration already {'enabled' if new_status else 'disabled'}")

def shutdown_system():
    """Shutdown the system gracefully."""
    print("Shutting down .clinerules logger system...")
    
    # Stop VSCode integration if running
    if vscode_integration and vscode_integration.is_running():
        try:
            vscode_integration.stop()
            print("VSCode integration stopped.")
        except Exception as e:
            print(f"Error stopping VSCode integration: {e}")
    
    # Stop file watcher if running
    if file_watcher and file_watcher.is_running():
        try:
            file_watcher.stop()
            print("File watcher stopped.")
        except Exception as e:
            print(f"Error stopping file watcher: {e}")
    
    # Log system shutdown
    try:
        db_manager.log_system_event(
            "system_shutdown",
            "main",
            {
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"Error logging system shutdown: {e}")
    
    print("System shutdown complete.")

def main():
    """Main entry point."""
    # Initialize the system
    initialize_system()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Enhanced .clinerules Task Execution Logger')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    version_parser.set_defaults(func=lambda _: print("ClinerRules Logger v1.1.0"))
    
    # Command: log
    log_parser = subparsers.add_parser('log', help='Log a rule execution')
    log_parser.add_argument('--rule-name', '-r', required=True, help='Name of the .clinerule')
    log_parser.add_argument('--component-name', '-c', required=True, help='Name of the component')
    log_parser.add_argument('--task-document', '-t', default=None, help='Task context document')
    log_parser.add_argument('--environment', '-e', default=None, help='Environment details for context window')
    log_parser.set_defaults(func=log_execution)
    
    # Command: metrics
    metrics_parser = subparsers.add_parser('metrics', help='Export analytics metrics')
    metrics_parser.add_argument('--days', '-d', type=int, default=30, help='Number of days to include in metrics')
    metrics_parser.add_argument('--output', '-o', default=None, help='Output file path')
    metrics_parser.set_defaults(func=export_metrics)
    
    # Command: patterns
    patterns_parser = subparsers.add_parser('patterns', help='Detect and report patterns')
    patterns_parser.set_defaults(func=detect_and_print_patterns)
    
    # Command: backups
    backup_parser = subparsers.add_parser('backups', help='List available backups')
    backup_parser.set_defaults(func=list_backups)
    
    # Command: backup
    create_backup_parser = subparsers.add_parser('backup', help='Create a backup')
    create_backup_parser.set_defaults(func=create_backup)
    
    # Command: restore
    restore_parser = subparsers.add_parser('restore', help='Restore from a backup')
    restore_parser.add_argument('--path', '-p', required=True, help='Path to backup file')
    restore_parser.set_defaults(func=restore_backup)
    
    # Command: status
    status_parser = subparsers.add_parser('status', help='Show system status')
    status_parser.set_defaults(func=show_status)
    
    # Command: toggle
    toggle_parser = subparsers.add_parser('toggle', help='Toggle component status')
    toggle_parser.add_argument('component', choices=['file_watcher', 'vscode'], help='Component to toggle')
    toggle_parser.add_argument('status', choices=['on', 'off'], help='New status')
    toggle_parser.set_defaults(func=toggle_component)
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Handle legacy mode (no command)
        if not args.command:
            if len(sys.argv) > 1:
                return legacy_mode(sys.argv[1:])
            else:
                return interactive_log()
        
        # Execute command
        if hasattr(args, 'func'):
            return args.func(args)
        else:
            parser.print_help()
            return False
    finally:
        # Ensure graceful shutdown on exit
        shutdown_system()

if __name__ == '__main__':
    main()
