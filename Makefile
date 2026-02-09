.PHONY: test-unit test-integration-pre test-integration-post test-full lint format

# Unit tests with coverage
test-unit:
	pytest tests/unit/ --cov=arranger --cov-report=term-missing --cov-fail-under=100

# Pre-PSR integration tests
test-integration-pre:
	pytest tests/integration/pre_psr/ -v

# Post-PSR integration tests (with mocks)
test-integration-post:
	pytest tests/integration/post_psr/ -v

# Full test suite
test-full: test-unit test-integration-pre test-integration-post

# Linting
lint:
	flake8 arranger tests
	black --check arranger tests

# Formatting
format:
	black arranger tests

# Install dev dependencies
install-dev:
	uv sync --group dev