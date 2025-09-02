#!/usr/bin/env python3
"""
Main entry point for Lightera UNDOKAI application
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Import app after path setup
    from app import app

    app.run(debug=True, host="0.0.0.0", port=5000)
