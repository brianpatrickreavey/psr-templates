# Development Environment

This project supports **Python 3.8+** with `uv` for dependency management and virtual environments.

## Requirements

- Python 3.8 or higher
- `uv` package manager (for consistent, fast dependency management)

## Setup

### 1. Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create and activate virtual environment

```bash
uv venv
source .venv/bin/activate  # or equivalent for your shell
```

### 3. Install dependencies

```bash
# Install with dev dependencies (includes pytest, flake8, black, mypy, etc.)
uv sync --group dev

# Or install as editable package
uv pip install -e .
```

## Tools

- **uv**: Multi-purpose Python environment and package manager
- **pytest**: Unit and integration testing with coverage tracking
- **flake8**: Code linting (configured in `pyproject.toml`, enabled by `flake8-pyproject`)
- **black**: Code formatting (120 char line length)
- **mypy**: Static type checking (strict mode)
- **act**: Local GitHub Actions testing (isolated container execution)

## Running Tests

### Unit Tests (fastest feedback)

```bash
make test-unit
```

- Runs pytest with 95% coverage requirement
- Includes coverage report with missing line identification
- Passes locally → will pass in CI

### Full Test Suite

```bash
make test-full
```

- Runs unit tests + integration tests
- Slower but comprehensive validation

### Linting & Type Checking

```bash
make lint        # flake8 + black + mypy
make flake8      # Code linting only
make black-check # Code formatting check
make mypy        # Type checking
```

### Local CI Simulation

In the fixture repo (`psr-templates-fixture`):

```bash
make ci-simulate
```

- Runs full GitHub Actions workflow locally using `act`
- Tests behavior with different Python versions (3.8-3.12)
- Safe: All artifacts created in isolated fixture repo only

## CI/CD

The project uses GitHub Actions with `uv` for:

- PR validation across Python 3.8-3.12
- Unit tests with 95% coverage enforcement
- Linting checks (flake8, black, mypy)
- Coverage reporting to Codecov
- Automatic releases via python-semantic-release

## Configuration Files

- `pyproject.toml`: Project metadata, dependencies, tool configuration
- `.pre-commit-config.yaml`: Pre-commit hooks (linting before commits)
- `.github/workflows/pr-validation.yml`: GitHub Actions validation workflow

## Key Dependencies

**Runtime:**
- `tomli`: TOML parsing (Python < 3.11 only)

**Dev Group:**
- `pytest`, `pytest-mock`, `pytest-cov`: Testing framework with mocking and coverage
- `flake8`, `flake8-pyproject`: Code linting (pyproject.toml support)
- `black`: Code formatting
- `mypy`: Type checking
- `python-semantic-release`: Automated versioning and releases

See `pyproject.toml` for complete dependency list.
