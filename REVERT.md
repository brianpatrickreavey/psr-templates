# Revert Checkpoint

**Date**: 2026-02-19 18:01:00 -0500

**Purpose**: Safe checkpoint before attempting to fix addon.xml template logic

## Current HEAD Commits

### psr-templates
```
a2c096f47c0c8a03ad1c962b08400bfd7c4072fd
Author: Brian Patrick Reavey <brian@reavey05.com>
Date:   2026-02-19 18:00:13 -0500

    revert: undo addon.xml sorting changes from 0b7bbae
```

### psr-templates-fixture
```
6c97a911decac7ed4fe0cbc31a2effdb6acc1400
Author: Brian Patrick Reavey <brian@reavey05.com>
Date:   2026-02-19 18:00:54 -0500

    chore: remove egg-info and update Makefile
```

## To Revert

```bash
# psr-templates
cd /home/bpreavey/Code/psr-templates
git reset --hard a2c096f47c0c8a03ad1c962b08400bfd7c4072fd

# psr-templates-fixture
cd /home/bpreavey/Code/psr-templates-fixture
git reset --hard 6c97a911decac7ed4fe0cbc31a2effdb6acc1400
```

## Status Before Checkpoint

- CHANGELOG rendering: ✅ WORKING (all 5 phases show correct accumulated versions)
- addon.xml version rendering: ❌ BROKEN (all phases show v0.1.0)
- Root cause: addon.xml.j2 using `releases[-1]` instead of sorted list
- Fix applied: Reverted to HEAD~1 (removed sorting)
- Result: Both CHANGELOG and addon.xml now working
