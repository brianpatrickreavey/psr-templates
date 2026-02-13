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
    config.setdefault("root_dir", ".")
    return config


def build_mappings(config, args):
    """Build the target: template mappings."""
    mappings = {}
    root_dir = config["root_dir"]
    # Default: changelog
    mappings[f"{root_dir}/templates/CHANGELOG.md.j2"] = "universal/CHANGELOG.md.j2"

    if config.get("use-default-pypi-structure") or args.pypi:
        # TODO: Add PyPI defaults
        pass

    if config.get("use-default-kodi-addon-structure") or args.kodi_addon:
        kodi_name = config.get("kodi-project-name")
        mappings[f"{root_dir}/../templates/addon.xml.j2"] = "kodi-addons/addon.xml.j2"

    # Add custom mappings
    for target, template in config.get("source-mappings", {}).items():
        if target in mappings:
            raise ValueError(f"Cannot override default mapping for {target}")
        mappings[target] = template

    return mappings


def arrange_templates(fixture_dir, mappings, override=False):
    """Place templates."""
    # Assume templates are in psr_templates.templates
    templates_package = "arranger.templates"
    for target, template in mappings.items():
        template_file = importlib.resources.files(templates_package) / template
        content = template_file.read_text()
        # Place raw template content
        dst = fixture_dir / target
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Overwrite if exists
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
    parser.add_argument(
        "--override", action="store_true", help="Override default mappings"
    )
    args = parser.parse_args()

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found in current directory")

    config = load_config(pyproject_path)
    mappings = build_mappings(config, args)
    arrange_templates(Path("."), mappings, override=args.override)
    print("Template structure built.")


if __name__ == "__main__":
    main()  # pragma: no cover
