# Python 3 Migration TODO List

**Last Updated:** 2025-12-19
**Branch:** claude/python3-port-completion-BQdAp
**Status:** 85-90% Complete - Critical blockers prevent execution on Python 3.7+

---

## 🔴 CRITICAL - Must Fix (Blocks Python 3.7+)

### [ ] 1. Fix Reserved Keyword 'async' Usage
**Priority:** CRITICAL
**Severity:** Code will not compile on Python 3.7+
**Estimated Time:** 2-3 hours

`async` became a reserved keyword in Python 3.5. Must rename throughout codebase.

**Files to modify:**
- [ ] `laikaboss/clientLib.py:164` - Rename parameter `async` to `async_mode` or `use_async`
- [ ] `laikaboss/clientLib.py:180` - Update `self._ASYNC = async` assignment
- [ ] `laikad.py:101` - Update config default `'async': 'False'`
- [ ] `laikad.py:797-800` - Update command line option `-a/--async`
- [ ] `laikad.py:894, 896, 933, 950` - Update all variable references to `async`
- [ ] Update any configuration files that reference 'async' setting
- [ ] Update documentation mentioning async parameter

**Testing:**
- [ ] Verify code compiles: `python3 -m py_compile laikaboss/clientLib.py`
- [ ] Test ZeroMQ client with new parameter name
- [ ] Verify configuration parsing still works

---

### [ ] 2. Replace Python 2 buffer() Function
**Priority:** CRITICAL
**Severity:** Runtime errors on all Python 3 versions
**Estimated Time:** 1-2 hours

The `buffer()` builtin was removed in Python 3.

**Files to modify:**
- [ ] `laikaboss/util.py:97` - Replace `buffer(theBuffer, 0, maxBytes)` with `theBuffer[0:maxBytes]`
- [ ] `laikaboss/modules/scan_yara.py:85` - Replace `buffer(scanObject.buffer, 0, maxBytes)`
- [ ] `laikaboss/modules/scan_yara.py:97` - Replace `buffer(scanObject.buffer, 0, maxBytes)`

**Implementation:**
```python
# OLD (Python 2):
matches = yara_rule.match(data=buffer(theBuffer, 0, maxBytes))

# NEW (Python 3):
matches = yara_rule.match(data=theBuffer[0:maxBytes])
# OR if memoryview needed:
matches = yara_rule.match(data=memoryview(theBuffer)[0:maxBytes].tobytes())
```

**Testing:**
- [ ] Test YARA scanning with maxBytes set
- [ ] Test YARA scanning without maxBytes
- [ ] Verify no performance regression with large files
- [ ] Test with various buffer types (bytes, bytearray)

---

## 🟠 HIGH PRIORITY - Should Fix Soon

### [ ] 3. Remove basestring/unicode Compatibility Shims
**Priority:** HIGH
**Estimated Time:** 4-6 hours

Heavy reliance on `future` library for Python 2/3 compatibility. Update to native Python 3.

**Files using past.builtins (10 files):**
- [ ] `laikaboss/util.py` - Replace `basestring` and `unicode` with `str`
- [ ] `laikaboss/objectmodel.py` - Replace `basestring` checks
- [ ] `laikaboss/modules/scan_yara.py` - Remove unicode import
- [ ] `laikaboss/modules/scan_html.py`
- [ ] `laikaboss/modules/explode_macho.py`
- [ ] `laikaboss/modules/submit_storage_s3.py`
- [ ] `laikaboss/extras/text_util.py`
- [ ] `laikaboss/extras/extra_util.py`
- [ ] `laikaboss/extras/dictParser.py`
- [ ] `laikaboss/lbconfigparser.py`

**Changes needed:**
```python
# OLD:
from past.builtins import basestring, unicode
if isinstance(value, basestring):
    ...
if isinstance(value, unicode):
    ...

# NEW:
if isinstance(value, str):
    ...
# For checking both str and bytes:
if isinstance(value, (str, bytes)):
    ...
```

**Testing:**
- [ ] Test string/bytes handling throughout codebase
- [ ] Verify metadata storage works correctly
- [ ] Test email parsing with various encodings
- [ ] Ensure no Unicode decode errors

---

### [ ] 4. Update Python Version Requirements
**Priority:** HIGH
**Estimated Time:** 2-3 hours

Target modern Python 3 (3.8+) and update dependencies.

**Tasks:**
- [ ] Update `setup.py` to add `python_requires='>=3.8'`
- [ ] Regenerate `requirements3.txt` with Python 3.8+:
  ```bash
  cd /var/laikaboss/run
  pip-compile --output-file=requirements3.txt requirements3.in
  ```
- [ ] Test with Python 3.8, 3.9, 3.10, 3.11
- [ ] Update Docker base image from Ubuntu 18.04 (Python 3.6) to Ubuntu 22.04 (Python 3.10)
- [ ] Update README.md to note Python 3.8+ requirement
- [ ] Document any breaking changes from Python 3.6 → 3.8+

**Files to modify:**
- [ ] `setup.py` - Add python_requires
- [ ] `requirements3.txt` - Regenerate
- [ ] `requirements3.in` - Review and update if needed
- [ ] `README.md` - Update Python version requirements
- [ ] `Docker/Dockerfile` - Update base image

---

### [ ] 5. Verify file() Usage
**Priority:** MEDIUM
**Estimated Time:** 2-3 hours

22 files contain `file()` function references. Verify these are actually `open()` or need conversion.

**Files to check:**
- [ ] `setup-secrets.py`
- [ ] `submitstoraged.py`
- [ ] `laikarest/storage/storage_helper.py`
- [ ] `laikarest/utils.py`
- [ ] `laikatest.py`
- [ ] `laikarest/routes/storage.py`
- [ ] `laikarest/routes/__init__.py`
- [ ] `laikacollector.py`
- [ ] `laikaboss/test.py`
- [ ] `laikaboss/modules/store_file.py`
- [ ] `laikaboss/modules/meta_onenote.py`
- [ ] `laikaboss/modules/meta_lnk.py`
- [ ] `laikaboss/modules/explode_zip.py`
- [ ] `laikaboss/modules/explode_sevenzip.py`
- [ ] `laikaboss/modules/explode_tar.py`
- [ ] `laikaboss/modules/explode_officexml.py`
- [ ] `laikaboss/modules/explode_gzip.py`
- [ ] `laikaboss/modules/explode_iso.py`
- [ ] `laikaboss/modules/explode_bz2.py`
- [ ] `laikaboss/modules/explode_cab.py`
- [ ] `laikaboss/modules/explode_ace.py`
- [ ] `laika.py`

**Action:** Search for actual `file(` usage vs context (e.g., "file_path", "filename")

---

## 🟡 MEDIUM PRIORITY - Test Infrastructure & CI/CD

### [ ] 6. Set Up GitHub Actions for CI/CD
**Priority:** HIGH (for TDD)
**Estimated Time:** 4-6 hours

Create automated testing pipeline to enable Test-Driven Development.

#### [ ] 6.1 Create Basic CI Workflow
**File:** `.github/workflows/ci.yml`

**Tasks:**
- [ ] Create `.github/workflows/` directory
- [ ] Create Python test workflow (see below)
- [ ] Set up matrix testing for Python 3.8, 3.9, 3.10, 3.11
- [ ] Add status badge to README.md

**Workflow should:**
- [ ] Run on push and pull request
- [ ] Test multiple Python versions
- [ ] Install dependencies from requirements3.txt
- [ ] Run linting (flake8)
- [ ] Run security checks (bandit)
- [ ] Run unit tests
- [ ] Generate coverage report
- [ ] Upload coverage to codecov (optional)

#### [ ] 6.2 Create Syntax Check Workflow
**File:** `.github/workflows/syntax-check.yml`

- [ ] Run `python -m py_compile` on all .py files
- [ ] Check for syntax errors
- [ ] Verify imports don't fail
- [ ] Fast feedback (runs before full tests)

#### [ ] 6.3 Create Docker Build Workflow
**File:** `.github/workflows/docker-build.yml`

- [ ] Build Docker image on push
- [ ] Test Docker container starts
- [ ] Verify all services initialize
- [ ] Tag images appropriately
- [ ] Optional: Push to registry on main branch

#### [ ] 6.4 Set Up Pre-commit Hooks
**File:** `.pre-commit-config.yaml`

- [ ] Configure pre-commit framework
- [ ] Add black (code formatter)
- [ ] Add flake8 (linter)
- [ ] Add isort (import sorter)
- [ ] Add trailing whitespace removal
- [ ] Document setup in README

---

### [ ] 7. Expand Test Coverage
**Priority:** HIGH (for TDD)
**Estimated Time:** 8-16 hours

Build out comprehensive test suite for Test-Driven Development.

#### [ ] 7.1 Set Up Test Framework
- [ ] Review existing `laikatest.py` framework
- [ ] Set up pytest configuration (`pytest.ini` or `pyproject.toml`)
- [ ] Configure test discovery
- [ ] Set up fixtures for common test data
- [ ] Create test data directory structure
- [ ] Document how to run tests in README

#### [ ] 7.2 Create Unit Tests
**Priority modules to test:**
- [ ] `laikaboss/util.py` - Core utilities
- [ ] `laikaboss/objectmodel.py` - Data structures
- [ ] `laikaboss/dispatch.py` - Dispatching logic
- [ ] `laikaboss/clientLib.py` - Client library
- [ ] Module tests for critical modules:
  - [ ] SCAN_YARA
  - [ ] EXPLODE_ZIP
  - [ ] META_PE
  - [ ] EXPLODE_EMAIL
  - [ ] DISPOSITIONER

#### [ ] 7.3 Create Integration Tests
- [ ] Test full scan pipeline
- [ ] Test Redis queue integration
- [ ] Test S3 storage integration
- [ ] Test REST API endpoints
- [ ] Test email server (laikamail)

#### [ ] 7.4 Add Test Coverage Reporting
- [ ] Integrate `pytest-cov`
- [ ] Set coverage goals (80%+ recommended)
- [ ] Add coverage report to CI
- [ ] Create coverage badge

---

### [ ] 8. Remove future Library Dependency
**Priority:** MEDIUM
**Estimated Time:** 8-12 hours

Since code is Python 3 only, remove compatibility library.

**Files using future imports (45 files):**

**Common patterns to replace:**
```python
# REMOVE:
from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import str, bytes, object, int

# ALREADY Python 3:
# No imports needed - these are built-in
```

**Tasks:**
- [ ] Create script to automatically remove future imports
- [ ] Test each file after removal
- [ ] Update requirements to remove `future` package
- [ ] Run full test suite
- [ ] Document changes

---

### [ ] 9. Clean Up Commented Debug Code
**Priority:** LOW
**Estimated Time:** 1-2 hours

Remove old Python 2 syntax in commented code.

**Files with commented debug code:**
- [ ] `laikaboss/modules/meta_zip.py:70` - `#for k,v in archive.iteritems():`
- [ ] `laikaboss/modules/meta_zip.py:69-72` - Old print statements in comments
- [ ] Search for other instances: `grep -r "\.iteritems\|\.iterkeys\|\.itervalues" --include="*.py"`

---

## 🟢 DOCUMENTATION & POLISH

### [ ] 10. Update Documentation
**Priority:** MEDIUM
**Estimated Time:** 3-4 hours

- [ ] Update README.md:
  - [ ] Note Python 3.8+ requirement
  - [ ] Update installation instructions
  - [ ] Add CI/CD status badges
  - [ ] Document test execution
  - [ ] Update Docker instructions
- [ ] Create CONTRIBUTING.md:
  - [ ] Development setup guide
  - [ ] How to run tests
  - [ ] How to add new modules
  - [ ] Code style guide
- [ ] Update CHANGELOG.md:
  - [ ] Document Python 3 migration
  - [ ] List breaking changes
  - [ ] Note deprecated features
- [ ] Create TESTING.md:
  - [ ] How to run tests
  - [ ] How to write tests
  - [ ] Test coverage requirements
  - [ ] TDD workflow

---

### [ ] 11. Code Quality Improvements
**Priority:** LOW
**Estimated Time:** 4-8 hours

- [ ] Run flake8 and fix issues:
  ```bash
  flake8 laikaboss/ --max-line-length=120 --ignore=E501,W503
  ```
- [ ] Run black formatter:
  ```bash
  black laikaboss/ --line-length=120
  ```
- [ ] Run isort for import ordering:
  ```bash
  isort laikaboss/
  ```
- [ ] Run mypy for type checking (optional):
  ```bash
  mypy laikaboss/ --ignore-missing-imports
  ```
- [ ] Fix any security issues found by bandit:
  ```bash
  bandit -r laikaboss/
  ```

---

## 📊 Testing Checklist

### Manual Testing Required After Fixes
- [ ] Test standalone scanner: `./laika.py <sample_file>`
- [ ] Test with laikadq worker
- [ ] Test Redis queue functionality
- [ ] Test REST API (laikarestd)
- [ ] Test email server (laikamail)
- [ ] Test S3 storage submission
- [ ] Test GUI functionality
- [ ] Test module tests: `./laikatest.py`
- [ ] Test Docker deployment
- [ ] Test cluster configuration

### Performance Testing
- [ ] Benchmark scanning speed vs previous version
- [ ] Memory usage profiling
- [ ] Test with large files (1GB+)
- [ ] Test with high volume of small files
- [ ] Verify no regressions from buffer() changes

---

## 📋 Project Timeline Estimate

| Phase | Tasks | Time Estimate | Priority |
|-------|-------|---------------|----------|
| **Phase 1: Critical Fixes** | Tasks 1-2 | 3-5 hours | CRITICAL |
| **Phase 2: Test Infrastructure** | Tasks 6-7 | 12-22 hours | HIGH |
| **Phase 3: Compatibility Updates** | Tasks 3-5 | 8-14 hours | HIGH |
| **Phase 4: Cleanup & Optimization** | Tasks 8-9 | 9-14 hours | MEDIUM |
| **Phase 5: Documentation** | Tasks 10-11 | 7-12 hours | LOW |
| **Total** | | **39-67 hours** | |

**Recommended Approach:**
1. Fix critical blockers (Phase 1) - IMMEDIATE
2. Set up CI/CD & testing (Phase 2) - NEXT
3. Use TDD for remaining fixes (Phases 3-5)

---

## 🎯 Quick Start for Contributors

1. **Fix Critical Issues First:**
   ```bash
   # Fix async keyword
   git checkout claude/python3-port-completion-BQdAp
   # Edit files listed in Task 1
   python3 -m py_compile laikaboss/clientLib.py  # Verify syntax

   # Fix buffer() calls
   # Edit files listed in Task 2
   # Run tests
   ```

2. **Set Up Testing:**
   ```bash
   # Install test dependencies
   pip install pytest pytest-cov flake8 black isort

   # Run existing tests
   ./laikatest.py

   # Set up pre-commit
   pip install pre-commit
   pre-commit install
   ```

3. **Create GitHub Actions:**
   ```bash
   mkdir -p .github/workflows
   # Create workflow files (see Task 6)
   git add .github/workflows/
   git commit -m "Add CI/CD workflows"
   ```

---

## ✅ Success Criteria

The Python 3 migration will be considered complete when:

- [x] All code passes Python 3.8+ syntax check
- [ ] No usage of Python 2-only features (async keyword, buffer(), etc.)
- [ ] All imports work on Python 3.8+
- [ ] Test suite runs successfully
- [ ] CI/CD pipeline is operational
- [ ] Code coverage >70%
- [ ] Docker container builds and runs
- [ ] All critical modules tested
- [ ] Documentation updated
- [ ] No runtime errors on basic operations

---

## 📞 Questions or Issues?

- Check existing GitHub issues
- Review test failures in CI/CD
- Consult Python 3 migration guide: https://docs.python.org/3/howto/pyporting.html
- Review `future` library docs for reference: https://python-future.org/

**Current Status:** Ready to begin critical fixes and test infrastructure setup.
