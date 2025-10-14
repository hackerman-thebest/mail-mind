"""
Unit Tests for Priority Classifier

Tests the enhanced priority classification system with user learning capabilities.
Covers sender importance tracking, user correction learning, and classification accuracy.

Test Coverage:
- Database schema initialization
- Priority classification with sender importance
- User correction recording and learning
- Sender importance adjustments
- Accuracy tracking and reporting
- VIP sender management
- Edge cases and error handling

Author: MailMind Development Team
Created: 2025-10-13
Story: 1.4
"""

import unittest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta

from src.mailmind.core.priority_classifier import PriorityClassifier


class TestPriorityClassifier(unittest.TestCase):
    """Test cases for PriorityClassifier class."""

    def setUp(self):
        """Set up test database and classifier instance."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.classifier = PriorityClassifier(self.db_path)

        # Sample email data
        self.sample_email = {
            'metadata': {
                'from': 'test@example.com',
                'to': 'user@mailmind.com',
                'subject': 'Test Email',
                'date': '2025-10-13T10:00:00Z'
            },
            'content': {
                'body': 'This is a test email body.',
                'plain_text': 'This is a test email body.'
            }
        }

        # Sample base analysis (from Story 1.3)
        self.sample_base_analysis = {
            'priority': 'Medium',
            'confidence': 0.7,
            'summary': 'Test email summary',
            'tags': ['test', 'email'],
            'sentiment': 'neutral'
        }

    def tearDown(self):
        """Clean up test database."""
        self.classifier.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    # Database Initialization Tests

    def test_database_initialization(self):
        """Test that database schema is created correctly."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check user_corrections table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_corrections'
        """)
        self.assertIsNotNone(cursor.fetchone())

        # Check sender_importance table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='sender_importance'
        """)
        self.assertIsNotNone(cursor.fetchone())

        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_corrections_sender'
        """)
        self.assertIsNotNone(cursor.fetchone())

        conn.close()

    def test_database_schema_columns(self):
        """Test that required columns exist in tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check user_corrections columns
        cursor.execute("PRAGMA table_info(user_corrections)")
        columns = {row[1] for row in cursor.fetchall()}
        required_columns = {
            'id', 'message_id', 'sender', 'original_priority',
            'original_confidence', 'user_priority', 'correction_reason',
            'correction_type', 'timestamp', 'applied_to_model'
        }
        self.assertTrue(required_columns.issubset(columns))

        # Check sender_importance columns
        cursor.execute("PRAGMA table_info(sender_importance)")
        columns = {row[1] for row in cursor.fetchall()}
        required_columns = {
            'id', 'sender_email', 'sender_name', 'importance_score',
            'email_count', 'reply_count', 'correction_count',
            'is_vip', 'is_blocked', 'first_seen', 'last_seen', 'last_updated'
        }
        self.assertTrue(required_columns.issubset(columns))

        conn.close()

    # Priority Classification Tests

    def test_basic_priority_classification(self):
        """Test basic priority classification without sender history."""
        result = self.classifier.classify_priority(
            self.sample_email,
            self.sample_base_analysis
        )

        # Should maintain base priority for new sender
        self.assertEqual(result['priority'], 'Medium')
        self.assertEqual(result['base_priority'], 'Medium')
        self.assertIn('confidence', result)
        self.assertIn('sender_importance', result)
        self.assertIn('visual_indicator', result)

    def test_priority_classification_output_structure(self):
        """Test that classification output has correct structure."""
        result = self.classifier.classify_priority(
            self.sample_email,
            self.sample_base_analysis
        )

        required_keys = {
            'priority', 'confidence', 'sender_importance',
            'base_priority', 'adjustments', 'visual_indicator',
            'classification_source'
        }
        self.assertTrue(required_keys.issubset(result.keys()))
        self.assertIn('sender_adjustment', result['adjustments'])
        self.assertIn('correction_adjustment', result['adjustments'])

    def test_visual_indicators(self):
        """Test correct visual indicators for each priority level."""
        test_cases = [
            ('High', '🔴'),
            ('Medium', '🟡'),
            ('Low', '🔵')
        ]

        for priority, expected_indicator in test_cases:
            base_analysis = {'priority': priority, 'confidence': 0.8}
            result = self.classifier.classify_priority(
                self.sample_email,
                base_analysis
            )
            self.assertEqual(result['visual_indicator'], expected_indicator)

    # Sender Importance Tests

    def test_new_sender_default_importance(self):
        """Test that new senders get default importance score."""
        sender_importance = self.classifier._get_sender_importance('new@sender.com')

        self.assertEqual(sender_importance['score'], 0.5)
        self.assertFalse(sender_importance['is_vip'])
        self.assertEqual(sender_importance['email_count'], 0)
        self.assertEqual(sender_importance['reply_count'], 0)
        self.assertEqual(sender_importance['adjustment'], 0)

    def test_vip_sender_priority_upgrade(self):
        """Test that VIP senders get priority upgrade."""
        sender = 'vip@example.com'
        self.classifier.set_sender_vip(sender, True)

        email = self.sample_email.copy()
        email['metadata'] = email['metadata'].copy()
        email['metadata']['from'] = sender

        base_analysis = {'priority': 'Low', 'confidence': 0.6}
        result = self.classifier.classify_priority(email, base_analysis)

        # VIP should upgrade priority from Low to Medium
        self.assertEqual(result['priority'], 'Medium')
        self.assertEqual(result['adjustments']['sender_adjustment'], +1)

    def test_high_importance_sender_upgrade(self):
        """Test that high importance senders (>0.8) get priority upgrade."""
        sender = 'important@example.com'

        # Manually set high importance
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO sender_importance (sender_email, importance_score)
            VALUES (?, ?)
        """, (sender, 0.85))
        conn.commit()
        conn.close()

        email = self.sample_email.copy()
        email['metadata'] = email['metadata'].copy()
        email['metadata']['from'] = sender

        base_analysis = {'priority': 'Medium', 'confidence': 0.7}
        result = self.classifier.classify_priority(email, base_analysis)

        # High importance should upgrade to High
        self.assertEqual(result['priority'], 'High')

    def test_low_importance_sender_downgrade(self):
        """Test that low importance senders (<0.3) get priority downgrade."""
        sender = 'spam@example.com'

        # Manually set low importance
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO sender_importance (sender_email, importance_score)
            VALUES (?, ?)
        """, (sender, 0.2))
        conn.commit()
        conn.close()

        email = self.sample_email.copy()
        email['metadata'] = email['metadata'].copy()
        email['metadata']['from'] = sender

        base_analysis = {'priority': 'Medium', 'confidence': 0.6}
        result = self.classifier.classify_priority(email, base_analysis)

        # Low importance should downgrade to Low
        self.assertEqual(result['priority'], 'Low')

    def test_sender_importance_with_email_count(self):
        """Test confidence boost for senders with high email count and importance."""
        sender = 'frequent@example.com'

        # Insert sender with high email count AND high importance (>0.8 to trigger upgrade)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO sender_importance (sender_email, importance_score, email_count)
            VALUES (?, ?, ?)
        """, (sender, 0.85, 20))  # High importance + high email count
        conn.commit()
        conn.close()

        email = self.sample_email.copy()
        email['metadata'] = email['metadata'].copy()
        email['metadata']['from'] = sender

        base_analysis = {'priority': 'Medium', 'confidence': 0.6}
        result = self.classifier.classify_priority(email, base_analysis)

        # Should have confidence boost (>10 emails) and priority upgrade (>0.8 importance)
        self.assertGreater(result['confidence'], 0.6)
        self.assertEqual(result['priority'], 'High')  # Upgraded due to high importance

    # User Correction Tests

    def test_record_user_override(self):
        """Test recording user priority override."""
        message_id = 'msg_test_123'
        sender = 'test@example.com'

        self.classifier.record_user_override(
            message_id=message_id,
            sender=sender,
            original_priority='Medium',
            original_confidence=0.7,
            user_priority='High',
            reason='Wrong sender importance'
        )

        # Check correction was recorded
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT * FROM user_corrections WHERE message_id = ?
        """, (message_id,))
        correction = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(correction)
        self.assertEqual(correction[1], message_id)  # message_id
        self.assertEqual(correction[2], sender)  # sender

    def test_sender_importance_update_on_upgrade(self):
        """Test sender importance increases when user upgrades priority."""
        sender = 'test@example.com'

        # Record initial importance
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO sender_importance (sender_email, importance_score)
            VALUES (?, ?)
        """, (sender, 0.5))
        conn.commit()
        conn.close()

        # User upgrades priority
        self.classifier.record_user_override(
            message_id='msg_001',
            sender=sender,
            original_priority='Medium',
            original_confidence=0.7,
            user_priority='High',
            reason='Important sender'
        )

        # Check importance increased
        sender_stats = self.classifier.get_sender_stats(sender)
        self.assertGreater(sender_stats['importance_score'], 0.5)

    def test_sender_importance_update_on_downgrade(self):
        """Test sender importance decreases when user downgrades priority."""
        sender = 'spam@example.com'

        # Record initial importance
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO sender_importance (sender_email, importance_score)
            VALUES (?, ?)
        """, (sender, 0.5))
        conn.commit()
        conn.close()

        # User downgrades priority
        self.classifier.record_user_override(
            message_id='msg_002',
            sender=sender,
            original_priority='Medium',
            original_confidence=0.6,
            user_priority='Low',
            reason='Spam sender'
        )

        # Check importance decreased
        sender_stats = self.classifier.get_sender_stats(sender)
        self.assertLess(sender_stats['importance_score'], 0.5)

    def test_correction_adjustment_calculation(self):
        """Test correction adjustment is calculated from history."""
        sender = 'test@example.com'

        # Record multiple upgrades
        for i in range(5):
            self.classifier.record_user_override(
                message_id=f'msg_{i}',
                sender=sender,
                original_priority='Medium',
                original_confidence=0.7,
                user_priority='High'
            )

        # Check correction adjustment
        adjustment = self.classifier._get_correction_adjustment(
            sender=sender,
            subject='Test',
            body='Test'
        )

        # Should have positive adjustment (user tends to upgrade)
        self.assertGreater(adjustment, 0)

    def test_correction_type_determination(self):
        """Test correction type is determined correctly from reason."""
        test_cases = [
            ('Wrong sender importance', 'sender_importance'),
            ('Urgency misdetected', 'urgency_misdetection'),
            ('Category incorrect', 'category_adjustment'),
            ('Other reason', 'priority_override'),
            (None, 'priority_override')
        ]

        for reason, expected_type in test_cases:
            correction_type = self.classifier._determine_correction_type(
                original_priority='Medium',
                user_priority='High',
                reason=reason
            )
            self.assertEqual(correction_type, expected_type)

    # Accuracy Tracking Tests

    def test_accuracy_calculation_no_data(self):
        """Test accuracy calculation with no data returns 0%."""
        accuracy = self.classifier.get_classification_accuracy(days=30)

        self.assertEqual(accuracy['accuracy_percentage'], 0.0)
        self.assertEqual(accuracy['total_classified'], 0)
        self.assertEqual(accuracy['user_corrections'], 0)
        self.assertFalse(accuracy['target_met'])

    def test_accuracy_calculation_with_data(self):
        """Test accuracy calculation with sample data."""
        # Create email_analysis table for testing
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                priority TEXT,
                confidence REAL
            )
        """)

        # Insert 100 classifications
        for i in range(100):
            conn.execute("""
                INSERT INTO email_analysis (message_id, priority, confidence)
                VALUES (?, 'Medium', 0.7)
            """, (f'msg_{i}',))

        conn.commit()
        conn.close()

        # Record 10 corrections (90% accuracy)
        for i in range(10):
            self.classifier.record_user_override(
                message_id=f'msg_{i}',
                sender='test@example.com',
                original_priority='Medium',
                original_confidence=0.7,
                user_priority='High'
            )

        accuracy = self.classifier.get_classification_accuracy(days=30)

        self.assertEqual(accuracy['total_classified'], 100)
        self.assertEqual(accuracy['user_corrections'], 10)
        self.assertEqual(accuracy['accuracy_percentage'], 90.0)
        self.assertTrue(accuracy['target_met'])  # >85% target

    def test_accuracy_target_met_threshold(self):
        """Test accuracy target_met flag at 85% threshold."""
        # Create email_analysis table
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                priority TEXT,
                confidence REAL
            )
        """)

        # Insert 100 classifications
        for i in range(100):
            conn.execute("""
                INSERT INTO email_analysis (message_id, priority, confidence)
                VALUES (?, 'Medium', 0.7)
            """, (f'msg_{i}',))

        conn.commit()
        conn.close()

        # Test exactly 85% accuracy (15 corrections)
        for i in range(15):
            self.classifier.record_user_override(
                message_id=f'msg_{i}',
                sender='test@example.com',
                original_priority='Medium',
                original_confidence=0.7,
                user_priority='High'
            )

        accuracy = self.classifier.get_classification_accuracy(days=30)
        self.assertTrue(accuracy['target_met'])
        self.assertEqual(accuracy['accuracy_percentage'], 85.0)

    # VIP Management Tests

    def test_set_sender_vip(self):
        """Test setting sender as VIP."""
        sender = 'boss@company.com'
        self.classifier.set_sender_vip(sender, True)

        sender_stats = self.classifier.get_sender_stats(sender)
        self.assertIsNotNone(sender_stats)
        self.assertTrue(sender_stats['is_vip'])

    def test_remove_sender_vip(self):
        """Test removing VIP status from sender."""
        sender = 'boss@company.com'
        self.classifier.set_sender_vip(sender, True)
        self.classifier.set_sender_vip(sender, False)

        sender_stats = self.classifier.get_sender_stats(sender)
        self.assertFalse(sender_stats['is_vip'])

    def test_get_sender_stats_nonexistent(self):
        """Test getting stats for nonexistent sender returns None."""
        stats = self.classifier.get_sender_stats('nonexistent@example.com')
        self.assertIsNone(stats)

    def test_get_sender_stats_existing(self):
        """Test getting stats for existing sender."""
        sender = 'test@example.com'
        self.classifier.set_sender_vip(sender, True)

        stats = self.classifier.get_sender_stats(sender)
        self.assertIsNotNone(stats)
        self.assertEqual(stats['sender_email'], sender)
        self.assertTrue(stats['is_vip'])

    # Edge Cases and Error Handling

    def test_priority_upgrade_at_maximum(self):
        """Test priority upgrade when already at High doesn't exceed."""
        base_analysis = {'priority': 'High', 'confidence': 0.9}
        sender = 'vip@example.com'
        self.classifier.set_sender_vip(sender, True)

        email = self.sample_email.copy()
        email['metadata'] = email['metadata'].copy()
        email['metadata']['from'] = sender

        result = self.classifier.classify_priority(email, base_analysis)

        # Should stay at High
        self.assertEqual(result['priority'], 'High')

    def test_priority_downgrade_at_minimum(self):
        """Test priority downgrade when already at Low doesn't go below."""
        base_analysis = {'priority': 'Low', 'confidence': 0.5}
        sender = 'spam@example.com'

        # Set low importance
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO sender_importance (sender_email, importance_score)
            VALUES (?, ?)
        """, (sender, 0.1))
        conn.commit()
        conn.close()

        email = self.sample_email.copy()
        email['metadata'] = email['metadata'].copy()
        email['metadata']['from'] = sender

        result = self.classifier.classify_priority(email, base_analysis)

        # Should stay at Low
        self.assertEqual(result['priority'], 'Low')

    def test_confidence_bounds(self):
        """Test confidence stays within 0.0-1.0 bounds."""
        # Test with very high base confidence
        base_analysis = {'priority': 'High', 'confidence': 0.95}

        email = self.sample_email.copy()
        result = self.classifier.classify_priority(email, base_analysis)

        self.assertGreaterEqual(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)

    def test_missing_email_metadata(self):
        """Test handling of missing email metadata."""
        incomplete_email = {'content': {'body': 'Test'}}

        # Should handle gracefully with default sender
        result = self.classifier.classify_priority(
            incomplete_email,
            self.sample_base_analysis
        )

        self.assertIn('priority', result)
        self.assertIn('confidence', result)

    def test_context_manager_usage(self):
        """Test PriorityClassifier can be used as context manager."""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')

        with PriorityClassifier(db_path) as classifier:
            result = classifier.classify_priority(
                self.sample_email,
                self.sample_base_analysis
            )
            self.assertIsNotNone(result)

        # Database should be closed
        os.close(db_fd)
        os.unlink(db_path)

    def test_multiple_corrections_same_sender(self):
        """Test handling multiple corrections for same sender."""
        sender = 'test@example.com'

        # Record multiple corrections with different priorities
        corrections = [
            ('Medium', 'High'),
            ('Medium', 'High'),
            ('High', 'Medium'),
            ('Medium', 'High'),
        ]

        for i, (orig, user) in enumerate(corrections):
            self.classifier.record_user_override(
                message_id=f'msg_{i}',
                sender=sender,
                original_priority=orig,
                original_confidence=0.7,
                user_priority=user
            )

        # Should calculate net adjustment (3 upgrades, 1 downgrade = +2 net)
        adjustment = self.classifier._get_correction_adjustment(sender, '', '')
        self.assertGreater(adjustment, 0)  # Net positive adjustment

    def test_old_corrections_outside_window(self):
        """Test that old corrections outside 30-day window are ignored."""
        sender = 'old@example.com'

        # Insert old correction (outside window) directly
        conn = sqlite3.connect(self.db_path)
        old_date = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("""
            INSERT INTO user_corrections (
                message_id, sender, original_priority, user_priority,
                correction_type, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, ('msg_old', sender, 'Medium', 'High', 'priority_override', old_date))
        conn.commit()
        conn.close()

        # Get adjustment - should be 0 (outside window)
        adjustment = self.classifier._get_correction_adjustment(sender, '', '')
        self.assertEqual(adjustment, 0.0)


class TestPriorityHelperMethods(unittest.TestCase):
    """Test helper methods and utility functions."""

    def test_is_upgrade(self):
        """Test priority upgrade detection."""
        self.assertTrue(PriorityClassifier._is_upgrade('Low', 'Medium'))
        self.assertTrue(PriorityClassifier._is_upgrade('Medium', 'High'))
        self.assertTrue(PriorityClassifier._is_upgrade('Low', 'High'))
        self.assertFalse(PriorityClassifier._is_upgrade('High', 'Medium'))
        self.assertFalse(PriorityClassifier._is_upgrade('Medium', 'Low'))
        self.assertFalse(PriorityClassifier._is_upgrade('Medium', 'Medium'))

    def test_is_downgrade(self):
        """Test priority downgrade detection."""
        self.assertTrue(PriorityClassifier._is_downgrade('High', 'Medium'))
        self.assertTrue(PriorityClassifier._is_downgrade('Medium', 'Low'))
        self.assertTrue(PriorityClassifier._is_downgrade('High', 'Low'))
        self.assertFalse(PriorityClassifier._is_downgrade('Low', 'Medium'))
        self.assertFalse(PriorityClassifier._is_downgrade('Medium', 'High'))
        self.assertFalse(PriorityClassifier._is_downgrade('Medium', 'Medium'))

    def test_upgrade_priority_levels(self):
        """Test priority upgrade method."""
        self.assertEqual(PriorityClassifier._upgrade_priority('Low'), 'Medium')
        self.assertEqual(PriorityClassifier._upgrade_priority('Medium'), 'High')
        self.assertEqual(PriorityClassifier._upgrade_priority('High'), 'High')

    def test_downgrade_priority_levels(self):
        """Test priority downgrade method."""
        self.assertEqual(PriorityClassifier._downgrade_priority('High'), 'Medium')
        self.assertEqual(PriorityClassifier._downgrade_priority('Medium'), 'Low')
        self.assertEqual(PriorityClassifier._downgrade_priority('Low'), 'Low')

    def test_get_visual_indicator(self):
        """Test visual indicator retrieval."""
        self.assertEqual(PriorityClassifier._get_visual_indicator('High'), '🔴')
        self.assertEqual(PriorityClassifier._get_visual_indicator('Medium'), '🟡')
        self.assertEqual(PriorityClassifier._get_visual_indicator('Low'), '🔵')
        self.assertEqual(PriorityClassifier._get_visual_indicator('Unknown'), '⚪')


if __name__ == '__main__':
    unittest.main()
