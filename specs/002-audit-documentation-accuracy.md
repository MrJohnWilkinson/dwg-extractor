# Chore: Audit Documentation Accuracy Against Actual Codebase

## Chore Description
Audit all documentation files in the codebase to verify they accurately reflect the actual implementation. Create a two-column comparison table showing discrepancies between documentation and actual code. This audit focuses on ensuring that reference documentation files accurately describe the current state of the application structure, naming conventions, technology stack, and field naming patterns.

## Discrepancy Analysis Table

| Documentation Claim | Actual Codebase Reality | Status |
|---------------------|------------------------|--------|
| **README.md** |
| Project structure shows `app/client/` and `app/server/` | Only `app/core/`, `app/tests/`, and `app/main.py` exist | ❌ MISMATCH |
| Usage: `bash scripts/start.sh` | ✓ `scripts/start.sh` exists and is executable | ✅ MATCH |
| Usage: `uv run pytest app/tests/` | ✓ Correct path, pytest configured in `pyproject.toml` | ✅ MATCH |
| Usage: `uv run mypy app/` | ✓ mypy configured in `pyproject.toml` | ✅ MATCH |
| Tech Stack: Python 3.11+ | ✓ `pyproject.toml` requires Python 3.8+, `.python-version` has 3.11 | ✅ MATCH |
| Tech Stack: uv package manager | ✓ `uv.lock` exists, scripts use `uv run` | ✅ MATCH |
| Reference: `ai_docs/001-naming-convention-guide.md` | ✓ File exists | ✅ MATCH |
| Reference: `ai_docs/002-standardized-app-structure.md` | ✓ File exists | ✅ MATCH |
| Reference: `app_docs/005-field-naming-convention.md` | ✓ File exists | ✅ MATCH |
| **ai_docs/001-naming-convention-guide.md** |
| Guide covers Python Backend, PostgreSQL, JavaScript/React, CSS | This is a single-file desktop app with no database, no frontend framework, no CSS classes | ⚠️ OVER-GENERALIZED |
| Python naming conventions (snake_case, UPPER_SNAKE_CASE) | ✓ Codebase follows these conventions correctly | ✅ MATCH |
| PostgreSQL table/column naming | Project uses no database | ❌ NOT APPLICABLE |
| JavaScript/React conventions (camelCase, PascalCase) | Project uses vanilla customtkinter (Python), no JavaScript | ❌ NOT APPLICABLE |
| CSS class naming conventions | Project uses customtkinter, no CSS files | ❌ NOT APPLICABLE |
| **ai_docs/002-standardized-app-structure.md** |
| Describes TAC course application structure | This is not a TAC course project | ⚠️ WRONG CONTEXT |
| Shows `app/client/` and `app/server/` structure | Actual structure: `app/core/`, `app/tests/`, `app/main.py` | ❌ MISMATCH |
| Mentions FastAPI, Vite, TypeScript, Vue 3, Tailwind | This project uses none of these technologies | ❌ NOT APPLICABLE |
| Mentions `adws/` directory for AI workflows | Project has `.claude/` but no `adws/` directory | ❌ MISMATCH |
| Mentions `specs/` directory | ✓ `specs/` directory exists | ✅ MATCH |
| Mentions `scripts/` directory with `start.sh` and `stop_apps.sh` | ✓ `scripts/` exists with `start.sh` and `build.sh` (no `stop_apps.sh`) | ⚠️ PARTIAL MATCH |
| **app_docs/005-field-naming-convention.md** |
| Field pattern: `{domain}_{attribute}[_{qualifier}]` | ✓ Code follows this pattern in `constants.py` | ✅ MATCH |
| Examples: `block_name`, `block_insertion_count`, `block_entity_count` | ✓ All exist in `constants.py` | ✅ MATCH |
| Examples: `layer_name`, `layer_insertion_count`, `layer_entity_count` | ✓ All exist in `constants.py` | ✅ MATCH |
| Examples: `entity_type_name`, `entity_type_count` | ✓ Both exist in `constants.py` | ✅ MATCH |
| Constants pattern: `EXCEL_COLUMN_*` | ✓ All column constants follow this pattern | ✅ MATCH |
| Adding New Fields Checklist mentions `ExtractionResult TypedDict` | ✓ `ExtractionResult` exists in `app/core/extractor.py` | ✅ MATCH |
| **pyproject.toml** |
| Project name: `dwg-block-extractor` | ✓ Matches | ✅ MATCH |
| Python version: `>=3.8` | README claims 3.11+, but pyproject.toml allows 3.8+ | ⚠️ INCONSISTENT |
| Dependencies: ezdxf, pandas, openpyxl, customtkinter | ✓ All present | ✅ MATCH |
| Dev dependencies: pytest, mypy | ✓ All present | ✅ MATCH |
| Build group: pyinstaller | ✓ Present in `dependency-groups` | ✅ MATCH |
| **scripts/start.sh** |
| Follows working directory convention (no cd commands) | ✓ Uses `uv run python app/main.py` from root | ✅ MATCH |
| Checks Python version, uv, and venv | ✓ All checks present | ✅ MATCH |
| **scripts/build.sh** |
| Creates standalone executables using PyInstaller | ✓ Script exists and uses PyInstaller | ✅ MATCH |
| Follows working directory convention | ✓ Uses root-relative paths | ✅ MATCH |

## Key Findings Summary

### Critical Issues (Must Fix)
1. **ai_docs/002-standardized-app-structure.md** is entirely wrong for this project - describes TAC course full-stack applications, not a single-file Python desktop app
2. **ai_docs/001-naming-convention-guide.md** is over-generalized - includes PostgreSQL, JavaScript/React, CSS conventions that don't apply to this project
3. **README.md** has incorrect project structure diagram showing `app/client/` and `app/server/` when actual structure is `app/core/`, `app/tests/`, `app/main.py`

### Minor Issues (Should Fix)
4. **Python version inconsistency**: README claims "3.11+" but `pyproject.toml` allows ">=3.8"
5. **Missing script**: `ai_docs/002-standardized-app-structure.md` mentions `stop_apps.sh` but project has `build.sh` instead

### What's Working Well
- `app_docs/005-field-naming-convention.md` is perfectly accurate
- README's usage instructions, tech stack (except structure), and reference files sections are accurate
- All actual code follows documented conventions correctly
- `pyproject.toml`, `scripts/start.sh`, and `scripts/build.sh` match their descriptions

## Relevant Files
Use these files to resolve the chore:

- **README.md** - Contains incorrect project structure diagram; needs correction to match actual `app/` layout
- **ai_docs/001-naming-convention-guide.md** - Will be trimmed to Python-only sections (remove PostgreSQL, JavaScript/React, CSS)
- **ai_docs/002-standardized-app-structure.md** - Will be DELETED (TAC course material, not applicable)
- **pyproject.toml** - Python version requirement will be updated to ">=3.11" to match README
- **app_docs/005-field-naming-convention.md** - ACCURATE, keep as-is (reference only, no changes needed)

### New Files
No new files are needed. This chore involves correcting or removing existing documentation.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix Critical Documentation Mismatches

#### 1.1 Delete ai_docs/002-standardized-app-structure.md
- **Action**: DELETE this file - it's TAC course material that describes FastAPI/Vite/TypeScript applications, completely irrelevant to dwg-extractor
- This file provides zero value to this single-file Python desktop application
- Remove the file: `rm ai_docs/002-standardized-app-structure.md`

#### 1.2 Trim ai_docs/001-naming-convention-guide.md to Python-Only
- **Action**: TRIM to only Python-relevant sections
- Remove these sections (they don't apply to this Python-only desktop app):
  - PostgreSQL Database (lines 101-191)
  - JavaScript/React Frontend (lines 193-281)
  - CSS (lines 283-331)
- Keep these sections (relevant to Python code):
  - Python Backend (lines 6-98)
  - Key Principles (lines 333-452)
- Update the header to clarify this is Python-specific naming conventions

#### 1.3 Fix README.md Project Structure Diagram
- Update the project structure in README.md (lines 27-47) to accurately reflect actual structure:
  ```
  dwg-extractor/
  ├── app/                          # Application code
  │   ├── core/                     # Business logic
  │   │   ├── extractor.py          # DWG/DXF extraction
  │   │   ├── excel_writer.py       # Excel generation
  │   │   ├── constants.py          # App constants
  │   │   └── logger.py             # Stdout logging
  │   ├── tests/                    # Test suite
  │   │   ├── core/                 # Unit tests
  │   │   └── assets/               # Test fixtures
  │   └── main.py                   # GUI entry point
  │
  ├── scripts/                      # Utility scripts
  │   ├── start.sh                  # Launch application
  │   └── build.sh                  # Build executable
  │
  ├── .venv/                        # Virtual environment (managed by uv)
  └── pyproject.toml                # Dependencies and project config (uv)
  ```
- Remove references to non-existent `client/` and `server/` directories

### Step 2: Resolve Minor Inconsistencies

#### 2.1 Align Python Version Requirements
- **Action**: Update `pyproject.toml` line 5 to require ">=3.11" to match README and `.python-version`
- Change: `requires-python = ">=3.8"` → `requires-python = ">=3.11"`
- Rationale: 3.11+ is what's actually tested and documented in README; keep consistency

#### 2.2 Verify No Orphaned References Remain
- **Action**: After deleting `ai_docs/002-standardized-app-structure.md`, verify no documentation references it
- Check README.md line 56-58 to ensure reference to deleted file is removed
- No need to create `scripts/stop_apps.sh` - not needed for single desktop app

### Step 3: Create Documentation Audit Report

#### 3.1 Create Comparison Table Document
- Create a markdown file documenting the discrepancies found (use the table from this spec as starting point)
- Save as `ai_output/documentation-audit-{timestamp}.md`
- Include recommendations for ongoing documentation maintenance

#### 3.2 Add Documentation Maintenance Guidelines
- Add a section to README.md or create `CONTRIBUTING.md` with guidelines:
  - When adding new fields, update `app_docs/005-field-naming-convention.md` examples
  - When changing project structure, update README.md structure diagram
  - When adding new Excel columns, update both code constants AND documentation

### Step 4: Validate All Changes

#### 4.1 Verify Documentation Consistency
- Read through README.md to ensure all sections are internally consistent
- Check that no references to deleted files remain
- Ensure all file paths mentioned in documentation actually exist

#### 4.2 Verify Code Still Matches Documentation
- Compare `app/core/constants.py` with `app_docs/005-field-naming-convention.md`
- Compare README tech stack with actual `pyproject.toml` dependencies
- Compare README usage instructions with actual script behavior

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/` - Run all tests to ensure no code was accidentally modified
- `uv run mypy app/` - Run type checking to ensure no imports or structure was broken
- `bash scripts/start.sh --help` - Verify start script still works correctly
- `grep -r "app/client" README.md ai_docs/ app_docs/ || echo "No references to app/client found (good)"` - Ensure old structure references removed
- `grep -r "app/server" README.md ai_docs/ app_docs/ || echo "No references to app/server found (good)"` - Ensure old structure references removed
- `test -f ai_docs/002-standardized-app-structure.md && echo "ERROR: File should be deleted" || echo "File correctly removed"` - Verify TAC course doc was removed
- `ls app/core/constants.py && echo "Constants file exists"` - Verify core structure intact
- `cat README.md | grep -A 20 "## Project Structure" | grep "app/core/" || echo "ERROR: README structure not updated"` - Verify README updated

## Notes
- **app_docs/005-field-naming-convention.md is the gold standard** - it's 100% accurate and should be used as the reference for all field naming decisions
- **ai_docs/ contains general reference material** that was likely copied from other projects and doesn't specifically apply to dwg-extractor
- **The actual code is correctly implemented** - the issue is purely documentation accuracy
- **No code changes are required** - this is purely a documentation cleanup chore
- When in doubt about what's correct, **trust the actual code over the documentation**
- Consider this a lesson in documentation drift: as projects evolve, documentation can become outdated if not actively maintained
