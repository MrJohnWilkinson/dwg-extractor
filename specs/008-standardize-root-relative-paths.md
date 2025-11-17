# Chore: Standardize to Root-Relative Paths

## Chore Description
Eliminate confusion from mixed path conventions by standardizing all commands to use root-relative paths. Currently, the project uses `uv run --directory app` which changes the working directory before executing commands, causing mental overhead when switching between paths relative to `app/` vs paths relative to project root. This chore moves the virtual environment to project root and updates all documentation, scripts, and spec files to use consistent root-relative paths (always prefixed with `app/`).

**Current Problem:**
- `uv run --directory app pytest tests/...` (paths relative to `app/`)
- `test -f app/tests/...` (paths relative to root)
- Two mental models causing confusion

**Solution:**
- Move `.venv/` from `app/.venv/` to root `.venv/`
- Use `uv run <command> app/...` everywhere
- All paths always include `app/` prefix
- One consistent mental model

**Benefits:**
- Zero cognitive overhead - all paths look the same
- Easier to understand and maintain
- Simpler for new developers
- No impact on PyInstaller EXE building (`.venv` location doesn't matter)

## Relevant Files
Use these files to resolve the chore:

- **app/.venv/** - Current virtual environment location. Will be deleted and recreated at root level.

- **README.md:60-65** - Documents the current working directory convention using `uv run --directory app`. Needs complete rewrite to document new `uv run` pattern with root-relative paths.

- **scripts/start.sh:13** - Launch script using `uv run --directory app python main.py`. Needs update to `uv run python app/main.py`.

- **specs/001-phase1-project-setup.md** - Contains validation commands using `uv run --directory app`. Need to update all command examples to use root-relative paths.

- **specs/002-phase2-core-logic-implementation.md** - Contains validation commands and step-by-step tasks using `uv run --directory app`. Need to update all command examples.

- **specs/004-phase3-gui-implementation.md** - Contains validation commands using `uv run --directory app`. Need to update all command examples.

- **specs/006-fix-implementation-plan-cd-commands.md** - Ironically, this spec about fixing `cd` commands uses `uv run --directory app`. Needs update for consistency.

- **specs/007-phase4-comprehensive-testing.md** - Most recent spec, heavily uses `uv run --directory app pytest`. Need to update all validation commands and task descriptions.

- **specs/README.md** - Spec writing guide that may reference the working directory convention. Needs review and potential update.

- **.gitignore:20** - Currently has `.venv` pattern which catches both `app/.venv/` and `.venv/`. Already correct, no changes needed (good design!).

### New Files
No new files need to be created. This is purely a refactoring/standardization chore.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Backup Current State
- Verify current virtual environment exists at `app/.venv/`
- Verify current tests pass with existing setup: `uv run --directory app pytest`
- Document current Python version and uv version for reference
- This ensures we can rollback if needed

### Step 2: Move Virtual Environment to Root
- Delete the existing virtual environment: `rm -rf app/.venv/`
- Create new virtual environment at root: `cd` to project root, then run `uv sync --project app`
- Verify new `.venv/` exists at project root
- Verify `uv` can find the virtual environment automatically

### Step 3: Update README.md Working Directory Convention
- Replace the entire "Working Directory Convention" section (lines 60-65)
- Remove all references to `--directory app`
- Document new pattern: `uv run <command> app/...`
- Add examples showing consistent root-relative paths:
  - `uv run pytest app/tests/` - run tests
  - `uv run python app/main.py` - run application
  - `test -f app/tests/assets/sample.dxf` - file operations
- Emphasize that ALL paths always include `app/` prefix for consistency
- Keep the "never use `cd` commands" directive
- Keep reference to `.claude/settings.json` CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR setting

### Step 4: Update scripts/start.sh
- Replace line 13: `uv run --directory app python main.py`
- With: `uv run python app/main.py`
- Update comment on line 12 if needed to reflect new pattern
- Ensure script still executes from project root (already correct)

### Step 5: Update specs/001-phase1-project-setup.md
- Find all instances of `uv run --directory app`
- Replace with `uv run`
- Update all path examples to include `app/` prefix
- Specifically update validation commands section
- Example: `uv run --directory app pytest` → `uv run pytest app/tests/`

### Step 6: Update specs/002-phase2-core-logic-implementation.md
- Find all instances of `uv run --directory app`
- Replace with `uv run`
- Update all path examples to include `app/` prefix
- Update both task descriptions and validation commands
- Example: `uv run --directory app pytest tests/core/` → `uv run pytest app/tests/core/`

### Step 7: Update specs/004-phase3-gui-implementation.md
- Find all instances of `uv run --directory app`
- Replace with `uv run`
- Update all path examples to include `app/` prefix
- Update validation commands section

### Step 8: Update specs/006-fix-implementation-plan-cd-commands.md
- Find all instances of `uv run --directory app`
- Replace with `uv run`
- Update all path examples to include `app/` prefix
- Ironic that this spec about avoiding `cd` uses `--directory` (which changes directories)

### Step 9: Update specs/007-phase4-comprehensive-testing.md
- Find all instances of `uv run --directory app`
- Replace with `uv run`
- Update all path examples to include `app/` prefix
- This spec has many validation commands, update all of them
- Example patterns:
  - `uv run --directory app pytest` → `uv run pytest app/tests/`
  - `uv run --directory app pytest tests/core/test_extractor.py -v` → `uv run pytest app/tests/core/test_extractor.py -v`
  - `uv run --directory app pytest --cov=core` → `uv run pytest --cov=app/core app/tests/`

### Step 10: Update specs/README.md
- Review for any references to `--directory app` pattern
- Update spec writing examples if they mention the working directory convention
- Ensure consistency with new root-relative path standard

### Step 11: Run All Validation Commands
- Execute all commands from the "Validation Commands" section below
- Verify tests still pass with new virtual environment location
- Verify application launches successfully
- Verify no regressions introduced

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `test -d .venv` - Verify virtual environment exists at project root
- `test ! -d app/.venv` - Verify old virtual environment is deleted
- `uv run pytest app/tests/` - Run all tests from project root with new path pattern. All 16 tests must pass (1 skipped expected).
- `uv run pytest app/tests/ -v` - Run tests verbose to verify execution
- `uv run pytest --cov=app/core app/tests/ --cov-report=term-missing` - Run tests with coverage. Coverage must be >80%.
- `uv run python app/main.py --help 2>&1 | head -5` - Verify application can be launched (will show GUI or error, quickly exit)
- `bash scripts/start.sh &` - Verify launch script works with new pattern (will start GUI, kill quickly)
- `grep -q "uv run --directory app" README.md && echo "FAIL: Found old pattern in README" || echo "PASS: README updated"` - Verify README has no old patterns
- `grep -q "uv run --directory app" scripts/start.sh && echo "FAIL: Found old pattern in start.sh" || echo "PASS: start.sh updated"` - Verify script updated
- `grep -c "uv run --directory app" specs/*.md` - Count remaining old patterns in specs (should be 0)

## Notes

- **Virtual Environment Location**: Moving `.venv` to root doesn't affect PyInstaller. PyInstaller analyzes imports from `app/main.py` and bundles dependencies regardless of where the development virtual environment lives.

- **uv Behavior**: When you run `uv run` from project root, uv automatically:
  1. Looks for `.venv/` in current directory (finds it at root)
  2. Looks for `pyproject.toml` to determine project structure (finds it in `app/`)
  3. Uses the virtual environment from root with the project config from `app/`
  4. No `--directory` or `--project` flags needed!

- **.gitignore Already Correct**: The `.gitignore` file has `.venv` pattern on line 20, which will catch `.venv/` at any level. No changes needed.

- **No Code Changes**: This chore only changes documentation, scripts, and spec files. No changes to actual Python application code in `app/core/` or `app/tests/`.

- **Consistency Wins**: The cognitive overhead of "am I relative to root or relative to app?" is eliminated. Every single path now has the same mental model: relative to project root with `app/` prefix.

- **Claude Code Setting**: The `.claude/settings.json` setting `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR: 1` already enforces staying at project root. This chore aligns all documentation with that setting.

- **Backwards Compatibility**: After this change, old commands like `uv run --directory app pytest` will still work, but we standardize on the simpler pattern for consistency.

- **Testing Coverage**: The validation commands include comprehensive testing to ensure:
  - All 16 unit tests pass
  - Code coverage remains >80%
  - Application launches successfully
  - No old patterns remain in documentation
