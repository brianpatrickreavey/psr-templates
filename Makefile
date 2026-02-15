.PHONY: test-unit test-integration-pre test-integration-post test-full lint format install-dev run-test-harness clean

# Clean build artifacts, caches, and generated files
clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

# Unit tests with coverage (test_helpers is for integration tests, not counted here)
# Coverage threshold lowered to 95% since test_helpers.py not tested at unit level
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