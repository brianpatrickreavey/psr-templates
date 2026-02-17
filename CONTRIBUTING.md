# Contributing to PSR Templates

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the PSR Templates project.

## Code of Conduct

Be respectful and constructive in all interactions with other contributors and maintainers.

## How to Contribute

### Reporting Bugs

1. **Search existing issues** to avoid duplicates
2. **Include detailed information:**
   - Python version (`python --version`)
   - How to reproduce the issue
   - Expected vs. actual behavior
   - Full error message or traceback
   - Your `pyproject.toml` configuration (sanitized)
3. **Use a clear, descriptive title**

Example issue:
```
Title: Error when template path contains uppercase letters

Description:
When I run psr-build-template-structure with a template path containing uppercase letters,
I get a FileNotFoundError even though the file exists.

To reproduce:
1. Create template at: templates/MyTemplate.j2
2. Configure source-mappings: {"dest/file.txt" = "MyTemplate.j2"}
3. Run: psr-build-template-structure

Expected: Template should be found and placed
Actual: FileNotFoundError: Template file not found: MyTemplate.j2

Environment:
- Python 3.9.2
- psr-templates 0.1.0
- Linux 5.10
```

### Suggesting Enhancements

1. **Use descriptive title** explaining the enhancement
2. **Provide use case:** Why would this enhancement be useful?
3. **Describe expected behavior:** How would users interact with it?
4. **Consider alternatives:** Are there other ways to accomplish this?

Example enhancement:
```
Title: Add support for environment variable substitution in template paths

Use Case:
Users might want to use environment variables in their pyproject.toml configuration
to support different template locations in different environments (dev, staging, prod).

Expected Behavior:
[tool.arranger.source-mappings]
"dest/file.txt" = "${TEMPLATE_DIR}/file.j2"

Would expand to actual path using process environment variables.

Alternatives Considered:
- Using absolute paths (not portable)
- Using conditional configuration (verbose)
```

### Pull Requests

#### Prerequisites

1. **Fork the repository** on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/psr-templates.git
   cd psr-templates
   ```
3. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or for bug fixes:
   git checkout -b fix/issue-description
   ```

#### Development Workflow

1. **Set up development environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   pre-commit install  # Optional: auto-format on commit
   ```

2. **Make your changes:**
   - Keep commits atomic and focused
   - Write clear commit messages (see below)
   - Include tests for new functionality
   - Update docstrings and type hints

3. **Run tests and linting:**
   ```bash
   make validate        # Run all checks (lint + tests)
   make test-unit       # Run unit tests with coverage
   make lint            # Check code quality
   make black-format    # Auto-format code
   ```

4. **Verify coverage:**
   ```bash
   make coverage-report
   ```
   - Target: 95%+ coverage
   - Focus coverage on new code paths

5. **Commit your changes:**
   ```bash
   git add src/arranger/run.py tests/unit/test_arranger.py
   git commit -m "feat: brief description of your feature"
   ```

6. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub with:
   - Clear description of what changed and why
   - Reference to related issues (closes #123)
   - Summary of test coverage added

#### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to break)
- [ ] Documentation update

## Related Issues
Closes #(issue number)

## Testing
- [x] Added tests for new functionality
- [x] All existing tests pass
- [x] Coverage maintained/improved (95%+)

## Checklist
- [x] Code follows project style (black/flake8)
- [x] Type hints added (mypy strict)
- [x] Docstrings added/updated
- [x] Tests added/updated
- [x] No breaking changes
```

#### Commit Message Guidelines

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type:** feat, fix, docs, style, refactor, perf, test, chore
**Scope:** area affected (e.g., config, validation, tests)
**Subject:** 50 chars max, lowercase, no period

Examples:
```
feat(config): add environment variable substitution support
fix(validation): resolve symlink handling in override mode
docs(readme): add troubleshooting section
test(fixtures): consolidate mock setup helpers
refactor(arrange): extract path validation logic
```

### Code Style

#### Python Style

- **Formatter:** black (line length: 120)
- **Linter:** flake8
- **Type Checker:** mypy (strict mode)
- **Version:** Python 3.8+

#### Type Hints

All code must be fully typed:

```python
# ✅ CORRECT: Full type hints
def load_config(pyproject_path: Path) -> Dict[str, Any]:
    """Load configuration from pyproject.toml."""
    ...

# ❌ WRONG: Missing types
def load_config(pyproject_path):
    """Load configuration from pyproject.toml."""
    ...
```

#### Docstrings

Use Google-style docstrings for all public functions:

```python
def build_mappings(
    config: Dict[str, Any],
    args: argparse.Namespace,
    templates_pkg: Optional[Any] = None,
) -> Dict[str, str]:
    """
    Build destination: template_path mappings.

    Constructs a mapping dictionary from configuration and CLI arguments.

    Args:
        config: Configuration dictionary from [tool.arranger].
        args: Parsed command-line arguments.
        templates_pkg: Optional templates package reference.

    Returns:
        Dictionary mapping destination paths to template source paths.

    Raises:
        ValueError: If configuration is invalid or flags are mutually exclusive.
    """
```

#### Error Messages

Provide clear, actionable error messages:

```python
# ✅ GOOD: Actionable and specific
raise FileNotFoundError(
    f"Template file not found: {template_path}\n"
    f"Please ensure the template exists in the templates package.\n"
    f"Available templates should be in: {TEMPLATES_PACKAGE}"
)

# ❌ POOR: Vague and unhelpful
raise FileNotFoundError(f"File not found: {template_path}")
```

### Testing

#### Test Organization

- **Location:** `tests/unit/test_arranger.py`
- **Fixtures:** `tests/unit/conftest.py`
- **Framework:** pytest
- **Mocking:** pytest-mock

#### Writing Tests

```python
def test_build_mappings_with_kodi(self, mocker):
    """Test build_mappings with kodi addon enabled."""
    config = {
        "use-default-kodi-addon-structure": True,
        "kodi-addon-directory": "script.module.test",
        "source-mappings": {},
    }
    args = mocker.MagicMock()
    args.pypi = False
    args.kodi_addon = True
    args.changelog_only = False

    result = build_mappings(config, args)

    expected = {
        "templates/script.module.test/addon.xml.j2": "kodi-addons/addon.xml.j2",
        "templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2",
    }
    assert result == expected
```

#### Test Requirements

- **Unit tests:** 34+ tests covering all code paths
- **Coverage:** 95%+ required
- **Mocking:** Use pytest-mock for external dependencies
- **Fixtures:** Reuse conftest fixtures to avoid duplication
- **Naming:** `test_<function>_<scenario>` (e.g., `test_load_config_missing_file`)

#### Running Tests

```bash
# All tests
pytest

# Specific test class
pytest tests/unit/test_arranger.py::TestLoadConfig

# Specific test
pytest tests/unit/test_arranger.py::TestLoadConfig::test_load_config_missing_pyproject -v

# With coverage
pytest --cov=arranger --cov-report=html tests/unit/

# Watch mode
make watch-tests
```

### Documentation

#### README Updates

For new features, update README.md with:
- Usage examples
- Configuration options
- Troubleshooting for common errors

#### Docstring Guidelines

- **Module docstrings:** Describe purpose and usage
- **Function docstrings:** Include Args, Returns, Raises sections
- **Comments:** Explain "why", not "what" (code says "what")

#### Example Documentation

```python
def arrange_templates(
    fixture_dir: Path,
    mappings: Dict[str, str],
    override: bool = True,
) -> None:
    """
    Place templates into the fixture directory according to mappings.

    Reads template files from the arranger.templates package and writes them
    to the specified fixture directory at the destination paths defined in the
    mappings dictionary.

    Process:
    1. Validates fixture directory (creates if missing)
    2. Imports templates from package
    3. For each mapping: reads template and writes to destination
    4. Creates parent directories as needed

    Args:
        fixture_dir: Path to fixture directory (created if missing).
        mappings: Dict mapping destination paths to template source paths.
        override: Whether to overwrite existing files (default: True).

    Raises:
        ValueError: If fixture_dir invalid or mappings empty.
        FileNotFoundError: If template file cannot be found.
        PermissionError: If lacking write permissions.
    """
```

## Project Structure

Understanding the project structure helps with contributions:

```
src/arranger/
├── __init__.py              # Package initialization
├── run.py                   # Main module (350+ lines)
│   ├── Constants            # TEMPLATES_PACKAGE, DEFAULT_TEMPLATES_DIR, etc.
│   ├── Validation functions # _validate_config, _validate_fixture_directory
│   ├── Helper functions     # _read_template_content, _handle_existing_destination
│   ├── Core functions       # load_config, build_mappings, arrange_templates, main
│
└── templates/
    ├── universal/           # Universal templates (CHANGELOG.md.j2, etc.)
    └── kodi-addons/         # Kodi addon templates (addon.xml.j2, etc.)

tests/unit/
├── conftest.py              # Pytest fixtures and setup utilities
└── test_arranger.py         # Unit tests (648 lines, 34 tests)

[root]/
├── README.md                # User documentation
├── CONTRIBUTING.md          # This file
├── pyproject.toml           # Build and tool configuration
├── setup.cfg                # Flake8 configuration
├── Makefile                 # Development automation
└── AUDIT-FINDINGS.md        # Improvement tracking
```

## Development Tools

### Make Targets

```bash
make test-unit          # Run unit tests with coverage
make lint               # Run flake8, black-check, mypy
make black-format       # Auto-format code
make validate           # Run lint + tests
make coverage-report    # Generate HTML coverage report
make watch-tests        # Watch mode (auto-run tests)
make run-test-harness   # Trigger integration tests
make status-test-harness # Check integration test status
```

### Pre-commit Hooks (Optional)

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

## Release Process

Only maintainers create releases, but understanding the process helps:

1. **Bump version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Create git tag:** `git tag v0.x.y`
4. **Push:** `git push origin main --tags`
5. **PyPI:** Automated via GitHub Actions

## Recognition

Contributors are recognized in:
- GitHub Contributors page
- Release notes / CHANGELOG
- Project documentation

Thank you for contributing to PSR Templates! 🎉
