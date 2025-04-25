#!/usr/bin/env python3
"""
Simple setup and demonstration script for the ClinerRules Logger.

This standalone script demonstrates the basic functionality of the
ClinerRules Logger without requiring package installation. It creates
the necessary database tables and logs some sample interactions.
"""

import os
import sys
import json
import time
import sqlite3
import datetime
from pathlib import Path

# Simple helper functions for demonstration purposes
def setup_database(db_path):
    """Set up a simple SQLite database."""
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_events (
        id INTEGER PRIMARY KEY,
        event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        event_type TEXT NOT NULL,
        source TEXT,
        event_details TEXT
    )
    ''')
    
    # Commit and close
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")
    return True

def get_or_create_rule(db_path, rule_name, file_path=None):
    """Get or create a rule record."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if rule exists
    cursor.execute("SELECT id FROM rules WHERE rule_name = ?", (rule_name,))
    result = cursor.fetchone()
    
    if result:
        rule_id = result[0]
    else:
        # Create new rule
        cursor.execute(
            "INSERT INTO rules (rule_name, file_path) VALUES (?, ?)",
            (rule_name, file_path)
        )
        rule_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return rule_id

def log_file_interaction(db_path, rule_name, interaction_type, metadata=None, application="demo_script"):
    """Log a file interaction."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get or create rule
    rule_id = get_or_create_rule(db_path, rule_name)
    
    # Prepare metadata
    if metadata:
        meta_json = json.dumps(metadata)
    else:
        meta_json = None
    
    # Log interaction
    cursor.execute(
        "INSERT INTO file_interactions (rule_id, interaction_type, application, meta_data) VALUES (?, ?, ?, ?)",
        (rule_id, interaction_type, application, meta_json)
    )
    
    conn.commit()
    conn.close()
    print(f"Logged {interaction_type} interaction for rule '{rule_name}'")

def log_system_event(db_path, event_type, source="demo", details=None):
    """Log a system event."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prepare details
    if details:
        details_json = json.dumps(details)
    else:
        details_json = None
    
    # Log event
    cursor.execute(
        "INSERT INTO system_events (event_type, source, event_details) VALUES (?, ?, ?)",
        (event_type, source, details_json)
    )
    
    conn.commit()
    conn.close()
    print(f"Logged system event: {event_type}")

def list_recent_interactions(db_path, limit=10):
    """List recent file interactions."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        rules.rule_name,
        file_interactions.interaction_type,
        file_interactions.interaction_time,
        file_interactions.application,
        file_interactions.meta_data
    FROM 
        file_interactions
    JOIN 
        rules ON file_interactions.rule_id = rules.id
    ORDER BY 
        file_interactions.interaction_time DESC
    LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    interactions = cursor.fetchall()
    
    print("\nRecent File Interactions:")
    print("-" * 80)
    for interaction in interactions:
        rule_name, interaction_type, timestamp, application, meta_data = interaction
        
        # Parse metadata if available
        if meta_data:
            try:
                metadata_dict = json.loads(meta_data)
                meta_str = json.dumps(metadata_dict, indent=2)
            except:
                meta_str = meta_data
        else:
            meta_str = "None"
        
        print(f"Rule: {rule_name}")
        print(f"Type: {interaction_type}")
        print(f"Time: {timestamp}")
        print(f"App:  {application}")
        print(f"Meta: {meta_str}")
        print("-" * 80)
    
    conn.close()

def get_statistics(db_path):
    """Get basic statistics."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count interactions by type
    cursor.execute("""
    SELECT interaction_type, COUNT(*) 
    FROM file_interactions 
    GROUP BY interaction_type
    """)
    interaction_counts = cursor.fetchall()
    
    # Count interactions by rule
    cursor.execute("""
    SELECT rules.rule_name, COUNT(*)
    FROM file_interactions
    JOIN rules ON file_interactions.rule_id = rules.id
    GROUP BY rules.rule_name
    ORDER BY COUNT(*) DESC
    LIMIT 5
    """)
    rule_counts = cursor.fetchall()
    
    # Count interactions by application
    cursor.execute("""
    SELECT application, COUNT(*)
    FROM file_interactions
    GROUP BY application
    """)
    app_counts = cursor.fetchall()
    
    print("\nStatistics:")
    print("-" * 80)
    
    print("Interactions by Type:")
    for type_name, count in interaction_counts:
        print(f"  {type_name}: {count}")
    
    print("\nTop Rules:")
    for rule_name, count in rule_counts:
        print(f"  {rule_name}: {count}")
    
    print("\nApplications:")
    for app_name, count in app_counts:
        print(f"  {app_name}: {count}")
    
    print("-" * 80)
    
    conn.close()

def main():
    """Main demonstration function."""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set up database in the data directory
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "clinerules_demo.db")
    
    print("\n=== ClinerRules Logger Simple Setup ===\n")
    
    # Initialize database
    if not os.path.exists(db_path):
        print("Setting up new database...")
        setup_database(db_path)
    else:
        print(f"Using existing database at {db_path}")
    
    # Log startup event
    log_system_event(db_path, "demo_startup", details={
        "timestamp": datetime.datetime.now().isoformat(),
        "script": os.path.basename(__file__)
    })
    
    # Log some sample interactions
    print("\nLogging sample interactions...")
    
    # First rule
    log_file_interaction(db_path, "01-sequence-diagrams", "read", metadata={
        "source": "demo",
        "path": "~/OneDrive/Documents/Cline/Rules/01-sequence-diagrams.md"
    })
    
    # Short delay for demo
    time.sleep(0.5)
    
    log_file_interaction(db_path, "01-sequence-diagrams", "execute", metadata={
        "source": "demo",
        "component": "Task Planning Visualization Protocol"
    })
    
    # Second rule
    time.sleep(0.5)
    
    log_file_interaction(db_path, "02-auto-testing", "read", metadata={
        "source": "demo",
        "path": "~/OneDrive/Documents/Cline/Rules/02-auto-testing.md"
    })
    
    time.sleep(0.5)
    
    # Log a file modification
    log_file_interaction(db_path, "05-new-task", "write", metadata={
        "source": "demo",
        "path": "~/OneDrive/Documents/Cline/Rules/05-new-task.md",
        "changes": "Updated formatting in the task handoff section."
    })
    
    # List recent interactions
    list_recent_interactions(db_path)
    
    # Show statistics
    get_statistics(db_path)
    
    print("\nSimple setup complete! You can now explore the database at:")
    print(f"{db_path}")
    print("\nUse this script as a starting point for your own applications.")

if __name__ == "__main__":
    main()
