# Architecture

## High-Level Architecture

This project is a Python package providing a CLI tool for placing PSR templates in consuming repositories. The architecture is config-driven, using pyproject.toml for declarative configuration.

### Key Components
- **arranger/run.py**: Main CLI module that parses [tool.arranger] config from pyproject.toml, builds template mappings, and places raw templates using importlib.resources.
- **Templates**: Bundled as package data in psr_templates/templates/, accessed via importlib.resources for embedded file handling.
- **Config Structure**: [tool.arranger] in pyproject.toml with flags like use-default-pypi-structure, kodi-project-name, and source-mappings for custom templates.

### Patterns
- **Config-Driven CLI**: Prioritizes pyproject.toml over CLI args for reproducibility.
- **Embedded Resources**: Uses importlib.resources for cross-platform access to bundled templates without file system dependencies.
- **Separation of Concerns**: Arranger places raw templates; PSR handles rendering externally.
- **Testing**: 100% unit coverage with pytest; integration tests via act in fixture repo.

### Decisions
- CLI tool installed as package (pip install psr-templates) for easy distribution.
- No rendering in arranger; raw .j2 files placed for PSR to process (no Jinja2 dependency in arranger).
- Arranger overwrites existing files without error (no --override flag needed, as templates are raw and PSR handles rendering).
- importlib.resources preferred over file copying for embedded assets.

## CI/Test Harness Architecture

The CI/test harness is designed to validate PSR template placement and semantic release functionality in an isolated environment, ensuring no pollution of the source repositories.

### Repository Roles
- **psr-templates**: Source of truth for templates, tests, and configuration. Remains untouched during testing.
- **psr-templates-fixture**: Isolated test environment ("harness") where all test artifacts—commits, pushes, tags, releases, and modifications—live. This keeps the harness self-contained.

### Workflow Overview
1. **pre-psr-tests**: Sets up environments, runs pre-PSR integration tests on templates, arranges templates into fixture, generates test commits in fixture, and pushes the test branch to fixture.
2. **psr-execution**: Checks out the prepared fixture branch and runs PSR to analyze commits, create tags/releases, and generate changelog—all within fixture.
3. **post-psr-tests**: Runs post-PSR tests (currently on templates, but can be adjusted).
4. **cleanup**: Removes test branches and tags from fixture.

### Key Principles
- **Isolation**: Test artifacts are confined to fixture; templates repo is read-only.
- **Reusability**: Composite actions for shared steps (arranger, commit generation, PSR execution).
- **Compatibility**: Supports both GitHub Actions and local ACT testing with conditional logic.
- **Permissions**: Workflow has `contents: write` to push branches in fixture.