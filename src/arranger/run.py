#!/usr/bin/env python3
"""
Arranger script: Build template structure from PSR templates.

Reads config from pyproject.toml [tool.arranger], places templates.
"""

import argparse
from pathlib import Path
import tomllib
import importlib.resources


def load_config(pyproject_path):
    """Load [tool.arranger] from pyproject.toml."""
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    config = data.get("tool", {}).get("arranger", {})
    # Set defaults
    config.setdefault("use-default-pypi-structure", False)
    config.setdefault("use-default-kodi-addon-structure", False)
    config.setdefault("kodi-project-name", "script.module.example")
    config.setdefault("source-mappings", {})
    return config


def build_mappings(config, args):
    """Build the target: template mappings."""
    mappings = {}
    # Default: changelog
    mappings["CHANGELOG.md"] = "universal/CHANGELOG.md.j2"

    if config.get("use-default-pypi-structure") or args.pypi:
        # TODO: Add PyPI defaults
        pass

    if config.get("use-default-kodi-addon-structure") or args.kodi_addon:
        kodi_name = config.get("kodi-project-name")
        mappings["addon.xml"] = f"kodi/{kodi_name}/addon.xml"

    # Add custom mappings
    for target, template in config.get("source-mappings", {}).items():
        if target in mappings:
            raise ValueError(f"Cannot override default mapping for {target}")
        mappings[target] = template

    return mappings


def arrange_templates(fixture_dir, mappings):
    """Place templates."""
    # Assume templates are in psr_templates.templates
    templates_package = "psr_templates.templates"
    for target, template in mappings.items():
        template_file = importlib.resources.files(templates_package) / template
        content = template_file.read_text()
        # Place raw template content
        dst = fixture_dir / target
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise FileExistsError(f"Target {dst} already exists")
        dst.write_text(content)
        print(f"Placed {template} to {dst}")


def main():
    parser = argparse.ArgumentParser(
        description="Build template structure from PSR templates."
    )
    parser.add_argument(
        "--pypi", action="store_true", help="Include default PyPI structure"
    )
    parser.add_argument(
        "--kodi-addon", action="store_true", help="Include default Kodi addon structure"
    )
    parser.add_argument(
        "--changelog-only", action="store_true", help="Only create changelog"
    )
    args = parser.parse_args()

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found in current directory")

    config = load_config(pyproject_path)
    mappings = build_mappings(config, args)
    arrange_templates(Path("."), mappings)
    print("Template structure built.")


if __name__ == "__main__":
    main()  # pragma: no cover
