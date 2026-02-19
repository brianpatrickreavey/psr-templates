"""Context generation for PSR rendering."""

import logging
from pathlib import Path
from typing import Optional

from .config import ChangelogConfig

logger = logging.getLogger(__name__)


def _python_to_jinja(obj: object, indent: int = 0) -> str:
    """Convert Python object to Jinja2-compatible representation.

    Handles strings, numbers, booleans, lists, and dicts for safe Jinja2 inclusion.
    """
    ind = " " * indent
    next_ind = " " * (indent + 2)

    if obj is None:
        return "none"
    elif isinstance(obj, bool):
        return "true" if obj else "false"
    elif isinstance(obj, (int, float)):
        return str(obj)
    elif isinstance(obj, str):
        # Escape quotes and newlines for Jinja2 string literals
        escaped = obj.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    elif isinstance(obj, list):
        if not obj:
            return "[]"
        items = [_python_to_jinja(item, indent + 2) for item in obj]
        return f"[\n{next_ind}" + f",\n{next_ind}".join(items) + f"\n{ind}]"
    elif isinstance(obj, dict):
        if not obj:
            return "{}"
        pairs = []
        for key, value in obj.items():
            val_str = _python_to_jinja(value, indent + 2)
            pairs.append(f'"{key}": {val_str}')
        return f"{{\n{next_ind}" + f",\n{next_ind}".join(pairs) + f"\n{ind}}}"
    else:
        return str(obj)


def write_addon_context(
    addon_data: dict[str, str],
    news_types: Optional[dict[str, str]] = None,
    universal_templates_dir: Optional[Path] = None,
    addon_templates_dir: Optional[Path] = None,
) -> None:
    """Write addon context to .psr-context.j2 files in template directories.

    Generates Jinja2 variable definitions and writes to both universal and addon
    template directories so PSR can include them when rendering.

    Args:
        addon_data: Reconciled addon data (from reconcile_addon)
        news_types: News type mappings from changelog config (commit_type → label)
        universal_templates_dir: Path to universal templates directory (e.g., templates/)
        addon_templates_dir: Path to addon templates directory (e.g., templates/<addon_id>/)
    """
    # Build context with sensible defaults
    context = {
        "id": addon_data.get("id", ""),
        "name": addon_data.get("name"),
        "provider_name": addon_data.get("provider-name"),  # Convert to snake_case
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

    # Generate Jinja2 variable definition
    jinja_context_str = _python_to_jinja(context)
    context_content = f"{{% set addon = {jinja_context_str} %}}\n"

    # Write to universal templates directory if provided
    if universal_templates_dir:
        universal_templates_dir.mkdir(parents=True, exist_ok=True)
        universal_context = universal_templates_dir / ".psr-context.j2"
        universal_context.write_text(context_content, encoding="utf-8")
        logger.info(f"Wrote addon context to {universal_context}")

    # Write to addon templates directory if provided
    if addon_templates_dir:
        addon_templates_dir.mkdir(parents=True, exist_ok=True)
        addon_context = addon_templates_dir / ".psr-context.j2"
        addon_context.write_text(context_content, encoding="utf-8")
        logger.info(f"Wrote addon context to {addon_context}")


def generate_context_injection(
    addon_data: Optional[dict[str, str]] = None,
    news_types: Optional[dict[str, str]] = None,
) -> str:
    r"""Generate Jinja2 context injection string for templates.

    Creates a string containing {% set %} statements that define context variables
    at the top of templates. This makes context available to the entire template.

    Args:
        addon_data: Addon metadata to inject (from reconcile_addon)
        news_types: News type mappings from changelog config

    Returns:
        String containing Jinja2 set statements (e.g., "{% set addon = {...} %}\n")
        Returns empty string if no addon_data provided.
    """
    if not addon_data:
        return ""

    # Build context with sensible defaults
    context = {
        "id": addon_data.get("id", ""),
        "name": addon_data.get("name"),
        "provider_name": addon_data.get("provider-name"),
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

    # Generate Jinja2 variable definition
    jinja_context_str = _python_to_jinja(context)
    return f"{{% set addon = {jinja_context_str} %}}\n"


def write_changelog_context(
    config: ChangelogConfig,
    changelog_exists: bool,
) -> None:
    """Write changelog context (currently unused, kept for compatibility).

    Args:
        config: Changelog configuration
        changelog_exists: Whether CHANGELOG.md currently exists
    """
    # Changelog context is now handled by PSR's built-in variables
    # This function is kept for backwards compatibility
    logger.debug("Changelog context is provided by PSR's built-in variables")
