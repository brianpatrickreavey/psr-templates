### Kodi Addon Integration Plan for PSR Test Harness
**Date**: February 12, 2026
**Status**: Implementation Complete

#### Overview
This plan outlined the steps to add conditional Kodi addon ZIP building and publishing to the PSR test harness workflow, including environment variable setup from `pyproject.toml`, temporary pre-cleanup checks, and extended pytest validations for releases/artifacts.

#### Key Components
- **Workflow Updates**: New jobs in `psr-templates-fixture/.github/workflows/test-harness.yml` for Kodi detection, ZIP building, publishing, and pre-cleanup inspection.
- **Pytest Enhancements**: New tests in `psr-templates/tests/integration/post_psr/test_post_psr.py` to validate releases and artifacts when `PSR_VALIDATE_REAL=1`.
- **Config-Driven Logic**: Use `pyproject.toml` `[tool.arranger]` to detect Kodi projects and set env vars.

#### Detailed Steps
1. **Update Workflow YAML**: ✅ Added `kodi-check`, `kodi-zip`, `kodi-publish`, `pre-cleanup-check` jobs with proper dependencies and conditions.
2. **Update Pytest File**: ✅ Added `test_release_creation()` and `test_release_artifacts()` functions.
3. **Testing and Validation**: Ready for testing on fixture repo.
4. **Cleanup**: Remove `pre-cleanup-check` after confirmation.

#### Files Modified
- `/home/bpreavey/Code/psr-templates-fixture/.github/workflows/test-harness.yml`
- `/home/bpreavey/Code/psr-templates/tests/integration/post_psr/test_post_psr.py`

#### Next Actions
- Test the workflow end-to-end.
- Verify ZIP creation, publishing, and pytest checks.
- Remove temporary `pre-cleanup-check` job.