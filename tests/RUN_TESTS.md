# Quick Test Runner

Run tests from project root:

```bash
# Set PYTHONPATH and run tests
$env:PYTHONPATH="c:\Users\Artur\sampelit"; pytest tests/test_blog.py -v

# Or use python -m pytest
python -m pytest tests/test_blog.py -v

# Run all tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=public_api --cov=orchestration --cov-report=html
```

## Alternative: Run from Python

```python
# run_tests.py
import subprocess
import sys

result = subprocess.run([
    sys.executable, "-m", "pytest", 
    "tests/", "-v"
], cwd="c:/Users/Artur/sampelit")

sys.exit(result.returncode)
```

Then: `python run_tests.py`
