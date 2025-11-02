#!/bin/bash
set -e

echo "=========================================="
echo "Java to Node.js Conversion Agent"
echo "=========================================="
echo ""

# Create output directories if they don't exist
mkdir -p /app/outputs /app/tmp

# Check if config file exists, create example if not
if [ ! -f "/app/llm_config.json" ]; then
    echo "⚠️  llm_config.json not found. Creating example..."
    cp /app/llm_config.json.example /app/llm_config.json 2>/dev/null || true
    echo "Please configure llm_config.json or provide API tokens via environment variables"
    echo ""
fi

# Determine what to run
if [ "$1" = "api" ] || [ -z "$1" ]; then
    echo "Starting API server on port 8000..."
    echo "API docs available at: http://localhost:8000/docs"
    echo "Web UI available at: http://localhost:8000/"
    echo ""
    exec python -m src.api.server
elif [ "$1" = "convert" ]; then
    echo "Running conversion via CLI..."
    shift
    exec python run_conversion.py "$@"
else
    echo "Executing: $@"
    exec "$@"
fi

