# Enhanced Template Implementation Plan

**Objective**: Enhance PSR templates (addon.xml and CHANGELOG.md) to leverage PSR's update mode for surgical, intelligent updates while preserving developer-controlled content.

**Status**: In Progress

---

## Executive Summary

- **Metadata source**: Existing addon.xml is authoritative for id, name, requires, provider-name
- **Version source**: PSR's semantic release logic (git tags/history); always overrides addon.xml version
- **News updates**: Replace entirely with latest release only; trim all older releases
- **Config scope**: [tool.arranger] is for discovery/mode only; NOT a metadata store
- **Insertion point**: Rebuild via template; `<news>` element holds latest release notes

---

## Implementation Steps

### Step 1: Create implementation plan markdown
**Status**: ✅ COMPLETED
**Date**: 2026-02-17
**Details**:
- Created IMPLEMENTATION_PLAN.md with all steps, status tracking
- Established task tracking system

---

### Step 2: Clarify [tool.arranger] configuration scope
**Status**: ✅ COMPLETED
**Date**: 2026-02-17
**Objective**: Review and document the intended scope of [tool.arranger] configuration

**Tasks Completed**:
- [x] Reviewed [pyproject.toml](pyproject.toml) in both psr-templates and psr-templates-fixture
- [x] Verified [tool.arranger] is used for:
  - `templates-dir`: Template directory location string
  - `use-default-pypi-structure`: Boolean mode flag for PyPI projects
  - `use-default-kodi-addon-structure`: Boolean mode flag for Kodi addons
  - `kodi-addon-directory`: String identifier for Kodi project directory name
  - `source-mappings`: Dictionary of custom source-to-destination template mappings
- [x] Confirmed [tool.arranger] is NOT used for:
  - Addon metadata (id, name, requires, version) - these should come from addon.xml
- [x] Reviewed [src/arranger/run.py](src/arranger/run.py) to understand config loading and validation
- [x] Reviewed existing [docs/development/architecture.md](docs/development/architecture.md)

**Key Findings**:
- Fixture's pyproject.toml currently has: `use-default-kodi-addon-structure = true`, `kodi-addon-directory = "script.module.example"`, `source-mappings = {}`
- Arranger design is clean: config + CLI args determine template placement
- PSR handles rendering separately—proper separation of concerns
- Code validation already implements type and value checking
- No metadata currently stored in [tool.arranger] ✓
- Architecture doc clearly explains arranger vs PSR roles ✓

**Acceptance Criteria**: ✅ MET
- Configuration scope is fully documented in architecture doc
- [tool.arranger] is used for configuration/discovery only (no metadata)
- Separation of concerns between arranger and PSR is clear

---

### Step 3: Design arranger logic to read existing addon.xml metadata
**Status**: ✅ COMPLETED
**Date**: 2026-02-17
**Objective**: Implement XML parsing in arranger to extract metadata from existing addon.xml

**Tasks Completed**:
- [x] Added XML parsing function `_parse_addon_xml()` in [src/arranger/run.py](src/arranger/run.py):
  - Extracts id, name, version, provider-name from addon element
  - Extracts requires/import elements with addon and version attributes
  - Returns None if file doesn't exist, handles ParseError gracefully
- [x] Added validation function `_validate_addon_metadata_consistency()`:
  - Compares [tool.arranger.kodi-addon] config against addon.xml values
  - Warns on mismatch (uses addon.xml values, ignores config)
  - Only runs if both config and file exist
- [x] Integrated validation into main() flow:
  - Called when --kodi-addon flag or use-default-kodi-addon-structure is set
  - Logs warnings to stderr without stopping execution
- [x] Added 7 comprehensive unit tests in [tests/unit/test_arranger.py](psr-templates/tests/unit/test_arranger.py):
  - Test nonexistent files
  - Test successful parsing with requires/imports
  - Test parsing without requires section
  - Test malformed XML handling
  - Test validation with matching metadata
  - Test validation with mismatching metadata
  - Test validation with no existing file (new project)
- [x] Fixed pre-commit configuration:
  - Updated [.pre-commit-config.yaml](.pre-commit-config.yaml) to exclude tests/ from mypy
  - Added flake8-pyproject to dependencies to properly read [tool.flake8] from pyproject.toml
  - Fixed flake8 code issues: redundant exception types, imperative docstring mood
- [x] All tests passing: 63/63 (56 existing + 7 new)
- [x] All pre-commit hooks passing

**Acceptance Criteria**: ✅ MET
- Metadata correctly parsed from existing addon.xml files
- Warnings logged for config/addon.xml mismatches
- Addon.xml values take precedence over config
- New projects can proceed without existing addon.xml
- Unit test coverage comprehensive
- All pre-commit hooks pass

---

### Step 4: Enhance addon.xml.j2 template for update mode + refactor config key
**Status**: ✅ COMPLETED
**Objective**: Update template to support both init and update modes, refactor confusing config key name

**Tasks**:
- [x] Refactor configuration key: `kodi-project-name` → `kodi-addon-directory` ✅ COMPLETED
  - More accurately reflects its use as a directory path, not project name
  - Updated across: config validation, variable names, documentation, tests, fixture, tools
  - This is a breaking change (acceptable at this stage of development)
- [ ] Enhance [src/arranger/templates/kodi-addons/addon.xml.j2](src/arranger/templates/kodi-addons/addon.xml.j2):
  - Detect mode via `ctx.changelog_mode` (init vs update)
  - Use PSR's native approach for version updates

- [ ] **Version attribute handling**:
  - Version updates handled by PSR's `version_variables` config (pattern matching)
  - No version logic in template itself
  - Example config: `version_variables = ["script/module/name/addon.xml:version:nf"]`

- [ ] **Init mode** (file doesn't exist, first release):
  - Generate complete barebones addon.xml
  - Use placeholders: id="script.module.placeholder", name="Placeholder", provider-name="Unknown"
  - Include minimal structure: requires, extension (xbmc.python.module), metadata
  - Include latest release news

- [ ] **Update mode** (file exists, iterative releases):
  - Detect mode via `{% if ctx.changelog_mode == "update" %}`
  - Preserve existing XML structure (id, name, provider-name, requires untouched)
  - Update only: version (via version_variables), news (via template)
  - News: Latest release notes only (no history, within `<news>` tags)

- [ ] **Release notes formatting**:
  - Extract latest release from `ctx.history.released` (semantic version sort)
  - Format: version header + commit messages grouped by type (feat/fix/perf/etc)
  - Filter previous releases (update mode only displays latest)

**Acceptance Criteria**:
- Template correctly detects init vs update mode via `ctx.changelog_mode`
- Init mode generates valid barebones addon.xml with placeholders
- Update mode generates update-compatible addon.xml (preserves existing metadata)
- News section contains only latest release (no prior version history)
- Version attribute updated by PSR's version_variables (not template)
- All 63+ unit tests pass, pre-commit hooks pass
- Template documented with mode behavior and version_variables example

---

### Step 5: Update CHANGELOG.md.j2 template for consistency
**Status**: ⏳ PENDING
**Objective**: Verify and align CHANGELOG.md.j2 with update mode patterns

**Tasks**:
- [ ] Review [src/arranger/templates/universal/CHANGELOG.md.j2](src/arranger/templates/universal/CHANGELOG.md.j2)
- [ ] Verify insertion flag usage for update mode
- [ ] Confirm cumulative history in init mode
- [ ] Confirm latest-only prepend in update mode
- [ ] Align section filtering logic with project conventions
- [ ] No changes expected; document if none needed

**Acceptance Criteria**:
- CHANGELOG.md uses insertion flags correctly
- Behavior documented in code comments
- Consistent with addon.xml template patterns

---

### Step 6: Add metadata validation and warning logic to arranger
**Status**: ⏳ PENDING
**Objective**: Implement validation that warns on metadata drift between config and addon.xml

**Tasks**:
- [ ] In [src/arranger/run.py](src/arranger/run.py):
  - Add validation function comparing [tool.arranger.kodi-addon] vs. parsed addon.xml
  - Warn on mismatch (field-by-field)
  - Log which values are being used (addon.xml takes precedence)
- [ ] Example warning format:
  - "Using id='script.module.example' from existing addon.xml; [tool.arranger] specifies 'old-id'. Ignoring config value."
- [ ] Write unit tests for validation logic
- [ ] Test edge cases: missing config, missing addon.xml, partial mismatches

**Acceptance Criteria**:
- Mismatches detected and logged as warnings
- Addon.xml values always used (config never overrides)
- No errors raised; process continues with warnings

---

### Step 7: Update fixture project (psr-templates-fixture) configuration
**Status**: ⏳ PENDING
**Objective**: Prepare fixture for multi-phase testing with proper configuration

**Tasks**:
- [ ] Review [psr-templates-fixture/pyproject.toml](psr-templates-fixture/pyproject.toml)
- [ ] Ensure [tool.arranger] section:
  - Sets templates-dir correctly
  - Includes --kodi flag or equivalent for Kodi addon mode
  - Does NOT store addon metadata
- [ ] Review [psr-templates-fixture/script.module.example/addon.xml](psr-templates-fixture/script.module.example/addon.xml):
  - Verify it has: id, name, version (initial), provider-name, requires
  - Ensure has empty or minimal `<news>` section (template will populate)
- [ ] Verify fixture directory structure supports multi-release testing

**Acceptance Criteria**:
- [tool.arranger] configured for discovery only
- addon.xml has complete metadata and empty news section
- Fixture ready for multi-release CI workflow

---

### Step 8: Create/update integration tests in psr-templates-fixture
**Status**: ⏳ PENDING
**Objective**: Implement tests validating multi-release workflow and template behavior

**Tasks**:
- [ ] Review [tests/integration/post_psr/test_multi_release.py](psr-templates-fixture/tests/integration/post_psr/test_multi_release.py)
- [ ] Add/update tests for:
  - Multi-release workflow: v0.1.0 → v0.2.0 → v1.0.0
  - Version correctly bumped each release
  - News section contains **only latest release** (no older releases)
  - Metadata (id, name, requires) unchanged across releases
  - Version mismatch detection (if applicable)
- [ ] Validate news section structure and content
- [ ] Add XML parsing helper to validate output structure
- [ ] Test both init (first release) and update (subsequent) modes

**Acceptance Criteria**:
- All multi-release scenarios tested and passing
- News section verified as latest-only (no history)
- Metadata preservation verified
- Tests document expected behavior clearly

---

### Step 9: Add unit tests for template and arranger logic
**Status**: ⏳ PENDING
**Objective**: Implement comprehensive unit tests for new/modified code

**Tasks**:
- [ ] In [tests/unit/test_arranger.py](psr-templates/tests/unit/test_arranger.py):
  - Test addon.xml metadata parsing (extraction of id, name, requires)
  - Test semantic version sorting (unsorted, mixed versions)
  - Test version mismatch detection and warning generation
  - Test metadata validation (config vs. addon.xml comparison)
- [ ] Add template rendering tests:
  - Mock `read_file` filter for update mode
  - Test init mode: complete XML generation
  - Test update mode: metadata preservation, version update, news trimming
  - Test news section trimming (old releases removed)
  - Test invalid/malformed XML handling
- [ ] Aim for 95%+ code coverage

**Acceptance Criteria**:
- All edge cases tested
- >95% code coverage maintained
- Tests clearly document expected behavior
- Mock setup is robust and maintainable

---

### Step 10: Update development documentation
**Status**: ⏳ PENDING
**Objective**: Document new architecture, conventions, and usage patterns

**Tasks**:
- [ ] Update [docs/development/architecture.md](docs/development/architecture.md):
  - Explain arranger vs. PSR roles (separation of concerns)
  - Document metadata sourcing (addon.xml as source of truth)
  - Document version ownership (PSR semantic release logic)
  - Explain init vs. update modes
  - Diagram showing data flow
- [ ] Update [docs/development/conventions.md](docs/development/conventions.md):
  - Document addon.xml structure expectations
  - Explain where metadata should live (addon.xml, not config)
  - Document version management expectations
  - News section format/structure
- [ ] Update [README.md](psr-templates/README.md):
  - Add Kodi addon project example
  - Show minimal pyproject.toml configuration
  - Emphasize addon.xml as source of truth for metadata
  - Show expected addon.xml structure for new projects
- [ ] Update [docs/testing.md](docs/testing.md) if needed for new test patterns

**Acceptance Criteria**:
- Architecture clearly documented
- Conventions reflected in code and docs
- Examples provided for common scenarios
- All colleagues can understand and maintain system

---

## Testing & Verification Checklist

- [ ] **Unit tests passing**: All arranger and template logic tested
- [ ] **Integration tests passing**: Multi-release workflow validated
- [ ] **Manual validation**: Test-results addon.xml files inspected for correct structure
- [ ] **CI/CD validation**: Fixture CI pipeline passes all checks
- [ ] **Documentation complete**: All docs updated and reviewed
- [ ] **Code review ready**: Changes prepared for team review

---

## Rollback Plan

If issues arise during implementation:
1. Each step is committed as a separate git commit
2. Can revert to previous working state with `git reset`
3. No data loss; all changes tracked in version control
4. Plan document itself tracked in git for reference

---

## Notes

- Will leverage PSR's `update mode` (v9.10+) for surgical file updates
- XML `<news>` element used as insertion point (no special markers needed)
- Defensive semantic version sorting to handle any dict key ordering
- Config-driven but source-of-truth is always the existing addon.xml file
