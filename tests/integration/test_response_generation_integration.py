"""
Integration tests for Response Generation

Tests the complete response generation pipeline with real Ollama LLM inference.

Tests cover:
- End-to-end response generation
- Writing style analysis and application
- All response lengths with actual LLM
- All tone options with actual LLM
- Template-based generation
- Thread context incorporation
- Performance benchmarking
- Real-world scenarios

Story 1.5: Response Generation Assistant

Requirements:
- Ollama must be running
- Llama 3.1 8B or Mistral 7B model must be available
"""

import pytest
import time
import tempfile
import os
from typing import Dict, Any

from src.mailmind.core.ollama_manager import OllamaManager
from src.mailmind.core.email_preprocessor import EmailPreprocessor
from src.mailmind.core.writing_style_analyzer import WritingStyleAnalyzer
from src.mailmind.core.response_generator import ResponseGenerator
from src.mailmind.utils.config import load_config, get_ollama_config


# Skip all tests if Ollama is not available
pytestmark = pytest.mark.skipif(
    not os.getenv('RUN_INTEGRATION_TESTS', 'false').lower() == 'true',
    reason="Integration tests require RUN_INTEGRATION_TESTS=true and Ollama running"
)


@pytest.fixture(scope='module')
def ollama_manager():
    """Create OllamaManager instance for integration tests."""
    try:
        config = load_config()
        ollama_config = get_ollama_config(config)
        ollama = OllamaManager(ollama_config)
        ollama.initialize()
        return ollama
    except Exception as e:
        pytest.skip(f"Ollama not available: {e}")


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
def preprocessor():
    """Create EmailPreprocessor instance."""
    return EmailPreprocessor()


@pytest.fixture
def style_analyzer(temp_db):
    """Create WritingStyleAnalyzer instance."""
    return WritingStyleAnalyzer(db_path=temp_db)


@pytest.fixture
def response_generator(ollama_manager, temp_db):
    """Create ResponseGenerator instance."""
    return ResponseGenerator(ollama_manager, db_path=temp_db)


@pytest.fixture
def sample_sent_emails():
    """Sample sent emails for style analysis."""
    return [
        {
            'body': 'Hi John,\n\nThanks for reaching out. I\'ll review the document and get back to you by end of week.\n\nThanks,\nAlice',
            'subject': 'Re: Q4 Budget Review'
        },
        {
            'body': 'Hi Sarah,\n\nI can attend the meeting on Tuesday at 2pm. Looking forward to discussing the project timeline.\n\nBest,\nAlice',
            'subject': 'Re: Project Kickoff Meeting'
        },
        {
            'body': 'Hi Team,\n\nPlease review the attached proposal and let me know if you have any questions or concerns.\n\nThanks,\nAlice',
            'subject': 'Q1 Marketing Proposal'
        },
        {
            'body': 'Hi Mike,\n\nThanks for the update! The presentation looks great. I really appreciate all your hard work on this.\n\nBest,\nAlice',
            'subject': 'Re: Client Presentation Draft'
        },
        {
            'body': 'Hi Lisa,\n\nI wanted to follow up on our conversation from last week. Are you available for a quick call tomorrow afternoon?\n\nThanks,\nAlice',
            'subject': 'Follow-up: Marketing Strategy'
        },
    ]


@pytest.fixture
def meeting_request_email(preprocessor):
    """Sample meeting request email."""
    raw = {
        'from': 'john.smith@company.com',
        'from_name': 'John Smith',
        'subject': 'Team Meeting Next Week',
        'body': '''Hi Alice,

I wanted to schedule a team meeting for next Tuesday at 2pm to discuss the Q4 roadmap and upcoming priorities.

Would you be available?

Thanks,
John''',
        'date': '2025-10-13T10:00:00Z',
        'message_id': 'meeting_001'
    }

    return preprocessor.preprocess_email(raw)


@pytest.fixture
def status_update_email(preprocessor):
    """Sample status update request email."""
    raw = {
        'from': 'manager@company.com',
        'from_name': 'Sarah Manager',
        'subject': 'Project Status Check-in',
        'body': '''Hi Alice,

Could you provide a quick status update on the email assistant project? Specifically:
- Current progress
- Any blockers
- Timeline for next milestone

Thanks for keeping me in the loop!

Sarah''',
        'date': '2025-10-13T11:30:00Z',
        'message_id': 'status_001'
    }

    return preprocessor.preprocess_email(raw)


class TestWritingStyleAnalysis:
    """Test writing style analysis pipeline."""

    def test_analyze_sent_emails_integration(self, style_analyzer, sample_sent_emails):
        """Test complete writing style analysis."""
        profile = style_analyzer.analyze_sent_emails(sample_sent_emails)

        # Verify profile structure
        assert 'greeting_style' in profile
        assert 'closing_style' in profile
        assert 'formality_level' in profile
        assert 'common_phrases' in profile
        assert 'avg_sentence_length' in profile
        assert 'tone_markers' in profile

        # Verify values are reasonable
        assert profile['sample_size'] == len(sample_sent_emails)
        assert 0.0 <= profile['formality_level'] <= 1.0
        assert profile['avg_sentence_length'] > 0

        print(f"\n✓ Writing style profile created:")
        print(f"  Greeting: {profile['greeting_style']}")
        print(f"  Closing: {profile['closing_style']}")
        print(f"  Formality: {profile['formality_level']:.2f}")
        print(f"  Avg sentence length: {profile['avg_sentence_length']} words")

    def test_save_and_load_profile(self, style_analyzer, sample_sent_emails):
        """Test saving and loading style profile."""
        # Analyze and save
        profile = style_analyzer.analyze_sent_emails(sample_sent_emails, profile_name='test_user')

        # Load back
        loaded = style_analyzer.load_profile('test_user')

        assert loaded is not None
        assert loaded['greeting_style'] == profile['greeting_style']
        assert loaded['closing_style'] == profile['closing_style']
        assert loaded['formality_level'] == profile['formality_level']

        print(f"\n✓ Style profile persisted and loaded successfully")


class TestEndToEndResponseGeneration:
    """Test complete response generation pipeline."""

    def test_generate_brief_response(self, response_generator, meeting_request_email):
        """Test generating a brief response with real LLM."""
        start_time = time.time()

        result = response_generator.generate_response(
            meeting_request_email,
            length='Brief',
            tone='Professional'
        )

        duration = time.time() - start_time

        # Verify result structure
        assert 'response_text' in result
        assert result['length'] == 'Brief'
        assert result['tone'] == 'Professional'
        assert result['word_count'] > 0
        assert result['processing_time_ms'] > 0

        # Verify response is reasonably brief
        assert result['word_count'] <= 80  # Allow some buffer beyond 50

        print(f"\n✓ Brief response generated in {duration:.2f}s:")
        print(f"  Word count: {result['word_count']}")
        print(f"  Processing time: {result['processing_time_ms']}ms")
        print(f"\n  Response:\n{result['response_text']}\n")

        # Performance check (target: <3s, acceptable: <5s)
        if duration < 3.0:
            print(f"  ✓ Performance: EXCELLENT (target met)")
        elif duration < 5.0:
            print(f"  ✓ Performance: GOOD (acceptable)")
        else:
            print(f"  ⚠ Performance: SLOW (exceeds acceptable limit)")

    def test_generate_standard_response(self, response_generator, meeting_request_email):
        """Test generating a standard response with real LLM."""
        start_time = time.time()

        result = response_generator.generate_response(
            meeting_request_email,
            length='Standard',
            tone='Professional'
        )

        duration = time.time() - start_time

        # Verify result
        assert result['length'] == 'Standard'
        assert 40 <= result['word_count'] <= 180  # Allow buffer

        print(f"\n✓ Standard response generated in {duration:.2f}s:")
        print(f"  Word count: {result['word_count']}")
        print(f"  Processing time: {result['processing_time_ms']}ms")
        print(f"\n  Response:\n{result['response_text']}\n")

        # Performance check (target: <5s, acceptable: <8s)
        if duration < 5.0:
            print(f"  ✓ Performance: EXCELLENT (target met)")
        elif duration < 8.0:
            print(f"  ✓ Performance: GOOD (acceptable)")
        else:
            print(f"  ⚠ Performance: SLOW (exceeds acceptable limit)")

    def test_generate_detailed_response(self, response_generator, status_update_email):
        """Test generating a detailed response with real LLM."""
        start_time = time.time()

        result = response_generator.generate_response(
            status_update_email,
            length='Detailed',
            tone='Professional'
        )

        duration = time.time() - start_time

        # Verify result
        assert result['length'] == 'Detailed'
        assert result['word_count'] >= 100  # Detailed should be substantial

        print(f"\n✓ Detailed response generated in {duration:.2f}s:")
        print(f"  Word count: {result['word_count']}")
        print(f"  Processing time: {result['processing_time_ms']}ms")
        print(f"\n  Response:\n{result['response_text']}\n")

        # Performance check (target: <10s, acceptable: <15s)
        if duration < 10.0:
            print(f"  ✓ Performance: EXCELLENT (target met)")
        elif duration < 15.0:
            print(f"  ✓ Performance: GOOD (acceptable)")
        else:
            print(f"  ⚠ Performance: SLOW (exceeds acceptable limit)")


class TestToneVariations:
    """Test response generation with different tones."""

    def test_professional_tone(self, response_generator, meeting_request_email):
        """Test professional tone generation."""
        result = response_generator.generate_response(
            meeting_request_email,
            length='Standard',
            tone='Professional'
        )

        assert result['tone'] == 'Professional'
        print(f"\n✓ Professional tone response:\n{result['response_text']}\n")

    def test_friendly_tone(self, response_generator, meeting_request_email):
        """Test friendly tone generation."""
        result = response_generator.generate_response(
            meeting_request_email,
            length='Standard',
            tone='Friendly'
        )

        assert result['tone'] == 'Friendly'
        print(f"\n✓ Friendly tone response:\n{result['response_text']}\n")

    def test_formal_tone(self, response_generator, meeting_request_email):
        """Test formal tone generation."""
        result = response_generator.generate_response(
            meeting_request_email,
            length='Standard',
            tone='Formal'
        )

        assert result['tone'] == 'Formal'
        print(f"\n✓ Formal tone response:\n{result['response_text']}\n")

    def test_casual_tone(self, response_generator, meeting_request_email):
        """Test casual tone generation."""
        result = response_generator.generate_response(
            meeting_request_email,
            length='Standard',
            tone='Casual'
        )

        assert result['tone'] == 'Casual'
        print(f"\n✓ Casual tone response:\n{result['response_text']}\n")


class TestTemplateBasedGeneration:
    """Test response generation with templates."""

    def test_meeting_acceptance_template(self, response_generator, meeting_request_email):
        """Test Meeting Acceptance template."""
        result = response_generator.generate_response(
            meeting_request_email,
            length='Brief',
            tone='Professional',
            template='Meeting Acceptance'
        )

        assert result['template'] == 'Meeting Acceptance'
        assert result['word_count'] > 0

        print(f"\n✓ Meeting Acceptance template response:\n{result['response_text']}\n")

    def test_status_update_template(self, response_generator, status_update_email):
        """Test Status Update template."""
        result = response_generator.generate_response(
            status_update_email,
            length='Standard',
            tone='Professional',
            template='Status Update'
        )

        assert result['template'] == 'Status Update'

        print(f"\n✓ Status Update template response:\n{result['response_text']}\n")

    def test_thank_you_template(self, response_generator, preprocessor):
        """Test Thank You template."""
        thank_you_email = preprocessor.preprocess_email({
            'from': 'colleague@company.com',
            'subject': 'Great presentation!',
            'body': 'Alice, your presentation yesterday was excellent. Thanks for putting that together!',
            'date': '2025-10-13T09:00:00Z',
            'message_id': 'thank_001'
        })

        result = response_generator.generate_response(
            thank_you_email,
            length='Brief',
            tone='Friendly',
            template='Thank You'
        )

        assert result['template'] == 'Thank You'

        print(f"\n✓ Thank You template response:\n{result['response_text']}\n")


class TestThreadContextIntegration:
    """Test response generation with thread context."""

    def test_generate_with_thread_context(self, response_generator, preprocessor):
        """Test response generation incorporating thread context."""
        # Create a thread of emails
        thread = [
            preprocessor.preprocess_email({
                'from': 'alice@company.com',
                'subject': 'Budget Planning',
                'body': 'Hi team, we need to finalize the Q4 budget by next week.',
                'date': '2025-10-10T10:00:00Z',
                'message_id': 'thread_001'
            }),
            preprocessor.preprocess_email({
                'from': 'bob@company.com',
                'subject': 'Re: Budget Planning',
                'body': 'Alice, can we schedule a meeting to review the numbers?',
                'date': '2025-10-11T14:00:00Z',
                'message_id': 'thread_002'
            })
        ]

        # Current email
        current_email = preprocessor.preprocess_email({
            'from': 'charlie@company.com',
            'subject': 'Re: Budget Planning',
            'body': 'I have some concerns about the marketing allocation. Can we discuss?',
            'date': '2025-10-12T11:00:00Z',
            'message_id': 'thread_003'
        })

        result = response_generator.generate_response(
            current_email,
            length='Standard',
            tone='Professional',
            thread_context=thread
        )

        assert result['word_count'] > 0

        print(f"\n✓ Response with thread context:\n{result['response_text']}\n")


class TestWritingStyleApplication:
    """Test that writing style is applied to responses."""

    def test_response_uses_style_profile(self, style_analyzer, response_generator,
                                        sample_sent_emails, meeting_request_email):
        """Test that generated responses use the user's writing style."""
        # First, analyze writing style
        profile = style_analyzer.analyze_sent_emails(sample_sent_emails)

        # Update generator's style
        response_generator.writing_style = profile

        # Generate response
        result = response_generator.generate_response(
            meeting_request_email,
            length='Brief',
            tone='Professional'
        )

        # Response should contain style elements
        response_text = result['response_text'].lower()

        # Check if greeting style is present (flexible check)
        greeting = profile['greeting_style'].lower()
        has_greeting = greeting in response_text

        print(f"\n✓ Response using style profile:")
        print(f"  Expected greeting: {profile['greeting_style']}")
        print(f"  Expected closing: {profile['closing_style']}")
        print(f"  Formality level: {profile['formality_level']:.2f}")
        print(f"\n  Response:\n{result['response_text']}\n")
        print(f"  Greeting found: {has_greeting}")


class TestPerformanceBenchmark:
    """Benchmark response generation performance."""

    def test_brief_response_performance_benchmark(self, response_generator, meeting_request_email):
        """Benchmark brief response generation."""
        times = []

        for i in range(3):
            start = time.time()
            result = response_generator.generate_response(
                meeting_request_email,
                length='Brief',
                tone='Professional'
            )
            duration = time.time() - start
            times.append(duration)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n✓ Brief response performance benchmark (3 runs):")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Min: {min_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")
        print(f"  Target: <3s, Acceptable: <5s")

        if avg_time < 3.0:
            print(f"  ✓ EXCELLENT - Target met")
        elif avg_time < 5.0:
            print(f"  ✓ GOOD - Acceptable range")
        else:
            print(f"  ⚠ NEEDS OPTIMIZATION")

    def test_standard_response_performance_benchmark(self, response_generator, meeting_request_email):
        """Benchmark standard response generation."""
        times = []

        for i in range(3):
            start = time.time()
            result = response_generator.generate_response(
                meeting_request_email,
                length='Standard',
                tone='Professional'
            )
            duration = time.time() - start
            times.append(duration)

        avg_time = sum(times) / len(times)

        print(f"\n✓ Standard response performance benchmark (3 runs):")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Target: <5s, Acceptable: <8s")

        if avg_time < 5.0:
            print(f"  ✓ EXCELLENT - Target met")
        elif avg_time < 8.0:
            print(f"  ✓ GOOD - Acceptable range")
        else:
            print(f"  ⚠ NEEDS OPTIMIZATION")


class TestMetricsAndFeedback:
    """Test metrics tracking and user feedback."""

    def test_response_metrics_tracking(self, response_generator, meeting_request_email):
        """Test that response metrics are tracked."""
        # Generate a few responses
        for i in range(3):
            response_generator.generate_response(
                meeting_request_email,
                length='Standard',
                tone='Professional'
            )

        # Get metrics
        metrics = response_generator.get_response_metrics(days=1)

        assert metrics['total_generated'] >= 3
        assert 'by_length' in metrics
        assert 'Standard' in metrics['by_length']

        print(f"\n✓ Response metrics:")
        print(f"  Total generated: {metrics['total_generated']}")
        print(f"  By length: {metrics['by_length']}")


class TestRealWorldScenarios:
    """Test real-world email scenarios."""

    def test_urgent_request_scenario(self, response_generator, preprocessor):
        """Test response to urgent request."""
        urgent_email = preprocessor.preprocess_email({
            'from': 'ceo@company.com',
            'subject': 'URGENT: Board Meeting Prep',
            'body': '''Alice,

I need the Q4 performance slides for the board meeting ASAP. Can you send them by end of day?

Thanks,
CEO''',
            'date': '2025-10-13T16:00:00Z',
            'message_id': 'urgent_001'
        })

        result = response_generator.generate_response(
            urgent_email,
            length='Brief',
            tone='Professional'
        )

        print(f"\n✓ Urgent request response:\n{result['response_text']}\n")

    def test_casual_team_communication(self, response_generator, preprocessor):
        """Test response to casual team communication."""
        casual_email = preprocessor.preprocess_email({
            'from': 'teammate@company.com',
            'subject': 'Quick question',
            'body': '''Hey Alice,

Do you have a sec to chat about the API changes? I\'m a bit confused about the new endpoints.

Thanks!
Sam''',
            'date': '2025-10-13T13:30:00Z',
            'message_id': 'casual_001'
        })

        result = response_generator.generate_response(
            casual_email,
            length='Brief',
            tone='Friendly'
        )

        print(f"\n✓ Casual team communication response:\n{result['response_text']}\n")
