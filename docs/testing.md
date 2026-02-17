# Testing Strategy

This document outlines the comprehensive testing strategy for PSR Templates. The strategy separates unit tests from integration tests for maintainability and distinguishes between local development and CI execution.

## Testing Goals

- **Unit Tests**: 95%+ coverage with mocks for all external dependencies
- **Integration Tests**: End-to-end validation in fixture repo (psr-templates-fixture)
- **Local Development**: Run with `make test-unit` for fast feedback
- **CI Pipeline**: Full validation in GitHub Actions

## Test Structure

```
tests/unit/
├── test_arranger.py        # 56 tests, 98% coverage (Phase 5)
├── conftest.py             # Shared fixtures and helpers
└── __pycache__/
```

**Note:** Integration tests run in `psr-templates-fixture/` repo to avoid polluting the source repo.

## Running Tests Locally

### Unit Tests (Fast)

```bash
make test-unit
```

- Runs 56 tests with mocks for external dependencies
- Validates component logic, error handling, edge cases
- Reports coverage (95% threshold)
- ~1 second execution

### Full Test Suite

```bash
make test-full
```

Includes unit tests + integration tests (if psr-templates-fixture is available).

### Linting & Type Checking

```bash
make lint        # flake8 + black + mypy
make mypy        # Type checking only
```

## Test Categories

### Unit Tests (56 tests, 98% coverage)

**Configuration Tests (6):**
- Config loading from pyproject.toml
- Missing files, malformed TOML, TOML decode errors
- Default values and config merging

**Mapping Tests (18):**
- Default mappings for project types
- Custom source-mappings validation
- Path validation and conflict detection
- Flag handling and exclusivity

**File Operations (15):**
- Template reading and content extraction
- Destination file creation
- Symlink handling and override behavior
- Permission errors and encoding issues

**Error Handling (17):**
- All exception paths tested
- Validation failures
- Configuration type/value constraints
- Edge cases (empty values, non-string values, missing fields)

### Integration Tests (psr-templates-fixture)

Run separately in fixture repo after committing changes to main repo:

```bash
cd psr-templates-fixture
make test-integration-pre   # Pre-PSR setup validation
make test-integration-post  # Post-PSR output validation
```

**Pre-PSR Phase:**
- Template arrangement in fixture repo
- Commit generation
- Setup validation before PSR execution

**Post-PSR Phase:**
- Generated changelog validation
- Version numbers and dates
- File rendering and format
- Release artifacts

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/pr-validation.yml`):

1. **PR Validation** (on pull_request or push to main)
   - Matrix: Python 3.8, 3.9, 3.10, 3.11, 3.12
   - Run flake8, black, mypy
   - Run unit tests with 95% coverage requirement
   - Upload coverage to Codecov (Python 3.9 only)
   - Comment PRs with validation results

2. **Required Status** (Python 3.9 must pass)
   - Blocks merge if tests fail on Python 3.9
   - Soft warnings for older/newer Python versions

## Test Environment

### Local Development

```bash
# Activate venv
source .venv/bin/activate

# Run tests
make test-unit

# Check coverage
make test-unit  # Shows coverage report at end
```

### GitHub Actions

- Runs on ubuntu-latest
- Installs Python versions 3.8-3.12
- Uses pip cache for faster builds
- Uploads coverage to Codecov

### Local CI Simulation (act)

For testing GitHub Actions locally:

```bash
cd psr-templates-fixture
make ci-simulate
```

This runs the actual GitHub Actions workflows in Docker (requires Docker and act).

## Test Dependencies

**Testing Framework:**
- pytest (test runner)
- pytest-mock (mocking)
- pytest-cov (coverage tracking)

**Code Quality:**
- flake8 (linting)
- black (formatting)
- mypy (type checking)

See `pyproject.toml` for complete dependency list.

## Coverage Standards

- **Minimum threshold**: 95% (enforced in CI)
- **Current**: 98% (56 tests, 187/191 statements covered)
- **Uncovered lines**: 4 total (acceptable edge cases and intentional pragma: no cover)

### `pragma: no cover` Usage

Lines marked with `# pragma: no cover` are explicitly excluded from coverage requirements. These must be approved and documented.

**Current usage:**
- Line 229: PyPI config path (future feature, not production-ready)

## Failure Handling

**Unit Tests:**
- Run full suite on any failure
- Detailed error messages with stack traces
- Coverage report shows missing lines

**Integration Tests:**
- Fail fast to save time
- Clean up test artifacts on failure
- Report which phase failed

## Continuous Integration Rules

- **Commit before testing** - CI always tests against committed code from main
- **Python 3.9 required** - Tests must pass on 3.9; other versions are optional
- **Coverage threshold** - Must meet 95% minimum
- **Type checking required** - mypy must pass with strict mode
- **Code formatting required** - black and flake8 must pass

## See Also

- [Development Guide](./environment.md) - Setup and tools
- [Coding Conventions](./conventions.md) - Testing standards
- [Architecture](./architecture.md) - Component design and testing patterns
