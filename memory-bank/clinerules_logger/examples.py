#!/usr/bin/env python3
"""
Examples of using the enhanced .clinerules logger system.
"""

import os
import sys
import json
import importlib.util
from datetime import datetime

# Add the necessary paths to sys.path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

# Add the current directory and project root to sys.path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Define function to load Python modules directly from file paths
def load_module_from_path(module_path, module_name):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not load spec for {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Add subdirectories to the Python path
trackers_dir = os.path.join(current_dir, "trackers")
db_dir = os.path.join(current_dir, "db")
analytics_dir = os.path.join(current_dir, "analytics")
notification_dir = os.path.join(current_dir, "notification")
backup_dir = os.path.join(current_dir, "backup")

# Add all directories to Python path
for directory in [current_dir, project_root, trackers_dir, db_dir, analytics_dir, notification_dir, backup_dir]:
    if directory not in sys.path and os.path.exists(directory):
        sys.path.insert(0, directory)

# Create fallback classes in case modules can't be loaded
class DummyMetricsCalculator:
    @staticmethod
    def get_context_window_metrics(*args, **kwargs):
        return {"session_id": "dummy", "token_count": 0, "rule_count": 0, "component_count": 0}
    
    @staticmethod
    def get_rule_usage_metrics(*args, **kwargs):
        return {"summary": {"total_rules": 0, "total_executions": 0}, "rules": []}
    
    @staticmethod
    def get_session_metrics(*args, **kwargs):
        return {"sessions": []}
    
    @staticmethod
    def export_metrics_to_json(*args, **kwargs):
        return {}

class DummyPatternDetector:
    @staticmethod
    def detect_frequent_rule_usage(*args, **kwargs):
        return []
    
    @staticmethod
    def detect_frequent_component_usage(*args, **kwargs):
        return []
    
    @staticmethod
    def detect_rule_component_co_occurrence(*args, **kwargs):
        return []

class DummyBackupManager:
    def create_backup(self, *args, **kwargs):
        return True
    
    def list_available_backups(self, *args, **kwargs):
        return []
    
    def restore_from_backup(self, *args, **kwargs):
        return True

class DummyRuleDetector:
    def __init__(self):
        self._rules_dir = ""
        self._cached_rules = {}
        
    def log_rule_execution(self, rule_name, component_name, task_document=None, notes=None):
        print(f"[DUMMY] Logging rule execution: {rule_name} > {component_name}")
        return {"status": "dummy", "rule_name": rule_name, "component_name": component_name}
    
    def get_rule_details(self, rule_name):
        return {"id": 0, "path": "", "components": {}}
    
    def refresh_rules_cache(self):
        pass
    
    def analyze_rule_executions(self, rule_name=None, time_period=None):
        return {"status": "dummy", "rule_name": rule_name, "time_period": time_period}
    
    def detect_rules_from_text(self, text):
        return []

class DummyContextTracker:
    def __init__(self):
        self._context_window_id = 0
        self._active_session_id = "dummy_session"
        
    def get_current_context_window_id(self):
        return self._context_window_id
    
    def update_token_count(self, token_count):
        print(f"[DUMMY] Updating token count: {token_count}")
        return True
    
    def update_from_environment(self, env_string):
        print(f"[DUMMY] Updating from environment")
        return True
    
    def log_rule_execution(self, rule_name, component_name, task_document=None, notes=None):
        print(f"[DUMMY] Logging rule execution: {rule_name} > {component_name}")
        return {"status": "dummy"}
    
    def complete_session(self):
        pass
    
    def reset_session(self):
        pass

# Load module files directly if they exist
context_window_path = os.path.join(trackers_dir, "context_window.py")
rule_detector_path = os.path.join(trackers_dir, "rule_detector.py")
manager_path = os.path.join(db_dir, "manager.py")
metrics_path = os.path.join(analytics_dir, "metrics.py")
detector_path = os.path.join(notification_dir, "detector.py")
backup_path = os.path.join(backup_dir, "manager.py")

# Try different import approaches
try:
    # Try direct imports first (if modules are already in sys.path)
    import context_window
    context_tracker = context_window.context_tracker
    
    import rule_detector
    rule_detector = rule_detector.rule_detector
    
    import manager
    db_manager = manager.db_manager
    
    import metrics
    MetricsCalculator = metrics.MetricsCalculator
    
    import detector
    detect_patterns = detector.detect_patterns
    PatternDetector = detector.PatternDetector
    
    import backup_manager
    backup_manager = backup_manager.backup_manager
except ImportError:
    # Try direct file loads next
    try:
        # Load context_window module
        if os.path.exists(context_window_path):
            context_window_module = load_module_from_path(context_window_path, "context_window")
            context_tracker = context_window_module.context_tracker
        else:
            # Try with relative imports
            from trackers.context_window import context_tracker
            
        # Load rule_detector module
        if os.path.exists(rule_detector_path):
            rule_detector_module = load_module_from_path(rule_detector_path, "rule_detector")
            rule_detector = rule_detector_module.rule_detector
        else:
            # Try with relative imports
            from trackers.rule_detector import rule_detector
            
        # Load db_manager module
        if os.path.exists(manager_path):
            manager_module = load_module_from_path(manager_path, "manager")
            db_manager = manager_module.db_manager
        else:
            # Try with relative imports
            from db.manager import db_manager
            
        # Load analytics module
        if os.path.exists(metrics_path):
            metrics_module = load_module_from_path(metrics_path, "metrics")
            MetricsCalculator = metrics_module.MetricsCalculator
        else:
            # Try with relative imports
            try:
                from analytics.metrics import MetricsCalculator
            except ImportError:
                print("Warning: Could not import MetricsCalculator, using dummy implementation")
                MetricsCalculator = DummyMetricsCalculator
                
        # Load notification module
        if os.path.exists(detector_path):
            detector_module = load_module_from_path(detector_path, "detector")
            detect_patterns = detector_module.detect_patterns
            PatternDetector = detector_module.PatternDetector
        else:
            # Try with relative imports
            try:
                from notification.detector import detect_patterns, PatternDetector
            except ImportError:
                print("Warning: Could not import detector module, using dummy implementation")
                detect_patterns = lambda x: x
                PatternDetector = DummyPatternDetector
                
        # Load backup module
        if os.path.exists(backup_path):
            backup_module = load_module_from_path(backup_path, "backup_manager")
            backup_manager = backup_module.backup_manager
        else:
            # Try with relative imports
            try:
                from backup.manager import backup_manager
            except ImportError:
                print("Warning: Could not import backup manager, using dummy implementation")
                backup_manager = DummyBackupManager()
    except Exception as e:
        print(f"Error importing modules: {e}")
        # Create dummy objects
        context_tracker = DummyContextTracker()
        rule_detector = DummyRuleDetector()
        db_manager = None
        MetricsCalculator = DummyMetricsCalculator
        PatternDetector = DummyPatternDetector
        backup_manager = DummyBackupManager()
        print("Warning: Using dummy implementations due to import failures")


def setup_environment():
    """Set up the environment for the examples."""
    print("Setting up environment...")
    
    # Ensure data directory exists
    data_dir = os.path.join(current_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Ensure backup directory exists
    backup_dir = os.path.join(current_dir, "backup", "data")
    os.makedirs(backup_dir, exist_ok=True)
    
    print("Environment setup complete.\n")


def example_log_execution():
    """Example: Log a rule execution."""
    print("\n=== Example: Log Rule Execution ===")
    
    # Parameters
    rule_name = "05-new-task"
    component_name = "Update the GitHub repository"
    task_document = "Example_Task"
    
    # Log execution
    result = rule_detector.log_rule_execution(
        rule_name=rule_name,
        component_name=component_name,
        task_document=task_document
    )
    
    if result:
        print(f"Successfully logged execution of {rule_name} > {component_name}")
        print(f"Result: {result}")
    else:
        print("Error logging execution")


def example_context_window_tracking():
    """Example: Track context window usage."""
    print("\n=== Example: Context Window Tracking ===")
    
    # Get current context window
    context_window_id = context_tracker.get_current_context_window_id()
    print(f"Current context window ID: {context_window_id}")
    
    # Simulate token count update
    context_tracker.update_token_count(15000)
    print("Updated token count to 15000")
    
    # Example environment string (what's normally in environment_details)
    env_string = """# Context Window Usage
15,423 / 200K tokens used (7.7%)
"""
    
    # Update from environment string
    result = context_tracker.update_from_environment(env_string)
    if result:
        print("Successfully updated context window from environment details")
    else:
        print("Error updating from environment details")
    
    # Get metrics for current context window
    metrics = MetricsCalculator.get_context_window_metrics(context_window_id=context_window_id)
    if metrics:
        print("\nContext Window Metrics:")
        print(f"- Session ID: {metrics['session_id']}")
        print(f"- Token Count: {metrics['token_count']}")
        print(f"- Rules Triggered: {metrics['rule_count']}")
        print(f"- Components Triggered: {metrics['component_count']}")
    else:
        print("No metrics available for current context window")


def example_metrics_generation():
    """Example: Generate metrics and analytics."""
    print("\n=== Example: Metrics Generation ===")
    
    # Generate rule usage metrics
    rule_metrics = MetricsCalculator.get_rule_usage_metrics(days=30)
    if rule_metrics:
        print("\nRule Usage Metrics:")
        print(f"- Total Rules: {rule_metrics['summary']['total_rules']}")
        print(f"- Total Executions: {rule_metrics['summary']['total_executions']}")
        
        if rule_metrics['rules']:
            print("\nTop Rules:")
            for rule in rule_metrics['rules'][:3]:  # Show top 3
                print(f"- {rule['rule_name']}: {rule['execution_count']} executions")
    else:
        print("No rule metrics available")
    
    # Generate session metrics
    session_metrics = MetricsCalculator.get_session_metrics(days=30, limit=5)
    if session_metrics and session_metrics['sessions']:
        print("\nRecent Sessions:")
        for session in session_metrics['sessions'][:3]:  # Show top 3
            print(f"- {session['session_id']}: {session['rule_count']} rules, {session['component_count']} components")
    else:
        print("No session metrics available")
    
    # Export metrics to file
    output_file = os.path.join(current_dir, "data", f"example_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    metrics = MetricsCalculator.export_metrics_to_json(output_file, days=30)
    if metrics:
        print(f"\nExported metrics to {output_file}")
    else:
        print("\nError exporting metrics")


def example_pattern_detection():
    """Example: Detect usage patterns."""
    print("\n=== Example: Pattern Detection ===")
    
    # Detect patterns without creating notifications
    patterns = {
        'frequent_rules': PatternDetector.detect_frequent_rule_usage(
            threshold=2, window_hours=24, create_notification=False
        ),
        'frequent_components': PatternDetector.detect_frequent_component_usage(
            threshold=2, window_hours=24, create_notification=False
        ),
        'rule_co_occurrences': PatternDetector.detect_rule_component_co_occurrence(
            threshold=2, window_hours=24, create_notification=False
        )
    }
    
    # Display patterns
    if patterns['frequent_rules']:
        print("\nFrequently Used Rules:")
        for rule in patterns['frequent_rules']:
            print(f"- {rule['rule_name']}: {rule['execution_count']} executions")
    else:
        print("\nNo frequently used rules detected")
    
    if patterns['frequent_components']:
        print("\nFrequently Used Components:")
        for component in patterns['frequent_components']:
            print(f"- {component['component_name']} (from {component['rule_name']}): {component['execution_count']} executions")
    else:
        print("\nNo frequently used components detected")
    
    if patterns['rule_co_occurrences']:
        print("\nRule Co-occurrences:")
        for pair in patterns['rule_co_occurrences']:
            print(f"- {pair['rule1']} & {pair['rule2']}: {pair['co_occurrence_count']} co-occurrences")
    else:
        print("\nNo significant rule co-occurrences detected")


def example_backup_management():
    """Example: Manage database backups."""
    print("\n=== Example: Backup Management ===")
    
    # Create a backup
    print("Creating backup...")
    result = backup_manager.create_backup()
    if result:
        print("Backup created successfully")
    else:
        print("Error creating backup")
    
    # List available backups
    backups = backup_manager.list_available_backups()
    if backups:
        print("\nAvailable Backups:")
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup['name']} ({backup['date']}, {backup['size_mb']} MB)")
    else:
        print("\nNo backups available")
    
    # Note: We don't include restore example as it's destructive
    print("\nNote: To restore from a backup, use:")
    print("backup_manager.restore_from_backup(backup_path)")


def run_all_examples():
    """Run all example functions."""
    setup_environment()
    example_log_execution()
    example_context_window_tracking()
    example_metrics_generation()
    example_pattern_detection()
    example_backup_management()
    print("\nAll examples completed successfully!")


if __name__ == "__main__":
    print("Enhanced .clinerules Logger System Examples")
    print("------------------------------------------")
    print("This script demonstrates how to use the enhanced logger system.")
    print("Running examples...")
    
    run_all_examples()
