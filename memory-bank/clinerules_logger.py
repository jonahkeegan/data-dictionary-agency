#!/usr/bin/env python3
"""
.clinerules Task Execution Logger
---------------------------------
Enhanced version with automatic logging, analytics, and notifications.
"""

import os
import sys
import json
import datetime
import argparse
from pathlib import Path

# Make the clinerules_logger package importable
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))

try:
    # Try to import from enhanced system
    from memory_bank.clinerules_logger.main import interactive_log, log_execution, legacy_mode, detect_and_print_patterns, export_metrics
    from memory_bank.clinerules_logger.utils.config import config
    from memory_bank.clinerules_logger.trackers.context_window import context_tracker
    
    # Flag to indicate if enhanced system is available
    ENHANCED_MODE = True
    print("Enhanced mode active: Using SQLite-based logger system")
    
except ImportError:
    # Fall back to legacy mode if enhanced system is not available
    ENHANCED_MODE = False
    print("Legacy mode active: Enhanced system not found, using basic logger")
    
    # Define legacy functionality
    LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinerules.log")
    
    def initialize_log():
        """Initialize the log file with a header if it doesn't exist."""
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'w') as log_file:
                log_file.write("Checkpoint ID | Timestamp | Task Context Document | Referenced .clinerule | Referenced Component\n")
                log_file.write("-" * 120 + "\n")
    
    def get_next_checkpoint_id():
        """Determine the next checkpoint ID by reading the existing log."""
        if not os.path.exists(LOG_PATH):
            return 1
            
        with open(LOG_PATH, 'r') as log_file:
            lines = log_file.readlines()
            if len(lines) <= 2:  # Only header and separator
                return 1
                
            # Get the last non-empty line and extract the ID
            for line in reversed(lines):
                if line.strip():
                    try:
                        return int(line.split('|')[0].strip()) + 1
                    except (ValueError, IndexError):
                        return 1
        return 1
    
    def log_clinerule_execution(task_context, clinerule, component):
        """Generate and append a log entry."""
        initialize_log()
        checkpoint_id = get_next_checkpoint_id()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"{checkpoint_id} | {timestamp} | {task_context} | {clinerule} | {component}\n"
        
        with open(LOG_PATH, 'a') as log_file:
            log_file.write(log_entry)
            
        return log_entry
    
    def create_log_entry():
        """Interactive function to create a log entry."""
        print("=== .clinerules Task Execution Logger (Legacy Mode) ===")
        
        # Get task context document
        task_context = input("Task Context Document (e.g., Task_002): ")
        
        # Get referenced .clinerule
        clinerule = input("Referenced .clinerule (e.g., 05-new-task): ")
        
        # Get referenced component
        component = input("Referenced Component (e.g., 'Update the GitHub repository'): ")
        
        # Create and append log entry
        entry = log_clinerule_execution(task_context, clinerule, component)
        
        print("\nLog entry created successfully:")
        print(entry)
    
    def legacy_mode(args):
        """Handle legacy command-line mode."""
        if len(args) >= 3:
            task_context = args[0]
            clinerule = args[1]
            component = args[2]
            entry = log_clinerule_execution(task_context, clinerule, component)
            print("Log entry created:")
            print(entry)
            return True
        return False


def main():
    """Main entry point with enhanced functionality."""
    if ENHANCED_MODE:
        # Use argparse to handle enhanced commands
        parser = argparse.ArgumentParser(description='Enhanced .clinerules Task Execution Logger')
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        # Command: log
        log_parser = subparsers.add_parser('log', help='Log a rule execution')
        log_parser.add_argument('--rule-name', '-r', required=True, help='Name of the .clinerule')
        log_parser.add_argument('--component-name', '-c', required=True, help='Name of the component')
        log_parser.add_argument('--task-document', '-t', default=None, help='Task context document')
        log_parser.add_argument('--environment', '-e', default=None, help='Environment details for context window')
        
        # Command: metrics
        metrics_parser = subparsers.add_parser('metrics', help='Export analytics metrics')
        metrics_parser.add_argument('--days', '-d', type=int, default=30, help='Number of days to include in metrics')
        metrics_parser.add_argument('--output', '-o', default=None, help='Output file path')
        
        # Command: patterns
        subparsers.add_parser('patterns', help='Detect and report patterns')
        
        # Parse arguments
        args = parser.parse_args()
        
        # Handle different commands
        if args.command == 'log':
            log_execution(args)
        elif args.command == 'metrics':
            export_metrics(args)
        elif args.command == 'patterns':
            detect_and_print_patterns(None)
        elif len(sys.argv) > 1:
            # Try legacy mode with command line args
            legacy_mode(sys.argv[1:])
        else:
            # Interactive mode
            interactive_log()
    else:
        # Fall back to legacy mode
        if not legacy_mode(sys.argv[1:]):
            create_log_entry()

if __name__ == "__main__":
    main()
