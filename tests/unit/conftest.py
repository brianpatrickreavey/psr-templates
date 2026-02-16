"""
Shared test fixtures and utilities for arranger unit tests.

Provides common mock setups and pytest fixtures to reduce code duplication
across test classes.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_template_file(mocker):
    """
    Create a mock template file with read_text() method.

    Returns:
        MagicMock: Mock template file that returns "template content" on read_text().
    """
    mock_file = MagicMock()
    mock_file.read_text.return_value = "template content"
    return mock_file


@pytest.fixture
def mock_fixture_dir(mocker):
    """
    Create a mock fixture directory with proper Path mocking.

    Sets up:
    - fixture_dir.resolve() -> fixture_dir_resolved
    - fixture_dir_resolved.mkdir() -> no-op
    - fixture_dir_resolved / dest -> mock_dst

    Returns:
        Tuple[MagicMock, MagicMock, MagicMock]: (fixture_dir, fixture_dir_resolved, mock_dst)
    """
    fixture_dir = mocker.MagicMock(spec=Path)
    fixture_dir_resolved = mocker.MagicMock(spec=Path)
    mock_dst = mocker.MagicMock(spec=Path)

    fixture_dir.resolve.return_value = fixture_dir_resolved
    fixture_dir_resolved.mkdir = mocker.MagicMock()
    fixture_dir_resolved.__truediv__.return_value = mock_dst

    # Set up destination file mocking
    mock_dst.exists.return_value = False
    mock_dst.is_symlink.return_value = False
    mock_dst.parent.mkdir = mocker.MagicMock()
    mock_dst.write_text = mocker.MagicMock()

    return fixture_dir, fixture_dir_resolved, mock_dst


@pytest.fixture
def mock_templates_package(mocker):
    """
    Create a mock templates package from importlib.resources.files.

    Returns:
        Tuple[MagicMock, MagicMock]: (mock_files patch, mock_template_root)

    Usage:
        mock_files_patch, mock_root = mock_templates_package
        mock_root.__truediv__.return_value = custom_template_mock
    """
    mock_files = mocker.patch("importlib.resources.files")
    mock_root = mocker.MagicMock()
    mock_files.return_value = mock_root
    return mock_files, mock_root


@pytest.fixture
def mock_arrangeable_template(mocker, mock_templates_package, mock_template_file):
    """
    Create a complete mock setup for a successfully arrangeable template.

    Sets up the full chain:
    - importlib.resources.files() returned
    - Mock files / template_path -> mock template file
    - mock template file.read_text() -> "template content"

    Returns:
        Tuple[MagicMock, MagicMock, MagicMock]: (mock_files, mock_root, mock_template)
    """
    mock_files, mock_root = mock_templates_package
    mock_root.__truediv__.return_value = mock_template_file
    return mock_files, mock_root, mock_template_file


def setup_fixture_and_templates_mocks(mocker, fixture_dir_mock=None, template_content="template content"):
    """
    Setup both fixture directory and templates package mocks together.

    Helper function to configure matching mocks for a complete test scenario.

    Args:
        mocker: pytest-mock fixture
        fixture_dir_mock: Optional pre-configured fixture dir mock. If None, creates new one.
        template_content: Content to return from template file read_text()

    Returns:
        Dict with keys: fixture_dir, fixture_dir_resolved, mock_dst, mock_files, mock_root
    """
    # Setup fixture directory
    fixture_dir = mocker.MagicMock(spec=Path)
    fixture_dir_resolved = mocker.MagicMock(spec=Path)
    mock_dst = mocker.MagicMock(spec=Path)

    fixture_dir.resolve.return_value = fixture_dir_resolved
    fixture_dir_resolved.mkdir = mocker.MagicMock()
    fixture_dir_resolved.__truediv__.return_value = mock_dst

    mock_dst.exists.return_value = False
    mock_dst.is_symlink.return_value = False
    mock_dst.parent.mkdir = mocker.MagicMock()
    mock_dst.write_text = mocker.MagicMock()

    # Setup templates package
    mock_files = mocker.patch("importlib.resources.files")
    mock_root = mocker.MagicMock()
    mock_template = mocker.MagicMock()
    mock_template.read_text.return_value = template_content

    mock_root.__truediv__.return_value = mock_template
    mock_files.return_value = mock_root

    return {
        "fixture_dir": fixture_dir,
        "fixture_dir_resolved": fixture_dir_resolved,
        "mock_dst": mock_dst,
        "mock_files": mock_files,
        "mock_root": mock_root,
        "mock_template": mock_template,
    }
