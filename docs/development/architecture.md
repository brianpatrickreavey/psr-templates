# Architecture

## High-Level Architecture

This project is a Python package providing a CLI tool for placing PSR templates in consuming repositories. The architecture is config-driven, using `[tool.arranger]` in `pyproject.toml` for declarative configuration.

### Key Components

- **src/arranger/run.py**: Main CLI module that parses `[tool.arranger]` config from pyproject.toml, builds template mappings, and places raw templates using `importlib.resources`. Contains ~700 lines with 9 refactored helper functions (Phase 4).
- **src/arranger/templates/**: Bundled package data containing template files (Jinja2 `.j2` templates for CHANGELOG, Kodi addons, PyPI packages, etc.). Accessed via `importlib.resources` for cross-platform embedded file handling.
- **Configuration**: `[tool.arranger]` section in `pyproject.toml` with options like `use-default-pypi-structure`, `kodi-addon-directory`, `templates-dir`, and `source-mappings` for custom templates.

### Data Flow

```
User runs: psr-build-template-structure
           ↓
    Load config from pyproject.toml
           ↓
    Parse CLI args (--pypi, --kodi-addon, --changelog-only, --override)
           ↓
    Build template mappings (default + custom from source-mappings)
           ↓
    For each mapping:
      - Read template content from src/arranger/templates/**/*.j2
      - Determine destination path
      - Check if file exists → respect --override flag
      - Write raw template to destination (UTF-8)
           ↓
    Output: Raw .j2 templates placed for PSR to render later
```

### Design Patterns

- **Config-Driven CLI**: Prioritizes `pyproject.toml` over CLI args for reproducibility and transparency.
- **Embedded Resources**: Uses `importlib.resources` for cross-platform access to bundled templates without file system dependencies or relative paths.
- **Separation of Concerns**: Arranger places raw `.j2` templates; PSR handles Jinja2 rendering and changelog generation externally (no rendering engine in arranger).
- **Helper Functions** (Phase 4): Refactored into 9 focused helpers for better testability:
  - `_validate_flag_exclusivity()`: Mutually exclusive flag validation
  - `_set_default_flag()`: Default to changelog_only if no flags specified
  - `_build_default_mappings()`: Template structure based on project type
  - `_validate_custom_mappings()`: User-provided source-mappings validation
  - `_validate_fixture_directory()`: Fixture repo setup and permissions
  - `_read_template_content()`: Load template file content
  - `_handle_existing_destination()`: Check/remove existing files/symlinks
  - `_write_destination_file()`: Write template with error handling
  - `_arrange_single_template()`: Orchestrate placement of one template
- **Comprehensive Error Handling** (Phase 1-2): Human-readable errors with actionable guidance for missing files, permission issues, TOML decode errors, etc.
- **Type Hints** (Phase 3): Full type annotations with mypy strict mode validation.
- **Testing**: 98% unit test coverage (56 tests) with comprehensive error path testing (Phase 5).

### Key Decisions

1. **CLI tool installed as package** (`pip install psr-templates`) for easy distribution across projects.
2. **No rendering in arranger**: Raw `.j2` files placed for PSR to process separately. This decouples template placement from rendering.
3. **`--override` flag required**: Phase 2 added explicit handling requiring `--override` to replace existing files/symlinks. Provides safety and transparency.
4. **`importlib.resources` preferred** over file copying for embedded assets (no setup.py data_files, cross-platform).
5. **Config validation comprehensive**: Type checking, path validation, mutually exclusive flag handling, empty value detection.

## Project Structure

```
src/arranger/
├── __init__.py           # Package entry point
├── run.py                # Main CLI (704 lines, 9 helpers, full type hints)
└── templates/
    ├── __init__.py
    ├── kodi-addons/      # Kodi addon templates
    │   └── addon.xml.j2
    ├── python-packages/  # PyPI package templates (future)
    └── universal/        # Universal templates
        └── CHANGELOG.md.j2

tests/
├── unit/
│   ├── test_arranger.py  # 56 tests across 7 test classes (98% coverage)
│   ├── conftest.py       # Shared test fixtures and helpers
│   └── __pycache__/
└── __pycache__/
```

## CI/Test Harness Architecture

The CI/test harness is designed to validate PSR template placement and semantic release functionality in an isolated environment, ensuring no pollution of the source repositories.

### Repository Roles

- **psr-templates**: Source of truth for templates, tests, and logic. Read-only during testing.
- **psr-templates-fixture**: Isolated test environment ("harness") where all test artifacts—commits, pushes, tags, releases, and modifications—live. This keeps the harness self-contained.

### Multi-Phase Release Testing (5 Phases)

The workflow executes 5 sequential release phases to validate semantic versioning precedence and release logic. Each phase appends new commits to the repository, and PSR calculates the correct version bump based on commit messages and accumulated state.

**Phase Design** (tests semantic versioning rules):

1. **Phase 1: v0.1.0 - Minor Bump (Pure Features)**
   - Commits: 2× `feat:`
   - Expected: v0.1.0 (minor bump from v0.0.0)
   - Tests: Basic feature versioning

2. **Phase 2: v0.2.0 - Feature Precedence**
   - Commits: 1× `fix:` + 1× `feat:`
   - Expected: v0.2.0 (feature commits take precedence over fixes)
   - Tests: Semantic version precedence rules

3. **Phase 3: v1.0.0 - Force Major Override**
   - Commits: 1× `fix:` + 1× `feat:` (same types as phase 2)
   - Config: `force: major` override in phase config
   - Expected: v1.0.0 (forced major bump overrides calculated version)
   - Tests: Release override behavior

4. **Phase 4: v1.0.0 - No Version Change (Docs Only)**
   - Commits: 2× `docs:`
   - Expected: v1.0.0 (no new release, docs-only commits filtered)
   - Tests: Changelog filter rules, docs-only handling

5. **Phase 5: v1.0.1 - Fix Precedence (Post-Major)**
   - Commits: 1× `fix:` + 1× `docs:`
   - Expected: v1.0.1 (fix commits take precedence over docs)
   - Tests: Precedence rules PostRelease, patch versioning

Each phase:
- Generates phase-specific commits via `tools/generate_commits.py --phase N`
- Pushes commits to test branch
- Runs `psr-prepare` to prepare templates and context
- Executes `python-semantic-release` to create tags and GitHub releases
- (Optional) Builds and publishes Kodi addon artifacts if present
- Subsequent phases see prior commits and tags (full git history inheritance)

### Workflow Overview (GitHub Actions)

1. **pre-release-tests**: Checkout, cleanup old artifacts, setup venv, run pre-PSR tests
2. **release-phase-1 through release-phase-5**: Each generates → prepares → releases
3. **kodi-check/zip/publish**: Parallel Kodi addon tasks (one per phase)
4. **post-release-tests**: Integration validation of all releases and changelogs

### Local Testing with `act` and Gitea

For iterative development without polluting GitHub, the workflow supports local execution via `act` (a local GitHub Actions runner) with an embedded Gitea service for a self-contained git server.

**Why Local Testing Matters:**
- **No GitHub Artifacts**: Test tags, releases, and commits stay local; nothing leaks to your GitHub repository
- **Fast Iteration**: Complete test cycle in seconds without network roundtrip to GitHub
- **Reproducibility**: Local environment matches CI environment for deterministic testing
- **Cost**: Avoids GitHub API quotas and workflow run minutes during development

**Setup Requirements:**
- `act` v0.48.0+ installed (GitHub Actions local runner)
- Docker engine running
- `jq` for JSON processing in scripts

**How It Works:**

The workflow auto-detects local execution mode:
- **ACT Mode Detection**: Presence of `$ACT` environment variable (set by act runner)
- **Gitea Service**: `gitea/gitea:latest` runs as service container (ACT mode only)
- **Git Server URL**: Auto-switches between `http://localhost:3000` (local) or `https://github.com` (GitHub)
- **Anonymous Access**: Gitea configured for anonymous clone/push without authentication

**Running Local Tests:**

```bash
# Clean previous test artifacts
cd psr-templates-fixture
make clean-gitea

# Run all 5 phases locally (20-30 minutes depending on system)
make ci-simulate-consolidated-gitea

# Or run specific phase with act directly
act repository_dispatch \
  -W .github/workflows/test-harness.yml \
  --secret GITHUB_TOKEN="$(gh auth token)" \
  -j phase-1
```

**Output:**
- All 5 phase commits tagged locally in Gitea
- Kodi addon artifacts built to `.artifacts/` directory
- Full workflow logs to console (--verbose for more detail)
- Test cleanup automatic at end (tags, releases, branches)

**Monitoring Progress:**
- Each phase prints version calculated: "Release version: v0.X.Y"
- Debug steps show git log, tag visibility, PSR starting point
- Post-release-tests validate all releases completed successfully

**Key Gotchas:**
- First run downloads Gitea image (~200MB) - cache reused on subsequent runs
- Cleanup may take 30-60 seconds per run
- ACT requires resources (CPU/memory) for parallel job execution

All 5 phases can be tested locally before any push to GitHub, achieving full validation with zero GitHub interaction.

### Key Principles

- **Isolation**: Test artifacts confined to fixture (GitHub or local gitea); templates repo untouched
- **Reproducibility**: Local testing via `act` with gitea mirrors production CI behavior
- **Safety**: No production tags/releases in CI runs; uses isolated test repos or local gitea
- **Git State Persistence**: Full commit history and tags inherited across phases within a single workflow run

## Testing Strategy

### Unit Tests (98% coverage, 56 tests)

- **Configuration Loading**: Config parsing, TOML errors, missing files
- **Template Mapping**: Default mappings, custom mappings, validation
- **File Operations**: Existing file handling, symlinks, permissions, encoding
- **Error Paths**: All exception handlers tested with realistic scenarios
- **Edge Cases**: Empty values, type mismatches, encoding errors

### Integration Tests (in fixture repo)

- Full workflow: config → templates placed → PSR execution → releases

See [AUDIT-FINDINGS.md](../../AUDIT-FINDINGS.md) for detailed test phase breakdowns (Phases 1-5).

## Recent Changes (Phases 1-5)

- **Phase 1**: Added comprehensive error handling with user-friendly messages.
- **Phase 2**: Enhanced validation for source-mappings, override behavior, symlink handling.
- **Phase 3**: Added full type hints and mypy strict mode validation.
- **Phase 4**: Refactored into helper functions, added comprehensive docstrings, extracted test fixtures.
- **Phase 5**: Expanded test coverage from 80% to 98%, added documentation stream (README, CONTRIBUTING, pre-commit, GitHub Actions workflow, etc.).

## See Also

- [Development Guide](./environment.md) - Setup and tools
- [Coding Conventions](./conventions.md) - Standards and requirements
- [Workflow Protocols](./protocols.md) - Development practices
- [AUDIT-FINDINGS.md](../../AUDIT-FINDINGS.md) - Detailed improvement tracking
