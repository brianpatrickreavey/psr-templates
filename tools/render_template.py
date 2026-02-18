#!/usr/bin/env python3
"""Render Jinja2 templates using PSR's actual environment with mocked commits.

This tool mimics PSR's template rendering behavior but uses mocked commit history
instead of git operations, allowing local testing of templates with psr_prepare output.

Usage:
  # Render all templates from src/arranger/templates to output/
  python tools/render_template.py --template-dir src/arranger/templates --target-dir output

  # Test psr_prepare output (reads templates/*, references .psr_context/ JSON automatically)
  python tools/render_template.py --template-dir templates --target-dir output

  # Single template to stdout (for quick verification)
  python tools/render_template.py --template-dir src/arranger/templates --template CHANGELOG.md.j2
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple, Optional, cast

# Add src to path to import arranger
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# PSR imports for template rendering
# noqa: E402
from semantic_release.changelog.context import \
    ChangelogContext  # noqa: E402,type: ignore
from semantic_release.changelog.release_history import (  # noqa: E402,type: ignore
    Release, ReleaseHistory)
from semantic_release.changelog.template import \
    environment  # noqa: E402,type: ignore
from semantic_release.version.version import Version  # noqa: E402,type: ignore

# Arranger custom filters
from arranger.jinja_filters import FILTERS as ARRANGER_FILTERS  # noqa: E402


class MockParsedCommit(NamedTuple):
    """Mock ParseResult object matching PSR's interface."""

    descriptions: list[str]
    breaking_descriptions: list[str]


def hello_world_filter(value: str = "") -> str:
    """Return a simple greeting message.

    Args:
        value: The piped value (ignored in this demo)

    Returns:
        A greeting message
    """
    return "Hello, World!"


def build_mock_release_history(phase: int = 0) -> ReleaseHistory:
    """Build a mock ReleaseHistory using PSR's Version objects.

    Args:
        phase: 0=v0.1.0, 1=adds v0.2.0, 2=adds v1.0.0
    """
    released: dict[Version, Release] = {}

    # Phase 0: v0.1.0
    if phase >= 0:
        v_0_1_0 = Version.parse("0.1.0")
        released[v_0_1_0] = cast(
            Release,
            {
                "version": v_0_1_0,
                "tagged_date": datetime.now(timezone.utc),
                "tagger": None,
                "committer": None,
                "elements": {
                    "feat": [
                        MockParsedCommit(descriptions=["add feature 1"], breaking_descriptions=[]),
                        MockParsedCommit(descriptions=["add feature 2"], breaking_descriptions=[]),
                    ],
                    "fix": [
                        MockParsedCommit(descriptions=["resolve bug"], breaking_descriptions=[]),
                    ],
                },
            },
        )

    # Phase 1: v0.2.0
    if phase >= 1:
        v_0_2_0 = Version.parse("0.2.0")
        released[v_0_2_0] = cast(
            Release,
            {
                "version": v_0_2_0,
                "tagged_date": datetime.now(timezone.utc),
                "tagger": None,
                "committer": None,
                "elements": {
                    "feat": [
                        MockParsedCommit(descriptions=["add feature 3"], breaking_descriptions=[]),
                    ],
                    "fix": [
                        MockParsedCommit(descriptions=["resolve another bug"], breaking_descriptions=[]),
                    ],
                },
            },
        )

    # Phase 2: v1.0.0 (with breaking changes)
    if phase >= 2:
        v_1_0_0 = Version.parse("1.0.0")
        released[v_1_0_0] = cast(
            Release,
            {
                "version": v_1_0_0,
                "tagged_date": datetime.now(timezone.utc),
                "tagger": None,
                "committer": None,
                "elements": {
                    "feat": [
                        MockParsedCommit(
                            descriptions=["add feature 4"],
                            breaking_descriptions=["removed old API"],
                        ),
                    ],
                    "perf": [
                        MockParsedCommit(descriptions=["improve performance"], breaking_descriptions=[]),
                    ],
                },
            },
        )

    return ReleaseHistory(released=released, unreleased={})


def render_templates(
    template_dir: Path,
    target_dir: Optional[Path] = None,
    specific_template: Optional[str] = None,
    phase: int = 0,
) -> None:
    """Render Jinja2 templates using PSR's environment with mocked commits.

    Args:
        template_dir: Directory containing .j2 templates
        target_dir: Output directory (if None, use stdout for single template)
        specific_template: Render only this template (relative path in template_dir)
        phase: Mock release phase (0, 1, or 2)
    """
    # Resolve paths
    template_dir = Path(template_dir).resolve()

    if target_dir:
        target_dir = Path(target_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

    # Change to template_dir parent for file operations
    work_dir = template_dir.parent
    os.chdir(work_dir)

    # Build mock release history
    release_history = build_mock_release_history(phase=phase)

    # Set up PSR's template environment
    env = environment(
        template_dir=template_dir,
        trim_blocks=False,
        lstrip_blocks=False,
        keep_trailing_newline=True,
    )

    # Register arranger's custom filters to PSR's environment
    env.filters.update(ARRANGER_FILTERS)

    # Register custom demo filter
    env.filters["hello_world"] = hello_world_filter

    # Build changelog context using PSR's actual ChangelogContext
    ctx = ChangelogContext(
        repo_name="example",
        repo_owner="example-owner",
        hvcs_type="github",
        history=release_history,
        changelog_mode="init",
        prev_changelog_file="",
        changelog_insertion_flag="<!-- version list -->",
        mask_initial_release=False,
        filters=(),
    )

    # Bind context to environment (registers all filters and ctx global)
    ctx.bind_to_environment(env)

    # Extract latest release and make it available
    if release_history.released:
        # Get the last (newest) release from the ordered dict
        latest_release = list(release_history.released.values())[-1]
        env.globals["latest_release"] = latest_release

    # Load psr_prepare context if available
    psr_context_dir = work_dir / ".psr_context"
    if psr_context_dir.exists():
        addon_json_path = psr_context_dir / "addon.json"
        if addon_json_path.exists():
            try:
                with open(addon_json_path) as f:
                    addon_data = json.load(f)
                    # Convert "provider-name" to "provider_name" for Jinja2 access
                    if "provider-name" in addon_data:
                        addon_data["provider_name"] = addon_data["provider-name"]
                    # Make addon context available in templates
                    env.globals["addon"] = addon_data
            except Exception as e:
                print(f"⚠ Warning: Failed to load addon.json: {e}", file=sys.stderr)

    # Find templates to render
    if specific_template:
        templates_to_render = [Path(specific_template)]
    else:
        # Find all .j2 files recursively in template_dir
        templates_to_render = sorted(template_dir.rglob("*.j2"))
        if not templates_to_render:
            print(f"No .j2 templates found in {template_dir}", file=sys.stderr)
            return

    print(
        f"Rendering {len(templates_to_render)} template(s) with phase {phase} using PSR's environment...",
        file=sys.stderr,
    )

    # Render each template
    for template_file in templates_to_render:
        # Get template relative to template_dir
        if template_file.is_absolute():
            try:
                rel_path = template_file.relative_to(template_dir)
            except ValueError:
                rel_path = Path(template_file.name)
        else:
            rel_path = template_file

        try:
            # Render template
            template = env.get_template(str(rel_path))
            rendered = template.render()

            # Output to file or stdout
            if target_dir:
                # Calculate output path (remove .j2 extension)
                output_path = target_dir / Path(str(rel_path).replace(".j2", ""))
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(rendered)
                print(f"✓ {rel_path} → {output_path}", file=sys.stderr)
            else:
                # Render to stdout (only for single template)
                if len(templates_to_render) == 1:
                    print(rendered)
                else:
                    # For multiple templates without target_dir, show filename header
                    print(f"\n{'=' * 60}")
                    print(f"### {rel_path}")
                    print(f"{'=' * 60}\n")
                    print(rendered)
        except Exception as e:
            print(f"✗ Error rendering {rel_path}: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            continue


def main() -> None:
    """Render templates with PSR environment and mock release history."""
    parser = argparse.ArgumentParser(
        description="Render Jinja2 templates using PSR's actual environment with mocked commits",
        epilog="""
Examples:
  # Render all templates from src/arranger/templates to output/
  python tools/render_template.py --template-dir src/arranger/templates --target-dir output

  # Test psr_prepare output (templates/ references .psr_context/ JSON automatically)
  python tools/render_template.py --template-dir templates --target-dir output

  # Single template to stdout for verification
  python tools/render_template.py --template-dir src/arranger/templates --template CHANGELOG.md.j2

  # With different mock phase
  python tools/render_template.py --template-dir templates --target-dir output --phase 2
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--template-dir",
        "-d",
        type=Path,
        default=Path("src/arranger/templates"),
        help="Directory containing .j2 templates (default: src/arranger/templates)",
    )
    parser.add_argument(
        "--target-dir",
        "-t",
        type=Path,
        help="Output directory for rendered templates (if not specified, prints to stdout for single template)",
    )
    parser.add_argument(
        "--template",
        "-f",
        help="Render only this specific template (relative path in template-dir)",
    )
    parser.add_argument(
        "--phase",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="Mock release phase: 0=v0.1.0, 1=v0.1.0+v0.2.0, 2=v0.1.0+v0.2.0+v1.0.0 (default: 0)",
    )

    args = parser.parse_args()

    # Render templates
    render_templates(
        template_dir=args.template_dir,
        target_dir=args.target_dir,
        specific_template=args.template,
        phase=args.phase,
    )


if __name__ == "__main__":
    main()
