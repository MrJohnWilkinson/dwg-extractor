# Working Directory Convention

## Overview

This project follows a strict working directory convention where **all commands are executed from the project root** (`/home/john/github-projects-linux/dwg-extractor`). This convention is enforced by the Claude Code settings in `.claude/settings.json` where `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` is set to `1`.

## Why This Matters

The working directory convention helps:
- **Maintain context**: Claude Code can track the current directory across tool invocations
- **Avoid confusion**: No need to track which directory commands are running in
- **Simplify scripts**: Scripts don't need to change directories or make assumptions about where they're called from
- **Consistency**: All documentation and commands work the same way

## Command Patterns

### ✅ Correct Patterns

All commands should be executed from the project root and use the `--directory` flag or relative paths when needed:

```bash
# Running Python commands in the app directory
uv run --directory app python main.py
uv run --directory app python -c "from core.extractor import extract_blocks"

# Running pytest in the app directory
uv run --directory app pytest tests/core/ -v
uv run --directory app pytest --cov=core --cov-report=term-missing

# Syncing dependencies
uv sync --directory app

# File operations from project root
test -f app/tests/assets/sample_drawing.dxf && echo 'File exists'
ls -la app/
cat app/pyproject.toml
```

### ❌ Incorrect Patterns (Do Not Use)

These patterns violate the working directory convention:

```bash
# Don't use cd commands
cd app && uv run python main.py
cd app && uv run pytest
cd "$(dirname "$0")/../app" || exit 1

# Don't assume you're in the app directory
uv run python main.py  # Wrong if not in app/
pytest tests/core/     # Wrong if not in app/
```

## Project Structure

```
/home/john/github-projects-linux/dwg-extractor/  # <-- Always execute commands from here
├── app/                                          # Application code directory
│   ├── core/                                     # Core modules
│   ├── tests/                                    # Test files
│   ├── main.py                                   # Main entry point
│   └── pyproject.toml                            # Python dependencies
├── scripts/                                      # Utility scripts
│   └── start.sh                                  # Launch script
├── specs/                                        # Specification documents
├── ai_docs/                                      # AI/LLM documentation
├── ai_output/                                    # AI-generated output
└── README.md                                     # Main documentation
```

## uv --directory Flag

The `uv` package manager supports a `--directory` (or `-d`) flag that allows running commands in a specific directory without using `cd`. This is the preferred approach for all uv commands:

```bash
# Sync dependencies in app/
uv sync --directory app

# Run Python script in app/
uv run --directory app python main.py

# Run pytest in app/
uv run --directory app pytest tests/core/ -v

# Run Python one-liner in app/
uv run --directory app python -c "import core.constants; print('OK')"
```

## Shell Scripts

Shell scripts in the `scripts/` directory should also follow this convention. They should not use `cd` commands and should instead use the `--directory` flag or relative paths from the project root.

Example from `scripts/start.sh`:

```bash
#!/bin/bash

# DWG Block Extractor Launcher
# Execute from project root

# Check if python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi

# Launch application from project root
uv run --directory app python main.py
```

## Spec Files and Documentation

All validation commands and code examples in spec files should use the working directory convention:

```markdown
### Validation Commands

- `uv run --directory app pytest tests/core/ -v` - Run tests
- `test -f app/tests/assets/sample_drawing.dxf && echo 'File exists'` - Check file
- `uv run --directory app python -c "from core.extractor import extract_blocks"` - Test import
```

## Alternative Approaches

If the `--directory` flag is not available for a specific command, use relative paths from the project root:

```bash
# Using relative paths
python app/main.py
pytest app/tests/core/
cat app/pyproject.toml
```

## Claude Code Settings

The `.claude/settings.json` file contains:

```json
{
  "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": "1"
}
```

This setting instructs Claude Code to maintain the project working directory throughout the session and avoid using `cd` commands.

## Benefits

1. **Clarity**: Always clear which directory commands are running in
2. **Reproducibility**: Commands work the same way every time
3. **Tool Support**: Works well with Claude Code's session management
4. **Simplicity**: No need to track or change working directories
5. **Consistency**: All documentation follows the same pattern

## Migration Notes

If you encounter old documentation or scripts using `cd app &&` patterns, they should be updated to use the `--directory` flag:

```bash
# Old pattern (deprecated)
cd app && uv run pytest tests/core/ -v

# New pattern (correct)
uv run --directory app pytest tests/core/ -v
```

This migration ensures consistency with the project's working directory convention and improves compatibility with Claude Code's session management.
