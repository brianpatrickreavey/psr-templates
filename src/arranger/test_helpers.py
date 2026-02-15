"""
Shared test helper utilities for parsing and validating template outputs.

Used by both unit tests (psr-templates) and integration tests (psr-templates-fixture).
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class AddonXmlParser:
    """Parse and validate addon.xml content."""

    @staticmethod
    def parse(content: str) -> Dict:
        """
        Parse addon.xml content and extract key information.

        Args:
            content: XML content as string

        Returns:
            Dict with:
            - root: ElementTree.Element
            - version: Version attribute from addon element
            - id: Addon ID
            - news: News section text
            - news_markers: List of (tag, descriptions) from news section
        """
        root = ET.fromstring(content)
        
        version = root.get("version")
        addon_id = root.get("id")
        
        # Extract news section
        news_elem = root.find(".//news")
        news_text = (news_elem.text or "").strip() if news_elem is not None else ""
        
        # Parse news section for commit markers
        # Format: [feat] description, [fix] description, etc.
        news_markers = []
        if news_text:
            # Split by newlines and look for [tag] markers
            for line in news_text.split("\n"):
                line = line.strip()
                if line and "[" in line and "]" in line:
                    # Extract [tag] and description
                    match = re.match(r"\[(\w+)\]\s+(.*)", line)
                    if match:
                        tag, desc = match.groups()
                        news_markers.append((tag, desc))
        
        return {
            "root": root,
            "version": version,
            "id": addon_id,
            "news": news_text,
            "news_markers": news_markers,
        }

    @staticmethod
    def validate_structure(parsed: Dict) -> None:
        """
        Validate addon.xml has required structure.

        Args:
            parsed: Dict from parse()

        Raises:
            AssertionError if structure invalid
        """
        root = parsed["root"]
        
        # Check required attributes
        assert root.get("id") is not None, "addon element missing 'id' attribute"
        assert root.get("version") is not None, "addon element missing 'version' attribute"
        
        # Check for required child elements
        requires = root.find("requires")
        assert requires is not None, "addon missing <requires> element"
        
        # Check for extension elements
        extensions = root.findall("extension")
        assert len(extensions) > 0, "addon missing <extension> elements"


class ChangelogParser:
    """Parse and validate CHANGELOG.md content."""

    @staticmethod
    def parse(content: str) -> Dict:
        """
        Parse CHANGELOG.md and extract releases and sections.

        Args:
            content: Markdown content as string

        Returns:
            Dict with:
            - content: Original content
            - releases: Dict of {version: {sections: {section_type: count, items: []}}}
            - release_order: List of versions in order they appear
        """
        releases = {}
        release_order = []
        
        # Split by version headers ## vX.Y.Z
        version_pattern = r"^## v([\d.]+)"
        current_version = None
        current_section = None
        
        for line in content.split("\n"):
            # Check for version header
            version_match = re.match(version_pattern, line)
            if version_match:
                current_version = version_match.group(1)
                release_order.append(current_version)
                releases[current_version] = {
                    "sections": {},
                    "items": [],
                }
                current_section = None
                continue
            
            if current_version is None:
                continue
            
            # Check for section headers (### section type)
            section_match = re.match(r"^###\s+(.+)$", line)
            if section_match:
                current_section = section_match.group(1).lower()
                if current_section not in releases[current_version]["sections"]:
                    releases[current_version]["sections"][current_section] = {
                        "count": 0,
                        "items": [],
                    }
                continue
            
            # Count items under current section
            if current_section and current_version:
                # Look for list items (- item)
                item_match = re.match(r"^[\s]*[-*]\s+(.+)$", line)
                if item_match:
                    item = item_match.group(1)
                    releases[current_version]["sections"][current_section]["items"].append(item)
                    releases[current_version]["sections"][current_section]["count"] += 1
                    releases[current_version]["items"].append(item)
        
        return {
            "content": content,
            "releases": releases,
            "release_order": release_order,
        }

    @staticmethod
    def validate_releases_present(parsed: Dict, expected_versions: List[str]) -> None:
        """
        Validate that expected releases are present in changelog.

        Args:
            parsed: Dict from parse()
            expected_versions: List of version strings to check (e.g., ['0.1.0', '0.2.0'])

        Raises:
            AssertionError if any version missing
        """
        releases = parsed["releases"]
        for version in expected_versions:
            assert version in releases, f"Version {version} not found in changelog"

    @staticmethod
    def validate_section_exists(parsed: Dict, version: str, section: str) -> None:
        """
        Validate a section exists in a release.

        Args:
            parsed: Dict from parse()
            version: Version key
            section: Section name (e.g., 'features', 'bug fixes')

        Raises:
            AssertionError if section missing or empty
        """
        releases = parsed["releases"]
        assert version in releases, f"Version {version} not found"
        assert section in releases[version]["sections"], \
            f"Section '{section}' not found in version {version}"
        assert releases[version]["sections"][section]["count"] > 0, \
            f"Section '{section}' in version {version} is empty"


class JinjaTemplateRenderer:
    """Render Jinja2 templates with mock context for testing."""

    @staticmethod
    def render_addon_xml_template(ctx_history_released: Dict) -> str:
        """
        Render addon.xml.j2 template with mock history data.

        Args:
            ctx_history_released: Dict like {'0.1.0': {elements: {...}}, ...}

        Returns:
            Rendered XML string
        """
        from jinja2 import Template
        
        # Load actual template from psr-templates package
        template_path = Path(__file__).parent / "templates" / "kodi-addons" / "addon.xml.j2"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        template_content = template_path.read_text()
        template = Template(template_content)
        
        # Create mock context object with .history.released
        class MockContext:
            class MockHistory:
                def __init__(self, released):
                    self.released = released
            
            def __init__(self, released):
                self.history = self.MockHistory(released)
        
        ctx = MockContext(ctx_history_released)
        
        return template.render(ctx=ctx)

    @staticmethod
    def render_changelog_template(ctx_history_released: Dict) -> str:
        """
        Render CHANGELOG.md.j2 template with mock history data.

        Args:
            ctx_history_released: Dict like {'0.1.0': {elements: {...}, tagged_date: ...}, ...}

        Returns:
            Rendered Markdown string
        """
        from jinja2 import Template
        from datetime import datetime
        
        # Load actual template
        template_path = Path(__file__).parent / "templates" / "universal" / "CHANGELOG.md.j2"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        template_content = template_path.read_text()
        template = Template(template_content)
        
        # Create mock context with date formatting capability
        class MockRelease:
            def __init__(self, version, elements):
                self.version = version
                self.elements = elements
                self.tagged_date = datetime.now()
            
            def __getitem__(self, key):
                if key == "elements":
                    return self.elements
                raise KeyError(key)
        
        class MockContext:
            class MockHistory:
                def __init__(self, released):
                    self.released = {
                        v: MockRelease(v, data.get("elements", {}))
                        for v, data in released.items()
                    }
            
            def __init__(self, released):
                self.history = self.MockHistory(released)
        
        ctx = MockContext(ctx_history_released)
        
        return template.render(ctx=ctx)
