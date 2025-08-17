#!/usr/bin/env python3
import os
import subprocess
import sys

# Get PORT from environment with fallback
port = os.environ.get('PORT', '8000')
print(f"=== Railway Python Startup ===")
print(f"PORT from environment: {port}")
print(f"Starting uvicorn on port: {port}")

# Start uvicorn with the port
try:
    subprocess.run([
        sys.executable, '-m', 'uvicorn',
        'main:app',
        '--host', '0.0.0.0',
        '--port', str(port)
    ], check=True)
except Exception as e:
    print(f"Failed to start uvicorn: {e}")
    sys.exit(1)
