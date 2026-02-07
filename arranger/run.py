#!/usr/bin/env python3
"""
Arranger script: Place PSR templates and configure the fixture repo.

Reads template-to-destination mappings from pyproject.toml [tool.arranger],
copies templates, and updates PSR config.
"""

import shutil
import sys
from pathlib import Path
import tomllib  # Python 3.11+, or tomli for older

def load_config(pyproject_path):
    """Load [tool.arranger] from pyproject.toml."""
    with open(pyproject_path, 'rb') as f:
        data = tomllib.load(f)
    return data.get('tool', {}).get('arranger', {})

def arrange_templates(templates_dir, fixture_dir, config):
    """Copy templates to destinations based on config."""
    # Example: config = {'changelog': 'CHANGELOG.md', 'addon_xml': 'addon/addon.xml'}
    for template, dest in config.items():
        src = templates_dir / f"{template}.j2"
        dst = fixture_dir / dest
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        print(f"Copied {src} to {dst}")

def update_psr_config(fixture_pyproject, templates_dir):
    """Update PSR config to point to new template paths."""
    # Read, modify, write back
    with open(fixture_pyproject, 'r') as f:
        content = f.read()

    # Simple replace for now
    updated = content.replace('template_dir = "templates"', f'template_dir = "{templates_dir}"')
    with open(fixture_pyproject, 'w') as f:
        f.write(updated)
    print(f"Updated PSR config in {fixture_pyproject}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python run.py <templates_dir> <fixture_dir>")
        sys.exit(1)

    templates_dir = Path(sys.argv[1])
    fixture_dir = Path(sys.argv[2])

    pyproject_path = fixture_dir / 'pyproject.toml'
    config = load_config(pyproject_path)

    arrange_templates(templates_dir, fixture_dir, config)
    update_psr_config(pyproject_path, templates_dir)

    print("Arrangement complete.")

if __name__ == '__main__':
    main()