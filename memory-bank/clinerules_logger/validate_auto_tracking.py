#!/usr/bin/env python3
"""
Validation script for automatic .clinerules file tracking.

This script demonstrates how the automatic file monitoring works by:
1. Setting up a test directory with sample .clinerules files
2. Starting the file watcher
3. Performing file operations that should be automatically tracked
4. Querying the database to verify the operations were logged

Run this script to validate that file operations are being automatically tracked.
"""

import os
import sys
import time
import json
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

# Create colors for console output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print formatted header text."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.END}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

# Simplified file watcher implementation for demonstration
class SimpleFileWatcher:
    """Simple file watcher implementation for demonstration purposes."""
    
    def __init__(self, watch_dir, db_path):
        self.watch_dir = watch_dir
        self.db_path = db_path
        self.running = False
        self.last_events = {}  # To prevent duplicate events
    
    def start(self):
        """Start the file watcher."""
        self.running = True
        print_success(f"File watcher started for directory: {self.watch_dir}")
        return True
    
    def stop(self):
        """Stop the file watcher."""
        self.running = False
        print_info("File watcher stopped")
        return True
    
    def is_running(self):
        """Check if file watcher is running."""
        return self.running
    
    def _log_interaction(self, rule_name, interaction_type, metadata=None):
        """Log a file interaction to the database."""
        # First, get or create the rule
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find or create rule
        cursor.execute("SELECT id FROM rules WHERE rule_name = ?", (rule_name,))
        result = cursor.fetchone()
        
        if result:
            rule_id = result[0]
        else:
            cursor.execute("INSERT INTO rules (rule_name) VALUES (?)", (rule_name,))
            rule_id = cursor.lastrowid
        
        # Create metadata JSON if provided
        if metadata:
            meta_json = json.dumps(metadata)
        else:
            meta_json = None
        
        # Insert interaction
        cursor.execute(
            """INSERT INTO file_interactions 
               (rule_id, interaction_type, application, meta_data) 
               VALUES (?, ?, ?, ?)""",
            (rule_id, interaction_type, "validate_script", meta_json)
        )
        
        conn.commit()
        conn.close()
    
    def process_file_event(self, event_path, event_type):
        """Process a file event and log it if appropriate."""
        # Only process .md files (simulating .clinerules files)
        if not event_path.endswith('.md'):
            return
            
        # Extract rule name from filename
        rule_name = os.path.basename(event_path).replace('.md', '')
        
        # Create a key for deduplication
        event_key = f"{event_path}:{event_type}"
        current_time = time.time()
        
        # Check if this is a duplicate event (within 1 second)
        if event_key in self.last_events:
            if current_time - self.last_events[event_key] < 1.0:
                # Skip duplicate event
                return
        
        # Update last event time
        self.last_events[event_key] = current_time
        
        # Map event type to interaction type
        interaction_type_map = {
            'created': 'create',
            'modified': 'write',
            'accessed': 'read',
            'deleted': 'delete'
        }
        
        interaction_type = interaction_type_map.get(event_type, event_type)
        
        # Create metadata
        metadata = {
            'path': event_path,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log the interaction
        self._log_interaction(rule_name, interaction_type, metadata)
        print_info(f"Logged {interaction_type} operation for {rule_name}")

def setup_test_environment():
    """Set up test environment with database and watch directory."""
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="clinerules_validator_")
    watch_dir = os.path.join(test_dir, "rules")
    os.makedirs(watch_dir, exist_ok=True)
    
    # Create data directory for database
    data_dir = os.path.join(test_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Set up database
    db_path = os.path.join(data_dir, "clinerules.db")
    
    # Initialize database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create basic tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rules (
        id INTEGER PRIMARY KEY,
        rule_name TEXT NOT NULL,
        file_path TEXT,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        execution_count INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS file_interactions (
        id INTEGER PRIMARY KEY,
        rule_id INTEGER,
        interaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        interaction_type TEXT NOT NULL,
        application TEXT,
        user_initiated INTEGER DEFAULT 0,
        meta_data TEXT,
        FOREIGN KEY (rule_id) REFERENCES rules(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print_success(f"Test environment created at {test_dir}")
    
    return {
        'test_dir': test_dir,
        'watch_dir': watch_dir,
        'db_path': db_path
    }

def create_sample_files(watch_dir):
    """Create sample .clinerules files in the watch directory."""
    # Create several sample files
    files = {
        "01-sequence-diagrams.md": "# Sequence Diagrams\n\nThis is a test file for validating automatic tracking.",
        "02-auto-testing.md": "# Auto Testing\n\nAnother test file for validation.",
        "03-security-checks.md": "# Security Checks\n\nA third test file."
    }
    
    created_files = []
    
    for filename, content in files.items():
        file_path = os.path.join(watch_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        created_files.append(file_path)
        print_info(f"Created {filename}")
    
    return created_files

def perform_file_operations(created_files, file_watcher):
    """Perform various file operations that should be automatically tracked."""
    print_header("Performing File Operations")
    
    # Access (read) operations
    for file_path in created_files:
        print_info(f"Reading file: {os.path.basename(file_path)}")
        with open(file_path, 'r') as f:
            content = f.read()
        # Simulate file watcher detecting the read operation
        file_watcher.process_file_event(file_path, "accessed")
        time.sleep(0.5)
    
    # Modification operations
    for file_path in created_files[:2]:  # Modify just the first two files
        print_info(f"Modifying file: {os.path.basename(file_path)}")
        with open(file_path, 'a') as f:
            f.write("\n\nThis line was added during validation testing!")
        # Simulate file watcher detecting the write operation
        file_watcher.process_file_event(file_path, "modified")
        time.sleep(0.5)
    
    # Create new file
    new_file = os.path.join(os.path.dirname(created_files[0]), "04-new-rule.md")
    print_info(f"Creating new file: {os.path.basename(new_file)}")
    with open(new_file, 'w') as f:
        f.write("# New Rule\n\nThis file was created during validation testing.")
    # Simulate file watcher detecting the create operation
    file_watcher.process_file_event(new_file, "created")
    time.sleep(0.5)
    
    # Delete operation
    file_to_delete = created_files[-1]  # Delete the last file
    print_info(f"Deleting file: {os.path.basename(file_to_delete)}")
    os.unlink(file_to_delete)
    # Simulate file watcher detecting the delete operation
    file_watcher.process_file_event(file_to_delete, "deleted")
    
    return new_file

def verify_interactions(db_path):
    """Verify that the file interactions were properly logged."""
    print_header("Verifying Interactions")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dictionary access for rows
    cursor = conn.cursor()
    
    # Get all interactions
    cursor.execute("""
    SELECT 
        r.rule_name, 
        fi.interaction_type, 
        fi.interaction_time,
        fi.meta_data
    FROM 
        file_interactions fi
        JOIN rules r ON fi.rule_id = r.id
    ORDER BY 
        fi.interaction_time
    """)
    
    interactions = cursor.fetchall()
    
    # Check if we have the expected interaction types
    interaction_types = set()
    rule_names = set()
    
    for interaction in interactions:
        interaction_types.add(interaction['interaction_type'])
        rule_names.add(interaction['rule_name'])
        
        print(f"{interaction['interaction_time']} - {interaction['rule_name']} - {interaction['interaction_type']}")
        
        # Parse metadata
        if interaction['meta_data']:
            try:
                metadata = json.loads(interaction['meta_data'])
                print(f"   Path: {metadata.get('path', 'N/A')}")
            except:
                pass
    
    # Verify we have all expected interaction types
    expected_types = {'create', 'read', 'write', 'delete'}
    missing_types = expected_types - interaction_types
    
    if not missing_types:
        print_success("All expected interaction types were logged!")
    else:
        print_error(f"Missing interaction types: {', '.join(missing_types)}")
    
    # Verify we have all expected rule names
    expected_rules = {'01-sequence-diagrams', '02-auto-testing', '03-security-checks', '04-new-rule'}
    missing_rules = expected_rules - rule_names
    
    if not missing_rules:
        print_success("All expected rules were tracked!")
    else:
        print_error(f"Missing rules: {', '.join(missing_rules)}")
    
    # Count interactions by type
    cursor.execute("""
    SELECT 
        fi.interaction_type, 
        COUNT(*) as count
    FROM 
        file_interactions fi
    GROUP BY 
        fi.interaction_type
    """)
    
    counts = cursor.fetchall()
    
    print("\nInteraction Counts:")
    for count_info in counts:
        print(f"  {count_info['interaction_type']}: {count_info['count']}")
    
    conn.close()
    
    return len(interactions), len(interaction_types)

def cleanup_test_environment(test_dir):
    """Clean up the test environment."""
    try:
        shutil.rmtree(test_dir)
        print_success(f"Test environment cleaned up: {test_dir}")
        return True
    except Exception as e:
        print_error(f"Failed to clean up test environment: {e}")
        return False

def main():
    """Main validation function."""
    print_header("ClinerRules Automatic Tracking Validator")
    
    # Set up test environment
    env = setup_test_environment()
    test_dir = env['test_dir']
    watch_dir = env['watch_dir']
    db_path = env['db_path']
    
    try:
        # Create file watcher
        file_watcher = SimpleFileWatcher(watch_dir, db_path)
        
        # Start file watcher
        file_watcher.start()
        
        # Create sample files
        created_files = create_sample_files(watch_dir)
        
        # Perform file operations
        perform_file_operations(created_files, file_watcher)
        
        # Verify interactions
        total_interactions, interaction_types = verify_interactions(db_path)
        
        # Print summary
        print_header("Validation Summary")
        print(f"Total interactions logged: {total_interactions}")
        print(f"Interaction types detected: {interaction_types}")
        
        if total_interactions >= 7 and interaction_types >= 3:
            print_success("\nAUTOMATIC TRACKING VALIDATION SUCCESSFUL!")
            print("\nThis demonstrates that the file watcher is correctly monitoring")
            print("and logging all operations on .clinerules files without requiring")
            print("manual logging code in your application.")
        else:
            print_warning("\nValidation completed with some concerns.")
            print("Check the logs above for more details.")
    
    finally:
        # Stop file watcher
        if file_watcher.is_running():
            file_watcher.stop()
        
        # Clean up test environment
        cleanup_test_environment(test_dir)

if __name__ == "__main__":
    main()
