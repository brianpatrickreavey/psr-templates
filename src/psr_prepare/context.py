"""Context JSON generation for PSR rendering."""

import json
import logging
from pathlib import Path
from typing import Optional

from .config import ChangelogConfig

logger = logging.getLogger(__name__)


def write_addon_context(
    context_dir: Path,
    addon_data: dict[str, str],
    news_types: Optional[dict[str, str]] = None,
) -> None:
    """Write addon context to .psr_context/addon.json.

    Args:
        context_dir: Path to .psr_context directory
        addon_data: Reconciled addon data (from reconcile_addon)
        news_types: News type mappings from changelog config (commit_type → label)
    """
    context_dir.mkdir(parents=True, exist_ok=True)

    addon_json = context_dir / "addon.json"

    # Build context with sensible defaults
    context = {
        "id": addon_data.get("id", ""),
        "name": addon_data.get("name"),
        "provider-name": addon_data.get("provider-name"),
        "summary": addon_data.get("summary"),
        "description": addon_data.get("description"),
        "disclaimer": addon_data.get("disclaimer"),
        "license": addon_data.get("license"),
        "source": addon_data.get("source"),
        "assets": addon_data.get("assets", {}),
        "requires": addon_data.get("requires", []),
        "news": addon_data.get("news", ""),
        "news_types": news_types or {},
        "unknown_extensions": addon_data.get("unknown_extensions", ""),
    }

    with open(addon_json, "w") as f:
        json.dump(context, f, indent=2)

    logger.info(f"Wrote addon context to {addon_json}")


def write_changelog_context(
    context_dir: Path,
    config: ChangelogConfig,
    changelog_exists: bool,
) -> None:
    """Write changelog context to .psr_context/changelog.json.

    Args:
        context_dir: Path to .psr_context directory
        config: Changelog configuration
        changelog_exists: Whether CHANGELOG.md currently exists
    """
    context_dir.mkdir(parents=True, exist_ok=True)

    changelog_json = context_dir / "changelog.json"

    context = {
        "file": config.file,
        "mode": config.mode if changelog_exists else "init",
        "existing": changelog_exists,
    }

    with open(changelog_json, "w") as f:
        json.dump(context, f, indent=2)

    logger.info(f"Wrote changelog context to {changelog_json}")
