# PSR Template Test Harness Implementation Plan

## Overview
This plan outlines the setup of a deterministic test harness for python-semantic-release (PSR) templates. It uses two repos: this templates repo and a separate fixture repo for testing. The harness ensures end-to-end validation of templates, arranger logic, PSR behavior, changelogs, and artifacts in GitHub Actions without polluting real repos.

## Goals
- Test templates and PSR end-to-end in CI.
- Generate standard CHANGELOG.md and custom artifacts (e.g., addon.xml).
- Ensure deterministic, isolated runs.
- Avoid repo pollution, tag collisions, and cleanup failures.

## Architecture
- **Templates Repo (this repo)**: Houses Jinja templates, arranger script, and shared logic.
- **Fixture Repo (`psr-templates-fixture`)**: Fake Python project with CI workflows, golden files, and test runs. Contains separate subdirectories for different project types (e.g., `fixture/pypi/` for PyPI-style projects, `fixture/kodi/` for Kodi addons) to test varied templates and PSR behaviors.

## Core Principles
1. **Branch-per-Run Isolation**: Create ci/<run_id> branches from main for each test.
2. **Unique CI Tags**: Use tag_format = "ci-{run_id}-v{version}" to avoid collisions.
3. **File-Based Config**: Use read_file filters in templates; no env vars.
4. **Deterministic Commits**: Script-generated commits with " (ci-test-run)" marker.
5. **Exclusion Patterns**: Exclude non-test commits from changelog.

## Implementation Steps
1. **Refine Templates**: Update/add Jinja templates in templates/ for CHANGELOG.md and addon.xml (initial targets). Requirements:
   - Templates must support updating existing files, not just overwriting (e.g., merge new content with existing).
   - Use PSR's `read_file` filter to access original file content, parse it, and update specific sections (e.g., inject version/changelog while preserving dependencies in addon.xml).
   - For addon.xml: Preserve existing dependencies and metadata; only update version/changelog sections.
   - For CHANGELOG.md: Prefer updating (e.g., prepend new entries), but full rewrite is acceptable if needed.
2. **Create Examples Directory**: Add an examples/ directory with sample pyproject.toml files, arranger config examples, and fixture repo structures to demonstrate usage.
3. **Create Commit Generation Script**: Python script (e.g., tools/generate_commits.py) in this repo to create deterministic test commits on the fixture branch, with " (ci-test-run)" appended to messages. Requirements:
   - Assume starting version (e.g., 0.1.0); handle potential mismatches between pyproject.toml and git tags (PSR may error or prioritize tags—verify behavior).
   - Include a test case for mismatch (e.g., pyproject at 0.1.0, tag at 0.1.1) to validate PSR handling.
   - Generate commits in sequential phases to test PSR version bumping (building on each other, e.g., 0.1.0 → 0.2.0 → 1.0.0 → 1.1.0 → 1.1.1):
     - Phase 0: Breaking changes + others → minor bump if version <1.
     - Phase 1: Breaking + others → major bump if version >=1.
     - Phase 2: Features + others → minor bump.
     - Phase 3: Fixes + lesser commits → patch bump.
     - Phase 4: CI/test/etc. commits → no bump.
   - "Others" in phases: Mixture of equal/lesser conventional commits + non-conventional (e.g., "typo", "bump", "initial commit"; [typo], [oops], [ping], [bump]) to ensure correct omission.
   - Include: one of each standard Conventional Commit type, two each of feat/fix/perf; example order: [fix], [feat], [fix], [perf], [ci] → changelog with feat top, 2 fixes, perf, ci; minor bump.
   - Ensure fixture starts with known state; run janitor manually if unclean.
4. **Create Arranger Script**: Python script (arranger/run.py) to place templates and write configs. Requirements:
   - Read template-to-destination mappings from pyproject.toml (e.g., under [tool.arranger] or similar), with hardcoded defaults for common cases; overrides allow customization.
   - Be aware that not all projects need all templates—skip unused ones based on config or presence.
   - For addon directory names, use the project name from pyproject.toml ([project].name); allow override in config if needed.
   - After checking out templates, move/tweak files as needed (e.g., copy _include.j2 into subdirectories to avoid PSR's upwards traversal restrictions).
   - Dynamically match target directory structure in the fixture repo.
   - For Kodi addon.xml, place in addon-named directory (e.g., script.module.testmodule/addon.xml), reading the directory name from pyproject.toml for determinism (avoid error-prone searches).
   - Handle common templating abstractions by replicating shared files into appropriate subdirs.
   - Update PSR config in pyproject.toml post-arrangement (e.g., changelog.template_dir and changelog.default_templates.changelog_file to point to new paths).
   - Handle multiple templates per run (e.g., CHANGELOG.md and addon.xml); process all configured ones.
   - Fail on errors (e.g., missing project name or invalid mappings) unless defaults are explicitly set.
   - Accept CLI args: --templates (path to checked-out templates), --dest (fixture repo root), --run-id (for unique tagging).
3. **Set Up Fixture Repo**:   - Create `psr-templates-fixture` repo manually in GitHub (under the same org, with a README for initialization).   - Fake Python project with pyproject.toml.
   - Golden files (from sample runs).
   - Pre-commit-msg hook rejecting "ci-test-run" commits on main.
   - GitHub Actions: workflow_dispatch (from templates), push to main (drift check).
4. **CI Workflows**:
   - Triggered by repository_dispatch and push.
   - Steps: Checkout, branch creation, template/arranger setup, commit gen, PSR run, diff, cleanup.
5. **Janitor Job**: Scheduled cleanup of ci/* branches/tags.
6. **Pin Versions**: PSR 10.5.3, latest GitHub Actions.
7. **Tests**: Unit tests for scripts (90%+ coverage).

## Endstate Workflow
1. **Template Change**: Developer updates a Jinja template (e.g., CHANGELOG.md.j2) in the templates repo.
2. **Push to Main**: Push changes to main in templates repo.
3. **Trigger Fixture Test**: Automatically trigger a repository_dispatch event in the fixture repo using the `peter-evans/repository-dispatch` GitHub Action on pushes/PRs to main, passing data like templates_ref (SHA) and run_id (e.g., GitHub run ID) in the event payload.
4. **Fixture CI Run**:
   - Creates ci/<run_id> branch from main.
   - Checks out templates and runs arranger.
   - Generates test commits with "ci-test-run" marker.
   - Runs PSR to generate changelog and artifacts.
   - Diffs outputs against golden files.
   - Uploads artifacts and cleans up branch.
5. **Validation**: If diffs match, test passes; else, fails and alerts developer to update golden files or fix issues.
6. **Drift Check**: Pushes to main in fixture repo trigger validation to ensure no "ci-test-run" commits or other pollution.
7. **Cleanup**: Scheduled janitor removes stale ci/* branches/tags.

### Cross-Repo Status Mirroring
To make the templates repo's CI job wait for and mirror the fixture repo's test result:
- Use GitHub CLI (`gh workflow run`) to trigger the fixture workflow and capture the run ID.
- Poll the fixture workflow status using `gh run view <run-id>` until completion.
- If the fixture job fails, fail the templates CI job accordingly.
- Requires a PAT with repo permissions; add as a secret in templates repo.

## Verification
- Manual CI runs from templates repo.
- Check outputs match golden files.
- Monitor determinism and cleanup.

## Testing Framework and Strategy
Adopt pytest as the testing framework for the harness to provide structure, rich reporting, parametrization, and CI integration. Tests live in the `psr-templates` repo (e.g., `tests/` directory) to keep logic with scripts/templates and minimize fixture changes. The fixture repo's CI checks out `psr-templates` and runs the tests from there.

### Pros
- Structured framework with fixtures, parametrization, and assertions for validating PSR outputs (e.g., versions, changelogs, artifacts).
- Rich reporting and debugging (e.g., via plugins like pytest-html), ideal for CI.
- Parametrization for testing different scenarios (e.g., phases, mismatches).
- Extensibility with plugins (e.g., pytest-mock, pytest-cov).

### Cons
- Overhead for e2e operations (e.g., Git clones, PSR runs), making suites slower than pure scripts.
- Setup complexity for managing Git state in tests.

### Concerns
- Isolation: Ensure clean state between tests to avoid flakes.
- Performance: Git ops add time; mitigate with caching/shallow clones.
- Scope: Focus on key invariants (e.g., version bumps, artifact generation) to avoid over-testing.

### Fixture Strategy
Use Approach 2 (incremental Git ops) to balance speed and isolation:
- **Session/Module Fixtures** (e.g., `@pytest.fixture(scope="session")`): Clone the fixture repo once, set up base state (e.g., branch, initial pyproject.toml at 0.1.0, no tags). This handles heavy setup once per pytest run.
- **Class/Function Fixtures** (e.g., `@pytest.fixture(scope="class")`): Reset to base state (e.g., hard reset branch, clean tags) for each test class/function.
- **Phased Tests**: Tests build incrementally—e.g., Phase 0 adds commits and runs PSR; Phase 1 adds more on top. Use dependencies (e.g., `pytest-depends` or explicit calls) to ensure phases run in order.
- **Failing Fast**: Stop at the first phase failure to prevent state pollution (e.g., Phase 0 error invalidating Phase 1). Use assertions that raise early.
- **Teardown**: Clean up (delete branches, tags) at session end.

This enables local testing (fast reruns) while keeping CI efficient. Use `tmp_path` for isolation and libraries like `gitpython` for Git ops.

## Decisions
- Python for arranger.
- Golden files from sample runs.
- Triggers: workflow_dispatch + push.
- Marker-based isolation.
- Local hook + Actions checks for protection.