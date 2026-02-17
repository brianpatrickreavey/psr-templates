#!/usr/bin/env python3
"""Test template rendering locally without test harness.

Creates a temporary git repo with test commits and renders templates.
Useful for quick feedback without running full test harness.

Usage:
  python tools/test_template_rendering.py [--output-dir /tmp/results]
"""

import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Union

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))  # noqa: E402

from jinja2 import Environment, FileSystemLoader  # noqa: E402

# Import custom Jinja2 filters from arranger package
from arranger.jinja_filters import FILTERS as JINJA_FILTERS  # noqa: E402


def run_git(cmd: Union[str, list[str]], cwd: Path) -> str:
    """Run git command. cmd can be a string or list."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    result = subprocess.run(["git"] + cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def git_commit(message: str, cwd: Path) -> None:
    """Create a commit with message."""
    run_git(["commit", "-m", message], cwd)


def git_tag(tag: str, cwd: Path) -> None:
    """Create a git tag."""
    run_git(["tag", tag], cwd)


def setup_test_repo(repo_path: Path) -> None:
    """Create a test git repo with commits and tags."""
    repo_path.mkdir(exist_ok=True)

    # Init repo
    run_git(["init"], repo_path)
    run_git(["config", "user.email", "test@example.com"], repo_path)
    run_git(["config", "user.name", "Test User"], repo_path)

    # Create initial commit
    (repo_path / "README.md").write_text("# Test Project\n")
    run_git(["add", "README.md"], repo_path)
    git_commit("initial commit", repo_path)

    # Phase 1: Features for 0.1.0
    (repo_path / "feature1.txt").write_text("feature 1")
    run_git(["add", "feature1.txt"], repo_path)
    git_commit("feat: add feature 1", repo_path)

    (repo_path / "feature2.txt").write_text("feature 2")
    run_git(["add", "feature2.txt"], repo_path)
    git_commit("feat: add feature 2", repo_path)

    (repo_path / "bugfix1.txt").write_text("fix")
    run_git(["add", "bugfix1.txt"], repo_path)
    git_commit("fix: resolve bug", repo_path)

    # Tag 0.1.0
    git_tag("v0.1.0", repo_path)

    # Phase 2: Features for 0.2.0
    (repo_path / "feature3.txt").write_text("feature 3")
    run_git(["add", "feature3.txt"], repo_path)
    git_commit("feat: add feature 3", repo_path)

    (repo_path / "bugfix2.txt").write_text("fix 2")
    run_git(["add", "bugfix2.txt"], repo_path)
    git_commit("fix: resolve another bug", repo_path)

    # Tag 0.2.0
    git_tag("v0.2.0", repo_path)

    print(f"✓ Created test repo with commits and tags at {repo_path}")


def build_mock_release_history(repo_path: Path) -> dict[str, Any]:
    """Build a mock ReleaseHistory from git commits."""
    # For simplicity, manually construct the release history
    # that matches the commits we created above

    releases = {
        "0.1.0": {
            "version": "0.1.0",
            "tagged_date": datetime.now(timezone.utc),
            "tagger": None,
            "committer": None,
            "elements": {
                "feat": [
                    SimpleNamespace(descriptions=["add feature 1"], breaking_descriptions=[]),
                    SimpleNamespace(descriptions=["add feature 2"], breaking_descriptions=[]),
                ],
                "fix": [SimpleNamespace(descriptions=["resolve bug"], breaking_descriptions=[])],
            },
        },
        "0.2.0": {
            "version": "0.2.0",
            "tagged_date": datetime.now(timezone.utc),
            "tagger": None,
            "committer": None,
            "elements": {
                "feat": [SimpleNamespace(descriptions=["add feature 3"], breaking_descriptions=[])],
                "fix": [SimpleNamespace(descriptions=["resolve another bug"], breaking_descriptions=[])],
            },
        },
    }

    return releases


def render_templates(releases: dict[str, Any], output_dir: Path) -> None:
    """Render both templates for each release sequentially, building up history."""
    output_dir.mkdir(parents=True, exist_ok=True)
    templates_dir = Path("src/arranger/templates")
    fixture_dir = Path("../psr-templates-fixture")

    # Custom Jinja2 filter for read_file
    # Use filters from arranger package (read_file, read_file_or_empty, file_exists)
    # Note: these are also registered globally via arranger.__init__ monkey-patching

    # Sort versions to render in order (0.1.0, then 0.2.0, etc.)
    sorted_versions = sorted(releases.keys(), key=lambda v: tuple(map(int, v.split("."))))

    cumulative_releases = {}  # Build up releases as we go

    for i, version in enumerate(sorted_versions):
        # Add this version to cumulative history (simulating PSR workflow)
        cumulative_releases[version] = releases[version]

        version_dir = output_dir / f"v{version}"
        version_dir.mkdir(exist_ok=True)

        # Determine if this is first release (init) or subsequent (update)
        # For addon.xml: if fixture has it, v0.1.0 reads from fixture (update mode)
        #                otherwise v0.1.0 generates from scratch (init mode)
        is_first_release = i == 0
        fixture_addon_exists = (fixture_dir / "script.module.example" / "addon.xml").exists()
        addon_xml_mode = "init" if (is_first_release and not fixture_addon_exists) else "update"
        # For changelog: only init if first release AND no existing changelog
        fixture_changelog_exists = (fixture_dir / "CHANGELOG.md").exists()
        changelog_mode = "init" if (is_first_release and not fixture_changelog_exists) else "update"

        # Set up files for rendering
        addon_xml_path = version_dir / "addon.xml"
        changelog_path = version_dir / "CHANGELOG.md"

        # For init mode, use fixture files as base
        if is_first_release:
            fixture_addon = fixture_dir / "script.module.example" / "addon.xml"
            if fixture_addon.exists():
                addon_xml_path.write_text(fixture_addon.read_text())
                print("  Copied addon.xml from fixture repo")

            fixture_changelog = fixture_dir / "CHANGELOG.md"
            if fixture_changelog.exists():
                changelog_path.write_text(fixture_changelog.read_text())
                print("  Copied CHANGELOG.md from fixture repo")
        else:
            # For update mode, copy from previous version
            prev_version = sorted_versions[i - 1]
            prev_addon = output_dir / f"v{prev_version}" / "addon.xml"
            if prev_addon.exists():
                addon_xml_path.write_text(prev_addon.read_text())
                print(f"  Copied addon.xml from v{prev_version}")

            prev_changelog = output_dir / f"v{prev_version}" / "CHANGELOG.md"
            if prev_changelog.exists():
                changelog_path.write_text(prev_changelog.read_text())
                print(f"  Copied CHANGELOG.md from v{prev_version}")

        # Debug: print what's happening
        print(f"  Rendering v{version} | addon.xml: {addon_xml_mode} | CHANGELOG.md: {changelog_mode}")

        # Mock PSR context with only releases up to this point
        # For addon.xml update mode: pass the source file (fixture for v0.1.0, previous release otherwise)
        addon_source = None
        if addon_xml_mode == "update":
            if is_first_release:
                # For v0.1.0 in update mode, read from fixture
                addon_source = str(fixture_dir / "script.module.example" / "addon.xml")
            else:
                # For subsequent releases, read from previous release
                addon_source = str(addon_xml_path)

        # For changelog update mode: pass the source file similarly
        changelog_source = None
        if changelog_mode == "update":
            changelog_source = str(changelog_path)

        ctx = SimpleNamespace(
            changelog_mode=changelog_mode,
            history=SimpleNamespace(released=cumulative_releases.copy()),
            existing_addon_file=addon_source,
            existing_changelog_file=changelog_source,
        )

        # Render addon.xml.j2
        env = Environment(loader=FileSystemLoader(templates_dir / "kodi-addons"))
        env.filters.update(JINJA_FILTERS)  # Register all custom filters
        addon_template = env.get_template("addon.xml.j2")
        addon_output = addon_template.render(ctx=ctx)

        # For update mode: merge with existing addon.xml at <news> insertion point
        if addon_xml_mode == "update" and ctx.existing_addon_file:
            # Read the source file (fixture for v0.1.0, previous release for v0.2.0+)
            existing_addon = Path(ctx.existing_addon_file).read_text()

            # Extract just the <news>...</news> section from the new output
            news_start = addon_output.find("<news>")
            news_end = addon_output.find("</news>")
            if news_start >= 0 and news_end > news_start:
                news_section = addon_output[news_start : news_end + 7]  # Include </news>

                # Find and replace the <news> section in existing addon.xml
                existing_news_start = existing_addon.find("<news>")
                existing_news_end = existing_addon.find("</news>")
                if existing_news_start >= 0 and existing_news_end > existing_news_start:
                    # Replace the old news section with new one
                    addon_output = (
                        existing_addon[:existing_news_start] + news_section + existing_addon[existing_news_end + 7 :]
                    )

        (version_dir / "addon.xml").write_text(addon_output)
        print(f"✓ Rendered addon.xml for v{version}")

        # Render CHANGELOG.md.j2
        env = Environment(loader=FileSystemLoader(templates_dir / "universal"))
        env.filters.update(JINJA_FILTERS)  # Register all custom filters
        changelog_template = env.get_template("CHANGELOG.md.j2")
        changelog_output = changelog_template.render(ctx=ctx)

        # For update mode: merge with newest first
        if changelog_mode == "update":
            # Read the existing CHANGELOG
            existing_changelog = changelog_path.read_text()

            # Extract just the release section from the new output
            # Find where the ## vX.Y.Z section starts
            release_section = ""
            if "## v" in changelog_output:
                idx = changelog_output.find("## v")
                release_section = changelog_output[idx:]
                # Remove the insertion flag from the section
                insertion_flag = "<!-- version list -->"
                release_section = release_section.replace(insertion_flag, "").strip()

                # Find the position to insert: before the first ## vX.Y.Z in existing file
                first_version_match = re.search(r"^## v\d+\.\d+\.\d+", existing_changelog, re.MULTILINE)
                if first_version_match:
                    insert_pos = first_version_match.start()
                    # Insert before the first version heading
                    merged = (
                        existing_changelog[:insert_pos] + release_section + "\n\n" + existing_changelog[insert_pos:]
                    )
                    changelog_output = merged
                elif insertion_flag in existing_changelog:
                    # Fallback: insert at flag location if no version found
                    merged = existing_changelog.replace(insertion_flag, release_section + "\n" + insertion_flag)
                    changelog_output = merged

        (version_dir / "CHANGELOG.md").write_text(changelog_output)
        print(f"✓ Rendered CHANGELOG.md for v{version}")

        # After rendering v0.1.0, make a backup and edit metadata to test preservation in v0.2.0
        if is_first_release:
            import shutil

            backup_dir = output_dir / f"v{version}-original"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(version_dir, backup_dir)
            print(f"✓ Backed up v{version} to v{version}-original")

            # Edit addon.xml metadata
            addon_xml_content = addon_xml_path.read_text()
            addon_xml_content = addon_xml_content.replace(
                'id="script.module.placeholder"', 'id="script.module.example"'
            )
            addon_xml_content = addon_xml_content.replace('name="Placeholder"', 'name="Example Module"')
            addon_xml_content = addon_xml_content.replace('provider-name="Unknown"', 'provider-name="Example"')

            # Add a fake requires import
            python_import = '        <import addon="xbmc.python" version="3.0.0"/>'
            python_and_requests = python_import + '\n        <import addon="script.module.requests" version="2.28.0"/>'
            addon_xml_content = addon_xml_content.replace(python_import, python_and_requests)

            addon_xml_path.write_text(addon_xml_content)
            print(f"✓ Edited v{version} addon.xml metadata for preservation test")


def main() -> None:
    """Run template rendering test with local git repo."""
    import argparse

    parser = argparse.ArgumentParser(description="Test template rendering locally")
    parser.add_argument(
        "--output-dir", default="/tmp/psr-template-test-results", help="Output directory for rendered templates"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    # Clean and create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)

    print(f"Testing template rendering to {output_dir}\n")

    # Create temp test repo
    with tempfile.TemporaryDirectory() as tmpdir:
        test_repo = Path(tmpdir) / "test-repo"
        setup_test_repo(test_repo)

        # Build mock release history
        releases = build_mock_release_history(test_repo)

        # Render templates
        render_templates(releases, output_dir)

    print(f"\n✓ Test artifacts written to {output_dir}")
    print("\nYou can now inspect:")
    for version_dir in sorted(output_dir.glob("v*")):
        print(f"\n  {version_dir.name}/")
        print("    - addon.xml")
        print("    - CHANGELOG.md")


if __name__ == "__main__":
    main()
