## Plan: Refactor Arranger for Configurable PSR Template Application

TL;DR: Refactor the arranger module to read source/target paths from the consuming repo's pyproject.toml, add CLI flags for default modes (--pypi, --kodi-addon, --changelog-only), and ensure the fixture repo has a dev dependency to check out the main branch of the templates repo. This creates a user-friendly, declarative workflow where users configure PSR in their pyproject.toml and run simple commands, eliminating manual path specification and improving reproducibility. The target architecture is a CLI tool that installs as a package, reads config from pyproject.toml, and places raw templates with optional overrides. Rendering is handled externally by PSR.

**Steps**
1. Update arranger/run.py to parse pyproject.toml for [tool.arranger] section with source and target paths, falling back to CLI args if not specified. Use importlib.resources to access bundled templates.
2. Add CLI flags --pypi, --kodi-addon, --changelog-only with default behaviors (e.g., --pypi enables PyPI package mode, --kodi-addon for Kodi addons, --changelog-only for changelog updates only).
3. Modify pyproject.toml in psr-templates to include [tool.arranger] config schema, update dependencies for pyproject.toml parsing (e.g., add tomli for TOML reading), and bundle templates as package data.
4. Update fixture/pyproject.toml to add dev dependency for checking out main branch of psr-templates (e.g., via git URL or local path for testing).
5. Refactor main() function in run.py to prioritize pyproject.toml config, apply mode flags, and validate paths before execution. Arranger places raw templates without rendering.
6. Update tests to cover pyproject.toml parsing, CLI flag interactions, and mode-specific behaviors, ensuring raw template placement.
7. Update documentation (README, TESTING-STRATEGY.md) to describe the new declarative config and CLI usage, clarifying that PSR handles rendering.

**Verification**
- Run local tests with various pyproject.toml configs and CLI combinations to ensure correct path resolution and mode application.
- Test fixture repo dev dependency installation and template checkout.
- Manual end-to-end test: Create a sample consuming repo with pyproject.toml config, run arranger commands, verify raw templates are placed correctly (PSR handles rendering separately).
- CI tests pass with new config parsing and mode flags.
- **Act Testing**: Use `act` to simulate GitHub Actions locally for safe, isolated testing of fixture repo integration. Create two workflow files in the fixture repo (`psr-templates-fixture`): `test-harness-act.yml` (single-job workflow for ACT simulation) and `test-harness.yml` (multi-job workflow for real GitHub Actions). Both workflows use shared composite actions in `.github/actions/` for common steps (e.g., setup-environment, checkout-repos, install-deps, run-pre-psr-tests, run-psr). The ACT workflow runs PSR locally via a dedicated composite action (`run-psr-locally`) that installs `python-semantic-release` and executes it with `--dry-run` to simulate releases without real operations. The GitHub workflow uses the standard `python-semantic-release` action. Run `make ci-simulate` in the fixture repo to trigger the ACT workflow via repository_dispatch (defined in `.act/event.json`), ensuring pre/post PSR tests execute with maintained state in the single job. Update composite actions and workflows as needed for new CLI interface and mode flags.

**Decisions**
- Chose pyproject.toml [tool.arranger] section for config to follow Python packaging standards (similar to [tool.black] or [tool.isort]).
- CLI flags override pyproject.toml defaults for flexibility, but prioritize declarative config for reproducibility.
- Dev dependency in fixture uses git URL to main branch for automatic updates in testing, avoiding hardcoded versions.
- Arranger places raw templates (e.g., .j2 files) without rendering; PSR is responsible for rendering them externally.
- Use importlib.resources for accessing bundled templates, providing embedded file access without file system dependencies.

To ensure a clear target architecture, here are the further questions I would ask:

1. What is the exact structure for [tool.arranger] in pyproject.toml? For example, should it be [tool.arranger] source = "path/to/templates", target = "path/to/output", with optional mode flags like pypi = true?

```
[tool.arranger]
use-default-pypi-structure = true
use-default-kodi-addon-structure = false
kodi-project-name = "script.module.example"
source-mappings = [
"CHANGELOG.md" = "templates/CHANGELOG.md.j2"
"addon.xml" = "kodi/script.module.example/addon.xml"
]
```

Add other fields as the become necessary.


2. What are the default behaviors for the CLI flags? For instance, if --pypi is not specified, does it default to false (no PyPI mode), and how do the flags interact (e.g., can multiple be enabled, or are they mutually exclusive)?

Default should be to only create a standard CHANGELOG.md from templates/CHANGELOG.md.j2
Preojct-ype flags (pypi, kodi) should default false.

3. How should the fixture repo's dev dependency work? Is it a git dependency like "psr-templates @ git+https://github.com/user/psr-templates.git@main" in pyproject.toml, or a local path for development?

I do not think a local path will be useful as we will need to maintain separate
pyprojec.toml files for local development vs CI testing.  Just git for now.


4. What is the intended end-user installation method? Should users install arranger as a package (e.g., pip install psr-templates), and if so, how does it access the templates (bundled or separate checkout)?

pip install psr-templates should install the arranger CLI tool and standard templates.

5. Are there any constraints on the source/target paths (e.g., must be relative to repo root, or absolute allowed)? And how should validation handle missing or invalid paths?

source should be just names of templates in the package. Target should be relative to the repo root.