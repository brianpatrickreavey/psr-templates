#!/usr/bin/env python3
"""
Arranger script: Build template structure from PSR templates.

Reads config from pyproject.toml [tool.arranger], places templates.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict
import tomllib
import importlib.resources
from importlib.resources import files
import sys

# Module constants (C3.6)
TEMPLATES_PACKAGE = "arranger.templates"
DEFAULT_TEMPLATES_DIR = "templates"
DEFAULT_CHANGELOG_DEST = "universal/CHANGELOG.md.j2"
DEFAULT_KODI_ADDON_DEST = "kodi-addons/addon.xml.j2"
VALID_CONFIG_KEYS = {
    "templates-dir",
    "use-default-pypi-structure",
    "use-default-kodi-addon-structure",
    "kodi-project-name",
    "source-mappings",
}


def load_config(pyproject_path: Path) -> Dict[str, Any]:
    """Load [tool.arranger] from pyproject.toml.
    
    Args:
        pyproject_path: Path to pyproject.toml file.
        
    Returns:
        Dictionary with arranger config, defaults included.
        
    Raises:
        FileNotFoundError: If pyproject_path does not exist.
        ValueError: If TOML is malformed.
    """
    if not pyproject_path.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {pyproject_path.absolute()}\n"
            "Please ensure you run this command from the project root directory."
        )
    
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(
            f"Invalid TOML syntax in {pyproject_path}: {str(e)}\n"
            "Please check the file for syntax errors."
        ) from e
    except Exception as e:
        raise ValueError(
            f"Failed to read {pyproject_path}: {str(e)}"
        ) from e
    
    config = data.get("tool", {}).get("arranger", {})
    # Set defaults
    config.setdefault("source-mappings", {})
    
    # Warn about unknown config keys (E1.6 - partial)
    unknown_keys = set(config.keys()) - VALID_CONFIG_KEYS
    if unknown_keys:
        print(f"Warning: Unknown keys in [tool.arranger]: {', '.join(sorted(unknown_keys))}", file=sys.stderr)
    
    return config


def build_mappings(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, str]:
    """Build the destination: template_path mappings.
    
    Args:
        config: Configuration dictionary from [tool.arranger].
        args: Parsed command-line arguments.
        
    Returns:
        Dictionary mapping destination paths to template source paths.
        
    Raises:
        ValueError: If flags are mutually exclusive or config is invalid.
    """
    mappings: Dict[str, str] = {}

    # Check for mutually exclusive flags
    flag_count = sum([args.pypi, args.kodi_addon, args.changelog_only])
    if flag_count > 1:
        raise ValueError("Flags --pypi, --kodi-addon, and --changelog-only are mutually exclusive")

    # Default to changelog-only if no flags
    if flag_count == 0:
        args.changelog_only = True

    # Get templates directory (default: "templates", can be configured)
    templates_dir = config.get("templates-dir", DEFAULT_TEMPLATES_DIR)

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
            mappings[f"{templates_dir}/{kodi_project_name}/addon.xml.j2"] = DEFAULT_KODI_ADDON_DEST
        else:
            # Fallback to root templates if no project name
            mappings[f"{templates_dir}/addon.xml.j2"] = DEFAULT_KODI_ADDON_DEST

    # Always include changelog in addition to other templates
    mappings[f"{templates_dir}/CHANGELOG.md.j2"] = DEFAULT_CHANGELOG_DEST

    # Track default destinations to prevent overriding
    default_destinations = set(mappings.keys())

    # Add custom mappings from config, but prevent overriding defaults
    for dest, template_path in config.get("source-mappings", {}).items():
        if dest in default_destinations:
            raise ValueError(f"Cannot override default mapping for {dest}")
        mappings[dest] = template_path

    return mappings


def arrange_templates(fixture_dir: Path, mappings: Dict[str, str], override: bool = True) -> None:
    """
    Place templates into the fixture directory.

    Args:
        fixture_dir: Path to the fixture directory
        mappings: Dict mapping destination paths to template paths
        override: Whether to overwrite existing files (default: True)
        
    Raises:
        FileNotFoundError: If template file cannot be found or read.
        PermissionError: If cannot write to destination directory.
        Exception: If template package cannot be imported.
    """
    try:
        templates = importlib.resources.files(TEMPLATES_PACKAGE)
    except (ModuleNotFoundError, ImportError) as e:
        raise RuntimeError(
            f"Failed to import template package '{TEMPLATES_PACKAGE}':\n"
            f"{str(e)}\n\n"
            "Please ensure 'psr-templates' is installed with:\n"
            "  pip install psr-templates\n"
            "or for development:\n"
            "  pip install -e ."
        ) from e
    
    for dest, template_path in mappings.items():
        try:
            # E1.1: Validate template file exists before reading
            template_file = templates / template_path
            try:
                content = template_file.read_text(encoding="utf-8")
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f"Template file not found: {template_path}\n"
                    f"Please ensure the template exists in the templates package.\n"
                    f"Available templates should be in: {TEMPLATES_PACKAGE}"
                ) from e
            except IsADirectoryError as e:
                raise ValueError(
                    f"Template path points to a directory, not a file: {template_path}"
                ) from e
            
            # Place raw template content
            dst = fixture_dir / dest
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise PermissionError(
                    f"Permission denied creating directory: {dst.parent}\n"
                    "Please check that you have write permissions in this directory."
                ) from e
            
            if dst.exists() and not override:
                raise FileExistsError(f"File {dst} exists, use --override to overwrite")
            
            try:
                dst.write_text(content, encoding="utf-8")
            except PermissionError as e:
                raise PermissionError(
                    f"Permission denied writing to: {dst}\n"
                    "Please check that you have write permissions in this directory."
                ) from e
            
            print(f"Placed {template_path} to {dst}")
        except (FileNotFoundError, PermissionError, ValueError, IsADirectoryError) as e:
            raise type(e)(str(e)) from e


def main() -> None:
    """Main entry point for the arranger CLI."""
    parser = argparse.ArgumentParser(
        description="Build template structure from PSR templates.",
        epilog="Example: psr-build-template-structure --kodi-addon"
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

    try:
        pyproject_path = Path("pyproject.toml")
        config = load_config(pyproject_path)
        mappings = build_mappings(config, args)
        arrange_templates(Path("."), mappings, override=args.override)
        print("✓ Template structure built successfully.")
    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except (PermissionError, RuntimeError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
