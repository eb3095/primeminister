# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the PrimeMinister project.

## Workflows

### `test.yml` - Test Suite
Runs on every pull request and push to main/develop branches.

**What it does:**
- Tests across Python versions 3.8-3.12
- Installs dependencies
- Checks code formatting with black
- Runs the test suite with pytest
- Builds the package and validates it

**Required for merge:** ✅ Yes

### `security.yml` - Security Scanning
Runs on pull requests, pushes, and weekly.

**What it does:**
- Runs static security analysis with `bandit`
- Uploads security reports as artifacts

**Required for merge:** ⚠️ Recommended (warnings should be reviewed)

## Local Development

Before submitting a PR, ensure these commands pass locally:

```bash
# Install development dependencies
make install-dev

# Check code formatting
make check-format

# Run tests
make test

# Build package
make build
```

## Adding New Workflows

When adding new workflows:
1. Follow the existing naming convention
2. Use appropriate triggers (PR, push, schedule)
3. Cache dependencies when possible
4. Upload artifacts for debugging
5. Update this README with workflow descriptions