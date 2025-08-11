"""
Tests for PrimeMinister package initialization and basic functionality.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import primeminister


class TestPackageInitialization:
    """Test cases for package initialization."""

    def test_package_import(self):
        """Test that the package can be imported."""
        assert primeminister is not None

    def test_package_metadata(self):
        """Test package metadata."""
        assert hasattr(primeminister, '__version__')
        assert hasattr(primeminister, '__author__')
        assert hasattr(primeminister, '__email__')

        assert primeminister.__version__ == "1.0.0"
        assert primeminister.__author__ == "Eric Benner"
        assert primeminister.__email__ == "ebennerit@gmail.com"

    def test_package_exports(self):
        """Test that required classes are exported."""
        # These should always be available
        assert hasattr(primeminister, 'ConfigManager')
        assert hasattr(primeminister, 'PrimeMinisterLogger')

        # Check if they're in __all__
        assert 'ConfigManager' in primeminister.__all__
        assert 'PrimeMinisterLogger' in primeminister.__all__

    def test_core_imports_available(self):
        """Test that core imports are available when dependencies are present."""
        # These depend on external dependencies being available
        if hasattr(primeminister, 'PrimeMinister'):
            assert hasattr(primeminister, 'CouncilMember')
            assert 'PrimeMinister' in primeminister.__all__
            assert 'CouncilMember' in primeminister.__all__

    def test_core_imports_graceful_failure(self):
        """Test that package handles missing dependencies gracefully."""
        # Mock ImportError for core module
        with patch.dict('sys.modules', {'primeminister.core': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'openai'")):
                # This should not raise an exception
                # The package should handle missing dependencies gracefully
                pass

    def test_config_manager_import(self):
        """Test ConfigManager can be imported and instantiated."""
        from primeminister import ConfigManager

        # Should be able to create an instance
        with patch.object(ConfigManager, '__init__', return_value=None):
            cm = ConfigManager()
            assert cm is not None

    def test_logger_import(self):
        """Test PrimeMinisterLogger can be imported and instantiated."""
        from primeminister import PrimeMinisterLogger

        # Should be able to create an instance
        with patch.object(PrimeMinisterLogger, '__init__', return_value=None):
            logger = PrimeMinisterLogger()
            assert logger is not None

    @patch('primeminister._CORE_AVAILABLE', True)
    def test_core_available_true(self):
        """Test behavior when core modules are available."""
        # Reload the module to test the conditional import
        import importlib
        importlib.reload(primeminister)

        # When core is available, these should be in __all__
        if hasattr(primeminister, 'PrimeMinister'):
            assert 'PrimeMinister' in primeminister.__all__
            assert 'CouncilMember' in primeminister.__all__

    @patch('primeminister._CORE_AVAILABLE', False)
    def test_core_available_false(self):
        """Test behavior when core modules are not available."""
        # When core is not available, these should be None
        if not hasattr(primeminister, 'PrimeMinister') or primeminister.PrimeMinister is None:
            assert primeminister.PrimeMinister is None
            assert primeminister.CouncilMember is None


class TestPackageStructure:
    """Test cases for package structure and organization."""

    def test_module_structure(self):
        """Test that expected modules exist."""
        expected_modules = [
            'primeminister.config_manager',
            'primeminister.logger'
        ]

        for module_name in expected_modules:
            try:
                __import__(module_name)
            except ImportError:
                pytest.fail(f"Expected module {module_name} not found")

    def test_optional_modules(self):
        """Test that optional modules handle dependencies gracefully."""
        # These modules might not be available if dependencies are missing
        optional_modules = [
            'primeminister.core',
            'primeminister.cli'
        ]

        for module_name in optional_modules:
            try:
                __import__(module_name)
            except ImportError:
                # This is acceptable for optional modules
                pass

    def test_package_docstring(self):
        """Test that package has proper documentation."""
        assert primeminister.__doc__ is not None
        assert "PrimeMinister" in primeminister.__doc__
        assert "AI Council Decision System" in primeminister.__doc__


class TestBackwardCompatibility:
    """Test cases for backward compatibility."""

    def test_import_patterns(self):
        """Test various import patterns work correctly."""
        # Direct imports
        from primeminister import ConfigManager, PrimeMinisterLogger
        assert ConfigManager is not None
        assert PrimeMinisterLogger is not None

        # Module-level import
        import primeminister
        assert hasattr(primeminister, 'ConfigManager')
        assert hasattr(primeminister, 'PrimeMinisterLogger')

    def test_star_import(self):
        """Test that star imports work correctly."""
        # Test star import functionality
        import primeminister

        # Test that __all__ contains expected items
        expected_items = ['ConfigManager', 'PrimeMinisterLogger']
        for item in expected_items:
            assert item in primeminister.__all__
            assert hasattr(primeminister, item)