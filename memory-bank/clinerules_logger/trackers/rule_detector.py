#!/usr/bin/env python3
"""
Rule detector module for .clinerules logger.
"""

import os
import re
import json
import sys
import importlib.util
from pathlib import Path
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
    # Try direct import first from context window module
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
        # If context_tracker import fails, create a dummy
        class DummyContextTracker:
            def log_rule_execution(self, *args, **kwargs):
                print("Warning: Using dummy context tracker")
                return {"status": "dummy"}
        context_tracker = DummyContextTracker()

# Try different import approaches for config and db_manager
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
        try:
            # Try absolute import with memory_bank prefix
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
                    def get_or_create_rule(self, *args, **kwargs):
                        class DummyRule:
                            id = 0
                        return DummyRule()
                    
                    def get_or_create_component(self, *args, **kwargs):
                        return True
                
                db_manager = DummyDBManager()
                config = DummyConfig()
                print("Warning: Using dummy manager and config due to import failures")

class RuleDetector:
    """Detects and parses .clinerules files and their executions."""
    
    _instance = None
    _rules_dir = Path(os.path.expanduser("~")) / "OneDrive" / "Documents" / "Cline" / "Rules"
    _cached_rules = {}
    
    def __new__(cls):
        """Singleton pattern to ensure only one rule detector instance."""
        if cls._instance is None:
            cls._instance = super(RuleDetector, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the rule detector."""
        self._scan_rules_directory()
    
    def _scan_rules_directory(self):
        """Scan the .clinerules directory and cache rule information."""
        if not os.path.exists(self._rules_dir):
            print(f"Warning: Rules directory not found at {self._rules_dir}")
            return
            
        for file_path in self._rules_dir.glob("*.md"):
            rule_name = file_path.stem
            self._parse_rule_file(rule_name, file_path)
    
    def _parse_rule_file(self, rule_name, file_path):
        """Parse a .clinerules file to extract components and structure."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Create rule in database if it doesn't exist
            rule = db_manager.get_or_create_rule(
                rule_name=rule_name,
                file_path=str(file_path),
                description=self._extract_description(content)
            )
            
            # Extract components
            components = self._extract_components(content)
            
            # Create components in database if they don't exist
            for comp_name, comp_desc in components.items():
                db_manager.get_or_create_component(
                    rule_id=rule.id,
                    component_name=comp_name,
                    description=comp_desc
                )
            
            # Cache rule information
            self._cached_rules[rule_name] = {
                'id': rule.id,
                'path': str(file_path),
                'components': components
            }
            
        except Exception as e:
            print(f"Error parsing rule file {file_path}: {e}")
    
    def _extract_description(self, content):
        """Extract the description from the rule file content."""
        # Try to get the first h1 title as description
        h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
            
        # Fallback to first paragraph
        p_match = re.search(r'^(.+?)(\n\n|\n#|$)', content, re.DOTALL)
        if p_match:
            return p_match.group(1).strip()
            
        return "No description available"
    
    def _extract_components(self, content):
        """Extract components from the rule file content."""
        components = {}
        
        # Look for headers as components
        for match in re.finditer(r'^(#{2,4}) (.+)$', content, re.MULTILINE):
            level = len(match.group(1))
            component_name = match.group(2).strip()
            
            # Get paragraph after header as description
            desc_match = re.search(r'{}[^\n]*\n\n(.+?)(\n\n|\n#|$)'.format(re.escape(match.group(0))), 
                                 content, re.DOTALL)
            
            description = desc_match.group(1).strip() if desc_match else "No description available"
            components[component_name] = description
        
        # If no headers found, use the rule itself as the only component
        if not components:
            components["Main Rule"] = self._extract_description(content)
            
        return components
    
    def refresh_rules_cache(self):
        """Refresh the rules cache by rescanning the rules directory."""
        self._cached_rules = {}
        self._scan_rules_directory()
    
    def get_rule_details(self, rule_name):
        """Get details about a specific rule."""
        # Check cache first
        if rule_name in self._cached_rules:
            return self._cached_rules[rule_name]
            
        # Look for the rule file
        rule_path = self._rules_dir / f"{rule_name}.md"
        if not os.path.exists(rule_path):
            return None
            
        # Parse and cache the rule
        self._parse_rule_file(rule_name, rule_path)
        return self._cached_rules.get(rule_name)
    
    def log_rule_execution(self, rule_name, component_name, task_document=None, notes=None):
        """Log a rule execution."""
        # Get rule details
        rule_details = self.get_rule_details(rule_name)
        if not rule_details:
            # Try to create the rule if it doesn't exist in our cache
            rule = db_manager.get_or_create_rule(rule_name=rule_name)
            if not rule:
                return None
                
            db_manager.get_or_create_component(
                rule_id=rule.id,
                component_name=component_name
            )
            
            # Refresh the cache for next time
            self.refresh_rules_cache()
        
        # Log the execution using the context tracker
        return context_tracker.log_rule_execution(
            rule_name=rule_name,
            component_name=component_name,
            task_document=task_document,
            notes=notes
        )
    
    def analyze_rule_executions(self, rule_name=None, time_period=None):
        """
        Analyze rule executions for patterns and insights.
        
        This is a placeholder for the analytics module.
        """
        return {
            'status': 'Analysis not implemented yet',
            'rule_name': rule_name,
            'time_period': time_period
        }
    
    def detect_rules_from_text(self, text):
        """
        Detect references to .clinerules files in text.
        
        This can be used to automatically detect when rules are being discussed
        or referenced in conversations.
        """
        detected_rules = []
        
        # Look for patterns like "05-new-task" or "05-new-task.md"
        for match in re.finditer(r'\b(\d{2}-[\w-]+)(?:\.md)?\b', text):
            rule_name = match.group(1)
            if self.get_rule_details(rule_name) or os.path.exists(self._rules_dir / f"{rule_name}.md"):
                detected_rules.append(rule_name)
        
        # Also look for full references like "MANDATORY Test Automation" (titles)
        for rule_name, details in self._cached_rules.items():
            desc = details.get('description', '')
            if desc and desc in text:
                detected_rules.append(rule_name)
        
        return list(set(detected_rules))  # Remove duplicates

# Create singleton instance
rule_detector = RuleDetector()
