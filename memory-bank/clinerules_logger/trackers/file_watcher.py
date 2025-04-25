#!/usr/bin/env python3
"""
File watcher module for .clinerules logger.

This module monitors .clinerules files for access, modification, and interaction events,
automatically logging these interactions to the database.
"""

import os
import sys
import time
import json
import threading
import importlib.util
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Add paths for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
clinerules_dir = os.path.dirname(current_dir)
db_dir = os.path.join(clinerules_dir, "db")
utils_dir = os.path.join(clinerules_dir, "utils")
sys.path.insert(0, db_dir)
sys.path.insert(0, utils_dir)

# Function to load module from file path
def load_module_from_path(module_path, module_name):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not load spec for {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Try different import approaches
try:
    # Try from rule_detector module first
    from rule_detector import rule_detector
except ImportError:
    try:
        # Try from current directory
        rule_detector_path = os.path.join(current_dir, "rule_detector.py")
        if os.path.exists(rule_detector_path):
            rule_detector_module = load_module_from_path(rule_detector_path, "rule_detector")
            rule_detector = rule_detector_module.rule_detector
        else:
            # Fallback to relative imports
            from .rule_detector import rule_detector
    except ImportError:
        print("Warning: Could not import rule_detector")

# Try different import approaches for context_tracker
try:
    # Try from context_window module
    from context_window import context_tracker
except ImportError:
    try:
        # Try from current directory
        context_window_path = os.path.join(current_dir, "context_window.py")
        if os.path.exists(context_window_path):
            context_window_module = load_module_from_path(context_window_path, "context_window")
            context_tracker = context_window_module.context_tracker
        else:
            # Fallback to relative imports
            from .context_window import context_tracker
    except ImportError:
        print("Warning: Could not import context_tracker")

# Try different import approaches for db_manager and config
try:
    # Try direct import
    import manager
    db_manager = manager.db_manager
    import config
    config_module = config
except ImportError:
    try:
        # Try relative import
        from ..db.manager import db_manager
        from ..utils.config import config as config_module
    except ImportError:
        # Try absolute import with memory_bank prefix
        try:
            from memory_bank.clinerules_logger.db.manager import db_manager
            from memory_bank.clinerules_logger.utils.config import config as config_module
        except ImportError:
            # Try dynamically loading modules
            manager_path = os.path.join(db_dir, "manager.py")
            config_path = os.path.join(utils_dir, "config.py")
            
            try:
                manager_module = load_module_from_path(manager_path, "manager")
                db_manager = manager_module.db_manager
                config_module = load_module_from_path(config_path, "config")
                config = config_module.config
            except Exception as e:
                print(f"Error loading modules: {e}")
                print("Warning: File watcher will not be able to log interactions")


class ClinerRulesFileEventHandler(FileSystemEventHandler):
    """
    Event handler for .clinerules files.
    
    This handler processes file system events related to .clinerules files
    and logs them to the database.
    """
    
    def __init__(self, source_application="file_watcher"):
        """Initialize the event handler."""
        self.source_application = source_application
        self.last_events = {}  # Cache to debounce duplicate events
        self.debounce_time = 0.5  # Debounce time in seconds
    
    def _is_clinerules_file(self, path):
        """Check if a file is a .clinerules file or in the .clinerules directory."""
        if not path:
            return False
            
        path_obj = Path(path)
        
        # Check if it's in the clinerules directory
        rules_dir = Path(os.path.expanduser("~")) / "OneDrive" / "Documents" / "Cline" / "Rules"
        try:
            # Check if it's a subdirectory of the rules directory
            return path_obj.suffix == '.md' and rules_dir in path_obj.parents
        except:
            # Fallback to simple name check
            return path_obj.suffix == '.md' and 'clinerules' in path_obj.name.lower()
    
    def _get_rule_id(self, path):
        """Get the rule ID for the given file path."""
        stem = Path(path).stem  # Get filename without extension
        
        # Use rule_detector to get rule details
        if hasattr(rule_detector, 'get_rule_details'):
            rule_details = rule_detector.get_rule_details(stem)
            if rule_details and 'id' in rule_details:
                return rule_details['id']
        
        # If not found, create or get the rule
        return self._get_or_create_rule(stem, path).id
    
    def _get_or_create_rule(self, rule_name, file_path):
        """Get or create a rule for the given rule name and path."""
        return db_manager.get_or_create_rule(rule_name, file_path)
    
    def _debounce_event(self, event_type, src_path):
        """Debounce file events to prevent duplicate logs."""
        current_time = time.time()
        event_key = f"{event_type}:{src_path}"
        
        if event_key in self.last_events:
            last_time = self.last_events[event_key]
            if current_time - last_time < self.debounce_time:
                return False  # Skip this event
        
        self.last_events[event_key] = current_time
        return True  # Process this event
    
    def _log_interaction(self, event_type, path, application=None):
        """Log a file interaction to the database."""
        if not self._is_clinerules_file(path):
            return False
            
        if not self._debounce_event(event_type, path):
            return False
            
        try:
            rule_id = self._get_rule_id(path)
            
            # Get current context window ID if available
            context_window_id = None
            if hasattr(context_tracker, 'get_current_context_window_id'):
                context_window_id = context_tracker.get_current_context_window_id()
            
            # Map event types to interaction types
            interaction_type_map = {
                'created': 'create',
                'modified': 'write',
                'moved': 'move',
                'deleted': 'delete',
                'opened': 'read',
                'accessed': 'read'
            }
            
            interaction_type = interaction_type_map.get(event_type, event_type)
            
            # Create metadata
            metadata = {
                'file_path': str(path),
                'time': datetime.now().isoformat(),
                'event_type': event_type,
            }
            
            # Log the interaction
            db_manager.log_file_interaction(
                rule_id=rule_id,
                interaction_type=interaction_type,
                metadata=metadata,
                context_window_id=context_window_id,
                application=application or self.source_application,
                user_initiated=True
            )
            
            return True
        except Exception as e:
            print(f"Error logging interaction: {e}")
            return False
    
    def on_created(self, event):
        """Called when a file is created."""
        if not event.is_directory:
            self._log_interaction('created', event.src_path)
    
    def on_modified(self, event):
        """Called when a file is modified."""
        if not event.is_directory:
            self._log_interaction('modified', event.src_path)
    
    def on_moved(self, event):
        """Called when a file is moved."""
        if not event.is_directory:
            if self._is_clinerules_file(event.src_path):
                self._log_interaction('moved_from', event.src_path)
            if self._is_clinerules_file(event.dest_path):
                self._log_interaction('moved_to', event.dest_path)
    
    def on_deleted(self, event):
        """Called when a file is deleted."""
        if not event.is_directory:
            self._log_interaction('deleted', event.src_path)


class FileWatcher:
    """
    File watcher for .clinerules files.
    
    This class provides a watchdog observer to monitor the .clinerules directory
    and log all file operations.
    """
    
    _instance = None
    _lock = threading.Lock()
    _observer = None
    _running = False
    _rules_dir = Path(os.path.expanduser("~")) / "OneDrive" / "Documents" / "Cline" / "Rules"
    
    def __new__(cls):
        """Singleton pattern to ensure only one file watcher instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FileWatcher, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """Initialize the file watcher."""
        # Check if we should monitor files based on config
        try:
            if hasattr(config_module, 'get') and not config_module.get('file_watcher', 'enabled', True):
                print("File watcher disabled in configuration")
                return
        except:
            pass  # Default to enabled if config not available
        
        self._event_handler = ClinerRulesFileEventHandler()
        self._observer = Observer()
        
        # Ensure the rules directory exists
        if not self._rules_dir.exists():
            print(f"Rules directory not found at {self._rules_dir}")
        else:
            self.start()
    
    def start(self):
        """Start the file watcher."""
        if self._observer and not self._running:
            try:
                self._observer.schedule(self._event_handler, str(self._rules_dir), recursive=True)
                self._observer.start()
                self._running = True
                print(f"File watcher started for {self._rules_dir}")
                
                # Log start event
                self._log_system_event("file_watcher_started", {
                    "watched_directory": str(self._rules_dir),
                    "recursive": True
                })
            except Exception as e:
                print(f"Error starting file watcher: {e}")
    
    def stop(self):
        """Stop the file watcher."""
        if self._observer and self._running:
            self._observer.stop()
            self._observer.join()
            self._running = False
            print("File watcher stopped")
            
            # Log stop event
            self._log_system_event("file_watcher_stopped")
    
    def is_running(self):
        """Check if the file watcher is running."""
        return self._running
    
    def _log_system_event(self, event_type, details=None):
        """Log a system event."""
        try:
            db_manager.log_system_event(
                event_type=event_type, 
                source="file_watcher",
                details=details
            )
        except Exception as e:
            print(f"Error logging system event: {e}")
    
    def log_manual_interaction(self, rule_name, interaction_type, metadata=None, application=None):
        """
        Manually log a file interaction without going through the file system events.
        
        This is useful for tracking interactions that aren't file system events,
        such as programmatic access or integrations with editors.
        
        Args:
            rule_name: Name of the rule (e.g., '05-new-task')
            interaction_type: Type of interaction (e.g., 'read', 'execute', 'validate')
            metadata: Optional dictionary with additional information
            application: Source application (e.g., 'vscode', 'api')
        
        Returns:
            True if logging succeeded, False otherwise
        """
        try:
            # Get the rule ID
            rule = db_manager.get_or_create_rule(rule_name)
            if not rule:
                return False
            
            # Get current context window ID if available
            context_window_id = None
            if hasattr(context_tracker, 'get_current_context_window_id'):
                context_window_id = context_tracker.get_current_context_window_id()
            
            # Log the interaction
            db_manager.log_file_interaction(
                rule_id=rule.id,
                interaction_type=interaction_type,
                metadata=metadata or {},
                context_window_id=context_window_id,
                application=application or "manual_api",
                user_initiated=True
            )
            
            return True
        except Exception as e:
            print(f"Error logging manual interaction: {e}")
            return False
    
    def get_recent_interactions(self, limit=10):
        """Get recent file interactions."""
        return db_manager.get_recent_interactions(limit)


# Create singleton instance
file_watcher = FileWatcher()
