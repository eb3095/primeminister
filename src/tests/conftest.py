"""
Pytest configuration and fixtures for PrimeMinister tests.
"""
import pytest
import os
import tempfile
import sys
import json
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files during testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files during testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = MagicMock()

    # Mock successful API response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock AI response"

    client.chat.completions.create = AsyncMock(return_value=mock_response)
    return client


@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return {
        "openai_key": "test_key_12345",
        "api_url": "https://api.openai.com/v1",
        "mode": "council",
        "council_members": [
            {
                "model": "gpt-4",
                "personality": "Conservative advisor focused on risk management and traditional approaches",
                "voter": True,
                "silent": False
            },
            {
                "model": "gpt-4",
                "personality": "Progressive advisor focused on innovation and creative solutions",
                "voter": True,
                "silent": False
            },
            {
                "model": "gpt-3.5-turbo",
                "personality": "Analytical advisor focused on data-driven decisions",
                "voter": True,
                "silent": False
            }
        ]
    }


@pytest.fixture
def sample_session_data():
    """Provide sample session data for testing."""
    return {
        "session_id": "test-session-12345",
        "timestamp": "2024-01-15T10:30:00.000Z",
        "query": "What should I do about my career?",
        "mode": "council",
        "decision": "Consider both stability and growth opportunities",
        "council_responses": [
            "Focus on stable, proven career paths",
            "Explore innovative opportunities in emerging fields",
            "Analyze market data to make informed decisions"
        ],
        "vote_counts": {
            "Focus on stable, proven career paths": 1,
            "Explore innovative opportunities in emerging fields": 2,
            "Analyze market data to make informed decisions": 0
        },
        "vote_details": [
            "I vote for innovative opportunities because they offer growth",
            "I vote for stable paths for security",
            "I vote for innovative opportunities for future potential"
        ],
        "tie_breaker_used": False,
        "tie_breaker_reasoning": None,
        "council_summary": {
            "total_members": 3,
            "voters": 3,
            "silent_members": 0
        }
    }


@pytest.fixture
def mock_config_file(temp_config_dir, sample_config):
    """Create a mock configuration file for testing."""
    config_file = temp_config_dir / "config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config, f, indent=2)
    return config_file


@pytest.fixture
def mock_log_file(temp_log_dir, sample_session_data):
    """Create a mock log file for testing."""
    log_file = temp_log_dir / "2024-01.json"
    with open(log_file, 'w') as f:
        json.dump([sample_session_data], f, indent=2)
    return log_file


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration settings."""
    return {
        "test_mode": True,
        "api_key": "test_key_12345",
        "model": "gpt-4",
    }


@pytest.fixture(autouse=True)
def reset_imports():
    """Reset module imports between tests to ensure clean state."""
    yield
    # Clean up any cached imports that might affect other tests
    modules_to_clean = [
        'primeminister.core',
        'primeminister.config_manager',
        'primeminister.logger',
        'primeminister.cli'
    ]

    for module in modules_to_clean:
        if module in sys.modules:
            # Don't actually remove them, just ensure fresh state for next test
            pass


# Configure pytest to handle async tests
def pytest_configure(config):
    """Configure pytest for async testing."""
    config.addinivalue_line("markers", "asyncio: mark test as async")


# Set up asyncio event loop policy for tests
@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()