"""
Unit tests for laikaboss/util.py

Tests utility functions that don't require external dependencies.
Functions requiring yara, minio, or syslog are tested separately
in integration tests.
"""
import pytest
import hashlib


# =============================================================================
# Test listToSSV
# =============================================================================

class TestListToSSV:
    """Tests for the listToSSV function."""

    @pytest.fixture
    def list_to_ssv(self):
        """Import and return the listToSSV function."""
        try:
            from laikaboss.util import listToSSV
            return listToSSV
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_basic_list(self, list_to_ssv):
        """Test converting basic list to SSV."""
        result = list_to_ssv(["a", "b", "c"])
        assert result == "a b c"

    def test_single_item(self, list_to_ssv):
        """Test single item list."""
        result = list_to_ssv(["single"])
        assert result == "single"

    def test_empty_list(self, list_to_ssv):
        """Test empty list."""
        result = list_to_ssv([])
        assert result == ""

    def test_list_with_spaces(self, list_to_ssv):
        """Test list items with spaces."""
        result = list_to_ssv(["hello world", "foo bar"])
        assert result == "hello world foo bar"


# =============================================================================
# Test getObjectHash
# =============================================================================

class TestGetObjectHash:
    """Tests for the getObjectHash function."""

    @pytest.fixture
    def get_hash(self):
        """Import and return the getObjectHash function."""
        try:
            from laikaboss.util import getObjectHash
            return getObjectHash
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_basic_hash(self, get_hash):
        """Test basic hash computation."""
        buffer = b"test data"
        result = get_hash(buffer)

        # Verify it's a valid hash (hexadecimal string)
        assert isinstance(result, str)
        assert all(c in "0123456789abcdef" for c in result)

    def test_empty_buffer(self, get_hash):
        """Test hash of empty buffer."""
        result = get_hash(b"")
        # Should produce valid hash of empty string
        expected = hashlib.md5(b"").hexdigest()
        assert result == expected

    def test_consistent_hash(self, get_hash):
        """Test that same input produces same hash."""
        buffer = b"consistent test data"
        result1 = get_hash(buffer)
        result2 = get_hash(buffer)
        assert result1 == result2

    def test_different_data_different_hash(self, get_hash):
        """Test that different data produces different hash."""
        result1 = get_hash(b"data one")
        result2 = get_hash(b"data two")
        assert result1 != result2


# =============================================================================
# Test clean_field
# =============================================================================

class TestCleanField:
    """Tests for the clean_field function."""

    @pytest.fixture
    def clean_field(self):
        """Import and return the clean_field function."""
        try:
            from laikaboss.util import clean_field
            return clean_field
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_basic_string(self, clean_field):
        """Test cleaning basic string."""
        result = clean_field("hello")
        # Should end with delimiter (|)
        assert result.endswith("|")
        assert result.startswith("hello")

    def test_last_field_no_delimiter(self, clean_field):
        """Test last field has no trailing delimiter."""
        result = clean_field("hello", last=True)
        assert not result.endswith("|")
        assert result == "hello"

    def test_replaces_pipe_delimiter(self, clean_field):
        """Test that pipe characters are replaced."""
        result = clean_field("hello|world")
        # Pipe should be replaced with underscore
        assert "|" not in result[:-1]  # Exclude trailing delimiter

    def test_replaces_null_chars(self, clean_field):
        """Test that null characters are replaced."""
        result = clean_field("hello\0world")
        assert "\0" not in result

    def test_list_input(self, clean_field):
        """Test cleaning a list input."""
        result = clean_field(["a", "b", "c"])
        # Should convert list to space-separated
        assert isinstance(result, str)

    def test_integer_input(self, clean_field):
        """Test cleaning integer input."""
        result = clean_field(12345)
        assert "12345" in result

    def test_strips_whitespace(self, clean_field):
        """Test that whitespace is stripped."""
        result = clean_field("  hello  ", last=True)
        assert result == "hello"


# =============================================================================
# Test getRandFill
# =============================================================================

class TestGetRandFill:
    """Tests for the getRandFill function."""

    @pytest.fixture
    def get_rand(self):
        """Import and return the getRandFill function."""
        try:
            from laikaboss.util import getRandFill
            return getRandFill
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_returns_string(self, get_rand):
        """Test that getRandFill returns a string."""
        result = get_rand()
        assert isinstance(result, str)

    def test_length_is_six(self, get_rand):
        """Test that result is 6 characters."""
        result = get_rand()
        assert len(result) == 6

    def test_alphanumeric(self, get_rand):
        """Test that result is alphanumeric."""
        result = get_rand()
        assert result.isalnum()

    def test_randomness(self, get_rand):
        """Test that results are different (with high probability)."""
        results = [get_rand() for _ in range(10)]
        # At least some should be different
        assert len(set(results)) > 1


# =============================================================================
# Test get_module_arguments
# =============================================================================

class TestGetModuleArguments:
    """Tests for the get_module_arguments function."""

    @pytest.fixture
    def get_args(self):
        """Import and return the get_module_arguments function."""
        try:
            from laikaboss.util import get_module_arguments
            return get_module_arguments
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_no_arguments(self, get_args):
        """Test module with no arguments."""
        module, args = get_args("SCAN_YARA")
        assert module == "SCAN_YARA"
        assert args == {}

    def test_single_argument(self, get_args):
        """Test module with single argument."""
        module, args = get_args("SCAN_MODULE(key=value)")
        assert module == "SCAN_MODULE"
        assert args == {"key": "value"}

    def test_multiple_arguments(self, get_args):
        """Test module with multiple arguments."""
        module, args = get_args("SCAN_MODULE(arg1=val1,arg2=val2)")
        assert module == "SCAN_MODULE"
        assert args["arg1"] == "val1"
        assert args["arg2"] == "val2"

    def test_arguments_with_spaces(self, get_args):
        """Test that spaces around arguments are stripped."""
        module, args = get_args("SCAN_MODULE(arg1 = val1, arg2 = val2)")
        assert module == "SCAN_MODULE"
        assert args["arg1"] == "val1"
        assert args["arg2"] == "val2"


# =============================================================================
# Test uniqueList
# =============================================================================

class TestUniqueList:
    """Tests for the uniqueList function."""

    @pytest.fixture
    def unique_list(self):
        """Import and return the uniqueList function."""
        try:
            from laikaboss.util import uniqueList
            return uniqueList
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_removes_duplicates(self, unique_list):
        """Test that duplicates are removed."""
        result = list(unique_list(["a", "b", "a", "c", "b"]))
        assert result == ["a", "b", "c"]

    def test_preserves_order(self, unique_list):
        """Test that order is preserved."""
        result = list(unique_list(["c", "a", "b", "a", "c"]))
        assert result == ["c", "a", "b"]

    def test_empty_list(self, unique_list):
        """Test empty list."""
        result = list(unique_list([]))
        assert result == []

    def test_no_duplicates(self, unique_list):
        """Test list with no duplicates."""
        result = list(unique_list(["a", "b", "c"]))
        assert result == ["a", "b", "c"]

    def test_all_same(self, unique_list):
        """Test list with all same values."""
        result = list(unique_list(["a", "a", "a", "a"]))
        assert result == ["a"]


# =============================================================================
# Test toBool
# =============================================================================

class TestToBool:
    """Tests for the toBool function."""

    @pytest.fixture
    def to_bool(self):
        """Import and return the toBool function."""
        try:
            from laikaboss.util import toBool
            return toBool
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_true_values(self, to_bool):
        """Test values that should return True."""
        for val in ["yes", "YES", "Yes", "true", "TRUE", "True", "on", "ON", "enabled", "1"]:
            assert to_bool(val) is True

    def test_false_values(self, to_bool):
        """Test values that should return False."""
        for val in ["no", "NO", "No", "false", "FALSE", "False", "off", "OFF", "disabled", "0"]:
            assert to_bool(val) is False

    def test_bool_passthrough(self, to_bool):
        """Test that booleans pass through unchanged."""
        assert to_bool(True) is True
        assert to_bool(False) is False

    def test_default_on_invalid(self, to_bool):
        """Test that default is returned for invalid values."""
        assert to_bool("invalid", default=True) is True
        assert to_bool("invalid", default=False) is False

    def test_raises_without_default(self, to_bool):
        """Test that ValueError is raised for invalid value without default."""
        with pytest.raises(ValueError):
            to_bool("invalid")

    def test_none_with_default(self, to_bool):
        """Test None value with default."""
        assert to_bool(None, default=True) is True
        assert to_bool(None, default=False) is False

    def test_whitespace_handling(self, to_bool):
        """Test that whitespace is stripped."""
        assert to_bool("  true  ") is True
        assert to_bool("  false  ") is False


# =============================================================================
# Test get_option
# =============================================================================

class TestGetOption:
    """Tests for the get_option function."""

    @pytest.fixture
    def get_option(self):
        """Import and return the get_option function."""
        try:
            from laikaboss.util import get_option
            return get_option
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_value_from_args(self, get_option):
        """Test getting value from arguments."""
        args = {"mykey": "myvalue"}
        result = get_option(args, "mykey", "configkey")
        assert result == "myvalue"

    def test_default_when_missing(self, get_option):
        """Test default is returned when key is missing."""
        args = {}
        result = get_option(args, "missing", "configkey", default="default_val")
        assert result == "default_val"

    def test_args_takes_precedence(self, get_option):
        """Test that args take precedence over config."""
        args = {"key": "from_args"}
        # Even if config has the key, args should win
        result = get_option(args, "key", "configkey")
        assert result == "from_args"


# =============================================================================
# Test getRootObject and getParentObject
# =============================================================================

class TestResultHelpers:
    """Tests for result helper functions."""

    @pytest.fixture
    def helpers(self):
        """Import helper functions."""
        try:
            from laikaboss.util import getRootObject, getParentObject
            from laikaboss.objectmodel import ScanResult, ScanObject
            return {
                "getRootObject": getRootObject,
                "getParentObject": getParentObject,
                "ScanResult": ScanResult,
                "ScanObject": ScanObject
            }
        except ImportError:
            pytest.skip("laikaboss.util or objectmodel not available")

    def test_get_root_object(self, helpers):
        """Test getting root object from result."""
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]
        getRootObject = helpers["getRootObject"]

        result = ScanResult()
        root = ScanObject(buffer=b"root", filename="root.txt")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        retrieved = getRootObject(result)
        assert retrieved.filename == "root.txt"

    def test_get_parent_object(self, helpers):
        """Test getting parent object."""
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]
        getParentObject = helpers["getParentObject"]

        result = ScanResult()

        # Create parent
        parent = ScanObject(buffer=b"parent", filename="parent.txt")
        result.files["parent_uid"] = parent

        # Create child with parent reference
        child = ScanObject(buffer=b"child", filename="child.txt", parent="parent_uid")
        result.files["child_uid"] = child

        retrieved = getParentObject(result, child)
        assert retrieved.filename == "parent.txt"

    def test_get_parent_of_root_returns_none(self, helpers):
        """Test that getting parent of root returns None."""
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]
        getParentObject = helpers["getParentObject"]

        result = ScanResult()
        root = ScanObject(buffer=b"root", filename="root.txt", parent="")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        retrieved = getParentObject(result, root)
        assert retrieved is None


# =============================================================================
# Test get_scanObjectUID
# =============================================================================

class TestGetScanObjectUID:
    """Tests for get_scanObjectUID function."""

    @pytest.fixture
    def get_uid(self):
        """Import the function."""
        try:
            from laikaboss.util import get_scanObjectUID
            from laikaboss.objectmodel import ScanObject
            return get_scanObjectUID, ScanObject
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_returns_uuid(self, get_uid):
        """Test that UUID is returned."""
        get_scanObjectUID, ScanObject = get_uid
        obj = ScanObject(buffer=b"test", filename="test.txt")
        uid = get_scanObjectUID(obj)
        assert uid == obj.uuid
        assert isinstance(uid, str)


# =============================================================================
# Test get_parent_metadata and get_root_metadata
# =============================================================================

class TestMetadataHelpers:
    """Tests for metadata helper functions."""

    @pytest.fixture
    def helpers(self):
        """Import helper functions."""
        try:
            from laikaboss.util import get_parent_metadata, get_root_metadata
            from laikaboss.objectmodel import ScanResult, ScanObject
            return {
                "get_parent_metadata": get_parent_metadata,
                "get_root_metadata": get_root_metadata,
                "ScanResult": ScanResult,
                "ScanObject": ScanObject
            }
        except ImportError:
            pytest.skip("laikaboss.util not available")

    def test_get_root_metadata_all(self, helpers):
        """Test getting all root metadata."""
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]
        get_root_metadata = helpers["get_root_metadata"]

        result = ScanResult()
        root = ScanObject(buffer=b"root", filename="root.txt")
        root.addMetadata("MODULE_A", "key1", "value1")
        root.addMetadata("MODULE_B", "key2", "value2")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        metadata = get_root_metadata(result)
        assert "MODULE_A" in metadata
        assert "MODULE_B" in metadata

    def test_get_root_metadata_specific_module(self, helpers):
        """Test getting specific module metadata from root."""
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]
        get_root_metadata = helpers["get_root_metadata"]

        result = ScanResult()
        root = ScanObject(buffer=b"root", filename="root.txt")
        root.addMetadata("MODULE_A", "key1", "value1")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        metadata = get_root_metadata(result, "MODULE_A")
        assert metadata == {"key1": "value1"}

    def test_get_parent_metadata(self, helpers):
        """Test getting parent metadata."""
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]
        get_parent_metadata = helpers["get_parent_metadata"]

        result = ScanResult()

        parent = ScanObject(buffer=b"parent", filename="parent.txt")
        parent.addMetadata("PARENT_MODULE", "pkey", "pvalue")
        result.files["parent_uid"] = parent

        child = ScanObject(buffer=b"child", filename="child.txt", parent="parent_uid")
        result.files["child_uid"] = child

        metadata = get_parent_metadata(result, child, "PARENT_MODULE")
        assert metadata == {"pkey": "pvalue"}
