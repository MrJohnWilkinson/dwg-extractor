#!/bin/bash

# DWG Block Extractor Launcher
# Execute from project root

# Check if python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi

# Launch application using root-relative path
uv run python app/main.py
