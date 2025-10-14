"""
Email Analysis Engine for MailMind

This module provides AI-powered email analysis using local LLM inference.
Implements Story 1.3: Real-Time Analysis Engine (<2s)

Key Features:
- Priority classification (High/Medium/Low with confidence)
- Email summarization (2-3 sentences)
- Topic/tag extraction (up to 5 tags)
- Sentiment analysis (positive/neutral/negative/urgent)
- Action item and deadline extraction
- Result caching in SQLite (<100ms cache hits)
- Batch processing queue (10-15 emails/minute)
- Performance monitoring and metrics

Integration:
- Uses OllamaManager (Story 1.1) for LLM inference
- Uses EmailPreprocessor (Story 1.2) for email preprocessing
- Complete pipeline: Raw Email → Preprocessed → Analysis → Cache
"""

import re
import time
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime
from pathlib import Path

from src.mailmind.core.ollama_manager import OllamaManager
from src.mailmind.core.email_preprocessor import EmailPreprocessor
from mailmind.database import DatabaseManager


logger = logging.getLogger(__name__)


class EmailAnalysisError(Exception):
    """Base exception for email analysis errors."""
    pass


class EmailAnalysisEngine:
    """
    AI-powered email analysis engine.

    Analyzes emails using local LLM to generate:
    - Priority classification (High/Medium/Low)
    - 2-3 sentence summary
    - Up to 5 relevant tags/topics
    - Sentiment (positive/neutral/negative/urgent)
    - Action items with deadlines

    Features:
    - Progressive disclosure (quick priority → summary → full analysis)
    - SQLite caching for instant repeat analyses
    - Batch processing for multiple emails
    - Performance monitoring and metrics

    Performance Targets:
    - Optimal hardware (high-GPU): <1s analysis
    - Recommended hardware (mid-GPU): <2s analysis
    - Minimum hardware (CPU-only): <5s analysis
    - Cache hits: <100ms
    """

    # Quick priority keywords for heuristic
    HIGH_PRIORITY_KEYWORDS = [
        'urgent', 'asap', 'critical', 'emergency', 'immediately',
        'deadline', 'due', 'expires', 'time-sensitive', 'action required'
    ]

    MEDIUM_PRIORITY_KEYWORDS = [
        'meeting', 'schedule', 'review', 'update', 'fyi', 'please'
    ]

    def __init__(self, ollama_manager: OllamaManager, db_path: str = 'data/mailmind.db'):
        """
        Initialize Email Analysis Engine.

        Args:
            ollama_manager: OllamaManager instance for LLM inference
            db_path: Path to SQLite database file
        """
        self.ollama = ollama_manager
        self.preprocessor = EmailPreprocessor()

        # Initialize DatabaseManager (replaces direct SQLite operations)
        self.db = DatabaseManager(db_path=db_path)

        logger.info(f"EmailAnalysisEngine initialized with DatabaseManager: {db_path}")


    def analyze_email(self, raw_email: Any, use_cache: bool = True,
                     force_reanalyze: bool = False) -> Dict[str, Any]:
        """
        Analyze email with LLM and return structured results.

        This is the main entry point for email analysis. It orchestrates:
        1. Email preprocessing
        2. Cache checking
        3. Quick priority heuristic
        4. LLM analysis
        5. Result caching
        6. Performance logging

        Args:
            raw_email: Raw email in any supported format (dict, MIME, Message)
            use_cache: Check cache before running analysis (default: True)
            force_reanalyze: Force re-analysis even if cached (default: False)

        Returns:
            Analysis results dictionary:
            {
                "priority": "High|Medium|Low",
                "confidence": 0.92,
                "summary": "...",
                "tags": ["tag1", "tag2"],
                "sentiment": "positive|neutral|negative|urgent",
                "action_items": ["Action 1", "Action 2"],
                "processing_time_ms": 1847,
                "tokens_per_second": 52.3,
                "model_version": "llama3.1:8b-instruct-q4_K_M",
                "cache_hit": false
            }

        Raises:
            EmailAnalysisError: If analysis fails critically
        """
        start_time = time.time()

        try:
            # Step 1: Preprocess email
            logger.debug("Preprocessing email...")
            preprocessed = self.preprocessor.preprocess_email(raw_email)
            message_id = preprocessed['metadata']['message_id']

            logger.debug(f"Email preprocessed: message_id={message_id}")

            # Step 2: Check cache (unless force_reanalyze)
            if use_cache and not force_reanalyze:
                cached = self._get_cached_analysis(message_id)
                if cached:
                    logger.info(f"Cache hit for message_id={message_id}")
                    cached['cache_hit'] = True
                    cached['processing_time_ms'] = int((time.time() - start_time) * 1000)
                    return cached

            logger.debug("Cache miss, proceeding with LLM analysis")

            # Step 3: Quick priority heuristic (for progressive disclosure)
            quick_priority = self._quick_priority_heuristic(preprocessed)
            logger.debug(f"Quick priority: {quick_priority}")

            # Step 4: Build LLM prompt
            prompt = self._build_analysis_prompt(preprocessed)
            logger.debug(f"Prompt built ({len(prompt)} chars)")

            # Step 5: Generate analysis with LLM
            logger.info("Calling LLM for analysis...")
            llm_start = time.time()

            response = self.ollama.client.generate(
                model=self.ollama.current_model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'num_ctx': self.ollama.context_window,
                    'num_predict': 500,  # Max tokens for analysis
                    'stop': ['}']  # Stop at end of JSON
                }
            )

            llm_time = time.time() - llm_start
            logger.info(f"LLM analysis completed in {llm_time:.2f}s")

            # Step 6: Parse LLM response
            analysis = self._parse_analysis_response(response['response'])

            # Step 7: Add metadata
            processing_time = int((time.time() - start_time) * 1000)
            analysis['processing_time_ms'] = processing_time
            analysis['tokens_per_second'] = self._calculate_tokens_per_sec(response)
            analysis['model_version'] = self.ollama.current_model
            analysis['cache_hit'] = False

            # Use LLM priority, but fallback to quick heuristic if confidence is low
            if analysis.get('confidence', 0) < 0.5:
                logger.warning("Low confidence, using quick priority heuristic")
                analysis['priority'] = quick_priority
                analysis['confidence'] = 0.5

            logger.info(f"Analysis complete: priority={analysis['priority']}, "
                       f"confidence={analysis['confidence']:.2f}, "
                       f"time={processing_time}ms")

            # Step 8: Cache results
            self._cache_analysis(message_id, preprocessed, analysis)

            # Step 9: Log performance
            self._log_performance(analysis, operation='email_analysis')

            return analysis

        except Exception as e:
            logger.error(f"Email analysis failed: {e}", exc_info=True)
            # Return default analysis rather than failing completely
            return self._default_analysis(str(e))

    def _quick_priority_heuristic(self, email: Dict[str, Any]) -> str:
        """
        Fast priority classification without LLM (<100ms).

        Uses keyword matching and simple rules for instant feedback
        during progressive disclosure.

        Args:
            email: Preprocessed email data

        Returns:
            Priority string: "High", "Medium", or "Low"
        """
        body = email['content']['body'].lower()
        subject = email['metadata']['subject'].lower()
        combined = f"{subject} {body}"

        # High priority indicators
        for keyword in self.HIGH_PRIORITY_KEYWORDS:
            if keyword in combined:
                logger.debug(f"High priority keyword found: {keyword}")
                return 'High'

        # Check for deadlines in text
        deadline_patterns = [
            r'by\s+(today|tomorrow|eod|end of day|friday)',
            r'due\s+(today|tomorrow|this week)',
            r'deadline.*\d{1,2}[/-]\d{1,2}'
        ]

        for pattern in deadline_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                logger.debug(f"Deadline pattern found: {pattern}")
                return 'High'

        # Medium priority for replies in important threads
        if email['thread_context']['is_reply']:
            thread_length = email['thread_context'].get('thread_length', 1)
            if thread_length > 2:
                logger.debug("Part of active thread (>2 messages)")
                return 'Medium'

        # Medium priority indicators
        for keyword in self.MEDIUM_PRIORITY_KEYWORDS:
            if keyword in combined:
                logger.debug(f"Medium priority keyword found: {keyword}")
                return 'Medium'

        # Default to Low priority
        logger.debug("No priority indicators found, defaulting to Low")
        return 'Low'

    def _build_analysis_prompt(self, email: Dict[str, Any]) -> str:
        """
        Build LLM prompt from preprocessed email.

        Creates a structured prompt that asks the LLM to return JSON
        with all required analysis fields.

        Args:
            email: Preprocessed email data

        Returns:
            Prompt string for LLM
        """
        metadata = email['metadata']
        content = email['content']
        thread_context = email['thread_context']

        # Build context about thread
        thread_info = ""
        if thread_context['is_reply']:
            thread_info = f"\nThis is a reply in an email thread (message #{thread_context['thread_length']})."

        # Build attachments info
        attachments_info = ""
        if content['has_attachments']:
            attachments_list = ', '.join(content['attachments'])
            attachments_info = f"\nAttachments: {attachments_list}"

        prompt = f"""Analyze this email and provide structured output in JSON format.

Email Metadata:
From: {metadata['from']}
Subject: {metadata['subject']}
Date: {metadata['date']}{thread_info}{attachments_info}

Email Body:
{content['body']}

Provide analysis as valid JSON with these exact fields:
{{
  "priority": "High|Medium|Low",
  "confidence": 0.92,
  "summary": "2-3 sentence summary capturing key points and main purpose",
  "tags": ["tag1", "tag2", "tag3"],
  "sentiment": "positive|neutral|negative|urgent",
  "action_items": ["Action 1 with deadline", "Action 2"]
}}

Guidelines:
- Priority: High for urgent/time-sensitive, Medium for standard, Low for FYI
- Confidence: 0.0-1.0, higher for clear priority signals
- Summary: Concise, preserve key details (names, dates, amounts)
- Tags: Up to 5 relevant topics (lowercase, 1-3 words each)
- Sentiment: urgent if time-sensitive, otherwise positive/neutral/negative
- Action items: Extract clear actions with deadlines, or empty array if none

Return ONLY the JSON object, no additional text:"""

        return prompt

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM JSON response into structured analysis.

        Handles various response formats and provides fallback parsing
        if JSON is malformed.

        Args:
            response: LLM response text (should contain JSON)

        Returns:
            Parsed analysis dictionary
        """
        try:
            # Try to extract JSON from response
            # Handle markdown code blocks: ```json ... ```
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.warning("No JSON found in response, using fallback parsing")
                    return self._fallback_parse(response)

            # Parse JSON
            analysis = json.loads(json_str)

            # Validate and normalize fields
            analysis['priority'] = analysis.get('priority', 'Medium')
            analysis['confidence'] = float(analysis.get('confidence', 0.5))
            analysis['summary'] = analysis.get('summary', 'No summary available')
            analysis['tags'] = analysis.get('tags', [])[:5]  # Limit to 5 tags
            analysis['sentiment'] = analysis.get('sentiment', 'neutral')
            analysis['action_items'] = analysis.get('action_items', [])[:5]  # Limit to 5 actions

            # Validate priority values
            if analysis['priority'] not in ['High', 'Medium', 'Low']:
                logger.warning(f"Invalid priority: {analysis['priority']}, defaulting to Medium")
                analysis['priority'] = 'Medium'

            # Validate sentiment values
            if analysis['sentiment'] not in ['positive', 'neutral', 'negative', 'urgent']:
                logger.warning(f"Invalid sentiment: {analysis['sentiment']}, defaulting to neutral")
                analysis['sentiment'] = 'neutral'

            # Ensure tags are strings and normalized
            analysis['tags'] = [str(tag).lower().strip() for tag in analysis['tags']]

            # Ensure action items are strings
            analysis['action_items'] = [str(item).strip() for item in analysis['action_items']]

            logger.debug("Successfully parsed LLM response")
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.debug(f"Response was: {response[:200]}...")
            return self._fallback_parse(response)

        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}", exc_info=True)
            return self._default_analysis("Parsing error")

    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """
        Fallback parsing when JSON extraction fails.

        Uses simple heuristics to extract information from free-form text.

        Args:
            response: LLM response text

        Returns:
            Best-effort analysis dictionary
        """
        logger.warning("Using fallback parsing for malformed response")

        analysis = self._default_analysis("Fallback parsing")

        # Try to extract priority
        response_lower = response.lower()
        if 'high' in response_lower:
            analysis['priority'] = 'High'
        elif 'low' in response_lower:
            analysis['priority'] = 'Low'
        else:
            analysis['priority'] = 'Medium'

        # Try to extract summary (first few sentences)
        sentences = re.split(r'[.!?]+', response)
        if len(sentences) >= 2:
            analysis['summary'] = '. '.join(sentences[:2]).strip() + '.'

        # Try to extract tags (look for comma-separated words)
        tags_match = re.search(r'tags?:?\s*([a-z0-9,\s-]+)', response_lower)
        if tags_match:
            tags = [t.strip() for t in tags_match.group(1).split(',')]
            analysis['tags'] = tags[:5]

        return analysis

    def _default_analysis(self, reason: str = "Unknown") -> Dict[str, Any]:
        """
        Return default analysis when parsing fails or error occurs.

        Args:
            reason: Reason for using default analysis

        Returns:
            Default analysis dictionary
        """
        logger.warning(f"Returning default analysis: {reason}")

        return {
            'priority': 'Medium',
            'confidence': 0.3,
            'summary': 'Unable to analyze email content automatically.',
            'tags': [],
            'sentiment': 'neutral',
            'action_items': [],
            'processing_time_ms': 0,
            'tokens_per_second': 0.0,
            'model_version': self.ollama.current_model,
            'cache_hit': False,
            'error': reason
        }

    def _get_cached_analysis(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Check cache for existing analysis using DatabaseManager.

        Args:
            message_id: Unique message identifier

        Returns:
            Cached analysis dictionary or None if not found
        """
        try:
            cached_result = self.db.get_email_analysis(message_id)

            if cached_result:
                # Check if model version matches (invalidate cache if changed)
                cached_model = cached_result.get('model_version')
                if cached_model != self.ollama.current_model:
                    logger.info(f"Cache invalidated due to model change: {cached_model} → {self.ollama.current_model}")
                    return None

                # Extract analysis from cached result
                analysis = cached_result.get('analysis', {})
                logger.debug(f"Cache hit for message_id={message_id}")
                return analysis

            return None

        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            return None

    def _cache_analysis(self, message_id: str, email: Dict[str, Any],
                       analysis: Dict[str, Any]):
        """
        Store analysis results in cache using DatabaseManager.

        Args:
            message_id: Unique message identifier
            email: Preprocessed email data
            analysis: Analysis results
        """
        try:
            metadata = email['metadata']

            # Insert using DatabaseManager
            self.db.insert_email_analysis(
                message_id=message_id,
                analysis=analysis,
                metadata={
                    'subject': metadata['subject'],
                    'sender': metadata['from'],
                    'received_date': metadata['date'],
                    'model_version': analysis['model_version'],
                    'processing_time_ms': analysis['processing_time_ms'],
                    'tokens_per_second': analysis.get('tokens_per_second', 0.0)
                }
            )

            logger.debug(f"Analysis cached for message_id={message_id}")

        except Exception as e:
            logger.error(f"Failed to cache analysis: {e}")

    def _calculate_tokens_per_sec(self, response: Dict[str, Any]) -> float:
        """
        Calculate tokens per second from LLM response.

        Args:
            response: Ollama generate response dictionary

        Returns:
            Tokens per second (float)
        """
        try:
            # Ollama returns total_duration and eval_count
            if 'total_duration' in response and 'eval_count' in response:
                total_duration_s = response['total_duration'] / 1e9  # nanoseconds to seconds
                eval_count = response['eval_count']

                if total_duration_s > 0:
                    tokens_per_sec = eval_count / total_duration_s
                    return round(tokens_per_sec, 2)

            return 0.0

        except Exception as e:
            logger.debug(f"Could not calculate tokens/sec: {e}")
            return 0.0

    def _log_performance(self, analysis: Dict[str, Any], operation: str = 'email_analysis',
                        batch_size: int = 1):
        """
        Log performance metrics to database using DatabaseManager.

        Args:
            analysis: Analysis results with performance data
            operation: Operation name (e.g., 'email_analysis', 'batch_processing')
            batch_size: Number of emails processed (for batch operations)
        """
        try:
            metrics = {
                'processing_time_ms': analysis.get('processing_time_ms', 0),
                'tokens_per_second': analysis.get('tokens_per_second', 0.0),
                'model_version': analysis.get('model_version', 'unknown'),
                'batch_size': batch_size
            }
            self.db.insert_performance_metric(operation=operation, metrics=metrics)

            logger.debug(f"Performance logged: {operation}, {analysis.get('processing_time_ms', 0)}ms")

        except Exception as e:
            logger.error(f"Failed to log performance: {e}")

    def analyze_batch(self, emails: List[Any],
                     callback: Optional[Callable[[int, int, Dict], None]] = None) -> List[Dict[str, Any]]:
        """
        Analyze multiple emails in batch.

        Processes emails sequentially to avoid GPU thrashing and provides
        progress updates via callback.

        Args:
            emails: List of raw emails
            callback: Optional progress callback(current, total, result)
                     Called after each email is analyzed

        Returns:
            List of analysis results (same order as input emails)

        Example:
            def progress(current, total, result):
                print(f"Analyzed {current}/{total}: {result['priority']}")

            results = engine.analyze_batch(emails, callback=progress)
        """
        logger.info(f"Starting batch analysis of {len(emails)} emails")
        batch_start = time.time()

        results = []
        total = len(emails)

        for i, email in enumerate(emails):
            try:
                result = self.analyze_email(email)
                results.append(result)

                # Call progress callback if provided
                if callback:
                    callback(i + 1, total, result)

                logger.debug(f"Batch progress: {i+1}/{total} ({(i+1)/total*100:.1f}%)")

            except Exception as e:
                logger.error(f"Failed to analyze email {i+1}/{total}: {e}")
                # Add error result but continue processing
                results.append(self._default_analysis(f"Batch processing error: {str(e)}"))

        batch_time = time.time() - batch_start
        emails_per_min = (total / batch_time) * 60 if batch_time > 0 else 0

        logger.info(f"Batch analysis complete: {total} emails in {batch_time:.1f}s "
                   f"({emails_per_min:.1f} emails/min)")

        # Log batch performance
        if results:
            avg_analysis = {
                'processing_time_ms': int(batch_time * 1000),
                'tokens_per_second': sum(r.get('tokens_per_second', 0) for r in results) / len(results),
                'model_version': results[0].get('model_version', 'unknown')
            }
            self._log_performance(avg_analysis, operation='batch_processing', batch_size=total)

        return results

    def get_analysis_stats(self) -> Dict[str, Any]:
        """
        Get analysis statistics from database using DatabaseManager.

        Returns:
            Statistics dictionary with counts, averages, etc.
        """
        try:
            # Get counts by priority
            high_count = len(self.db.get_emails_by_priority('High'))
            medium_count = len(self.db.get_emails_by_priority('Medium'))
            low_count = len(self.db.get_emails_by_priority('Low'))
            total_analyses = high_count + medium_count + low_count

            priority_dist = {
                'High': high_count,
                'Medium': medium_count,
                'Low': low_count
            }

            # Get performance metrics (last 365 days)
            metrics = self.db.get_performance_metrics(days=365, operation='email_analysis')

            # Calculate averages from metrics
            avg_processing_time = 0
            avg_tokens_per_sec = 0
            if metrics:
                avg_processing_time = sum(m['processing_time_ms'] for m in metrics) / len(metrics)
                tokens_metrics = [m['tokens_per_second'] for m in metrics if m.get('tokens_per_second', 0) > 0]
                if tokens_metrics:
                    avg_tokens_per_sec = sum(tokens_metrics) / len(tokens_metrics)

            return {
                'total_analyses': total_analyses,
                'priority_distribution': priority_dist,
                'avg_processing_time_ms': round(avg_processing_time, 2),
                'avg_tokens_per_second': round(avg_tokens_per_sec, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Convenience function for quick analysis
def analyze_email(raw_email: Any, ollama_manager: OllamaManager,
                 db_path: str = 'data/mailmind.db') -> Dict[str, Any]:
    """
    Convenience function to analyze a single email.

    Args:
        raw_email: Raw email in any supported format
        ollama_manager: OllamaManager instance
        db_path: Path to database file

    Returns:
        Analysis results dictionary
    """
    engine = EmailAnalysisEngine(ollama_manager, db_path=db_path)
    return engine.analyze_email(raw_email)
