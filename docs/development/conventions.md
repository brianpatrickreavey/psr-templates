# Conventions

## Coding Conventions

- Use clear, descriptive names for variables, functions, and classes.
- Follow consistent formatting and style guidelines (e.g., PEP 8 for Python).
- Write comprehensive docstrings for all functions and classes.
- Include comments to explain complex logic or decisions.
- Use type hints for function signatures and variable declarations.

## Testing Conventions

- Ensure all code is covered by unit tests with high coverage.
- `black` and `flake8` must pass without errors or warnings.
- Use `pytest` for testing, with clear, descriptive test names.
- Use `mock` for testing external dependencies and side effects.
- Project MUST achieve minimum **95% unit test coverage** (increased from 90% in Phase 5).
- Any use of `# pragma: no cover` must be explicitly approved and documented.
- Use test data and parameterization extensively in tests.
- Favor verbose, readable code over clever or obscure implementations.

## GIT Conventions

Use trunk-based development with feature branches as needed. Use Conventional Commits for commit messages (e.g., `feat: add new feature`, `fix: resolve bug`). Avoid merge commits; rebase feature branches onto main before merging. Ensure all commits are atomic and focused on a single change or feature.

## Phases Overview

The project improvements are structured in 5 phases:

1. **Phase 1**: Error handling & robustness (10 tasks, 22 tests, v0.1.0)
2. **Phase 2**: Edge cases & validation (6 tasks, 8 tests, v0.2.0)
3. **Phase 3**: Type hints & linting (8 tasks, integrated, v1.0.0)
4. **Phase 4**: Code quality & maintainability (8 tasks, 34 tests total, docstrings + refactoring)
5. **Phase 5**: Test coverage & documentation (22 new tests + D4.2-D4.8 docs, 98% coverage, 56 tests total)

See [AUDIT-FINDINGS.md](../../AUDIT-FINDINGS.md) for detailed progress tracking.
