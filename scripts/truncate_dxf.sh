#!/bin/bash

# DXF File Truncation Utility
# Generate truncated versions of large DXF files for diagnostic testing
# Execute from project root
# Follows working directory convention: uses root-relative paths, no cd commands

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration defaults
DEFAULT_LINE_COUNT=100000
VERBOSE=0

# Function to log verbose messages
log_verbose() {
    if [ $VERBOSE -eq 1 ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Function to display usage information
show_help() {
    echo "DXF File Truncation Utility"
    echo ""
    echo "Generate truncated versions of large DXF files for diagnostic testing."
    echo "Useful for isolating size-related performance issues."
    echo ""
    echo "Usage: $0 [OPTIONS] <input.dxf> <output.dxf> [line_count]"
    echo ""
    echo "Arguments:"
    echo "  input.dxf      Path to the input DXF file (required)"
    echo "  output.dxf     Path for the output truncated file (required)"
    echo "  line_count     Number of lines to keep (optional, default: $DEFAULT_LINE_COUNT)"
    echo ""
    echo "Options:"
    echo "  -v, --verbose  Show detailed output"
    echo "  -h, --help     Display this help message"
    echo ""
    echo "Examples:"
    echo "  # Truncate to default 100,000 lines"
    echo "  $0 app/tests/assets/samples/SP-GF-EX-4154.dxf /tmp/small.dxf"
    echo ""
    echo "  # Truncate to specific line count"
    echo "  $0 app/tests/assets/samples/SP-GF-EX-4154.dxf /tmp/small.dxf 50000"
    echo ""
    echo "  # Use with verbose output"
    echo "  $0 -v app/tests/assets/sample_drawing.dxf /tmp/test.dxf 1000"
    echo ""
    echo "Note: The truncated file may not be a valid DXF (could cut mid-entity),"
    echo "but this is acceptable for performance diagnostic testing."
    exit 0
}

# Function to validate line count is a positive integer
validate_line_count() {
    local count="$1"
    if ! [[ "$count" =~ ^[0-9]+$ ]] || [ "$count" -le 0 ]; then
        echo -e "${RED}Error: Line count must be a positive integer, got: $count${NC}"
        exit 1
    fi
}

# Function to validate DXF file extension (case-insensitive)
validate_dxf_extension() {
    local file="$1"
    local basename
    basename=$(basename "$file")
    local extension="${basename##*.}"
    local extension_lower
    extension_lower=$(echo "$extension" | tr '[:upper:]' '[:lower:]')

    if [ "$extension_lower" != "dxf" ]; then
        echo -e "${RED}Error: Input file must have .dxf extension, got: .$extension${NC}"
        exit 1
    fi
}

# Parse arguments
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            show_help
            ;;
        -*)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

# Restore positional arguments
set -- "${POSITIONAL_ARGS[@]}"

# Validate argument count
if [ $# -lt 2 ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS] <input.dxf> <output.dxf> [line_count]"
    echo ""
    echo "Use -h or --help for detailed usage information"
    exit 1
fi

# Extract arguments
INPUT_FILE="$1"
OUTPUT_FILE="$2"
LINE_COUNT="${3:-$DEFAULT_LINE_COUNT}"

log_verbose "Input file: $INPUT_FILE"
log_verbose "Output file: $OUTPUT_FILE"
log_verbose "Line count: $LINE_COUNT"

# Validate input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}Error: Input file not found: $INPUT_FILE${NC}"
    exit 1
fi

# Validate input file has .dxf extension
validate_dxf_extension "$INPUT_FILE"

# Validate line count
validate_line_count "$LINE_COUNT"

# Get input file info
INPUT_SIZE=$(du -h "$INPUT_FILE" | cut -f1)
INPUT_LINES=$(wc -l < "$INPUT_FILE")

log_verbose "Input file size: $INPUT_SIZE"
log_verbose "Input file lines: $INPUT_LINES"

# Check if requested lines exceed input file lines
if [ "$LINE_COUNT" -ge "$INPUT_LINES" ]; then
    echo -e "${YELLOW}Warning: Requested line count ($LINE_COUNT) >= input file lines ($INPUT_LINES)${NC}"
    echo -e "${YELLOW}Copying entire file instead of truncating${NC}"
fi

# Perform truncation
echo -e "${BLUE}Truncating DXF file...${NC}"
head -n "$LINE_COUNT" "$INPUT_FILE" > "$OUTPUT_FILE" || {
    echo -e "${RED}Error: Failed to truncate file${NC}"
    exit 1
}

# Get output file info
OUTPUT_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
OUTPUT_LINES=$(wc -l < "$OUTPUT_FILE")

# Display success message
echo -e "${GREEN}Truncation completed successfully${NC}"
echo ""
echo -e "${BLUE}=== Summary ===${NC}"
echo "Input file:    $INPUT_FILE"
echo "Input size:    $INPUT_SIZE ($INPUT_LINES lines)"
echo "Output file:   $OUTPUT_FILE"
echo "Output size:   $OUTPUT_SIZE ($OUTPUT_LINES lines)"
echo "Lines kept:    $OUTPUT_LINES of $INPUT_LINES ($(awk "BEGIN {printf \"%.1f\", ($OUTPUT_LINES/$INPUT_LINES)*100}")%)"
echo -e "${BLUE}===============${NC}"
