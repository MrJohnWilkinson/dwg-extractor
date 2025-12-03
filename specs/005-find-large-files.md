# Chore: Find All Files with 1000+ Lines of Code

## Chore Description
Search the project for all files containing 1000 or more lines of code and return a simple list with file paths and their line counts. The previous search method using `find` with `wc -l {} +` and `awk` filtering missed files because of how `wc` batches output when using `+` instead of `\;`.

## Relevant Files
Use these files to resolve the chore:

- `app/**/*.py` - All Python source files in the application directory need to be scanned for line counts.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Search All Python Files for Line Counts
- Use `find` with `-exec wc -l {} \;` (semicolon, not plus) to get individual line counts per file
- Filter results to show only files with 1000+ lines
- Sort results by line count in descending order
- Command: `find . -type f -name "*.py" ! -path "./.venv/*" ! -path "./.git/*" -exec wc -l {} \; | awk '$1 >= 1000' | sort -rn`

### 2. Display Results as Simple List
- Output format: `<line_count> <file_path>`
- Example output:
  ```
  2460 ./app/tests/core/test_extractor.py
  2435 ./app/tests/core/test_excel_writer.py
  1657 ./app/tests/core/test_excel_formatting.py
  ```

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `find . -type f -name "*.py" ! -path "./.venv/*" ! -path "./.git/*" -exec wc -l {} \; | awk '$1 >= 1000' | sort -rn` - Find and list all Python files with 1000+ lines
- `wc -l app/tests/core/test_excel_formatting.py` - Verify the previously missed file (1657 lines) is captured

## Notes
- The original command used `wc -l {} +` which batches multiple files per `wc` invocation, making `awk` filtering unreliable
- Using `wc -l {} \;` runs `wc` once per file, giving clean output for filtering
- Current files with 1000+ lines (as of this analysis):
  - `app/tests/core/test_extractor.py` - 2460 lines
  - `app/tests/core/test_excel_writer.py` - 2435 lines
  - `app/tests/core/test_excel_formatting.py` - 1657 lines
