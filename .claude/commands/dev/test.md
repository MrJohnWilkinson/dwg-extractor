---
description: Execute comprehensive validation tests for frontend and backend
model: opus
---

# Application Validation Test Suite

Execute comprehensive validation tests for both frontend and backend components, returning results in a standardized JSON format for automated processing.

## Purpose

Proactively identify and fix issues in the application before they impact users or developers. By running this comprehensive test suite, you can:
- Detect syntax errors, type mismatches, and import failures
- Identify broken tests or security vulnerabilities
- Verify build processes and dependencies
- Ensure the application is in a healthy state

## Variables

TEST_COMMAND_TIMEOUT: 5 minutes

## Instructions

- Execute each test in the sequence provided below
- Capture the result (passed/failed) and any error messages
- IMPORTANT: Return ONLY the JSON array with test results
  - IMPORTANT: Do not include any additional text, explanations, or markdown formatting
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON
- If a test passes, omit the error field
- If a test fails, include the error message in the error field
- Execute all tests even if some fail
- Error Handling:
  - If a command returns non-zero exit code, mark as failed and immediately stop processing tests
  - Capture stderr output for error field
  - Timeout commands after `TEST_COMMAND_TIMEOUT`
  - IMPORTANT: If a test fails, stop processing tests and return the results thus far
- Some tests may have dependencies (e.g., server must be stopped for port availability)
- API health check is required
- Test execution order is important - dependencies should be validated first
- All file paths are relative to the project root
- Always run `pwd` and `cd` before each test to ensure you're operating in the correct directory for the given test

## Test Execution Sequence

### Backend Tests

1. **Python Syntax Check**
   - Preparation Command: None
   - Command: `cd /home/john/github-projects-linux/ac-log && uv run python -m py_compile app/server/main.py app/server/models.py app/server/database.py app/server/config.py app/server/errors.py app/server/routes/activities.py app/server/routes/health.py app/server/routes/logs.py`
   - test_name: "python_syntax_check"
   - test_purpose: "Validates Python syntax by compiling source files to bytecode, catching syntax errors like missing colons, invalid indentation, or malformed statements"

2. **Backend Code Quality Check**
   - Preparation Command: None
   - Command: `cd /home/john/github-projects-linux/ac-log && uv run ruff check app/server`
   - test_name: "backend_linting"
   - test_purpose: "Validates Python code quality, identifies unused imports, style violations, and potential bugs"

3. **All Backend Tests**
   - Preparation Command: None
   - Command: `cd /home/john/github-projects-linux/ac-log && uv run pytest app/server/tests/ -v --tb=short`
   - test_name: "all_backend_tests"
   - test_purpose: "Validates all backend functionality including activity management, log CRUD operations, database integration, and API endpoints"

### Frontend Tests

4. **TypeScript Type Check**
   - Preparation Command: None
   - Command: `cd /home/john/github-projects-linux/ac-log/app/client && npm run type-check`
   - test_name: "typescript_check"
   - test_purpose: "Validates TypeScript type correctness without generating output files, catching type errors, missing imports, and incorrect function signatures"

5. **Frontend Build**
   - Preparation Command: None
   - Command: `cd /home/john/github-projects-linux/ac-log/app/client && npm run build`
   - test_name: "frontend_build"
   - test_purpose: "Validates the complete frontend build process including TypeScript compilation, Vite bundling, and production optimization"

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- Sort the JSON array with failed tests (passed: false) at the top
- Include all tests in the output, both passed and failed
- The execution_command field should contain the exact command that can be run to reproduce the test
- This allows subsequent agents to quickly identify and resolve errors

### Output Structure

```json
[
  {
    "test_name": "string",
    "passed": boolean,
    "execution_command": "string",
    "test_purpose": "string",
    "error": "optional string"
  },
  ...
]
```

### Example Output

```json
[
  {
    "test_name": "frontend_build",
    "passed": false,
    "execution_command": "cd /home/john/github-projects-linux/ac-log/app/client && npm run build",
    "test_purpose": "Validates the complete frontend build process including TypeScript compilation, Vite bundling, and production optimization",
    "error": "TS2345: Argument of type 'string' is not assignable to parameter of type 'number'"
  },
  {
    "test_name": "all_backend_tests",
    "passed": true,
    "execution_command": "cd /home/john/github-projects-linux/ac-log && uv run pytest app/server/tests/ -v --tb=short",
    "test_purpose": "Validates all backend functionality including activity management, log CRUD operations, database integration, and API endpoints"
  }
]
```
