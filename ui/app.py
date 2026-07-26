"""
ui/app.py — Mirrors root app.py for compatibility when running from ui/ directory.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Run the main app
exec(open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.py")).read())
