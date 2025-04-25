#!/usr/bin/env python3
"""
Context window tracking module for .clinerules logger.
"""

import os
import re
import uuid
import json
import sys
import importlib.util
from datetime import datetime

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
    # Try direct import
    import manager
    db_manager = manager.db_manager
    import config
    config = config.config
except ImportError:
    try:
        # Try relative import
        from ..db.manager import db_manager
        from ..utils.config import config
    except ImportError:
        # Try absolute import with memory_bank prefix
        try:
            from memory_bank.clinerules_logger.db.manager import db_manager
            from memory_bank.clinerules_logger.utils.config import config
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
                # Fallback to create dummy objects for minimal functionality
                class DummyConfig:
                    def get(self, *args, **kwargs):
                        return True
                
                class DummyDBManager:
                    def start_context_window(self, *args, **kwargs):
                        class DummyContext:
                            id = 0
                        return DummyContext()
                    
                    def update_context_window(self, *args, **kwargs):
                        pass
                    
                    def get_or_create_rule(self, *args, **kwargs):
                        class DummyRule:
                            id = 0
                        return DummyRule()
                    
                    def get_or_create_component(self, *args, **kwargs):
                        class DummyComponent:
                            id = 0
                        return DummyComponent()
                    
                    def log_rule_execution(self, *args, **kwargs):
                        class DummyRuleExec:
                            id = 0
                        return DummyRuleExec()
                    
                    def log_component_execution(self, *args, **kwargs):
                        class DummyCompExec:
                            id = 0
                        return DummyCompExec()
                
                db_manager = DummyDBManager()
                config = DummyConfig()
                print("Warning: Using dummy manager and config due to import failures")

class ContextWindowTracker:
    """Tracks Cline AI context window sessions and rule executions."""
    
    _instance = None
    _active_session_id = None
    _context_window_id = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one context window tracker instance."""
        if cls._instance is None:
            cls._instance = super(ContextWindowTracker, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the context window tracker."""
        self._active_session_id = self._generate_session_id()
        self._start_session()
    
    def _generate_session_id(self):
        """Generate a unique session ID."""
        return f"session_{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _start_session(self):
        """Start a new context window session."""
        if not config.get('context_window', 'track_sessions'):
            return
        
        try:    
            context_window = db_manager.start_context_window(self._active_session_id)
            # Store the ID directly to avoid DetachedInstanceError later
            if hasattr(context_window, 'id'):
                self._context_window_id = context_window.id
            else:
                # If we can't get the ID, generate a fake one
                print("Warning: Could not get context window ID, using fallback")
                self._context_window_id = 0
        except Exception as e:
            print(f"Warning: Error starting context window session: {e}")
            # Assign a default ID so the rest of the code works
            self._context_window_id = 0
    
    def update_token_count(self, token_count):
        """Update the token count for the current context window."""
        if not config.get('context_window', 'track_sessions') or not self._active_session_id:
            return
            
        db_manager.update_context_window(self._active_session_id, token_count=token_count)
    
    def complete_session(self):
        """Mark the current context window session as completed."""
        if not config.get('context_window', 'track_sessions') or not self._active_session_id:
            return
            
        db_manager.update_context_window(self._active_session_id, status='completed')
        self._active_session_id = self._generate_session_id()
        self._start_session()
    
    def get_current_context_window_id(self):
        """Get the ID of the current context window."""
        return self._context_window_id
    
    def reset_session(self):
        """Reset the current session and start a new one."""
        self.complete_session()
    
    @staticmethod
    def extract_tokens_from_environment(env_string):
        """
        Extract token usage from the environment details string.
        
        Looks for patterns like:
        "# Context Window Usage
        105,000 / 200,000 tokens (53%)"
        """
        if not env_string:
            return None
            
        # Look for the context window usage pattern
        pattern = r"# Context Window Usage\s*(\d{1,3}(?:,\d{3})*)\s*\/\s*(\d{1,3}(?:k|K|,\d{3})*)\s*tokens\s*\((\d+)%\)"
        match = re.search(pattern, env_string)
        
        if not match:
            return None
            
        try:
            # Extract values
            used_str = match.group(1).replace(',', '')
            total_str = match.group(2).lower().replace('k', '000').replace(',', '')
            percentage = int(match.group(3))
            
            used = int(used_str)
            total = int(total_str)
            
            return {
                'used': used,
                'total': total,
                'percentage': percentage
            }
        except (ValueError, IndexError):
            return None
    
    def update_from_environment(self, env_string):
        """Update context window information from environment details."""
        if not config.get('context_window', 'track_sessions') or not self._active_session_id:
            return False
            
        token_info = self.extract_tokens_from_environment(env_string)
        if not token_info:
            return False
            
        self.update_token_count(token_info['used'])
        return True
    
    def log_rule_execution(self, rule_name, component_name, task_document=None, notes=None):
        """Log a rule execution in the current context window."""
        if not config.get('context_window', 'track_sessions') or not self._context_window_id:
            return None
            
        # Get or create rule
        rule = db_manager.get_or_create_rule(rule_name)
        if not rule:
            return None
            
        # Get or create component
        component = db_manager.get_or_create_component(rule.id, component_name)
        if not component:
            return None
            
        # Log rule execution
        rule_exec = db_manager.log_rule_execution(
            self._context_window_id,
            rule.id,
            task_document=task_document,
            notes=notes
        )
        if not rule_exec:
            return None
            
        # Log component execution
        comp_exec = db_manager.log_component_execution(
            rule_exec.id,
            component.id,
            notes=notes
        )
        
        return {
            'rule_execution': rule_exec,
            'component_execution': comp_exec
        }
    
    def analyze_current_session(self):
        """Analyze rule executions in the current context window."""
        if not self._context_window_id:
            return None
            
        # This would be implemented in the analytics module
        # For now, return placeholder stats
        return {
            'context_window_id': self._context_window_id,
            'session_id': self._active_session_id,
            'rules_triggered': 0,
            'components_triggered': 0
        }

# Create singleton instance
context_tracker = ContextWindowTracker()
