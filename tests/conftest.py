"""
Shared pytest fixtures and configuration for Laikaboss tests.

This file is automatically loaded by pytest and makes fixtures
available to all test files.
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Ensure laikaboss package is importable
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp(prefix='laikaboss_test_')
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def repo_root():
    """Return the repository root path."""
    return REPO_ROOT


@pytest.fixture
def tests_dir():
    """Return the tests directory path."""
    return REPO_ROOT / "tests"


@pytest.fixture
def sample_files_dir(tests_dir):
    """Return the sample test files directory path."""
    data_dir = tests_dir / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


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


# =============================================================================
# Laikaboss-specific fixtures
# =============================================================================

@pytest.fixture
def lbtest_files(tests_dir):
    """Return list of all .lbtest files in tests directory."""
    return list(tests_dir.glob("*.lbtest"))


@pytest.fixture
def laikaboss_config():
    """
    Provide a minimal laikaboss configuration for testing.

    This initializes laikaboss with a null configuration suitable for testing.
    """
    try:
        import laikaboss.config
        # Initialize with null config (no YARA rules, no external dependencies)
        laikaboss.config.init(path=os.devnull)

        # Override settings for testing
        laikaboss.config.yaradispatchrules = os.devnull
        laikaboss.config.yaraconditionalrules = os.devnull
        laikaboss.config.modulelogging = True
        laikaboss.config.logresultfromsource = ''

        return laikaboss.config
    except ImportError:
        pytest.skip("laikaboss package not installed")


@pytest.fixture
def scan_object():
    """
    Create a ScanObject instance for testing.

    Returns a factory function that creates ScanObjects with given parameters.
    """
    try:
        from laikaboss.objectmodel import ScanObject

        def _create_scan_object(buffer=b"test data", filename="test.txt", **kwargs):
            return ScanObject(
                buffer=buffer,
                filename=filename,
                **kwargs
            )

        return _create_scan_object
    except ImportError:
        pytest.skip("laikaboss package not installed")


@pytest.fixture
def scan_result():
    """
    Create a ScanResult instance for testing.

    Returns a factory function that creates ScanResult objects.
    """
    try:
        from laikaboss.objectmodel import ScanResult
        import time

        def _create_scan_result(source="test", **kwargs):
            result = ScanResult()
            result.source = source
            result.startTime = time.time()
            return result

        return _create_scan_result
    except ImportError:
        pytest.skip("laikaboss package not installed")


@pytest.fixture
def external_vars():
    """
    Create an ExternalVars instance for testing.

    Returns a factory function that creates ExternalVars objects.
    """
    try:
        from laikaboss.objectmodel import ExternalVars

        def _create_external_vars(filename="test.txt", source="test", **kwargs):
            return ExternalVars(
                filename=filename,
                source=source,
                **kwargs
            )

        return _create_external_vars
    except ImportError:
        pytest.skip("laikaboss package not installed")


# =============================================================================
# Service connection fixtures (for integration tests)
# =============================================================================

@pytest.fixture(scope="session")
def redis_available():
    """Check if Redis is available for testing."""
    try:
        import redis
        client = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", 6379)),
            socket_connect_timeout=2
        )
        client.ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def minio_available():
    """Check if MinIO is available for testing."""
    try:
        from minio import Minio
        client = Minio(
            os.environ.get("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
            secure=False
        )
        client.list_buckets()
        return True
    except Exception:
        return False


@pytest.fixture
def redis_client(redis_available):
    """Provide a Redis client for integration tests."""
    if not redis_available:
        pytest.skip("Redis not available")

    import redis
    client = redis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379))
    )
    yield client
    # Cleanup: delete any test keys
    for key in client.keys("laikaboss_test_*"):
        client.delete(key)


@pytest.fixture
def minio_client(minio_available):
    """Provide a MinIO client for integration tests."""
    if not minio_available:
        pytest.skip("MinIO not available")

    from minio import Minio
    client = Minio(
        os.environ.get("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
        secure=False
    )
    return client
