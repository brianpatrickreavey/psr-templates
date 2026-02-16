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


def build_mappings(config: Dict[str, Any], args: argparse.Namespace, templates_pkg: Any = None) -> Dict[str, str]:
    """Build the destination: template_path mappings.
    
    Args:
        config: Configuration dictionary from [tool.arranger].
        args: Parsed command-line arguments.
        templates_pkg: Optional templates package reference (for validation).
        
    Returns:
        Dictionary mapping destination paths to template source paths.
        
    Raises:
        ValueError: If flags are mutually exclusive or config is invalid.
    """
    mappings: Dict[str, str] = {}

    # E1.7: Check for mutually exclusive flags with clear error messages
    flag_count = sum([args.pypi, args.kodi_addon, args.changelog_only])
    if flag_count > 1:
        raise ValueError(
            "Flags --pypi, --kodi-addon, and --changelog-only are mutually exclusive.\n"
            "Please specify only one of these flags."
        )

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

    # E1.8: Validate source-mappings paths before using them
    source_mappings = config.get("source-mappings", {})
    for dest, template_path in source_mappings.items():
        # Validate destination path format
        if not dest or "/" not in dest.rstrip("/"):
            raise ValueError(
                f"Invalid destination path format: '{dest}'\n"
                "Destination paths should be file paths with at least one directory level (e.g., 'dir/file.txt')"
            )
        
        if dest.endswith("/"):
            raise ValueError(
                f"Destination path cannot be a directory: '{dest}'\n"
                "Please specify a full file path."
            )
        
        # Validate template path format
        if not template_path or template_path.endswith("/"):
            raise ValueError(
                f"Invalid template path format: '{template_path}'\n"
                "Template paths should reference specific files, not directories."
            )
        
        if dest in default_destinations:
            raise ValueError(
                f"Cannot override default mapping for '{dest}'\n"
                f"Default mappings are reserved for framework templates. "
                f"Please choose a different destination path."
            )
        
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
        ValueError: If fixture directory is invalid or mappings are empty.
        RuntimeError: If template package cannot be imported.
    """
    # E1.7: Validate fixture directory
    if not fixture_dir:
        raise ValueError("Fixture directory path cannot be empty")
    
    try:
        fixture_dir_abs = fixture_dir.resolve()
        fixture_dir_abs.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied creating/accessing fixture directory: {fixture_dir}\n"
            "Please check that you have write permissions in this location."
        ) from e
    except Exception as e:
        raise ValueError(
            f"Cannot access fixture directory {fixture_dir}: {str(e)}"
        ) from e
    
    # E1.10: Handle empty mappings
    if not mappings:
        raise ValueError(
            "No templates to arrange. Please configure at least one template source.\n"
            "Use --changelog-only (default), --kodi-addon, or --pypi flag, "
            "or add [tool.arranger] configuration in pyproject.toml"
        )
    
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
            # Validate template file exists before reading
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
            dst = fixture_dir_abs / dest
            
            # E1.11: Handle symlinks - resolve them but don't follow
            if dst.exists() and dst.is_symlink():
                if not override:
                    raise FileExistsError(
                        f"Symlink exists at {dst}, use --override to replace it"
                    )
                try:
                    dst.unlink()
                except PermissionError as e:
                    raise PermissionError(
                        f"Permission denied removing symlink: {dst}"
                    ) from e
            
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise PermissionError(
                    f"Permission denied creating directory: {dst.parent}\n"
                    "Please check that you have write permissions in this directory."
                ) from e
            
            # E1.9: Validate override behavior
            if dst.exists() and not override:
                raise FileExistsError(
                    f"File exists at {dst}\n"
                    "Use --override flag to overwrite existing files."
                )
            
            try:
                # Explicit UTF-8 encoding (E1.12)
                dst.write_text(content, encoding="utf-8")
            except PermissionError as e:
                raise PermissionError(
                    f"Permission denied writing to: {dst}\n"
                    "Please check that you have write permissions in this directory."
                ) from e
            except UnicodeEncodeError as e:
                raise ValueError(
                    f"File encoding error while writing {dst}: {str(e)}\n"
                    "Ensure template content is valid UTF-8."
                ) from e
            
            print(f"Placed {template_path} to {dst}")
        except (FileNotFoundError, PermissionError, ValueError, IsADirectoryError) as e:
            raise type(e)(str(e)) from e


def main() -> None:
    """Main entry point for the arranger CLI."""
    parser = argparse.ArgumentParser(
        description="Build template structure from PSR templates.",
        epilog=(
            "Examples:\n"
            "  psr-build-template-structure --kodi-addon\n"
            "  psr-build-template-structure --changelog-only\n"
            "  psr-build-template-structure --override (to overwrite existing files)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
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
        "--override", action="store_true", help="Override existing files (default: False)"
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
    except FileExistsError as e:
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
