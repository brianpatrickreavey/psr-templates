# Revert Checkpoint - WORKING STATE

**Date**: 2026-02-20 00:11:00 UTC

**Purpose**: Safe checkpoint - Full Kodi addon.xml template system working with news section

## Current HEAD Commits

### psr-templates
```
8339d580fa7ddc3acceb9f0c19e8550e666a3a3a
Author: Brian Patrick Reavey <brian@reavey05.com>
Date:   2026-02-19T18:23:57-05:00

    feat: add priority-based news with conventional commit tags to addon.xml
```

### psr-templates-fixture
```
59b12d1179b9f8255fd53401cd899d9532e7d5b2
Author: Brian Patrick Reavey <brian@reavey05.com>
Date:   2026-02-19T18:59:52-05:00

    chore: revert multi-type commit experiment, align with Conventional Commits spec
```

## To Revert to This State

```bash
# psr-templates
cd /home/bpreavey/Code/psr-templates
git reset --hard 8339d580fa7ddc3acceb9f0c19e8550e666a3a3a

# psr-templates-fixture
cd /home/bpreavey/Code/psr-templates-fixture
git reset --hard 59b12d1179b9f8255fd53401cd899d9532e7d5b2
```

## Status - FULLY WORKING

✅ **CHANGELOG rendering**: All 5 phases show correct accumulated versions
✅ **addon.xml version rendering**: All 5 phases show correct semantic versions (0.1.0 → 0.1.1 → 1.0.0 → 1.0.0 → 1.0.1)
✅ **addon.xml news section**: Priority-based ordering (P1→P2→P3) with conventional commit tags
✅ **Multi-release handling**: Phase 4 (docs-only) correctly reuses v1.0.0, Phase 5 accumulates Phase 4 changes
✅ **Kodi addon structure**: Resources/lib directory with hello_world module included
✅ **Template preservation**: <requires> blocks and addon metadata survive merges
✅ **GitHub workflow**: test-harness.yml successfully executed all 5 phases with real PSR
✅ **Release artifacts**: 4 releases created with CHANGELOGs and Kodi ZIPs

## Key Implementation Details

### addon.xml.j2 Features
- Sorted releases by version (descending) to get latest
- Priority-based news ordering: Features (P1) → Bugs/Perf (P2) → Docs/Tests/CI/Chores (P3)
- Conventional commit tag mapping (feat→[feat], fix→[fix], etc.)
- Catch-all for unknown types with space-to-dash conversion
- Single description per commit (only first body line parsed by PSR)

### News Section Format
```
<news>vX.Y.Z (YYYY-MM-DD)
[feat] description
[fix] description
[docs] description
</news>
```

### Notable Decisions
- Follows Conventional Commits spec: one type per commit
- PSR limitation: only first body line parsed if multiple types in one commit
- Template uses sorted() not relies on git history order
- Phase 4 correctly shows no news (docs-only, no version bump)
