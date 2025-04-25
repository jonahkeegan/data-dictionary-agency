#!/usr/bin/env python3
"""
Direct runner for the examples, avoiding module import issues.
"""

import os
import sys

# Get the current directory and add it to the path
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the examples.py directory to the path
sys.path.append(current_dir)

# Import and run the examples
import examples

# Run all examples
if __name__ == "__main__":
    print("Running .clinerules Logger Examples...")
    examples.run_all_examples()
