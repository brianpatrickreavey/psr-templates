"""Addon.xml parsing and reconciliation."""

import logging
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

from .config import AddonConfig

logger = logging.getLogger(__name__)


class AddonXmlData:
    """Parsed data from addon.xml."""

    def __init__(self) -> None:
        """Initialize empty addon.xml data."""
        self.id: Optional[str] = None
        self.version: Optional[str] = None
        self.name: Optional[str] = None
        self.provider_name: Optional[str] = None
        self.summary: Optional[str] = None
        self.description: Optional[str] = None
        self.disclaimer: Optional[str] = None
        self.license: Optional[str] = None
        self.source: Optional[str] = None
        self.assets: dict[str, str] = {}
        self.requires: list[dict[str, str]] = []
        self.news: Optional[str] = None
        self.root: Optional[ET.Element] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "provider-name": self.provider_name,
            "summary": self.summary,
            "description": self.description,
            "disclaimer": self.disclaimer,
            "license": self.license,
            "source": self.source,
            "assets": self.assets,
            "requires": self.requires,
            "news": self.news,
        }

    def get_unknown_extensions_xml(self) -> str:
        """Extract unknown (non-metadata) extensions as XML strings.

        Returns:
            Concatenated XML strings of unknown extensions, or empty string if none.
        """
        if not self.root:
            return ""

        unknown_extensions = []
        for ext in self.root.findall("extension"):
            point = ext.get("point")
            # Skip the metadata extension (it's handled by template)
            if point and point != "xbmc.addon.metadata":
                # Serialize this extension element as XML
                xml_str = ET.tostring(ext, encoding="unicode")
                unknown_extensions.append(xml_str)

        return "".join(unknown_extensions)


def parse_addon_xml(addon_xml_path: Path) -> AddonXmlData:
    """Parse addon.xml file.

    Args:
        addon_xml_path: Path to addon.xml

    Returns:
        AddonXmlData with parsed attributes

    Raises:
        FileNotFoundError: If addon.xml not found
        ET.ParseError: If XML is malformed
    """
    if not addon_xml_path.exists():
        raise FileNotFoundError(f"addon.xml not found: {addon_xml_path}")

    logger.info(f"Parsing addon.xml from {addon_xml_path}")

    try:
        tree = ET.parse(addon_xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"Failed to parse addon.xml: {e}")
        # Debug: dump file contents when parse fails
        try:
            content = addon_xml_path.read_text(encoding="utf-8")
            logger.error(f"DEBUG: addon.xml first 800 chars:\n{repr(content[:800])}")
        except Exception as debug_e:
            logger.error(f"DEBUG: Could not read file: {debug_e}")
        raise

    data = AddonXmlData()
    data.root = root

    # Parse root attributes
    data.id = root.get("id")
    data.version = root.get("version")
    data.name = root.get("name")
    data.provider_name = root.get("provider-name")

    # Parse metadata extension
    metadata = root.find("extension[@point='xbmc.addon.metadata']")
    if metadata is not None:
        # Simple text elements
        for tag in ("summary", "description", "disclaimer", "license", "source"):
            elem = metadata.find(tag)
            if elem is not None and elem.text:
                setattr(data, tag, elem.text)

        # Assets
        assets_elem = metadata.find("assets")
        if assets_elem is not None:
            for child in assets_elem:
                if child.text:
                    data.assets[child.tag] = child.text

        # Requires
        for req_elem in metadata.findall("requires"):
            addon = req_elem.get("addon")
            version = req_elem.get("version", "")
            if addon:
                data.requires.append({"addon": addon, "version": version})

        # News
        news_elem = metadata.find("news")
        if news_elem is not None:
            data.news = news_elem.text or ""

    logger.info(f"Parsed addon.xml: id={data.id}, version={data.version}")
    return data


def reconcile_requires(
    xml_requires: list[dict[str, str]],
    config_requires: list[dict[str, str]],
    strict: bool = False,
) -> tuple[list[dict[str, str]], list[str]]:
    """Merge requires from addon.xml and config, choosing higher versions on conflict.

    Args:
        xml_requires: Requires from addon.xml
        config_requires: Requires from pyproject.toml config
        strict: If True, raise error on version conflict; if False, warn and choose higher

    Returns:
        Tuple of (merged_requires, warnings)

    Raises:
        ValueError: If strict mode and version conflict found
    """
    requires_dict: dict[str, str] = {}
    warnings = []

    # Start with XML requires
    for req in xml_requires:
        addon = req.get("addon")
        if addon:
            requires_dict[addon] = req.get("version", "")

    # Overlay with config requires
    for req in config_requires:
        addon = req.get("addon")
        if not addon:
            continue

        config_version = req.get("version", "")

        if addon in requires_dict:
            xml_version = requires_dict[addon]
            if xml_version != config_version:
                # Version conflict
                if strict:
                    msg = f"addon {addon}: version conflict - xml={xml_version} vs config={config_version}"
                    logger.error(msg)
                    raise ValueError(msg)
                else:
                    # Choose higher version (simple string comparison for now)
                    higher = max(xml_version, config_version)
                    warning = (
                        f"addon {addon}: versions differ (xml={xml_version}, config={config_version}), using {higher}"
                    )
                    logger.warning(warning)
                    warnings.append(warning)
                    requires_dict[addon] = higher
        else:
            # New addon from config
            requires_dict[addon] = config_version
            logger.info(f"addon {addon}: added from config")

    # Convert back to list
    merged = [{"addon": k, "version": v} for k, v in sorted(requires_dict.items())]
    return merged, warnings


def reconcile_addon(
    xml_data: Optional[AddonXmlData],
    config: Optional[AddonConfig],
    strict: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Reconcile addon.xml and config, with config winning for simple fields.

    Args:
        xml_data: Parsed addon.xml data (or None if file doesn't exist)
        config: Addon config from pyproject.toml (or None if not configured)
        strict: If True, raise error on conflicts; if False, warn and use config

    Returns:
        Tuple of (merged_addon_dict, warnings)

    Raises:
        ValueError: If strict mode and conflicts found
    """
    warnings: list[str] = []
    merged: dict[str, Any] = {}

    if not config:
        # No config, use XML as-is
        if xml_data:
            merged = xml_data.to_dict()
        return merged, warnings

    # Config exists; use it as source of truth for simple fields
    merged["id"] = config.id
    merged["name"] = config.name
    merged["provider-name"] = config.provider_name
    merged["description"] = config.description
    merged["summary"] = config.summary
    merged["license"] = config.license
    merged["disclaimer"] = config.disclaimer
    merged["source"] = config.source
    merged["assets"] = config.assets

    # Check for conflicts with XML (if it exists)
    if xml_data:
        for field in ("id", "name", "provider-name", "description"):
            xml_val = getattr(xml_data, field.replace("-", "_"), None)
            config_val = getattr(config, field.replace("-", "_"), None)

            if xml_val and config_val and xml_val != config_val:
                if strict:
                    msg = f"addon.{field}: conflict between xml='{xml_val}' and config='{config_val}'"
                    logger.error(msg)
                    raise ValueError(msg)
                else:
                    warning = f"addon.{field}: xml='{xml_val}' overridden by config='{config_val}'"
                    logger.warning(warning)
                    warnings.append(warning)

    # Merge requires intelligently
    xml_requires = xml_data.requires if xml_data else []
    config_requires = config.requires if config else []
    merged["requires"], req_warnings = reconcile_requires(xml_requires, config_requires, strict=strict)
    warnings.extend(req_warnings)

    # Keep news from XML (if exists), otherwise empty
    if xml_data and xml_data.news:
        merged["news"] = xml_data.news
    else:
        merged["news"] = ""

    # Preserve unknown extensions from XML
    if xml_data:
        merged["unknown_extensions"] = xml_data.get_unknown_extensions_xml()
    else:
        merged["unknown_extensions"] = ""

    return merged, warnings
