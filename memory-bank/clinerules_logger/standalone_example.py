#!/usr/bin/env python3
"""
Standalone example of enhanced .clinerules logger functionality.
This file can be run directly without any dependencies on SQLAlchemy or other modules.
"""

import os
import sys
import json
import datetime
import sqlite3
from pathlib import Path

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
LEGACY_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "clinerules.log")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

class SimpleLogger:
    """A simplified version of the logger that works without dependencies."""
    
    def __init__(self):
        """Initialize the logger."""
        self.log_file = os.path.join(DATA_DIR, "simple_logger.log")
        self._ensure_log_exists()
    
    def _ensure_log_exists(self):
        """Ensure the log file exists with headers."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("Timestamp | Rule Name | Component Name | Task Document | Context Window Usage\n")
                f.write("-" * 100 + "\n")
    
    def log_execution(self, rule_name, component_name, task_document=None, context_window_usage=None):
        """Log a rule execution."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the log entry
        log_entry = f"{timestamp} | {rule_name} | {component_name} | {task_document or 'N/A'} | {context_window_usage or 'N/A'}\n"
        
        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        
        print(f"Execution logged: {rule_name} > {component_name}")
        return log_entry
    
    def import_legacy_log(self):
        """Import data from legacy log file if it exists."""
        if not os.path.exists(LEGACY_LOG_PATH):
            print(f"Legacy log file not found at {LEGACY_LOG_PATH}")
            return False
        
        try:
            with open(LEGACY_LOG_PATH, 'r') as legacy_file, open(self.log_file, 'a') as new_file:
                # Skip header and separator lines
                lines = legacy_file.readlines()[2:]
                
                imported_count = 0
                for line in lines:
                    if not line.strip() or line.startswith('-'):
                        continue
                        
                    parts = [part.strip() for part in line.split('|')]
                    if len(parts) < 4:  # Need at least checkpoint_id, timestamp, task_context, clinerule
                        continue
                    
                    # Extract data
                    _, timestamp, task_document, rule_name, component_name = parts[:5]
                    
                    # Format as new log entry
                    new_entry = f"{timestamp} | {rule_name} | {component_name} | {task_document} | Imported from legacy\n"
                    new_file.write(new_entry)
                    imported_count += 1
                
                print(f"Imported {imported_count} entries from legacy log")
                return True
                
        except Exception as e:
            print(f"Error importing legacy log: {e}")
            return False
    
    def analyze_usage(self):
        """Analyze rule usage patterns."""
        if not os.path.exists(self.log_file):
            print("No log file found to analyze")
            return
        
        try:
            # Count rule executions
            rule_counts = {}
            component_counts = {}
            
            with open(self.log_file, 'r') as f:
                # Skip header and separator
                lines = f.readlines()[2:]
                
                for line in lines:
                    if not line.strip():
                        continue
                        
                    parts = [part.strip() for part in line.split('|')]
                    if len(parts) < 3:
                        continue
                        
                    # Extract rule and component
                    _, rule_name, component_name = parts[:3]
                    
                    # Count rules
                    rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
                    
                    # Count components
                    key = f"{rule_name} > {component_name}"
                    component_counts[key] = component_counts.get(key, 0) + 1
            
            # Display results
            print("\n=== Rule Usage Analysis ===")
            
            print("\nTop Rules:")
            for rule, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"{rule}: {count} executions")
            
            print("\nTop Components:")
            for comp, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"{comp}: {count} executions")
                
            return {
                'rule_counts': rule_counts,
                'component_counts': component_counts,
                'total_entries': len(lines)
            }
            
        except Exception as e:
            print(f"Error analyzing usage: {e}")
            return None
    
    def backup_log(self):
        """Create a backup of the log file."""
        if not os.path.exists(self.log_file):
            print("No log file to backup")
            return False
        
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup", "data")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"log_backup_{timestamp}.txt")
            
            # Copy file
            with open(self.log_file, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
                
            print(f"Backup created: {backup_file}")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def export_metrics(self, output_file=None):
        """Export metrics to a JSON file."""
        metrics = self.analyze_usage()
        
        if not metrics:
            return False
            
        try:
            # Create default filename if not provided
            if not output_file:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(DATA_DIR, f"metrics_{timestamp}.json")
                
            # Add timestamp to metrics
            metrics['generated_at'] = datetime.datetime.now().isoformat()
            
            # Write to file
            with open(output_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
            print(f"Metrics exported to {output_file}")
            return True
            
        except Exception as e:
            print(f"Error exporting metrics: {e}")
            return False


def run_interactive_demo():
    """Run an interactive demo of the Simple Logger."""
    logger = SimpleLogger()
    
    # Welcome message
    print("\n=== Enhanced .clinerules Logger (Standalone Demo) ===")
    print("This demo shows the core functionality without requiring complex setup.")
    
    # Import legacy data if it exists
    if os.path.exists(LEGACY_LOG_PATH):
        print("\nLegacy log file found. Importing data...")
        logger.import_legacy_log()
    
    while True:
        print("\nDemo Menu:")
        print("1. Log a Rule Execution")
        print("2. Analyze Rule Usage")
        print("3. Create Backup")
        print("4. Export Metrics")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            # Log a rule execution
            print("\n--- Log Rule Execution ---")
            rule_name = input("Rule Name (e.g., 05-new-task): ")
            component_name = input("Component Name (e.g., Update GitHub Repository): ")
            task_document = input("Task Document (optional): ")
            context_usage = input("Context Window Usage (optional): ")
            
            logger.log_execution(rule_name, component_name, task_document, context_usage)
            
        elif choice == "2":
            # Analyze rule usage
            print("\n--- Analyzing Rule Usage ---")
            logger.analyze_usage()
            
        elif choice == "3":
            # Create backup
            print("\n--- Creating Backup ---")
            logger.backup_log()
            
        elif choice == "4":
            # Export metrics
            print("\n--- Exporting Metrics ---")
            logger.export_metrics()
            
        elif choice == "5":
            # Exit
            print("\nThank you for using the Standalone Demo!")
            break
            
        else:
            print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    run_interactive_demo()
