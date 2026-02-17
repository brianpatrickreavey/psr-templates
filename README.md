# PSR Templates

A Python utility for building template structures for PSR (Package/Project Structure Recommendations) compliant projects. Supports multiple project types including Python packages, Kodi addons, and custom configurations.

**Status:** ✅ Production-Ready (Phase 4+ complete)

## Features

- **Multiple Project Types:** Built-in templates for PyPI packages and Kodi addons
- **Custom Mappings:** Define your own template sources and destinations
- **Comprehensive Error Handling:** Clear error messages with actionable guidance
- **Type Safety:** Full type hints with mypy strict mode enforcement
- **Well Documented:** Extensive docstrings and configuration examples
- **Thoroughly Tested:** 34 unit tests with 80%+ coverage

## Installation

### From PyPI (Production)
```bash
pip install psr-templates
```

### From Source (Development)
```bash
git clone https://github.com/brianpatrickreavey/psr-templates.git
cd psr-templates
pip install -e .
```

### Requirements
- Python 3.8 or higher
- No external dependencies (uses standard library only)

## Quick Start

### Basic Usage

The simplest way to use PSR Templates is to run the command from your project root:

```bash
# Only create CHANGELOG.md template (default)
psr-build-template-structure

# Include Kodi addon structure
psr-build-template-structure --kodi-addon

# Include PyPI package structure
psr-build-template-structure --pypi

# Overwrite existing files
psr-build-template-structure --override
```

### Configuration

Create a `[tool.arranger]` section in your `pyproject.toml`:

```toml
[tool.arranger]
# Optional: specify custom templates directory (default: "templates")
templates-dir = "templates"

# Optional: include default Kodi addon structure
use-default-kodi-addon-structure = true
kodi-project-name = "script.module.example"

# Optional: custom source-to-destination mappings
[tool.arranger.source-mappings]
"docs/VERSION.md" = "universal/VERSION.md.j2"
"src/constants.py" = "python-packages/constants.py.j2"
```

## Usage Examples

### Example 1: Kodi Addon Project

```toml
[tool.arranger]
templates-dir = "templates"
use-default-kodi-addon-structure = true
kodi-project-name = "script.module.myproject"
```

Then run:
```bash
psr-build-template-structure --override
```

**Result:** Creates templates at:
- `templates/script.module.myproject/addon.xml.j2` → `script.module.myproject/addon.xml`
- `templates/CHANGELOG.md.j2` → `CHANGELOG.md`

### Example 2: PyPI Package with Custom Mappings

```toml
[tool.arranger]
templates-dir = "templates"

[tool.arranger.source-mappings]
"src/version.py" = "python-packages/version.py.j2"
"docs/CHANGELOG.md" = "universal/CHANGELOG.md.j2"
```

Then run:
```bash
psr-build-template-structure --pypi
```

**Result:** Creates all mapped templates in the fixture directory.

### Example 3: Custom Project Structure

```toml
[tool.arranger]
templates-dir = "my-templates"

[tool.arranger.source-mappings]
"docs/README.md" = "universal/README.md.j2"
"src/LICENSE" = "LICENSE.j2"
"config/defaults.json" = "config/defaults.json.j2"
```

## Command-Line Reference

```bash
psr-build-template-structure [OPTIONS]

OPTIONS:
  --pypi                Include default PyPI package structure templates
  --kodi-addon          Include default Kodi addon structure templates
  --changelog-only      Only create CHANGELOG.md template (default if no flags)
  --override            Overwrite existing files (default: raises error if files exist)
  -h, --help            Show help message and exit

EXAMPLES:
  psr-build-template-structure
  psr-build-template-structure --kodi-addon --override
  psr-build-template-structure --pypi
```

## Configuration Reference

### Configuration Keys

All configuration is optional. Here's the complete reference:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `templates-dir` | string | `"templates"` | Directory name containing template files (relative path only) |
| `use-default-pypi-structure` | boolean | `false` | Include PyPI package structure templates |
| `use-default-kodi-addon-structure` | boolean | `false` | Include Kodi addon structure templates |
| `kodi-project-name` | string | `` | Name of Kodi addon project (required if using Kodi structure) |
| `source-mappings` | dict | `{}` | Custom source-to-destination template mappings |

### Configuration Validation

The tool validates all configuration at runtime:

- **Type checking:** Keys must have correct types (strings for names, dicts for mappings)
- **Format checking:** Paths must contain directory separators and not end with slashes
- **Conflict checking:** Custom mappings cannot override default framework mappings
- **Existence checking:** Template files must exist in the templates package

Invalid configuration produces clear error messages:
```
Error: Configuration error: 'kodi-project-name' cannot be an empty string.
```

## Troubleshooting

### Common Errors and Solutions

#### Error: "pyproject.toml not found"
**Cause:** Running the command from wrong directory
**Solution:** Run from project root (where `pyproject.toml` is located)
```bash
cd /path/to/project
psr-build-template-structure
```

#### Error: "Invalid TOML syntax"
**Cause:** Syntax error in `pyproject.toml`
**Solution:** Check TOML syntax, common issues:
- Missing quotes around strings
- Invalid key names
- Incorrect indentation
```toml
# ❌ WRONG: Missing quotes
kodi-project-name = script.module.example

# ✅ CORRECT: Strings need quotes
kodi-project-name = "script.module.example"
```

#### Error: "Permission denied creating/accessing fixture directory"
**Cause:** Insufficient write permissions
**Solution:** Check directory permissions
```bash
# Check permissions
ls -ld /path/to/fixture

# Fix if needed (example)
chmod u+w /path/to/fixture
```

#### Error: "File exists at..."
**Cause:** Destination file already exists and `--override` not specified
**Solution:** Either use `--override` flag or delete existing files
```bash
psr-build-template-structure --override
```

#### Error: "Flags ... are mutually exclusive"
**Cause:** Specified multiple flags that cannot be used together
**Solution:** Only use one project type flag
```bash
# ❌ WRONG: Both --pypi and --kodi-addon specified
psr-build-template-structure --pypi --kodi-addon

# ✅ CORRECT: Use one flag
psr-build-template-structure --pypi
```

#### Warning: "Unknown keys in [tool.arranger]"
**Cause:** Configuration contains unrecognized keys
**Solution:** Remove typos or unknown keys from configuration
```toml
[tool.arranger]
templates-dir = "templates"
typo-key = "value"  # ← This is unknown, remove it
```

### Getting Help

1. **Check the troubleshooting section** above for common issues
2. **Review configuration examples** in this README
3. **Open an issue** on GitHub with:
   - Python version (`python --version`)
   - Error message (full traceback)
   - Your `pyproject.toml` configuration
   - Command you ran

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/brianpatrickreavey/psr-templates.git
cd psr-templates

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all unit tests
make test-unit

# Run with coverage report
make coverage-report

# Run specific test class
pytest tests/unit/test_arranger.py::TestLoadConfig -v

# Watch mode (auto-run tests on file changes)
make watch-tests
```

### Code Quality

```bash
# Format code with black
make black-format

# Check code quality (flake8, black, mypy)
make lint

# Full validation (lint + tests)
make validate
```

### Project Structure

```
psr-templates/
├── src/arranger/
│   ├── __init__.py           # Package initialization
│   ├── run.py                # Main module with CLI and core functions
│   └── templates/            # Built-in Jinja2 templates
│       ├── universal/        # Universal templates (CHANGELOG, etc.)
│       └── kodi-addons/      # Kodi-specific templates
├── tests/
│   └── unit/
│       ├── conftest.py       # Pytest fixtures and configuration
│       └── test_arranger.py  # Unit tests (34 tests, 80%+ coverage)
├── pyproject.toml            # Project metadata and tool configuration
├── setup.cfg                 # Flake8 configuration
├── Makefile                  # Development automation targets
├── README.md                 # This file
├── CONTRIBUTING.md           # Contribution guidelines
└── AUDIT-FINDINGS.md         # Improvement tracking document
```

### Key Files

- **src/arranger/run.py:** Core implementation with error handling and type hints
- **tests/unit/test_arranger.py:** Comprehensive unit test suite (34 tests)
- **tests/unit/conftest.py:** Shared test fixtures and helpers
- **pyproject.toml:** Python build configuration and tool settings
- **Makefile:** Development workflow automation

## Architecture & Design

### Core Workflow

1. **Configuration Loading** (`load_config`): Parse `[tool.arranger]` from `pyproject.toml`
2. **Validation:** Verify configuration types and values
3. **Mapping Building** (`build_mappings`): Construct source→destination template mappings
4. **Template Arrangement** (`arrange_templates`): Copy templates to fixture directory
5. **Error Handling:** Clear messages for all failure scenarios

### Error Handling Strategy

- **Validation errors** (TOML, config): Caught at load/build time with suggestions
- **Runtime errors** (missing files, permissions): Caught with context before operation
- **Edge cases** (symlinks, encoding, overrides): Handled with fallback logic
- **User guidance:** All errors include suggested fixes

### Type System

- Full Python 3.8+ type hints
- mypy strict mode (`disallow_untyped_defs`, `strict_equality`)
- Type-safe Path handling with proper casts
- Generic types for configuration dictionaries

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## License

MIT License - see LICENSE file for details

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history and version notes.

## Support

- **Issues:** Report bugs and request features on [GitHub Issues](https://github.com/brianpatrickreavey/psr-templates/issues)
- **Discussions:** Ask questions on [GitHub Discussions](https://github.com/brianpatrickreavey/psr-templates/discussions)
- **Documentation:** Full API documentation in docstrings and this README
