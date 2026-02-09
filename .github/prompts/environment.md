# Environment

## Development Environment

This project uses Python 3.13 with uv for dependency management and virtual environments. The venv is activated locally for running commands.

### Tools
- **uv**: For syncing dependencies, running commands, and managing the virtual environment.
- **pytest**: For unit and integration testing with coverage.
- **flake8** and **black**: For linting and formatting.
- **act**: For running GitHub Actions locally in isolated containers (used for safe testing with the fixture repo).

### Setup
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Create venv: `uv venv`
- Activate: `source .venv/bin/activate` (or equivalent)
- Sync deps: `uv sync --group dev`
- Install editable: `uv pip install -e .`

### Testing
- Unit tests: `make test-unit` (runs pytest with coverage)
- Full suite: `make test-full` (includes integration tests)
- Act testing: In fixture repo, `make ci-simulate` for isolated CI simulation.

### CI
- Uses GitHub Actions with uv for builds and tests.
- Fixture repo uses act for local CI testing via repository_dispatch events.