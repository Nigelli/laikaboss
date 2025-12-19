# Laikaboss Test Suite

This directory contains the test suite for Laikaboss using pytest.

## Directory Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for full workflows
├── modules/          # Tests for scan modules
├── fixtures/         # Test data and fixtures
└── conftest.py       # Shared pytest fixtures and configuration
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Module tests only
pytest tests/modules/

# Tests with specific markers
pytest -m unit
pytest -m "not slow"
pytest -m requires_redis
```

### Run with coverage
```bash
# Generate coverage report
pytest --cov=laikaboss --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run specific test file or function
```bash
# Single file
pytest tests/unit/test_util.py

# Single test function
pytest tests/unit/test_util.py::test_getObjectHash

# Tests matching pattern
pytest -k "test_hash"
```

## Writing Tests

### Test File Naming
- Test files must start with `test_` or end with `_test.py`
- Example: `test_objectmodel.py`, `util_test.py`

### Test Function Naming
- Test functions must start with `test_`
- Use descriptive names: `test_getObjectHash_returns_md5_by_default`

### Using Markers
```python
import pytest

@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
@pytest.mark.requires_redis
def test_redis_integration():
    pass

@pytest.mark.slow
def test_large_file_processing():
    pass
```

### Using Fixtures
```python
import pytest

@pytest.fixture
def sample_scanobject():
    from laikaboss.objectmodel import ScanObject
    return ScanObject(buffer=b"test data")

def test_scanobject(sample_scanobject):
    assert sample_scanobject.buffer == b"test data"
```

## Test-Driven Development (TDD) Workflow

1. **Write a failing test** - Before fixing a bug or adding a feature
   ```bash
   # Create test file
   vim tests/unit/test_myfeature.py

   # Run test (should fail)
   pytest tests/unit/test_myfeature.py -v
   ```

2. **Write minimal code** - Make the test pass
   ```bash
   # Edit source code
   vim laikaboss/myfeature.py

   # Run test again
   pytest tests/unit/test_myfeature.py -v
   ```

3. **Refactor** - Improve code while keeping tests passing
   ```bash
   # Refactor and continuously test
   pytest tests/unit/test_myfeature.py -v
   ```

4. **Run full suite** - Ensure no regressions
   ```bash
   pytest
   ```

## Continuous Integration

Tests run automatically on:
- Every push to any branch (syntax check)
- Pull requests (full test suite)
- Main branch merges (full suite + coverage)

See `.github/workflows/` for CI configuration.

## Coverage Goals

- **Overall:** >70%
- **Core modules:** >80%
- **New code:** 100%

Check coverage with:
```bash
pytest --cov=laikaboss --cov-report=term-missing
```

## Troubleshooting

### Tests fail to import laikaboss
```bash
# Install in development mode
pip install -e .
```

### Missing dependencies
```bash
# Install test dependencies
pip install pytest pytest-cov

# Install all dependencies
pip install -r requirements3.txt
```

### Redis/S3 tests failing
```bash
# Skip tests requiring external services
pytest -m "not requires_redis and not requires_s3"
```

## Example Test

```python
# tests/unit/test_util.py
import pytest
from laikaboss import util

class TestGetObjectHash:
    def test_returns_md5_by_default(self):
        buffer = b"test data"
        result = util.getObjectHash(buffer)
        assert len(result) == 32  # MD5 is 32 hex chars

    def test_handles_empty_buffer(self):
        buffer = b""
        result = util.getObjectHash(buffer)
        assert isinstance(result, str)

    @pytest.mark.parametrize("algorithm", ["sha1", "sha256"])
    def test_supports_multiple_algorithms(self, algorithm):
        # Implementation depends on config.objecthashmethod
        pass
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
