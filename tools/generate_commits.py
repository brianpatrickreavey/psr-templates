#!/usr/bin/env python3
"""
Generate deterministic test commits for PSR template testing.

This script creates commits in phases to test version bumping behavior.
All commits include " (ci-test-run)" marker for exclusion.
"""

import subprocess
import sys
from pathlib import Path

def run_git(*args, cwd=None):
    """Run a git command."""
    result = subprocess.run(['git'] + list(args), cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git command failed: {' '.join(args)}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip()

def create_commit(message, cwd=None):
    """Create a commit with the test marker."""
    full_message = f"{message} (ci-test-run)"
    run_git('commit', '-m', full_message, '--allow-empty', cwd=cwd)

def phase_0_breaking_changes(repo_path):
    """Phase 0: Breaking changes + others → minor bump if version <1."""
    print("Phase 0: Breaking changes")
    # Example: feat!: breaking change
    run_git('commit', '-m', 'feat!: add breaking API change (ci-test-run)', '--allow-empty', cwd=repo_path)
    # Add others: fix, ci, etc.

def phase_1_major_bump(repo_path):
    """Phase 1: Breaking + others → major bump if version >=1."""
    print("Phase 1: Major bump")
    # Continue from phase 0

def phase_2_minor_bump(repo_path):
    """Phase 2: Features + others → minor bump."""
    print("Phase 2: Minor bump")

def phase_3_patch_bump(repo_path):
    """Phase 3: Fixes + lesser → patch bump."""
    print("Phase 3: Patch bump")

def phase_4_no_bump(repo_path):
    """Phase 4: CI/test/etc. → no bump."""
    print("Phase 4: No bump")

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_commits.py <fixture_repo_path>")
        sys.exit(1)

    repo_path = Path(sys.argv[1])
    if not repo_path.exists():
        print(f"Repo path {repo_path} does not exist")
        sys.exit(1)

    # Assume starting at 0.1.0
    print("Generating test commits...")

    phase_0_breaking_changes(repo_path)
    phase_1_major_bump(repo_path)
    phase_2_minor_bump(repo_path)
    phase_3_patch_bump(repo_path)
    phase_4_no_bump(repo_path)

    print("Commits generated.")

if __name__ == '__main__':
    main()