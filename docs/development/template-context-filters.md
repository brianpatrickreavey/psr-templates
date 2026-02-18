# Jinja2 Template Context & Filters Reference

This document maps all available context variables and filters when rendering PSR templates.

## Context Variables

### PSR-Provided Context (`ctx.*`)

| Variable | Type | Availability | Description |
|----------|------|--------------|-------------|
| `ctx.history.released` | dict | Always | All releases with version as key, release data as value |
| `ctx.existing_addon_file` | Path or None | Always | Path to existing addon.xml (None if init mode) |
| `ctx.existing_changelog_file` | Path or None | Always | Path to existing CHANGELOG.md (None if init mode) |
| `ctx.changelog_mode` | string | Always | Either `'init'` or `'update'` mode |

### Release History Structure

Each release in `ctx.history.released[version]` contains:

```python
{
    "version": "0.1.0",                    # Semantic version string
    "tagged_date": datetime,               # When tag was created (datetime object)
    "tagger": str or None,                 # Tagger name
    "committer": str or None,              # Committer name
    "elements": {                          # Commit data grouped by type
        "feat": [                          # Features
            {
                "descriptions": ["Add feature X"],
                "breaking_descriptions": []
            },
            ...
        ],
        "fix": [                           # Bug fixes
            {
                "descriptions": ["Fix bug Y"],
                "breaking_descriptions": []
            },
            ...
        ],
        "perf": [...],                     # Performance improvements
        "docs": [...],                     # Documentation changes
        "refactor": [...],                 # Refactoring
        "test": [...],                     # Test changes
        "chore": [...]                     # Maintenance/chores
    }
}
```

## Built-in Jinja2 Filters

### String Manipulation

| Filter | Syntax | Example | Notes |
|--------|--------|---------|-------|
| `upper` | `str \| upper` | `"hello" \| upper` → `"HELLO"` | Uppercase conversion |
| `lower` | `str \| lower` | `"HELLO" \| lower` → `"hello"` | Lowercase conversion |
| `title` | `str \| title` | `"hello world" \| title` → `"Hello World"` | Title case |
| `capitalize` | `str \| capitalize` | `"hello" \| capitalize` → `"Hello"` | First letter capital |
| `trim` | `str \| trim` | `"  hello  " \| trim` → `"hello"` | Remove whitespace edges |
| `replace(old, new)` | `str \| replace('a','b')` | `"cat" \| replace('a','e')` → `"cet"` | String replacement |
| `indent(width, first=false)` | `str \| indent(4)` | Indent text by N spaces | Common for code blocks |
| `join(sep)` | `list \| join(', ')` | `['a','b'] \| join(', ')` → `"a, b"` | Join with separator |
| `length` | `str \| length` | `"hello" \| length` → `5` | String/list length |
| `reverse` | `str \| reverse` | `"hello" \| reverse` → `"olleh"` | Reverse string |
| `wordwrap(width)` | `str \| wordwrap(10)` | Wrap text at width | Text wrapping |
| `escape` / `e` | `str \| escape` | HTML-escapes special characters | Security: `<` → `&lt;` |
| `striptags` | `str \| striptags` | Remove `<tag>` markup | Strips HTML/XML tags |

### List & Sequence Operations

| Filter | Syntax | Example | Returns |
|--------|--------|---------|---------|
| `list` | `sequence \| list` | `dict.values() \| list` | Convert to list |
| `first` | `list \| first` | `[1,2,3] \| first` → `1` | First element |
| `last` | `list \| last` | `[1,2,3] \| last` → `3` | Last element |
| `length` | `list \| length` | `[1,2,3] \| length` → `3` | Length of list |
| `reverse` | `list \| reverse` | Reverse order | List reversed |
| `sort(attr, reverse)` | `list \| sort(attribute='version', reverse=true)` | Sort by attribute | Sorted list |
| `unique(attr)` | `list \| unique(attribute='id')` | Get unique items | Deduplicated list |
| `join(sep)` | `list \| join(', ')` | Join with separator | String result |
| `slice(slices)` | `list \| slice(3)` | Slice into N groups | List of lists |
| `batch(size)` | `list \| batch(3)` | Group into batches | List of lists |
| `select(test)` | `list \| select('odd')` | Filter matching items | Filtered list |
| `reject(test)` | `list \| reject('even')` | Filter non-matching | Filtered list |
| `selectattr(attr, test)` | `items \| selectattr('active', 'true')` | Filter by attribute | Filtered list |
| `rejectattr(attr, test)` | `items \| rejectattr('archived', 'true')` | Filter by attribute | Filtered list |
| `sum` | `numbers \| sum` | `[1,2,3] \| sum` → `6` | Sum all numbers |
| `min` | `numbers \| min` | `[3,1,2] \| min` → `1` | Minimum value |
| `max` | `numbers \| max` | `[3,1,2] \| max` → `3` | Maximum value |

### Dictionary Operations

| Filter | Syntax | Example | Notes |
|--------|--------|---------|-------|
| `.keys()` | `dict.keys()` | Method call (not filter) | All keys |
| `.values()` | `dict.values() \| list` | Convert values to list | All values |
| `.items()` | `for k, v in dict.items()` | Key-value pairs | For loops |
| `dictsort` | `dict \| dictsort` | Sort by keys | Sorted list of tuples |

### Type Conversion Filters

| Filter | Input | Output | Example |
|--------|-------|--------|---------|
| `int` | string/float | integer | `"42" \| int` → `42` |
| `float` | string/int | float | `"3.14" \| float` → `3.14` |
| `string` | any | string | `42 \| string` → `"42"` |
| `bool` | any | boolean | `"yes" \| bool` → `true` |
| `list` | iterable | list | `dict.values() \| list` |

### Math & Numeric

| Filter | Syntax | Output | Example |
|--------|--------|--------|---------|
| `abs` | `number \| abs` | Absolute value | `-5 \| abs` → `5` |
| `round(precision)` | `float \| round(2)` | Rounded float | `3.14159 \| round(2)` → `3.14` |
| `sum` | `list \| sum` | Total | `[1,2,3] \| sum` → `6` |
| `min` | `list \| min` | Minimum | `[3,1,2] \| min` → `1` |
| `max` | `list \| max` | Maximum | `[3,1,2] \| max` → `3` |

### Special Filters

| Filter | Syntax | Use Case | Notes |
|--------|--------|----------|-------|
| `default(value)` | `var \| default('fallback')` | Provide fallback | If var undefined/none |
| `default(value, boolean=true)` | Force boolean coercion | Treat empty as false | |
| `tojson` | `data \| tojson` | JSON output | Converts to JSON string |
| `truncate(length, end)` | `str \| truncate(10)` | Shorten string | `"hello world" \| truncate(5)` → `"hello..."` |
| `groupby(attr)` | `items \| groupby('type')` | Group by attribute | List of (key, items) tuples |

## Built-in Tests (for `if` conditions)

Use in conditional statements with `is` keyword:

```jinja
{% if variable is test %}
  {# Conditional block #}
{% endif %}
```

| Test | Checks | Example | Returns |
|------|--------|---------|---------|
| `defined` | Variable exists | `if var is defined` | bool |
| `undefined` | Variable does NOT exist | `if var is undefined` | bool |
| `none` | Value is None | `if value is none` | bool |
| `string` | Is a string | `if value is string` | bool |
| `iterable` | Can be iterated | `if value is iterable` | bool |
| `sequence` | Is a sequence (list/tuple) | `if value is sequence` | bool |
| `mapping` | Is dict-like | `if value is mapping` | bool |
| `number` | Is numeric (int/float) | `if value is number` | bool |
| `integer` | Is an integer | `if value is integer` | bool |
| `float` | Is a float | `if value is float` | bool |
| `even` | Number is even | `if num is even` | bool |
| `odd` | Number is odd | `if num is odd` | bool |
| `sameas` | Same object (identity) | `if x is sameas(y)` | bool |
| `equalto(value)` | Value equals | `if x is equalto(5)` | bool |
| `divisibleby(value)` | Divisible by value | `if num is divisibleby(3)` | bool |

## Custom Filters (PSR Templates)

These are registered by `arranger.jinja_filters`:

| Filter | Signature | Purpose | Notes |
|--------|-----------|---------|-------|
| `read_file` | `read_file(path)` | Read file contents | Raises error if missing |
| `read_file_or_empty` | `read_file_or_empty(path)` | Read file safely | Returns "" if missing |
| `file_exists` | `file_exists(path)` | Check file existence | Returns bool |

## Python Methods on Objects

You can call Python methods directly in Jinja2:

```jinja
{# String methods #}
{{ "hello".upper() }}              {# → "HELLO" #}
{{ "  hello  ".strip() }}         {# → "hello" #}

{# Dict methods #}
{{ mydict.get("key", "default") }} {# → value or "default" #}
{{ mydict.keys() | list }}         {# → list of keys #}

{# List methods #}
{{ mylist[0] }}                    {# → first element #}
{{ mylist | length }}              {# → length #}

{# Date/time methods #}
{{ datetime_obj.strftime('%Y-%m-%d') }}  {# → "2024-02-18" #}
```

## Common Filter Chains Used in PSR Templates

### Get sorted release versions (newest first)
```jinja
{%- set sorted_releases = ctx.history.released.values() | list | sort(attribute='version', reverse=True) -%}
```

### Format release date
```jinja
{{ release.tagged_date.strftime('%Y-%m-%d') if release.tagged_date else 'Unreleased' }}
```

### Indent multi-line content
```jinja
{{- content | indent(8) }}
```

### Join list of items with separator
```jinja
{{ release_versions | join(', ') }}
```

### Get first release or default
```jinja
{%- set first = releases | first if releases else none -%}
```

### Filter items by test
```jinja
{%- for feature in release.elements.feat | default([]) -%}
  - {{ feature.descriptions[0] }}
{%- endfor -%}
```

### Conditional with safe default
```jinja
{%- set elements = release.get("elements", {}) if release is mapping else release.elements -%}
```

## Addon.xml Template Use Cases

Since your addon.xml is complex with XML structure, consider:

1. **Preserve metadata with regex/XML parsing** - Read existing file, parse XML, update only `<news>` section while preserving everything else
2. **Use `file_exists` to detect mode** - Check if addon.xml exists to switch init vs update mode
3. **Filter commit types** - Map semantic commit types (feat/fix/perf) → human-readable sections
4. **Escape content safely** - Use `escape` filter for any user-provided content in XML
5. **Indent news content** - Use `indent(8)` to properly format news under XML parent elements

## Example: Complex addon.xml Logic

```jinja
{# Read existing file if it exists #}
{%- if ctx.existing_addon_file and (ctx.existing_addon_file | file_exists) -%}
  {# Update mode: preserve existing, update only <news> #}
  {%- set existing_content = ctx.existing_addon_file | read_file -%}
  {%- set news_content = generate_news(ctx.history.released.values() | first) -%}
  {# Merge: replace <news>...</news> with new content #}
{%- else -%}
  {# Init mode: generate complete addon.xml #}
  {%- set news_content = generate_news(ctx.history.released.values() | first) -%}
  <?xml version="1.0"?>
  <addon>
    <news>{{ news_content | indent(4) }}</news>
  </addon>
{%- endif -%}
```

---

**Last Updated**: 2024-02-18
**Applies To**: PSR Templates with semantic_release integration
