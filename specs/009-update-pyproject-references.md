# Chore: Update pyproject.toml and UV References in Documentation

## Chore Description
Update outdated references to `pyproject.toml` location and UV usage patterns throughout the codebase documentation. After moving `pyproject.toml` from `app/` to project root in spec 008, the project structure diagram in README.md still shows it in the old location (line 39). Additionally, the usage comment in `app/main.py` needs to reflect the new root-relative path convention.

**Issue Examples:**
- README.md line 39 shows: `│   └── pyproject.toml            # Dependencies (uv)` but pyproject.toml is now at root
- app/main.py line 10 shows: `uv run python main.py` but should be `uv run python app/main.py` from root

This chore ensures all documentation accurately reflects the current project structure established in spec 008.

## Relevant Files
Use these files to resolve the chore:

- **README.md:25-54** - Project structure ASCII diagram that incorrectly shows `pyproject.toml` under `app/` directory (line 39). Needs to be moved to root level in the diagram to match actual file location.

- **README.md:68** - Working directory convention section correctly documents that `pyproject.toml` and `.venv` are at root. This is correct and should remain unchanged. Serves as reference for correct structure.

- **app/main.py:7-10** - Module docstring with usage instructions. Line 10 shows `uv run python main.py` which doesn't follow the root-relative path convention. Should be updated to `uv run python app/main.py` to match the working directory convention.

### New Files
No new files need to be created. This is purely a documentation update chore.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update README.md Project Structure Diagram
- Read the current project structure diagram in README.md (lines 25-54)
- Move the `pyproject.toml` entry from under `app/` to the root level
- Update the comment to reflect it's at root: `├── pyproject.toml              # Dependencies and project config (uv)`
- Add `.venv/` directory at root level: `├── .venv/                     # Virtual environment (managed by uv)`
- Ensure the `app/` section no longer shows pyproject.toml
- Verify the diagram accurately represents the current structure from spec 008

### Step 2: Update app/main.py Usage Documentation
- Read app/main.py docstring (lines 1-11)
- Update line 10 from `uv run python main.py` to `uv run python app/main.py`
- Ensure the usage example follows the root-relative path convention
- Keep line 8 as-is since it documents running from within app/ directory

### Step 3: Verify All Changes Are Complete
- Re-read both modified files to confirm changes are accurate
- Ensure no other UV or pyproject.toml references need updating in README.md or app/
- Double-check that the structure diagram matches the actual filesystem

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `test -f pyproject.toml && echo "PASS: pyproject.toml at root" || echo "FAIL: pyproject.toml missing"` - Verify pyproject.toml exists at root
- `test ! -f app/pyproject.toml && echo "PASS: No pyproject.toml in app/" || echo "FAIL: Old pyproject.toml still exists"` - Verify old location is empty
- `test -d .venv && echo "PASS: .venv at root" || echo "FAIL: .venv missing"` - Verify venv at root
- `grep -q "├── pyproject.toml" README.md && echo "PASS: README shows pyproject.toml at root" || echo "FAIL: README structure incorrect"` - Verify README structure updated
- `grep -q "uv run python app/main.py" app/main.py && echo "PASS: main.py usage updated" || echo "FAIL: main.py usage incorrect"` - Verify main.py usage updated
- `grep -q "│   └── pyproject.toml" README.md && echo "FAIL: README still shows pyproject.toml in app/" || echo "PASS: README cleaned up"` - Verify old reference removed
- `uv run pytest app/tests/ -q` - Run all tests to ensure no regressions (16 tests should pass, 1 skipped)

## Notes

- **Context**: This chore is a follow-up to spec 008 which moved pyproject.toml to root. The code changes were completed but documentation wasn't fully updated to reflect the new structure.

- **Scope**: Only updating README.md and app/main.py. Intentionally ignoring files in `ai_docs/`, `ai_output/`, and `specs/` as requested.

- **ASCII Diagram Guidelines**: When updating the project structure diagram, maintain consistent indentation and alignment with the existing style. Use `├──` for items at the same level and `│` for vertical lines.

- **No Code Changes**: This chore only updates documentation and comments. No functional code changes are required.

- **Validation**: The grep commands verify both that new references are added AND old references are removed to prevent confusion.
