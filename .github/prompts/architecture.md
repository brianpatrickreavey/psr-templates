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
- No rendering in arranger; raw .j2 files placed for PSR to process.
- importlib.resources preferred over file copying for embedded assets.