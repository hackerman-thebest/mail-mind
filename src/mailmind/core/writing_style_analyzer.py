"""
Writing Style Analyzer for MailMind

This module analyzes user's writing style from sent emails to enable authentic response generation.
Implements part of Story 1.5: Response Generation Assistant

Key Features:
- Greeting style extraction (Hi/Hello/Dear)
- Closing style extraction (Thanks/Best/Regards)
- Formality level calculation (0.0-1.0 scale)
- Common phrase extraction
- Sentence structure analysis
- Tone marker detection
- Style profile persistence in SQLite

Integration:
- Works with sent email data to learn user patterns
- Stores style profiles for ResponseGenerator to use
- Supports incremental learning from user edits
"""

import re
import json
import logging
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)


class WritingStyleError(Exception):
    """Base exception for writing style analysis errors."""
    pass


class WritingStyleAnalyzer:
    """
    Analyzes user's writing style from sent emails.

    Extracts patterns from 20-50 sent emails to build a writing style profile:
    - Greeting style (Hi/Hello/Dear/etc.)
    - Closing style (Thanks/Best/Regards/etc.)
    - Formality level (0.0 casual to 1.0 formal)
    - Common phrases and expressions
    - Average sentence length
    - Tone markers (enthusiasm, directness, politeness)

    The style profile is used by ResponseGenerator to match user's authentic voice.

    Database Schema:
    - writing_style_profiles: Stores user writing style profiles
    - style_analysis_history: Tracks incremental learning from edits
    """

    # Greeting patterns to detect
    GREETING_PATTERNS = [
        (r'^(Hi|Hello|Hey|Dear|Greetings|Good\s+(?:morning|afternoon|evening))', 'greeting_line'),
        (r'^(Hi\s+there|Hello\s+there)', 'informal_greeting'),
        (r'^(Dear\s+(?:Sir|Madam|Mr\.|Mrs\.|Ms\.))', 'formal_greeting'),
    ]

    # Closing patterns to detect
    CLOSING_PATTERNS = [
        (r'(Thanks|Thank\s+you|Best\s+regards|Best|Regards|Sincerely|Cheers|Warmly)', 'closing_line'),
        (r'(Kind\s+regards|Warm\s+regards|With\s+gratitude)', 'formal_closing'),
    ]

    # Formality indicators
    INFORMAL_INDICATORS = [
        # Contractions
        r"n't|'s|'re|'ve|'ll|'d",
        # Casual words
        r'\b(hey|yeah|yep|nope|gonna|wanna|gotta)\b',
        # Exclamations
        r'!',
    ]

    FORMAL_INDICATORS = [
        # Formal greetings/closings
        r'\b(Dear|Sincerely|Regards)\b',
        # Formal transitional words
        r'\b(furthermore|therefore|accordingly|consequently|nevertheless)\b',
        # Passive voice (simple heuristic: "is/was/been" + past participle)
        r'\b(is|was|been)\s+\w+ed\b',
    ]

    def __init__(self, db_path: str = 'data/mailmind.db'):
        """
        Initialize Writing Style Analyzer.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.info(f"WritingStyleAnalyzer initialized with database: {db_path}")

    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create writing_style_profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS writing_style_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_name TEXT UNIQUE NOT NULL DEFAULT 'default',

                -- Style components
                greeting_style TEXT,
                closing_style TEXT,
                formality_level REAL CHECK(formality_level BETWEEN 0.0 AND 1.0),

                -- JSON fields for complex data
                common_phrases TEXT,  -- JSON array
                tone_markers TEXT,     -- JSON object

                -- Statistics
                avg_sentence_length REAL,
                sample_size INTEGER,

                -- Metadata
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(profile_name)
            )
        ''')

        # Create style_analysis_history table for incremental learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS style_analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_name TEXT NOT NULL,

                -- Edit tracking
                original_text TEXT,
                edited_text TEXT,
                edit_percentage REAL,

                -- Pattern changes detected
                changes_detected TEXT,  -- JSON object

                -- Metadata
                analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(profile_name) REFERENCES writing_style_profiles(profile_name)
            )
        ''')

        # Create index for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_profile_name ON writing_style_profiles(profile_name)')

        conn.commit()
        conn.close()

        logger.info("Writing style database initialized successfully")

    def analyze_sent_emails(self, sent_emails: List[Dict[str, Any]],
                           profile_name: str = 'default') -> Dict[str, Any]:
        """
        Analyze sent emails to extract writing style patterns.

        This is the main entry point for style analysis. Processes 20-50 emails
        to build a comprehensive writing style profile.

        Args:
            sent_emails: List of sent email dictionaries with 'body', 'subject' fields
            profile_name: Name for this style profile (default: 'default')

        Returns:
            Writing style profile dictionary:
            {
                "greeting_style": "Hi",
                "closing_style": "Thanks",
                "formality_level": 0.5,
                "common_phrases": ["looking forward", "let me know"],
                "avg_sentence_length": 15.3,
                "tone_markers": {"enthusiasm": 0.6, "directness": 0.7},
                "sample_size": 42,
                "last_updated": "2025-10-13T14:30:00Z"
            }

        Raises:
            WritingStyleError: If analysis fails critically
        """
        if not sent_emails:
            logger.warning("No sent emails provided, using default style")
            return self._default_style_profile()

        logger.info(f"Analyzing writing style from {len(sent_emails)} sent emails")

        # Determine optimal sample size (20-50 emails, but use all if less than 20)
        if len(sent_emails) < 20:
            sample_size = len(sent_emails)
            sample = sent_emails
        else:
            sample_size = min(50, len(sent_emails))
            sample = sent_emails[:sample_size]

        logger.debug(f"Using sample of {sample_size} emails for analysis")

        try:
            # Extract greeting patterns
            greetings = self._extract_greetings(sample)
            most_common_greeting = self._get_most_common(greetings, default='Hi')

            # Extract closing patterns
            closings = self._extract_closings(sample)
            most_common_closing = self._get_most_common(closings, default='Thanks')

            # Calculate formality level
            formality = self._calculate_formality(sample)

            # Extract common phrases
            common_phrases = self._extract_common_phrases(sample)

            # Analyze sentence structure
            avg_sentence_length = self._calculate_avg_sentence_length(sample)

            # Extract tone markers
            tone_markers = self._extract_tone_markers(sample)

            # Build profile
            profile = {
                'greeting_style': most_common_greeting,
                'closing_style': most_common_closing,
                'formality_level': formality,
                'common_phrases': common_phrases[:10],  # Top 10
                'avg_sentence_length': avg_sentence_length,
                'tone_markers': tone_markers,
                'sample_size': sample_size,
                'last_updated': datetime.now().isoformat()
            }

            logger.info(f"Style analysis complete: greeting={most_common_greeting}, "
                       f"closing={most_common_closing}, formality={formality:.2f}")

            # Store profile in database
            self._save_profile(profile, profile_name)

            return profile

        except Exception as e:
            logger.error(f"Style analysis failed: {e}", exc_info=True)
            raise WritingStyleError(f"Failed to analyze writing style: {e}")

    def _extract_greetings(self, emails: List[Dict[str, Any]]) -> List[str]:
        """
        Extract greeting patterns from emails.

        Args:
            emails: List of email dictionaries

        Returns:
            List of detected greetings
        """
        greetings = []

        for email in emails:
            body = email.get('body', '')
            if not body:
                continue

            # Get first line (typically where greeting appears)
            lines = body.split('\n')
            first_line = lines[0].strip() if lines else ''

            # Try to match greeting patterns
            for pattern, _ in self.GREETING_PATTERNS:
                match = re.search(pattern, first_line, re.IGNORECASE)
                if match:
                    greeting = match.group(1).strip()
                    greetings.append(greeting)
                    logger.debug(f"Found greeting: {greeting}")
                    break

        # Return greetings or default
        return greetings if greetings else ['Hi']

    def _extract_closings(self, emails: List[Dict[str, Any]]) -> List[str]:
        """
        Extract closing patterns from emails.

        Args:
            emails: List of email dictionaries

        Returns:
            List of detected closings
        """
        closings = []

        for email in emails:
            body = email.get('body', '')
            if not body:
                continue

            # Get last 3 lines (where closing typically appears)
            lines = body.split('\n')
            last_lines = '\n'.join(lines[-3:]) if len(lines) >= 3 else body

            # Try to match closing patterns
            for pattern, _ in self.CLOSING_PATTERNS:
                match = re.search(pattern, last_lines, re.IGNORECASE)
                if match:
                    closing = match.group(1).strip()
                    closings.append(closing)
                    logger.debug(f"Found closing: {closing}")
                    break

        # Return closings or default
        return closings if closings else ['Thanks']

    def _calculate_formality(self, emails: List[Dict[str, Any]]) -> float:
        """
        Calculate formality score 0.0 (casual) to 1.0 (formal).

        Analyzes language patterns to determine overall formality level.

        Args:
            emails: List of email dictionaries

        Returns:
            Formality score between 0.0 and 1.0
        """
        formality_scores = []

        for email in emails:
            body = email.get('body', '')
            if not body:
                continue

            informal_count = 0
            formal_count = 0

            # Count informal indicators
            for pattern in self.INFORMAL_INDICATORS:
                matches = re.findall(pattern, body, re.IGNORECASE)
                informal_count += len(matches)

            # Count formal indicators
            for pattern in self.FORMAL_INDICATORS:
                matches = re.findall(pattern, body, re.IGNORECASE)
                formal_count += len(matches)

            # Calculate formality score for this email
            total = informal_count + formal_count
            if total > 0:
                formality = formal_count / total
            else:
                formality = 0.5  # Neutral if no indicators found

            formality_scores.append(formality)
            logger.debug(f"Email formality: {formality:.2f} (informal={informal_count}, formal={formal_count})")

        # Average across all emails
        avg_formality = sum(formality_scores) / len(formality_scores) if formality_scores else 0.5

        # Round to 2 decimal places
        return round(avg_formality, 2)

    def _extract_common_phrases(self, emails: List[Dict[str, Any]]) -> List[str]:
        """
        Extract common phrases and expressions from emails.

        Args:
            emails: List of email dictionaries

        Returns:
            List of common phrases (sorted by frequency)
        """
        # Extract 2-4 word phrases
        phrases = []

        for email in emails:
            body = email.get('body', '')
            if not body:
                continue

            # Normalize: lowercase, remove extra whitespace
            body = re.sub(r'\s+', ' ', body.lower())

            # Extract 2-3 word phrases
            words = body.split()
            for i in range(len(words) - 2):
                bigram = f"{words[i]} {words[i+1]}"
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"

                # Filter out common stopwords and short phrases
                if len(bigram) > 8 and not self._is_stopword_phrase(bigram):
                    phrases.append(bigram)

                if len(trigram) > 12 and not self._is_stopword_phrase(trigram):
                    phrases.append(trigram)

        # Count frequency and return top phrases
        if phrases:
            phrase_counts = Counter(phrases)
            # Filter: must appear at least 2 times
            common = [phrase for phrase, count in phrase_counts.most_common(20) if count >= 2]
            logger.debug(f"Found {len(common)} common phrases")
            return common[:10]  # Top 10

        return []

    def _is_stopword_phrase(self, phrase: str) -> bool:
        """
        Check if phrase is just common stopwords.

        Args:
            phrase: Phrase to check

        Returns:
            True if phrase is mostly stopwords
        """
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been',
                    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                    'can', 'could', 'may', 'might', 'must', 'this', 'that', 'these', 'those'}

        words = phrase.split()
        stopword_count = sum(1 for word in words if word in stopwords)

        # If more than 50% are stopwords, consider it a stopword phrase
        return stopword_count > len(words) / 2

    def _calculate_avg_sentence_length(self, emails: List[Dict[str, Any]]) -> float:
        """
        Calculate average sentence length in words.

        Args:
            emails: List of email dictionaries

        Returns:
            Average sentence length
        """
        all_sentences = []

        for email in emails:
            body = email.get('body', '')
            if not body:
                continue

            # Split into sentences (basic splitting on .!?)
            sentences = re.split(r'[.!?]+', body)

            for sentence in sentences:
                words = sentence.strip().split()
                if words:  # Ignore empty sentences
                    all_sentences.append(len(words))

        avg_length = sum(all_sentences) / len(all_sentences) if all_sentences else 15.0

        return round(avg_length, 1)

    def _extract_tone_markers(self, emails: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Extract tone markers (enthusiasm, directness, politeness).

        Args:
            emails: List of email dictionaries

        Returns:
            Dictionary of tone marker scores (0.0-1.0)
        """
        enthusiasm_count = 0
        directness_count = 0
        politeness_count = 0
        total_emails = len(emails)

        for email in emails:
            body = email.get('body')
            if not body:
                continue

            body = body.lower()

            # Enthusiasm indicators
            if re.search(r'!|excit|great|excellent|awesome|fantastic', body):
                enthusiasm_count += 1

            # Directness indicators (short sentences, imperatives)
            sentences = re.split(r'[.!?]+', body)
            short_sentences = sum(1 for s in sentences if len(s.split()) < 10)
            if short_sentences > len(sentences) / 2:
                directness_count += 1

            # Politeness indicators
            if re.search(r'please|thank|appreciate|grateful|kindly|could you', body):
                politeness_count += 1

        return {
            'enthusiasm': round(enthusiasm_count / total_emails, 2) if total_emails > 0 else 0.5,
            'directness': round(directness_count / total_emails, 2) if total_emails > 0 else 0.5,
            'politeness': round(politeness_count / total_emails, 2) if total_emails > 0 else 0.5,
        }

    def _get_most_common(self, items: List[str], default: str) -> str:
        """
        Get most common item from list.

        Args:
            items: List of items
            default: Default value if list is empty

        Returns:
            Most common item or default
        """
        if not items:
            return default

        counter = Counter(items)
        most_common = counter.most_common(1)

        return most_common[0][0] if most_common else default

    def _default_style_profile(self) -> Dict[str, Any]:
        """
        Return default style profile when no sent emails available.

        Returns:
            Default professional style profile
        """
        logger.info("Using default professional style profile")

        return {
            'greeting_style': 'Hi',
            'closing_style': 'Thanks',
            'formality_level': 0.5,  # Balanced
            'common_phrases': [],
            'avg_sentence_length': 15.0,
            'tone_markers': {
                'enthusiasm': 0.5,
                'directness': 0.5,
                'politeness': 0.7
            },
            'sample_size': 0,
            'last_updated': datetime.now().isoformat()
        }

    def _save_profile(self, profile: Dict[str, Any], profile_name: str = 'default'):
        """
        Save writing style profile to database.

        Args:
            profile: Style profile dictionary
            profile_name: Name for this profile
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO writing_style_profiles (
                    profile_name, greeting_style, closing_style, formality_level,
                    common_phrases, tone_markers, avg_sentence_length, sample_size,
                    last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile_name,
                profile['greeting_style'],
                profile['closing_style'],
                profile['formality_level'],
                json.dumps(profile['common_phrases']),
                json.dumps(profile['tone_markers']),
                profile['avg_sentence_length'],
                profile['sample_size'],
                profile['last_updated']
            ))

            conn.commit()
            conn.close()

            logger.info(f"Style profile '{profile_name}' saved to database")

        except Exception as e:
            logger.error(f"Failed to save style profile: {e}")
            raise WritingStyleError(f"Failed to save profile: {e}")

    def load_profile(self, profile_name: str = 'default') -> Optional[Dict[str, Any]]:
        """
        Load writing style profile from database.

        Args:
            profile_name: Name of profile to load

        Returns:
            Style profile dictionary or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT greeting_style, closing_style, formality_level,
                       common_phrases, tone_markers, avg_sentence_length,
                       sample_size, last_updated
                FROM writing_style_profiles
                WHERE profile_name = ?
            ''', (profile_name,))

            row = cursor.fetchone()
            conn.close()

            if row:
                profile = {
                    'greeting_style': row[0],
                    'closing_style': row[1],
                    'formality_level': row[2],
                    'common_phrases': json.loads(row[3]),
                    'tone_markers': json.loads(row[4]),
                    'avg_sentence_length': row[5],
                    'sample_size': row[6],
                    'last_updated': row[7]
                }

                logger.info(f"Loaded style profile '{profile_name}'")
                return profile

            logger.warning(f"Profile '{profile_name}' not found")
            return None

        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return None

    def record_edit_feedback(self, original_text: str, edited_text: str,
                           profile_name: str = 'default'):
        """
        Record user edit to learn from style adjustments.

        This supports incremental learning by tracking how users edit
        generated responses.

        Args:
            original_text: Original generated text
            edited_text: User's edited version
            profile_name: Profile to update
        """
        try:
            # Calculate edit percentage
            original_len = len(original_text)
            edited_len = len(edited_text)

            if original_len == 0:
                edit_percentage = 0.0
            else:
                # Simple metric: character difference ratio
                diff = abs(edited_len - original_len)
                edit_percentage = (diff / original_len) * 100

            # Detect significant changes (for future learning)
            changes = self._detect_style_changes(original_text, edited_text)

            # Store in history
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO style_analysis_history (
                    profile_name, original_text, edited_text,
                    edit_percentage, changes_detected
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                profile_name,
                original_text,
                edited_text,
                round(edit_percentage, 2),
                json.dumps(changes)
            ))

            conn.commit()
            conn.close()

            logger.debug(f"Recorded edit feedback: {edit_percentage:.1f}% changed")

        except Exception as e:
            logger.error(f"Failed to record edit feedback: {e}")

    def _detect_style_changes(self, original: str, edited: str) -> Dict[str, Any]:
        """
        Detect significant style changes between original and edited text.

        Args:
            original: Original text
            edited: Edited text

        Returns:
            Dictionary of detected changes
        """
        changes = {}

        # Check greeting change
        original_greeting = self._extract_greetings([{'body': original}])
        edited_greeting = self._extract_greetings([{'body': edited}])

        if original_greeting != edited_greeting:
            changes['greeting_changed'] = {
                'from': original_greeting[0] if original_greeting else None,
                'to': edited_greeting[0] if edited_greeting else None
            }

        # Check closing change
        original_closing = self._extract_closings([{'body': original}])
        edited_closing = self._extract_closings([{'body': edited}])

        if original_closing != edited_closing:
            changes['closing_changed'] = {
                'from': original_closing[0] if original_closing else None,
                'to': edited_closing[0] if edited_closing else None
            }

        # Check formality change (rough heuristic)
        original_formality = self._calculate_formality([{'body': original}])
        edited_formality = self._calculate_formality([{'body': edited}])

        if abs(original_formality - edited_formality) > 0.2:
            changes['formality_changed'] = {
                'from': original_formality,
                'to': edited_formality
            }

        return changes


# Convenience function for quick style analysis
def analyze_writing_style(sent_emails: List[Dict[str, Any]],
                         db_path: str = 'data/mailmind.db') -> Dict[str, Any]:
    """
    Convenience function to analyze writing style from sent emails.

    Args:
        sent_emails: List of sent email dictionaries
        db_path: Path to database file

    Returns:
        Writing style profile dictionary
    """
    analyzer = WritingStyleAnalyzer(db_path=db_path)
    return analyzer.analyze_sent_emails(sent_emails)
