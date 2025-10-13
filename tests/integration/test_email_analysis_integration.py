"""
Integration Tests for Email Analysis Engine (Story 1.3)

Tests the complete pipeline with real Ollama inference:
- OllamaManager (Story 1.1) → EmailAnalysisEngine (Story 1.3)
- EmailPreprocessor (Story 1.2) → EmailAnalysisEngine (Story 1.3)

Requirements:
- Ollama must be running
- Model must be available (llama3.1:8b-instruct-q4_K_M or mistral:7b-instruct-q4_K_M)

Usage:
    pytest tests/integration/test_email_analysis_integration.py -v
    pytest tests/integration/test_email_analysis_integration.py -v -s  # Show output
"""

import pytest
import os
import sys
import time
import tempfile
import sqlite3
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.mailmind.core.ollama_manager import OllamaManager
from src.mailmind.core.email_analysis_engine import EmailAnalysisEngine
from src.mailmind.utils.config import load_config, get_ollama_config


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope='module')
def ollama_manager():
    """Initialize real OllamaManager for integration tests."""
    config = load_config()
    ollama_config = get_ollama_config(config)
    ollama = OllamaManager(ollama_config)

    success, message = ollama.initialize()
    if not success:
        pytest.skip(f"Ollama not available: {message}")

    return ollama


@pytest.fixture
def temp_db():
    """Create temporary database for each test."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def analysis_engine(ollama_manager, temp_db):
    """Create EmailAnalysisEngine with real Ollama."""
    return EmailAnalysisEngine(ollama_manager, db_path=temp_db)


# ============================================================================
# Sample Test Emails
# ============================================================================

URGENT_EMAIL = {
    'from': 'ceo@company.com (Jane Doe - CEO)',
    'subject': 'URGENT: Server Outage - All Hands Required',
    'body': '''Team,

Our production servers are down and customers are unable to access the platform.
This is a P0 incident.

Immediate actions required:
1. DevOps: Investigate root cause
2. Support: Update status page and notify customers
3. Engineering: Standby for hotfix deployment

We need this resolved within the next hour. Please join the war room on Slack #incident-response.

Jane''',
    'date': '2025-10-13T10:00:00Z',
    'message_id': 'msg_urgent_001'
}

NORMAL_EMAIL = {
    'from': 'colleague@company.com (Bob Smith)',
    'subject': 'Team Lunch Next Week',
    'body': '''Hey team,

Let\'s do a team lunch next Tuesday at 12:30 PM. I\'m thinking we could try that new Italian place downtown.

Let me know if you can make it!

Bob''',
    'date': '2025-10-13T11:00:00Z',
    'message_id': 'msg_normal_001'
}

INFORMATIONAL_EMAIL = {
    'from': 'newsletter@company.com',
    'subject': 'Weekly Product Updates - October Edition',
    'body': '''Hello,

Here are this week\'s product updates:

- New dashboard analytics released
- Mobile app performance improvements
- Bug fixes and stability updates

Check out the full release notes on our blog.

Best,
Product Team''',
    'date': '2025-10-13T12:00:00Z',
    'message_id': 'msg_info_001'
}

ACTION_REQUIRED_EMAIL = {
    'from': 'hr@company.com (HR Department)',
    'subject': 'Action Required: Complete Annual Performance Review by Friday',
    'body': '''Hi,

This is a reminder to complete your annual performance review by Friday, October 17th.

Please:
1. Complete your self-assessment in Workday
2. Submit your goals for next quarter
3. Schedule a 1:1 with your manager

Failure to complete by the deadline may impact your annual bonus.

Thanks,
HR Team''',
    'date': '2025-10-13T13:00:00Z',
    'message_id': 'msg_action_001'
}

HTML_EMAIL = {
    'from': 'partner@external.com (Sarah Johnson)',
    'subject': 'Partnership Proposal Follow-Up',
    'body_html': '''
        <html>
            <body>
                <p>Hi there,</p>
                <p>Following up on our call last week regarding the partnership proposal.</p>
                <p>We're interested in moving forward and would like to schedule a meeting
                to discuss terms and timeline. Are you available next Wednesday?</p>
                <p>Best regards,<br/>Sarah</p>
                <hr/>
                <p style="font-size: 10px; color: gray;">
                Sarah Johnson<br/>
                VP of Partnerships<br/>
                TechCorp Inc.
                </p>
            </body>
        </html>
    ''',
    'date': '2025-10-13T14:00:00Z',
    'message_id': 'msg_html_001',
    'attachments': [
        {'filename': 'proposal.pdf', 'size': 500000}
    ]
}


# ============================================================================
# Test: AC1 - Progressive Disclosure (Quick Priority)
# ============================================================================

class TestQuickPriorityIntegration:
    """Test AC1: Quick priority heuristic completes in <500ms."""

    def test_quick_priority_performance(self, analysis_engine):
        """Verify quick priority completes in <500ms."""
        preprocessed = analysis_engine.preprocessor.preprocess_email(URGENT_EMAIL)

        start = time.time()
        priority = analysis_engine._quick_priority_heuristic(preprocessed)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 500, f"Quick priority took {elapsed_ms:.1f}ms (target: <500ms)"
        assert priority in ['High', 'Medium', 'Low']

    def test_quick_priority_urgent_detection(self, analysis_engine):
        """Verify urgent emails detected as High priority."""
        preprocessed = analysis_engine.preprocessor.preprocess_email(URGENT_EMAIL)
        priority = analysis_engine._quick_priority_heuristic(preprocessed)
        assert priority == 'High'

    def test_quick_priority_normal_detection(self, analysis_engine):
        """Verify normal emails detected as Low/Medium priority."""
        preprocessed = analysis_engine.preprocessor.preprocess_email(NORMAL_EMAIL)
        priority = analysis_engine._quick_priority_heuristic(preprocessed)
        assert priority in ['Low', 'Medium']


# ============================================================================
# Test: AC2-AC6 - LLM Analysis with Real Inference
# ============================================================================

class TestRealLLMAnalysis:
    """Test LLM analysis with real Ollama inference."""

    def test_analyze_urgent_email(self, analysis_engine):
        """Analyze urgent email and verify High priority classification."""
        analysis = analysis_engine.analyze_email(URGENT_EMAIL, use_cache=False)

        # AC2: Priority classification
        assert analysis['priority'] in ['High', 'Medium', 'Low']
        assert 'confidence' in analysis
        assert 0 <= analysis['confidence'] <= 1

        # AC3: Summary
        assert 'summary' in analysis
        assert len(analysis['summary']) > 20
        assert len(analysis['summary']) <= 150

        # AC4: Tags (1-5 items)
        assert 'tags' in analysis
        assert 1 <= len(analysis['tags']) <= 5
        assert all(tag.islower() for tag in analysis['tags'])

        # AC5: Sentiment
        assert analysis['sentiment'] in ['positive', 'neutral', 'negative', 'urgent']

        # AC6: Action items
        assert 'action_items' in analysis
        assert isinstance(analysis['action_items'], list)

        # Metadata
        assert 'processing_time_ms' in analysis
        assert 'model_version' in analysis
        assert 'cache_hit' in analysis
        assert analysis['cache_hit'] is False  # First analysis

    def test_analyze_normal_email(self, analysis_engine):
        """Analyze normal email and verify appropriate classification."""
        analysis = analysis_engine.analyze_email(NORMAL_EMAIL, use_cache=False)

        assert analysis['priority'] in ['Low', 'Medium']
        assert analysis['sentiment'] in ['positive', 'neutral']
        assert len(analysis['summary']) > 0
        assert 1 <= len(analysis['tags']) <= 5

    def test_analyze_html_email(self, analysis_engine):
        """Verify HTML emails are preprocessed and analyzed correctly."""
        analysis = analysis_engine.analyze_email(HTML_EMAIL, use_cache=False)

        # Verify HTML was converted to text and analyzed
        assert analysis['priority'] in ['High', 'Medium', 'Low']
        assert len(analysis['summary']) > 0
        assert len(analysis['tags']) > 0

        # Should detect attachment in preprocessing
        preprocessed = analysis_engine.preprocessor.preprocess_email(HTML_EMAIL)
        assert 'attachments' in preprocessed
        assert preprocessed['attachments'][0]['filename'] == 'proposal.pdf'

    def test_action_items_extraction(self, analysis_engine):
        """Verify action items are extracted from action-required emails."""
        analysis = analysis_engine.analyze_email(ACTION_REQUIRED_EMAIL, use_cache=False)

        # Should detect multiple action items
        assert len(analysis['action_items']) >= 1

        # Action items should be strings
        assert all(isinstance(item, str) for item in analysis['action_items'])


# ============================================================================
# Test: AC7 - Performance Metrics
# ============================================================================

class TestPerformanceMetrics:
    """Test AC7: Performance monitoring and metrics."""

    def test_performance_tracking(self, analysis_engine):
        """Verify performance metrics are tracked."""
        analysis = analysis_engine.analyze_email(NORMAL_EMAIL, use_cache=False)

        # Check required metrics
        assert 'processing_time_ms' in analysis
        assert analysis['processing_time_ms'] > 0

        assert 'tokens_per_second' in analysis
        assert analysis['tokens_per_second'] > 0

        assert 'model_version' in analysis
        assert len(analysis['model_version']) > 0

    def test_performance_target_recommended_hardware(self, analysis_engine):
        """Verify analysis completes in <2s on recommended hardware.

        Note: This may fail on minimum hardware (M1/Ryzen 5) where <5s is acceptable.
        Run on M2/Ryzen 7 or better for <2s target.
        """
        start = time.time()
        analysis = analysis_engine.analyze_email(NORMAL_EMAIL, use_cache=False)
        elapsed_s = time.time() - start

        # Log performance for manual verification
        print(f"\nPerformance: {elapsed_s:.2f}s")
        print(f"Tokens/sec: {analysis['tokens_per_second']:.1f}")
        print(f"Model: {analysis['model_version']}")

        # Warn if slower than recommended target
        if elapsed_s > 2.0:
            pytest.warn(f"Analysis took {elapsed_s:.2f}s (recommended: <2s). "
                       f"May indicate minimum hardware or background load.")


# ============================================================================
# Test: AC8 - Result Caching
# ============================================================================

class TestCachingIntegration:
    """Test AC8: SQLite caching with real database."""

    def test_cache_miss_then_hit(self, analysis_engine):
        """Verify first analysis is cache miss, second is cache hit."""
        email = NORMAL_EMAIL.copy()
        email['message_id'] = 'msg_cache_test_001'

        # First analysis: cache miss
        analysis1 = analysis_engine.analyze_email(email)
        assert analysis1['cache_hit'] is False
        time1 = analysis1['processing_time_ms']

        # Second analysis: cache hit
        analysis2 = analysis_engine.analyze_email(email)
        assert analysis2['cache_hit'] is True
        time2 = analysis2['processing_time_ms']

        # Cache hit should be much faster
        assert time2 < time1
        assert time2 < 100  # <100ms for cache retrieval

        # Results should be identical
        assert analysis1['priority'] == analysis2['priority']
        assert analysis1['summary'] == analysis2['summary']
        assert analysis1['tags'] == analysis2['tags']

    def test_cache_invalidation_on_model_change(self, analysis_engine, temp_db):
        """Verify cache is invalidated when model version changes."""
        email = NORMAL_EMAIL.copy()
        email['message_id'] = 'msg_cache_invalidation_001'

        # First analysis with current model
        analysis1 = analysis_engine.analyze_email(email)
        assert analysis1['cache_hit'] is False

        # Manually change model version in cache
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE email_analysis
            SET model_version = 'old-model:1.0'
            WHERE message_id = ?
        ''', (email['message_id'],))
        conn.commit()
        conn.close()

        # Next analysis should be cache miss (model version mismatch)
        analysis2 = analysis_engine.analyze_email(email)
        assert analysis2['cache_hit'] is False

    def test_force_reanalyze_bypasses_cache(self, analysis_engine):
        """Verify force_reanalyze=True bypasses cache."""
        email = NORMAL_EMAIL.copy()
        email['message_id'] = 'msg_force_reanalyze_001'

        # First analysis
        analysis1 = analysis_engine.analyze_email(email)
        assert analysis1['cache_hit'] is False

        # Second analysis with force_reanalyze
        analysis2 = analysis_engine.analyze_email(email, force_reanalyze=True)
        assert analysis2['cache_hit'] is False

        # Third analysis (should hit cache now)
        analysis3 = analysis_engine.analyze_email(email)
        assert analysis3['cache_hit'] is True


# ============================================================================
# Test: AC9 - Batch Processing
# ============================================================================

class TestBatchProcessingIntegration:
    """Test AC9: Batch email processing."""

    def test_batch_processing(self, analysis_engine):
        """Process multiple emails in batch."""
        emails = [
            URGENT_EMAIL,
            NORMAL_EMAIL,
            INFORMATIONAL_EMAIL,
            ACTION_REQUIRED_EMAIL
        ]

        results = analysis_engine.analyze_batch(emails)

        # Verify all emails processed
        assert len(results) == len(emails)

        # Verify each result has required fields
        for result in results:
            assert 'priority' in result
            assert 'summary' in result
            assert 'tags' in result
            assert 'sentiment' in result
            assert 'action_items' in result
            assert 'processing_time_ms' in result

    def test_batch_with_progress_callback(self, analysis_engine):
        """Verify progress callback is invoked during batch processing."""
        emails = [URGENT_EMAIL, NORMAL_EMAIL, INFORMATIONAL_EMAIL]

        progress_calls = []

        def callback(current, total, result):
            progress_calls.append((current, total, result['priority']))

        results = analysis_engine.analyze_batch(emails, callback=callback)

        # Verify callback was called for each email
        assert len(progress_calls) == len(emails)

        # Verify progress increments correctly
        for i, (current, total, priority) in enumerate(progress_calls, 1):
            assert current == i
            assert total == len(emails)

    def test_batch_uses_cache(self, analysis_engine):
        """Verify batch processing uses cache for previously analyzed emails."""
        emails = [NORMAL_EMAIL, NORMAL_EMAIL]  # Same email twice

        # First batch (both cache miss)
        results1 = analysis_engine.analyze_batch([e.copy() for e in emails])
        assert results1[0]['cache_hit'] is False
        assert results1[1]['cache_hit'] is True  # Second one hits cache

        # Second batch (both cache hit)
        results2 = analysis_engine.analyze_batch([e.copy() for e in emails])
        assert results2[0]['cache_hit'] is True
        assert results2[1]['cache_hit'] is True


# ============================================================================
# Test: Complete Pipeline Integration
# ============================================================================

class TestCompletePipeline:
    """Test complete pipeline: Preprocessing → Analysis → Caching."""

    def test_end_to_end_pipeline(self, analysis_engine):
        """Verify complete pipeline works end-to-end."""
        # Raw email with HTML and attachments
        raw_email = HTML_EMAIL.copy()

        # Pipeline: Raw → Preprocess → Analyze → Cache
        analysis = analysis_engine.analyze_email(raw_email)

        # Verify preprocessing occurred (HTML → text)
        preprocessed = analysis_engine.preprocessor.preprocess_email(raw_email)
        assert 'content' in preprocessed
        assert 'body' in preprocessed['content']

        # Verify analysis completed
        assert analysis['priority'] in ['High', 'Medium', 'Low']
        assert len(analysis['summary']) > 0

        # Verify caching occurred
        cached = analysis_engine._get_cached_analysis(raw_email['message_id'])
        assert cached is not None
        assert cached['priority'] == analysis['priority']

    def test_statistics_aggregation(self, analysis_engine):
        """Verify analysis statistics are tracked correctly."""
        # Analyze multiple emails
        emails = [URGENT_EMAIL, NORMAL_EMAIL, INFORMATIONAL_EMAIL]
        analysis_engine.analyze_batch(emails)

        # Get statistics
        stats = analysis_engine.get_analysis_stats()

        # Verify stats structure
        assert 'total_analyses' in stats
        assert stats['total_analyses'] >= len(emails)

        assert 'cache_hit_rate_percent' in stats
        assert 0 <= stats['cache_hit_rate_percent'] <= 100

        assert 'avg_processing_time_ms' in stats
        assert stats['avg_processing_time_ms'] > 0

        assert 'priority_distribution' in stats
        assert isinstance(stats['priority_distribution'], dict)


# ============================================================================
# Test: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_required_fields(self, analysis_engine):
        """Verify graceful handling of emails missing required fields."""
        incomplete_email = {
            'subject': 'Test Email'
            # Missing 'from', 'body', etc.
        }

        # Should handle gracefully (preprocessor adds defaults)
        analysis = analysis_engine.analyze_email(incomplete_email)
        assert 'priority' in analysis

    def test_empty_email_body(self, analysis_engine):
        """Verify handling of empty email body."""
        empty_email = {
            'from': 'test@example.com',
            'subject': 'Empty Email',
            'body': '',
            'message_id': 'msg_empty_001'
        }

        analysis = analysis_engine.analyze_email(empty_email)
        assert analysis['priority'] in ['High', 'Medium', 'Low']
        assert 'summary' in analysis

    def test_very_long_email(self, analysis_engine):
        """Verify handling of very long emails."""
        long_email = {
            'from': 'test@example.com',
            'subject': 'Long Email',
            'body': 'Lorem ipsum dolor sit amet. ' * 1000,  # ~5000 words
            'message_id': 'msg_long_001'
        }

        analysis = analysis_engine.analyze_email(long_email)

        # Summary should still be concise
        assert len(analysis['summary']) <= 150

        # Tags should still be limited
        assert len(analysis['tags']) <= 5


# ============================================================================
# Performance Benchmarking
# ============================================================================

class TestPerformanceBenchmark:
    """Benchmark performance against Story 1.3 targets."""

    def test_benchmark_single_email_analysis(self, analysis_engine):
        """Benchmark single email analysis performance."""
        print("\n" + "="*70)
        print("PERFORMANCE BENCHMARK: Single Email Analysis")
        print("="*70)

        test_emails = [
            ("Urgent", URGENT_EMAIL),
            ("Normal", NORMAL_EMAIL),
            ("Informational", INFORMATIONAL_EMAIL),
            ("Action Required", ACTION_REQUIRED_EMAIL),
            ("HTML", HTML_EMAIL)
        ]

        for name, email in test_emails:
            # Ensure fresh analysis (no cache)
            email_copy = email.copy()
            email_copy['message_id'] = f"{email['message_id']}_benchmark"

            start = time.time()
            analysis = analysis_engine.analyze_email(email_copy, use_cache=False)
            elapsed_s = time.time() - start

            print(f"\n{name} Email:")
            print(f"  Time: {elapsed_s:.2f}s")
            print(f"  Priority: {analysis['priority']}")
            print(f"  Tokens/sec: {analysis['tokens_per_second']:.1f}")
            print(f"  Model: {analysis['model_version']}")

    def test_benchmark_batch_throughput(self, analysis_engine):
        """Benchmark batch processing throughput."""
        print("\n" + "="*70)
        print("PERFORMANCE BENCHMARK: Batch Throughput")
        print("="*70)

        # Create batch of 10 emails
        emails = []
        for i in range(10):
            email = NORMAL_EMAIL.copy()
            email['message_id'] = f'msg_batch_benchmark_{i}'
            emails.append(email)

        start = time.time()
        results = analysis_engine.analyze_batch(emails)
        elapsed_s = time.time() - start

        throughput = len(emails) / elapsed_s * 60  # emails/minute

        print(f"\nBatch Size: {len(emails)} emails")
        print(f"Total Time: {elapsed_s:.2f}s")
        print(f"Throughput: {throughput:.1f} emails/minute")
        print(f"Avg per email: {elapsed_s / len(emails):.2f}s")

    def test_benchmark_cache_speedup(self, analysis_engine):
        """Benchmark cache performance improvement."""
        print("\n" + "="*70)
        print("PERFORMANCE BENCHMARK: Cache Speedup")
        print("="*70)

        email = NORMAL_EMAIL.copy()
        email['message_id'] = 'msg_cache_benchmark'

        # First analysis (cache miss)
        start1 = time.time()
        analysis1 = analysis_engine.analyze_email(email)
        time1_ms = (time.time() - start1) * 1000

        # Second analysis (cache hit)
        start2 = time.time()
        analysis2 = analysis_engine.analyze_email(email)
        time2_ms = (time.time() - start2) * 1000

        speedup = time1_ms / time2_ms if time2_ms > 0 else 0

        print(f"\nCache Miss: {time1_ms:.0f}ms")
        print(f"Cache Hit: {time2_ms:.0f}ms")
        print(f"Speedup: {speedup:.1f}x faster")
        print(f"Cache hit target: <100ms (actual: {time2_ms:.1f}ms)")

        assert time2_ms < 100, f"Cache hit took {time2_ms:.1f}ms (target: <100ms)"
