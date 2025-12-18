# Chore: Create DXF Truncation Utility Script

## Chore Description

Create a utility shell script `scripts/truncate_dxf.sh` that generates truncated versions of large DXF files for diagnostic testing purposes. This script supports the extractor lockup diagnostic investigation plan (Step 4: Test with Reduced Data) by providing a repeatable, configurable way to create smaller test files from large DXF files like `SP-GF-EX-4154.dxf` (7M lines).

The script should:
- Accept input DXF file path and output path as arguments
- Default to truncating to first 100,000 lines
- Allow optional line count parameter
- Validate that input file exists
- Provide helpful usage message with examples

This enables developers to quickly create reduced test files to isolate size-related performance issues without manually running `head` commands.

## Relevant Files

Use these files to resolve the chore:

- **`scripts/start.sh`** - Reference for script conventions: color codes, argument parsing, help messages, error handling, and verbose logging patterns used in this project
- **`scripts/build.sh`** - Additional reference for script structure: function organization, platform detection, and cleanup patterns
- **`README.md`** - Documents the scripts directory and working directory conventions (execute from project root, use root-relative paths)
- **`ai_output/089-extractor-lockup-diagnostic-plan.md`** - Contains the diagnostic plan that motivates this utility (Step 4: Test with Reduced Data shows the example usage)

### New Files

- **`scripts/truncate_dxf.sh`** - New utility script to create truncated DXF files for testing

## Step by Step Tasks

### Step 1: Create the truncate_dxf.sh Script

Create `scripts/truncate_dxf.sh` with the following structure:

- Add shebang and header comment explaining purpose
- Follow project conventions from `start.sh`:
  - Use `set -e` for exit on error
  - Define color codes (RED, GREEN, YELLOW, BLUE, NC)
  - Default configuration variables
- Define arguments:
  - `$1` - Input DXF file path (required)
  - `$2` - Output DXF file path (required)
  - `$3` - Line count (optional, default 100000)
- Support `-h|--help` flag for usage information

### Step 2: Implement Argument Parsing

- Parse command line arguments
- Handle `-h|--help` to show usage message with examples
- Validate that at least 2 arguments are provided (input and output paths)
- Set default line count to 100000 if not specified
- Handle `-v|--verbose` flag for detailed output (optional, following project convention)

### Step 3: Implement Input Validation

- Check that input file exists using `[ -f "$INPUT_FILE" ]`
- Validate input file has `.dxf` extension (case-insensitive)
- Check that line count is a positive integer
- Provide clear error messages with color coding

### Step 4: Implement Truncation Logic

- Use `head -n $LINE_COUNT "$INPUT_FILE" > "$OUTPUT_FILE"` to truncate
- Show progress/success message with:
  - Input file path
  - Output file path
  - Number of lines truncated
  - Output file size (using `du -h`)
- Handle errors gracefully

### Step 5: Add Usage Help Message

Create comprehensive help message showing:
- Script purpose
- Usage syntax
- Arguments description
- Default values
- Example commands (including the example from diagnostic plan)

### Step 6: Make Script Executable and Test

- Verify script has proper structure
- Test help message: `bash scripts/truncate_dxf.sh --help`
- Test error handling: invalid arguments, missing file, etc.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

```bash
# 1. Verify script exists and is properly formatted
test -f scripts/truncate_dxf.sh && echo "Script exists"

# 2. Verify script has shebang
head -1 scripts/truncate_dxf.sh | grep -q "#!/bin/bash" && echo "Shebang present"

# 3. Test help message displays correctly
bash scripts/truncate_dxf.sh --help

# 4. Test error handling - no arguments
bash scripts/truncate_dxf.sh 2>&1 | grep -q "Error\|Usage" && echo "No-args error handled"

# 5. Test error handling - missing input file
bash scripts/truncate_dxf.sh /nonexistent/file.dxf /tmp/out.dxf 2>&1 | grep -q "Error" && echo "Missing file error handled"

# 6. Test actual truncation with a small test file
bash scripts/truncate_dxf.sh app/tests/assets/sample_drawing.dxf /tmp/truncated_test.dxf 50

# 7. Verify output file was created
test -f /tmp/truncated_test.dxf && echo "Output file created"

# 8. Verify line count of output
wc -l < /tmp/truncated_test.dxf

# 9. Cleanup test file
rm -f /tmp/truncated_test.dxf

# 10. Run shellcheck if available (optional lint check)
command -v shellcheck && shellcheck scripts/truncate_dxf.sh || echo "shellcheck not installed, skipping"
```

## Notes

- The script follows the same conventions as `scripts/start.sh` and `scripts/build.sh` for consistency
- Default of 100,000 lines comes from the diagnostic plan's recommended test size
- DXF files are text-based, so `head` works correctly for truncation
- The truncated file may not be a valid DXF (could cut mid-entity), but this is acceptable for diagnostic testing where we're measuring performance, not correctness
- Consider adding a `-v|--verbose` flag for consistency with other scripts, but it's optional for this simple utility
