"""
Unit tests for laikaboss/objectmodel.py

Tests the core object model classes:
- convertToUTF8, ensureNotUnicode, ensureBytes, cleanKey
- ScanObject
- ScanResult
- ExternalVars
- ExternalObject
"""
import pytest
import json
import uuid
import time


# =============================================================================
# Test Utility Functions
# =============================================================================

class TestConvertToUTF8:
    """Tests for the convertToUTF8 function."""

    @pytest.fixture
    def convert_func(self):
        """Import and return the convertToUTF8 function."""
        try:
            from laikaboss.objectmodel import convertToUTF8
            return convertToUTF8
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_bytes_to_string(self, convert_func):
        """Test converting bytes to UTF-8 string."""
        result = convert_func(b"hello world")
        assert result == "hello world"
        assert isinstance(result, str)

    def test_string_passthrough(self, convert_func):
        """Test that strings pass through unchanged."""
        result = convert_func("hello world")
        assert result == "hello world"
        assert isinstance(result, str)

    def test_list_conversion(self, convert_func):
        """Test converting list of bytes to list of strings."""
        result = convert_func([b"hello", b"world"])
        assert result == ["hello", "world"]
        assert all(isinstance(item, str) for item in result)

    def test_tuple_conversion(self, convert_func):
        """Test converting tuple of bytes to tuple of strings."""
        result = convert_func((b"hello", b"world"))
        assert result == ("hello", "world")
        assert isinstance(result, tuple)

    def test_dict_conversion(self, convert_func):
        """Test converting dict with bytes keys/values."""
        result = convert_func({b"key": b"value"})
        assert result == {"key": "value"}

    def test_nested_structure(self, convert_func):
        """Test converting nested data structures."""
        data = {
            b"list": [b"a", b"b"],
            b"nested": {b"key": b"value"}
        }
        result = convert_func(data)
        assert result["list"] == ["a", "b"]
        assert result["nested"]["key"] == "value"

    def test_integer_passthrough(self, convert_func):
        """Test that integers pass through unchanged."""
        assert convert_func(42) == 42
        assert convert_func(0) == 0
        assert convert_func(-1) == -1

    def test_float_passthrough(self, convert_func):
        """Test that floats pass through unchanged."""
        assert convert_func(3.14) == 3.14

    def test_boolean_passthrough(self, convert_func):
        """Test that booleans pass through unchanged."""
        assert convert_func(True) is True
        assert convert_func(False) is False

    def test_uuid_to_string(self, convert_func):
        """Test converting UUID to string."""
        test_uuid = uuid.uuid4()
        result = convert_func(test_uuid)
        assert result == str(test_uuid)
        assert isinstance(result, str)

    def test_bytes_with_invalid_utf8(self, convert_func):
        """Test handling of invalid UTF-8 bytes (should use replacement char)."""
        invalid_bytes = b"\xff\xfe"
        result = convert_func(invalid_bytes)
        assert isinstance(result, str)
        # Should contain replacement characters
        assert "\ufffd" in result or result != ""


class TestEnsureNotUnicode:
    """Tests for the ensureNotUnicode function."""

    @pytest.fixture
    def ensure_func(self):
        """Import and return the ensureNotUnicode function."""
        try:
            from laikaboss.objectmodel import ensureNotUnicode
            return ensureNotUnicode
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_string_to_bytes(self, ensure_func):
        """Test converting string to bytes."""
        result = ensure_func("hello")
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_bytes_passthrough(self, ensure_func):
        """Test that bytes pass through unchanged."""
        result = ensure_func(b"hello")
        assert result == b"hello"
        assert isinstance(result, bytes)


class TestEnsureBytes:
    """Tests for the ensureBytes function."""

    @pytest.fixture
    def ensure_func(self):
        """Import and return the ensureBytes function."""
        try:
            from laikaboss.objectmodel import ensureBytes
            return ensureBytes
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_bytes_passthrough(self, ensure_func):
        """Test that bytes pass through unchanged."""
        result = ensure_func(b"hello")
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_bytearray_to_bytes(self, ensure_func):
        """Test converting bytearray to bytes."""
        result = ensure_func(bytearray(b"hello"))
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_memoryview_to_bytes(self, ensure_func):
        """Test converting memoryview to bytes."""
        result = ensure_func(memoryview(b"hello"))
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_string_to_bytes(self, ensure_func):
        """Test converting string to bytes."""
        result = ensure_func("hello")
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_invalid_type_raises(self, ensure_func):
        """Test that invalid types raise an exception."""
        with pytest.raises(Exception):
            ensure_func(12345)  # Integer should fail

        with pytest.raises(Exception):
            ensure_func(None)  # None should fail


class TestCleanKey:
    """Tests for the cleanKey function."""

    @pytest.fixture
    def clean_func(self):
        """Import and return the cleanKey function."""
        try:
            from laikaboss.objectmodel import cleanKey
            return cleanKey
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_removes_null_chars(self, clean_func):
        """Test that null characters are replaced."""
        result = clean_func("hello\0world")
        assert "\0" not in result
        assert result == "hello_world"

    def test_removes_dots(self, clean_func):
        """Test that dots are replaced."""
        result = clean_func("hello.world")
        assert "." not in result
        assert result == "hello_world"

    def test_removes_dollar(self, clean_func):
        """Test that dollar signs are replaced."""
        result = clean_func("hello$world")
        assert "$" not in result
        assert result == "hello_world"

    def test_multiple_bad_chars(self, clean_func):
        """Test replacing multiple bad characters."""
        result = clean_func("a.b$c\0d")
        assert result == "a_b_c_d"

    def test_clean_key_unchanged(self, clean_func):
        """Test that clean keys pass through unchanged."""
        result = clean_func("clean_key_name")
        assert result == "clean_key_name"


# =============================================================================
# Test ScanObject
# =============================================================================

class TestScanObject:
    """Tests for the ScanObject class."""

    @pytest.fixture
    def ScanObject(self):
        """Import and return the ScanObject class."""
        try:
            from laikaboss.objectmodel import ScanObject
            return ScanObject
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_basic_initialization(self, ScanObject):
        """Test basic ScanObject initialization."""
        obj = ScanObject(buffer=b"test data", filename="test.txt")
        assert obj.buffer == b"test data"
        assert obj.filename == "test.txt"
        assert obj.flags == []
        assert obj.moduleMetadata == {}
        assert obj.scanModules == []

    def test_initialization_with_string_buffer(self, ScanObject):
        """Test ScanObject converts string buffer to bytes."""
        obj = ScanObject(buffer="test data", filename="test.txt")
        assert obj.buffer == b"test data"
        assert isinstance(obj.buffer, bytes)

    def test_add_flag(self, ScanObject):
        """Test adding flags to ScanObject."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addFlag("FLAG_ONE")
        assert "FLAG_ONE" in obj.flags

        obj.addFlag("FLAG_TWO")
        assert "FLAG_ONE" in obj.flags
        assert "FLAG_TWO" in obj.flags

    def test_add_flag_no_duplicates(self, ScanObject):
        """Test that duplicate flags are not added."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addFlag("FLAG_ONE")
        obj.addFlag("FLAG_ONE")
        assert obj.flags.count("FLAG_ONE") == 1

    def test_add_metadata_basic(self, ScanObject):
        """Test adding basic metadata."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addMetadata("MODULE_A", "key1", "value1")

        assert "MODULE_A" in obj.moduleMetadata
        assert obj.moduleMetadata["MODULE_A"]["key1"] == "value1"

    def test_add_metadata_multiple_keys(self, ScanObject):
        """Test adding multiple keys to same module."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addMetadata("MODULE_A", "key1", "value1")
        obj.addMetadata("MODULE_A", "key2", "value2")

        assert obj.moduleMetadata["MODULE_A"]["key1"] == "value1"
        assert obj.moduleMetadata["MODULE_A"]["key2"] == "value2"

    def test_add_metadata_creates_list_on_duplicate(self, ScanObject):
        """Test that adding same key creates a list."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addMetadata("MODULE_A", "key1", "value1")
        obj.addMetadata("MODULE_A", "key1", "value2")

        assert isinstance(obj.moduleMetadata["MODULE_A"]["key1"], list)
        assert "value1" in obj.moduleMetadata["MODULE_A"]["key1"]
        assert "value2" in obj.moduleMetadata["MODULE_A"]["key1"]

    def test_add_metadata_unique_flag(self, ScanObject):
        """Test unique flag prevents duplicates."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addMetadata("MODULE_A", "key1", "value1")
        obj.addMetadata("MODULE_A", "key1", "value1", unique=True)

        # Should not have duplicate
        if isinstance(obj.moduleMetadata["MODULE_A"]["key1"], list):
            assert obj.moduleMetadata["MODULE_A"]["key1"].count("value1") == 1
        else:
            assert obj.moduleMetadata["MODULE_A"]["key1"] == "value1"

    def test_add_metadata_list_value(self, ScanObject):
        """Test adding a list as metadata value."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addMetadata("MODULE_A", "key1", ["a", "b", "c"])

        assert obj.moduleMetadata["MODULE_A"]["key1"] == ["a", "b", "c"]

    def test_get_metadata_existing(self, ScanObject):
        """Test getting existing metadata."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addMetadata("MODULE_A", "key1", "value1")

        result = obj.getMetadata("MODULE_A", "key1")
        assert result == "value1"

    def test_get_metadata_missing_key(self, ScanObject):
        """Test getting non-existent key returns empty string."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addMetadata("MODULE_A", "key1", "value1")

        result = obj.getMetadata("MODULE_A", "nonexistent")
        assert result == ""

    def test_get_metadata_missing_module(self, ScanObject):
        """Test getting metadata for non-existent module returns empty."""
        obj = ScanObject(buffer=b"test", filename="test.txt")

        result = obj.getMetadata("NONEXISTENT")
        assert result == {}

        result = obj.getMetadata("NONEXISTENT", "key")
        assert result == ""

    def test_get_metadata_all_for_module(self, ScanObject):
        """Test getting all metadata for a module."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addMetadata("MODULE_A", "key1", "value1")
        obj.addMetadata("MODULE_A", "key2", "value2")

        result = obj.getMetadata("MODULE_A")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_serialize_minimal_level(self, ScanObject):
        """Test serialization at minimal level."""
        from laikaboss.constants import level_minimal
        obj = ScanObject(buffer=b"test", filename="test.txt", level=level_minimal)
        obj.addMetadata("MODULE_A", "key1", "value1")

        serialized = obj.serialize()
        assert "buffer" not in serialized
        assert "moduleMetadata" not in serialized
        assert serialized["filename"] == "test.txt"

    def test_serialize_metadata_level(self, ScanObject):
        """Test serialization at metadata level."""
        from laikaboss.constants import level_metadata
        obj = ScanObject(buffer=b"test", filename="test.txt", level=level_metadata)

        serialized = obj.serialize()
        assert "buffer" not in serialized
        assert "moduleMetadata" in serialized

    def test_uuid_assigned(self, ScanObject):
        """Test that UUID is assigned on creation."""
        obj = ScanObject(buffer=b"test", filename="test.txt")
        assert obj.uuid is not None
        assert isinstance(obj.uuid, str)


# =============================================================================
# Test ScanResult
# =============================================================================

class TestScanResult:
    """Tests for the ScanResult class."""

    @pytest.fixture
    def ScanResult(self):
        """Import and return the ScanResult class."""
        try:
            from laikaboss.objectmodel import ScanResult
            return ScanResult
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    @pytest.fixture
    def ScanObject(self):
        """Import and return the ScanObject class."""
        try:
            from laikaboss.objectmodel import ScanObject
            return ScanObject
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_basic_initialization(self, ScanResult):
        """Test basic ScanResult initialization."""
        result = ScanResult()
        assert result.files == {}
        assert result.startTime == 0
        assert result.source == ""
        assert result.disposition == ""

    def test_initialization_with_params(self, ScanResult):
        """Test ScanResult initialization with parameters."""
        result = ScanResult(source="test_source", rootUID="uid123", submitID="submit456")
        assert result.source == "test_source"
        assert result.rootUID == "uid123"
        assert result.submitID == "submit456"

    def test_encode_decode_roundtrip(self, ScanResult, ScanObject):
        """Test that encode/decode produces equivalent result."""
        original = ScanResult(source="test", rootUID="root123")
        original.startTime = time.time()

        # Add a scan object
        obj = ScanObject(buffer=b"test data", filename="test.txt")
        original.files["obj1"] = obj
        original.rootUID = "obj1"

        # Encode and decode
        encoded = ScanResult.encode(original)
        assert isinstance(encoded, bytes)

        decoded = ScanResult.decode(encoded)
        assert decoded.source == original.source
        assert decoded.rootUID == original.rootUID

    def test_encode_produces_json(self, ScanResult):
        """Test that encode produces valid JSON."""
        result = ScanResult(source="test")
        result.startTime = time.time()

        encoded = ScanResult.encode(result)
        # Should be valid JSON
        parsed = json.loads(encoded)
        assert parsed["source"] == "test"


# =============================================================================
# Test ExternalVars
# =============================================================================

class TestExternalVars:
    """Tests for the ExternalVars class."""

    @pytest.fixture
    def ExternalVars(self):
        """Import and return the ExternalVars class."""
        try:
            from laikaboss.objectmodel import ExternalVars
            return ExternalVars
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_basic_initialization(self, ExternalVars):
        """Test basic ExternalVars initialization."""
        ext = ExternalVars()
        assert ext.filename == ""
        assert ext.source == ""
        assert ext.depth == 0

    def test_initialization_with_params(self, ExternalVars):
        """Test ExternalVars with parameters."""
        ext = ExternalVars(
            filename="test.txt",
            source="email",
            depth=2,
            submitter="user@example.com"
        )
        assert ext.filename == "test.txt"
        assert ext.source == "email"
        assert ext.depth == 2
        assert ext.submitter == "user@example.com"

    def test_content_type_as_list(self, ExternalVars):
        """Test setting contentType as list."""
        ext = ExternalVars(contentType=["text/plain", "application/pdf"])
        assert ext.contentType == ["text/plain", "application/pdf"]

    def test_content_type_as_string(self, ExternalVars):
        """Test setting contentType as string converts to list."""
        ext = ExternalVars(contentType="text/plain")
        assert ext.contentType == ["text/plain"]

    def test_encode_as_dict(self, ExternalVars):
        """Test encoding ExternalVars as dictionary."""
        ext = ExternalVars(filename="test.txt", source="test")
        encoded = ext.encode(as_dict=True)

        assert isinstance(encoded, dict)
        assert encoded["filename"] == "test.txt"
        assert encoded["source"] == "test"

    def test_encode_as_json(self, ExternalVars):
        """Test encoding ExternalVars as JSON string."""
        ext = ExternalVars(filename="test.txt", source="test")
        encoded = ext.encode(as_dict=False)

        assert isinstance(encoded, str)
        parsed = json.loads(encoded)
        assert parsed["filename"] == "test.txt"

    def test_ext_metadata_as_dict(self, ExternalVars):
        """Test setting extMetaData as dict."""
        ext = ExternalVars(extMetaData={"key": "value"})
        # extMetaData also contains laikaboss_ext for submitter, comment, submitID
        assert "key" in ext.extMetaData
        assert ext.extMetaData["key"] == "value"

    def test_ext_metadata_as_json_string(self, ExternalVars):
        """Test setting extMetaData as JSON string."""
        ext = ExternalVars(extMetaData='{"key": "value"}')
        # extMetaData also contains laikaboss_ext for submitter, comment, submitID
        assert "key" in ext.extMetaData
        assert ext.extMetaData["key"] == "value"

    def test_submitter_in_ext_metadata(self, ExternalVars):
        """Test that submitter is added to extMetaData."""
        ext = ExternalVars(submitter="user@example.com")
        assert "laikaboss_ext" in ext.extMetaData
        assert ext.extMetaData["laikaboss_ext"]["submitter"] == "user@example.com"

    def test_comment_in_ext_metadata(self, ExternalVars):
        """Test that comment is added to extMetaData."""
        ext = ExternalVars(comment="Test comment")
        assert "laikaboss_ext" in ext.extMetaData
        assert ext.extMetaData["laikaboss_ext"]["comment"] == "Test comment"


# =============================================================================
# Test Exception Classes
# =============================================================================

class TestExceptionClasses:
    """Tests for exception classes in objectmodel."""

    def test_scan_error(self):
        """Test ScanError exception."""
        try:
            from laikaboss.objectmodel import ScanError
            with pytest.raises(ScanError):
                raise ScanError("Test error")
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_quit_scan_exception(self):
        """Test QuitScanException."""
        try:
            from laikaboss.objectmodel import QuitScanException
            with pytest.raises(QuitScanException):
                raise QuitScanException("Quit scan")
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_global_scan_timeout_error(self):
        """Test GlobalScanTimeoutError."""
        try:
            from laikaboss.objectmodel import GlobalScanTimeoutError
            with pytest.raises(GlobalScanTimeoutError):
                raise GlobalScanTimeoutError("Timeout")
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")

    def test_global_module_timeout_error(self):
        """Test GlobalModuleTimeoutError."""
        try:
            from laikaboss.objectmodel import GlobalModuleTimeoutError
            with pytest.raises(GlobalModuleTimeoutError):
                raise GlobalModuleTimeoutError("Module timeout")
        except ImportError:
            pytest.skip("laikaboss.objectmodel not available")
