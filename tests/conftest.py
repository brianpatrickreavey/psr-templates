"""
Shared fixtures for PSR template test harness.
"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        # Initialize git repo
        import subprocess

        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
        )
        # Create initial commit on master
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "initial"],
            cwd=repo_path,
            check=True,
        )
        yield repo_path


@pytest.fixture
def mock_psr_response():
    """Mock response from PSR execution."""
    return {
        "version": "0.1.0",
        "tag": "v0.1.0",
        "changelog": "## v0.1.0 - 2023-01-01\n### Added\n- Initial release\n",
        "artifacts": [],
    }


@pytest.fixture
def sample_config():
    """Sample configuration for arranger."""
    return {
        "templates/universal/CHANGELOG.md.j2": "CHANGELOG.md",
        "templates/kodi-addons/addon.xml.j2": "addon.xml",
    }
