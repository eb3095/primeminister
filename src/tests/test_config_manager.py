"""
Tests for ConfigManager functionality.
"""
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from primeminister.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""

    @pytest.fixture
    def config_manager(self):
        """Create a ConfigManager instance for testing."""
        return ConfigManager()

    @pytest.fixture
    def sample_config(self):
        """Sample configuration data for testing."""
        return {
            "openai_key": "test_key_123",
            "api_url": "https://api.openai.com/v1",
            "mode": "council",
            "council": [
                {
                    "model": "gpt-4",
                    "personality": "Test personality",
                    "voter": True,
                    "silent": False
                }
            ]
        }

    def test_init(self, config_manager):
        """Test ConfigManager initialization."""
        assert hasattr(config_manager, 'system')
        assert hasattr(config_manager, 'user_config_path')
        assert hasattr(config_manager, 'system_config_path')
        assert hasattr(config_manager, 'module_config_path')
        # System config path is None on non-Linux or Linux path on Linux
        if config_manager.system == 'linux':
            assert config_manager.system_config_path == Path('/etc/primeminister/config.json')
        else:
            assert config_manager.system_config_path is None

    @patch('platform.system')
    def test_init_linux(self, mock_system):
        """Test ConfigManager initialization on Linux."""
        mock_system.return_value = 'Linux'
        cm = ConfigManager()
        assert cm.system == 'linux'
        assert cm.system_config_path == Path('/etc/primeminister/config.json')

    @patch('platform.system')
    def test_init_non_linux(self, mock_system):
        """Test ConfigManager initialization on non-Linux systems."""
        mock_system.return_value = 'Darwin'
        cm = ConfigManager()
        assert cm.system == 'darwin'
        assert cm.system_config_path is None

    @patch('platform.system')
    @patch('pathlib.Path.exists')
    @patch('os.geteuid')
    def test_get_config_path_linux_exists(self, mock_geteuid, mock_exists, mock_system, config_manager):
        """Test get_config_path when Linux, running as root, and system config exists."""
        mock_system.return_value = 'Linux'
        mock_geteuid.return_value = 0  # Running as root
        mock_exists.return_value = True
        cm = ConfigManager()

        result = cm.get_config_path()
        assert result == cm.system_config_path

    @patch('platform.system')
    @patch('pathlib.Path.exists')
    def test_get_config_path_linux_not_exists(self, mock_exists, mock_system, config_manager):
        """Test get_config_path when Linux but user config doesn't exist."""
        mock_system.return_value = 'Linux'
        mock_exists.return_value = False  # Neither user nor system config exists
        cm = ConfigManager()

        result = cm.get_config_path()
        assert result == cm.module_config_path

    @patch('platform.system')
    def test_get_config_path_non_linux(self, mock_system, config_manager):
        """Test get_config_path on non-Linux systems."""
        mock_system.return_value = 'Darwin'
        cm = ConfigManager()

        result = cm.get_config_path()
        assert result == cm.module_config_path

    def test_load_config_success(self, config_manager, sample_config):
        """Test successful config loading."""
        mock_data = json.dumps(sample_config)

        with patch.object(config_manager, 'ensure_config_exists') as mock_ensure:
            mock_ensure.return_value = Path('/test/config.json')
            with patch('builtins.open', mock_open(read_data=mock_data)):
                result = config_manager.load_config()

        assert result == sample_config

    def test_load_config_file_not_found(self, config_manager):
        """Test config loading when file doesn't exist."""
        with patch.object(config_manager, 'get_config_path') as mock_path:
            mock_path.return_value = Path('/nonexistent/config.json')
            with patch('builtins.open', side_effect=FileNotFoundError):
                with patch.object(config_manager, 'ensure_config_exists') as mock_ensure:
                    mock_ensure.return_value = Path('/test/config.json')
                    with patch('builtins.open', mock_open(read_data='{"test": "data"}')):
                        result = config_manager.load_config()

        mock_ensure.assert_called_once()
        assert result == {"test": "data"}

    def test_load_config_json_decode_error(self, config_manager):
        """Test config loading with invalid JSON."""
        with patch.object(config_manager, 'get_config_path') as mock_path:
            mock_path.return_value = Path('/test/config.json')
            with patch('builtins.open', mock_open(read_data='invalid json')):
                with patch.object(config_manager, 'ensure_config_exists') as mock_ensure:
                    mock_ensure.return_value = Path('/test/config.json')
                    with patch('builtins.open', mock_open(read_data='{"test": "data"}')):
                        result = config_manager.load_config()

        mock_ensure.assert_called_once()
        assert result == {"test": "data"}

    @patch('platform.system')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @patch('shutil.copy2')
    @patch('os.geteuid')
    def test_ensure_config_exists_linux_success(self, mock_geteuid, mock_copy, mock_mkdir, mock_exists, mock_system):
        """Test ensure_config_exists on Linux as root with successful creation."""
        mock_system.return_value = 'Linux'
        mock_geteuid.return_value = 0  # Running as root
        # First call (system_config_path.exists()) returns False, second call (module_config_path.exists()) returns True
        mock_exists.side_effect = [False, True]
        cm = ConfigManager()

        result = cm.ensure_config_exists()

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_copy.assert_called_once_with(cm.module_config_path, cm.system_config_path)
        assert result == cm.system_config_path

    @patch('platform.system')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @patch('shutil.copy2')
    @patch('os.geteuid')
    def test_ensure_config_exists_linux_permission_error(self, mock_geteuid, mock_copy, mock_mkdir, mock_exists, mock_system):
        """Test ensure_config_exists on Linux as root with permission error, falls back to user config."""
        mock_system.return_value = 'Linux'
        mock_geteuid.return_value = 0  # Running as root
        # First call (system_config_path.exists()) returns False, then mkdir fails
        mock_exists.side_effect = [False, False, True]  # system doesn't exist, user doesn't exist, module exists
        mock_mkdir.side_effect = [PermissionError, None]  # System mkdir fails, user mkdir succeeds
        cm = ConfigManager()

        result = cm.ensure_config_exists()

        # Should fall back to user config
        assert result == cm.user_config_path
        mock_copy.assert_called_once_with(cm.module_config_path, cm.user_config_path)

    def test_create_default_config(self, config_manager, tmp_path):
        """Test _create_default_config method."""
        config_file = tmp_path / "test_config.json"

        config_manager._create_default_config(config_file)

        assert config_file.exists()
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Check that essential keys exist (using actual config structure)
        assert 'openai_key' in config
        assert 'api_url' in config
        assert 'mode' in config
        assert 'council' in config
        assert isinstance(config['council'], list)
        assert len(config['council']) > 0

    def test_save_config(self, config_manager, sample_config, tmp_path):
        """Test save_config method."""
        config_file = tmp_path / "test_config.json"

        with patch.object(config_manager, 'get_config_path', return_value=config_file):
            config_manager.save_config(sample_config)

        assert config_file.exists()
        with open(config_file, 'r') as f:
            saved_config = json.load(f)

        assert saved_config == sample_config

    def test_save_config_permission_error(self, config_manager, sample_config):
        """Test save_config with permission error."""
        with patch.object(config_manager, 'get_config_path') as mock_path:
            mock_path.return_value = Path('/readonly/config.json')
            with patch('pathlib.Path.mkdir', side_effect=OSError("Read-only file system")):
                # Should raise RuntimeError for save config failures
                with pytest.raises(RuntimeError, match="Failed to save configuration"):
                    config_manager.save_config(sample_config)