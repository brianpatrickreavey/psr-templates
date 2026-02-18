"""Template copying and mapping."""

import logging
import shutil
from pathlib import Path

from .config import AddonConfig

logger = logging.getLogger(__name__)


def copy_universal_templates(source_dir: Path, target_dir: Path) -> None:
    """Copy universal templates from source to target.

    Args:
        source_dir: Source template directory (e.g., src/arranger/templates/universal)
        target_dir: Target directory (e.g., templates/)
    """
    universal_src = source_dir / "universal"

    if not universal_src.exists():
        logger.warning(f"Universal templates directory not found: {universal_src}")
        return

    target_dir.mkdir(parents=True, exist_ok=True)

    for item in universal_src.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(universal_src)
            target_file = target_dir / rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target_file)
            logger.info(f"Copied universal/{rel_path}")

    logger.info(f"Universal templates copied to {target_dir}")


def copy_addon_templates(
    source_dir: Path,
    target_dir: Path,
    addon_config: AddonConfig,
) -> None:
    """Copy addon templates from source to target, organized by addon_id.

    Also ensures addon.xml.j2 template includes news placeholder.

    Args:
        source_dir: Source template directory (e.g., src/arranger/templates)
        target_dir: Target directory (e.g., templates/)
        addon_config: Addon configuration with id
    """
    addon_src = source_dir / "kodi-addons"

    if not addon_src.exists():
        logger.warning(f"Addon templates directory not found: {addon_src}")
        return

    addon_id = addon_config.id
    addon_target = target_dir / addon_id
    addon_target.mkdir(parents=True, exist_ok=True)

    for item in addon_src.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(addon_src)
            target_file = addon_target / rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target_file)
            logger.info(f"Copied kodi-addons/{rel_path} → {addon_id}/{rel_path}")

    # Ensure addon.xml.j2 has news placeholder
    addon_xml_template = addon_target / "addon.xml.j2"
    if addon_xml_template.exists():
        ensure_news_placeholder(addon_xml_template)

    logger.info(f"Addon templates copied to {addon_target}")


def ensure_news_placeholder(addon_xml_template: Path) -> None:
    """Ensure addon.xml.j2 template includes news placeholder.

    If the template doesn't have <news>...</news> in the metadata extension,
    insert an empty news placeholder.

    Args:
        addon_xml_template: Path to addon.xml.j2 template
    """
    content = addon_xml_template.read_text()

    # Check if news placeholder already exists
    if "<news>" in content:
        logger.info("addon.xml.j2 already has news placeholder")
        return

    # Try to parse as XML-like to find insertion point
    # (templates have Jinja2 so we can't parse as pure XML)
    metadata_idx = content.find("</extension>")

    if metadata_idx != -1:
        # Insert before closing extension tag
        news_placeholder = "    <news>{{ news }}</news>\n  "
        new_content = content[:metadata_idx] + news_placeholder + content[metadata_idx:]
        addon_xml_template.write_text(new_content)
        logger.info("Added news placeholder to addon.xml.j2")
    else:
        logger.warning("Could not find insertion point for news placeholder in addon.xml.j2")
