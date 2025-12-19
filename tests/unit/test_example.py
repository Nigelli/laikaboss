"""
Example unit tests demonstrating test structure and best practices.

This file can be used as a template for writing new tests.
Delete or modify this file as the real test suite is developed.
"""
import pytest


class TestExampleBasics:
    """Example test class demonstrating basic pytest usage."""

    def test_simple_assertion(self):
        """Simple assertion test."""
        assert 1 + 1 == 2

    def test_string_operations(self):
        """Test string operations."""
        text = "laikaboss"
        assert text.upper() == "LAIKABOSS"
        assert len(text) == 9

    @pytest.mark.parametrize("input,expected", [
        (b"hello", 5),
        (b"", 0),
        (b"test data", 9),
    ])
    def test_buffer_length(self, input, expected):
        """Parametrized test example."""
        assert len(input) == expected


class TestExampleFixtures:
    """Example tests using fixtures."""

    def test_sample_buffer(self, sample_buffer):
        """Test using sample_buffer fixture."""
        assert isinstance(sample_buffer, bytes)
        assert len(sample_buffer) > 0

    def test_temp_dir(self, temp_dir):
        """Test using temp_dir fixture."""
        import os
        assert os.path.isdir(temp_dir)


@pytest.mark.slow
class TestExampleSlowTests:
    """Example of marking tests as slow."""

    def test_slow_operation(self):
        """This test would be skipped with: pytest -m "not slow" """
        import time
        time.sleep(0.1)  # Simulate slow operation
        assert True


# Example of testing exceptions
def test_exception_handling():
    """Test that exceptions are raised correctly."""
    with pytest.raises(ValueError):
        raise ValueError("Expected error")


# Example of skipping tests
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    """This test will be skipped."""
    pass


# Example of conditional skip
@pytest.mark.skipif(True, reason="Example of conditional skip")
def test_conditional_feature():
    """This test is conditionally skipped."""
    pass
