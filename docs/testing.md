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

**Test Categories:**

1. **Pre-PSR Phase Tests** (`tests/integration/pre_psr/`):
   - Validates that arranger correctly places templates in fixture repo
   - Runs immediately after templates are committed to main branch
   - Uses `test_template_arrangement()` to verify:
     - `templates/CHANGELOG.md.j2` exists
     - `templates/script.module.example/addon.xml.j2` exists
   - Quick validation (~0.02s) before PSR execution
   - No external dependencies

2. **Post-PSR Phase Tests** (`tests/integration/post_psr/`):
   - Validates that PSR correctly renders templates in fixture repo
   - Runs after PSR creates releases and generates CHANGELOG.md/addon.xml
   - **TestMultiReleaseProgression** (8 tests):
     - `test_release_0_1_0_changelog`: First release only
     - `test_release_0_1_0_addon_xml`: Version and structure validation
     - `test_release_0_2_0_changelog_cumulative`: Cumulative history (0.1.0 + 0.2.0)
     - `test_release_0_2_0_addon_xml_cumulative`: Version updated to 0.2.0
     - `test_release_1_0_0_changelog_full_history`: All versions present
     - `test_release_1_0_0_addon_xml_major_version`: Version 1.0.0
     - `test_changelog_markdown_format`: Validates syntax
     - `test_addon_xml_no_jinja_references`: No unrendered template markers
   - **TestTemplateRenderingEdgeCases** (2 tests):
     - `test_changelog_handles_empty_sections`: Empty content handled
     - `test_addon_xml_has_required_attributes`: XML structure intact
   - Tests gracefully skip if PSR hasn't run yet (pytest.skip)
   - Full validation (~0.1s per test) when files exist

## Integration Test Workflow

### Dispatch Workflow (GitHub Actions)

The psr-templates repository has a dispatch workflow that orchestrates testing:

**Workflow:** `.github/workflows/dispatch-test-harness.yml`

**How it works:**
1. User runs: `make run-test-harness`
2. Workflow sends `repository_dispatch` event to psr-templates-fixture repo
3. Payload includes: templates_repo, templates_ref, run_id (metadata)
4. Fixture repo's test-harness workflow receives event and:
   - Clones templates from specified ref
   - Copies templates to fixture repo
   - Runs arranger to place templates
   - Runs PSR to generate releases and artifacts
   - Runs integration tests to validate output

**Example:**
```bash
# In psr-templates repo
make run-test-harness    # Dispatches "main" branch to fixture repo
```

This creates a workflow run in psr-templates-fixture that executes the full pipeline.

**Monitoring:** `make watch-test-harness-output` and `make logs-test-harness`

### Local Testing with act

To simulate the GitHub Actions workflow locally (with Docker):

```bash
cd psr-templates-fixture
make ci-simulate      # Runs test-harness-act.yml workflow locally
```

**Note:** This uses Docker and requires `act` to be installed. In some environments (like WSL), this may have issues contacting the Docker daemon.

### Local Manual Testing

For development without GitHub Actions:

```bash
# Step 1: Template arrangement (Pre-PSR)
cd psr-templates-fixture
python -m pytest tests/integration/pre_psr/ -v
# Expected: test_template_arrangement passes

# Step 2: Run PSR manually (if you have PSR installed)
cd psr-templates-fixture
semantic-release version  # Generate new release and render templates
# Creates CHANGELOG.md and renders addon.xml.j2 → addon.xml

# Step 3: Validate output (Post-PSR)
python -m pytest tests/integration/post_psr/ -v
# Expected: Multiple tests validate the generated files
```

### Integration Test Results

Post-PSR tests validate three cumulative releases:

**Release 0.1.0 (First release):**
- CHANGELOG.md: Section for v0.1.0 only
- addon.xml: Version="0.1.0", news section with all commits
- Validates initial template rendering

**Release 0.2.0 (Second release):**
- CHANGELOG.md: Sections for v0.1.0 AND v0.2.0 (cumulative)
- addon.xml: Version="0.2.0", news section with only 0.2.0 commits (NOT 0.1.0)
- Validates cumulative CHANGELOG, latest-only news in addon.xml

**Release 1.0.0 (Third release):**
- CHANGELOG.md: All three sections (v0.1.0, v0.2.0, v1.0.0)
- addon.xml: Version="1.0.0", news section with only 1.0.0 commits
- Validates major version bump and history preservation in CHANGELOG

### Test Helpers

Shared parsing utilities in `psr-templates-fixture/tests/test_helpers.py`:

- **AddonXmlParser**: Parses XML, extracts version/news/structure
- **ChangelogParser**: Extracts releases, sections, commit counts
- **JinjaTemplateValidator**: Detects unrendered Jinja2 syntax
- **AddonXmlInfo** and **ReleaseInfo**: Data classes for parsed info

These helpers are used by both test_multi_release.py and test_post_psr.py for consistent validation.

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
