.PHONY: help install install-dev build clean test format check-format publish publish-test

# Default target
help:
	@echo "PrimeMinister - AI Council Decision System"
	@echo ""
	@echo "Available targets:"
	@echo "  install      Install the package"
	@echo "  install-dev  Install in development mode with dev dependencies"
	@echo "  build        Build distribution packages"
	@echo "  clean        Clean build artifacts"
	@echo "  test         Run tests"

	@echo "  format       Format code with black"
	@echo "  check-format Check code formatting"
	@echo "  publish      Build and publish to PyPI"
	@echo "  publish-test Build and publish to TestPyPI (for testing)"
	@echo "  help         Show this help message"

# Installation targets
install:
	pip install -e src/

install-dev:
	pip install -e src/
	pip install black pytest pytest-asyncio twine setuptools wheel

# Build targets
build: clean
	cd src && python -m build

clean:
	rm -rf src/build/
	rm -rf src/dist/
	rm -rf src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Testing targets
test:
	pytest src/tests/ -v

# Code quality targets
format:
	black src/primeminister/ --line-length=100

check-format:
	black src/primeminister/ --line-length=100 --check

# Quick setup for new users
setup: install
	@echo ""
	@echo "🎉 PrimeMinister installed successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Set up your OpenAI API key:"
	@echo "   primeminister --config"
	@echo ""
	@echo "2. Edit the config file to add your API key"
	@echo ""
	@echo "3. Start using PrimeMinister:"
	@echo "   primeminister"
	@echo "   or"
	@echo "   primeminister 'Your question here'"
	@echo ""

# Development workflow
dev-setup: install-dev
	@echo "Development environment ready!"
	@echo "Run 'make check-format' and 'make test' before committing."

# Publishing targets
publish: build
	@echo "📦 Publishing PrimeMinister to PyPI..."
	@echo "⚠️  Make sure you have set up your PyPI credentials with 'twine configure'"
	@echo ""
	@which twine > /dev/null || (echo "❌ twine not found. Run 'make install-dev' first." && exit 1)
	# Copy license and readme to src directory for packaging
	cp LICENSE src/ 2>/dev/null || echo "⚠️  LICENSE file not found, skipping..."
	cp README.md src/ 2>/dev/null || echo "⚠️  README.md file not found, skipping..."
	# Build and upload
	cd src && python3 -m twine upload dist/*.tar.gz dist/*.whl
	@echo ""
	@echo "✅ Published to PyPI successfully!"
	@echo "🧹 Cleaning up build artifacts..."
	$(MAKE) clean

publish-test: build
	@echo "📦 Publishing PrimeMinister to TestPyPI..."
	@echo "⚠️  Make sure you have set up your TestPyPI credentials"
	@echo ""
	@which twine > /dev/null || (echo "❌ twine not found. Run 'make install-dev' first." && exit 1)
	# Copy license and readme to src directory for packaging
	cp LICENSE src/ 2>/dev/null || echo "⚠️  LICENSE file not found, skipping..."
	cp README.md src/ 2>/dev/null || echo "⚠️  README.md file not found, skipping..."
	# Build and upload to TestPyPI
	cd src && python3 -m twine upload --repository testpypi dist/*.tar.gz dist/*.whl
	@echo ""
	@echo "✅ Published to TestPyPI successfully!"
	@echo "🧹 Cleaning up build artifacts..."
	$(MAKE) clean
	@echo ""
	@echo "To test the TestPyPI package:"
	@echo "  pip install --index-url https://test.pypi.org/simple/ primeminister"
