## Plan: Arranger Dead Code Removal

Remove the obsolete `arranger` component, fully replaced by `psr_prepare`, to simplify the codebase. Research confirmed it's broken (missing templates), unused in active workflows, and redundant.

**Steps**
1. Delete [src/arranger/](src/arranger/) directory entirely.
2. Migrate Jinja2 filters: Move `arranger.jinja_filters.FILTERS` to `psr_prepare.jinja_filters` (add to [src/psr_prepare/jinja_filters.py](src/psr_prepare/jinja_filters.py) if not present).
3. Update tool imports: Change `arranger.jinja_filters` to `psr_prepare.jinja_filters` in [tools/render_template.py](tools/render_template.py) and [tools/test_template_rendering.py](tools/test_template_rendering.py).
4. Remove entry point: Delete `psr-build-template-structure` from [pyproject.toml](pyproject.toml).
5. Delete tests: Remove [tests/unit/test_arranger.py](tests/unit/test_arranger.py) (56 tests).
6. Update docs: Remove arranger references from [README.md](README.md), [docs/development/architecture.md](docs/development/architecture.md), and [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) (already removed in Phase 1).
7. Clean fixture config: Remove unused `[tool.arranger]` section from fixture [pyproject.toml](pyproject.toml).

**Verification**
- Run `make test-unit` to confirm no import errors.
- Execute `make ci-simulate` in fixture to ensure workflows unaffected.
- Check coverage: Update thresholds in [pyproject.toml](pyproject.toml) if coverage drops.

**Decisions**
- Full removal chosen over migration, as no unique functionality remains.
