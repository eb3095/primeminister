"""
Tests for CLI functionality.
"""
import argparse
import asyncio
import json
import sys
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock, AsyncMock
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from primeminister import cli


class TestCLIFunctions:
    """Test cases for CLI utility functions."""

    def test_print_banner(self, capsys):
        """Test print_banner function."""
        cli.print_banner()
        captured = capsys.readouterr()

        assert "PRIME MINISTER" in captured.out
        assert "AI Council Decision System" in captured.out
        assert "╔" in captured.out  # Check for box drawing characters

    def test_print_council_summary(self, capsys):
        """Test print_council_summary function."""
        mock_pm = MagicMock()
        mock_pm.get_council_summary.return_value = {
            'total_members': 3,
            'voters': 2,
            'silent_members': 1,
            'members': [
                {
                    'personality': 'Conservative Advisor',
                    'model': 'gpt-4',
                    'voter': True,
                    'silent': False
                },
                {
                    'personality': 'Progressive Advisor',
                    'model': 'gpt-4',
                    'voter': True,
                    'silent': False
                },
                {
                    'personality': 'Silent Observer',
                    'model': 'gpt-3.5-turbo',
                    'voter': False,
                    'silent': True
                }
            ]
        }

        cli.print_council_summary(mock_pm)
        captured = capsys.readouterr()

        assert "Council Summary:" in captured.out
        assert "Total Members: 3" in captured.out
        assert "Voting Members: 2" in captured.out
        assert "Silent Members: 1" in captured.out
        assert "Conservative Advisor" in captured.out
        assert "Progressive Advisor" in captured.out
        assert "Silent Observer" in captured.out
        assert "🗳️" in captured.out  # Voting icon
        assert "🤫" in captured.out  # Silent icon

    def test_format_response_basic(self, capsys):
        """Test format_response with basic decision."""
        decision = "This is the final decision"

        cli.format_response(decision, None)  # format_response prints, doesn't return
        captured = capsys.readouterr()

        assert "DECISION" in captured.out
        assert decision in captured.out
        assert "🏛️" in captured.out  # Check for formatting

    def test_format_response_with_session_data(self, capsys):
        """Test format_response with session data."""
        decision = "This is the final decision"
        session_data = {
            'metadata': {  # The actual format expects metadata wrapper
                'mode': 'council',
                'total_council_members': 2,
                'voting_members': 2,
                'tie_broken_by_pm': False
            },
            'responses': ['Response A', 'Response B'],
            'votes': {'Response A': ['voter1', 'voter2'], 'Response B': ['voter3']}
        }

        cli.format_response(decision, session_data)
        captured = capsys.readouterr()

        assert decision in captured.out
        assert "DECISION" in captured.out
        assert "📊 Voting Results:" in captured.out

    def test_format_response_with_tie_breaker(self, capsys):
        """Test format_response with tie breaker used."""
        decision = "This is the final decision"
        session_data = {
            'metadata': {
                'mode': 'council',
                'tie_broken_by_pm': True
            },
            'votes': {
                'Response A': ['voter1', 'Prime Minister (tie-breaker)'],
                'Response B': ['voter2']
            }
        }

        cli.format_response(decision, session_data)
        captured = capsys.readouterr()

        assert "tie was broken" in captured.out.lower()
        assert "prime minister" in captured.out.lower()

    def test_format_response_advisor_mode(self, capsys):
        """Test format_response in advisor mode."""
        decision = "This is the synthesized advice"
        session_data = {
            'metadata': {
                'mode': 'advisor'
            }
        }

        cli.format_response(decision, session_data)
        captured = capsys.readouterr()

        assert "SYNTHESIS" in captured.out
        assert "Direct synthesis" in captured.out

    @patch('primeminister.cli.ConfigManager')
    def test_show_config(self, mock_config_manager, capsys):
        """Test show_config function."""
        mock_cm = MagicMock()
        mock_cm.get_config_path.return_value = "/test/config.json"
        mock_config_manager.return_value = mock_cm

        cli.show_config()
        captured = capsys.readouterr()

        assert "Configuration file:" in captured.out
        assert "/test/config.json" in captured.out





if __name__ == '__main__':
    pytest.main([__file__])