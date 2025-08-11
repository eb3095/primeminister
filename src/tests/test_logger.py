"""
Tests for PrimeMinisterLogger functionality.
"""
import json
import logging
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from primeminister.logger import PrimeMinisterLogger


class TestPrimeMinisterLogger:
    """Test cases for PrimeMinisterLogger class."""

    @pytest.fixture
    def logger(self):
        """Create a PrimeMinisterLogger instance for testing."""
        with patch.object(PrimeMinisterLogger, 'setup_logging_directory'):
            return PrimeMinisterLogger()

    @pytest.fixture
    def sample_session_data(self):
        """Sample session data for testing."""
        return {
            "session_id": "test-session-123",
            "timestamp": "2024-01-15T10:30:00",
            "query": "Test query",
            "mode": "council",
            "decision": "Test decision",
            "council_responses": ["Response 1", "Response 2"],
            "votes": {"Response 1": 2, "Response 2": 1}
        }

    @patch('platform.system')
    def test_init_linux(self, mock_system):
        """Test initialization on Linux."""
        mock_system.return_value = 'Linux'

        with patch.object(PrimeMinisterLogger, 'setup_logging_directory'):
            logger = PrimeMinisterLogger()
            assert logger.system == 'linux'

    @patch('platform.system')
    def test_init_non_linux(self, mock_system):
        """Test initialization on non-Linux systems."""
        mock_system.return_value = 'Darwin'

        with patch.object(PrimeMinisterLogger, 'setup_logging_directory'):
            logger = PrimeMinisterLogger()
            assert logger.system == 'darwin'

    @patch('platform.system')
    @patch('os.geteuid')
    def test_setup_logging_directory_linux(self, mock_geteuid, mock_system):
        """Test setup_logging_directory on Linux as root."""
        mock_system.return_value = 'Linux'
        mock_geteuid.return_value = 0  # Running as root

        with patch('pathlib.Path.mkdir') as mock_mkdir:
            logger = PrimeMinisterLogger()
            assert logger.log_dir == Path('/var/log/primeminister')
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('platform.system')
    @patch('os.geteuid')
    def test_setup_logging_directory_linux_permission_error(self, mock_geteuid, mock_system):
        """Test setup_logging_directory on Linux as root with permission error."""
        mock_system.return_value = 'Linux'
        mock_geteuid.return_value = 0  # Running as root

        # Mock mkdir to fail once (for /var/log/primeminister) then succeed (for user logs)
        with patch('pathlib.Path.mkdir', side_effect=[PermissionError, None]) as mock_mkdir:
            logger = PrimeMinisterLogger()
            # Should fallback to user logs
            assert logger.log_dir == Path.home() / 'primeminister' / 'logs'
            assert mock_mkdir.call_count == 2  # First attempt + fallback

    @patch('platform.system')
    def test_setup_logging_directory_non_linux(self, mock_system):
        """Test setup_logging_directory on non-Linux systems."""
        mock_system.return_value = 'Darwin'

        with patch('pathlib.Path.mkdir') as mock_mkdir:
            logger = PrimeMinisterLogger()
            assert logger.log_dir == Path.home() / 'primeminister' / 'logs'
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_get_current_log_file(self, logger):
        """Test get_current_log_file method."""
        logger.log_dir = Path('/test/logs')

        with patch('primeminister.logger.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.year = 2024
            mock_now.month = 3
            mock_datetime.now.return_value = mock_now

            result = logger.get_current_log_file()
            expected = Path('/test/logs/2024-03.json')
            assert result == expected

    def test_load_existing_logs_file_exists(self, logger):
        """Test load_existing_logs when file exists with valid JSON."""
        test_logs = [{"session_id": "test1"}, {"session_id": "test2"}]
        mock_data = json.dumps(test_logs)

        with patch.object(logger, 'get_current_log_file') as mock_get_file:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_get_file.return_value = mock_file

            with patch('builtins.open', mock_open(read_data=mock_data)):
                result = logger.load_existing_logs()

        assert result == test_logs

    def test_load_existing_logs_file_not_exists(self, logger):
        """Test load_existing_logs when file doesn't exist."""
        with patch.object(logger, 'get_current_log_file') as mock_get_file:
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_get_file.return_value = mock_file

            result = logger.load_existing_logs()

        assert result == []

    def test_load_existing_logs_empty_file(self, logger):
        """Test load_existing_logs with empty file."""
        with patch.object(logger, 'get_current_log_file') as mock_get_file:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_get_file.return_value = mock_file

            with patch('builtins.open', mock_open(read_data='')):
                result = logger.load_existing_logs()

        assert result == []

    def test_load_existing_logs_invalid_json(self, logger):
        """Test load_existing_logs with invalid JSON."""
        with patch.object(logger, 'get_current_log_file') as mock_get_file:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_get_file.return_value = mock_file

            with patch('builtins.open', mock_open(read_data='invalid json')):
                result = logger.load_existing_logs()

        assert result == []

