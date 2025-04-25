#!/usr/bin/env python3
"""
VSCode integration module for .clinerules logger.

This module provides integration with VS Code to track interactions
with .clinerules files within the editor environment.
"""

import os
import sys
import json
import socket
import threading
import importlib.util
from pathlib import Path
from datetime import datetime

# Add paths for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
clinerules_dir = os.path.dirname(current_dir)
trackers_dir = os.path.join(clinerules_dir, "trackers")
db_dir = os.path.join(clinerules_dir, "db")
utils_dir = os.path.join(clinerules_dir, "utils")

for directory in [trackers_dir, db_dir, utils_dir]:
    if directory not in sys.path:
        sys.path.insert(0, directory)

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

# Try to load required modules
try:
    # Try to import file_watcher first
    file_watcher_path = os.path.join(trackers_dir, "file_watcher.py")
    file_watcher_module = load_module_from_path(file_watcher_path, "file_watcher")
    file_watcher = file_watcher_module.file_watcher
except ImportError:
    try:
        # Try relative import
        from ..trackers.file_watcher import file_watcher
    except ImportError:
        print("Warning: Could not import file_watcher")
        file_watcher = None

# Try to load context_tracker
try:
    context_window_path = os.path.join(trackers_dir, "context_window.py")
    context_window_module = load_module_from_path(context_window_path, "context_window")
    context_tracker = context_window_module.context_tracker
except ImportError:
    try:
        # Try relative import
        from ..trackers.context_window import context_tracker
    except ImportError:
        print("Warning: Could not import context_tracker")
        context_tracker = None

# Try to load db_manager
try:
    manager_path = os.path.join(db_dir, "manager.py")
    manager_module = load_module_from_path(manager_path, "manager")
    db_manager = manager_module.db_manager
except ImportError:
    try:
        # Try relative import
        from ..db.manager import db_manager
    except ImportError:
        print("Warning: Could not import db_manager")
        db_manager = None

# Try to load config
try:
    config_path = os.path.join(utils_dir, "config.py")
    config_module = load_module_from_path(config_path, "config")
    config = config_module.config
except ImportError:
    try:
        # Try relative import
        from ..utils.config import config
    except ImportError:
        print("Warning: Could not import config")
        config = None


class VSCodeIntegration:
    """
    VSCode integration for .clinerules logger.
    
    This class provides integration with VS Code to automatically
    track interactions with .clinerules files within the editor.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one integration instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VSCodeIntegration, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """Initialize the integration."""
        self._enabled = self._check_enabled()
        self._port = self._get_config_port()
        self._server_thread = None
        self._running = False
        
        # If file_watcher isn't available, we can't function
        if not file_watcher:
            print("VSCode integration disabled: file_watcher not available")
            self._enabled = False
        
        if self._enabled:
            self._start_server()
    
    def _check_enabled(self):
        """Check if the integration is enabled in config."""
        if not config:
            return True  # Default to enabled if config not available
        
        try:
            return config.get('integrations', 'vscode_enabled', True)
        except:
            return True  # Default to enabled if error
    
    def _get_config_port(self):
        """Get the server port from config."""
        if not config:
            return 5678  # Default port
        
        try:
            return config.get('integrations', 'vscode_port', 5678)
        except:
            return 5678  # Default port
    
    def _start_server(self):
        """Start the server in a background thread."""
        if not self._enabled or self._running:
            return
        
        self._server_thread = threading.Thread(target=self._run_server)
        self._server_thread.daemon = True
        self._server_thread.start()
    
    def _run_server(self):
        """Run the server to listen for requests from VSCode."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(('127.0.0.1', self._port))
                server.listen(5)
                self._running = True
                
                print(f"VSCode integration server started on port {self._port}")
                
                # Log start event
                if db_manager:
                    db_manager.log_system_event(
                        event_type="vscode_integration_started",
                        source="vscode_integration",
                        details={"port": self._port}
                    )
                
                while self._running:
                    try:
                        server.settimeout(1.0)  # 1 second timeout for clean shutdown
                        client, addr = server.accept()
                        self._handle_client(client)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"Server error: {e}")
                        if self._running:
                            # Log error but continue running
                            if db_manager:
                                db_manager.log_system_event(
                                    event_type="vscode_integration_error",
                                    source="vscode_integration",
                                    details={"error": str(e)}
                                )
        except Exception as e:
            print(f"Failed to start VSCode integration server: {e}")
            self._running = False
    
    def _handle_client(self, client_socket):
        """Handle a client connection."""
        try:
            # Set a timeout to prevent hanging on incomplete requests
            client_socket.settimeout(5.0)
            
            # Read data from the client
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check for end of message marker
                if data.endswith(b"\n\n"):
                    break
            
            # Process the request
            if data:
                try:
                    request = json.loads(data.decode('utf-8').strip())
                    response = self._process_request(request)
                    
                    # Send response back to client
                    client_socket.sendall(json.dumps(response).encode('utf-8') + b"\n\n")
                except json.JSONDecodeError:
                    # Send error response for invalid JSON
                    error_response = {
                        "success": False,
                        "error": "Invalid JSON request"
                    }
                    client_socket.sendall(json.dumps(error_response).encode('utf-8') + b"\n\n")
        except socket.timeout:
            # Send error response for timeout
            error_response = {
                "success": False,
                "error": "Request timeout"
            }
            client_socket.sendall(json.dumps(error_response).encode('utf-8') + b"\n\n")
        except Exception as e:
            # Send error response for other exceptions
            error_response = {
                "success": False,
                "error": str(e)
            }
            client_socket.sendall(json.dumps(error_response).encode('utf-8') + b"\n\n")
        finally:
            # Close the client socket
            client_socket.close()
    
    def _process_request(self, request):
        """Process a request from VSCode."""
        if not isinstance(request, dict) or 'action' not in request:
            return {
                "success": False,
                "error": "Invalid request format"
            }
        
        action = request.get('action')
        
        # Process based on action type
        if action == 'log_interaction':
            return self._handle_log_interaction(request)
        elif action == 'log_rule_execution':
            return self._handle_log_rule_execution(request)
        elif action == 'get_recent_interactions':
            return self._handle_get_recent_interactions(request)
        elif action == 'ping':
            return {
                "success": True,
                "message": "pong",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
    
    def _handle_log_interaction(self, request):
        """Handle a log_interaction request."""
        if not file_watcher:
            return {
                "success": False,
                "error": "File watcher not available"
            }
        
        rule_name = request.get('rule_name')
        interaction_type = request.get('interaction_type')
        metadata = request.get('metadata', {})
        application = request.get('application', 'vscode')
        
        if not rule_name or not interaction_type:
            return {
                "success": False,
                "error": "Missing required parameters"
            }
        
        # Add VSCode-specific metadata
        metadata['source'] = 'vscode_integration'
        metadata['timestamp'] = datetime.now().isoformat()
        
        # Log the interaction
        success = file_watcher.log_manual_interaction(
            rule_name=rule_name,
            interaction_type=interaction_type,
            metadata=metadata,
            application=application
        )
        
        return {
            "success": success,
            "rule_name": rule_name,
            "interaction_type": interaction_type,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_log_rule_execution(self, request):
        """Handle a log_rule_execution request."""
        if not context_tracker or not db_manager:
            return {
                "success": False,
                "error": "Required modules not available"
            }
        
        rule_name = request.get('rule_name')
        component_name = request.get('component_name')
        task_document = request.get('task_document')
        notes = request.get('notes')
        
        if not rule_name:
            return {
                "success": False,
                "error": "Missing rule_name parameter"
            }
        
        # Get or create rule
        rule = db_manager.get_or_create_rule(rule_name)
        if not rule:
            return {
                "success": False,
                "error": f"Failed to create rule: {rule_name}"
            }
        
        # Get current context window ID
        context_window_id = context_tracker.get_current_context_window_id()
        
        # Log rule execution
        rule_exec = db_manager.log_rule_execution(
            context_window_id=context_window_id,
            rule_id=rule.id,
            task_document=task_document,
            notes=notes
        )
        
        # If component name provided, log component execution
        if component_name and rule_exec:
            # Get or create component
            component = db_manager.get_or_create_component(
                rule_id=rule.id,
                component_name=component_name
            )
            
            if component:
                db_manager.log_component_execution(
                    rule_execution_id=rule_exec.id,
                    component_id=component.id,
                    notes=notes
                )
        
        return {
            "success": bool(rule_exec),
            "rule_name": rule_name,
            "component_name": component_name,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_get_recent_interactions(self, request):
        """Handle a get_recent_interactions request."""
        if not file_watcher:
            return {
                "success": False,
                "error": "File watcher not available"
            }
        
        limit = int(request.get('limit', 10))
        interactions = file_watcher.get_recent_interactions(limit=limit)
        
        # Format interactions for response
        formatted_interactions = []
        for interaction in interactions:
            formatted_interactions.append({
                "id": interaction.id,
                "rule_name": interaction.rule.rule_name if interaction.rule else None,
                "interaction_type": interaction.interaction_type,
                "interaction_time": interaction.interaction_time.isoformat(),
                "application": interaction.application,
                "metadata": interaction.get_metadata() if hasattr(interaction, 'get_metadata') else {}
            })
        
        return {
            "success": True,
            "interactions": formatted_interactions,
            "timestamp": datetime.now().isoformat()
        }
    
    def stop(self):
        """Stop the integration server."""
        self._running = False
        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=5.0)
            
            # Log stop event
            if db_manager:
                db_manager.log_system_event(
                    event_type="vscode_integration_stopped",
                    source="vscode_integration"
                )
    
    def is_running(self):
        """Check if the integration server is running."""
        return self._running
    
    def log_interaction(self, rule_name, interaction_type, metadata=None, application='vscode_direct'):
        """
        Log a file interaction directly from Python code.
        
        This is useful for cases where you want to log an interaction
        without going through the network server.
        
        Args:
            rule_name: Name of the rule (e.g., '05-new-task')
            interaction_type: Type of interaction (e.g., 'read', 'execute', 'validate')
            metadata: Optional dictionary with additional information
            application: Source application (default: 'vscode_direct')
        
        Returns:
            True if logging succeeded, False otherwise
        """
        if not file_watcher:
            return False
        
        if not metadata:
            metadata = {}
        
        # Add VSCode-specific metadata
        metadata['source'] = 'vscode_integration_direct'
        metadata['timestamp'] = datetime.now().isoformat()
        
        return file_watcher.log_manual_interaction(
            rule_name=rule_name,
            interaction_type=interaction_type,
            metadata=metadata,
            application=application
        )


# Create singleton instance
vscode_integration = VSCodeIntegration()

# For testing directly
if __name__ == "__main__":
    import time
    
    print("Starting VSCode integration testing...")
    
    # Wait for a bit to allow server to start
    time.sleep(2)
    
    # Check if running
    print(f"Integration server running: {vscode_integration.is_running()}")
    
    # Try direct logging
    result = vscode_integration.log_interaction(
        rule_name='test-rule',
        interaction_type='test',
        metadata={'test': True},
        application='test_script'
    )
    print(f"Direct logging result: {result}")
    
    # Keep running for a bit to allow server to receive connections
    try:
        while vscode_integration.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping on keyboard interrupt")
        vscode_integration.stop()
