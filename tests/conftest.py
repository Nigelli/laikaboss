"""
Shared pytest fixtures and configuration for Laikaboss tests.

This file is automatically loaded by pytest and makes fixtures
available to all test files.
"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp(prefix='laikaboss_test_')
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_buffer():
    """Provide a sample buffer for testing."""
    return b"This is sample test data for Laikaboss testing"


@pytest.fixture
def sample_malware_buffer():
    """
    Provide a sample 'malware-like' buffer for testing.
    NOTE: This is NOT actual malware, just test data.
    """
    # EICAR test string (harmless malware test signature)
    return b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'


@pytest.fixture
def sample_zip_file(temp_dir):
    """Create a simple ZIP file for testing."""
    import zipfile
    import io

    zip_path = Path(temp_dir) / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("test.txt", "Test content")
        zf.writestr("folder/test2.txt", "More test content")

    with open(zip_path, 'rb') as f:
        return f.read()


@pytest.fixture
def sample_pdf_buffer():
    """Provide a minimal valid PDF for testing."""
    # Minimal PDF structure
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
194
%%EOF"""


@pytest.fixture
def mock_config():
    """Provide a mock configuration object for testing."""
    class MockConfig:
        objecthashmethod = 'md5'
        tempdir = '/tmp'
        logfacility = 'LOG_LOCAL4'
        logidentity = 'laikaboss_test'
        moduleloglevel = 'LOG_DEBUG'
        scanloglevel = 'LOG_INFO'
        logresultfromsource = ['test']

    return MockConfig()


# Skip markers for conditional test execution
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "requires_s3: mark test as requiring S3/MinIO"
    )
    config.addinivalue_line(
        "markers", "requires_network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "module: mark test as a module test"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip tests based on availability of dependencies."""
    import importlib.util

    # Check for Redis
    redis_available = importlib.util.find_spec("redis") is not None

    # Check for boto3/minio (S3)
    s3_available = importlib.util.find_spec("minio") is not None

    for item in items:
        # Skip Redis tests if Redis not available
        if "requires_redis" in item.keywords and not redis_available:
            item.add_marker(pytest.mark.skip(reason="Redis not available"))

        # Skip S3 tests if MinIO not available
        if "requires_s3" in item.keywords and not s3_available:
            item.add_marker(pytest.mark.skip(reason="S3/MinIO not available"))
