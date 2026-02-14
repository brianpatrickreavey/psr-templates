#!/usr/bin/env python3
"""
Arranger script: Build template structure from PSR templates.

Reads config from pyproject.toml [tool.arranger], places templates.
"""

import argparse
from pathlib import Path
import tomllib
import importlib.resources
from importlib.resources import files


def load_config(pyproject_path):
    """Load [tool.arranger] from pyproject.toml."""
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    config = data.get("tool", {}).get("arranger", {})
    # Set defaults
    config.setdefault("source-mappings", {})
    return config


def build_mappings(config, args):
    """Build the destination: template_path mappings."""
    mappings = {}

    # Check for mutually exclusive flags
    flag_count = sum([args.pypi, args.kodi_addon, args.changelog_only])
    if flag_count > 1:
        raise ValueError("Flags --pypi, --kodi-addon, and --changelog-only are mutually exclusive")

    # Default to changelog-only if no flags
    if flag_count == 0:
        args.changelog_only = True

    # Get templates directory (default: "templates", can be configured)
    templates_dir = config.get("templates-dir", "templates")

    # Build default mappings based on flags or config
    if args.pypi or config.get("use-default-pypi-structure"):  # pragma: no cover
        # TODO: Add PyPI defaults
        pass

    if args.kodi_addon or config.get("use-default-kodi-addon-structure"):
        # For Kodi addons, place addon.xml.j2 in the addon's subdirectory within templates
        # Template directory structure mirrors output structure per PSR design
        kodi_project_name = config.get("kodi-project-name")
        if kodi_project_name:
            # e.g., templates/script.module.example/addon.xml.j2 -> script.module.example/addon.xml
            mappings[f"{templates_dir}/{kodi_project_name}/addon.xml.j2"] = "kodi-addons/addon.xml.j2"
        else:
            # Fallback to root templates if no project name
            mappings[f"{templates_dir}/addon.xml.j2"] = "kodi-addons/addon.xml.j2"

    if args.changelog_only or (flag_count == 0):
        mappings[f"{templates_dir}/CHANGELOG.md.j2"] = "universal/CHANGELOG.md.j2"

    # Track default destinations to prevent overriding
    default_destinations = set(mappings.keys())

    # Add custom mappings from config, but prevent overriding defaults
    for dest, template_path in config.get("source-mappings", {}).items():
        if dest in default_destinations:
            raise ValueError(f"Cannot override default mapping for {dest}")
        mappings[dest] = template_path

    return mappings


def arrange_templates(fixture_dir, mappings, override=True):
    """
    Place templates into the fixture directory.
    
    Args:
        fixture_dir: Path to the fixture directory
        mappings: Dict mapping destination paths to template paths
        override: Whether to overwrite existing files (default: True)
    """
    # Assume templates are in arranger.templates
    templates_package = "arranger.templates"
    for dest, template_path in mappings.items():
        template_file = importlib.resources.files(templates_package) / template_path
        content = template_file.read_text()
        # Place raw template content
        dst = fixture_dir / dest
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and not override:
            raise FileExistsError(f"File {dst} exists, use --override to overwrite")
        dst.write_text(content)
        print(f"Placed {template_path} to {dst}")


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
        "--override", action="store_true", help="Override existing files"
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
