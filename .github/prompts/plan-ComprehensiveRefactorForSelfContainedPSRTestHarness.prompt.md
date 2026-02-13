## Plan: Comprehensive Refactor for Self-Contained PSR Test Harness with Declarative Arranger

TL;DR: Move integration tests to the fixture repo first for self-contained execution, complete the arranger refactor for declarative config and CLI modes, and finalize workflows. This creates a modular, reproducible system where the fixture simulates a real addon repo with integrated tests, arranger uses pyproject.toml for config, and CI supports both ACT and GitHub with shared actions. Testing sequence: pytest via Makefile, then ACT via Makefile, then GitHub CI via Makefile. Fail on edge cases (e.g., missing config or invalid flags).

**Steps**
1. Move integration tests first: Relocate `psr-templates/tests/integration/` and `psr-templates/tests/conftest.py` to `psr-templates-fixture/tests/`. Update all `Path` references in test files for new relative locations (e.g., `Path("../../pyproject.toml")` for fixture config, `Path("../../psr-templates/tools/generate_commits.py")`, `Path("../../kodi-addon-fixture/CHANGELOG.md")`). Fail if paths are invalid.
2. Update fixture pyproject.toml: Add dev dependency `"psr-templates @ git+https://github.com/user/psr-templates.git@main"` in `[tool.uv.dev-dependencies]` for CI/testing access to arranger and templates.
3. Refactor arranger for config: Update `psr-templates/src/arranger/run.py` to parse `[tool.arranger]` from pyproject.toml with mappings like `{"addon.xml": "kodi/script.module.example/addon.xml", "CHANGELOG.md": "CHANGELOG.md"}`. Add CLI flags `--pypi` (mutually exclusive, defaults false), `--kodi-addon` (defaults false), `--changelog-only` (defaults true if no flags). Use importlib.resources for bundled templates. Prioritize pyproject.toml, fall back to CLI. Fail on invalid config or flags.
4. Bundle templates: Update `psr-templates/pyproject.toml` to include templates as package data via `[tool.setuptools.packages.find]` or similar, ensuring `pip install psr-templates` provides access.
5. Update workflows and actions: Modify `run-pre-psr-tests/action.yml` and `run-post-psr-tests/action.yml` to run `uv run pytest tests/integration/... -v` locally in fixture (remove `--directory` and `cd`). Ensure arranger invocation uses new CLI (e.g., `python -m arranger.run --kodi-addon`).
6. Update tests and docs: Adjust unit tests in `psr-templates/tests/unit/` for new arranger interface. Update `TESTING-STRATEGY.md` and READMEs to describe test locations, declarative config, and CLI usage.
7. Validate end-to-end: Run pytest via Makefile, then ACT via Makefile, then GitHub CI via Makefile to ensure tests pass in fixture, arranger places templates correctly, and PSR succeeds. Suggest additional Makefile targets as needed (e.g., for local arranger testing).

**Verification**
- Tests run successfully from fixture repo with `uv run pytest`.
- Arranger CLI works with pyproject.toml config and flags (e.g., default CHANGELOG.md only); fails on edge cases.
- Workflows execute without path errors; ACT dry-run matches GitHub behavior.
- Templates bundled and accessible post-install.

**Decisions**
- Tests in fixture: Improves self-containment and real-repo simulation.
- Config schema: Simple mappings of template name to destination path.
- Flags: Mutually exclusive for modes, default to CHANGELOG.md only; fail on conflicts.
- Dep: Git URL for ACT compatibility.
- Install: Package-based with bundled templates.
- Testing: Makefile-driven for consistency (pytest → ACT → GitHub CI).