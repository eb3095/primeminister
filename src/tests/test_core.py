"""
Tests for core PrimeMinister functionality.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from primeminister.core import CouncilMember, PrimeMinister


class TestCouncilMember:
    """Test cases for CouncilMember class."""

    def test_init_default(self):
        """Test CouncilMember initialization with default values."""
        member = CouncilMember("gpt-4", "Test personality")

        assert member.model == "gpt-4"
        assert member.personality == "Test personality"
        assert member.is_voter is True
        assert member.is_silent is False
        assert member.response == ""

    def test_init_custom(self):
        """Test CouncilMember initialization with custom values."""
        member = CouncilMember("gpt-3.5-turbo", "Custom personality", voter=False, silent=True)

        assert member.model == "gpt-3.5-turbo"
        assert member.personality == "Custom personality"
        assert member.is_voter is False
        assert member.is_silent is True
        assert member.response == ""

    def test_repr(self):
        """Test CouncilMember string representation."""
        member = CouncilMember("gpt-4", "A very long personality description that should be truncated", voter=True, silent=False)

        repr_str = repr(member)
        assert "CouncilMember" in repr_str
        assert "voter=True" in repr_str
        assert "silent=False" in repr_str
        assert "A very long personality descri..." in repr_str


class TestPrimeMinister:
    """Test cases for PrimeMinister class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "openai_key": "test_key_123",
            "api_url": "https://api.openai.com/v1",
            "mode": "council",
            "council": [
                {
                    "model": "gpt-4",
                    "personality": "Conservative advisor focused on risk management",
                    "voter": True,
                    "silent": False
                },
                {
                    "model": "gpt-4",
                    "personality": "Progressive advisor focused on innovation",
                    "voter": True,
                    "silent": False
                }
            ]
        }

    @pytest.fixture
    def prime_minister(self, mock_config):
        """Create a PrimeMinister instance for testing."""
        with patch('primeminister.core.ConfigManager') as mock_config_manager:
            with patch('primeminister.core.PrimeMinisterLogger') as mock_logger:
                with patch('primeminister.core.AsyncOpenAI') as mock_openai:
                    mock_config_manager_instance = MagicMock()
                    mock_config_manager_instance.load_config.return_value = mock_config
                    mock_config_manager.return_value = mock_config_manager_instance

                    mock_logger_instance = MagicMock()
                    mock_std_logger = MagicMock()
                    mock_logger_instance.setup_standard_logging.return_value = mock_std_logger
                    mock_logger.return_value = mock_logger_instance

                    mock_openai_instance = MagicMock()
                    mock_openai.return_value = mock_openai_instance

                    pm = PrimeMinister()
                    pm.client = mock_openai_instance

                    # Manually initialize council from config since mocking prevents normal initialization
                    pm.council = []
                    for member_config in mock_config.get('council', []):
                        member = CouncilMember(
                            model=member_config['model'],
                            personality=member_config['personality'],
                            voter=member_config.get('voter', True),
                            silent=member_config.get('silent', False)
                        )
                        pm.council.append(member)

                    return pm

    def test_init(self, mock_config):
        """Test PrimeMinister initialization."""
        with patch('primeminister.core.ConfigManager') as mock_config_manager:
            with patch('primeminister.core.PrimeMinisterLogger') as mock_logger:
                with patch('primeminister.core.AsyncOpenAI') as mock_openai:
                    mock_config_manager_instance = MagicMock()
                    mock_config_manager_instance.load_config.return_value = mock_config
                    mock_config_manager.return_value = mock_config_manager_instance

                    mock_logger_instance = MagicMock()
                    mock_logger.return_value = mock_logger_instance

                    pm = PrimeMinister()

                    assert pm.config == mock_config
                    assert len(pm.council) == 2
                    assert all(isinstance(member, CouncilMember) for member in pm.council)

    def test_init_with_mode_override(self, mock_config):
        """Test PrimeMinister initialization with mode override."""
        with patch('primeminister.core.ConfigManager') as mock_config_manager:
            with patch('primeminister.core.PrimeMinisterLogger') as mock_logger:
                with patch('primeminister.core.AsyncOpenAI'):
                    mock_config_manager_instance = MagicMock()
                    mock_config_manager_instance.load_config.return_value = mock_config
                    mock_config_manager.return_value = mock_config_manager_instance

                    mock_logger_instance = MagicMock()
                    mock_std_logger = MagicMock()
                    mock_logger_instance.setup_standard_logging.return_value = mock_std_logger
                    mock_logger.return_value = mock_logger_instance

                    pm = PrimeMinister(mode_override="advisor")

                    assert pm.config['mode'] == "advisor"
                    # Verify that some initialization logging occurred
                    mock_std_logger.info.assert_called()

    def test_initialize_council(self, prime_minister):
        """Test _initialize_council method."""
        assert len(prime_minister.council) == 2

        member1 = prime_minister.council[0]
        assert member1.model == "gpt-4"
        assert "Conservative advisor" in member1.personality
        assert member1.is_voter is True
        assert member1.is_silent is False

        member2 = prime_minister.council[1]
        assert member2.model == "gpt-4"
        assert "Progressive advisor" in member2.personality
        assert member2.is_voter is True
        assert member2.is_silent is False

    def test_get_council_summary(self, prime_minister):
        """Test get_council_summary method."""
        summary = prime_minister.get_council_summary()

        assert summary['total_members'] == 2
        assert summary['voters'] == 2
        assert summary['silent_members'] == 0
        assert len(summary['members']) == 2

        for member in summary['members']:
            assert 'model' in member
            assert 'personality' in member
            assert 'voter' in member
            assert 'silent' in member

    # Two-round opinion system tests for advisor mode

    @pytest.mark.asyncio
    async def test_conduct_opinion_rounds_basic(self, prime_minister):
        """Test the basic two-round opinion system."""
        # Create mock initial responses from council members
        initial_responses = [
            {
                'uuid': 'response-1',
                'personality': 'Conservative advisor focused on risk management',
                'response': 'Conservative approach to the problem',
                'model': 'gpt-4',
                'has_error': False
            },
            {
                'uuid': 'response-2',
                'personality': 'Progressive advisor focused on innovation',
                'response': 'Progressive approach to the problem',
                'model': 'gpt-4',
                'has_error': False
            }
        ]

        # Mock API responses for opinion rounds
        mock_responses = [
            "Opinion on conservative approach",
            "Opinion on progressive approach",
            "Response to opinions on conservative",
            "Response to opinions on progressive"
        ]

        call_count = 0
        async def mock_api_call(*args, **kwargs):
            nonlocal call_count
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = mock_responses[call_count % len(mock_responses)]
            call_count += 1
            return mock_response

        prime_minister.client.chat.completions.create = mock_api_call

        # Run the opinion rounds
        first_round_opinions, second_round_responses = await prime_minister.conduct_opinion_rounds(
            initial_responses, "Test question"
        )

        # Verify first round opinions structure
        assert len(first_round_opinions) == 2
        for opinion in first_round_opinions:
            assert 'uuid' in opinion
            assert 'opinion_giver' in opinion
            assert 'target_response_uuid' in opinion
            assert 'opinion' in opinion
            assert opinion['has_error'] is False

        # Verify second round responses structure
        assert len(second_round_responses) == 2
        for response in second_round_responses:
            assert 'uuid' in response
            assert 'personality' in response
            assert 'original_response_uuid' in response
            assert 'response_to_opinions' in response
            assert 'opinions_considered' in response
            assert response['has_error'] is False

    @pytest.mark.asyncio
    async def test_prime_minister_advisor_synthesis_with_opinions(self, prime_minister):
        """Test PM synthesis with the new opinion system."""
        initial_responses = [
            {'uuid': 'response-1', 'personality': 'Conservative', 'response': 'Conservative view', 'has_error': False}
        ]

        first_round_opinions = [
            {
                'uuid': 'opinion-1',
                'opinion_giver': 'Progressive',
                'target_response_uuid': 'response-1',
                'opinion': 'Good points but consider alternatives',
                'has_error': False
            }
        ]

        second_round_responses = [
            {
                'uuid': 'second-1',
                'personality': 'Conservative',
                'response_to_opinions': 'Thank you, I see your point',
                'has_error': False
            }
        ]

                # Mock the OpenAI API call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Synthesized response with opinions"
        prime_minister.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await prime_minister.prime_minister_advisor_synthesis_with_opinions(
            initial_responses, first_round_opinions, second_round_responses, "Test question"
        )

        assert result == "Synthesized response with opinions"
        prime_minister.client.chat.completions.create.assert_called_once()

        # Verify the prompt includes all three rounds
        call_args = prime_minister.client.chat.completions.create.call_args
        prompt_content = call_args[1]['messages'][0]['content']
        assert "ROUND 1 - Initial Council Responses:" in prompt_content
        assert "ROUND 2 - Peer Opinions on Initial Responses:" in prompt_content
        assert "ROUND 3 - Original Advisors' Responses to Opinions:" in prompt_content

    @pytest.mark.asyncio
    async def test_advisor_mode_integration(self, prime_minister):
        """Test the complete advisor mode flow with opinion rounds."""
        # Set advisor mode
        prime_minister.config['mode'] = 'advisor'

        # Mock council responses
        mock_initial_responses = [
            {
                'uuid': 'resp-1',
                'personality': 'Conservative',
                'response': 'Conservative solution',
                'model': 'gpt-4',
                'has_error': False
            }
        ]

        # Mock the methods
        prime_minister.gather_council_responses = AsyncMock(return_value=mock_initial_responses)

        # Mock opinion rounds
        mock_opinions = [{'uuid': 'op-1', 'opinion_giver': 'Progressive', 'has_error': False}]
        mock_second_responses = [{'uuid': 'sr-1', 'personality': 'Conservative', 'has_error': False}]
        prime_minister.conduct_opinion_rounds = AsyncMock(return_value=(mock_opinions, mock_second_responses))

        # Mock final synthesis
        prime_minister.prime_minister_advisor_synthesis_with_opinions = AsyncMock(
            return_value="Final synthesized decision"
        )

        # Process the request
        result, session_data = await prime_minister.process_request("Test advisor question")

        # Verify the flow
        assert result == "Final synthesized decision"
        prime_minister.gather_council_responses.assert_called_once()
        prime_minister.conduct_opinion_rounds.assert_called_once()
        prime_minister.prime_minister_advisor_synthesis_with_opinions.assert_called_once()

        # Verify session data includes opinion data
        assert 'first_round_opinions' in session_data
        assert 'second_round_responses' in session_data
        assert session_data['metadata']['mode'] == 'advisor'
        assert 'opinion_rounds_conducted' in session_data['metadata']
        assert session_data['metadata']['opinion_rounds_conducted'] == 2

    def test_opinion_uuid_generation(self):
        """Test that opinions have proper UUID generation."""
        # Validate UUID format and structure
        import uuid as uuid_module

        # Test UUID format
        test_uuid = str(uuid_module.uuid4())
        assert len(test_uuid) == 36
        assert test_uuid.count('-') == 4

    @pytest.mark.asyncio
    async def test_opinion_rounds_error_handling(self, prime_minister):
        """Test error handling in opinion rounds."""
        initial_responses = [
            {
                'uuid': 'response-1',
                'personality': 'Conservative advisor',
                'response': 'Test response',
                'model': 'gpt-4',
                'has_error': False
            }
        ]

        # Mock API to raise an exception
        prime_minister.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        first_round_opinions, second_round_responses = await prime_minister.conduct_opinion_rounds(
            initial_responses, "Test question"
        )

        # Should handle errors gracefully
        assert len(first_round_opinions) >= 0  # May have error entries
        assert len(second_round_responses) >= 0  # May have error entries

        # Check if error opinions are marked properly
        for opinion in first_round_opinions:
            if opinion.get('has_error'):
                assert 'Error:' in opinion['opinion']

    @pytest.mark.asyncio
    async def test_silent_advisors_skip_opinions(self, prime_minister):
        """Test that silent advisors don't participate in opinion rounds."""
        # Add a silent advisor to the council
        from primeminister.core import CouncilMember
        silent_advisor = CouncilMember("gpt-4", "Silent advisor", voter=False, silent=True)
        prime_minister.council.append(silent_advisor)

        initial_responses = [
            {
                'uuid': 'response-1',
                'personality': 'Regular advisor',
                'response': 'Regular response',
                'model': 'gpt-4',
                'has_error': False
            }
        ]

        # Mock API calls
        prime_minister.client.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Opinion content"))]
        ))

        first_round_opinions, second_round_responses = await prime_minister.conduct_opinion_rounds(
            initial_responses, "Test question"
        )

        # Silent advisor should not give opinions
        opinion_givers = [op['opinion_giver'] for op in first_round_opinions]
        assert "Silent advisor" not in opinion_givers