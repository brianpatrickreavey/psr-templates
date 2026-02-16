# Multi-Release CI Pipeline Implementation Plan

**Date**: February 15, 2026
**Goal**: Restructure test-harness.yml to execute 3 cumulative PSR releases (0.1.0 → 0.2.0 → 1.0.0)

## Current State

**Single Release Flow:**
```
pre-psr-tests
  └─ Generate all commits at once
  └─ Create test branch ci/run-id
  └─ Push

psr-execution (SINGLE)
  └─ Run PSR once
  └─ Creates v0.1.0 release

post-psr-tests
  └─ Runs test_multi_release.py
  └─ Tests skip (only 1 version, not 3)
```

## Target State

**Multi-Release Flow:**
```
pre-psr-tests
  └─ cleanup tags/releases
  └─ create empty test branch ci/run-id
  └─ push branch

release-phase-1 (0.0.1 → 0.1.0)
  └─ checkout ci/run-id
  └─ generate-commits (phase 0: breaking + fix + ci)
  └─ commit and push
  └─ run arranger
  └─ run PSR → v0.1.0 tag + release

release-phase-2 (0.1.0 → 0.2.0)
  └─ checkout ci/run-id (with v0.1.0 history)
  └─ generate-commits-append (phase 1: breaking + docs)
  └─ commit and push
  └─ run arranger
  └─ run PSR → v0.2.0 tag + release

release-phase-3 (0.2.0 → 1.0.0)
  └─ checkout ci/run-id (with v0.1.0 + v0.2.0 history)
  └─ generate-commits-append (phase 2: breaking + refactor)
  └─ commit and push
  └─ run arranger
  └─ run PSR → v1.0.0 tag + release

post-psr-tests (PSR_VALIDATE_REAL=1)
  └─ checkout ci/run-id (with all 3 versions)
  └─ CHANGELOG.md: all 3 versions present
  └─ addon.xml: version 1.0.0
  └─ Runs test_multi_release.py
  └─ All 10 tests should PASS (not skip)

cleanup
  └─ delete ci/run-id branch
  └─ delete tags/releases
```

## Implementation Steps

### Step 1: Modify generate_commits.py
**File**: `psr-templates-fixture/tools/generate_commits.py`

**Changes**:
- Add `--phase N` argument to generate only specific phase commits (instead of all at once)
- Add `--append` flag to allow running multiple times on same branch
- Keep `--all` flag for backward compatibility (generates all phases)

**Example usage**:
```bash
generate_commits.py --phase 0       # Generate only phase 0 commits
generate_commits.py --phase 1       # Generate only phase 1 commits
generate_commits.py --all           # Generate all phases (current behavior)
```

**Output**: Commits are appended to git history, allowing cumulative effect

### Step 2: Update Workflow Job Structure
**File**: `.github/workflows/test-harness.yml`

**Current Jobs**:
- pre-psr-tests
- psr-execution (SINGLE)
- kodi-check
- kodi-zip
- kodi-publish
- post-psr-tests
- cleanup

**New Jobs**:
- pre-psr-tests (unchanged, creates empty ci/run-id branch)
- release-phase-1 (generate commits phase 0 → run PSR → v0.1.0)
- release-phase-2 (generate commits phase 1 → run PSR → v0.2.0)
- release-phase-3 (generate commits phase 2 → run PSR → v1.0.0)
- kodi-check (after all phases complete)
- kodi-zip, kodi-publish (after all phases)
- post-psr-tests (after all phases - now validates 3 versions)
- cleanup (same as now)

**Job Dependencies**:
```
pre-psr-tests
  ↓
release-phase-1
  ↓
release-phase-2
  ↓
release-phase-3
  ↓
kodi-check
  ↓
kodi-zip → kodi-publish
  ↓
post-psr-tests
  ↓
cleanup
```

### Step 3: Implement Release Phase Jobs
**Pattern** (each phase similar, but phase 3 uses force-version):

**Phase 1 & 2** (auto semantic bump):
```yaml
release-phase-N:
  needs: release-phase-(N-1)  # Sequential dependency
  runs-on: ubuntu-latest
  outputs:
    phase_N_tag: ${{ steps.psr_N.outputs.tag }}
    phase_N_version: ${{ steps.psr_N.outputs.version }}
  steps:
    - name: Checkout test branch
      uses: actions/checkout@v4
      with:
        ref: ci/${{ github.event.client_payload.run_id }}
        fetch-depth: 0  # Full history to see prior releases

    - name: Generate phase N commits
      run: |
        python tools/generate_commits.py --phase N
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add -A
        git commit -m "Phase N: adds commits for version bump testing (ci-test-run)" || true
        git push origin ci/${{ github.event.client_payload.run_id }}

    - name: Run arranger (template rendering)
      run: python -m arranger

    - name: Run PSR
      id: psr_N
      uses: python-semantic-release/python-semantic-release@v10.5.3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        commit: true
        push: true
        tag: true
        vcs_release: true
```

**Phase 3** (force major version to 1.0.0):
```yaml
release-phase-3:
  needs: release-phase-2  # Must see both 0.1.0 and 0.2.0 commits
  runs-on: ubuntu-latest
  outputs:
    phase_3_tag: ${{ steps.psr_3.outputs.tag }}
    phase_3_version: ${{ steps.psr_3.outputs.version }}
  steps:
    - name: Checkout test branch
      uses: actions/checkout@v4
      with:
        ref: ci/${{ github.event.client_payload.run_id }}
        fetch-depth: 0  # Full history

    - name: Generate phase 3 commits (breaking changes)
      run: |
        python tools/generate_commits.py --phase 2
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add -A
        git commit -m "Phase 3: breaking changes for major version bump (ci-test-run)" || true
        git push origin ci/${{ github.event.client_payload.run_id }}

    - name: Run arranger (template rendering)
      run: python -m arranger

    - name: Run PSR with force=major to 1.0.0
      id: psr_3
      uses: python-semantic-release/python-semantic-release@v10.5.3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        force: major  # Force major version bump: 0.2.0 → 1.0.0
        commit: true
        push: true
        tag: true
        vcs_release: true
```

**Special handling**:
- Phase 1 depends on pre-psr-tests
- Phase 2 depends on phase 1 (semantic bump: 0.1.0 → 0.2.0)
- Phase 3 depends on phase 2 (FORCE: 0.2.0 → 1.0.0 regardless of commits)

### Step 4: Update Post-PSR Tests
**File**: `.github/workflows/test-harness.yml` (post-psr-tests job)

**Changes**:
- Now depends on release-phase-3 (not psr-execution)
- Checks out ci/run-id with full history (v0.1.0, v0.2.0, v1.0.0 all present)
- Sets PSR_VALIDATE_REAL=1
- Runs pytest tests/integration/post_psr/test_multi_release.py
- All 10 tests should PASS (not skip)

**Validation outputs**:
- test_release_0_1_0_changelog → PASS
- test_release_0_1_0_addon_xml → PASS
- test_release_0_2_0_changelog_cumulative → PASS
- test_release_0_2_0_addon_xml_cumulative → PASS
- test_release_1_0_0_changelog_full_history → PASS
- test_release_1_0_0_addon_xml_major_version → PASS
- test_changelog_markdown_format → PASS
- test_addon_xml_no_jinja_references → PASS
- test_changelog_handles_empty_sections → PASS
- test_addon_xml_has_required_attributes → PASS

### Step 5: Handle Kodi Artifacts
**Issue**: After 3 releases, which ZIP artifact do we publish?

**Options**:
1. **Publish only latest (v1.0.0)** - Simplest, final addon state
2. **Publish all 3 ZIPs** - Shows all release artifacts
3. **Publish final + validate others extracted correctly**

**Recommendation**: Publish only v1.0.0 (final release), as that's what users would download. Earlier ZIPs were for testing progression.

**Implementation**:
- kodi-zip/kodi-publish depend on release-phase-3 (not needed until end)
- Extract v1.0.0 tag version
- Build/publish single final ZIP

## Timeline and Dependencies

```
pre-psr-tests (5 min)
  ↓
release-phase-1 (10 min) - PSR runs, creates v0.1.0
  ↓
release-phase-2 (10 min) - PSR runs, creates v0.2.0
  ↓
release-phase-3 (10 min) - PSR runs, creates v1.0.0
  ↓
kodi-check (2 min)
  ↓
kodi-zip (5 min) + kodi-publish (5 min)
  ↓
post-psr-tests (5 min) - validates all 3 releases in templates
  ↓
cleanup (2 min)

Total: ~54 minutes
```

## Edge Cases to Handle

1. **PSR formatting**: Each phase maintains git history. Ensure PSR doesn't reformat git log
2. **Commits per phase**: Use deterministic commit messages (same format each phase)
3. **Fetch depth**: Use `fetch-depth: 0` in all checkout steps to see full history
4. **Branch cleanup**: On cleanup, delete ci/run-id branch to avoid clutter
5. **Error handling**: If any phase fails, cleanup should still run

## Files to Modify

1. **psr-templates-fixture/tools/generate_commits.py**
   - Add `--phase N` argument
   - Add `--append` flag
   - Keep backward compatibility

2. **psr-templates-fixture/.github/workflows/test-harness.yml**
   - Replace single `psr-execution` with `release-phase-1`, `release-phase-2`, `release-phase-3`
   - Update sequential dependencies
   - Update post-psr-tests to validate all 3 releases
   - Update kodi-zip/publish to reference final phase outputs

3. **psr-templates-fixture/TEMPLATE-RENDERING-TEST-PLAN.md**
   - Update Step 7 status to show multi-phase CI implementation

## Validation Criteria

✅ All 10 integration tests pass (not skip)
✅ CHANGELOG.md contains all 3 versions (0.1.0, 0.2.0, 1.0.0)
✅ addon.xml version matches v1.0.0
✅ All 3 releases published with correct tags
✅ Kodi ZIP artifact contains correct final versions
✅ GitHub Actions workflow completes within 60 minutes

## Success Indicators

After implementation and first test run:
- GitHub Actions logs show 3 sequential PSR executions
- Final post-psr-tests output shows "10 passed"
- Fixture repo shows 3 releases in GitHub UI
- CHANGELOG.md rendered with all 3 versions
- addon.xml rendered with v1.0.0
