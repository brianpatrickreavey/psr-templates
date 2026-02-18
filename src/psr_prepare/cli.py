"""Command-line interface for psr_prepare."""

import argparse
import logging
import sys
from pathlib import Path

from .addon import parse_addon_xml, reconcile_addon
from .config import load_config
from .context import write_addon_context, write_changelog_context
from .templating import copy_addon_templates, copy_universal_templates

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False, quiet: bool = False) -> None:
    """Set up logging configuration.

    Args:
        debug: Enable debug-level logging
        quiet: Suppress info-level logging
    """
    if quiet:
        level = logging.WARNING
    elif debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def main() -> int:
    """Main entry point for psr_prepare CLI.

    Returns:
        Exit code (0=success, 1=config error, 2=parse error, 3=reconciliation error)
    """
    parser = argparse.ArgumentParser(
        description="Prepare templates and configuration for PSR (Python Semantic Release)",
        epilog="""
Examples:
  psr-prepare                    # Standard run with defaults
  psr-prepare --strict           # Strict mode (fail on conflicts)
  psr-prepare --config ./custom-config.toml
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path("pyproject.toml"),
        help="Path to pyproject.toml config file (default: pyproject.toml)",
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="Strict mode: fail on conflicts instead of warning",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress info-level logging (warnings and errors only)",
    )

    args = parser.parse_args()

    setup_logging(debug=args.debug, quiet=args.quiet)

    logger.info("Starting psr_prepare")

    try:
        # 1. Load configuration
        config = load_config(args.config)

        # 2. Determine directories
        project_root = args.config.parent if args.config.is_absolute() else Path.cwd()
        templates_dir = project_root / "templates"
        context_dir = project_root / ".psr_context"
        source_templates_dir = Path(__file__).parent.parent.parent / "src" / "arranger" / "templates"

        logger.info(f"Project root: {project_root}")
        logger.info(f"Source templates: {source_templates_dir}")
        logger.info(f"Target templates: {templates_dir}")
        logger.info(f"Context directory: {context_dir}")

        if args.dry_run:
            logger.info("DRY RUN MODE - no changes will be made")

        # 3. Parse addon.xml if config asks for it
        addon_xml_data = None
        addon_merged: dict = {}  # type: ignore[assignment]
        warnings: list[str] = []

        if config.addon:
            addon_xml_path = project_root / config.addon.id / "addon.xml"
            if addon_xml_path.exists():
                try:
                    addon_xml_data = parse_addon_xml(addon_xml_path)
                    logger.debug(f"Parsed addon.xml from {addon_xml_path}")
                except Exception as e:
                    logger.error(f"Failed to parse addon.xml: {e}")
                    return 2
            else:
                logger.info(f"addon.xml not found (OK for new projects): {addon_xml_path}")

            # 4. Reconcile addon config
            try:
                addon_merged, addon_warnings = reconcile_addon(
                    addon_xml_data, config.addon, strict=args.strict
                )
                warnings.extend(addon_warnings)
            except ValueError as e:
                logger.error(f"Reconciliation error: {e}")
                return 3

        # 5. Write context JSON
        if config.addon:
            # Pass news_types from changelog config to addon context
            news_types = config.changelog.news_types if config.changelog else None
            if args.dry_run:
                logger.info(f"[DRY RUN] Would write addon.json to {context_dir / 'addon.json'}")
            else:
                write_addon_context(context_dir, addon_merged, news_types=news_types)
                logger.info(f"Wrote addon context to {context_dir / 'addon.json'}")

        if config.changelog:
            changelog_exists = (project_root / config.changelog.file).exists()
            if args.dry_run:
                logger.info(f"[DRY RUN] Would write changelog.json to {context_dir / 'changelog.json'}")
            else:
                write_changelog_context(context_dir, config.changelog, changelog_exists)
                logger.info(f"Wrote changelog context to {context_dir / 'changelog.json'}")

        # 6. Copy templates
        if args.dry_run:
            logger.info(f"[DRY RUN] Would copy universal templates to {templates_dir}")
        else:
            copy_universal_templates(source_templates_dir, templates_dir)
            logger.info(f"Universal templates copied to {templates_dir}")

        if config.addon:
            if args.dry_run:
                logger.info(f"[DRY RUN] Would copy addon templates to {templates_dir / config.addon.id}")
            else:
                copy_addon_templates(source_templates_dir, templates_dir, config.addon)
                logger.info(f"Addon templates copied to {templates_dir / config.addon.id}")

        # 7. Report warnings if any
        if warnings:
            logger.warning("Reconciliation warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")

        if args.dry_run:
            logger.info("✓ psr_prepare dry run completed (no changes made)")
        else:
            logger.info("✓ psr_prepare completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.debug("Check that pyproject.toml exists and paths are correct", exc_info=True)
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.debug("Check pyproject.toml configuration syntax and required fields", exc_info=True)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug("Full error details:", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
