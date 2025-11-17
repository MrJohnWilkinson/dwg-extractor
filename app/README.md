# Application Directory

DWG Block Extractor application code following TAC standardized app structure.

## Project Structure

```
app/
├── core/                         # Core business logic
│   ├── extractor.py              # DWG/DXF extraction logic
│   ├── excel_writer.py           # Excel generation
│   ├── constants.py              # Application constants
│   └── logger.py                 # Stdout logging
├── tests/                        # Test suite
│   ├── core/                     # Unit tests
│   └── assets/                   # Test fixtures (DXF files)
├── main.py                       # GUI entry point (CustomTkinter)
├── pyproject.toml                # Dependencies (uv)
└── .python-version               # Python 3.11
```

## Dependencies (pyproject.toml)

```toml
[project]
name = "dwg-block-extractor"
version = "0.1.0"
requires-python = ">=3.8"
dependencies = [
    "ezdxf>=1.0.0",           # DWG/DXF parsing
    "pandas>=2.0.0",          # Data manipulation
    "openpyxl>=3.1.0",        # Excel generation
    "customtkinter>=5.2.0",   # Modern GUI
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-cov>=4.0.0"]
build = ["pyinstaller>=6.0.0"]
```

## Core Modules

**extractor.py** - Loads DWG/DXF files, iterates modelspace INSERT entities, counts block references
```python
def extract_blocks(file_path: str) -> dict[str, int]:
    """Extract block insertion counts from DWG/DXF file."""
```

**excel_writer.py** - Generates formatted Excel with pandas/openpyxl, sorting and auto-filtering
```python
def write_excel(block_data: dict[str, int], output_path: str) -> str:
    """Write block data to Excel with formatting."""
```

**constants.py** - Application-wide constants: file extensions, Excel column names, UI messages

**logger.py** - Centralized logging to stdout for LLM agent monitoring
```python
from core.logger import setup_logger
logger = setup_logger(__name__)
logger.info("Processing started")
```

## Testing

```bash
cd app
uv run pytest                                        # Run all tests
uv run pytest --cov=core --cov-report=term-missing  # With coverage
uv run pytest tests/core/test_extractor.py -v       # Specific tests
```

**Coverage Target:** >80% for core modules

## Dependency Management (uv)

```bash
cd app
uv sync                 # Install dependencies
uv add package-name     # Add new dependency
uv add --dev package    # Add dev dependency
uv sync --upgrade       # Update dependencies
```

## Environment Variables (Optional)

Create `.env` in app directory:
```bash
LOG_LEVEL=INFO
DEBUG=false
OUTPUT_DIR=./output
AUTO_OPEN_EXCEL=true
```

Load with:
```python
from dotenv import load_dotenv
import os

load_dotenv()
log_level = os.getenv("LOG_LEVEL", "INFO")
```

## GUI Application (main.py)

CustomTkinter interface with:
- File picker for DWG/DXF selection
- Extract button to trigger processing
- Progress bar for visual feedback
- Status label for operation updates
- Auto-open Excel on completion

**Components:**
- `DWGExtractorApp(ctk.CTk)` - Main application class
- Threading for non-blocking extraction
- Error dialogs for invalid files

## Integration with scripts/start.sh

Launcher script:
```bash
#!/bin/bash
cd "$(dirname "$0")/../app" || exit 1
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi
uv run python main.py
```

## Best Practices

1. **Use uv exclusively** - No pip, conda, or other package managers
2. **Log to stdout** - All modules use centralized logger for LLM monitoring
3. **Test alongside implementation** - Write tests as you develop
4. **Follow TAC structure** - Keep core logic separate from UI
5. **Handle errors gracefully** - Display user-friendly error messages

## Resources

- **ezdxf:** https://ezdxf.readthedocs.io/
- **CustomTkinter:** https://customtkinter.tomschimansky.com/
- **pytest:** https://docs.pytest.org/
- **uv:** https://docs.astral.sh/uv/
