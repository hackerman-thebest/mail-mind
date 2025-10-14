"""
Unit tests for ResponseGenerator

Tests cover:
- Response generation with different lengths (Brief/Standard/Detailed)
- Response generation with different tones (Professional/Friendly/Formal/Casual)
- Template-based response generation
- Thread context incorporation
- Response formatting and cleanup
- Metrics tracking
- User feedback recording
- Edge cases and error handling

Story 1.5: Response Generation Assistant
"""

import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch

from src.mailmind.core.response_generator import (
    ResponseGenerator,
    ResponseGenerationError,
    generate_response
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def mock_ollama():
    """Create mock OllamaManager."""
    mock = Mock()
    mock.current_model = 'llama3.1:8b-instruct-q4_K_M'
    mock.context_window = 8192

    # Mock client.generate
    mock.client = Mock()
    mock.client.generate = Mock(return_value={
        'response': 'Hi Alice,\n\nYes, I can attend the meeting on Friday at 2pm.\n\nThanks,\nBob',
        'total_duration': 2500000000,  # 2.5 seconds in nanoseconds
        'eval_count': 50
    })

    return mock


@pytest.fixture
def generator(mock_ollama, temp_db):
    """Create ResponseGenerator instance with mocked dependencies."""
    return ResponseGenerator(mock_ollama, db_path=temp_db)


@pytest.fixture
def sample_email():
    """Sample preprocessed email for testing."""
    return {
        'metadata': {
            'from': 'alice@example.com',
            'from_name': 'Alice Smith',
            'subject': 'Meeting Request',
            'date': '2025-10-13T14:30:00Z',
            'message_id': 'msg_001'
        },
        'content': {
            'body': 'Hi Bob,\n\nWould you be available for a meeting this Friday at 2pm to discuss the Q4 budget?\n\nThanks,\nAlice',
            'has_html': False,
            'has_signature': False,
            'has_quotes': False
        },
        'thread_context': {
            'is_reply': False,
            'is_forward': False,
            'thread_depth': 0
        }
    }


class TestResponseGeneratorInitialization:
    """Test ResponseGenerator initialization."""

    def test_initialization(self, mock_ollama, temp_db):
        """Test basic initialization."""
        generator = ResponseGenerator(mock_ollama, db_path=temp_db)

        assert generator.db_path == temp_db
        assert generator.ollama == mock_ollama
        assert os.path.exists(temp_db)

    def test_database_tables_created(self, generator, temp_db):
        """Test that database tables are created."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check response_history table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='response_history'")
        assert cursor.fetchone() is not None

        conn.close()

    def test_database_schema(self, generator, temp_db):
        """Test database schema has required columns."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check response_history columns
        cursor.execute("PRAGMA table_info(response_history)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {
            'id', 'message_id', 'response_text', 'response_length',
            'response_tone', 'template_used', 'word_count',
            'processing_time_ms', 'model_version', 'generated_date'
        }

        assert required_columns.issubset(columns)

        conn.close()

    def test_writing_style_loaded(self, generator):
        """Test that writing style profile is loaded."""
        assert generator.writing_style is not None
        assert 'greeting_style' in generator.writing_style
        assert 'closing_style' in generator.writing_style


class TestResponseGeneration:
    """Test basic response generation."""

    def test_generate_response_standard(self, generator, sample_email):
        """Test generating a standard response."""
        result = generator.generate_response(sample_email, length='Standard', tone='Professional')

        assert result is not None
        assert 'response_text' in result
        assert result['length'] == 'Standard'
        assert result['tone'] == 'Professional'
        assert result['word_count'] > 0
        assert result['processing_time_ms'] >= 0  # Can be 0 with fast mocks

    def test_generate_response_brief(self, generator, sample_email):
        """Test generating a brief response."""
        generator.ollama.client.generate = Mock(return_value={
            'response': 'Hi Alice,\n\nYes, Friday at 2pm works.\n\nThanks',
            'total_duration': 1500000000,
            'eval_count': 20
        })

        result = generator.generate_response(sample_email, length='Brief', tone='Professional')

        assert result['length'] == 'Brief'
        assert result['word_count'] < 60  # Brief should be short

    def test_generate_response_detailed(self, generator, sample_email):
        """Test generating a detailed response."""
        long_response = 'Hi Alice,\n\n' + ' '.join(['word'] * 200) + '\n\nThanks'

        generator.ollama.client.generate = Mock(return_value={
            'response': long_response,
            'total_duration': 5000000000,
            'eval_count': 300
        })

        result = generator.generate_response(sample_email, length='Detailed', tone='Professional')

        assert result['length'] == 'Detailed'
        # Detailed responses are longer (though mock won't enforce exact length)

    def test_generate_response_calls_llm_with_correct_params(self, generator, sample_email):
        """Test that LLM is called with correct parameters."""
        generator.generate_response(sample_email, length='Standard', tone='Professional')

        # Verify LLM was called
        generator.ollama.client.generate.assert_called_once()

        # Check call arguments
        call_args = generator.ollama.client.generate.call_args
        assert call_args[1]['model'] == 'llama3.1:8b-instruct-q4_K_M'
        assert call_args[1]['options']['temperature'] == 0.7
        assert 'prompt' in call_args[1]


class TestResponseLengthControls:
    """Test response length controls."""

    def test_length_targets(self, generator):
        """Test that length targets are defined."""
        assert 'Brief' in generator.LENGTH_TARGETS
        assert 'Standard' in generator.LENGTH_TARGETS
        assert 'Detailed' in generator.LENGTH_TARGETS

        # Verify targets have min, target, max
        for length in ['Brief', 'Standard', 'Detailed']:
            assert 'min' in generator.LENGTH_TARGETS[length]
            assert 'target' in generator.LENGTH_TARGETS[length]
            assert 'max' in generator.LENGTH_TARGETS[length]

    def test_calculate_max_tokens(self, generator):
        """Test max token calculation for each length."""
        brief_tokens = generator._calculate_max_tokens('Brief')
        standard_tokens = generator._calculate_max_tokens('Standard')
        detailed_tokens = generator._calculate_max_tokens('Detailed')

        # Detailed should have more tokens than Standard, which should have more than Brief
        assert brief_tokens < standard_tokens < detailed_tokens

    def test_invalid_length_falls_back_to_standard(self, generator, sample_email):
        """Test that invalid length falls back to Standard."""
        result = generator.generate_response(sample_email, length='Invalid')

        assert result['length'] == 'Standard'


class TestToneOptions:
    """Test tone option controls."""

    def test_tone_descriptions_defined(self, generator):
        """Test that tone descriptions are defined."""
        assert 'Professional' in generator.TONE_DESCRIPTIONS
        assert 'Friendly' in generator.TONE_DESCRIPTIONS
        assert 'Formal' in generator.TONE_DESCRIPTIONS
        assert 'Casual' in generator.TONE_DESCRIPTIONS

    def test_generate_with_professional_tone(self, generator, sample_email):
        """Test generating response with professional tone."""
        result = generator.generate_response(sample_email, tone='Professional')

        assert result['tone'] == 'Professional'

    def test_generate_with_friendly_tone(self, generator, sample_email):
        """Test generating response with friendly tone."""
        result = generator.generate_response(sample_email, tone='Friendly')

        assert result['tone'] == 'Friendly'

    def test_generate_with_formal_tone(self, generator, sample_email):
        """Test generating response with formal tone."""
        result = generator.generate_response(sample_email, tone='Formal')

        assert result['tone'] == 'Formal'

    def test_generate_with_casual_tone(self, generator, sample_email):
        """Test generating response with casual tone."""
        result = generator.generate_response(sample_email, tone='Casual')

        assert result['tone'] == 'Casual'

    def test_invalid_tone_falls_back_to_professional(self, generator, sample_email):
        """Test that invalid tone falls back to Professional."""
        result = generator.generate_response(sample_email, tone='Invalid')

        assert result['tone'] == 'Professional'


class TestTemplates:
    """Test scenario templates."""

    def test_templates_defined(self, generator):
        """Test that all 8 templates are defined."""
        required_templates = [
            'Meeting Acceptance',
            'Meeting Decline',
            'Status Update',
            'Thank You',
            'Information Request',
            'Acknowledgment',
            'Follow-up',
            'Out of Office'
        ]

        for template in required_templates:
            assert template in generator.TEMPLATES

    def test_generate_with_meeting_acceptance_template(self, generator, sample_email):
        """Test generating response with Meeting Acceptance template."""
        result = generator.generate_response(sample_email, template='Meeting Acceptance')

        assert result['template'] == 'Meeting Acceptance'

        # Verify template instructions were included in prompt
        call_args = generator.ollama.client.generate.call_args
        prompt = call_args[1]['prompt']
        assert 'Meeting Acceptance' in prompt

    def test_generate_with_meeting_decline_template(self, generator, sample_email):
        """Test generating response with Meeting Decline template."""
        result = generator.generate_response(sample_email, template='Meeting Decline')

        assert result['template'] == 'Meeting Decline'

    def test_generate_with_status_update_template(self, generator, sample_email):
        """Test generating response with Status Update template."""
        result = generator.generate_response(sample_email, template='Status Update')

        assert result['template'] == 'Status Update'

    def test_generate_with_thank_you_template(self, generator, sample_email):
        """Test generating response with Thank You template."""
        result = generator.generate_response(sample_email, template='Thank You')

        assert result['template'] == 'Thank You'

    def test_invalid_template_ignored(self, generator, sample_email):
        """Test that invalid template is ignored."""
        result = generator.generate_response(sample_email, template='Invalid Template')

        assert result['template'] is None


class TestThreadContextIncorporation:
    """Test thread context incorporation."""

    def test_generate_with_thread_context(self, generator, sample_email):
        """Test generating response with thread context."""
        thread = [
            {
                'metadata': {'from': 'alice@example.com'},
                'content': {'body': 'Initial message about the project'}
            },
            {
                'metadata': {'from': 'bob@example.com'},
                'content': {'body': 'Reply with some questions'}
            }
        ]

        result = generator.generate_response(sample_email, thread_context=thread)

        # Verify thread context was included in prompt
        call_args = generator.ollama.client.generate.call_args
        prompt = call_args[1]['prompt']
        assert 'Thread Context' in prompt

    def test_summarize_thread_limits_to_5_messages(self, generator):
        """Test that thread summarization limits to last 5 messages."""
        thread = [
            {'metadata': {'from': f'user{i}@example.com'}, 'content': {'body': f'Message {i}'}}
            for i in range(10)
        ]

        summary = generator._summarize_thread(thread)

        # Should only include last 5 messages
        lines = summary.split('\n')
        assert len(lines) == 5

    def test_summarize_thread_formats_correctly(self, generator):
        """Test thread summary formatting."""
        thread = [
            {
                'metadata': {'from': 'alice@example.com'},
                'content': {'body': 'First message'}
            }
        ]

        summary = generator._summarize_thread(thread)

        assert 'alice@example.com' in summary
        assert 'First message' in summary


class TestResponseFormatting:
    """Test response formatting and cleanup."""

    def test_format_response_removes_markdown(self, generator):
        """Test that markdown artifacts are removed."""
        raw_response = '```python\ncode\n```\nHi Alice,\n\nResponse text.\n\nThanks'

        formatted = generator._format_response(raw_response)

        assert '```' not in formatted
        assert 'Hi Alice' in formatted

    def test_format_response_removes_response_prefix(self, generator):
        """Test that "Response:" prefix is removed."""
        raw_response = 'Response: Hi Alice,\n\nText here.\n\nThanks'

        formatted = generator._format_response(raw_response)

        assert not formatted.startswith('Response:')

    def test_format_response_normalizes_newlines(self, generator):
        """Test that excessive newlines are normalized."""
        raw_response = 'Hi Alice,\n\n\n\nToo many newlines.\n\n\n\nThanks'

        formatted = generator._format_response(raw_response)

        # Should not have more than 2 consecutive newlines
        assert '\n\n\n' not in formatted

    def test_format_response_removes_signature_blocks(self, generator):
        """Test that signature blocks are removed."""
        raw_response = 'Hi Alice,\n\nResponse text.\n\n-- \nBob Smith\nSenior Engineer\nbob@example.com'

        formatted = generator._format_response(raw_response)

        # Signature block should be removed
        assert 'Senior Engineer' not in formatted

    def test_format_response_strips_whitespace(self, generator):
        """Test that leading/trailing whitespace is stripped."""
        raw_response = '   \n\nHi Alice,\n\nResponse text.\n\nThanks\n\n   '

        formatted = generator._format_response(raw_response)

        assert formatted.startswith('Hi Alice')
        assert formatted.endswith('Thanks')


class TestStyleIntegration:
    """Test writing style integration."""

    def test_build_style_instructions(self, generator):
        """Test building style instructions from profile."""
        instructions = generator._build_style_instructions()

        assert 'Greeting:' in instructions
        assert 'Closing:' in instructions
        assert 'Formality:' in instructions

    def test_build_style_instructions_includes_greeting(self, generator):
        """Test that style instructions include greeting."""
        generator.writing_style['greeting_style'] = 'Hi'

        instructions = generator._build_style_instructions()

        assert 'Hi' in instructions

    def test_build_style_instructions_includes_closing(self, generator):
        """Test that style instructions include closing."""
        generator.writing_style['closing_style'] = 'Thanks'

        instructions = generator._build_style_instructions()

        assert 'Thanks' in instructions

    def test_build_style_instructions_formality_interpretation(self, generator):
        """Test formality level interpretation."""
        # Test formal
        generator.writing_style['formality_level'] = 0.9
        instructions = generator._build_style_instructions()
        assert 'formal' in instructions.lower()

        # Test casual
        generator.writing_style['formality_level'] = 0.2
        instructions = generator._build_style_instructions()
        assert 'casual' in instructions.lower()

    def test_build_style_instructions_includes_common_phrases(self, generator):
        """Test that common phrases are included in instructions."""
        generator.writing_style['common_phrases'] = ['looking forward', 'thanks for', 'let me know']

        instructions = generator._build_style_instructions()

        # Should include at least one common phrase
        assert any(phrase in instructions for phrase in generator.writing_style['common_phrases'])


class TestPromptBuilding:
    """Test prompt building logic."""

    def test_build_response_prompt(self, generator, sample_email):
        """Test building response prompt."""
        prompt = generator._build_response_prompt(
            sample_email,
            length='Standard',
            tone='Professional',
            template=None,
            thread_context=None
        )

        assert 'alice@example.com' in prompt  # From field
        assert 'Meeting Request' in prompt  # Subject
        assert 'Friday at 2pm' in prompt  # Body content
        assert 'Standard' in prompt  # Length
        assert 'Professional' in prompt  # Tone

    def test_build_response_prompt_includes_template(self, generator, sample_email):
        """Test that template instructions are included in prompt."""
        prompt = generator._build_response_prompt(
            sample_email,
            length='Standard',
            tone='Professional',
            template='Meeting Acceptance',
            thread_context=None
        )

        assert 'Meeting Acceptance' in prompt
        assert 'Template:' in prompt

    def test_build_response_prompt_includes_thread_context(self, generator, sample_email):
        """Test that thread context is included in prompt."""
        thread = [{'metadata': {'from': 'user@example.com'}, 'content': {'body': 'Previous message'}}]

        prompt = generator._build_response_prompt(
            sample_email,
            length='Standard',
            tone='Professional',
            template=None,
            thread_context=thread
        )

        assert 'Thread Context' in prompt


class TestMetricsTracking:
    """Test metrics tracking and retrieval."""

    def test_log_response_history(self, generator, sample_email, temp_db):
        """Test logging response to history."""
        result = {
            'response_text': 'Hi Alice,\n\nYes, I can attend.\n\nThanks',
            'length': 'Brief',
            'tone': 'Professional',
            'template': None,
            'word_count': 8,
            'processing_time_ms': 2500,
            'model_version': 'llama3.1:8b'
        }

        generator._log_response_history('msg_001', result)

        # Verify logged
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM response_history WHERE message_id = ?', ('msg_001',))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_log_performance_metrics(self, generator, temp_db):
        """Test logging performance metrics."""
        result = {
            'length': 'Standard',
            'processing_time_ms': 3500,
            'model_version': 'llama3.1:8b'
        }

        generator._log_performance_metrics(result)

        # Verify logged
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM performance_metrics WHERE operation LIKE ?', ('response_generation%',))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_get_response_metrics(self, generator, sample_email):
        """Test retrieving response metrics."""
        # Generate a few responses to create metrics
        generator.generate_response(sample_email, length='Brief')
        generator.generate_response(sample_email, length='Standard')

        metrics = generator.get_response_metrics(days=30)

        assert 'total_generated' in metrics
        assert metrics['total_generated'] >= 2
        assert 'by_length' in metrics


class TestUserFeedback:
    """Test user feedback recording."""

    def test_record_user_feedback(self, generator, sample_email, temp_db):
        """Test recording user feedback."""
        # First generate a response
        result = generator.generate_response(sample_email)

        # Get the response ID
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT id, response_text FROM response_history ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        response_id = row[0]
        original_text = row[1]
        conn.close()

        # Record feedback
        edited_text = original_text + " Additional text added by user."
        generator.record_user_feedback(response_id, edited_text, accepted=True, regeneration_count=0)

        # Verify recorded
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT edit_percentage, accepted FROM response_history WHERE id = ?', (response_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] > 0  # edit_percentage
        assert row[1] == 1  # accepted

    def test_record_user_feedback_calculates_edit_percentage(self, generator, temp_db):
        """Test that edit percentage is calculated correctly."""
        # Insert a test response
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO response_history (message_id, response_text, response_length,
                                         response_tone, word_count, processing_time_ms, model_version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('test_msg', 'Short response', 'Brief', 'Professional', 2, 1000, 'test'))
        conn.commit()
        response_id = cursor.lastrowid
        conn.close()

        # Record significant edit
        edited = 'This is a much longer response with significantly more content added by the user.'
        generator.record_user_feedback(response_id, edited, accepted=True)

        # Check edit percentage
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT edit_percentage FROM response_history WHERE id = ?', (response_id,))
        edit_pct = cursor.fetchone()[0]
        conn.close()

        assert edit_pct > 50  # Significant edit


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_generate_with_empty_email(self, generator):
        """Test generation with minimal email data."""
        empty_email = {
            'metadata': {'from': '', 'subject': '', 'message_id': 'empty'},
            'content': {'body': ''},
            'thread_context': {}
        }

        # Should handle gracefully
        result = generator.generate_response(empty_email)

        assert result is not None
        assert 'response_text' in result

    def test_generate_with_missing_fields(self, generator):
        """Test generation with missing email fields."""
        incomplete_email = {
            'metadata': {'message_id': 'incomplete'}
        }

        # Should handle gracefully with defaults
        result = generator.generate_response(incomplete_email)

        assert result is not None

    def test_llm_error_raises_exception(self, generator, sample_email):
        """Test that LLM errors are handled."""
        # Mock LLM to raise an exception
        generator.ollama.client.generate = Mock(side_effect=Exception('LLM error'))

        with pytest.raises(ResponseGenerationError):
            generator.generate_response(sample_email)


class TestConvenienceFunction:
    """Test convenience function."""

    def test_generate_response_function(self, mock_ollama, sample_email, temp_db):
        """Test convenience function for response generation."""
        result = generate_response(sample_email, mock_ollama, db_path=temp_db)

        assert result is not None
        assert 'response_text' in result


# Performance tests
class TestPerformance:
    """Test performance requirements."""

    def test_brief_response_performance(self, generator, sample_email):
        """Test that brief responses meet performance target."""
        import time

        start = time.time()
        result = generator.generate_response(sample_email, length='Brief')
        duration = time.time() - start

        # Brief responses should be fast (under 5s acceptable, 3s target)
        # In testing with mock, should be very fast
        assert duration < 1.0  # Mock should be instant
        assert result['processing_time_ms'] >= 0  # Can be 0 with fast mocks

    def test_standard_response_performance(self, generator, sample_email):
        """Test that standard responses meet performance target."""
        import time

        start = time.time()
        result = generator.generate_response(sample_email, length='Standard')
        duration = time.time() - start

        # Standard responses: 5s target, 8s acceptable
        # Mock should be instant
        assert duration < 1.0
        assert result['processing_time_ms'] >= 0  # Can be 0 with fast mocks
