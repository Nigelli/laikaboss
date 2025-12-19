"""
Legacy .lbtest file adapter for pytest.

This module provides a bridge to run existing .lbtest files through pytest,
allowing us to leverage the existing test suite without rewriting tests.

Benefits:
1. Immediate test coverage from 35+ existing .lbtest files
2. Pytest reporting (pass/fail, timing, markers)
3. Gradual migration path to pure pytest tests
4. Backward compatibility with laikatest.py CLI

Usage:
    # Run all legacy tests
    pytest tests/integration/test_legacy_lbtest.py -v

    # Run specific test file
    pytest tests/integration/test_legacy_lbtest.py -v -k "explode_zip"

    # Run with verbose output
    pytest tests/integration/test_legacy_lbtest.py -v -s
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Ensure laikaboss package is importable
REPO_ROOT = Path(__file__).parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Directory containing .lbtest files
TESTS_DIR = REPO_ROOT / "tests"


def discover_lbtest_files():
    """
    Discover all .lbtest files in the tests directory.

    Returns list of (test_id, file_path) tuples for pytest parametrization.
    """
    lbtest_files = []
    for lbtest_file in sorted(TESTS_DIR.glob("*.lbtest")):
        # Use filename without extension as test ID
        test_id = lbtest_file.stem
        lbtest_files.append((test_id, str(lbtest_file)))
    return lbtest_files


# Discover test files at module load time
LBTEST_FILES = discover_lbtest_files()


def load_lbtest_file(filepath):
    """
    Load a .lbtest file and return the test cases.

    Args:
        filepath: Path to the .lbtest file

    Returns:
        List of test case dictionaries
    """
    with open(filepath, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def laikaboss_test_module():
    """
    Import the laikaboss.test module for running legacy tests.

    This fixture handles the import and provides error handling
    if the module is not available.
    """
    try:
        from laikaboss import test as lb_test
        return lb_test
    except ImportError as e:
        pytest.skip(f"Could not import laikaboss.test: {e}")


@pytest.mark.module
@pytest.mark.integration
class TestLegacyLbtest:
    """
    Run legacy .lbtest files through pytest.

    This class wraps the existing laikaboss test framework to provide
    pytest compatibility and reporting.
    """

    @pytest.mark.parametrize(
        "test_id,lbtest_file",
        LBTEST_FILES,
        ids=[t[0] for t in LBTEST_FILES]
    )
    def test_lbtest_file(self, test_id, lbtest_file, laikaboss_test_module):
        """
        Execute a legacy .lbtest file.

        Args:
            test_id: Human-readable test identifier (filename stem)
            lbtest_file: Path to the .lbtest file
            laikaboss_test_module: The laikaboss.test module fixture
        """
        lb_test = laikaboss_test_module

        # Verify file exists
        assert os.path.isfile(lbtest_file), f"Test file not found: {lbtest_file}"

        # Load test cases from file
        try:
            test_cases = load_lbtest_file(lbtest_file)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {lbtest_file}: {e}")
        except Exception as e:
            pytest.fail(f"Failed to load {lbtest_file}: {e}")

        assert test_cases, f"No test cases found in {lbtest_file}"

        # Execute each test case in the file
        all_passed = True
        failures = []

        for i, test_case in enumerate(test_cases):
            try:
                # Use the existing execute_test function
                result = lb_test.execute_test(
                    test_case,
                    verbose=False,
                    test_file=lbtest_file
                )

                if not result:
                    all_passed = False
                    test_name = test_case.get('name', f'test_{i}')
                    failures.append(test_name)

            except Exception as e:
                all_passed = False
                test_name = test_case.get('name', f'test_{i}')
                failures.append(f"{test_name}: {str(e)}")

        # Report results
        if not all_passed:
            failure_msg = "\n".join(f"  - {f}" for f in failures)
            pytest.fail(f"Legacy test failures in {test_id}:\n{failure_msg}")


class TestLegacyTestFramework:
    """
    Tests for the legacy test framework itself.

    These tests verify that the laikaboss.test module is working correctly.
    """

    def test_import_laikaboss_test(self):
        """Verify laikaboss.test module can be imported."""
        try:
            from laikaboss import test as lb_test
            assert hasattr(lb_test, 'execute_test')
            assert hasattr(lb_test, 'load_one_test')
            assert hasattr(lb_test, 'scan')
        except ImportError:
            pytest.skip("laikaboss.test not available")

    def test_lbtest_files_exist(self):
        """Verify that .lbtest files exist in the tests directory."""
        lbtest_files = list(TESTS_DIR.glob("*.lbtest"))
        assert len(lbtest_files) > 0, "No .lbtest files found in tests directory"

    def test_lbtest_files_valid_json(self):
        """Verify all .lbtest files contain valid JSON."""
        for lbtest_file in TESTS_DIR.glob("*.lbtest"):
            try:
                with open(lbtest_file, "r") as f:
                    data = json.load(f)
                assert isinstance(data, list), f"{lbtest_file.name} should contain a list"
                assert len(data) > 0, f"{lbtest_file.name} should have at least one test"
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {lbtest_file.name}: {e}")

    @pytest.mark.parametrize(
        "test_id,lbtest_file",
        LBTEST_FILES[:3] if len(LBTEST_FILES) >= 3 else LBTEST_FILES,
        ids=[t[0] for t in (LBTEST_FILES[:3] if len(LBTEST_FILES) >= 3 else LBTEST_FILES)]
    )
    def test_lbtest_file_structure(self, test_id, lbtest_file):
        """Verify .lbtest files have expected structure."""
        test_cases = load_lbtest_file(lbtest_file)

        for i, test_case in enumerate(test_cases):
            # Required fields
            assert 'data' in test_case, f"Test {i} missing 'data' field"
            assert 'result' in test_case, f"Test {i} missing 'result' field"

            # Optional but common fields
            if 'name' in test_case:
                assert isinstance(test_case['name'], str)

            if 'filename' in test_case:
                assert isinstance(test_case['filename'], str)


# =============================================================================
# Standalone test execution
# =============================================================================

if __name__ == "__main__":
    # Allow running this file directly for debugging
    pytest.main([__file__, "-v", "-s"])
