# Conventions

## Coding Conventions
* Use clear, descriptive names for variables, functions, and classes.
* Follow consistent formatting and style guidelines (e.g., PEP 8 for Python).
* Write comprehensive docstrings for all functions and classes.
* Include comments to explain complex logic or decisions.
* Use type hints for function signatures and variable declarations.

## Testing Conventions
* Ensure all code is covered by unit tests with high coverage.
* `black` and `flake8` must pass without errors or warnings.
* Use `pytest` for testing, with clear, descriptive test names.
* Use `mock` for testing external dependencies and side effects.
* Project MUST achieve minimum 90% unit test coverage (target: 100% by v1.0.0).
* Any use of `# pragma: no cover` must be explicitly approved.
* Use test data and parameterization extensively in tests.
* Favor verbose, readable code over clever or obscure implementations.