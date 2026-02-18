"""psr_prepare - Preprocessing tool for PSR (Python Semantic Release).

Prepares templates and configuration for PSR consumption by:
1. Loading configuration from pyproject.toml
2. Parsing existing files (addon.xml, CHANGELOG.md)
3. Reconciling config sources and writing context JSON
4. Copying and mapping templates to correct locations

Usage:
    psr-prepare [--strict] [--config pyproject.toml]

Environment variable:
    PSR_PREPARE_DEBUG: Enable debug logging
"""

__version__ = "0.1.0"
__author__ = "PSR Templates Contributors"
