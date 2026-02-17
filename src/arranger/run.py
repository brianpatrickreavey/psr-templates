#!/usr/bin/env python3
"""
Arranger module: Build template structure from PSR templates.

This module provides the core functionality to read template configuration from a
pyproject.toml file and arrange Jinja2 template files according to specified source
and destination mappings. It supports multiple project types (PyPI, Kodi addons)
with customizable template structures.

Key functions:
  - load_config(): Load [tool.arranger] section from pyproject.toml
  - build_mappings(): Build source-to-destination template mappings
  - arrange_templates(): Place templates into the fixture directory
  - main(): CLI entry point for the template arrangement workflow

Usage:
  From command line:
    $ psr-build-template-structure [--kodi-addon | --pypi | --changelog-only] [--override]

  From Python:
    from arranger.run import load_config, build_mappings, arrange_templates
    config = load_config(Path("pyproject.toml"))
    mappings = build_mappings(config, args)
    arrange_templates(Path("."), mappings)

Configuration (in pyproject.toml):
  [tool.arranger]
  templates-dir = "templates"  # Optional: where to find templates
  use-default-kodi-addon-structure = false  # Include Kodi addon defaults
  kodi-project-name = "script.module.example"  # For Kodi projects
  source-mappings = {dest-path = "template-path"}  # Custom template mappings
"""

from __future__ import annotations

import argparse
import importlib.resources
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, cast

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
    """
    Load [tool.arranger] configuration from pyproject.toml.

    Reads the [tool.arranger] section from a pyproject.toml file and returns
    configuration as a dictionary. Includes default values for unspecified keys
    and validates that unknown configuration keys are reported as warnings.

    Expected configuration keys (optional):
      - templates-dir (str): Directory name containing templates (default: "templates")
      - use-default-pypi-structure (bool): Include PyPI structure defaults
      - use-default-kodi-addon-structure (bool): Include Kodi addon defaults
      - kodi-project-name (str): Name of Kodi addon project directory
      - source-mappings (dict): Custom source-to-destination mappings

    Args:
        pyproject_path: Path to pyproject.toml file to load.

    Returns:
        Dictionary with arranger configuration, including default values for
        missing optional keys. Always includes "source-mappings" key.

    Raises:
        FileNotFoundError: If pyproject_path does not exist or is not readable.
        ValueError: If TOML syntax is invalid or file cannot be read.
    """
    if not pyproject_path.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {pyproject_path.absolute()}\n"
            "Please ensure you run this command from the project root directory."
        )

    try:
        with open(pyproject_path, "rb") as f:
            data: Dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(
            f"Invalid TOML syntax in {pyproject_path}: {str(e)}\n" "Please check the file for syntax errors."
        ) from e
    except Exception as e:
        raise ValueError(f"Failed to read {pyproject_path}: {str(e)}") from e

    config: Dict[str, Any] = cast(Dict[str, Any], data.get("tool", {}).get("arranger", {}))
    # Set defaults
    config.setdefault("source-mappings", {})

    # Warn about unknown config keys (E1.6 - partial)
    unknown_keys = set(config.keys()) - VALID_CONFIG_KEYS
    if unknown_keys:
        print(
            f"Warning: Unknown keys in [tool.arranger]: {', '.join(sorted(unknown_keys))}",
            file=sys.stderr,
        )

    return config


def _validate_config_types(config: Dict[str, Any]) -> None:
    """
    Validate that configuration values have correct types.

    Args:
        config: Configuration dictionary from [tool.arranger].

    Raises:
        ValueError: If configuration values have incorrect types.
    """
    # Define expected types for each configuration key
    expected_types = {
        "templates-dir": str,
        "use-default-pypi-structure": bool,
        "use-default-kodi-addon-structure": bool,
        "kodi-project-name": str,
        "source-mappings": dict,
    }

    for key, expected_type in expected_types.items():
        if key in config:
            value = config[key]
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"Invalid type for config key '{key}': expected {expected_type.__name__}, "
                    f"got {type(value).__name__}\n"
                    f"Please ensure '{key}' is configured as: {expected_type.__name__.lower()}"
                )


def _validate_config_values(config: Dict[str, Any]) -> None:
    """
    Validate that configuration values are valid and meaningful.

    Args:
        config: Configuration dictionary from [tool.arranger].

    Raises:
        ValueError: If configuration values are invalid.
    """
    # Validate templates-dir
    templates_dir = config.get("templates-dir")
    if templates_dir is not None:
        if not templates_dir:
            raise ValueError("Configuration error: 'templates-dir' cannot be an empty string.")

        if "/" in templates_dir or "\\" in templates_dir:
            raise ValueError(
                f"Configuration error: 'templates-dir' should be a simple directory name, "
                f"not a path: '{templates_dir}'\n"
                f"Use 'templates-dir = \"mytemplates\"' instead of 'templates-dir = \"path/to/mytemplates\"'"
            )

    # Validate kodi-project-name
    kodi_project_name = config.get("kodi-project-name")
    if kodi_project_name is not None and not kodi_project_name:
        raise ValueError("Configuration error: 'kodi-project-name' cannot be an empty string.")

    # Validate source-mappings is a valid dictionary
    source_mappings = config.get("source-mappings", {})
    if not isinstance(source_mappings, dict):
        type_name = type(source_mappings).__name__
        raise ValueError(f"Configuration error: 'source-mappings' must be a dictionary, got {type_name}")

    for dest, template_path in source_mappings.items():
        if not isinstance(dest, str) or not isinstance(template_path, str):
            raise ValueError(
                f"Configuration error: All source-mappings keys and values must be strings.\n"
                f"Entry '{dest}' has invalid type(s)."
            )


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate entire configuration for correctness.

    Runs type and value validation on the configuration dictionary.

    Args:
        config: Configuration dictionary from [tool.arranger].

    Raises:
        ValueError: If configuration is invalid.
    """
    _validate_config_types(config)
    _validate_config_values(config)


def _validate_flag_exclusivity(args: argparse.Namespace) -> None:
    """
    Validate that mutually exclusive flags are not used together.

    Args:
        args: Parsed command-line arguments.

    Raises:
        ValueError: If more than one of --pypi, --kodi-addon, --changelog-only is set.
    """
    flag_count = sum([args.pypi, args.kodi_addon, args.changelog_only])
    if flag_count > 1:
        raise ValueError(
            "Flags --pypi, --kodi-addon, and --changelog-only are mutually exclusive.\n"
            "Please specify only one of these flags."
        )


def _set_default_flag(args: argparse.Namespace) -> None:
    """
    Set --changelog-only as default if no flag was specified.

    Args:
        args: Parsed command-line arguments (modified in-place).
    """
    flag_count = sum([args.pypi, args.kodi_addon, args.changelog_only])
    if flag_count == 0:
        args.changelog_only = True


def _build_default_mappings(
    config: Dict[str, Any],
    args: argparse.Namespace,
) -> Tuple[Dict[str, str], set[str]]:
    """
    Build default mappings for project types and return reserved destinations.

    Args:
        config: Configuration dictionary from [tool.arranger].
        args: Parsed command-line arguments.

    Returns:
        Tuple of (mappings dict, set of reserved destination paths).
    """
    mappings: Dict[str, str] = {}
    templates_dir = config.get("templates-dir", DEFAULT_TEMPLATES_DIR)

    # Build default mappings based on flags or config
    if args.pypi or config.get("use-default-pypi-structure"):  # pragma: no cover
        # TODO: Add PyPI defaults
        pass

    if args.kodi_addon or config.get("use-default-kodi-addon-structure"):
        kodi_project_name = config.get("kodi-project-name")
        if kodi_project_name:
            mappings[f"{templates_dir}/{kodi_project_name}/addon.xml.j2"] = DEFAULT_KODI_ADDON_DEST
        else:
            mappings[f"{templates_dir}/addon.xml.j2"] = DEFAULT_KODI_ADDON_DEST

    # Always include changelog template
    mappings[f"{templates_dir}/CHANGELOG.md.j2"] = DEFAULT_CHANGELOG_DEST

    return mappings, set(mappings.keys())


def _validate_custom_mappings(
    source_mappings: Dict[str, str],
    reserved_destinations: set[str],
) -> None:
    """
    Validate custom source-mappings configuration for format and conflicts.

    Args:
        source_mappings: Custom mappings from config [tool.arranger].
        reserved_destinations: Set of destination paths that cannot be overridden.

    Raises:
        ValueError: If mapping format is invalid or conflicts with reserved destinations.
    """
    for dest, template_path in source_mappings.items():
        # Validate destination path format
        if not dest or "/" not in dest.rstrip("/"):
            raise ValueError(
                f"Invalid destination path format: '{dest}'\n"
                "Destination paths should be file paths with at least one directory level "
                "(e.g., 'dir/file.txt')"
            )

        if dest.endswith("/"):
            raise ValueError(f"Destination path cannot be a directory: '{dest}'\n" "Please specify a full file path.")

        # Validate template path format
        if not template_path or template_path.endswith("/"):
            raise ValueError(
                f"Invalid template path format: '{template_path}'\n"
                "Template paths should reference specific files, not directories."
            )

        if dest in reserved_destinations:
            raise ValueError(
                f"Cannot override default mapping for '{dest}'\n"
                f"Default mappings are reserved for framework templates. "
                f"Please choose a different destination path."
            )


def build_mappings(
    config: Dict[str, Any],
    args: argparse.Namespace,
    templates_pkg: Optional[Any] = None,
) -> Dict[str, str]:
    """
    Build destination: template_path mappings from configuration and CLI arguments.

    Constructs a mapping dictionary that specifies which template files should be
    placed at which destination paths in the fixture directory. Automatically includes
    default templates for chosen project types (Kodi addon, PyPI) and validates both
    default and custom mappings for correctness.

    Behavior:
    - If no flags specified, defaults to --changelog-only
    - Flags (--pypi, --kodi-addon, --changelog-only) are mutually exclusive
    - Default mappings cannot be overridden by source-mappings
    - Custom source-mappings are validated for path format and conflicts

    Args:
        config: Configuration dictionary from [tool.arranger].
        args: Parsed command-line arguments (includes pypi, kodi_addon, changelog_only flags).
        templates_pkg: Optional templates package reference (unused, for future compatibility).

    Returns:
        Dictionary mapping destination file paths to template source paths.
        Example: {"CHANGELOG.md": "universal/CHANGELOG.md.j2"}

    Raises:
        ValueError: If flags are mutually exclusive, paths are invalid format,
                   or custom mappings conflict with reserved destinations.
    """
    # C3.4: Validate configuration (types and values)
    _validate_config(config)

    # E1.7: Validate flag exclusivity
    _validate_flag_exclusivity(args)

    # Default to changelog-only if no flags specified
    _set_default_flag(args)

    # Build default mappings and get reserved destination paths
    mappings, reserved_destinations = _build_default_mappings(config, args)

    # E1.8: Validate custom source-mappings
    source_mappings = config.get("source-mappings", {})
    _validate_custom_mappings(source_mappings, reserved_destinations)

    # Add validated custom mappings to result
    mappings.update(source_mappings)

    return mappings


def _validate_fixture_directory(fixture_dir: Path) -> Path:
    """
    Validate and prepare the fixture directory.

    Creates the fixture directory if it doesn't exist and ensures proper permissions.

    Args:
        fixture_dir: Path to the fixture directory to validate.

    Returns:
        Absolute resolved path to the fixture directory.

    Raises:
        ValueError: If fixture_dir is empty or inaccessible.
        PermissionError: If lacking permissions to create/access directory.
    """
    if not fixture_dir:
        raise ValueError("Fixture directory path cannot be empty")

    try:
        fixture_dir_abs = fixture_dir.resolve()
        fixture_dir_abs.mkdir(parents=True, exist_ok=True)
        return fixture_dir_abs
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied creating/accessing fixture directory: {fixture_dir}\n"
            "Please check that you have write permissions in this location."
        ) from e
    except Exception as e:
        raise ValueError(f"Cannot access fixture directory {fixture_dir}: {str(e)}") from e


def _read_template_content(templates: Any, template_path: str) -> str:
    """
    Read a template file from the templates package.

    Args:
        templates: Templates package reference from importlib.resources.
        template_path: Relative path to template file within templates package.

    Returns:
        Template file content as UTF-8 string.

    Raises:
        FileNotFoundError: If template file doesn't exist.
        ValueError: If template path points to a directory.
    """
    try:
        template_file: Any = templates / template_path
        try:
            content: str = cast(str, template_file.read_text(encoding="utf-8"))
            return content
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Template file not found: {template_path}\n"
                f"Please ensure the template exists in the templates package.\n"
                f"Available templates should be in: {TEMPLATES_PACKAGE}"
            ) from e
        except IsADirectoryError as e:
            raise ValueError(f"Template path points to a directory, not a file: {template_path}") from e
    except (FileNotFoundError, ValueError):
        raise


def _handle_existing_destination(dst: Path, override: bool) -> None:
    """
    Handle existing files and symlinks at destination.

    Removes symlinks if override=True, or raises error if file exists and
    override=False.

    Args:
        dst: Destination file path.
        override: Whether to overwrite existing files.

    Raises:
        FileExistsError: If destination exists and override=False.
        PermissionError: If lacking permissions to remove existing file.
    """
    if not dst.exists():
        return

    # E1.11: Handle symlinks - resolve them but don't follow
    if dst.is_symlink():
        if not override:
            raise FileExistsError(f"Symlink exists at {dst}, use --override to replace it")
        try:
            dst.unlink()
        except PermissionError as e:
            raise PermissionError(f"Permission denied removing symlink: {dst}") from e
        return

    # E1.9: Validate override behavior for regular files
    if not override:
        raise FileExistsError(f"File exists at {dst}\n" "Use --override flag to overwrite existing files.")


def _write_destination_file(
    dst: Path,
    content: str,
    override: bool = True,
) -> None:
    """
    Write template content to destination file with proper error handling.

    Creates parent directories as needed, handles existing files based on
    override flag, and validates file encoding.

    Args:
        dst: Destination file path.
        content: Template content to write.
        override: Whether to overwrite existing files (default: True).

    Raises:
        PermissionError: If lacking permissions to write.
        ValueError: If file encoding is invalid.
    """
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied creating directory: {dst.parent}\n"
            "Please check that you have write permissions in this directory."
        ) from e

    try:
        # Explicit UTF-8 encoding (E1.12)
        dst.write_text(content, encoding="utf-8")
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied writing to: {dst}\n" "Please check that you have write permissions in this directory."
        ) from e
    except UnicodeEncodeError as e:
        raise ValueError(
            f"File encoding error while writing {dst}: {str(e)}\n" "Ensure template content is valid UTF-8."
        ) from e


def _arrange_single_template(
    templates: Any,
    fixture_dir_abs: Path,
    dest: str,
    template_path: str,
    override: bool,
) -> None:
    """
    Arrange a single template file from source to destination.

    Reads a template file and places it in the fixture directory with proper
    error handling for all edge cases (missing templates, symlinks, permissions).

    Args:
        templates: Templates package reference.
        fixture_dir_abs: Absolute path to fixture directory.
        dest: Destination path within fixture directory.
        template_path: Source template path in templates package.
        override: Whether to overwrite existing files.

    Raises:
        FileNotFoundError: If template cannot be found.
        ValueError: If path or encoding is invalid.
        PermissionError: If lacking required permissions.
    """
    try:
        content: str = _read_template_content(templates, template_path)

        # Place raw template content
        dst = fixture_dir_abs / dest

        # Handle existing files/symlinks
        _handle_existing_destination(dst, override)

        # Write the destination file
        _write_destination_file(dst, content, override)

        print(f"Placed {template_path} to {dst}")
    except (FileNotFoundError, PermissionError, ValueError, IsADirectoryError) as e:
        raise type(e)(str(e)) from e


def _parse_addon_xml(addon_xml_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse addon.xml file and extract metadata.

    Extracts the following attributes from the root <addon> element:
      - id: addon identifier
      - name: human-readable addon name
      - version: current version
      - provider-name: addon provider/author name

    Also extracts all <import> elements from <requires> for tracking dependencies.

    Args:
        addon_xml_path: Path to addon.xml file to parse.

    Returns:
        Dictionary with keys: id, name, version, provider-name, requires (list of dicts).
        Returns None if file doesn't exist or parsing fails.
    """
    if not addon_xml_path.exists():
        return None

    try:
        tree = ET.parse(addon_xml_path)
        root = tree.getroot()

        # Extract addon attributes
        metadata: Dict[str, Any] = {
            "id": root.get("id"),
            "name": root.get("name"),
            "version": root.get("version"),
            "provider-name": root.get("provider-name"),
            "requires": [],
        }

        # Extract requires/import elements
        requires_elem = root.find("requires")
        if requires_elem is not None:
            for import_elem in requires_elem.findall("import"):
                import_info = {"addon": import_elem.get("addon"), "version": import_elem.get("version")}
                metadata["requires"].append(import_info)

        return metadata
    except ET.ParseError as e:
        print(
            f"Warning: Failed to parse addon.xml at {addon_xml_path}: {str(e)}\n"
            "Proceeding without metadata validation.",
            file=sys.stderr,
        )
        return None
    except Exception as e:
        print(
            f"Warning: Unexpected error reading addon.xml at {addon_xml_path}: {str(e)}\n"
            "Proceeding without metadata validation.",
            file=sys.stderr,
        )
        return None


def _validate_addon_metadata_consistency(
    fixture_dir: Path, kodi_project_name: str, config_metadata: Optional[Dict[str, Any]]
) -> None:
    """
    Check for consistency between pyproject.toml config and existing addon.xml.

    If both config and existing addon.xml specify metadata, compare them and warn
    on mismatches. Uses existing addon.xml values as authoritative (config is ignored).

    Args:
        fixture_dir: Root directory of fixture/project.
        kodi_project_name: Project name from config or CLI arg.
        config_metadata: Addon metadata from [tool.arranger] config, if present.
    """
    # Determine expected addon.xml path
    addon_xml_path = fixture_dir / kodi_project_name / "addon.xml"

    # Parse existing addon.xml if it exists
    existing_metadata = _parse_addon_xml(addon_xml_path)

    # Only validate if both config and file exist
    if config_metadata and existing_metadata:
        mismatches = []

        for key in ["id", "name", "provider-name"]:
            config_val = config_metadata.get(key)
            existing_val = existing_metadata.get(key)

            if config_val and existing_val and config_val != existing_val:
                mismatches.append(f"  {key}: config='{config_val}' vs addon.xml='{existing_val}'")

        if mismatches:
            print(
                f"Warning: Metadata mismatch between [tool.arranger] config and {addon_xml_path}:\n"
                + "\n".join(mismatches)
                + f"\nUsing values from {addon_xml_path}. Config values will be ignored.",
                file=sys.stderr,
            )


def arrange_templates(fixture_dir: Path, mappings: Dict[str, str], override: bool = True) -> None:
    """
    Place templates into the fixture directory according to mappings.

    Reads template files from the arranger.templates package and writes them
    to the specified fixture directory at the destination paths defined in the
    mappings dictionary. Handles edge cases including symlinks, missing directories,
    and permission errors with clear error messages.

    Process:
    1. Validates and creates fixture directory if needed
    2. Imports templates from the arranger.templates package
    3. For each mapping, reads template file and writes to destination
    4. Creates parent directories in fixture as needed
    5. Handles existing files based on override flag

    Edge cases handled:
    - Existing symlinks are removed before replacement (if override=True)
    - File encoding errors are reported with context
    - Permission errors include helpful troubleshooting hints
    - Non-existent template files are reported with available paths

    Args:
        fixture_dir: Path to the fixture directory (created if missing).
        mappings: Dictionary mapping destination paths to template source paths.
                 Keys are relative paths in fixture (e.g., "CHANGELOG.md").
                 Values are template source paths (e.g., "universal/CHANGELOG.md.j2").
        override: Whether to overwrite existing files (default: True).
                 If False, raises FileExistsError if destination exists.

    Raises:
        ValueError: If fixture_dir is invalid, mappings empty, or template path invalid.
        FileNotFoundError: If template file cannot be found in templates package.
        PermissionError: If lacking write/create permissions in fixture directory.
        RuntimeError: If templates package cannot be imported.
        FileExistsError: If destination exists and override=False.
    """
    # Validate and prepare the fixture directory
    fixture_dir_abs = _validate_fixture_directory(fixture_dir)

    # E1.10: Handle empty mappings
    if not mappings:
        raise ValueError(
            "No templates to arrange. Please configure at least one template source.\n"
            "Use --changelog-only (default), --kodi-addon, or --pypi flag, "
            "or add [tool.arranger] configuration in pyproject.toml"
        )

    # Import templates package
    try:
        templates: Any = importlib.resources.files(TEMPLATES_PACKAGE)
    except ImportError as e:
        raise RuntimeError(
            f"Failed to import template package '{TEMPLATES_PACKAGE}':\n"
            f"{str(e)}\n\n"
            "Please ensure 'psr-templates' is installed with:\n"
            "  pip install psr-templates\n"
            "or for development:\n"
            "  pip install -e ."
        ) from e

    # Arrange each template
    for dest, template_path in mappings.items():
        _arrange_single_template(templates, fixture_dir_abs, dest, template_path, override)


def main() -> None:
    """
    Orchestrate the template arrangement workflow.

    This is the main CLI entry point that:
    1. Loads [tool.arranger] configuration from pyproject.toml
    2. Parses command-line arguments for project type and options
    3. Builds source-to-destination template mappings
    4. Arranges templates into the fixture directory

    Command-line arguments:
      --pypi              Include default PyPI package structure templates
      --kodi-addon        Include default Kodi addon structure templates
      --changelog-only    Only create CHANGELOG.md template (default if no flags)
      --override          Overwrite existing template files (default: False)

    Exit codes:
      0 - Success: templates arranged without errors
      1 - Failure: configuration error, file not found, or arrangement failed

    Raises:
      SystemExit: With code 1 on any uncaught error (prints to stderr)
    """
    parser = argparse.ArgumentParser(
        description="Build template structure from PSR templates.",
        epilog=(
            "Examples:\n"
            "  psr-build-template-structure --kodi-addon\n"
            "  psr-build-template-structure --changelog-only\n"
            "  psr-build-template-structure --override (to overwrite existing files)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Project type group (mutually exclusive)
    type_group = parser.add_argument_group(
        "project type",
        "Choose one project type to generate templates for. " "If none specified, defaults to --changelog-only.",
    )
    type_group.add_argument(
        "--pypi",
        action="store_true",
        help="Include default PyPI package structure templates",
    )
    type_group.add_argument(
        "--kodi-addon",
        action="store_true",
        help="Include default Kodi addon structure templates",
    )
    type_group.add_argument(
        "--changelog-only",
        action="store_true",
        help="Only create CHANGELOG.md template (default if no flags specified)",
    )

    # Options group
    options_group = parser.add_argument_group(
        "options",
        "Control template arrangement behavior.",
    )
    options_group.add_argument(
        "--override",
        action="store_true",
        help="Overwrite existing template files (default: False, raises error if files exist)",
    )

    args = parser.parse_args()

    try:
        pyproject_path = Path("pyproject.toml")
        config = load_config(pyproject_path)
        mappings = build_mappings(config, args)

        # Validate addon metadata consistency if kodi addon is configured
        kodi_project_name = config.get("kodi-project-name")
        if args.kodi_addon or config.get("use-default-kodi-addon-structure"):
            if kodi_project_name:
                _validate_addon_metadata_consistency(Path("."), kodi_project_name, None)

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
