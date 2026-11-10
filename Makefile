# Makefile for github-stats project
# Provides targets for updating GitHub Actions and Python dependencies

.PHONY: help update-actions update-actions-dry update-deps check-deps install install-dev sync-reqs clean lint test

# Always use --break-system-packages to handle PEP 668 externally-managed environments
PIP_FLAGS := --break-system-packages

# Default target
help:
	@echo "Available targets:"
	@echo "  update-actions      - Update GitHub Actions to latest versions"
	@echo "  update-actions-dry  - Check for GitHub Actions updates (dry-run)"
	@echo "  update-deps         - Update Python dependencies to latest versions"
	@echo "  check-deps          - Check for outdated Python dependencies"
	@echo "  install             - Install Python dependencies from pyproject.toml"
	@echo "  install-dev         - Install development dependencies"
	@echo "  sync-reqs           - Generate requirements.txt from pyproject.toml (for compatibility)"
	@echo "  clean               - Remove generated files and caches"
	@echo "  lint                - Run linting tools"
	@echo "  test                - Run tests"

# Update GitHub Actions versions in workflow files
update-actions:
	@echo "Updating GitHub Actions versions..."
	python3 scripts/update_actions.py
	@echo "GitHub Actions updated to latest versions"
	@git diff .github/workflows/ || true

# Dry-run for update-actions (show what would change)
update-actions-dry:
	@echo "Checking for GitHub Actions updates (dry-run)..."
	python3 scripts/update_actions.py --dry-run
	@echo "Run 'make update-actions' to apply changes"

# Update Python dependencies
update-deps:
	@echo "Updating Python dependencies..."
	python3 scripts/update_deps.py
	@echo "Dependencies updated"

# Check for outdated dependencies without updating
check-deps:
	@echo "Checking for outdated Python dependencies..."
	python3 scripts/update_deps.py --dry-run --no-sync

# Install Python dependencies from pyproject.toml
install:
	@echo "Installing Python dependencies from pyproject.toml..."
	pip install $(PIP_FLAGS) -e .
	@echo "Dependencies installed"

# Install development dependencies
install-dev:
	@echo "Installing development dependencies..."
	pip install $(PIP_FLAGS) -e ".[dev]"
	@echo "Development dependencies installed"

# Generate requirements.txt from pyproject.toml (for compatibility)
sync-reqs:
	@echo "Generating requirements.txt from pyproject.toml..."
	pip install $(PIP_FLAGS) -e .
	pip freeze | grep -E '^(aiohttp|requests)==' > requirements.txt
	@echo "requirements.txt generated"

# Clean generated files and caches
clean:
	@echo "Cleaning generated files and caches..."
	rm -rf generated/*.svg generated/*.png
	rm -rf __pycache__ */__pycache__ .pytest_cache .mypy_cache
	rm -rf .venv
	rm -f requirements.txt
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "Cleanup complete"

# Lint the code
lint:
	@echo "Running linting..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics 2>/dev/null || true
	black --check . 2>/dev/null || true
	isort --check . 2>/dev/null || true
	@echo "Linting complete"

# Run tests
test:
	@echo "Running tests..."
	@echo "No tests defined yet"
