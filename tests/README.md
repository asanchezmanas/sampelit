# Test Suite - Samplit

Quick reference for running tests.

## Setup

```bash
# Install dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Verify installation
pytest --version
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_auth.py -v

# Specific test class
pytest tests/test_auth.py::TestAuth -v

# Specific test
pytest tests/test_auth.py::TestAuth::test_register_success -v

# With coverage
pytest tests/ --cov=public_api --cov=orchestration --cov-report=html

# Fast (skip slow tests)
pytest tests/ -m "not slow"

# Integration tests only
pytest tests/integration/ -v
```

## Test Files

- `test_auth.py` - Authentication (register, login)
- `test_experiments.py` - Experiment CRUD operations
- `test_blog.py` - Blog markdown rendering
- `test_analytics.py` - Bayesian analysis service

## Coverage Report

After running with `--cov-report=html`, open `htmlcov/index.html` in browser.

## Debugging Failed Tests

```bash
# Show full traceback
pytest tests/ -vv --tb=long

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf
```
