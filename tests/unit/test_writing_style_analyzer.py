"""
Unit tests for WritingStyleAnalyzer

Tests cover:
- Writing style analysis from sent emails
- Greeting extraction
- Closing extraction
- Formality calculation
- Common phrase extraction
- Sentence structure analysis
- Tone marker detection
- Style profile persistence
- Edit feedback recording
- Edge cases and error handling

Story 1.5: Response Generation Assistant
"""

import pytest
import sqlite3
import json
import tempfile
import os
from pathlib import Path

from src.mailmind.core.writing_style_analyzer import (
    WritingStyleAnalyzer,
    WritingStyleError,
    analyze_writing_style
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
def analyzer(temp_db):
    """Create WritingStyleAnalyzer instance with temporary database."""
    return WritingStyleAnalyzer(db_path=temp_db)


@pytest.fixture
def sample_sent_emails():
    """Sample sent emails for testing."""
    return [
        {
            'body': 'Hi John,\n\nThanks for reaching out. I\'ll review the document and get back to you by Friday.\n\nThanks,\nAlice',
            'subject': 'Re: Q4 Budget Review'
        },
        {
            'body': 'Hi Sarah,\n\nI can attend the meeting on Tuesday at 2pm. Looking forward to discussing the project.\n\nBest,\nAlice',
            'subject': 'Re: Project Kickoff Meeting'
        },
        {
            'body': 'Hello Team,\n\nPlease review the attached proposal and let me know if you have any questions.\n\nRegards,\nAlice',
            'subject': 'Q1 Marketing Proposal'
        },
        {
            'body': 'Hi Mike,\n\nThanks for the update! The presentation looks great. I appreciate all your hard work on this.\n\nThanks,\nAlice',
            'subject': 'Re: Client Presentation Draft'
        },
        {
            'body': 'Hi Lisa,\n\nI wanted to follow up on our conversation from last week. Are you available for a quick call tomorrow?\n\nBest,\nAlice',
            'subject': 'Follow-up: Marketing Strategy'
        },
    ]


class TestWritingStyleAnalyzerInitialization:
    """Test WritingStyleAnalyzer initialization."""

    def test_initialization(self, temp_db):
        """Test basic initialization."""
        analyzer = WritingStyleAnalyzer(db_path=temp_db)

        assert analyzer.db_path == temp_db
        assert os.path.exists(temp_db)

    def test_database_tables_created(self, analyzer, temp_db):
        """Test that database tables are created."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check writing_style_profiles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='writing_style_profiles'")
        assert cursor.fetchone() is not None

        # Check style_analysis_history table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='style_analysis_history'")
        assert cursor.fetchone() is not None

        conn.close()

    def test_database_schema(self, analyzer, temp_db):
        """Test database schema has required columns."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check writing_style_profiles columns
        cursor.execute("PRAGMA table_info(writing_style_profiles)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {
            'id', 'profile_name', 'greeting_style', 'closing_style',
            'formality_level', 'common_phrases', 'tone_markers',
            'avg_sentence_length', 'sample_size', 'created_date', 'last_updated'
        }

        assert required_columns.issubset(columns)

        conn.close()


class TestGreetingExtraction:
    """Test greeting extraction functionality."""

    def test_extract_greetings_hi(self, analyzer):
        """Test extraction of 'Hi' greetings."""
        emails = [
            {'body': 'Hi John,\n\nHow are you?\n\nThanks'},
            {'body': 'Hi there,\n\nJust checking in.\n\nBest'},
        ]

        greetings = analyzer._extract_greetings(emails)

        assert len(greetings) == 2
        assert all(g.lower() == 'hi' or g.lower() == 'hi there' for g in greetings)

    def test_extract_greetings_hello(self, analyzer):
        """Test extraction of 'Hello' greetings."""
        emails = [
            {'body': 'Hello Sarah,\n\nGreat to hear from you.\n\nRegards'},
        ]

        greetings = analyzer._extract_greetings(emails)

        assert len(greetings) >= 1
        assert greetings[0].lower() == 'hello'

    def test_extract_greetings_dear(self, analyzer):
        """Test extraction of 'Dear' greetings (formal)."""
        emails = [
            {'body': 'Dear Mr. Smith,\n\nI am writing regarding...\n\nSincerely'},
        ]

        greetings = analyzer._extract_greetings(emails)

        assert len(greetings) >= 1
        assert 'dear' in greetings[0].lower()

    def test_extract_greetings_good_morning(self, analyzer):
        """Test extraction of 'Good morning/afternoon' greetings."""
        emails = [
            {'body': 'Good morning team,\n\nHere is the update.\n\nThanks'},
        ]

        greetings = analyzer._extract_greetings(emails)

        assert len(greetings) >= 1
        assert 'good morning' in greetings[0].lower()

    def test_extract_greetings_no_body(self, analyzer):
        """Test greeting extraction with empty body."""
        emails = [{'body': ''}]

        greetings = analyzer._extract_greetings(emails)

        # Should return default
        assert greetings == ['Hi']

    def test_extract_greetings_no_greeting(self, analyzer):
        """Test greeting extraction when no greeting present."""
        emails = [
            {'body': 'Just wanted to update you on the project status.\n\nThanks'},
        ]

        greetings = analyzer._extract_greetings(emails)

        # Should return default
        assert greetings == ['Hi']


class TestClosingExtraction:
    """Test closing extraction functionality."""

    def test_extract_closings_thanks(self, analyzer):
        """Test extraction of 'Thanks' closings."""
        emails = [
            {'body': 'Hi John,\n\nPlease review.\n\nThanks,\nAlice'},
        ]

        closings = analyzer._extract_closings(emails)

        assert len(closings) >= 1
        assert closings[0].lower() == 'thanks'

    def test_extract_closings_best(self, analyzer):
        """Test extraction of 'Best' closings."""
        emails = [
            {'body': 'Hi Sarah,\n\nSee you tomorrow.\n\nBest,\nAlice'},
        ]

        closings = analyzer._extract_closings(emails)

        assert len(closings) >= 1
        assert closings[0].lower() == 'best'

    def test_extract_closings_regards(self, analyzer):
        """Test extraction of 'Regards' closings."""
        emails = [
            {'body': 'Hello Team,\n\nPlease find attached.\n\nRegards,\nAlice'},
        ]

        closings = analyzer._extract_closings(emails)

        assert len(closings) >= 1
        assert 'regards' in closings[0].lower()

    def test_extract_closings_sincerely(self, analyzer):
        """Test extraction of 'Sincerely' closings (formal)."""
        emails = [
            {'body': 'Dear Mr. Smith,\n\nI am pleased to inform you...\n\nSincerely,\nAlice Johnson'},
        ]

        closings = analyzer._extract_closings(emails)

        assert len(closings) >= 1
        assert closings[0].lower() == 'sincerely'

    def test_extract_closings_no_closing(self, analyzer):
        """Test closing extraction when no closing present."""
        emails = [
            {'body': 'Hi John,\n\nPlease review the document.'},
        ]

        closings = analyzer._extract_closings(emails)

        # Should return default
        assert closings == ['Thanks']


class TestFormalityCalculation:
    """Test formality level calculation."""

    def test_formality_casual(self, analyzer):
        """Test formality calculation for casual emails."""
        casual_emails = [
            {'body': "Hey! That's great! I'll check it out. Thanks!"},
            {'body': "I'm gonna look into this. Let's catch up soon!"},
        ]

        formality = analyzer._calculate_formality(casual_emails)

        # Should be low (casual)
        assert formality < 0.5

    def test_formality_formal(self, analyzer):
        """Test formality calculation for formal emails."""
        formal_emails = [
            {'body': 'Dear Sir,\n\nI am writing to inform you regarding the matter discussed. Therefore, I would like to propose...'},
            {'body': 'Good morning. Furthermore, the proposal was approved. Sincerely, Alice'},
        ]

        formality = analyzer._calculate_formality(formal_emails)

        # Should be high (formal)
        assert formality > 0.5

    def test_formality_balanced(self, analyzer):
        """Test formality calculation for balanced emails."""
        balanced_emails = [
            {'body': 'Hi John, Please review the attached document. Thanks, Alice'},
            {'body': 'Hello Sarah, I wanted to follow up on our meeting. Best, Alice'},
        ]

        formality = analyzer._calculate_formality(balanced_emails)

        # Should be around 0.5 (balanced)
        assert 0.3 <= formality <= 0.7

    def test_formality_empty_body(self, analyzer):
        """Test formality calculation with empty body."""
        empty_emails = [{'body': ''}]

        formality = analyzer._calculate_formality(empty_emails)

        # Should return default (0.5)
        assert formality == 0.5


class TestCommonPhraseExtraction:
    """Test common phrase extraction."""

    def test_extract_common_phrases(self, analyzer):
        """Test extraction of common phrases."""
        emails = [
            {'body': 'Thanks for reaching out. I appreciate your help with this.'},
            {'body': 'Thanks for reaching out again. Looking forward to the meeting.'},
            {'body': 'Thanks for the update. Looking forward to working together.'},
        ]

        phrases = analyzer._extract_common_phrases(emails)

        # Should find repeated phrases
        assert len(phrases) > 0
        # "thanks for" and "looking forward" should appear
        assert any('thanks for' in p for p in phrases)

    def test_extract_common_phrases_filters_stopwords(self, analyzer):
        """Test that common phrase extraction filters stopwords."""
        emails = [
            {'body': 'The the the and and or but is was are be been.'},
        ]

        phrases = analyzer._extract_common_phrases(emails)

        # Should not return pure stopword phrases
        assert len(phrases) == 0

    def test_extract_common_phrases_frequency_threshold(self, analyzer):
        """Test that phrases must appear multiple times."""
        emails = [
            {'body': 'Unique phrase one.'},
            {'body': 'Different phrase two.'},
        ]

        phrases = analyzer._extract_common_phrases(emails)

        # Should not return phrases that appear only once
        assert len(phrases) == 0


class TestSentenceLengthCalculation:
    """Test average sentence length calculation."""

    def test_calculate_avg_sentence_length(self, analyzer):
        """Test average sentence length calculation."""
        emails = [
            {'body': 'Short sentence. Another short one. This is slightly longer than the others.'},
        ]

        avg_length = analyzer._calculate_avg_sentence_length(emails)

        assert avg_length > 0
        assert 3 <= avg_length <= 10  # Reasonable range

    def test_calculate_avg_sentence_length_long_sentences(self, analyzer):
        """Test with long sentences."""
        emails = [
            {'body': 'This is a very long sentence with many words that should increase the average sentence length calculation significantly.'},
        ]

        avg_length = analyzer._calculate_avg_sentence_length(emails)

        assert avg_length > 10

    def test_calculate_avg_sentence_length_empty(self, analyzer):
        """Test with empty emails."""
        emails = [{'body': ''}]

        avg_length = analyzer._calculate_avg_sentence_length(emails)

        # Should return default
        assert avg_length == 15.0


class TestToneMarkerExtraction:
    """Test tone marker extraction."""

    def test_extract_tone_markers_enthusiastic(self, analyzer):
        """Test extraction of enthusiasm markers."""
        emails = [
            {'body': 'Great! That\'s excellent news! I\'m so excited about this project!'},
            {'body': 'Fantastic work! This is awesome!'},
        ]

        markers = analyzer._extract_tone_markers(emails)

        assert 'enthusiasm' in markers
        assert markers['enthusiasm'] > 0.5  # High enthusiasm

    def test_extract_tone_markers_polite(self, analyzer):
        """Test extraction of politeness markers."""
        emails = [
            {'body': 'Please let me know if you need anything. Thank you so much. I appreciate your help.'},
            {'body': 'Could you please review this? I would be grateful for your feedback.'},
        ]

        markers = analyzer._extract_tone_markers(emails)

        assert 'politeness' in markers
        assert markers['politeness'] > 0.5  # High politeness

    def test_extract_tone_markers_direct(self, analyzer):
        """Test extraction of directness markers."""
        emails = [
            {'body': 'Review this. Send by Friday. Call me.'},
            {'body': 'Check the docs. Let me know. Thanks.'},
        ]

        markers = analyzer._extract_tone_markers(emails)

        assert 'directness' in markers
        # Directness measured by short sentences


class TestWritingStyleAnalysis:
    """Test complete writing style analysis."""

    def test_analyze_sent_emails(self, analyzer, sample_sent_emails):
        """Test full writing style analysis."""
        profile = analyzer.analyze_sent_emails(sample_sent_emails)

        # Check required fields
        assert 'greeting_style' in profile
        assert 'closing_style' in profile
        assert 'formality_level' in profile
        assert 'common_phrases' in profile
        assert 'avg_sentence_length' in profile
        assert 'tone_markers' in profile
        assert 'sample_size' in profile
        assert 'last_updated' in profile

        # Check values are reasonable
        assert profile['sample_size'] == len(sample_sent_emails)
        assert 0.0 <= profile['formality_level'] <= 1.0
        assert profile['avg_sentence_length'] > 0

    def test_analyze_sent_emails_greeting_style(self, analyzer, sample_sent_emails):
        """Test that greeting style is detected correctly."""
        profile = analyzer.analyze_sent_emails(sample_sent_emails)

        # Most common greeting in sample is "Hi"
        assert 'hi' in profile['greeting_style'].lower()

    def test_analyze_sent_emails_closing_style(self, analyzer, sample_sent_emails):
        """Test that closing style is detected correctly."""
        profile = analyzer.analyze_sent_emails(sample_sent_emails)

        # Sample has mix of "Thanks" and "Best"
        assert profile['closing_style'].lower() in ['thanks', 'best', 'regards']

    def test_analyze_sent_emails_sample_size_limit(self, analyzer):
        """Test that sample size is limited to 50."""
        # Create 100 emails
        many_emails = [
            {'body': f'Hi {i},\n\nEmail {i}\n\nThanks'}
            for i in range(100)
        ]

        profile = analyzer.analyze_sent_emails(many_emails)

        assert profile['sample_size'] == 50  # Max 50

    def test_analyze_sent_emails_minimum_sample(self, analyzer):
        """Test analysis with fewer than 20 emails."""
        few_emails = [
            {'body': 'Hi John,\n\nThanks for the update.\n\nBest'}
            for _ in range(10)
        ]

        profile = analyzer.analyze_sent_emails(few_emails)

        # Should use all 10 emails
        assert profile['sample_size'] == 10

    def test_analyze_sent_emails_empty_list(self, analyzer):
        """Test analysis with no sent emails."""
        profile = analyzer.analyze_sent_emails([])

        # Should return default profile
        assert profile['greeting_style'] == 'Hi'
        assert profile['closing_style'] == 'Thanks'
        assert profile['formality_level'] == 0.5
        assert profile['sample_size'] == 0


class TestProfilePersistence:
    """Test saving and loading profiles."""

    def test_save_profile(self, analyzer, temp_db):
        """Test saving profile to database."""
        profile = {
            'greeting_style': 'Hi',
            'closing_style': 'Thanks',
            'formality_level': 0.6,
            'common_phrases': ['thanks for', 'looking forward'],
            'avg_sentence_length': 15.5,
            'tone_markers': {'enthusiasm': 0.7, 'directness': 0.5, 'politeness': 0.8},
            'sample_size': 25,
            'last_updated': '2025-10-13T14:30:00Z'
        }

        analyzer._save_profile(profile, 'test_profile')

        # Verify saved in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM writing_style_profiles WHERE profile_name = ?', ('test_profile',))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_load_profile(self, analyzer, temp_db):
        """Test loading profile from database."""
        # First save a profile
        profile = {
            'greeting_style': 'Hello',
            'closing_style': 'Best',
            'formality_level': 0.7,
            'common_phrases': ['please let', 'I appreciate'],
            'avg_sentence_length': 18.0,
            'tone_markers': {'enthusiasm': 0.5, 'directness': 0.6, 'politeness': 0.9},
            'sample_size': 30,
            'last_updated': '2025-10-13T15:00:00Z'
        }
        analyzer._save_profile(profile, 'test_profile')

        # Now load it
        loaded = analyzer.load_profile('test_profile')

        assert loaded is not None
        assert loaded['greeting_style'] == 'Hello'
        assert loaded['closing_style'] == 'Best'
        assert loaded['formality_level'] == 0.7
        assert loaded['sample_size'] == 30

    def test_load_profile_not_found(self, analyzer):
        """Test loading non-existent profile."""
        loaded = analyzer.load_profile('nonexistent')

        assert loaded is None

    def test_save_and_load_profile_roundtrip(self, analyzer):
        """Test save and load preserves data."""
        original = {
            'greeting_style': 'Dear',
            'closing_style': 'Sincerely',
            'formality_level': 0.9,
            'common_phrases': ['regarding this', 'I would like'],
            'avg_sentence_length': 22.0,
            'tone_markers': {'enthusiasm': 0.3, 'directness': 0.4, 'politeness': 0.95},
            'sample_size': 40,
            'last_updated': '2025-10-13T16:00:00Z'
        }

        analyzer._save_profile(original, 'roundtrip')
        loaded = analyzer.load_profile('roundtrip')

        assert loaded['greeting_style'] == original['greeting_style']
        assert loaded['closing_style'] == original['closing_style']
        assert loaded['formality_level'] == original['formality_level']
        assert loaded['common_phrases'] == original['common_phrases']
        assert loaded['sample_size'] == original['sample_size']


class TestEditFeedback:
    """Test edit feedback recording."""

    def test_record_edit_feedback(self, analyzer, temp_db):
        """Test recording edit feedback."""
        original = "Hi John, Thanks for the update. Best, Alice"
        edited = "Hi John, Thank you very much for the detailed update. Best regards, Alice"

        analyzer.record_edit_feedback(original, edited, 'default')

        # Verify saved in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM style_analysis_history WHERE profile_name = ?', ('default',))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_record_edit_feedback_calculates_percentage(self, analyzer, temp_db):
        """Test that edit percentage is calculated."""
        original = "Hi John, Thanks."
        edited = "Hi John, Thank you very much for your help with this project. It means a lot."

        analyzer.record_edit_feedback(original, edited, 'default')

        # Get edit percentage from database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT edit_percentage FROM style_analysis_history WHERE profile_name = ?', ('default',))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] > 0  # Should have non-zero edit percentage

    def test_detect_style_changes(self, analyzer):
        """Test detection of style changes."""
        original = "Hi John,\n\nThanks for the update.\n\nBest, Alice"
        edited = "Hello John,\n\nThank you for the detailed update.\n\nKind regards, Alice"

        changes = analyzer._detect_style_changes(original, edited)

        # Should detect greeting and closing changes
        assert 'greeting_changed' in changes or 'closing_changed' in changes


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_analyze_with_malformed_emails(self, analyzer):
        """Test analysis with malformed email data."""
        malformed = [
            {},  # No body
            {'body': None},  # None body
            {'subject': 'Test'},  # No body field
        ]

        # Should handle gracefully without crashing
        profile = analyzer.analyze_sent_emails(malformed)

        # Should return default-like profile since no valid data
        assert profile['greeting_style'] == 'Hi'
        # Sample size reflects input count, even if data is invalid
        assert profile['sample_size'] == 3

    def test_analyze_with_unicode(self, analyzer):
        """Test analysis with Unicode characters."""
        unicode_emails = [
            {'body': 'Hi José,\n\nMerci beaucoup! 你好\n\nThanks, Alice'},
        ]

        # Should handle Unicode
        profile = analyzer.analyze_sent_emails(unicode_emails)

        assert profile is not None

    def test_get_most_common_empty_list(self, analyzer):
        """Test _get_most_common with empty list."""
        result = analyzer._get_most_common([], 'default')

        assert result == 'default'

    def test_is_stopword_phrase(self, analyzer):
        """Test stopword phrase detection."""
        assert analyzer._is_stopword_phrase('the and or') == True
        assert analyzer._is_stopword_phrase('important meeting today') == False


class TestConvenienceFunction:
    """Test convenience function."""

    def test_analyze_writing_style_function(self, sample_sent_emails, temp_db):
        """Test convenience function for style analysis."""
        profile = analyze_writing_style(sample_sent_emails, db_path=temp_db)

        assert profile is not None
        assert 'greeting_style' in profile
        assert profile['sample_size'] > 0


# Performance tests
class TestPerformance:
    """Test performance requirements."""

    def test_analyze_large_sample_performance(self, analyzer):
        """Test analysis performance with large sample."""
        import time

        # Create 50 emails
        emails = [
            {
                'body': f'Hi Person{i},\n\nThis is email {i}. Looking forward to working together.\n\nBest, Alice',
                'subject': f'Email {i}'
            }
            for i in range(50)
        ]

        start = time.time()
        profile = analyzer.analyze_sent_emails(emails)
        duration = time.time() - start

        # Should complete in under 2 seconds
        assert duration < 2.0
        assert profile['sample_size'] == 50
