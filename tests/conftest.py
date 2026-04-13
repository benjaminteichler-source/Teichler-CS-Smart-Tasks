"""
tests/conftest.py - pytest configuration.

Ensures the project root is on sys.path and sets FLASK_ENV=testing
so the app uses an in-memory SQLite database for all tests.
"""

import os
import sys

# Put the project root on the path so imports like `from models.task import ...` work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use the testing config (in-memory SQLite, TESTING=True)
os.environ["FLASK_ENV"] = "testing"
