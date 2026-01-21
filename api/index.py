"""
Vercel Serverless Function Entry Point
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects the Flask app to be available as 'app'
# This is the handler for all requests

# For Vercel debugging
print(f"Vercel handler loaded - Environment: {os.getenv('FLASK_ENV', 'production')}")
