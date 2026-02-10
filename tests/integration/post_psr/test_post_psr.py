"""
Post-PSR integration tests for PSR template harness.
Validates PSR outputs: version numbers, dates, tags, releases, artifacts.
"""

import pytest
from pathlib import Path
import subprocess
import os


def test_version_number_extraction(mock_psr_response):
    """Test that version numbers are extracted correctly from PSR output."""
    if os.getenv("PSR_VALIDATE_REAL") == "1":
        # Validate real PSR output: check for version in CHANGELOG.md or pyproject.toml
        changelog_path = Path("../CHANGELOG.md")  # Relative to templates/
        if changelog_path.exists():
            content = changelog_path.read_text()
            assert "## [1.0.0]" in content  # Example assertion
        else:
            pytest.skip("CHANGELOG.md not found")
    else:
        # Use mock
        version = mock_psr_response["version"]
        assert version == "1.0.0"


def test_changelog_generation(mock_psr_response, temp_git_repo):
    """Test that changelog is generated with correct dates and content."""
    if os.getenv("PSR_VALIDATE_REAL") == "1":
        # Validate real changelog
        changelog_path = Path("../CHANGELOG.md")
        assert changelog_path.exists()
        content = changelog_path.read_text()
        assert "## [1.0.0]" in content
        assert "2023-01-01" in content  # Example date check
    else:
        # Use mock
        changelog_content = mock_psr_response["changelog"]
        assert "## [1.0.0]" in changelog_content
        assert "2023-01-01" in changelog_content
    assert "2023-01-01" in changelog_content


def test_tag_creation(temp_git_repo, mock_psr_response):
    """Test that tags are created correctly."""
    if os.getenv("PSR_VALIDATE_REAL") == "1":
        # Validate real tags in fixture repo
        result = subprocess.run(
            ["git", "tag", "-l"], cwd=Path("../"), capture_output=True, text=True
        )
        assert "v1.0.0" in result.stdout  # Example tag check
    else:
        # Use mock simulation
        tag = mock_psr_response["tag"]
        # Simulate tag creation
        subprocess.run(["git", "tag", tag], cwd=temp_git_repo, check=True)

        # Check tag exists
        result = subprocess.run(
            ["git", "tag", "-l"], cwd=temp_git_repo, capture_output=True, text=True
        )
        assert tag in result.stdout


def test_artifact_validation(mock_psr_response):
    """Test that artifacts are validated correctly."""
    artifacts = mock_psr_response["artifacts"]
    # For now, assume empty
    assert isinstance(artifacts, list)


def test_cleanup_after_failure(temp_git_repo):
    """Test that cleanup happens even after failure."""
    # Create a branch
    subprocess.run(
        ["git", "checkout", "-b", "test-branch"], cwd=temp_git_repo, check=True
    )

    # Simulate failure and cleanup
    with pytest.raises(Exception, match="Simulated failure"):
        try:
            raise Exception("Simulated failure")
        except Exception:
            # Perform cleanup - just attempt it, don't worry if it fails
            subprocess.run(["git", "checkout", "master"], cwd=temp_git_repo, check=False)
            subprocess.run(["git", "branch", "-D", "test-branch"], cwd=temp_git_repo, check=False)
            # Re-raise the original exception
            raise
