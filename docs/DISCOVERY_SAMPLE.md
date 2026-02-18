# Sample File for DISCOVERY Template Demo

This file demonstrates the `read_file` and `read_file_or_empty` Jinja2 filters.

## How to Use File Reading Filters

### read_file(path) - Safe Read
```jinja
{{ "path/to/file.txt" | read_file }}
```
Reads the file and throws an error if it doesn't exist.

### read_file_or_empty(path) - Graceful Read
```jinja
{{ "path/to/file.txt" | read_file_or_empty }}
```
Reads the file and returns empty string if it doesn't exist.

### file_exists(path) - Check Existence
```jinja
{% if "path/to/file.txt" | file_exists %}
  File exists!
{% endif %}
```
Returns boolean indicating if file exists.

## Real-World Use Cases

- Reading existing CHANGELOG.md to append new entries
- Reading addon.xml to update version numbers in existing files
- Conditionally including documentation based on file existence
- Building update vs init workflows based on what files already exist

## Code Examples

### Python String Operations
```python
# Split by newline
lines = text.split('\n')

# Replace pattern
clean = text.replace('old', 'new')

# Case conversion
upper_text = text.upper()
lower_text = text.lower()
```

### YAML Content
```yaml
version: 1.0.0
author: John Doe
maintainers:
  - name: Jane Smith
    email: jane@example.com
  - name: Bob Jones
    email: bob@example.com
```

### JSON Data
```json
{
  "name": "demo-package",
  "version": "2.5.3",
  "author": {
    "name": "Developer",
    "url": "https://example.com"
  },
  "keywords": ["demo", "template", "jinja2"],
  "engines": {
    "python": ">=3.8"
  }
}
```

### Markdown Changelog Reference
```markdown
# Changelog

## v2.0.0 (2026-02-18)

### Breaking Changes
- Removed deprecated API endpoint
- Changed default configuration path

### Features
- Added new streaming endpoint
- Implemented webhook support

### Bug Fixes
- Fixed memory leak in connection pool
- Corrected timezone calculation

## v1.5.0 (2026-01-15)

### Features
- Added caching layer for improved performance
- Introduced rate limiting configuration

### Bug Fixes
- Resolved SSL certificate validation issues
```

---

This is a demo file to show template file reading and text processing capabilities.
Use this file to test `read_file`, string filtering, and extraction patterns in your templates.
