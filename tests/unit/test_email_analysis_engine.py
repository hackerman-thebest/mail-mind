"""
Unit tests for EmailAnalysisEngine.

Tests Story 1.3: Real-Time Analysis Engine

Coverage:
- AC1: Progressive disclosure (quick priority heuristic)
- AC2: Priority classification
- AC3: Email summarization
- AC4: Topic/tag extraction
- AC5: Sentiment analysis
- AC6: Action item extraction
- AC7: Performance monitoring
- AC8: Result caching
- AC9: Batch processing
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch
from src.mailmind.core.email_analysis_engine import (
    EmailAnalysisEngine,
    EmailAnalysisError,
    analyze_email
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
    """Mock OllamaManager."""
    ollama = Mock()
    ollama.current_model = 'llama3.1:8b-instruct-q4_K_M'
    ollama.context_window = 8192
    ollama.client = Mock()
    return ollama


@pytest.fixture
def analysis_engine(mock_ollama, temp_db):
    """Create EmailAnalysisEngine instance with mocked dependencies."""
    return EmailAnalysisEngine(mock_ollama, db_path=temp_db)


@pytest.fixture
def sample_email():
    """Sample email for testing."""
    return {
        'from': 'alice@company.com (Alice Smith)',
        'subject': 'URGENT: Q4 Budget Review Needed',
        'body': '''Hi team,

We need to review the Q4 budget immediately. We're tracking 5% over budget.

Please review the attached spreadsheet and send your feedback by Friday.

Thanks,
Alice''',
        'date': '2025-10-13T14:30:00Z',
        'message_id': 'msg_urgent_budget'
    }


@pytest.fixture
def sample_llm_response():
    """Sample LLM response with valid JSON."""
    return {
        'response': '''```json
{
  "priority": "High",
  "confidence": 0.95,
  "summary": "Budget overrun alert for Q4. Team lead requests immediate review of spending and feedback by Friday.",
  "tags": ["budget", "q4", "urgent", "deadline", "review"],
  "sentiment": "urgent",
  "action_items": ["Review budget spreadsheet", "Send feedback by Friday"]
}
```''',
        'total_duration': 2000000000,  # 2 seconds in nanoseconds
        'eval_count': 100
    }


class TestEmailAnalysisEngineInitialization:
    """Test initialization and database setup."""

    def test_initialization(self, mock_ollama, temp_db):
        """Test that engine initializes correctly."""
        engine = EmailAnalysisEngine(mock_ollama, db_path=temp_db)

        assert engine.ollama == mock_ollama
        assert engine.db_path == temp_db
        assert engine.preprocessor is not None
        assert os.path.exists(temp_db)

    def test_database_tables_created(self, analysis_engine, temp_db):
        """Test that database tables are created."""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check email_analysis table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_analysis'")
        assert cursor.fetchone() is not None

        # Check performance_metrics table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='performance_metrics'")
        assert cursor.fetchone() is not None

        conn.close()


class TestQuickPriorityHeuristic:
    """Test AC1: Quick priority heuristic for progressive disclosure."""

    def test_high_priority_urgent_keyword(self, analysis_engine):
        """Test that URGENT keyword triggers high priority."""
        email = {
            'metadata': {'subject': 'URGENT: Action Required', 'from': 'test@example.com'},
            'content': {'body': 'Please respond immediately'},
            'thread_context': {'is_reply': False}
        }

        priority = analysis_engine._quick_priority_heuristic(email)
        assert priority == 'High'

    def test_high_priority_deadline(self, analysis_engine):
        """Test that deadline keywords trigger high priority."""
        email = {
            'metadata': {'subject': 'Project Update', 'from': 'test@example.com'},
            'content': {'body': 'Please complete this by end of day tomorrow'},
            'thread_context': {'is_reply': False}
        }

        priority = analysis_engine._quick_priority_heuristic(email)
        assert priority == 'High'

    def test_medium_priority_thread_reply(self, analysis_engine):
        """Test that replies in active threads get medium priority."""
        email = {
            'metadata': {'subject': 'Re: Discussion', 'from': 'test@example.com'},
            'content': {'body': 'Here are my thoughts on the topic'},
            'thread_context': {'is_reply': True, 'thread_length': 5}
        }

        priority = analysis_engine._quick_priority_heuristic(email)
        assert priority == 'Medium'

    def test_low_priority_default(self, analysis_engine):
        """Test that emails with no indicators get low priority."""
        email = {
            'metadata': {'subject': 'Newsletter', 'from': 'marketing@example.com'},
            'content': {'body': 'Check out our latest products'},
            'thread_context': {'is_reply': False}
        }

        priority = analysis_engine._quick_priority_heuristic(email)
        assert priority == 'Low'


class TestPromptBuilding:
    """Test prompt construction."""

    def test_build_basic_prompt(self, analysis_engine):
        """Test building prompt from email data."""
        email = {
            'metadata': {
                'from': 'alice@example.com',
                'subject': 'Test Email',
                'date': '2025-10-13T10:00:00Z'
            },
            'content': {
                'body': 'This is a test email body.',
                'has_attachments': False,
                'attachments': []
            },
            'thread_context': {
                'is_reply': False
            }
        }

        prompt = analysis_engine._build_analysis_prompt(email)

        assert 'alice@example.com' in prompt
        assert 'Test Email' in prompt
        assert 'This is a test email body' in prompt
        assert 'JSON' in prompt
        assert 'priority' in prompt.lower()

    def test_prompt_includes_thread_context(self, analysis_engine):
        """Test that thread context is included in prompt."""
        email = {
            'metadata': {'from': 'test@example.com', 'subject': 'Re: Discussion', 'date': '2025-10-13'},
            'content': {'body': 'Reply here', 'has_attachments': False, 'attachments': []},
            'thread_context': {'is_reply': True, 'thread_length': 3}
        }

        prompt = analysis_engine._build_analysis_prompt(email)

        assert 'reply' in prompt.lower()
        assert 'thread' in prompt.lower()

    def test_prompt_includes_attachments(self, analysis_engine):
        """Test that attachments are mentioned in prompt."""
        email = {
            'metadata': {'from': 'test@example.com', 'subject': 'Files', 'date': '2025-10-13'},
            'content': {
                'body': 'See attached',
                'has_attachments': True,
                'attachments': ['report.pdf (1.2MB)', 'data.xlsx (500KB)']
            },
            'thread_context': {'is_reply': False}
        }

        prompt = analysis_engine._build_analysis_prompt(email)

        assert 'report.pdf' in prompt
        assert 'data.xlsx' in prompt


class TestResponseParsing:
    """Test AC2-AC6: Parsing LLM responses."""

    def test_parse_valid_json(self, analysis_engine):
        """Test parsing valid JSON response."""
        response = '''{
  "priority": "High",
  "confidence": 0.92,
  "summary": "Test summary here",
  "tags": ["tag1", "tag2"],
  "sentiment": "urgent",
  "action_items": ["Action 1", "Action 2"]
}'''

        analysis = analysis_engine._parse_analysis_response(response)

        assert analysis['priority'] == 'High'
        assert analysis['confidence'] == 0.92
        assert 'Test summary' in analysis['summary']
        assert analysis['tags'] == ['tag1', 'tag2']
        assert analysis['sentiment'] == 'urgent'
        assert len(analysis['action_items']) == 2

    def test_parse_json_with_markdown(self, analysis_engine):
        """Test parsing JSON wrapped in markdown code block."""
        response = '''```json
{
  "priority": "Medium",
  "confidence": 0.75,
  "summary": "Summary text",
  "tags": ["test"],
  "sentiment": "neutral",
  "action_items": []
}
```'''

        analysis = analysis_engine._parse_analysis_response(response)

        assert analysis['priority'] == 'Medium'
        assert analysis['confidence'] == 0.75

    def test_parse_invalid_json_fallback(self, analysis_engine):
        """Test fallback parsing when JSON is invalid."""
        response = "The email has HIGH priority and discusses budget issues."

        analysis = analysis_engine._parse_analysis_response(response)

        # Should use fallback parsing
        assert 'priority' in analysis
        assert analysis['priority'] == 'High'  # Detected from text
        assert 'summary' in analysis

    def test_parse_normalizes_tags(self, analysis_engine):
        """Test that tags are normalized to lowercase."""
        response = '''{
  "priority": "Low",
  "confidence": 0.6,
  "summary": "Test",
  "tags": ["Budget", "URGENT", "Project-Alpha"],
  "sentiment": "neutral",
  "action_items": []
}'''

        analysis = analysis_engine._parse_analysis_response(response)

        assert all(tag.islower() for tag in analysis['tags'])
        assert 'budget' in analysis['tags']
        assert 'urgent' in analysis['tags']

    def test_parse_limits_tags_to_five(self, analysis_engine):
        """Test that tags are limited to 5."""
        response = '''{
  "priority": "Medium",
  "confidence": 0.7,
  "summary": "Test",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7"],
  "sentiment": "neutral",
  "action_items": []
}'''

        analysis = analysis_engine._parse_analysis_response(response)

        assert len(analysis['tags']) == 5

    def test_parse_limits_action_items_to_five(self, analysis_engine):
        """Test that action items are limited to 5."""
        response = '''{
  "priority": "High",
  "confidence": 0.9,
  "summary": "Test",
  "tags": ["test"],
  "sentiment": "urgent",
  "action_items": ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
}'''

        analysis = analysis_engine._parse_analysis_response(response)

        assert len(analysis['action_items']) == 5


class TestCaching:
    """Test AC8: Result caching."""

    def test_cache_stores_analysis(self, analysis_engine, temp_db):
        """Test that analysis is stored in cache."""
        message_id = 'test_msg_123'
        email = {
            'metadata': {
                'from': 'test@example.com',
                'subject': 'Test',
                'date': '2025-10-13',
                'message_id': message_id
            }
        }
        analysis = {
            'priority': 'High',
            'confidence': 0.9,
            'summary': 'Test summary',
            'tags': ['test'],
            'sentiment': 'urgent',
            'action_items': [],
            'processing_time_ms': 1500,
            'tokens_per_second': 50.0,
            'model_version': 'llama3.1:8b-instruct-q4_K_M'
        }

        analysis_engine._cache_analysis(message_id, email, analysis)

        # Verify it's in database
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM email_analysis WHERE message_id = ?', (message_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_cache_retrieval(self, analysis_engine, temp_db):
        """Test that cached analysis can be retrieved."""
        message_id = 'test_msg_456'
        email = {
            'metadata': {
                'from': 'test@example.com',
                'subject': 'Test',
                'date': '2025-10-13',
                'message_id': message_id
            }
        }
        analysis = {
            'priority': 'Medium',
            'confidence': 0.7,
            'summary': 'Cached test',
            'tags': ['cache', 'test'],
            'sentiment': 'neutral',
            'action_items': [],
            'processing_time_ms': 1000,
            'tokens_per_second': 45.0,
            'model_version': 'llama3.1:8b-instruct-q4_K_M'
        }

        # Store
        analysis_engine._cache_analysis(message_id, email, analysis)

        # Retrieve
        cached = analysis_engine._get_cached_analysis(message_id)

        assert cached is not None
        assert cached['priority'] == 'Medium'
        assert cached['summary'] == 'Cached test'
        assert 'cache' in cached['tags']

    def test_cache_invalidation_on_model_change(self, analysis_engine, temp_db):
        """Test that cache is invalidated when model version changes."""
        message_id = 'test_msg_789'
        email = {
            'metadata': {
                'from': 'test@example.com',
                'subject': 'Test',
                'date': '2025-10-13',
                'message_id': message_id
            }
        }
        analysis = {
            'priority': 'Low',
            'confidence': 0.6,
            'summary': 'Old model',
            'tags': ['old'],
            'sentiment': 'neutral',
            'action_items': [],
            'processing_time_ms': 1200,
            'tokens_per_second': 40.0,
            'model_version': 'old-model-version'
        }

        # Store with old model version
        analysis_engine._cache_analysis(message_id, email, analysis)

        # Try to retrieve (current model is different)
        cached = analysis_engine._get_cached_analysis(message_id)

        # Should return None (cache invalidated)
        assert cached is None


class TestBatchProcessing:
    """Test AC9: Batch processing."""

    @patch('src.mailmind.core.email_analysis_engine.EmailPreprocessor')
    def test_batch_processing(self, mock_preprocessor_class, analysis_engine, mock_ollama, sample_llm_response):
        """Test batch processing of multiple emails."""
        # Setup mocks
        mock_preprocessor = Mock()
        mock_preprocessor_class.return_value = mock_preprocessor

        mock_preprocessor.preprocess_email.side_effect = [
            {
                'metadata': {'message_id': f'msg_{i}', 'from': 'test@example.com', 'subject': f'Email {i}', 'date': '2025-10-13'},
                'content': {'body': f'Body {i}', 'has_attachments': False, 'attachments': []},
                'thread_context': {'is_reply': False}
            }
            for i in range(3)
        ]

        mock_ollama.client.generate.return_value = sample_llm_response

        # Create engine with mocked preprocessor
        analysis_engine.preprocessor = mock_preprocessor

        emails = [
            {'subject': 'Email 1', 'body': 'Test 1'},
            {'subject': 'Email 2', 'body': 'Test 2'},
            {'subject': 'Email 3', 'body': 'Test 3'}
        ]

        results = analysis_engine.analyze_batch(emails)

        assert len(results) == 3
        assert all('priority' in r for r in results)

    def test_batch_with_callback(self, analysis_engine, mock_ollama, sample_llm_response):
        """Test batch processing with progress callback."""
        mock_ollama.client.generate.return_value = sample_llm_response

        progress_updates = []

        def callback(current, total, result):
            progress_updates.append((current, total))

        emails = [
            {'subject': f'Email {i}', 'body': f'Body {i}', 'message_id': f'msg_{i}'}
            for i in range(3)
        ]

        results = analysis_engine.analyze_batch(emails, callback=callback)

        assert len(progress_updates) == 3
        assert progress_updates[-1] == (3, 3)  # Final update


class TestPerformanceMetrics:
    """Test AC7: Performance monitoring."""

    def test_calculate_tokens_per_sec(self, analysis_engine):
        """Test tokens per second calculation."""
        response = {
            'total_duration': 2000000000,  # 2 seconds in nanoseconds
            'eval_count': 100
        }

        tokens_per_sec = analysis_engine._calculate_tokens_per_sec(response)

        assert tokens_per_sec == 50.0  # 100 tokens / 2 seconds

    def test_performance_logging(self, analysis_engine, temp_db):
        """Test that performance metrics are logged."""
        analysis = {
            'priority': 'High',
            'model_version': 'llama3.1:8b-instruct-q4_K_M',
            'tokens_per_second': 55.0,
            'processing_time_ms': 1800
        }

        analysis_engine._log_performance(analysis, operation='test_analysis')

        # Verify in database
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM performance_metrics WHERE operation = ?', ('test_analysis',))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_get_analysis_stats(self, analysis_engine, temp_db):
        """Test getting analysis statistics."""
        # Create some test data
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        for i in range(5):
            cursor.execute('''
                INSERT INTO email_analysis (
                    message_id, subject, sender, analysis_json,
                    priority, confidence_score, processing_time_ms,
                    tokens_per_second, model_version, cache_hit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f'msg_{i}', f'Subject {i}', 'test@example.com', '{}',
                'High' if i < 2 else 'Medium', 0.9, 1500 + i*100, 50.0, 'test-model', 0
            ))

        conn.commit()
        conn.close()

        stats = analysis_engine.get_analysis_stats()

        assert stats['total_analyses'] == 5
        assert 'High' in stats['priority_distribution']
        assert stats['avg_processing_time_ms'] > 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_default_analysis(self, analysis_engine):
        """Test that default analysis is returned on error."""
        default = analysis_engine._default_analysis("Test error")

        assert default['priority'] == 'Medium'
        assert default['confidence'] == 0.3
        assert 'error' in default
        assert default['error'] == 'Test error'

    @patch('src.mailmind.core.email_analysis_engine.EmailPreprocessor')
    def test_analysis_continues_on_llm_error(self, mock_preprocessor_class, analysis_engine, mock_ollama):
        """Test that analysis returns default on LLM error."""
        mock_preprocessor = Mock()
        mock_preprocessor_class.return_value = mock_preprocessor

        mock_preprocessor.preprocess_email.return_value = {
            'metadata': {'message_id': 'test_msg', 'from': 'test@example.com', 'subject': 'Test', 'date': '2025-10-13'},
            'content': {'body': 'Test body', 'has_attachments': False, 'attachments': []},
            'thread_context': {'is_reply': False}
        }

        mock_ollama.client.generate.side_effect = Exception("LLM error")

        analysis_engine.preprocessor = mock_preprocessor

        result = analysis_engine.analyze_email({'test': 'email'})

        # Should return default analysis, not raise exception
        assert 'priority' in result
        assert 'error' in result or result['priority'] == 'Medium'


class TestConvenienceFunction:
    """Test convenience function."""

    @patch('src.mailmind.core.email_analysis_engine.EmailAnalysisEngine')
    def test_analyze_email_convenience_function(self, mock_engine_class, mock_ollama):
        """Test the analyze_email convenience function."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.analyze_email.return_value = {'priority': 'High'}

        result = analyze_email({'test': 'email'}, mock_ollama)

        assert result['priority'] == 'High'
        mock_engine_class.assert_called_once()
        mock_engine.analyze_email.assert_called_once()
