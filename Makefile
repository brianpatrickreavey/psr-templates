.PHONY: test-unit test-integration-pre test-integration-post test-full lint format install-dev run-test-harness clean get-test-results coverage-report validate watch-tests build mypy

# Clean build artifacts, caches, and generated files
clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

# Unit tests with coverage (95% threshold for arranger core logic)
test-unit:
	pytest tests/unit/ --cov=arranger --cov-report=term-missing --cov-fail-under=95

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

# Run test harness workflow
run-test-harness:
	gh workflow run --repo brianpatrickreavey/psr-templates dispatch-test-harness.yml \
		-f templates_ref=main \
		-f run_id=gha-test-run-$$(date +%Y%m%d-%H%M%S)

# Watch the latest test harness run in fixture repo
watch-test-harness-output:
	@echo "Finding the latest workflow run in psr-templates-fixture..."
	@RUN_ID=$$(gh run list --repo brianpatrickreavey/psr-templates-fixture --workflow="test-harness.yml" --limit 1 --json databaseId -q '.[0].databaseId'); \
	if [ -z "$$RUN_ID" ]; then \
		echo "No recent runs found."; \
		exit 1; \
	fi; \
	echo "Watching run $$RUN_ID..."; \
	gh run watch --repo brianpatrickreavey/psr-templates-fixture $$RUN_ID

# Get status of the latest test harness run
status-test-harness:
	@echo "Latest test harness run status:"
	@gh run list --repo brianpatrickreavey/psr-templates-fixture --workflow="test-harness.yml" --limit 1

# View logs of the latest test harness run
logs-test-harness:
	@echo "Fetching logs for the latest test harness run..."
	@RUN_ID=$$(gh run list --repo brianpatrickreavey/psr-templates-fixture --workflow="test-harness.yml" --limit 1 --json databaseId -q '.[0].databaseId'); \
	if [ -z "$$RUN_ID" ]; then \
		echo "No recent runs found."; \
		exit 1; \
	fi; \
	gh run view --repo brianpatrickreavey/psr-templates-fixture $$RUN_ID --log
# Download and extract test harness artifacts
get-test-results:
	@echo "Downloading test results from latest releases..."
	@cd ../psr-templates-fixture && rm -rf test-results && mkdir -p test-results && cd test-results && \
	for version in 0.1.0 0.2.0 1.0.0; do \
		mkdir -p "v$$version"; \
		gh release download "v$$version" --repo brianpatrickreavey/psr-templates-fixture --dir "v$$version" --clobber 2>/dev/null || echo "Warning: Could not download v$$version"; \
	done && \
	for version in 0.1.0 0.2.0 1.0.0; do \
		cd "v$$version"; \
		unzip -q "script.module.example-$$version.zip" 2>/dev/null || true; \
		cd ..; \
	done && \
	echo "✓ Test results downloaded to psr-templates-fixture/test-results/" && \
	echo "  v0.1.0/CHANGELOG.md - Release 0.1.0 only" && \
	echo "  v0.2.0/CHANGELOG.md - Releases 0.1.0 + 0.2.0" && \
	echo "  v1.0.0/CHANGELOG.md - All 3 releases cumulative"

# Generate HTML coverage report
coverage-report:
	pytest tests/unit/ --cov=arranger --cov-report=html && \
	echo "✓ Coverage report generated in htmlcov/index.html"

# Run all validation (lint + unit tests)
validate: lint test-unit
	@echo "✓ All validation checks passed"

# Watch tests on file changes (requires pytest-watch)
watch-tests:
	@command -v ptw > /dev/null || (echo "Installing pytest-watch..." && pip install pytest-watch)
	ptw tests/unit/ -- --cov=arranger

# Build distribution package
build: clean
	python -m build

# Run type checking with mypy (once types added in phase 3)
mypy:
	mypy src/arranger tests --strict || echo "Note: mypy checks will be enforced in Phase 3"
