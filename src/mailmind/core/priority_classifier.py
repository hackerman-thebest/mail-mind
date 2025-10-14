"""
Priority Classifier - Enhanced Priority Classification with User Learning

This module builds upon EmailAnalysisEngine (Story 1.3) to provide intelligent,
learning-based priority classification for emails. It tracks sender importance,
learns from user corrections, and continuously improves classification accuracy.

Key Features:
- Enhanced priority classification with confidence scores
- Sender importance tracking and scoring
- User correction recording and learning
- Classification accuracy tracking and reporting
- VIP sender management
- Adaptive learning from user behavior

Dependencies:
- Story 1.3: EmailAnalysisEngine (base priority classification)
- SQLite3: For persistent storage of corrections and sender data

Author: MailMind Development Team
Created: 2025-10-13
Story: 1.4
"""

import sqlite3
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PriorityClassifier:
    """
    Enhanced priority classification with learning from user corrections.

    Builds upon EmailAnalysisEngine (Story 1.3) basic priority classification
    by adding:
    - Sender importance scoring
    - User correction learning
    - Adaptive confidence adjustments
    - VIP sender management
    - Classification accuracy tracking

    Usage:
        >>> classifier = PriorityClassifier(db_path="mailmind.db")
        >>> email = {"metadata": {"from": "boss@company.com", "subject": "..."}, ...}
        >>> base_analysis = {"priority": "Medium", "confidence": 0.7, ...}
        >>> enhanced = classifier.classify_priority(email, base_analysis)
        >>> print(f"Priority: {enhanced['priority']} ({enhanced['confidence']:.0%} confident)")
    """

    # Priority levels for adjustment calculations
    PRIORITY_LEVELS = ['Low', 'Medium', 'High']

    # Adjustment thresholds
    HIGH_IMPORTANCE_THRESHOLD = 0.8
    LOW_IMPORTANCE_THRESHOLD = 0.3
    HIGH_CONFIDENCE_THRESHOLD = 0.8

    # Learning parameters
    SENDER_ADJUSTMENT_STEP = 0.05  # How much to adjust sender importance per correction
    MAX_CORRECTION_ADJUSTMENT = 0.3  # Maximum confidence adjustment from corrections
    CORRECTION_LOOKBACK_DAYS = 30  # Days to consider for correction patterns

    def __init__(self, db_path: str):
        """
        Initialize Priority Classifier with database connection.

        Args:
            db_path: Path to SQLite database file

        Raises:
            sqlite3.Error: If database connection fails
        """
        self.db_path = db_path
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row  # Enable column access by name
        self._init_db()
        logger.info(f"PriorityClassifier initialized with database: {db_path}")

    def _init_db(self) -> None:
        """
        Initialize database schema for priority classification.

        Creates tables:
        - user_corrections: Stores user priority overrides for learning
        - sender_importance: Tracks sender importance scores

        Extends email_analysis table from Story 1.3 with override fields.
        """
        cursor = self.db.cursor()

        # Check if email_analysis table exists and extend it
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='email_analysis'
        """)

        if cursor.fetchone():
            # Extend existing email_analysis table with override fields
            try:
                cursor.execute("ALTER TABLE email_analysis ADD COLUMN user_override TEXT")
                logger.info("Added user_override column to email_analysis")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                cursor.execute("ALTER TABLE email_analysis ADD COLUMN override_reason TEXT")
                logger.info("Added override_reason column to email_analysis")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                cursor.execute("ALTER TABLE email_analysis ADD COLUMN original_priority TEXT")
                logger.info("Added original_priority column to email_analysis")
            except sqlite3.OperationalError:
                # Column already exists
                pass

        # Create user_corrections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                sender TEXT NOT NULL,

                -- Original classification
                original_priority TEXT CHECK(original_priority IN ('High', 'Medium', 'Low')),
                original_confidence REAL,

                -- User correction
                user_priority TEXT CHECK(user_priority IN ('High', 'Medium', 'Low')),
                correction_reason TEXT,

                -- Learning data
                correction_type TEXT CHECK(correction_type IN (
                    'priority_override',
                    'sender_importance',
                    'category_adjustment',
                    'urgency_misdetection'
                )),

                -- Metadata
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                applied_to_model BOOLEAN DEFAULT 0
            )
        """)

        # Create indexes for user_corrections
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_corrections_sender
            ON user_corrections(sender)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_corrections_timestamp
            ON user_corrections(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_corrections_applied
            ON user_corrections(applied_to_model)
        """)

        # Create sender_importance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sender_importance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_email TEXT UNIQUE NOT NULL,
                sender_name TEXT,

                -- Importance scoring
                importance_score REAL DEFAULT 0.5,
                email_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                correction_count INTEGER DEFAULT 0,

                -- User flags
                is_vip BOOLEAN DEFAULT 0,
                is_blocked BOOLEAN DEFAULT 0,

                -- Metadata
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for sender_importance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sender_email
            ON sender_importance(sender_email)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_importance_score
            ON sender_importance(importance_score)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_is_vip
            ON sender_importance(is_vip)
        """)

        self.db.commit()
        logger.info("Database schema initialized successfully")

    def classify_priority(
        self,
        email: Dict[str, Any],
        base_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced priority classification with user learning.

        Takes base priority from Story 1.3's EmailAnalysisEngine and enhances it
        with sender importance scoring and user correction patterns.

        Args:
            email: Preprocessed email data with metadata and content
            base_analysis: Basic analysis from Story 1.3 including base priority

        Returns:
            Enhanced priority classification dictionary with:
            - priority: Enhanced priority level (High/Medium/Low)
            - confidence: Confidence score (0.0 - 1.0)
            - sender_importance: Sender importance score
            - base_priority: Original priority from Story 1.3
            - adjustments: Details of applied adjustments
            - visual_indicator: Emoji for UI display (🔴🟡🔵)

        Example:
            >>> email = {"metadata": {"from": "boss@company.com"}, ...}
            >>> base = {"priority": "Medium", "confidence": 0.7, ...}
            >>> result = classifier.classify_priority(email, base)
            >>> print(f"{result['visual_indicator']} {result['priority']}")
            🔴 High
        """
        # Start with base priority from Story 1.3
        base_priority = base_analysis.get('priority', 'Medium')
        base_confidence = base_analysis.get('confidence', 0.5)

        # Get sender information
        sender = email.get('metadata', {}).get('from', 'unknown@unknown.com')
        sender_importance = self._get_sender_importance(sender)

        # Apply sender importance adjustment
        adjusted_priority, confidence = self._adjust_for_sender(
            base_priority,
            base_confidence,
            sender_importance
        )

        # Apply user correction patterns
        subject = email.get('metadata', {}).get('subject', '')
        body = email.get('content', {}).get('body', '')
        correction_adjustment = self._get_correction_adjustment(sender, subject, body)

        final_priority, final_confidence = self._apply_corrections(
            adjusted_priority,
            confidence,
            correction_adjustment
        )

        # Get visual indicator
        visual_indicator = self._get_visual_indicator(final_priority)

        result = {
            'priority': final_priority,
            'confidence': final_confidence,
            'sender_importance': sender_importance['score'],
            'base_priority': base_priority,
            'adjustments': {
                'sender_adjustment': sender_importance['adjustment'],
                'correction_adjustment': correction_adjustment
            },
            'visual_indicator': visual_indicator,
            'classification_source': 'enhanced_learning'
        }

        logger.debug(
            f"Priority classification: {base_priority} → {final_priority} "
            f"(confidence: {final_confidence:.2f}, sender_importance: {sender_importance['score']:.2f})"
        )

        return result

    def _get_sender_importance(self, sender: str) -> Dict[str, Any]:
        """
        Get sender importance score from database.

        Args:
            sender: Email address of sender

        Returns:
            Dictionary containing sender importance data:
            - score: Importance score (0.0 - 1.0)
            - is_vip: Whether sender is marked as VIP
            - email_count: Number of emails received from sender
            - reply_count: Number of replies to sender
            - adjustment: Priority adjustment (-1, 0, +1)
        """
        cursor = self.db.execute("""
            SELECT importance_score, is_vip, email_count, reply_count
            FROM sender_importance
            WHERE sender_email = ?
        """, (sender,))

        row = cursor.fetchone()

        if row:
            score = row['importance_score']
            is_vip = bool(row['is_vip'])
            email_count = row['email_count']
            reply_count = row['reply_count']

            return {
                'score': score,
                'is_vip': is_vip,
                'email_count': email_count,
                'reply_count': reply_count,
                'adjustment': self._calculate_sender_adjustment(score, is_vip)
            }
        else:
            # New sender - neutral importance
            return {
                'score': 0.5,
                'is_vip': False,
                'email_count': 0,
                'reply_count': 0,
                'adjustment': 0
            }

    def _calculate_sender_adjustment(
        self,
        importance_score: float,
        is_vip: bool
    ) -> int:
        """
        Calculate priority adjustment based on sender importance.

        Args:
            importance_score: Sender importance score (0.0 - 1.0)
            is_vip: Whether sender is marked as VIP

        Returns:
            Priority adjustment: +1 (upgrade), 0 (no change), -1 (downgrade)
        """
        if is_vip or importance_score > self.HIGH_IMPORTANCE_THRESHOLD:
            return +1  # Upgrade priority
        elif importance_score < self.LOW_IMPORTANCE_THRESHOLD:
            return -1  # Downgrade priority
        else:
            return 0  # No adjustment

    def _get_correction_adjustment(
        self,
        sender: str,
        subject: str,
        body: str
    ) -> float:
        """
        Get priority adjustment based on user correction history.

        Analyzes recent user corrections (last 30 days) for this sender and
        returns a confidence adjustment to apply.

        Args:
            sender: Email address of sender
            subject: Email subject line
            body: Email body content

        Returns:
            Confidence adjustment value (-0.3 to +0.3)
        """
        # Get recent corrections for this sender
        cursor = self.db.execute("""
            SELECT original_priority, user_priority, correction_type
            FROM user_corrections
            WHERE sender = ?
            AND timestamp > datetime('now', '-' || ? || ' days')
            ORDER BY timestamp DESC
            LIMIT 10
        """, (sender, self.CORRECTION_LOOKBACK_DAYS))

        corrections = cursor.fetchall()

        if not corrections:
            return 0.0

        # Calculate adjustment based on correction patterns
        upgrade_count = sum(
            1 for row in corrections
            if self._is_upgrade(row['original_priority'], row['user_priority'])
        )
        downgrade_count = sum(
            1 for row in corrections
            if self._is_downgrade(row['original_priority'], row['user_priority'])
        )

        total = len(corrections)

        if upgrade_count > downgrade_count:
            # User tends to upgrade this sender - increase confidence in higher priorities
            adjustment = (upgrade_count / total) * 0.2
            return min(self.MAX_CORRECTION_ADJUSTMENT, adjustment)
        elif downgrade_count > upgrade_count:
            # User tends to downgrade this sender - decrease confidence
            adjustment = (downgrade_count / total) * 0.2
            return -min(self.MAX_CORRECTION_ADJUSTMENT, adjustment)
        else:
            return 0.0

    def _adjust_for_sender(
        self,
        priority: str,
        confidence: float,
        sender_importance: Dict[str, Any]
    ) -> Tuple[str, float]:
        """
        Apply sender importance adjustment to priority.

        Args:
            priority: Current priority level
            confidence: Current confidence score
            sender_importance: Sender importance data

        Returns:
            Tuple of (adjusted_priority, adjusted_confidence)
        """
        adjustment = sender_importance['adjustment']

        if adjustment == 0:
            return priority, confidence

        current_index = self.PRIORITY_LEVELS.index(priority)

        # Adjust priority
        new_index = max(0, min(len(self.PRIORITY_LEVELS) - 1, current_index + adjustment))
        new_priority = self.PRIORITY_LEVELS[new_index]

        # Adjust confidence based on sender data quantity
        if sender_importance['email_count'] > 10:
            # More data = more confidence in adjustment
            confidence_boost = 0.1
        else:
            confidence_boost = 0.0

        new_confidence = min(1.0, confidence + confidence_boost)

        return new_priority, new_confidence

    def _apply_corrections(
        self,
        priority: str,
        confidence: float,
        correction_adjustment: float
    ) -> Tuple[str, float]:
        """
        Apply user correction patterns to final classification.

        Args:
            priority: Current priority level
            confidence: Current confidence score
            correction_adjustment: Adjustment from correction history

        Returns:
            Tuple of (final_priority, final_confidence)
        """
        adjusted_confidence = min(1.0, max(0.0, confidence + correction_adjustment))

        # If confidence adjustment is strong, may change priority
        if correction_adjustment > 0.2 and priority != 'High':
            priority = self._upgrade_priority(priority)
        elif correction_adjustment < -0.2 and priority != 'Low':
            priority = self._downgrade_priority(priority)

        return priority, adjusted_confidence

    def record_user_override(
        self,
        message_id: str,
        sender: str,
        original_priority: str,
        original_confidence: float,
        user_priority: str,
        reason: Optional[str] = None
    ) -> None:
        """
        Record user priority override for learning.

        This is the core learning mechanism. When a user manually changes an email's
        priority, we record it to improve future classifications for similar emails.

        Args:
            message_id: Email message ID
            sender: Email sender address
            original_priority: System's original classification
            original_confidence: System's confidence score
            user_priority: User's corrected priority
            reason: Optional reason for correction (from UI feedback prompt)

        Example:
            >>> classifier.record_user_override(
            ...     message_id="msg_12345",
            ...     sender="boss@company.com",
            ...     original_priority="Medium",
            ...     original_confidence=0.72,
            ...     user_priority="High",
            ...     reason="Wrong sender importance"
            ... )
        """
        # Determine correction type
        correction_type = self._determine_correction_type(
            original_priority,
            user_priority,
            reason
        )

        # Store correction
        self.db.execute("""
            INSERT INTO user_corrections (
                message_id, sender,
                original_priority, original_confidence,
                user_priority, correction_reason, correction_type,
                applied_to_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            message_id, sender,
            original_priority, original_confidence,
            user_priority, reason, correction_type
        ))

        # Update sender importance
        self._update_sender_importance(sender, original_priority, user_priority)

        self.db.commit()

        logger.info(
            f"Recorded user override: {original_priority} → {user_priority} "
            f"for sender {sender} (reason: {reason})"
        )

    def _determine_correction_type(
        self,
        original_priority: str,
        user_priority: str,
        reason: Optional[str]
    ) -> str:
        """
        Determine the type of correction based on reason and priority change.

        Args:
            original_priority: Original system priority
            user_priority: User's corrected priority
            reason: User-provided reason (optional)

        Returns:
            Correction type string
        """
        if reason:
            reason_lower = reason.lower()
            if 'sender' in reason_lower or 'vip' in reason_lower or 'importance' in reason_lower:
                return 'sender_importance'
            elif 'urgent' in reason_lower or 'deadline' in reason_lower or 'misdetect' in reason_lower:
                return 'urgency_misdetection'
            elif 'category' in reason_lower or 'newsletter' in reason_lower or 'incorrect' in reason_lower:
                return 'category_adjustment'

        return 'priority_override'

    def _update_sender_importance(
        self,
        sender: str,
        original_priority: str,
        user_priority: str
    ) -> None:
        """
        Update sender importance based on correction.

        Args:
            sender: Email sender address
            original_priority: Original system priority
            user_priority: User's corrected priority
        """
        # Get current importance
        cursor = self.db.execute("""
            SELECT importance_score, correction_count
            FROM sender_importance
            WHERE sender_email = ?
        """, (sender,))

        row = cursor.fetchone()

        if row:
            current_score = row['importance_score']
            correction_count = row['correction_count']
        else:
            current_score = 0.5
            correction_count = 0

        # Calculate adjustment
        if self._is_upgrade(original_priority, user_priority):
            # User upgraded - increase importance
            adjustment = self.SENDER_ADJUSTMENT_STEP
        elif self._is_downgrade(original_priority, user_priority):
            # User downgraded - decrease importance
            adjustment = -self.SENDER_ADJUSTMENT_STEP
        else:
            adjustment = 0.0

        new_score = max(0.0, min(1.0, current_score + adjustment))
        new_correction_count = correction_count + 1

        # Update or insert
        self.db.execute("""
            INSERT INTO sender_importance (
                sender_email, importance_score, correction_count,
                last_seen, last_updated
            ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(sender_email) DO UPDATE SET
                importance_score = ?,
                correction_count = ?,
                last_seen = CURRENT_TIMESTAMP,
                last_updated = CURRENT_TIMESTAMP
        """, (sender, new_score, new_correction_count, new_score, new_correction_count))

        logger.debug(
            f"Updated sender importance: {sender} "
            f"score: {current_score:.2f} → {new_score:.2f}"
        )

    def get_classification_accuracy(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate classification accuracy over time period.

        Accuracy is calculated as: (Total - Corrections) / Total
        Target accuracy: >85% after 30 days of use.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Accuracy metrics dictionary with:
            - accuracy_percentage: Overall accuracy (0-100)
            - total_classified: Total emails classified
            - user_corrections: Number of user corrections
            - period_days: Analysis period
            - target_met: Whether 85% target is met
            - trend: "improving", "stable", or "declining"

        Example:
            >>> accuracy = classifier.get_classification_accuracy(days=30)
            >>> print(f"Accuracy: {accuracy['accuracy_percentage']:.1f}%")
            Accuracy: 87.5%
        """
        # Check if email_analysis table exists
        cursor = self.db.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='email_analysis'
        """)
        if not cursor.fetchone():
            # Table doesn't exist yet - return zero accuracy
            return {
                'accuracy_percentage': 0.0,
                'total_classified': 0,
                'user_corrections': 0,
                'period_days': days,
                'target_met': False,
                'trend': 'insufficient_data'
            }

        # Count total classifications in period
        cursor = self.db.execute("""
            SELECT COUNT(*) as count FROM email_analysis
            WHERE processed_date > datetime('now', '-' || ? || ' days')
        """, (days,))
        total = cursor.fetchone()['count']

        # Count corrections in period
        cursor = self.db.execute("""
            SELECT COUNT(*) as count FROM user_corrections
            WHERE timestamp > datetime('now', '-' || ? || ' days')
        """, (days,))
        corrections = cursor.fetchone()['count']

        if total == 0:
            accuracy = 0.0
        else:
            accuracy = (total - corrections) / total

        # Calculate trend (compare to previous period)
        prev_period_start = days * 2
        prev_period_end = days

        cursor = self.db.execute("""
            SELECT COUNT(*) as count FROM email_analysis
            WHERE processed_date BETWEEN
                datetime('now', '-' || ? || ' days') AND
                datetime('now', '-' || ? || ' days')
        """, (prev_period_start, prev_period_end))
        prev_total = cursor.fetchone()['count']

        cursor = self.db.execute("""
            SELECT COUNT(*) as count FROM user_corrections
            WHERE timestamp BETWEEN
                datetime('now', '-' || ? || ' days') AND
                datetime('now', '-' || ? || ' days')
        """, (prev_period_start, prev_period_end))
        prev_corrections = cursor.fetchone()['count']

        if prev_total > 0:
            prev_accuracy = (prev_total - prev_corrections) / prev_total
            if accuracy > prev_accuracy + 0.05:
                trend = "improving"
            elif accuracy < prev_accuracy - 0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        result = {
            'accuracy_percentage': accuracy * 100,
            'total_classified': total,
            'user_corrections': corrections,
            'period_days': days,
            'target_met': accuracy >= 0.85,
            'trend': trend
        }

        logger.info(
            f"Classification accuracy ({days} days): {accuracy * 100:.1f}% "
            f"({total} classified, {corrections} corrected, trend: {trend})"
        )

        return result

    @staticmethod
    def _get_visual_indicator(priority: str) -> str:
        """
        Get visual indicator emoji for priority level.

        Args:
            priority: Priority level (High/Medium/Low)

        Returns:
            Emoji indicator (🔴/🟡/🔵)
        """
        indicators = {
            'High': '🔴',
            'Medium': '🟡',
            'Low': '🔵'
        }
        return indicators.get(priority, '⚪')

    @staticmethod
    def _is_upgrade(original: str, new: str) -> bool:
        """Check if new priority is higher than original."""
        levels = {'Low': 0, 'Medium': 1, 'High': 2}
        return levels.get(new, 0) > levels.get(original, 0)

    @staticmethod
    def _is_downgrade(original: str, new: str) -> bool:
        """Check if new priority is lower than original."""
        levels = {'Low': 0, 'Medium': 1, 'High': 2}
        return levels.get(new, 0) < levels.get(original, 0)

    @staticmethod
    def _upgrade_priority(priority: str) -> str:
        """Upgrade priority by one level."""
        if priority == 'Low':
            return 'Medium'
        elif priority == 'Medium':
            return 'High'
        return 'High'

    @staticmethod
    def _downgrade_priority(priority: str) -> str:
        """Downgrade priority by one level."""
        if priority == 'High':
            return 'Medium'
        elif priority == 'Medium':
            return 'Low'
        return 'Low'

    def set_sender_vip(self, sender: str, is_vip: bool = True) -> None:
        """
        Mark sender as VIP (or remove VIP status).

        Args:
            sender: Email address of sender
            is_vip: Whether to mark as VIP (default: True)
        """
        self.db.execute("""
            INSERT INTO sender_importance (
                sender_email, is_vip, last_updated
            ) VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(sender_email) DO UPDATE SET
                is_vip = ?,
                last_updated = CURRENT_TIMESTAMP
        """, (sender, is_vip, is_vip))

        self.db.commit()
        logger.info(f"Set VIP status for {sender}: {is_vip}")

    def get_sender_stats(self, sender: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed statistics for a sender.

        Args:
            sender: Email address of sender

        Returns:
            Dictionary with sender statistics or None if not found
        """
        cursor = self.db.execute("""
            SELECT * FROM sender_importance
            WHERE sender_email = ?
        """, (sender,))

        row = cursor.fetchone()

        if row:
            return dict(row)
        else:
            return None

    def close(self) -> None:
        """Close database connection."""
        self.db.close()
        logger.info("PriorityClassifier database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
