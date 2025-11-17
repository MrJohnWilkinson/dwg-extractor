#!/bin/bash

# DWG Block Extractor Launcher
# Execute from project root
# Follows working directory convention: uses root-relative paths, no cd commands

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REQUIRED_PYTHON_VERSION="3.11"
VERBOSE=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            echo "DWG Block Extractor Launcher"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose    Show detailed startup diagnostics"
            echo "  -h, --help       Display this help message"
            echo ""
            echo "Requirements:"
            echo "  - Python $REQUIRED_PYTHON_VERSION or higher"
            echo "  - uv package manager installed"
            echo "  - Virtual environment configured (uv will handle this)"
            echo ""
            echo "Platform: $(uname -s)"
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Function to log verbose messages
log_verbose() {
    if [ $VERBOSE -eq 1 ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Function to check Python version
check_python_version() {
    log_verbose "Checking Python version compatibility..."

    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        echo -e "${RED}Error: Python not found${NC}"
        echo "Please install Python $REQUIRED_PYTHON_VERSION or higher"
        exit 1
    fi

    # Get Python version
    PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')

    log_verbose "Found Python version: $PYTHON_VERSION"

    # Extract major.minor version
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    REQUIRED_MAJOR=$(echo "$REQUIRED_PYTHON_VERSION" | cut -d. -f1)
    REQUIRED_MINOR=$(echo "$REQUIRED_PYTHON_VERSION" | cut -d. -f2)

    # Compare versions
    if [ "$PYTHON_MAJOR" -lt "$REQUIRED_MAJOR" ] || \
       ([ "$PYTHON_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$REQUIRED_MINOR" ]); then
        echo -e "${YELLOW}Warning: Python $PYTHON_VERSION found, but $REQUIRED_PYTHON_VERSION or higher is recommended${NC}"
    fi
}

# Function to check uv installation
check_uv() {
    log_verbose "Checking for uv package manager..."

    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: uv package manager not found${NC}"
        echo ""
        echo "Please install uv by running:"
        echo -e "${GREEN}curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        echo ""
        echo "Or visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi

    UV_VERSION=$(uv --version 2>&1 || echo "unknown")
    log_verbose "Found uv: $UV_VERSION"
}

# Function to check virtual environment
check_venv() {
    log_verbose "Checking virtual environment..."

    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Warning: Virtual environment not found at .venv${NC}"
        echo ""
        echo "Creating virtual environment and installing dependencies..."
        echo "This may take a few moments..."
        uv sync || {
            echo -e "${RED}Error: Failed to create virtual environment${NC}"
            echo "Please run: uv sync"
            exit 1
        }
        echo -e "${GREEN}Virtual environment created successfully${NC}"
    else
        log_verbose "Virtual environment found at .venv"
    fi
}

# Function to display platform information
show_platform_info() {
    if [ $VERBOSE -eq 1 ]; then
        echo -e "${BLUE}=== Platform Information ===${NC}"
        echo "Operating System: $(uname -s)"
        echo "Architecture: $(uname -m)"
        echo "Kernel: $(uname -r)"
        echo "Working Directory: $(pwd)"
        echo -e "${BLUE}===========================${NC}"
        echo ""
    fi
}

# Main execution
main() {
    # Display startup message
    if [ $VERBOSE -eq 1 ]; then
        echo -e "${BLUE}DWG Block Extractor - Starting...${NC}"
        echo ""
    fi

    # Show platform info
    show_platform_info

    # Run checks
    check_python_version
    check_uv
    check_venv

    # Launch application using root-relative path
    log_verbose "Launching application from app/main.py..."
    echo -e "${GREEN}Starting DWG Block Extractor...${NC}"

    # Run the application
    uv run python app/main.py || {
        echo -e "${RED}Error: Application failed to start${NC}"
        exit 1
    }
}

# Run main function
main
