#!/usr/bin/env python3
"""
Check for Kodi project in pyproject.toml and output environment variables.
Usage: python check_kodi.py <path_to_pyproject.toml>
Outputs: is_kodi, kodi_project_name, kodi_directory
"""

import sys
import tomllib
import os

def main():
    if len(sys.argv) != 2:
        print("Usage: python check_kodi.py <path_to_pyproject.toml>", file=sys.stderr)
        sys.exit(1)

    pyproject_path = sys.argv[1]
    try:
        with open(pyproject_path, 'rb') as f:
            config = tomllib.load(f)
    except Exception as e:
        print(f"Error reading {pyproject_path}: {e}", file=sys.stderr)
        sys.exit(1)

    arranger = config.get('tool', {}).get('arranger', {})
    kodi_name = arranger.get('kodi-project-name')

    if kodi_name:
        print(f"is_kodi=true")
        print(f"kodi_project_name={kodi_name}")
        print(f"kodi_directory=kodi-addon-fixture/{kodi_name}")
    else:
        print("is_kodi=false")

if __name__ == "__main__":
    main()