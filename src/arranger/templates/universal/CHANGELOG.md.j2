{#
    This changelog template controls which changelog creation occurs
    based on which mode is provided.

    Modes:
        - init: Initialize a full changelog from scratch
        - update: Insert new version details where the placeholder exists in the current changelog

#}{%  set insertion_flag = ctx.changelog_insertion_flag
%}{#  set unreleased_commits = ctx.history.unreleased | dictsort #}

{%- set section_order = ["features", "bug fixes", "performance improvements", "documentation", "continuous integration", "refactoring", "testing", "chores"] -%}
{%- set unreleased_commits = [] -%}
{%- for section in section_order -%}
{%- if section in ctx.history.unreleased -%}
{%- set _ = unreleased_commits.append((section, ctx.history.unreleased[section])) -%}
{%- endif -%}
{%- endfor -%}
{%- for section, commits in ctx.history.unreleased.items() -%}
{%- if section not in section_order -%}
{%- set _ = unreleased_commits.append((section, commits)) -%}
{%- endif -%}
{%- endfor -%}

{%  set releases = ctx.history.released.values() | list
%}{#
#}{%  if ctx.changelog_mode == "init"
%}{%    include ".components/changelog_init.md.j2"
%}{#
#}{%  elif ctx.changelog_mode == "update"
%}{%    set prev_changelog_file = ctx.prev_changelog_file
%}{%    include ".components/changelog_update.md.j2"
%}{#
#}{%  endif
%}
