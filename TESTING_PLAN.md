# Laikaboss Testing Strategy Plan

**Created:** 2025-12-19
**Branch:** claude/plan-testing-strategy-EBGxI
**Status:** Planning Phase

---

## Executive Summary

This document outlines a comprehensive testing strategy for Laikaboss to ensure the project works as originally intended after the Python 3 modernization. The plan covers unit tests, integration tests, legacy test migration, and CI/CD enhancements for both local development and GitHub Actions.

---

## 1. Current State Analysis

### 1.1 Existing Test Infrastructure

| Component | Status | Location |
|-----------|--------|----------|
| **Pytest Framework** | Set up, minimal tests | `tests/conftest.py`, `tests/unit/test_example.py` |
| **Legacy Test Framework** | Functional | `laikaboss/test.py`, `laikatest.py` |
| **Legacy Test Cases** | 35 .lbtest files | `tests/*.lbtest` |
| **CI/CD Pipeline** | Configured, requirements commented | `.github/workflows/python-tests.yml` |
| **Code Quality Checks** | Configured | `.github/workflows/code-quality.yml` |

### 1.2 Existing Fixtures (conftest.py)

- `temp_dir` - Temporary directory cleanup
- `sample_buffer` - Generic test data
- `sample_malware_buffer` - EICAR test string
- `sample_zip_file` - Pre-built ZIP archive
- `sample_pdf_buffer` - Minimal valid PDF
- `mock_config` - Mock configuration object

### 1.3 Existing Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.requires_redis` - Redis dependency
- `@pytest.mark.requires_s3` - S3/MinIO dependency
- `@pytest.mark.requires_network` - Network access
- `@pytest.mark.module` - Module-specific tests

### 1.4 Legacy Test Coverage (.lbtest files)

The existing 35 .lbtest files cover:
- **Archive Extraction:** binwalk, 7zip, zip (encrypted/unencrypted)
- **Office Documents:** encrypted Office, OLE, OOXML, RTF
- **Email Processing:** MSG, TNEF, multipart
- **Metadata Extraction:** PDF, EMF, OLE, macros
- **Other Formats:** plist, cryptocurrency patterns, HTML

---

## 2. Testing Strategy Overview

### 2.1 Test Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Docker-based full stack
                    │   (5-10 tests)  │
                    └────────┬────────┘
                   ┌─────────┴─────────┐
                   │ Integration Tests │  ← Component interactions
                   │   (20-30 tests)   │
                   └────────┬──────────┘
          ┌─────────────────┴─────────────────┐
          │           Unit Tests              │  ← Isolated components
          │         (100+ tests)              │
          └───────────────────────────────────┘
```

### 2.2 Testing Goals

1. **Verify Core Functionality** - Object scanning, dispatching, module execution
2. **Validate Python 3 Migration** - No regressions from modernization
3. **Module Coverage** - Test all 78+ scan modules
4. **API Verification** - REST API endpoints function correctly
5. **Performance Baseline** - Establish performance benchmarks
6. **CI/CD Integration** - Automated testing on every push/PR

---

## 3. Unit Testing Plan

### 3.1 Core Module Unit Tests

#### Priority 1: Critical Path (Week 1)

| Module | File | Test Focus | Est. Tests |
|--------|------|------------|------------|
| **Object Model** | `laikaboss/objectmodel.py` | ScanObject, ScanResult, ExternalVars | 15-20 |
| **Dispatcher** | `laikaboss/dispatch.py` | Module dispatching, YARA matching | 10-15 |
| **Utilities** | `laikaboss/util.py` | Hash functions, file type detection | 15-20 |
| **Config** | `laikaboss/config.py` | Configuration loading, defaults | 5-10 |
| **Client Library** | `laikaboss/clientLib.py` | JSON serialization, result handling | 10-15 |

**Test File Structure:**
```
tests/
├── unit/
│   ├── test_objectmodel.py
│   ├── test_dispatch.py
│   ├── test_util.py
│   ├── test_config.py
│   ├── test_clientlib.py
│   └── ...
```

#### Priority 2: Supporting Components (Week 2)

| Module | File | Test Focus | Est. Tests |
|--------|------|------------|------------|
| **Redis Client** | `laikaboss/redisClientLib.py` | Queue operations (mocked) | 10-15 |
| **Storage Utils** | `laikaboss/storage_utils.py` | S3 operations (mocked) | 10-15 |
| **Config Parser** | `laikaboss/lbconfigparser.py` | INI file parsing | 5-10 |
| **Constants** | `laikaboss/constants.py` | Constant definitions | 5 |

### 3.2 Module Unit Tests

For each of the 78+ modules, create focused unit tests:

**Test Template for Scan Modules:**
```python
@pytest.mark.module
class TestModuleName:
    """Unit tests for module_name.py"""

    def test_module_initialization(self):
        """Test module can be imported and initialized."""
        pass

    def test_scan_valid_input(self, sample_buffer):
        """Test scanning valid input produces expected output."""
        pass

    def test_scan_invalid_input(self):
        """Test module handles invalid input gracefully."""
        pass

    def test_scan_metadata_extraction(self):
        """Test correct metadata is extracted."""
        pass
```

#### Module Test Priority

**High Priority (Critical Modules):**
- [ ] `scan_yara.py` - YARA signature matching
- [ ] `explode_zip.py` - ZIP extraction
- [ ] `explode_email.py` - Email parsing
- [ ] `explode_pdf.py` - PDF analysis
- [ ] `meta_pe.py` - PE file metadata
- [ ] `dispositioner.py` - Dispositioning logic

**Medium Priority (Common Modules):**
- [ ] `explode_ole.py` - OLE document handling
- [ ] `explode_officexml.py` - OOXML documents
- [ ] `explode_rar2.py` - RAR extraction
- [ ] `explode_7zip.py` - 7-Zip extraction
- [ ] `meta_email.py` - Email metadata
- [ ] `scan_html.py` - HTML analysis

**Lower Priority (Specialized Modules):**
- All remaining explode_*, meta_*, scan_*, log_* modules

---

## 4. Integration Testing Plan

### 4.1 Component Integration Tests

**Test File:** `tests/integration/test_scan_pipeline.py`

| Test Scenario | Components | Description |
|---------------|------------|-------------|
| **Full Scan Pipeline** | dispatch + modules | Scan file through complete pipeline |
| **Module Chaining** | Multiple modules | Verify parent-child object creation |
| **Flag Propagation** | dispatch + modules | Verify flags propagate correctly |
| **Metadata Aggregation** | modules + clientLib | Verify metadata is collected |
| **Error Handling** | All components | Verify graceful failure handling |

### 4.2 Service Integration Tests

**Test File:** `tests/integration/test_services.py`

| Test Scenario | Services | Marker |
|---------------|----------|--------|
| **Redis Queue** | laikadq + Redis | `@pytest.mark.requires_redis` |
| **S3 Storage** | storage_utils + MinIO | `@pytest.mark.requires_s3` |
| **REST API** | laikarestd + Flask | `@pytest.mark.integration` |

### 4.3 Required Service Fixtures

```python
# tests/conftest.py additions

@pytest.fixture(scope="session")
def redis_client():
    """Provide a Redis client for integration tests."""
    # Connect to test Redis instance or skip

@pytest.fixture(scope="session")
def minio_client():
    """Provide a MinIO client for S3 integration tests."""
    # Connect to test MinIO instance or skip

@pytest.fixture
def test_scan_result():
    """Provide a realistic ScanResult for testing."""
    # Create populated ScanResult object
```

---

## 5. Legacy Test Migration

### 5.1 Strategy: Bridge Approach

Rather than rewriting 35 .lbtest files, create a pytest adapter that runs legacy tests:

**File:** `tests/integration/test_legacy_lbtest.py`

```python
"""
Bridge module to run legacy .lbtest files through pytest.

This allows us to:
1. Run existing tests without modification
2. Get pytest reporting and markers
3. Gradually migrate to pure pytest tests
"""
import pytest
import glob
from laikaboss.test import execute_test, load_one_test

# Discover all .lbtest files
LBTEST_FILES = glob.glob("tests/*.lbtest")

@pytest.mark.module
@pytest.mark.parametrize("lbtest_file", LBTEST_FILES, ids=lambda x: Path(x).stem)
def test_legacy_lbtest(lbtest_file):
    """Run legacy .lbtest file through pytest."""
    test = load_one_test(lbtest_file)
    assert test is not None, f"Failed to load {lbtest_file}"
    result = execute_test(test, verbose=False, test_file=lbtest_file)
    assert result, f"Legacy test failed: {lbtest_file}"
```

### 5.2 Migration Benefits

- Immediate test coverage without rewriting
- Pytest reporting (pass/fail, timing, markers)
- Can gradually convert to pure pytest
- Maintains backward compatibility with laikatest.py

### 5.3 Gradual Migration Path

1. **Phase 1:** Run all .lbtest files through pytest adapter (immediate)
2. **Phase 2:** Convert high-priority tests to pure pytest (as needed)
3. **Phase 3:** Archive deprecated .lbtest files (long-term)

---

## 6. GitHub Actions CI/CD Enhancements

### 6.1 Updated Test Workflow

**File:** `.github/workflows/python-tests.yml` (Updated)

```yaml
name: Python Tests

on:
  push:
    branches: [ main, master, develop, 'claude/**' ]
  pull_request:
    branches: [ main, master, develop ]

jobs:
  # Fast syntax and lint checks
  lint:
    name: Lint & Syntax Check
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'
      - name: Install linting tools
        run: pip install flake8 black isort bandit
      - name: Run critical lint checks
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=dependencies/
      - name: Check formatting
        run: black --check --diff laikaboss/ || true
      - name: Check imports
        run: isort --check-only --diff laikaboss/ || true

  # Unit tests (fast, no external dependencies)
  unit-tests:
    name: Unit Tests - Python ${{ matrix.python-version }}
    runs-on: ubuntu-22.04
    needs: lint
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            build-essential libssl-dev libffi-dev python3-dev \
            libldap2-dev libsasl2-dev libyara-dev libfuzzy-dev \
            libmagic1 libxml2-dev libxslt1-dev
      - name: Install Python dependencies
        run: |
          pip install --upgrade pip setuptools wheel
          pip install pytest pytest-cov pytest-timeout
          pip install -r requirements3.txt
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v -m "unit or not integration" \
            --cov=laikaboss --cov-report=xml --cov-report=term \
            --timeout=60
      - name: Upload coverage
        if: matrix.python-version == '3.10'
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          flags: unit

  # Integration tests (may need Redis, MinIO)
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-22.04
    needs: unit-tests
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      minio:
        image: minio/minio:latest
        ports:
          - 9000:9000
        env:
          MINIO_ROOT_USER: minioadmin
          MINIO_ROOT_PASSWORD: minioadmin
        options: >-
          --health-cmd "curl -f http://localhost:9000/minio/health/live"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y build-essential libssl-dev libffi-dev \
            python3-dev libldap2-dev libsasl2-dev libyara-dev libfuzzy-dev \
            libmagic1 libxml2-dev libxslt1-dev
          pip install --upgrade pip setuptools wheel
          pip install pytest pytest-cov pytest-timeout
          pip install -r requirements3.txt
      - name: Run integration tests
        env:
          REDIS_HOST: localhost
          REDIS_PORT: 6379
          MINIO_ENDPOINT: localhost:9000
          MINIO_ACCESS_KEY: minioadmin
          MINIO_SECRET_KEY: minioadmin
        run: |
          pytest tests/integration/ -v -m "integration" \
            --cov=laikaboss --cov-report=xml --timeout=120

  # Legacy module tests
  legacy-tests:
    name: Legacy Module Tests
    runs-on: ubuntu-22.04
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y build-essential libssl-dev libffi-dev \
            python3-dev libldap2-dev libsasl2-dev libyara-dev libfuzzy-dev \
            libmagic1 libxml2-dev libxslt1-dev
          pip install --upgrade pip setuptools wheel
          pip install -r requirements3.txt
      - name: Run legacy lbtest files
        run: |
          pytest tests/integration/test_legacy_lbtest.py -v \
            --timeout=300 || echo "Some legacy tests may need updating"
```

### 6.2 Local Testing Scripts

**File:** `scripts/run_tests.sh`

```bash
#!/bin/bash
# Convenience script for running tests locally

set -e

case "${1:-all}" in
  unit)
    echo "Running unit tests..."
    pytest tests/unit/ -v -m "unit or not integration"
    ;;
  integration)
    echo "Running integration tests..."
    pytest tests/integration/ -v -m "integration"
    ;;
  legacy)
    echo "Running legacy .lbtest tests..."
    python laikatest.py tests/
    ;;
  coverage)
    echo "Running tests with coverage..."
    pytest tests/ -v --cov=laikaboss --cov-report=html --cov-report=term
    echo "Coverage report: htmlcov/index.html"
    ;;
  all)
    echo "Running all tests..."
    pytest tests/ -v --cov=laikaboss --cov-report=term
    ;;
  *)
    echo "Usage: $0 {unit|integration|legacy|coverage|all}"
    exit 1
    ;;
esac
```

---

## 7. Docker-Based Testing

### 7.1 Test Container Configuration

**File:** `Docker/Dockerfile.test`

```dockerfile
# Test container for running full test suite
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 python3.10-venv python3.10-dev python3-pip \
    build-essential libssl-dev libffi-dev \
    libldap2-dev libsasl2-dev libyara-dev libfuzzy-dev \
    libmagic1 libxml2-dev libxslt1-dev \
    redis-tools curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements3.txt .
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install pytest pytest-cov pytest-timeout && \
    pip3 install -r requirements3.txt

# Copy application
COPY . .

# Install laikaboss in development mode
RUN pip3 install -e .

# Default command runs all tests
CMD ["pytest", "tests/", "-v", "--cov=laikaboss"]
```

### 7.2 Docker Compose for Testing

**File:** `docker-compose.test.yml`

```yaml
version: '3.8'

services:
  # Test runner
  test:
    build:
      context: .
      dockerfile: Docker/Dockerfile.test
    depends_on:
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
    volumes:
      - ./tests:/app/tests:ro
      - ./laikaboss:/app/laikaboss:ro
      - test-results:/app/test-results
    command: >
      pytest tests/ -v
        --cov=laikaboss
        --cov-report=xml:/app/test-results/coverage.xml
        --junitxml=/app/test-results/junit.xml

  # Redis for integration tests
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # MinIO for S3 integration tests
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  test-results:
```

### 7.3 Running Docker Tests

```bash
# Build and run all tests
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Run specific test suite
docker-compose -f docker-compose.test.yml run test pytest tests/unit/ -v

# Get test results
docker cp $(docker-compose -f docker-compose.test.yml ps -q test):/app/test-results ./test-results
```

---

## 8. Implementation Phases

### Phase 1: Foundation (Immediate - 1-2 days)

**Goal:** Enable basic test execution

- [ ] Update `tests/conftest.py` with additional fixtures
- [ ] Create `tests/integration/test_legacy_lbtest.py` adapter
- [ ] Enable requirements installation in CI (uncomment in python-tests.yml)
- [ ] Verify existing .lbtest files run through pytest
- [ ] Create `scripts/run_tests.sh` convenience script

**Deliverables:**
- All 35 legacy tests running in pytest
- CI pipeline executing tests on push

### Phase 2: Core Unit Tests (Week 1)

**Goal:** Test critical path components

- [ ] `tests/unit/test_objectmodel.py` - ScanObject, ScanResult, ExternalVars
- [ ] `tests/unit/test_dispatch.py` - Dispatcher, module selection
- [ ] `tests/unit/test_util.py` - Utility functions
- [ ] `tests/unit/test_config.py` - Configuration handling
- [ ] `tests/unit/test_clientlib.py` - Client library, JSON handling

**Target:** 50+ unit tests, 40%+ code coverage on core modules

### Phase 3: Module Tests (Weeks 2-3)

**Goal:** Test individual scan modules

- [ ] Create test template for modules
- [ ] Test high-priority modules (scan_yara, explode_zip, explode_email, etc.)
- [ ] Test medium-priority modules
- [ ] Generate sample test files for modules without .lbtest coverage

**Target:** All 78+ modules have at least basic tests

### Phase 4: Integration Tests (Week 3)

**Goal:** Test component interactions

- [ ] `tests/integration/test_scan_pipeline.py` - Full scan workflow
- [ ] `tests/integration/test_redis_queue.py` - Redis queue operations
- [ ] `tests/integration/test_s3_storage.py` - S3/MinIO storage
- [ ] `tests/integration/test_rest_api.py` - REST API endpoints
- [ ] Update CI to run integration tests with services

**Target:** 20+ integration tests, services tested

### Phase 5: Docker & E2E (Week 4)

**Goal:** Full stack testing

- [ ] Create `Docker/Dockerfile.test`
- [ ] Create `docker-compose.test.yml`
- [ ] E2E test: File submission through REST API
- [ ] E2E test: Queue processing with laikadq
- [ ] E2E test: Storage submission to MinIO

**Target:** Complete test infrastructure, >70% coverage

---

## 9. Test Data Management

### 9.1 Sample Files

Create a comprehensive test data directory:

```
tests/
├── data/
│   ├── archives/
│   │   ├── simple.zip
│   │   ├── encrypted.zip
│   │   ├── nested.tar.gz
│   │   └── ...
│   ├── documents/
│   │   ├── simple.pdf
│   │   ├── with_macros.docx
│   │   ├── ole_document.doc
│   │   └── ...
│   ├── emails/
│   │   ├── simple.eml
│   │   ├── with_attachments.msg
│   │   ├── tnef_encoded.msg
│   │   └── ...
│   ├── executables/
│   │   ├── simple_pe.exe (benign)
│   │   ├── macho_binary
│   │   └── elf_binary
│   └── malware_samples/
│       └── eicar.txt  # Only EICAR test file
```

### 9.2 Test Data Fixtures

```python
# tests/conftest.py additions

@pytest.fixture
def sample_files_dir():
    """Path to sample test files."""
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_zip(sample_files_dir):
    """Load sample ZIP file."""
    return (sample_files_dir / "archives" / "simple.zip").read_bytes()

@pytest.fixture
def sample_email(sample_files_dir):
    """Load sample email file."""
    return (sample_files_dir / "emails" / "simple.eml").read_bytes()
```

---

## 10. Success Metrics

### 10.1 Coverage Targets

| Phase | Target Coverage | Timeline |
|-------|-----------------|----------|
| Phase 1 | Baseline (legacy tests running) | Day 1-2 |
| Phase 2 | 40% core modules | Week 1 |
| Phase 3 | 60% all modules | Week 2-3 |
| Phase 4 | 70% overall | Week 3 |
| Phase 5 | 80%+ overall | Week 4 |

### 10.2 Test Count Targets

| Category | Target Count |
|----------|--------------|
| Unit Tests | 100+ |
| Module Tests | 150+ (2 per module) |
| Integration Tests | 25+ |
| Legacy Tests (via adapter) | 35 |
| E2E Tests | 5-10 |
| **Total** | **300+** |

### 10.3 CI/CD Success Criteria

- [ ] All tests pass on Python 3.8, 3.9, 3.10, 3.11
- [ ] Tests complete in <10 minutes for unit, <20 minutes for integration
- [ ] Coverage reports uploaded to codecov
- [ ] Test artifacts archived on failure
- [ ] Docker builds succeed after tests pass

---

## 11. Appendix: Quick Reference

### Running Tests Locally

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-timeout

# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v -m "unit"

# Run only integration tests
pytest tests/integration/ -v -m "integration"

# Run with coverage
pytest tests/ --cov=laikaboss --cov-report=html

# Run legacy .lbtest files
python laikatest.py tests/

# Run specific test file
pytest tests/unit/test_objectmodel.py -v

# Run tests matching pattern
pytest tests/ -k "test_scan" -v
```

### Docker Testing

```bash
# Build test container
docker-compose -f docker-compose.test.yml build

# Run all tests in Docker
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

### Debugging Tests

```bash
# Run with verbose output
pytest tests/ -v -s

# Run with debugger on failure
pytest tests/ --pdb

# Run single test with full trace
pytest tests/unit/test_objectmodel.py::TestScanObject::test_init -v --tb=long
```

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-19 | Claude | Initial testing strategy plan |

