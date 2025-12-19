"""
Unit tests for laikaboss/clientLib.py

Tests client library helper functions. The Client class itself requires
ZMQ and is tested in integration tests.
"""
import pytest
import json


class TestFlagRollup:
    """Tests for the flagRollup function."""

    @pytest.fixture
    def helpers(self):
        """Import helper functions and classes."""
        try:
            from laikaboss.clientLib import flagRollup
            from laikaboss.objectmodel import ScanResult, ScanObject
            return {
                "flagRollup": flagRollup,
                "ScanResult": ScanResult,
                "ScanObject": ScanObject
            }
        except ImportError:
            pytest.skip("laikaboss.clientLib not available")

    def test_empty_result(self, helpers):
        """Test flagRollup with empty result."""
        flagRollup = helpers["flagRollup"]
        ScanResult = helpers["ScanResult"]

        result = ScanResult()
        flags = flagRollup(result)
        assert flags == []

    def test_single_object_flags(self, helpers):
        """Test flagRollup with single object."""
        flagRollup = helpers["flagRollup"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addFlag("FLAG_A")
        obj.addFlag("FLAG_B")
        result.files["uid1"] = obj

        flags = flagRollup(result)
        assert "FLAG_A" in flags
        assert "FLAG_B" in flags

    def test_multiple_objects_flags(self, helpers):
        """Test flagRollup combines flags from multiple objects."""
        flagRollup = helpers["flagRollup"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()

        obj1 = ScanObject(buffer=b"test1", filename="test1.txt")
        obj1.addFlag("FLAG_A")
        result.files["uid1"] = obj1

        obj2 = ScanObject(buffer=b"test2", filename="test2.txt")
        obj2.addFlag("FLAG_B")
        obj2.addFlag("FLAG_C")
        result.files["uid2"] = obj2

        flags = flagRollup(result)
        assert "FLAG_A" in flags
        assert "FLAG_B" in flags
        assert "FLAG_C" in flags

    def test_deduplicates_flags(self, helpers):
        """Test that flagRollup removes duplicates."""
        flagRollup = helpers["flagRollup"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()

        obj1 = ScanObject(buffer=b"test1", filename="test1.txt")
        obj1.addFlag("DUPLICATE_FLAG")
        result.files["uid1"] = obj1

        obj2 = ScanObject(buffer=b"test2", filename="test2.txt")
        obj2.addFlag("DUPLICATE_FLAG")
        result.files["uid2"] = obj2

        flags = flagRollup(result)
        assert flags.count("DUPLICATE_FLAG") == 1

    def test_returns_sorted(self, helpers):
        """Test that flagRollup returns sorted list."""
        flagRollup = helpers["flagRollup"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()
        obj = ScanObject(buffer=b"test", filename="test.txt")
        obj.addFlag("Z_FLAG")
        obj.addFlag("A_FLAG")
        obj.addFlag("M_FLAG")
        result.files["uid1"] = obj

        flags = flagRollup(result)
        assert flags == sorted(flags)


class TestGetRootObject:
    """Tests for the getRootObject function."""

    @pytest.fixture
    def helpers(self):
        """Import helper functions and classes."""
        try:
            from laikaboss.clientLib import getRootObject
            from laikaboss.objectmodel import ScanResult, ScanObject
            return {
                "getRootObject": getRootObject,
                "ScanResult": ScanResult,
                "ScanObject": ScanObject
            }
        except ImportError:
            pytest.skip("laikaboss.clientLib not available")

    def test_get_root_object(self, helpers):
        """Test getting root object from result."""
        getRootObject = helpers["getRootObject"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()
        root = ScanObject(buffer=b"root", filename="root.txt")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        retrieved = getRootObject(result)
        assert retrieved.filename == "root.txt"
        assert retrieved is root


class TestGetScanObjectUID:
    """Tests for the get_scanObjectUID function."""

    @pytest.fixture
    def helpers(self):
        """Import helper functions and classes."""
        try:
            from laikaboss.clientLib import get_scanObjectUID
            from laikaboss.objectmodel import ScanObject
            return {
                "get_scanObjectUID": get_scanObjectUID,
                "ScanObject": ScanObject
            }
        except ImportError:
            pytest.skip("laikaboss.clientLib not available")

    def test_get_uid(self, helpers):
        """Test getting UID from ScanObject."""
        get_scanObjectUID = helpers["get_scanObjectUID"]
        ScanObject = helpers["ScanObject"]

        obj = ScanObject(buffer=b"test", filename="test.txt")
        uid = get_scanObjectUID(obj)

        assert uid == obj.uuid
        assert isinstance(uid, str)


class TestGetAttachmentList:
    """Tests for the getAttachmentList function."""

    @pytest.fixture
    def helpers(self):
        """Import helper functions and classes."""
        try:
            from laikaboss.clientLib import getAttachmentList
            from laikaboss.objectmodel import ScanResult, ScanObject
            return {
                "getAttachmentList": getAttachmentList,
                "ScanResult": ScanResult,
                "ScanObject": ScanObject
            }
        except ImportError:
            pytest.skip("laikaboss.clientLib not available")

    def test_empty_result(self, helpers):
        """Test getAttachmentList with empty result."""
        getAttachmentList = helpers["getAttachmentList"]
        ScanResult = helpers["ScanResult"]

        result = ScanResult()
        attachments = getAttachmentList(result)
        assert attachments == []

    def test_single_root_no_children(self, helpers):
        """Test with single root object and no children."""
        getAttachmentList = helpers["getAttachmentList"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()
        root = ScanObject(buffer=b"root", filename="root.txt", parent="")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        attachments = getAttachmentList(result)
        assert attachments == []

    def test_with_children(self, helpers):
        """Test with root and child objects."""
        getAttachmentList = helpers["getAttachmentList"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()

        # Root object
        root = ScanObject(buffer=b"root", filename="email.eml", parent="")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        # Child attachment
        child = ScanObject(buffer=b"child", filename="attachment.pdf", parent="root_uid")
        result.files["child_uid"] = child

        attachments = getAttachmentList(result)
        assert "attachment.pdf" in attachments

    def test_multiple_children(self, helpers):
        """Test with multiple child objects."""
        getAttachmentList = helpers["getAttachmentList"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()

        # Root object
        root = ScanObject(buffer=b"root", filename="email.eml", parent="")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        # Multiple children
        child1 = ScanObject(buffer=b"child1", filename="doc1.pdf", parent="root_uid")
        result.files["child1_uid"] = child1

        child2 = ScanObject(buffer=b"child2", filename="doc2.docx", parent="root_uid")
        result.files["child2_uid"] = child2

        attachments = getAttachmentList(result)
        assert len(attachments) == 2
        assert "doc1.pdf" in attachments
        assert "doc2.docx" in attachments


class TestGetJSON:
    """Tests for the getJSON function."""

    @pytest.fixture
    def helpers(self):
        """Import helper functions and classes."""
        try:
            from laikaboss.clientLib import getJSON
            from laikaboss.objectmodel import ScanResult, ScanObject
            return {
                "getJSON": getJSON,
                "ScanResult": ScanResult,
                "ScanObject": ScanObject
            }
        except ImportError:
            pytest.skip("laikaboss.clientLib not available")

    def test_returns_valid_json(self, helpers):
        """Test that getJSON returns valid JSON string."""
        getJSON = helpers["getJSON"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult(source="test")

        obj = ScanObject(buffer=b"test", filename="test.txt", order=0)
        result.files["uid1"] = obj
        result.rootUID = "uid1"

        json_str = getJSON(result)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_json_has_source(self, helpers):
        """Test that JSON includes source."""
        getJSON = helpers["getJSON"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult(source="email_scanner")

        obj = ScanObject(buffer=b"test", filename="test.txt", order=0)
        result.files["uid1"] = obj
        result.rootUID = "uid1"

        json_str = getJSON(result)
        parsed = json.loads(json_str)

        assert parsed["source"] == "email_scanner"

    def test_json_has_scan_result(self, helpers):
        """Test that JSON includes scan_result array."""
        getJSON = helpers["getJSON"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult(source="test")

        obj = ScanObject(buffer=b"test", filename="test.txt", order=0)
        obj.addFlag("TEST_FLAG")
        result.files["uid1"] = obj
        result.rootUID = "uid1"

        json_str = getJSON(result)
        parsed = json.loads(json_str)

        assert "scan_result" in parsed
        assert isinstance(parsed["scan_result"], list)
        assert len(parsed["scan_result"]) == 1

    def test_json_excludes_buffer(self, helpers):
        """Test that buffer is excluded from JSON."""
        getJSON = helpers["getJSON"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult(source="test")

        obj = ScanObject(buffer=b"sensitive data", filename="test.txt", order=0)
        result.files["uid1"] = obj
        result.rootUID = "uid1"

        json_str = getJSON(result)
        parsed = json.loads(json_str)

        # Buffer should not be in the result
        for scan_obj in parsed["scan_result"]:
            assert "buffer" not in scan_obj

    def test_multiple_objects_in_order(self, helpers):
        """Test that multiple objects are ordered correctly."""
        getJSON = helpers["getJSON"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult(source="test")

        obj0 = ScanObject(buffer=b"first", filename="first.txt", order=0)
        obj1 = ScanObject(buffer=b"second", filename="second.txt", order=1)
        obj2 = ScanObject(buffer=b"third", filename="third.txt", order=2)

        result.files["uid0"] = obj0
        result.files["uid1"] = obj1
        result.files["uid2"] = obj2
        result.rootUID = "uid0"

        json_str = getJSON(result)
        parsed = json.loads(json_str)

        assert parsed["scan_result"][0]["filename"] == "first.txt"
        assert parsed["scan_result"][1]["filename"] == "second.txt"
        assert parsed["scan_result"][2]["filename"] == "third.txt"


class TestDispositionFromResult:
    """Tests for the dispositionFromResult function."""

    @pytest.fixture
    def helpers(self):
        """Import helper functions and classes."""
        try:
            from laikaboss.clientLib import dispositionFromResult
            from laikaboss.objectmodel import ScanResult, ScanObject
            return {
                "dispositionFromResult": dispositionFromResult,
                "ScanResult": ScanResult,
                "ScanObject": ScanObject
            }
        except ImportError:
            pytest.skip("laikaboss.clientLib not available")

    def test_missing_disposition_returns_error(self, helpers):
        """Test that missing disposition returns ['Error']."""
        dispositionFromResult = helpers["dispositionFromResult"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()
        root = ScanObject(buffer=b"test", filename="test.txt")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        disposition = dispositionFromResult(result)
        assert disposition == ["Error"]

    def test_with_disposition_metadata(self, helpers):
        """Test with proper disposition metadata."""
        dispositionFromResult = helpers["dispositionFromResult"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()
        root = ScanObject(buffer=b"test", filename="test.txt")

        # Add disposition metadata
        root.moduleMetadata["DISPOSITIONER"] = {
            "Disposition": {
                "Matches": ["MALWARE", "SUSPICIOUS"]
            }
        }

        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        disposition = dispositionFromResult(result)
        assert "MALWARE" in disposition
        assert "SUSPICIOUS" in disposition
        # Should be sorted
        assert disposition == sorted(disposition)


class TestFinalDispositionFromResult:
    """Tests for the finalDispositionFromResult function."""

    @pytest.fixture
    def helpers(self):
        """Import helper functions and classes."""
        try:
            from laikaboss.clientLib import finalDispositionFromResult
            from laikaboss.objectmodel import ScanResult, ScanObject
            return {
                "finalDispositionFromResult": finalDispositionFromResult,
                "ScanResult": ScanResult,
                "ScanObject": ScanObject
            }
        except ImportError:
            pytest.skip("laikaboss.clientLib not available")

    def test_missing_disposition_returns_error(self, helpers):
        """Test that missing disposition returns ['Error']."""
        finalDispositionFromResult = helpers["finalDispositionFromResult"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()
        root = ScanObject(buffer=b"test", filename="test.txt")
        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        disposition = finalDispositionFromResult(result)
        assert disposition == ["Error"]

    def test_with_final_disposition(self, helpers):
        """Test with final disposition result."""
        finalDispositionFromResult = helpers["finalDispositionFromResult"]
        ScanResult = helpers["ScanResult"]
        ScanObject = helpers["ScanObject"]

        result = ScanResult()
        root = ScanObject(buffer=b"test", filename="test.txt")

        root.moduleMetadata["DISPOSITIONER"] = {
            "Disposition": {
                "Result": "BLOCK"
            }
        }

        result.files["root_uid"] = root
        result.rootUID = "root_uid"

        disposition = finalDispositionFromResult(result)
        assert disposition == "BLOCK"
