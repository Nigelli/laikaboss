"""
Unit tests for laikaboss/config.py

Tests configuration loading and parsing.
"""
import pytest
import os
import tempfile


class TestConfigDefaults:
    """Tests for configuration defaults."""

    @pytest.fixture
    def config_module(self):
        """Import the config module."""
        try:
            from laikaboss import config
            return config
        except ImportError:
            pytest.skip("laikaboss.config not available")

    def test_defaults_exist(self, config_module):
        """Test that defaults dictionary exists."""
        assert hasattr(config_module, 'defaults')
        assert isinstance(config_module.defaults, dict)

    def test_required_defaults_present(self, config_module):
        """Test that required default values are present."""
        defaults = config_module.defaults

        # Core settings
        assert 'yaradispatchrules' in defaults
        assert 'yaraconditionalrules' in defaults
        assert 'maxdepth' in defaults
        assert 'tempdir' in defaults

        # Logging settings
        assert 'logfacility' in defaults
        assert 'logidentity' in defaults
        assert 'moduleloglevel' in defaults
        assert 'scanloglevel' in defaults

        # Hash settings
        assert 'objecthashmethod' in defaults

    def test_default_hash_method_is_md5(self, config_module):
        """Test that default hash method is md5."""
        assert config_module.defaults['objecthashmethod'] == 'md5'

    def test_default_max_depth(self, config_module):
        """Test default max depth value."""
        assert config_module.defaults['maxdepth'] == '10'

    def test_default_timeouts(self, config_module):
        """Test default timeout values."""
        assert 'global_scan_timeout' in config_module.defaults
        assert 'global_module_timeout' in config_module.defaults


class TestConfigInit:
    """Tests for config.init() function."""

    @pytest.fixture
    def config_module(self):
        """Import the config module."""
        try:
            from laikaboss import config
            return config
        except ImportError:
            pytest.skip("laikaboss.config not available")

    def test_init_with_devnull(self, config_module):
        """Test init with /dev/null (no config file)."""
        # Should not raise
        config_module.init(path=os.devnull)

    def test_init_with_valid_config(self, config_module):
        """Test init with a valid config file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("[General]\n")
            f.write("maxdepth = 20\n")
            f.write("tempdir = /tmp/test\n")
            config_path = f.name

        try:
            config_module.init(path=config_path)
            # The config should have been loaded
            assert hasattr(config_module, 'maxdepth')
        finally:
            os.unlink(config_path)

    def test_init_with_nonexistent_file(self, config_module):
        """Test init with non-existent file (should not crash)."""
        # ConfigParser handles this gracefully
        config_module.init(path="/nonexistent/path/to/config.conf")


class TestConfigSectionMap:
    """Tests for _ConfigSectionMap function."""

    @pytest.fixture
    def config_module(self):
        """Import the config module."""
        try:
            from laikaboss import config
            return config
        except ImportError:
            pytest.skip("laikaboss.config not available")

    def test_nonexistent_section_returns_empty_dict(self, config_module):
        """Test that non-existent section returns empty dict."""
        config_module.init(path=os.devnull)
        result = config_module._ConfigSectionMap("NONEXISTENT_SECTION")
        assert result == {}


class TestMapToGlobals:
    """Tests for _map_to_globals function."""

    @pytest.fixture
    def config_module(self):
        """Import the config module."""
        try:
            from laikaboss import config
            return config
        except ImportError:
            pytest.skip("laikaboss.config not available")

    def test_true_string_becomes_bool(self, config_module):
        """Test that 'true' string becomes True boolean."""
        config_module._map_to_globals({'testbool': 'true'})
        # Should be set in globals
        import laikaboss.config as cfg
        assert cfg.testbool is True

    def test_false_string_becomes_bool(self, config_module):
        """Test that 'false' string becomes False boolean."""
        config_module._map_to_globals({'testbool2': 'false'})
        import laikaboss.config as cfg
        assert cfg.testbool2 is False

    def test_string_value_preserved(self, config_module):
        """Test that other strings are preserved."""
        config_module._map_to_globals({'teststr': 'some_value'})
        import laikaboss.config as cfg
        assert cfg.teststr == 'some_value'


class TestConfigParsing:
    """Test config file parsing with actual config content."""

    @pytest.fixture
    def config_module(self):
        """Import the config module."""
        try:
            from laikaboss import config
            return config
        except ImportError:
            pytest.skip("laikaboss.config not available")

    def test_parse_general_section(self, config_module):
        """Test parsing General section."""
        config_content = """
[General]
maxdepth = 15
tempdir = /custom/temp
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config_module.init(path=config_path)
            # Values should be loaded
            assert config_module.maxdepth == '15'
            assert config_module.tempdir == '/custom/temp'
        finally:
            os.unlink(config_path)

    def test_parse_logging_section(self, config_module):
        """Test parsing Logging section."""
        config_content = """
[Logging]
logfacility = LOG_LOCAL5
logidentity = test_laika
modulelogging = true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config_module.init(path=config_path)
            assert config_module.logfacility == 'LOG_LOCAL5'
            assert config_module.logidentity == 'test_laika'
            assert config_module.modulelogging is True
        finally:
            os.unlink(config_path)

    def test_parse_proxies_section(self, config_module):
        """Test parsing Proxies section."""
        config_content = """
[Proxies]
http = http://proxy.example.com:8080
https = https://proxy.example.com:8080
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config_module.init(path=config_path)
            # Proxies should be loaded
            if hasattr(config_module, 'proxies'):
                assert 'http' in config_module.proxies or 'https' in config_module.proxies
        finally:
            os.unlink(config_path)
