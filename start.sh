#!/bin/bash
# Start script for Railway deployment with debugging
echo "=== Railway Deployment Debug ==="
echo "PORT environment variable: ${PORT}"
echo "PATH: ${PATH}"
echo "Current directory: $(pwd)"
echo "Files in directory: $(ls -la)"

# Set PORT with fallback
if [ -z "$PORT" ]; then
    echo "PORT not set, using default 8000"
    export PORT=8000
else
    echo "PORT is set to: $PORT"
fi

echo "Starting uvicorn with port: $PORT"
exec python -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
