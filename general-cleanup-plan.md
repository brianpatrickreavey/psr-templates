## Plan: General Cleanup and Actions Refactor

Execute Phase 1 file removals and Phase 3 GitHub actions refactor to declutter and improve maintainability. Obsolete files are completed artifacts; actions need consolidation for consistency.

**Steps**
1. **Phase 1: Remove obsolete files** - Delete [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), [REVERT.md](REVERT.md) (both repos), [docs/DISCOVERY_SAMPLE.md](docs/DISCOVERY_SAMPLE.md), [docs/PSR_PREPARE_DESIGN.md](docs/PSR_PREPARE_DESIGN.md), and [TEMPLATE-RENDERING-TEST-PLAN.md](TEMPLATE-RENDERING-TEST-PLAN.md). No archiving; artifacts via `make clean`.
2. **Phase 3: Refactor GitHub actions** - Flatten: Move all `action.yml` from subdirs (e.g., [build-kodi-zip/action.yml](.github/actions/build-kodi-zip/action.yml)) to [.github/actions/](.github/actions/) as descriptive `.yml` files (e.g., `build-kodi-zip.yml`).
3. Create new composites: `install-dev-dependencies.yml`, `configure-git-push.yml`, and `run-psr.yml` (with conditional `no_operation_mode` for ACT).
4. Update workflows: Use shared composites, skip ACT-incompatible steps (e.g., kodi-publish) via env vars in CI files.
5. Delete [WORKFLOW-AUDIT.md](WORKFLOW-AUDIT.md) as irrelevant.

**Verification**
- Run `make test-full` in both repos for stability.
- Execute `make ci-simulate` to validate refactored workflows.
- Manual: Confirm flattened actions in GitHub UI; no broken paths.

**Decisions**
- Flattened actions for simplicity (no subdir benefit).
- Consolidated composites first; PSR differentiated GitHub/ACT.
- Deleted WORKFLOW-AUDIT.md as outdated.
