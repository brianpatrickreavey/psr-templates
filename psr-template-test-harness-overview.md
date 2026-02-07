# python-semantic-release Template & Arranger Test Harness
## Deterministic CI Implementation Plan

This document describes a robust, deterministic way to test:

- shared Jinja templates
- arranger logic (file placement, config injection)
- python-semantic-release (PSR) behavior
- changelog + custom artifact generation
- tag/release behavior

…without polluting real repositories or causing flaky CI runs.

---

# Goals

We want to:

✅ Test everything in **GitHub Actions (not just local)**  
✅ Validate **arranger + templates + PSR end‑to‑end**  
✅ Generate both:
- standard `CHANGELOG.md`
- custom artifacts (e.g. `addon.xml`)

✅ Test tags/releases behavior  
✅ Keep tests **deterministic**  
✅ Avoid polluting real repos  
✅ Avoid tag collisions  
✅ Avoid cleanup failures breaking determinism  

---

# High-Level Architecture

Use **three repos**:

1. **templates repo**
   - shared Jinja templates
   - partials/snippets
   - ordering logic
2. **arranger repo**
   - scripts to place templates correctly
   - writes runtime config files
   - patches pyproject for CI-only behavior
3. **fixture repo (test harness)**
   - fake project
   - deterministic commits
   - golden expected outputs
   - runs PSR

The templates repo triggers the fixture repo via `workflow_dispatch`.

---

# Core Design Principles

## 1) Branch-per-run (no history pollution)

Each test run:

```text
baseline tag → create branch ci/<run_id> → run tests → delete branch
```

Never run tests on `main`.

Benefits:
- fully isolated
- deterministic
- no cleanup complexity

---

## 2) Unique CI tag format (prevents collisions)

Configure PSR:

```toml
tag_format = "ci-{run_id}-v{version}"
```

Why:
- avoids collisions between concurrent runs
- CI tags don’t affect real releases
- PSR ignores tags not matching the format

---

## 3) No environment variables inside templates

PSR sandbox blocks `env`.

Instead:

### Use read_file filter

```jinja
{% set order = ("psr_order.txt" | read_file).strip().split(",") %}
```

Store runtime config files in project root.

---

## 4) Single source of truth via files

Examples:

```
psr_order.txt
psr_project_name.txt
psr_section_map.json
```

Arranger writes these per repo/run.

Templates read them.

---

## 5) Deterministic commits

Never create commits manually.

Use a script:

```bash
feat: add feature A
fix: correct bug B
perf: optimize C
```

Same messages every run.

No timestamps.

---

# Workflow Overview

## templates repo

On PR/push:

```
workflow_dispatch → fixture repo
inputs:
  templates_ref
  arranger_ref
  run_id
```

---

## fixture repo workflow

### Steps

1. checkout fixture repo (full history + tags)
2. create branch `ci/<run_id>`
3. checkout templates repo
4. checkout arranger repo
5. run arranger
6. generate deterministic commits
7. run PSR
8. compare outputs with golden files
9. upload artifacts
10. cleanup (always)

---

# Example GitHub Actions Workflow

```yaml
name: Fixture Test

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          fetch-tags: true

      - name: Create test branch
        run: |
          git checkout -b ci/${{ github.run_id }}

      - name: Checkout templates
        uses: actions/checkout@v4
        with:
          repository: org/templates-repo
          path: templates-src

      - name: Run arranger
        run: |
          python arranger/run.py             --templates templates-src             --dest .             --run-id ${{ github.run_id }}

      - name: Generate commits
        run: ./tools/make_test_commits.sh

      - name: Run semantic release
        run: semantic-release version

      - name: Compare outputs
        run: |
          diff -r expected docs
          diff -r expected-addon addon-dir

      - name: Cleanup
        if: always()
        run: |
          git push origin --delete ci/${{ github.run_id }} || true
```

---

# Scheduled Janitor

Because cleanup is not guaranteed (runner crash, cancellation), add:

```yaml
on:
  schedule:
    - cron: "0 * * * *"
```

Delete:

- ci/* branches
- tags starting with ci-
- releases created during tests

---

# Golden File Testing

Fixture repo layout:

```
docs/CHANGELOG.md
addon-dir/addon.xml
expected/docs/CHANGELOG.md
expected-addon/addon.xml
```

CI diff ensures regressions fail immediately.

---

# Recommended Practices

## Pin versions

- PSR version
- templates repo ref
- arranger repo ref

Avoid surprise behavior changes.

---

## Keep templates simple

Avoid copying PSR default macros.

Prefer minimal custom templates.

---

## Avoid timestamps or SHAs in output

They break determinism.

---

# Summary

This approach provides:

✅ deterministic outputs  
✅ full GitHub Actions testing  
✅ safe tag/release behavior  
✅ shared templates  
✅ no repo pollution  
✅ easy cleanup  

It scales cleanly as your templates and arranger grow.

---

If something breaks, inspect uploaded artifacts and diffs. Everything remains reproducible.
