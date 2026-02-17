"""Custom Jinja2 filters for template rendering.

These filters extend Jinja2 with file system operations needed by the templates.
To use in PSR, these must be registered before template rendering.
"""

from pathlib import Path
from typing import Union


def read_file(file_path: Union[str, Path]) -> str:
    """Read file contents, raising an error if file doesn't exist.

    Args:
        file_path: Path to file to read (string or Path object)

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    return Path(file_path).read_text()


def read_file_or_empty(file_path: Union[str, Path]) -> str:
    """Read file contents, returning empty string if file doesn't exist.

    Safe version that gracefully handles missing files.
    Useful for checking if files exist without error handling in templates.

    Args:
        file_path: Path to file to read (string or Path object)

    Returns:
        File contents as string, or empty string if file doesn't exist
    """
    try:
        return Path(file_path).read_text()
    except FileNotFoundError:
        return ""


def file_exists(file_path: Union[str, Path]) -> bool:
    """Check if a file exists.

    Args:
        file_path: Path to file to check (string or Path object)

    Returns:
        True if file exists, False otherwise
    """
    return Path(file_path).exists()


# Export filter dictionary for easy registration with Jinja2 Environment
FILTERS = {
    "read_file": read_file,
    "read_file_or_empty": read_file_or_empty,
    "file_exists": file_exists,
}
