#!/usr/bin/env python3
"""
Arranger script: Place PSR templates and configure the fixture repo.

Reads template-to-destination mappings from pyproject.toml [tool.arranger],
copies templates, and updates PSR config.
"""

import shutil
import argparse
from pathlib import Path
import tomllib  # Python 3.11+, or tomli for older


def load_config(pyproject_path):
    """Load [tool.arranger] from pyproject.toml."""
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    return data.get("tool", {}).get("arranger", {})


def arrange_templates(templates_dir, fixture_dir, config):
    """Copy templates to destinations based on config."""
    # Example: config = {'universal/CHANGELOG.md.j2': 'templates/CHANGELOG.md.j2'}
    for template, dest in config.items():
        src = templates_dir / template
        dst = fixture_dir / dest
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        print(f"Copied {src} to {dst}")


def update_psr_config(fixture_pyproject, templates_dir):
    """Update PSR config to point to new template paths."""
    # Read, modify, write back
    with open(fixture_pyproject, "r") as f:
        content = f.read()

    # Simple replace for now
    updated = content.replace(
        'template_dir = "templates"', f'template_dir = "{templates_dir}"'
    )
    with open(fixture_pyproject, "w") as f:
        f.write(updated)
    print(f"Updated PSR config in {fixture_pyproject}")


def main():
    parser = argparse.ArgumentParser(
        description="Arrange PSR templates into fixture directory."
    )
    parser.add_argument(
        "--templates-dir", required=True, help="Path to the templates directory"
    )
    parser.add_argument(
        "--fixture-dir",
        default=".",
        help="Path to the fixture directory (default: current directory)",
    )
    args = parser.parse_args()

    templates_dir = Path(args.templates_dir)
    fixture_dir = Path(args.fixture_dir)

    pyproject_path = fixture_dir / "pyproject.toml"
    config = load_config(pyproject_path)

    arrange_templates(templates_dir, fixture_dir, config)
    # update_psr_config(pyproject_path, templates_dir)  # Templates are copied to fixture/templates/, so relative path "templates" works

    print("Arrangement complete.")


if __name__ == "__main__":
    main()  # pragma: no cover
