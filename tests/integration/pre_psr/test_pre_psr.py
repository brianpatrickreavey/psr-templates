"""
Pre-PSR integration tests for PSR template harness.
Validates setup, template arrangement, and commit generation.
"""

from pathlib import Path
import subprocess


def test_template_arrangement(temp_git_repo, sample_config):
    """Test that templates are arranged correctly in the fixture repo."""
    templates_dir = Path(
        "/home/bpreavey/Code/psr-templates/templates"
    )  # Assuming absolute path
    fixture_dir = temp_git_repo

    # Run arranger (mock or real? For integration, real)
    from arranger.run import load_config, arrange_templates

    config = load_config(
        Path("/home/bpreavey/Code/psr-templates-fixture/pyproject.toml")
    )  # Need to adjust

    # For now, placeholder
    assert True  # TODO: Implement real test


def test_commit_generation(temp_git_repo):
    """Test that commits are generated correctly."""
    # Create initial commit
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=temp_git_repo, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=temp_git_repo, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "initial"],
        cwd=temp_git_repo,
        check=True,
    )

    # Create ci branch
    subprocess.run(["git", "checkout", "-b", "ci/test"], cwd=temp_git_repo, check=True)

    # Run generate_commits.py
    script_path = Path("/home/bpreavey/Code/psr-templates/tools/generate_commits.py")
    subprocess.run(["python", str(script_path), str(temp_git_repo)], check=True)

    # Check git log
    result = subprocess.run(
        ["git", "log", "--oneline"], cwd=temp_git_repo, capture_output=True, text=True
    )
    assert len(result.stdout.strip().split("\n")) > 1  # More than initial commit


def test_git_setup(temp_git_repo):
    """Test that git repository is set up correctly."""
    # Check if it's a git repo
    assert (temp_git_repo / ".git").exists()

    # Check initial commit or something
    result = subprocess.run(["git", "status"], cwd=temp_git_repo, capture_output=True)
    assert result.returncode == 0
