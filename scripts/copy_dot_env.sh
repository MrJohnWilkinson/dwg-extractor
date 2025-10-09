#!/bin/bash

#######################################################################
# Environment File Setup Script
#
# Copies .env.sample to .env for easy setup.
#
# Usage:
#   ./scripts/copy_dot_env.sh [target-directory]
#
# Examples:
#   ./scripts/copy_dot_env.sh                  # Copy root .env.sample to .env
#   ./scripts/copy_dot_env.sh app              # Copy app/.env.sample to app/.env
#   ./scripts/copy_dot_env.sh app/backend      # Copy app/backend/.env.sample to app/backend/.env
#
# This script helps quickly set up environment configuration by copying
# the .env.sample template to .env, which can then be edited with actual values.
#######################################################################

# Get the script's directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Determine target directory
if [ $# -eq 0 ]; then
    # No argument - use project root
    TARGET_DIR="$PROJECT_ROOT"
else
    # Argument provided - use as relative path from project root
    TARGET_DIR="$PROJECT_ROOT/$1"
fi

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist"
    exit 1
fi

# Check if .env.sample exists
if [ ! -f "$TARGET_DIR/.env.sample" ]; then
    echo "Error: $TARGET_DIR/.env.sample does not exist"
    echo "Available .env.sample files:"
    find "$PROJECT_ROOT" -name ".env.sample" -type f
    exit 1
fi

# Check if .env already exists
if [ -f "$TARGET_DIR/.env" ]; then
    echo "Warning: $TARGET_DIR/.env already exists"
    read -p "Overwrite existing .env file? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
fi

# Copy the file
cp "$TARGET_DIR/.env.sample" "$TARGET_DIR/.env"

# Verify copy succeeded
if [ -f "$TARGET_DIR/.env" ]; then
    echo "✅ Successfully copied .env.sample to .env in $TARGET_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Edit $TARGET_DIR/.env with your actual values"
    echo "  2. Never commit .env to version control (it's in .gitignore)"
    echo ""
    echo "Required variables (check .env.sample for details):"
    grep "^[A-Z_]*=" "$TARGET_DIR/.env.sample" | cut -d '=' -f1 | sed 's/^/  - /'
else
    echo "❌ Failed to copy .env file"
    exit 1
fi
