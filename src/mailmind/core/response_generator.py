"""
Response Generator for MailMind

This module generates contextual email responses matching user's writing style.
Implements Story 1.5: Response Generation Assistant

Key Features:
- AI-powered response generation using local LLM
- Three response lengths: Brief (<50 words), Standard (50-150), Detailed (150-300)
- Writing style matching from user's sent items
- Eight common scenario templates
- Four tone options: Professional, Friendly, Formal, Casual
- Thread context incorporation
- Response metrics tracking
- Performance: Brief <3s, Standard <5s, Detailed <10s

Integration:
- Uses OllamaManager (Story 1.1) for LLM inference
- Uses EmailPreprocessor (Story 1.2) for email parsing
- Uses WritingStyleAnalyzer for style matching
- Complete pipeline: Email + Style → LLM → Formatted Response
"""

import re
import time
import json
import logging
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from src.mailmind.core.ollama_manager import OllamaManager
from src.mailmind.core.writing_style_analyzer import WritingStyleAnalyzer

logger = logging.getLogger(__name__)


class ResponseGenerationError(Exception):
    """Base exception for response generation errors."""
    pass


class ResponseGenerator:
    """
    AI-powered email response generator.

    Generates contextual email responses that match user's writing style.
    Supports multiple lengths, tones, and scenario templates.

    Features:
    - Three response lengths (Brief/Standard/Detailed)
    - Four tone options (Professional/Friendly/Formal/Casual)
    - Eight scenario templates
    - Writing style matching
    - Thread context incorporation
    - Performance metrics tracking

    Performance Targets:
    - Brief responses: <3s (target), <5s (acceptable)
    - Standard responses: <5s (target), <8s (acceptable)
    - Detailed responses: <10s (target), <15s (acceptable)
    """

    # Response length targets (word counts)
    LENGTH_TARGETS = {
        'Brief': {'min': 20, 'target': 35, 'max': 50},
        'Standard': {'min': 50, 'target': 100, 'max': 150},
        'Detailed': {'min': 150, 'target': 225, 'max': 300}
    }

    # Scenario templates with generation instructions
    TEMPLATES = {
        'Meeting Acceptance': 'Confirm attendance, acknowledge time/date, express enthusiasm',
        'Meeting Decline': 'Politely decline, provide brief reason if appropriate, suggest alternative if possible',
        'Status Update': 'Provide clear status, mention progress, note any blockers, state next steps',
        'Thank You': 'Express genuine gratitude, acknowledge specific action, maintain warmth',
        'Information Request': 'Clearly state what information is needed, explain why, provide deadline if needed',
        'Acknowledgment': 'Confirm receipt, summarize key points, state next action',
        'Follow-up': 'Reference previous conversation, check current status, offer assistance',
        'Out of Office': 'State unavailability period, provide alternative contact, set return expectations'
    }

    # Tone descriptions for LLM
    TONE_DESCRIPTIONS = {
        'Professional': 'Formal business language, no contractions, structured sentences',
        'Friendly': 'Warm and approachable, some informality, conversational tone',
        'Formal': 'Very formal, use titles, structured language, passive voice acceptable',
        'Casual': 'Relaxed, conversational, contractions encouraged, informal expressions'
    }

    def __init__(self, ollama_manager: OllamaManager, db_path: str = 'data/mailmind.db'):
        """
        Initialize Response Generator.

        Args:
            ollama_manager: OllamaManager instance for LLM inference
            db_path: Path to SQLite database file
        """
        self.ollama = ollama_manager
        self.db_path = db_path
        self.style_analyzer = WritingStyleAnalyzer(db_path)

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Load user's writing style (or use default)
        self.writing_style = self._load_writing_style()

        logger.info(f"ResponseGenerator initialized with database: {db_path}")

    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create response_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS response_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT,  -- Original email message_id

                -- Response details
                response_text TEXT NOT NULL,
                response_length TEXT CHECK(response_length IN ('Brief', 'Standard', 'Detailed')),
                response_tone TEXT CHECK(response_tone IN ('Professional', 'Friendly', 'Formal', 'Casual')),
                template_used TEXT,

                -- Response metrics
                word_count INTEGER,
                processing_time_ms INTEGER,
                model_version TEXT,

                -- User feedback
                edit_percentage REAL,
                accepted BOOLEAN,
                regeneration_count INTEGER DEFAULT 0,

                -- Metadata
                generated_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_id_response ON response_history(message_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_generated_date ON response_history(generated_date)')

        # Note: writing_style_profiles table created by WritingStyleAnalyzer

        # Create performance_metrics table (may already exist from EmailAnalysisEngine)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                hardware_config TEXT,
                model_version TEXT,
                tokens_per_second REAL,
                memory_usage_mb INTEGER,
                processing_time_ms INTEGER,
                batch_size INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        logger.info("Response generator database initialized successfully")

    def _load_writing_style(self, profile_name: str = 'default') -> Dict[str, Any]:
        """
        Load user's writing style profile from database.

        Args:
            profile_name: Name of style profile to load

        Returns:
            Writing style profile dictionary
        """
        profile = self.style_analyzer.load_profile(profile_name)

        if profile:
            logger.info(f"Loaded writing style: greeting={profile['greeting_style']}, "
                       f"closing={profile['closing_style']}, formality={profile['formality_level']}")
            return profile
        else:
            # Use default professional style
            logger.info("Using default writing style (no profile found)")
            return self.style_analyzer._default_style_profile()

    def generate_response(
        self,
        email: Dict[str, Any],
        length: str = 'Standard',
        tone: str = 'Professional',
        template: Optional[str] = None,
        thread_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate email response using LLM.

        This is the main entry point for response generation.

        Args:
            email: Preprocessed email data (from EmailPreprocessor)
            length: Response length: 'Brief'|'Standard'|'Detailed' (default: Standard)
            tone: Response tone: 'Professional'|'Friendly'|'Formal'|'Casual' (default: Professional)
            template: Optional template name from TEMPLATES
            thread_context: Optional list of previous emails in thread (most recent last)

        Returns:
            Generated response dictionary:
            {
                "response_text": "Hi Alice,\n\nYes, I can attend...",
                "length": "Brief",
                "tone": "Professional",
                "template": "Meeting Acceptance",
                "word_count": 42,
                "processing_time_ms": 2847,
                "model_version": "llama3.1:8b-instruct-q4_K_M"
            }

        Raises:
            ResponseGenerationError: If generation fails critically
        """
        start_time = time.time()

        # Validate inputs
        if length not in self.LENGTH_TARGETS:
            logger.warning(f"Invalid length '{length}', using 'Standard'")
            length = 'Standard'

        if tone not in self.TONE_DESCRIPTIONS:
            logger.warning(f"Invalid tone '{tone}', using 'Professional'")
            tone = 'Professional'

        if template and template not in self.TEMPLATES:
            logger.warning(f"Invalid template '{template}', ignoring")
            template = None

        logger.info(f"Generating {length} response with {tone} tone" +
                   (f" using {template} template" if template else ""))

        try:
            # Step 1: Build generation prompt
            prompt = self._build_response_prompt(email, length, tone, template, thread_context)
            logger.debug(f"Prompt built ({len(prompt)} chars)")

            # Step 2: Determine max tokens based on length
            max_tokens = self._calculate_max_tokens(length)

            # Step 3: Generate response with LLM
            logger.info("Calling LLM for response generation...")
            llm_start = time.time()

            response = self.ollama.client.generate(
                model=self.ollama.current_model,
                prompt=prompt,
                options={
                    'temperature': 0.7,  # Higher for creative responses
                    'num_ctx': self.ollama.context_window,
                    'num_predict': max_tokens,
                    'stop': ['---', '\n\n\n']  # Stop patterns
                }
            )

            llm_time = time.time() - llm_start
            logger.info(f"LLM generation completed in {llm_time:.2f}s")

            # Step 4: Clean and format response
            response_text = self._format_response(response['response'])

            # Step 5: Calculate metrics
            processing_time = int((time.time() - start_time) * 1000)
            word_count = len(response_text.split())

            result = {
                'response_text': response_text,
                'length': length,
                'tone': tone,
                'template': template,
                'word_count': word_count,
                'processing_time_ms': processing_time,
                'model_version': self.ollama.current_model
            }

            logger.info(f"Response generated: {word_count} words in {processing_time}ms")

            # Step 6: Store in history (for metrics)
            message_id = email.get('metadata', {}).get('message_id', 'unknown')
            self._log_response_history(message_id, result)

            # Step 7: Log performance metrics
            self._log_performance_metrics(result)

            return result

        except Exception as e:
            logger.error(f"Response generation failed: {e}", exc_info=True)
            raise ResponseGenerationError(f"Failed to generate response: {e}")

    def _build_response_prompt(
        self,
        email: Dict[str, Any],
        length: str,
        tone: str,
        template: Optional[str],
        thread_context: Optional[List[Dict[str, Any]]]
    ) -> str:
        """
        Build LLM prompt for response generation.

        Args:
            email: Preprocessed email data
            length: Response length
            tone: Response tone
            template: Optional template name
            thread_context: Optional thread context

        Returns:
            Formatted prompt string for LLM
        """
        metadata = email.get('metadata', {})
        content = email.get('content', {})

        # Get length target
        length_spec = self.LENGTH_TARGETS[length]
        word_range = f"{length_spec['min']}-{length_spec['max']}"

        # Build thread summary if provided
        thread_summary = ""
        if thread_context:
            thread_summary = self._summarize_thread(thread_context)

        # Get template instructions if specified
        template_instructions = ""
        if template:
            template_instructions = self.TEMPLATES.get(template, '')

        # Build style instructions from user's profile
        style_instructions = self._build_style_instructions()

        # Build tone instructions
        tone_description = self.TONE_DESCRIPTIONS.get(tone, '')

        # Build template section if specified
        template_section = ""
        if template:
            template_section = f"- Template: {template}\n  Instructions: {template_instructions}\n"

        # Build thread section if provided
        thread_section = ""
        if thread_summary:
            thread_section = f"Thread Context (Previous Messages):\n{thread_summary}\n\n"

        prompt = f"""Generate an email response in the user's writing style.

Original Email:
From: {metadata.get('from', 'Unknown')}
Subject: {metadata.get('subject', 'No subject')}
Body:
{content.get('body', '')}

{thread_section}Response Requirements:
- Length: {length} ({word_range} words)
- Tone: {tone} - {tone_description}
{template_section}
User's Writing Style:
{style_instructions}

Generate ONLY the email response body. Do not include:
- Subject line
- Email headers
- Signature block (unless it's the closing phrase)

Match the user's writing style and requested tone.
Address all questions and points from the original email.
Be natural, conversational, and authentic.

Response:
"""

        return prompt

    def _build_style_instructions(self) -> str:
        """
        Build style instructions from user's writing profile.

        Returns:
            Formatted style instructions for LLM prompt
        """
        style = self.writing_style

        # Formality interpretation
        formality_level = style['formality_level']
        if formality_level > 0.7:
            formality_desc = 'Very formal - use structured language, avoid contractions'
        elif formality_level > 0.5:
            formality_desc = 'Somewhat formal - professional but not stiff'
        elif formality_level > 0.3:
            formality_desc = 'Balanced - professional with some warmth'
        else:
            formality_desc = 'Casual - conversational and relaxed'

        instructions = f"""- Greeting: Start with "{style['greeting_style']}"
- Closing: End with "{style['closing_style']}"
- Formality: {formality_desc}
- Average sentence length: {style['avg_sentence_length']} words"""

        # Add common phrases if available
        if style['common_phrases']:
            phrases = ', '.join(f'"{phrase}"' for phrase in style['common_phrases'][:3])
            instructions += f"\n- Common phrases to consider: {phrases}"

        return instructions

    def _summarize_thread(self, thread_context: List[Dict[str, Any]]) -> str:
        """
        Summarize thread context for prompt (limit to last 5 messages).

        Args:
            thread_context: List of previous emails in thread

        Returns:
            Formatted thread summary
        """
        # Limit to last 5 messages for token efficiency
        recent_thread = thread_context[-5:] if len(thread_context) > 5 else thread_context

        summary_lines = []
        for i, msg in enumerate(recent_thread):
            metadata = msg.get('metadata', {})
            content = msg.get('content', {})

            sender = metadata.get('from', 'Unknown')
            body_preview = content.get('body', '')[:150]  # First 150 chars

            summary_lines.append(f"{i+1}. From {sender}: {body_preview}...")

        return '\n'.join(summary_lines)

    def _calculate_max_tokens(self, length: str) -> int:
        """
        Calculate max tokens for LLM based on length.

        Args:
            length: Response length

        Returns:
            Max token count
        """
        # Rough heuristic: ~1.5 tokens per word
        target_words = self.LENGTH_TARGETS[length]['max']
        return int(target_words * 1.5 * 1.3)  # 30% buffer

    def _format_response(self, raw_response: str) -> str:
        """
        Clean and format generated response.

        Args:
            raw_response: Raw LLM response

        Returns:
            Cleaned and formatted response text
        """
        # Remove any markdown artifacts
        response = re.sub(r'```[\s\S]*?```', '', raw_response)

        # Remove leading/trailing whitespace
        response = response.strip()

        # Remove any "Response:" prefix if LLM added it
        response = re.sub(r'^Response:\s*', '', response, flags=re.IGNORECASE)

        # Ensure proper paragraph spacing (max 2 newlines)
        response = re.sub(r'\n{3,}', '\n\n', response)

        # Remove any email signature blocks that LLM might add
        # (signature patterns: "-- " or lines with just contact info)
        response = re.sub(r'\n--\s*\n[\s\S]*$', '', response)

        return response.strip()

    def _log_response_history(self, message_id: str, result: Dict[str, Any]):
        """
        Log response to history table.

        Args:
            message_id: Original email message_id
            result: Response generation result
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO response_history (
                    message_id, response_text, response_length, response_tone,
                    template_used, word_count, processing_time_ms, model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id,
                result['response_text'],
                result['length'],
                result['tone'],
                result.get('template'),
                result['word_count'],
                result['processing_time_ms'],
                result['model_version']
            ))

            conn.commit()
            conn.close()

            logger.debug(f"Response logged to history for message_id={message_id}")

        except Exception as e:
            logger.error(f"Failed to log response history: {e}")

    def _log_performance_metrics(self, result: Dict[str, Any]):
        """
        Log performance metrics to database.

        Args:
            result: Response generation result
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            operation = f'response_generation_{result["length"]}'

            cursor.execute('''
                INSERT INTO performance_metrics (
                    operation, processing_time_ms, model_version
                ) VALUES (?, ?, ?)
            ''', (
                operation,
                result['processing_time_ms'],
                result['model_version']
            ))

            conn.commit()
            conn.close()

            logger.debug(f"Performance logged: {operation}, {result['processing_time_ms']}ms")

        except Exception as e:
            logger.error(f"Failed to log performance: {e}")

    def record_user_feedback(self, response_id: int, edited_text: str,
                           accepted: bool, regeneration_count: int = 0):
        """
        Record user feedback on generated response.

        Args:
            response_id: ID from response_history table
            edited_text: User's edited version of response
            accepted: Whether user accepted the response
            regeneration_count: Number of times user regenerated
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get original response text
            cursor.execute('SELECT response_text FROM response_history WHERE id = ?', (response_id,))
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Response ID {response_id} not found")
                return

            original_text = row[0]

            # Calculate edit percentage
            original_len = len(original_text)
            edited_len = len(edited_text)

            if original_len > 0:
                edit_percentage = abs(edited_len - original_len) / original_len * 100
            else:
                edit_percentage = 0.0

            # Update response_history
            cursor.execute('''
                UPDATE response_history
                SET edit_percentage = ?,
                    accepted = ?,
                    regeneration_count = ?
                WHERE id = ?
            ''', (
                round(edit_percentage, 2),
                1 if accepted else 0,
                regeneration_count,
                response_id
            ))

            conn.commit()
            conn.close()

            logger.info(f"User feedback recorded: edit_percentage={edit_percentage:.1f}%, "
                       f"accepted={accepted}")

            # Also record in style analysis for learning
            self.style_analyzer.record_edit_feedback(original_text, edited_text)

        except Exception as e:
            logger.error(f"Failed to record user feedback: {e}")

    def get_response_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get response generation metrics for time period.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Metrics dictionary with stats
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total responses generated
            cursor.execute('''
                SELECT COUNT(*) FROM response_history
                WHERE generated_date > datetime('now', '-' || ? || ' days')
            ''', (days,))
            total_generated = cursor.fetchone()[0]

            # Breakdown by length
            cursor.execute('''
                SELECT response_length, COUNT(*), AVG(processing_time_ms)
                FROM response_history
                WHERE generated_date > datetime('now', '-' || ? || ' days')
                GROUP BY response_length
            ''', (days,))

            by_length = {}
            for row in cursor.fetchall():
                length, count, avg_time = row
                by_length[length] = {
                    'count': count,
                    'avg_time_ms': round(avg_time, 2) if avg_time else 0
                }

            # Acceptance rate
            cursor.execute('''
                SELECT COUNT(*) FROM response_history
                WHERE accepted = 1
                AND generated_date > datetime('now', '-' || ? || ' days')
            ''', (days,))
            accepted_count = cursor.fetchone()[0]

            acceptance_rate = (accepted_count / total_generated * 100) if total_generated > 0 else 0

            # Average edit percentage
            cursor.execute('''
                SELECT AVG(edit_percentage) FROM response_history
                WHERE edit_percentage IS NOT NULL
                AND generated_date > datetime('now', '-' || ? || ' days')
            ''', (days,))
            avg_edit_pct = cursor.fetchone()[0] or 0

            conn.close()

            return {
                'total_generated': total_generated,
                'by_length': by_length,
                'acceptance_rate_percent': round(acceptance_rate, 2),
                'avg_edit_percentage': round(avg_edit_pct, 2),
                'time_period_days': days
            }

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}


# Convenience function for quick response generation
def generate_response(email: Dict[str, Any], ollama_manager: OllamaManager,
                     length: str = 'Standard', tone: str = 'Professional',
                     db_path: str = 'data/mailmind.db') -> Dict[str, Any]:
    """
    Convenience function to generate a response.

    Args:
        email: Preprocessed email data
        ollama_manager: OllamaManager instance
        length: Response length
        tone: Response tone
        db_path: Path to database file

    Returns:
        Response generation result dictionary
    """
    generator = ResponseGenerator(ollama_manager, db_path=db_path)
    return generator.generate_response(email, length=length, tone=tone)
