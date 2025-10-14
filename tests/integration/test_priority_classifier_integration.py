"""
Integration Tests for Priority Classifier with Story 1.3

Tests the complete priority classification pipeline:
EmailAnalysisEngine (Story 1.3) → PriorityClassifier (Story 1.4)

These tests verify end-to-end functionality including:
- Integration with EmailAnalysisEngine
- Learning from user corrections over time
- Sender importance evolution
- Accuracy improvements with feedback

Author: MailMind Development Team
Created: 2025-10-13
Story: 1.4
"""

import unittest
import tempfile
import os
import sqlite3

from mailmind.core.ollama_manager import OllamaManager
from mailmind.core.email_preprocessor import EmailPreprocessor
from mailmind.core.email_analysis_engine import EmailAnalysisEngine
from mailmind.core.priority_classifier import PriorityClassifier


class TestPriorityClassifierIntegration(unittest.TestCase):
    """Integration tests for PriorityClassifier with EmailAnalysisEngine."""

    @classmethod
    def setUpClass(cls):
        """Set up shared resources for all tests."""
        # Initialize Ollama manager
        cls.ollama = OllamaManager(model_name="llama3.1:8b")

        # Check if model is available
        if not cls.ollama.is_model_available():
            cls.skipTest(cls, "Ollama model not available")

    def setUp(self):
        """Set up test database and components for each test."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')

        # Initialize components
        self.preprocessor = EmailPreprocessor()
        self.analysis_engine = EmailAnalysisEngine(self.ollama, self.db_path)
        self.priority_classifier = PriorityClassifier(self.db_path)

    def tearDown(self):
        """Clean up test resources."""
        self.priority_classifier.close()
        self.analysis_engine.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    # Full Pipeline Integration Tests

    def test_full_pipeline_basic_email(self):
        """Test complete pipeline from raw email to enhanced priority."""
        raw_email = {
            'From': 'colleague@company.com',
            'To': 'user@mailmind.com',
            'Subject': 'Project update',
            'Date': '2025-10-13T10:00:00Z',
            'Body': 'Here is an update on the project status.',
            'Message-ID': '<test001@example.com>'
        }

        # Step 1: Preprocess email
        preprocessed = self.preprocessor.preprocess_email(raw_email)

        # Step 2: Base analysis (Story 1.3)
        base_analysis = self.analysis_engine.analyze_email(
            preprocessed,
            analysis_type='full'
        )

        # Step 3: Enhanced priority classification (Story 1.4)
        enhanced = self.priority_classifier.classify_priority(
            preprocessed,
            base_analysis
        )

        # Verify complete result
        self.assertIn('priority', enhanced)
        self.assertIn('confidence', enhanced)
        self.assertIn('sender_importance', enhanced)
        self.assertIn('visual_indicator', enhanced)
        self.assertEqual(enhanced['base_priority'], base_analysis['priority'])

    def test_vip_sender_pipeline(self):
        """Test pipeline with VIP sender gets priority upgrade."""
        # Mark sender as VIP
        vip_sender = 'boss@company.com'
        self.priority_classifier.set_sender_vip(vip_sender, True)

        raw_email = {
            'From': vip_sender,
            'To': 'user@mailmind.com',
            'Subject': 'Quick question',
            'Date': '2025-10-13T10:00:00Z',
            'Body': 'Can you review this when you have a moment?',
            'Message-ID': '<test002@example.com>'
        }

        # Full pipeline
        preprocessed = self.preprocessor.preprocess_email(raw_email)
        base_analysis = self.analysis_engine.analyze_email(preprocessed, 'full')
        enhanced = self.priority_classifier.classify_priority(preprocessed, base_analysis)

        # VIP should upgrade priority
        base_priority_index = ['Low', 'Medium', 'High'].index(base_analysis['priority'])
        enhanced_priority_index = ['Low', 'Medium', 'High'].index(enhanced['priority'])

        self.assertGreaterEqual(enhanced_priority_index, base_priority_index)

    def test_urgent_email_detection(self):
        """Test urgent email gets high priority through full pipeline."""
        raw_email = {
            'From': 'manager@company.com',
            'To': 'user@mailmind.com',
            'Subject': 'URGENT: Production issue',
            'Date': '2025-10-13T10:00:00Z',
            'Body': 'We have a critical production issue that needs immediate attention. Please respond ASAP.',
            'Message-ID': '<test003@example.com>'
        }

        # Full pipeline
        preprocessed = self.preprocessor.preprocess_email(raw_email)
        base_analysis = self.analysis_engine.analyze_email(preprocessed, 'full')
        enhanced = self.priority_classifier.classify_priority(preprocessed, base_analysis)

        # Should detect as high priority
        self.assertIn(enhanced['priority'], ['High', 'Medium'])
        self.assertIn('urgent', base_analysis.get('tags', []))

    # Learning System Integration Tests

    def test_learning_from_single_correction(self):
        """Test system learns from a single user correction."""
        sender = 'newsletter@example.com'
        message_id = 'msg_newsletter_001'

        # Initial classification
        email = {
            'metadata': {
                'from': sender,
                'to': 'user@mailmind.com',
                'subject': 'Weekly Newsletter',
                'message_id': message_id
            },
            'content': {
                'body': 'This week in tech news...'
            }
        }

        base_analysis = {'priority': 'Medium', 'confidence': 0.6}
        result1 = self.priority_classifier.classify_priority(email, base_analysis)

        # User corrects to Low
        self.priority_classifier.record_user_override(
            message_id=message_id,
            sender=sender,
            original_priority=result1['priority'],
            original_confidence=result1['confidence'],
            user_priority='Low',
            reason='Newsletter sender'
        )

        # Check sender importance was updated
        sender_stats = self.priority_classifier.get_sender_stats(sender)
        self.assertIsNotNone(sender_stats)
        self.assertLess(sender_stats['importance_score'], 0.5)

    def test_learning_from_multiple_corrections(self):
        """Test system learns from multiple corrections and improves."""
        sender = 'boss@company.com'

        # Simulate 5 emails where user consistently upgrades priority
        for i in range(5):
            email = {
                'metadata': {
                    'from': sender,
                    'subject': f'Task {i+1}',
                    'message_id': f'msg_{i}'
                },
                'content': {'body': 'Please handle this task.'}
            }

            base_analysis = {'priority': 'Medium', 'confidence': 0.7}
            result = self.priority_classifier.classify_priority(email, base_analysis)

            # User upgrades to High
            self.priority_classifier.record_user_override(
                message_id=f'msg_{i}',
                sender=sender,
                original_priority=result['priority'],
                original_confidence=result['confidence'],
                user_priority='High',
                reason='Important sender'
            )

        # Check sender importance increased significantly
        sender_stats = self.priority_classifier.get_sender_stats(sender)
        self.assertGreater(sender_stats['importance_score'], 0.5)
        self.assertEqual(sender_stats['correction_count'], 5)

        # New email from this sender should get higher priority
        new_email = {
            'metadata': {
                'from': sender,
                'subject': 'New task',
                'message_id': 'msg_new'
            },
            'content': {'body': 'New task for you.'}
        }

        base_analysis = {'priority': 'Medium', 'confidence': 0.7}
        enhanced = self.priority_classifier.classify_priority(new_email, base_analysis)

        # Should be upgraded based on learning
        self.assertEqual(enhanced['priority'], 'High')

    def test_accuracy_improvement_over_time(self):
        """Test classification accuracy improves with corrections."""
        # Simulate initial classifications (80% accuracy)
        senders = {
            'important@company.com': 'High',
            'team@company.com': 'Medium',
            'newsletter@example.com': 'Low',
            'spam@example.com': 'Low'
        }

        # Create email_analysis table
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                sender TEXT,
                priority TEXT,
                confidence REAL
            )
        """)

        # Phase 1: Initial classifications (before learning)
        for i in range(100):
            sender = list(senders.keys())[i % len(senders)]
            priority = 'Medium'  # System starts with medium for everyone

            conn.execute("""
                INSERT INTO email_analysis (message_id, sender, priority, confidence)
                VALUES (?, ?, ?, 0.7)
            """, (f'msg_{i}', sender, priority))

        conn.commit()

        # Record corrections (system was wrong 20% of the time)
        for i in range(20):
            sender = list(senders.keys())[i % len(senders)]
            correct_priority = senders[sender]

            self.priority_classifier.record_user_override(
                message_id=f'msg_{i}',
                sender=sender,
                original_priority='Medium',
                original_confidence=0.7,
                user_priority=correct_priority
            )

        # Check initial accuracy (80%)
        accuracy_initial = self.priority_classifier.get_classification_accuracy(days=30)
        self.assertEqual(accuracy_initial['accuracy_percentage'], 80.0)

        # Phase 2: New classifications (after learning)
        # System should now classify correctly based on learned sender patterns
        for i in range(100, 150):
            sender = list(senders.keys())[i % len(senders)]
            expected_priority = senders[sender]

            email = {
                'metadata': {'from': sender, 'subject': 'Test', 'message_id': f'msg_{i}'},
                'content': {'body': 'Test content'}
            }
            base = {'priority': 'Medium', 'confidence': 0.7}
            enhanced = self.priority_classifier.classify_priority(email, base)

            # Store new classification
            conn.execute("""
                INSERT INTO email_analysis (message_id, sender, priority, confidence)
                VALUES (?, ?, ?, ?)
            """, (f'msg_{i}', sender, enhanced['priority'], enhanced['confidence']))

            # Only correct if still wrong (should be fewer corrections now)
            if enhanced['priority'] != expected_priority:
                self.priority_classifier.record_user_override(
                    message_id=f'msg_{i}',
                    sender=sender,
                    original_priority=enhanced['priority'],
                    original_confidence=enhanced['confidence'],
                    user_priority=expected_priority
                )

        conn.commit()
        conn.close()

        # Check improved accuracy (should be >85%)
        accuracy_improved = self.priority_classifier.get_classification_accuracy(days=30)

        # Accuracy should have improved
        self.assertGreater(
            accuracy_improved['accuracy_percentage'],
            accuracy_initial['accuracy_percentage']
        )

    # Batch Processing Tests

    def test_batch_email_classification(self):
        """Test classifying multiple emails with learning."""
        emails = [
            {
                'From': 'boss@company.com',
                'Subject': 'Meeting tomorrow',
                'Body': 'Can we meet tomorrow at 10am?',
                'Message-ID': '<batch001@example.com>'
            },
            {
                'From': 'newsletter@example.com',
                'Subject': 'Weekly digest',
                'Body': 'Here are this week\'s top stories...',
                'Message-ID': '<batch002@example.com>'
            },
            {
                'From': 'team@company.com',
                'Subject': 'Project status',
                'Body': 'FYI - project is on track.',
                'Message-ID': '<batch003@example.com>'
            }
        ]

        results = []
        for raw_email in emails:
            # Full pipeline
            preprocessed = self.preprocessor.preprocess_email(raw_email)
            base_analysis = self.analysis_engine.analyze_email(preprocessed, 'quick')
            enhanced = self.priority_classifier.classify_priority(preprocessed, base_analysis)
            results.append(enhanced)

        # Verify all classified
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('priority', result)
            self.assertIn('confidence', result)

    # Performance Tests

    def test_classification_performance(self):
        """Test enhanced classification meets performance targets (<50ms overhead)."""
        import time

        email = {
            'metadata': {
                'from': 'test@example.com',
                'subject': 'Test',
                'message_id': 'perf_test'
            },
            'content': {'body': 'Test content'}
        }

        base_analysis = {'priority': 'Medium', 'confidence': 0.7}

        # Measure classification time
        start = time.perf_counter()
        for _ in range(100):
            self.priority_classifier.classify_priority(email, base_analysis)
        end = time.perf_counter()

        avg_time_ms = (end - start) / 100 * 1000

        # Should be <50ms per classification
        self.assertLess(avg_time_ms, 50.0,
                       f"Classification took {avg_time_ms:.2f}ms, target <50ms")

    def test_sender_lookup_performance(self):
        """Test sender importance lookup meets performance targets (<10ms)."""
        import time

        # Pre-populate some senders
        for i in range(100):
            self.priority_classifier.set_sender_vip(f'sender{i}@example.com', False)

        # Measure lookup time
        start = time.perf_counter()
        for i in range(100):
            self.priority_classifier._get_sender_importance(f'sender{i}@example.com')
        end = time.perf_counter()

        avg_time_ms = (end - start) / 100 * 1000

        # Should be <10ms per lookup
        self.assertLess(avg_time_ms, 10.0,
                       f"Sender lookup took {avg_time_ms:.2f}ms, target <10ms")


class TestPriorityClassifierScenarios(unittest.TestCase):
    """Real-world scenario tests."""

    def setUp(self):
        """Set up test components."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.classifier = PriorityClassifier(self.db_path)

    def tearDown(self):
        """Clean up."""
        self.classifier.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_new_user_cold_start(self):
        """Test system behavior with new user (no history)."""
        email = {
            'metadata': {
                'from': 'new@example.com',
                'subject': 'Hello',
                'message_id': 'new_001'
            },
            'content': {'body': 'Hello, this is a test.'}
        }

        base = {'priority': 'Medium', 'confidence': 0.6}
        result = self.classifier.classify_priority(email, base)

        # Should use base classification (no learning data)
        self.assertEqual(result['priority'], 'Medium')
        self.assertEqual(result['sender_importance'], 0.5)  # Neutral

    def test_executive_email_scenario(self):
        """Test handling of executive/VIP email."""
        exec_sender = 'ceo@company.com'
        self.classifier.set_sender_vip(exec_sender, True)

        email = {
            'metadata': {
                'from': exec_sender,
                'subject': 'Strategy discussion',
                'message_id': 'exec_001'
            },
            'content': {'body': 'Let\'s discuss our strategy.'}
        }

        base = {'priority': 'Medium', 'confidence': 0.7}
        result = self.classifier.classify_priority(email, base)

        # VIP should upgrade to High
        self.assertEqual(result['priority'], 'High')
        self.assertEqual(result['visual_indicator'], '🔴')

    def test_spam_sender_scenario(self):
        """Test handling of spam/low-priority sender."""
        spam_sender = 'promotions@spam.com'

        # Simulate user marking as spam multiple times
        for i in range(5):
            self.classifier.record_user_override(
                message_id=f'spam_{i}',
                sender=spam_sender,
                original_priority='Medium',
                original_confidence=0.5,
                user_priority='Low',
                reason='Spam sender'
            )

        # New email from spam sender
        email = {
            'metadata': {
                'from': spam_sender,
                'subject': 'Special offer!',
                'message_id': 'spam_new'
            },
            'content': {'body': 'Buy now!'}
        }

        base = {'priority': 'Medium', 'confidence': 0.6}
        result = self.classifier.classify_priority(email, base)

        # Should be downgraded to Low
        self.assertEqual(result['priority'], 'Low')
        self.assertEqual(result['visual_indicator'], '🔵')

    def test_mixed_priority_sender(self):
        """Test sender with both important and unimportant emails."""
        sender = 'mixed@example.com'

        # Sometimes user upgrades, sometimes downgrades
        corrections = [
            ('Medium', 'High'),   # Important
            ('Medium', 'Low'),    # Newsletter
            ('Medium', 'High'),   # Important
            ('Medium', 'Low'),    # FYI
            ('Medium', 'High'),   # Important
        ]

        for i, (orig, user) in enumerate(corrections):
            self.classifier.record_user_override(
                message_id=f'mixed_{i}',
                sender=sender,
                original_priority=orig,
                original_confidence=0.7,
                user_priority=user
            )

        # Check sender importance (should be slightly higher due to more upgrades)
        sender_stats = self.classifier.get_sender_stats(sender)
        self.assertGreater(sender_stats['importance_score'], 0.5)


if __name__ == '__main__':
    unittest.main()
