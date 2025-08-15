#!/bin/bash

# OKR Pipeline Runner
# Simple wrapper script for the main orchestrator

set -e  # Exit on any error

echo "🚀 OKR Pipeline Runner"
echo "======================"

# Check if we're in the right directory
if [ ! -f "main_orchestrator.py" ]; then
    echo "❌ Error: main_orchestrator.py not found in current directory"
    echo "Please run this script from the OKR_reviewer directory"
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed or not in PATH"
    echo "Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check for access token
if [ -z "$FEISHU_ACCESS_TOKEN" ]; then
    echo "⚠️  Warning: FEISHU_ACCESS_TOKEN not set"
    echo "You may need to set it: export FEISHU_ACCESS_TOKEN='your_token'"
    echo ""
fi

# Parse arguments
OKR_LIMIT=${1:-2}
SKIP_DASHBOARD=${2:-false}
PORT=${3:-8000}

echo "Configuration:"
echo "  OKR Limit: $OKR_LIMIT"
echo "  Skip Dashboard: $SKIP_DASHBOARD"
echo "  Port: $PORT"
echo ""

# Build command
CMD="uv run python main_orchestrator.py --okr_limit $OKR_LIMIT --port $PORT"

if [ "$SKIP_DASHBOARD" = "true" ]; then
    CMD="$CMD --skip-dashboard"
fi

echo "Running: $CMD"
echo ""

# Run the orchestrator
eval $CMD

echo ""
echo "✅ Pipeline completed!"

