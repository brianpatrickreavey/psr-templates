"""Configuration loading from pyproject.toml."""

import logging
import tomllib  # Python 3.11+
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AddonConfig:
    """Parsed addon configuration from [tool.psr-prepare.addon]."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize addon config from dictionary."""
        self.id: str = data.get("id", "")
        self.name: Optional[str] = data.get("name")
        self.provider_name: Optional[str] = data.get("provider-name")
        self.description: Optional[str] = data.get("description")
        self.summary: Optional[str] = data.get("summary")
        self.license: Optional[str] = data.get("license")
        self.disclaimer: Optional[str] = data.get("disclaimer")
        self.source: Optional[str] = data.get("source")
        self.assets: dict[str, str] = data.get("assets", {})
        self.requires: list[dict[str, str]] = data.get("requires", [])

    def validate(self) -> list[str]:
        """Validate addon config, return list of errors."""
        errors = []
        if not self.id:
            errors.append("addon.id is required (e.g., id = 'script.module.example')")
        return errors


class ChangelogConfig:
    """Parsed changelog configuration from [tool.psr-prepare.changelog]."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize changelog config from dictionary."""
        self.file: str = data.get("file", "CHANGELOG.md")
        self.mode: str = data.get("mode", "update")

        # Parse news_types: dict mapping commit_type → label
        # Example: {feat: "new", fix: "fix", perf: "improved"}
        self.news_types: dict[str, str] = data.get("news_types", {})

    def validate(self) -> list[str]:
        """Validate changelog config, return list of errors."""
        errors = []
        if self.mode not in ("init", "update"):
            errors.append(f"changelog.mode must be 'init' or 'update', got '{self.mode}'")
        if not isinstance(self.news_types, dict):
            errors.append(f"changelog.news_types must be a dict, got {type(self.news_types).__name__}")
        else:
            for commit_type, label in self.news_types.items():
                if not isinstance(label, str):
                    errors.append(
                        f"changelog.news_types['{commit_type}'] must be a string, "
                        f"got {type(label).__name__}"
                    )
        return errors


class PsrPrepareConfig:
    """Complete psr_prepare configuration."""

    def __init__(self) -> None:
        """Initialize empty configuration."""
        self.addon: Optional[AddonConfig] = None
        self.changelog: Optional[ChangelogConfig] = None

    def validate(self) -> list[str]:
        """Validate configuration, return list of errors."""
        errors = []
        if self.addon:
            errors.extend(self.addon.validate())
        if self.changelog:
            errors.extend(self.changelog.validate())
        return errors


def load_config(config_path: Optional[Path] = None) -> PsrPrepareConfig:
    """Load psr_prepare configuration from pyproject.toml.

    Args:
        config_path: Optional path to pyproject.toml (defaults to current dir)

    Returns:
        PsrPrepareConfig object

    Raises:
        FileNotFoundError: If pyproject.toml not found
        ValueError: If configuration is invalid
    """
    if config_path is None:
        config_path = Path("pyproject.toml")
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    logger.info(f"Loading configuration from {config_path}")

    # Read and parse TOML
    with open(config_path, "rb") as f:
        pyproject = tomllib.load(f)

    # Extract psr-prepare config
    tool_config = pyproject.get("tool", {})
    psr_prepare = tool_config.get("psr-prepare", {})

    # Build config object
    config = PsrPrepareConfig()

    # Load addon section if present
    if "addon" in psr_prepare:
        config.addon = AddonConfig(psr_prepare["addon"])
        logger.info(f"Loaded addon config: id={config.addon.id}")

    # Load changelog section if present
    if "changelog" in psr_prepare:
        config.changelog = ChangelogConfig(psr_prepare["changelog"])
        logger.info(f"Loaded changelog config: file={config.changelog.file}")

    # Validate
    errors = config.validate()
    if errors:
        error_msg = "\n".join(f"  - {e}" for e in errors)
        raise ValueError(f"Configuration validation failed:\n{error_msg}")

    logger.info("Configuration valid")
    return config
