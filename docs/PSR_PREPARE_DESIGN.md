# psr_prepare Design Document

## Overview

**psr_prepare** is a preprocessing tool that prepares templates and configuration for Python Semantic Release (PSR) to consume. It replaces and extends the current "arranger" functionality.

**Core Philosophy:**
- Separation of concerns: psr_prepare handles file parsing and template placement; PSR handles rendering
- Configuration-driven behavior: no magic modes, config presence determines features
- Templates stay simple: they consume pre-parsed JSON, not make decisions
- Backward compatible: preserves existing arranger template mapping behavior

---

## Architecture

```
User Project
    ↓
psr_prepare
├── 1. Load pyproject.toml config
├── 2. Parse existing files (addon.xml, CHANGELOG.md)
├── 3. Reconcile config sources (warn/error on discrepancies)
├── 4. Write context JSON to .psr_context/
└── 5. Copy/map templates to templates/
    ↓
PSR (semantic-release)
├── Read templates from templates/
├── Read context from .psr_context/
├── Render templates with commit history + context
└── Output final artifacts
```

---

## psr_prepare Functionality

### 1. Configuration Loading

**Source:** `pyproject.toml` under `[tool.psr-prepare]`

**Sections:**
```toml
[tool.psr-prepare.addon]
id = "script.module.example"         # Required if section exists
name = "My Module"                   # Optional, overrides addon.xml
provider-name = "My Provider"        # Optional, overrides addon.xml
description = "A module for Kodi"   # Optional, overrides addon.xml
summary = "Short description"        # Optional, overrides addon.xml
license = "GPL-2.0-only"            # Optional, overrides addon.xml

[[tool.psr-prepare.addon.requires]]  # Optional, merged with addon.xml requires
addon = "xbmc.python"
version = "3.0.0+"

[[tool.psr-prepare.addon.requires]]
addon = "script.module.requests"
version = "2.31.0+"

[tool.psr-prepare.changelog]
# file = "CHANGELOG.md"              # Optional, defaults to CHANGELOG.md
# mode = "update"                    # Optional, defaults to "update"
```

**Feature Flags by Config Presence:**
- `[tool.psr-prepare.addon]` exists → process addon.xml mapping
- No addon section → skip addon processing entirely

### 2. File Parsing & Reconciliation

**If addon.xml exists:**
1. Parse as XML
2. Extract attributes (`id`, `version`, `provider-name`, etc.)
3. Compare to `[tool.psr-prepare.addon]` config
4. Log warning if attributes differ
5. Use `pyproject.toml` as source of truth
6. If `--strict` flag: fail with error instead of warning

**If CHANGELOG.md exists:**
1. Detect file presence
2. Pass existence to context (mode: "update" vs "init")

### 3. Write Context JSON

Output to `.psr_context/` directory:

**addon.json** (if `[tool.psr-prepare.addon]` configured):
```json
{
  "id": "script.module.example",
  "name": "My Module",
  "provider-name": "My Provider",
  "description": "A useful module for Kodi",
  "license": "GPL-2.0-only",
  "assets": {
    "icon": "resources/media/icon.png",
    "fanart": "resources/media/fanart.jpg"
  },
  "requires": [
    { "addon": "xbmc.python", "version": "3.0.0+" },
    { "addon": "script.module.requests", "version": "2.31.0+" }
  ],
  "news": "",
  "existing": true
}
```
Include **all** fields parsed from pyproject.toml and existing addon.xml, creating a "cleaned-up" version of addon metadata. Templates will reference these fields via Jinja2.

**changelog.json**:
```json
{
  "file": "CHANGELOG.md",
  "mode": "update",
  "existing": true
}
```

### 4. Template Mapping & Writing

**Source Directory:** `src/arranger/templates/` (in psr-templates package)

**Output:** Write Jinja2 templates to `templates/` directory (gitignored, regenerated each run)

**Categories:**

| Source Category | Config Check | Output Location | Use Case |
|---|---|---|---|
| `universal/` | Always | `templates/` | Files for all projects (CHANGELOG.md, etc.) |
| `kodi-addons/` | `[tool.psr-prepare.addon]` | `templates/{addon_id}/` | Kodi addon files (addon.xml.j2) |
| `python-packages/` | Future | `templates/{package_id}/` | Python package files (future) |

**Template Content:**
- Copy source templates as-is
- For addon.xml: ensure it has `<news>{{ addon.news }}</news>` placeholder (insert if missing)
- Templates reference JSON context: `{{ addon.id }}`, `{{ addon.requires }}`, etc.
- PSR will render these templates using JSON context to produce final output files

**Mapping Logic:**
```python
# Always copy universal templates
copy("src/arranger/templates/universal/*", "templates/")

# If addon section exists, copy addon templates and ensure news section
if "addon" in config:
    addon_id = config["addon"]["id"]

    # Copy template
    copy("src/arranger/templates/kodi-addons/addon.xml.j2",
         f"templates/{addon_id}/addon.xml.j2")

    # Ensure news placeholder exists in template
    ensure_news_section(f"templates/{addon_id}/addon.xml.j2")
```

**Example Output Structure:**
```
templates/                             # Gitignored - regenerated each run
├── script.module.example/
│   └── addon.xml.j2                   # References {{ addon.* }} variables
├── CHANGELOG.md.j2                    # References {{ changelog.* }} variables
└── ...

.psr_context/                          # Context for templates
├── addon.json
└── changelog.json
```

---

## Configuration Examples

### Minimal (CHANGELOG only, no addon)
```toml
[tool.psr-prepare.changelog]
file = "CHANGELOG.md"
```
→ Only universal templates copied to `templates/`, no addon processing

### Full (Kodi addon with CHANGELOG and requires)
```toml
[tool.psr-prepare.addon]
id = "script.module.example"
name = "My Script Module"
provider-name = "My Provider"
description = "A useful module for Kodi"
license = "GPL-2.0-only"

[[tool.psr-prepare.addon.requires]]
addon = "xbmc.python"
version = "3.0.0+"

[[tool.psr-prepare.addon.requires]]
addon = "script.module.requests"
version = "2.31.0+"

[tool.psr-prepare.changelog]
file = "CHANGELOG.md"
```
→ Both addon and universal templates copied, addon.json written with merged requires

### With Existing addon.xml (will be reconciled)
If `script.module.example/addon.xml` exists:
- psr_prepare parses it
- Reconciles with pyproject.toml config (pyproject.toml wins for simple fields)
- Merges requires blocks intelligently
- Logs warnings on conflicts
- Writes context JSON with merged/final values

### Strict Mode (fail on discrepancies)
```bash
psr-prepare --strict
```
→ If addon.xml has conflicting values with pyproject.toml, exits with error instead of warning

---

## Processing Flow

### Command Line Interface

```bash
# Standard run
psr-prepare

# Strict mode (fail on mismatch)
psr-prepare --strict

# Custom config file
psr-prepare --config custom-config.toml
```

### Exit Codes
- `0` - Success
- `1` - Configuration error (missing required fields)
- `2` - File parsing error (malformed XML)
- `3` - Reconciliation error (addon.xml conflicts with config, strict mode)

### Logging Levels
- `INFO` - Processing steps, files written
- `WARNING` - Discrepancies detected (addon.xml vs pyproject.toml)
- `ERROR` - Processing failures, reconciliation failures (strict)

---

## Reconciliation Logic

**pyproject.toml wins** for top-level attributes (id, name, provider-name, description), but requires blocks are merged intelligently.

### Top-Level Attributes

For simple fields like `id`, `name`, `description`:

```
if addon.xml exists:
    parse_xml()

    for each field in pyproject.toml:
        if field exists in XML and differs:
            if --strict:
                ERROR: "addon.xml conflicts with pyproject.toml on <field>"
                exit(3)
            else:
                WARNING: "addon.xml <field> overridden by pyproject.toml"

    # Use pyproject.toml values (these win)
    use(pyproject_toml_attrs)
else:
    # No XML to compare
    use(pyproject_toml_attrs)
```

### Requires Block Merging

For `<requires>` entries, merge intelligently by addon ID:

```
requires_merged = {}

# Start with addon.xml requires
if addon.xml exists:
    for req in xml.requires:
        requires_merged[req.addon] = req.version

# Overlay with pyproject.toml requires
for req in pyproject_toml.requires:
    if req.addon in requires_merged and requires_merged[req.addon] != req.version:
        # Same addon, different versions
        if --strict:
            ERROR: f"addon {req.addon} has conflicting versions"
            exit(3)
        else:
            # Choose higher version (semantic versioning comparison)
            xml_ver = requires_merged[req.addon]
            toml_ver = req.version
            WARNING: f"addon {req.addon}: xml={xml_ver} vs toml={toml_ver}, choosing higher"
            requires_merged[req.addon] = max_version(xml_ver, toml_ver)
    else:
        # New addon or same version
        requires_merged[req.addon] = req.version

# Result: merged list includes all addons from both sources
# with pyproject.toml values preferred, higher versions chosen on conflict
```

### Logging

- `INFO` - Processing steps, files written
- `WARNING` - Attribute discrepancies, version conflicts (when merged)
- `ERROR` - Configuration errors, parsing errors, reconciliation failures (--strict mode)

---

## Local Testing with render_template.py

**Purpose:** Test psr_prepare outputs locally by rendering templates with mocked commits (no git operations).

The `tools/render_template.py` script mimics PSR's rendering behavior using:
- Mocked commit history (phases 0, 1, 2 with different version/release combinations)
- PSR's actual Jinja2 environment and filters
- Auto-discovery of JSON context files (addon.json, changelog.json)

### Usage

**Render all templates to output directory:**
```bash
python tools/render_template.py --template-dir src/arranger/templates --target-dir output
```

**Test psr_prepare output:**
```bash
# First run psr_prepare in your project
psr-prepare

# Then render templates (PSR auto-loads .psr_context/addon.json)
python tools/render_template.py --template-dir templates --target-dir output
```

**Render single template to stdout:**
```bash
python tools/render_template.py --template-dir src/arranger/templates --template CHANGELOG.md.j2
```

**With different mock phase:**
```bash
python tools/render_template.py --template-dir templates --target-dir output --phase 2
```

### Command Options

- `--template-dir` / `-d`: Directory containing .j2 templates (default: `src/arranger/templates`)
- `--target-dir` / `-t`: Output directory for rendered files (if not specified, prints single template to stdout)
- `--template` / `-f`: Render only this specific template (relative path within template-dir)
- `--phase`: Mock release phase `0`/`1`/`2` (default: `0`)
  - Phase 0: v0.1.0 (initial release)
  - Phase 1: v0.1.0 + v0.2.0 (multiple releases)
  - Phase 2: v0.1.0 + v0.2.0 + v1.0.0 (with breaking changes)

### How It Works

1. **Environment Setup:**
   - Creates PSR's Jinja2 environment pointing to `--template-dir`
   - Registers arranger's custom filters
   - Builds mocked release history based on `--phase`

2. **Template Discovery:**
   - Finds all `.j2` files recursively in `--template-dir`
   - If `--template` specified, renders only that file

3. **Rendering:**
   - Renders each template using PSR's ChangelogContext
   - Output paths have `.j2` extension removed
   - Writes to `--target-dir` or stdout

4. **JSON Context Auto-Discovery:**
   - PSR's environment automatically finds and loads JSON files referenced in templates
   - If template contains `{{ addon.id }}`, PSR looks for `.psr_context/addon.json`
   - If template contains `{{ changelog.mode }}`, PSR looks for `.psr_context/changelog.json`
   - No manual configuration needed

### Testing Workflow

**Complete local test of psr_prepare + PSR rendering:**

```bash
# 1. Run psr_prepare in a test project
cd my-kodi-addon/
psr-prepare

# 2. Check generated files
ls -la templates/          # Should show copied templates
ls -la .psr_context/      # Should show addon.json, changelog.json

# 3. Test rendering locally
python /path/to/psr-templates/tools/render_template.py \
  --template-dir templates \
  --target-dir test-output \
  --phase 1  # Test with 2 versions

# 4. Inspect rendered output
cat test-output/addon.xml
cat test-output/CHANGELOG.md

# 5. If rendering succeeds, ready for real PSR run
semantic-release version
```

### Examples

**Testing addon.xml rendering:**
```bash
# Render only the addon template
python tools/render_template.py \
  --template-dir templates \
  --template script.module.example/addon.xml.j2 \
  --phase 2
```

**Testing with source templates:**
```bash
# Test source templates without psr_prepare output
python tools/render_template.py \
  --template-dir src/arranger/templates \
  --target-dir /tmp/rendered \
  --phase 1
```

**Quick verification of single template:**
```bash
# Quick check if CHANGELOG template renders
python tools/render_template.py \
  --template-dir templates \
  --template CHANGELOG.md.j2 \
  --phase 0
```

### Troubleshooting

**Template not found:**
```
No .j2 templates found in {template-dir}
```
→ Check that `--template-dir` contains `.j2` files

**Rendering error with addon context:**
```
Error rendering addon.xml.j2: 'addon' is undefined
```
→ Check that `.psr_context/addon.json` exists when testing psr_prepare output

**Filter not available:**
```
UndefinedError: 'my_filter' is undefined
```
→ Ensure custom filters are registered in `src/arranger/jinja_filters.py`

---

**Workflow:**
1. Run: `psr_prepare` (generates `templates/` and `.psr_context/`)
2. Run: `semantic-release version` (PSR processes)
3. PSR reads templates from `templates/` directory
4. PSR reads context JSON from `.psr_context/`
5. PSR renders templates using context + commit history
6. PSR writes final output files (including `addon.xml`) to repository

**File Flow:**
```
psr_prepare writes:
├── templates/{addon_id}/addon.xml.j2      (Jinja2 template, gitignored)
├── templates/CHANGELOG.md.j2              (Jinja2 template, gitignored)
└── .psr_context/
    ├── addon.json                         (Context data for templates)
    └── changelog.json                     (Context data for templates)

PSR reads:
├── templates/{addon_id}/addon.xml.j2      (renders with addon context)
├── .psr_context/addon.json                (variables available to template)
└── Commit history                         (for changelog context)

PSR writes:
└── {addon_id}/addon.xml                   (final output, committed to repo)
```

**Template Variable Access:**
```jinja
{# In templates/script.module.example/addon.xml.j2 #}
<addon id="{{ addon.id }}" version="{{ latest_release.version }}">
  <extension point="xbmc.addon.metadata">
    <name>{{ addon.name }}</name>
    <summary>{{ addon.summary }}</summary>
    {% for req in addon.requires -%}
    <requires addon="{{ req.addon }}" version="{{ req.version }}" />
    {% endfor -%}
    <news>{{ news }}</news>
  </extension>
</addon>
```

The `addon` object comes from `.psr_context/addon.json`, and `news` is generated by PSR from commit history.

---

## addon.xml Template Details

**Template Location:** `src/arranger/templates/kodi-addons/addon.xml.j2`

**Template Responsibilities:**
- Reference all addon metadata from `addon.json`
- Include version placeholder: `{{ latest_release.version }}`
- Include news placeholder: `<news>{{ news }}</news>`
- Render all other attributes from context

**News Section Handling:**
- If existing addon.xml has `<news>` element: template retains it (psr_prepare preserves content)
- If existing addon.xml lacks `<news>`: psr_prepare inserts empty `<news>{{ news }}</news>` in modified template
- If generating new addon.xml template: always includes news section
- Result: news placeholder always present, PSR fills it in during rendering

**Example Template:**
```jinja
<?xml version="1.0" encoding="utf-8"?>
<addon id="{{ addon.id }}" version="{{ latest_release.version }}" name="{{ addon.name }}" provider-name="{{ addon.provider-name }}">
  <extension point="xbmc.addon.metadata">
    <summary lang="en">{{ addon.summary }}</summary>
    <description lang="en">{{ addon.description }}</description>
    <disclaimer lang="en">{{ addon.disclaimer }}</disclaimer>
    <license>{{ addon.license }}</license>
    <source>{{ addon.source }}</source>
    <assets>
      {%- if addon.assets.icon %}
      <icon>{{ addon.assets.icon }}</icon>
      {%- endif %}
      {%- if addon.assets.fanart %}
      <fanart>{{ addon.assets.fanart }}</fanart>
      {%- endif %}
    </assets>
    {%- for req in addon.requires %}
    <requires addon="{{ req.addon }}" version="{{ req.version }}" />
    {%- endfor %}
    <news>{{ news }}</news>
  </extension>
</addon>
```

All variable references come from `addon.json` context or PSR's built-in variables like `news` and `latest_release`.

---

## Future Considerations

### .gitignore Configuration
- `templates/` directory should be added to `.gitignore` (regenerated each run by psr_prepare)
- `.psr_context/` directory should NOT be gitignored (contains context metadata needed by PSR)
- Only final rendered output (e.g., `addon.xml` in repo root) is committed

### News Section Handling
- psr_prepare ensures news placeholder exists in template
- If existing addon.xml lacks news section, psr_prepare adds it to the template
- PSR fills news placeholder during rendering based on commit history
- News content is PSR-generated; not stored in addon.json

### Extensibility
- Design allows adding more project types (e.g., `python-packages/`)
- Add sections to config, add corresponding templates
- No code changes needed if structure follows pattern

### Custom Attributes
- addon.xml can have custom attributes beyond the standard ones
- Store all parsed attrs in addon.json
- Templates access via: `addon.custom_attr`

### Validation
- Schema validation for pyproject.toml config
- Required field checking
- Warn on unknown config keys

### Dry Run Mode
```bash
psr-prepare --dry-run
```
- Show what would be written, don't write
- Show reconciliation findings
- Useful for debugging

---

## Implementation Phases

### Phase 1 (MVP) - COMPLETE ✓ (With Validation)
- [x] Core config loading from pyproject.toml (`config.py`)
- [x] XML parsing for addon.xml (`addon.py`)
- [x] Warning-level reconciliation (`addon.py`)
- [x] JSON context writing (`context.py`)
- [x] Template mapping (universal + addon) (`templating.py`)
- [x] Basic CLI (`cli.py`)
- [x] Full pipeline validation (psr_prepare → render_template.py → artifacts)

**Status:** Phase 1 implementation VALIDATED AND WORKING END-TO-END.

Package structure:
```
src/psr_prepare/
├── __init__.py       # Package metadata
├── cli.py            # Command entry point (main orchestrator)
├── config.py         # Config loading from pyproject.toml
├── addon.py          # XML parsing and reconciliation
├── context.py        # JSON context generation
└── templating.py     # Template copying and mapping
```

**Features Implemented:**
- Configuration-driven behavior (addon section determines features)
- pyproject.toml as source of truth for addon attributes
- Intelligent requires merging (combines XML + config, chooses higher versions)
- JSON context generation for PSR templates
- Automatic template discovery and copying
- News placeholder insertion in addon.xml.j2
- Comprehensive logging at INFO/WARNING/ERROR levels
- Auto-detection and injection of addon.json context into templates

**Validation Results (Phase 1 Complete):**

**Test Setup:**
- Fixture repo: `/psr-templates-fixture/`
- Test command: `psr-prepare` with config in pyproject.toml
- Render test: `render_template.py` with phase 1 mock releases

**Test Execution Results:**
```
✓ psr-prepare --debug on fixture repo
  - Config loaded: addon.id=script.module.example, changelog.mode=init
  - addon.xml parsed: 3 config overrides detected and logged
  - Reconciliation warnings: correct (name, provider-name, description)
  - Generated: .psr_context/addon.json with merged requires
  - Generated: .psr_context/changelog.json with mode=init, existing=false
  - Copied: universal templates (CHANGELOG.md.j2, DISCOVERY.md.j2)
  - Copied: addon templates (script.module.example/addon.xml.j2)
  - Template news placeholder: auto-inserted in addon.xml.j2

✓ render_template.py --phase 1
  - All 3 templates rendered successfully
  - addon.xml correctly rendered with psr_prepare context:
    - id: "script.module.example" ✓
    - name: "Example Script Module" ✓ (from config override)
    - version: "0.2.0" ✓ (from mock phase 1 release)
    - provider-name: "Example Provider" ✓ (from config override)
    - requires: correctly merged and formatted ✓
    - license: "GPL-2.0-only" ✓
    - description: "A example script module for testing" ✓
  - CHANGELOG.md correctly rendered with mock commit history ✓
  - DISCOVERY.md correctly rendered with context introspection ✓
  - addon.xml news section with Kodi formatting:
    - Release header: "v0.2.0 (2026-02-18)" ✓
    - Tagged commits: "[new] add feature 3", "[fix] resolve another bug" ✓
    - Commit types configurable via news_types in pyproject.toml ✓

✓ Full Pipeline Integration
  - psr_prepare output (templates/ + .psr_context/) correct
  - render_template.py successfully consumes output
  - Final artifacts have correct metadata and structure
  - News formatting complies with Kodi addon.xml standard
  - No data loss or transformation errors

**Kodi News Formatting:**

psr_prepare now supports Kodi-standard news formatting in addon.xml. Configure commit type → label mappings in pyproject.toml:

```toml
[[tool.psr-prepare.changelog.news_types]]
commit_type = "feat"
label = "new"

[[tool.psr-prepare.changelog.news_types]]
commit_type = "fix"
label = "fix"

[[tool.psr-prepare.changelog.news_types]]
commit_type = "perf"
label = "improved"
```

Renders as:
```xml
<news>v1.0.0 (2026-02-18)
  [new] add feature 4
  [improved] improve performance</news>
```

This mapping is:
- Written to .psr_context/changelog.json by psr_prepare
- Loaded by render_template.py during rendering
- Applied to structure commit messages with Kodi-standard [tag] prefixes
- Ordered per configuration

**Critical Fixes Applied During Validation:**
1. Updated `tools/render_template.py` to load addon.json from .psr_context/
2. Auto-expose latest_release from mock release history to templates
3. Map hyphenated keys (addon.provider-name → addon.provider_name) for Jinja2 access
4. Updated addon.xml.j2 template to use psr_prepare context variables
5. Implemented Kodi news formatting with release date and tagged commits
6. Added news_types configuration in psr_prepare for commit type → label mapping
7. Updated render_template.py to load and apply news_types from changelog.json

**Known Limitations (Phase 1):**
- `--strict` flag not yet enforced (validation only, doesn't exit with error)
- No dry-run mode
- Limited error messages (will improve in Phase 2)
- render_template.py is local tool only (not part of psr_prepare package)
- News only includes descriptions (breaking_descriptions not included)

### Phase 2
- [ ] Strict mode (--strict flag with exit codes)
- [ ] Better error messages
- [ ] Dry run mode
- [ ] Extended logging options
- [ ] Configuration validation improvements
- [ ] Extended logging

### Phase 3
- [ ] Schema validation
- [ ] Custom attributes exploration
- [ ] Support for additional project types
- [ ] Advanced reconciliation strategies

---

## Related Documentation

- [Copilot Instructions](../.github/copilot-instructions.md) - Development rules
- [Development Conventions](./development/conventions.md) - Coding standards
- [Architecture](./development/architecture.md) - Project structure
