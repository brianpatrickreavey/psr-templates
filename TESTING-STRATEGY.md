# Testing Strategy for PSR Template Test Harness

This document outlines the comprehensive testing strategy for the PSR (Python Semantic Release) Template Test Harness. The strategy separates unit tests from integration tests for maintainability, incorporates real actions (git commits, tags, PSR execution), and distinguishes between local and CI execution. The goal is 100% coverage for unit tests and 95% for integration tests.

## Overall Testing Strategy

- **Unit Tests**: Isolated, fast tests with 100% coverage goal. Use mocks/stubs for all external dependencies (git, PSR, file I/O). Focus on component logic (e.g., arranger, config parsing, edge cases like invalid inputs or empty states).
- **Integration Tests**: End-to-end tests with 95% coverage goal. Use real actions (git commits, tags, PSR execution) in phases. Focus on file outputs, version numbers, dates, ending tags/releases, and release artifacts. Fail fast and clean up after failures.
- **Directory Structure**:
  - `tests/unit/`: Unit tests (e.g., `test_arranger.py`, `test_config.py`).
  - `psr-templates-fixture/tests/integration/pre_psr/`: Pre-PSR validation tests (moved to fixture repo).
  - `psr-templates-fixture/tests/integration/post_psr/`: Post-PSR validation tests (moved to fixture repo).
  - `psr-templates-fixture/tests/conftest.py`: Shared fixtures (moved to fixture repo).
- **Tools**: pytest for all tests; act for local CI simulation; GitHub Actions for full CI. Use Make for consistent execution.

## What Can Be Run Locally (pytest and/or act)

- **Unit Tests**: Fully runnable locally with Make. Command: `make test-unit`.
  - Validates: Component logic with mocks; no real side effects.
- **Pre-PSR Integration Tests**: Runnable locally with Make/act. Command: `make test-integration-pre`.
  - Creates a `ci` branch in the fixture repo, runs tests, and cleans up the branch.
  - Validates: Template arrangement, commit generation, and setup up to PSR execution.
  - Uses real git operations within pytest steps.
- **Post-PSR Integration Tests**: Runnable locally with mocks; in act/Actions with real PSR validation. Command: `make test-integration-post`.
  - Locally: Uses mocked PSR outputs for fast testing.
  - In act/Actions: Validates actual PSR-generated files/tags via `PSR_VALIDATE_REAL=true` env var.
- **Full End-to-End**: Not fully local due to real PSR dependencies; approximate with `make test-full` using act.

## What Requires GitHub Actions

- **Full Integration Tests**: Must run in GitHub Actions for real PSR execution (with actual tags/releases) and external dispatching. Workflow: Consolidated `test-harness.yml` with phases: pre-PSR tests → PSR execution → post-PSR tests → cleanup.
  - Validates: Complete harness with real commits, tags, PSR analysis, releases, and result dispatching.
- **CI-Specific Scenarios**: Tests for commit types (breaking changes, features, fixes) and failures (e.g., PSR errors, pre-existing changelog/addon.xml).
- **Execution**: Trigger via repository dispatch; use job dependencies for phased testing.

## Simplified CI Workflow Approach

To avoid venv conflicts and complex dependency management, the CI workflow follows this simplified approach:

- **Always commit and push changes to `psr-templates` main before testing**
- **No checkout of `psr-templates` repo in CI** - dependencies are installed via git URLs
- **Workflow steps**:
  1. Checkout `psr-templates-fixture` repo
  2. Set up venv (`/tmp/venv`)
  3. `uv sync --group dev` (installs `psr-templates@main` and `pytest` from fixture's `pyproject.toml`)
  4. Run pre-PSR tests
- **Benefits**: Eliminates venv conflicts, simplifies workflow, ensures tests run against committed code
- **Local development**: For testing without push, use `uv pip install -e ../psr-templates` in fixture repo

## Detailed Test Phases (Integration)

- **Pre-PSR Phase**:
  - What: Validate setup (repo checkout, template arrangement, commit generation).
  - How: pytest with real git (ci branch creation/cleanup); assert file structures and commit history.
  - Local: Yes (Make/act); CI: Yes.
- **PSR Execution Phase**:
  - What: Run PSR action (no-op in act, full in Actions); test with pre-existing changelog/addon.xml.
  - How: GitHub Action with conditional `no_operation_mode` based on `GITHUB_ACTIONS` env var; validate no errors.
  - Local: Partial (PSR mocking if needed); CI: Full (act: no-op; Actions: real).
- **Post-PSR Phase**:
  - What: Validate PSR outputs (version numbers, dates, tags, releases, artifacts).
  - How: pytest assertions on real outputs in CI (act/Actions) via `PSR_VALIDATE_REAL=true` env var; mocked locally.
  - Local: Mocked; CI: Real validation.
- **Cleanup Phase**:
  - What: Remove test branches/tags; dispatch results.
  - How: Git commands and API calls; assert clean state.
  - Local: Partial; CI: Full.

## Execution Workflow

- **Local Development**: Use Make commands for consistent runs (e.g., `make test-unit` for fast feedback; `make test-integration-pre` for setup validation).
- **CI Pipeline**: Trigger via repository dispatch; run full PSR (with real releases/tags) in GitHub Actions for end-to-end validation.
- **Agent Execution Steps** (no further interaction needed):
  1. Update `tests/` directory with new tests (e.g., add assertions to placeholders, create phase subdirs).
  2. Create/update `Makefile` with targets: `test-unit`, `test-integration-pre`, `test-integration-post`, `test-full`.
  3. Modify `test-harness.yml` to consolidate jobs, add Make-based test execution, and enable real PSR validation in CI via `PSR_VALIDATE_REAL=true` env var.
  4. Run local tests with Make/act; push and trigger CI for full validation.
  5. Ensure coverage via pytest-cov; monitor for 100% unit / 95% integration.
- **Failure Handling**: Unit tests run full suite; integration tests fail fast and clean up (e.g., delete ci branch on failure).

## Environment-Specific Test Execution Flow

| Step                  | Local (via `make test-integration-post`) | act (Local Simulation) | GitHub Actions (Real CI) |
|-----------------------|------------------------------------------|-------------------------|---------------------------|
| **PSR Execution**    | No PSR run; tests use mocks.            | Real PSR runs in `no_operation_mode: true` on fixture repo (analyzes commits, generates local outputs). | Real PSR runs fully on fixture repo (creates and pushes tags, releases if applicable; no_operation_mode: false). |
| **Post-PSR Tests**   | Run mocked tests from templates repo (validate simulated data like version, changelog). | Run tests from fixture repo with `PSR_VALIDATE_REAL=true` set in workflow, validating actual PSR outputs (e.g., check generated files, tags). | Run tests from fixture repo with `PSR_VALIDATE_REAL=true` set in workflow, validating actual PSR outputs (e.g., check generated files, tags, releases). |
| **Outcome**          | Fast, isolated validation; no external deps. | Realistic simulation; validates real PSR behavior locally. | Full end-to-end validation; confirms PSR integration with actual releases/tags in production-like environment. |

## Risks and Mitigations

- **Local vs. CI Discrepancies**: Use act for simulation; tests conditionally validate mocks (local) vs. real PSR outputs (CI) via `PSR_VALIDATE_REAL` env var.
- **Test Flakiness**: Parameterize for commit scenarios; use temp repos with cleanup.
- **Dependencies**: PSR for local testing (mock if unavailable); no other tooling needed beyond git, pytest, act.
- **PSR Step Failure in act**: The PSR execution may fail in act due to Docker action limitations with Git repository access (e.g., ".git/HEAD file not found"), but `continue-on-error: true` allows the workflow to proceed. Post-PSR tests run with mocks in this case, validating the overall logic. This does not affect GitHub Actions execution.

## NOTE: Workflow Organization

GitHub Actions workflows are repository-specific and can only be triggered and executed within the repository where they are defined (e.g., in the `.github/workflows/` directory of that repo). You cannot directly run or reference a workflow file from one repository (like psr-templates) within another repository (like psr-templates-fixture). This is a security and isolation feature of GitHub Actions.

However, you can achieve cross-repository coordination using mechanisms like:
- **Repository Dispatch Events**: The psr-templates repo can send a dispatch event to psr-templates-fixture to trigger its workflows (as currently implemented with the `repository_dispatch` trigger).
- **Workflow Run Triggers**: One repo's workflow can trigger another repo's workflow via API calls or external tools.
- **Reusable Workflows**: GitHub supports reusable workflows, but they must be called from within the same repository or organization, not across different repos.

For organizational sense, keeping CI flows in psr-templates would be cleaner (centralizing logic), but since the workflows need to operate on the fixture repo (psr-templates-fixture), they must reside there. The current setup (workflows in psr-templates-fixture, triggered from psr-templates) is the correct approach. If you'd like to explore alternatives (e.g., moving logic to psr-templates and using dispatch), that could work but would require API-based triggering.