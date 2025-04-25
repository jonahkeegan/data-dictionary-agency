#!/usr/bin/env python3
"""
Configuration module for the enhanced .clinerules logger.
"""

import os
import json
import sys
from pathlib import Path

class Config:
    """Configuration manager for the enhanced .clinerules logger."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one configuration instance."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the configuration with default values."""
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self._config = {
            'database': {
                'path': os.path.join(current_dir, 'data', 'clinerules.db'),
                'backup_dir': os.path.join(current_dir, 'backup', 'data'),
                'backup_interval_hours': 24,
                'backup_retention_days': 30,
                'backup_prefix': 'clinerules_backup_'
            },
            'context_window': {
                'track_sessions': True
            },
            'notification': {
                'enabled': True,
                'threshold': 5,
                'window_hours': 24
            },
            'legacy': {
                'log_path': os.path.join(current_dir, '..', 'clinerules.log'),
                'import_on_startup': True
            }
        }
        
        # Create data directory if it doesn't exist
        data_dir = os.path.dirname(self._config['database']['path'])
        os.makedirs(data_dir, exist_ok=True)
        
        # Create backup directory if it doesn't exist
        backup_dir = self._config['database']['backup_dir']
        os.makedirs(backup_dir, exist_ok=True)
    
    def get(self, section, key, default=None):
        """Get a configuration value."""
        if section not in self._config:
            return default
        
        if key not in self._config[section]:
            return default
        
        return self._config[section][key]
    
    def set(self, section, key, value):
        """Set a configuration value."""
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section][key] = value
    
    def save(self, config_path=None):
        """Save configuration to file."""
        if not config_path:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, 'config.json')
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load(self, config_path=None):
        """Load configuration from file."""
        if not config_path:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, 'config.json')
        
        if not os.path.exists(config_path):
            return False
        
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                
                # Update only existing sections/keys
                for section, section_config in loaded_config.items():
                    if section not in self._config:
                        self._config[section] = {}
                        
                    for key, value in section_config.items():
                        self._config[section][key] = value
                        
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

# Create singleton instance
config = Config()
