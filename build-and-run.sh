#!/bin/bash
# Simple script to build Docker image and run conversion

set -e

echo "=========================================="
echo "Building Docker Image"
echo "=========================================="
docker build -t java-to-nodejs-converter .

echo ""
echo "=========================================="
echo "Running Conversion"
echo "=========================================="
echo ""

# Ensure output directory exists
OUTPUT_DIR="/Users/anant/Documents/repos/Coding-Agent/my-output-glm"
mkdir -p "$OUTPUT_DIR"

# Run the conversion
docker run --rm \
    -v "$(pwd)/outputs:/app/outputs" \
    -v "$(pwd)/tmp:/app/tmp" \
    -v "$OUTPUT_DIR:/app/custom-output" \
    -v "$(pwd)/llm_config.json:/app/llm_config.json:ro" \
    -e GEMINI_API_KEY="${GEMINI_API_KEY:-}" \
    -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    -e GLM_API_KEY="${GLM_API_KEY:-}" \
    -e GLM_BASE_URL="${GLM_BASE_URL:-}" \
    java-to-nodejs-converter \
    python run_conversion.py \
    --github-url "https://github.com/janjakovacevic/SakilaProject" \
    --profile glm-4-6-zai \
    --output "/app/custom-output"

echo ""
echo "=========================================="
echo "Conversion Complete!"
echo "=========================================="
echo "Output saved to: $OUTPUT_DIR"

