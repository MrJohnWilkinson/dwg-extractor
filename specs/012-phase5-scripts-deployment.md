# Chore: Phase 5 - Scripts and Deployment

## Chore Description
Create production-ready deployment scripts and documentation for the DWG Block Extractor application. This phase includes:
- Enhancing the existing launch script with robust error handling and platform support
- Creating a build script to generate standalone executables using PyInstaller
- Adding comprehensive usage documentation to the README
- Ensuring all scripts follow the project's working directory convention (root-relative paths, no `cd` usage)

All scripts must execute from the project root using `uv run` with root-relative paths (e.g., `app/main.py`), maintaining consistency with the project's established conventions.

## Relevant Files
Use these files to resolve the chore:

- **scripts/start.sh** (exists) - Current launch script that needs enhancement with better error handling, uv availability check, platform support documentation, and comprehensive logging
- **README.md** (exists) - Project documentation that needs a new "Usage" section detailing how to run the application in development and production modes, plus build instructions
- **pyproject.toml** (exists) - Contains build dependencies (`pyinstaller>=6.0.0`) in `[project.optional-dependencies.build]` section that need to be utilized
- **app/main.py** (exists) - Application entry point, used to understand the application structure for build configuration

### New Files
- **scripts/build.sh** - New build script to generate standalone executables for Windows, Linux, and macOS using PyInstaller with proper configuration for CustomTkinter, ezdxf, and embedded resources

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Enhance the Launch Script (scripts/start.sh)
- Add comprehensive error handling for missing uv installation
- Add check to verify virtual environment exists and suggest installation if missing
- Add platform detection and display platform-specific launch information
- Add verbose logging option to show startup diagnostics
- Ensure script maintains root-relative path convention (`uv run python app/main.py`)
- Add success message when application launches successfully
- Add option to check Python version compatibility (requires Python 3.11+)

### 2. Create Build Script (scripts/build.sh)
- Create new executable build script following the working directory convention
- Install build dependencies using `UV_PROJECT=. uv pip install --group build` or equivalent uv command
- Configure PyInstaller to bundle the application with all dependencies
- Set up proper icon path handling (create placeholder for future icon)
- Configure PyInstaller for CustomTkinter (requires special data file handling)
- Configure PyInstaller for ezdxf library compatibility
- Set application metadata (name, version from pyproject.toml)
- Create platform-specific executables in `dist/` directory
- Add cleanup of build artifacts (build/, *.spec files) with option to preserve
- Add verbose output showing build progress
- Generate executable for current platform (Windows: .exe, Linux/macOS: binary)
- Create basic PyInstaller spec file template for customization
- Add post-build verification that executable was created successfully

### 3. Update README Documentation
- Add new "Usage" section after "Project Structure" with three subsections
- **Development Mode** subsection:
  - Quick start: `scripts/start.sh` or `uv run python app/main.py`
  - Running tests: `uv run pytest app/tests/`
  - Coverage reports: `uv run pytest --cov=app/core app/tests/`
- **Building Executable** subsection:
  - Install build dependencies: `UV_PROJECT=. uv pip install --group build`
  - Run build script: `scripts/build.sh`
  - Location of generated executable: `dist/DWGBlockExtractor[.exe]`
  - Platform-specific notes for Windows, Linux, macOS
- **Production Mode** subsection:
  - How to run the built executable
  - No Python installation required for end users
  - Troubleshooting common issues (permissions, missing libraries)
- Add note about working directory convention in Usage section
- Update "Tech Stack" section to mention PyInstaller for deployment

### 4. Make Scripts Executable
- Set executable permissions on scripts/start.sh: `chmod +x scripts/start.sh`
- Set executable permissions on scripts/build.sh: `chmod +x scripts/build.sh`
- Verify permissions with `ls -l scripts/`

### 5. Test Scripts and Documentation
- Run `scripts/start.sh` to verify enhanced launch script works correctly
- Verify script output shows proper error messages and diagnostics
- Install build dependencies: `UV_PROJECT=. uv pip install --group build`
- Run `scripts/build.sh` to verify build process completes successfully
- Verify executable is created in `dist/` directory
- Manually test the generated executable (if GUI environment available)
- Review README updates for clarity and completeness

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/` - Run all tests to ensure no regressions in core functionality
- `uv run pytest --cov=app/core app/tests/` - Verify test coverage remains at acceptable levels
- `test -f scripts/start.sh && test -x scripts/start.sh` - Verify start script exists and is executable
- `test -f scripts/build.sh && test -x scripts/build.sh` - Verify build script exists and is executable
- `bash -n scripts/start.sh` - Validate start script syntax
- `bash -n scripts/build.sh` - Validate build script syntax
- `scripts/start.sh --help || true` - Test that start script runs without errors (will show help or launch GUI)
- `grep -q "## Usage" README.md` - Verify README contains new Usage section
- `grep -q "Development Mode" README.md` - Verify Development Mode documentation exists
- `grep -q "Building Executable" README.md` - Verify build documentation exists
- `grep -q "Production Mode" README.md` - Verify production documentation exists

## Notes
- **Platform Compatibility:** Build script should detect current platform and build appropriate executable format
- **PyInstaller CustomTkinter:** CustomTkinter requires special handling in PyInstaller - need to include theme files and data directories using `--add-data` flag
- **PyInstaller ezdxf:** The ezdxf library may require `--hidden-import` flags for certain submodules
- **Icon Support:** Build script should support optional icon parameter for branding (default: no icon)
- **Working Directory Convention:** Both scripts MUST execute from project root and use root-relative paths - never use `cd` commands
- **Testing Limitation:** Executable testing may be limited in headless environments; manual testing recommended when GUI is available
- **Build Dependencies:** The pyproject.toml already includes `pyinstaller>=6.0.0` in the build group, so we just need to install it
- **Error Handling:** Scripts should fail gracefully with clear error messages for common issues (missing dependencies, permission errors, etc.)
- **Future Enhancements:** Consider adding cross-platform build matrix, automated testing of executables, and CI/CD integration in future phases
