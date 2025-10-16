"""
Email Preprocessing Pipeline for MailMind

This module transforms raw emails into optimized format for LLM analysis.
Implements Story 1.2: Email Preprocessing Pipeline

Key Features:
- Email metadata extraction (sender, subject, date, thread context)
- HTML to plain text conversion with structure preserved
- Attachment handling (list files without content processing)
- Signature and quote stripping using heuristics
- Smart content truncation for emails >10k characters
- Structured JSON format for LLM consumption
- Thread context preservation
- Input sanitization to prevent prompt injection

Performance Target: <200ms preprocessing time
"""

import re
import time
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from email.parser import Parser
from email.message import Message

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Import centralized exceptions (Story 2.6, Story 3.2)
from mailmind.core.exceptions import EmailPreprocessorError, HTMLParsingError, SecurityException
from mailmind.core.security_logger import get_security_logger


logger = logging.getLogger(__name__)


# Email signature detection patterns
SIGNATURE_PATTERNS = [
    r'^--\s*$',  # Standard email signature delimiter
    r'^_{10,}',  # Underscores (10 or more)
    r'^={10,}',  # Equals signs
    r'Sent from my (iPhone|iPad|Android|BlackBerry)',
    r'Get Outlook for (iOS|Android)',
    r'\b(Best regards|Sincerely|Thanks|Cheers|Regards|Kind regards|Warm regards|Cordially),?\s*$',
    r'\b(Phone|Tel|Mobile|Cell|Office):',
    r'\bwww\.[a-z0-9-]+\.(com|net|org|io|co)',
    r'CONFIDENTIALITY NOTICE',
    r'DISCLAIMER:',
    r'This email and any attachments',
]

# Quote detection patterns
QUOTE_PATTERNS = [
    r'^On .+ wrote:$',  # Gmail style: "On Mon, Oct 13, 2025 at 2:30 PM, Alice wrote:"
    r'^From:.+Sent:.+To:.+Subject:',  # Outlook style headers
    r'^>',  # Traditional quote marker
    r'^\|',  # Pipe-style quote marker
    r'^>{2,}',  # Multiple quote markers (nested quotes)
]

# Suspicious content patterns for prompt injection detection
SUSPICIOUS_PATTERNS = [
    r'ignore\s+(previous|all|prior)\s+instructions',
    r'disregard\s+(previous|all|prior)',
    r'system\s*:',
    r'you\s+are\s+now',
    r'act\s+as\s+(if|though)',
    r'pretend\s+(to\s+be|that)',
    r'<\|im_start\|>',  # ChatML injection
    r'<\|im_end\|>',
]


class EmailPreprocessor:
    """
    Preprocesses raw emails into optimized format for LLM analysis.

    This class handles all email preprocessing tasks including metadata extraction,
    HTML parsing, signature/quote stripping, content truncation, and security sanitization.

    Attributes:
        signature_patterns: Compiled regex patterns for signature detection
        quote_patterns: Compiled regex patterns for quote detection
        suspicious_patterns: Compiled regex patterns for security checks
        warnings: List of warnings generated during preprocessing
        security_level: Security level for prompt injection blocking ("Strict", "Normal", "Permissive")
    """

    def __init__(self, security_level: str = "Normal", security_patterns_path: str = None):
        """
        Initialize EmailPreprocessor with compiled regex patterns and security settings.

        Story 3.2 AC5: Configurable Security Levels

        Args:
            security_level: Security level for blocking suspicious emails
                - "Strict": Block ALL suspicious patterns (high/medium/low severity)
                - "Normal": Block high/medium severity, warn on low severity (default)
                - "Permissive": Warn on all patterns, allow processing
            security_patterns_path: Path to security_patterns.yaml (optional, auto-discovered)
        """
        # Validate security level
        valid_levels = ["Strict", "Normal", "Permissive"]
        if security_level not in valid_levels:
            logger.warning(f"Invalid security_level '{security_level}', defaulting to 'Normal'")
            security_level = "Normal"

        self.security_level = security_level
        self.security_patterns_path = security_patterns_path

        # Compile regex patterns
        self.signature_patterns = [re.compile(p, re.MULTILINE | re.IGNORECASE)
                                   for p in SIGNATURE_PATTERNS]
        self.quote_patterns = [re.compile(p, re.MULTILINE | re.IGNORECASE)
                              for p in QUOTE_PATTERNS]

        # Load security patterns (will be enhanced in Task 3 with YAML loading)
        # For now, use default patterns with severity metadata
        self.suspicious_patterns = self._load_security_patterns()

        self.warnings: List[str] = []

        # Initialize security logger for event logging (Story 3.2 AC3)
        self.security_logger = get_security_logger()

        logger.info(f"EmailPreprocessor initialized with security_level='{security_level}'")

    def preprocess_email(self, raw_email: Any, max_chars: int = 10000) -> Dict[str, Any]:
        """
        Preprocess raw email into structured format for LLM.

        This is the main entry point for email preprocessing. It orchestrates all
        preprocessing steps and returns a structured dictionary ready for LLM consumption.

        Args:
            raw_email: Raw email message (can be MIME string, dict, or email.message.Message)
            max_chars: Maximum characters before truncation (default: 10000)

        Returns:
            Dictionary with preprocessed email data:
            {
                "metadata": {...},
                "content": {...},
                "thread_context": {...},
                "preprocessing_metadata": {...}
            }

        Raises:
            EmailPreprocessorError: If preprocessing fails critically
        """
        start_time = time.time()
        self.warnings = []  # Reset warnings for each email

        try:
            # Step 1: Extract metadata
            metadata = self.extract_metadata(raw_email)

            # Step 2: Parse body (HTML → plain text if needed)
            body = self.parse_body(raw_email)

            # Step 3: Strip signatures and quotes
            body = self.strip_signatures(body)
            body = self.strip_quotes(body)

            # Step 4: Handle attachments
            attachments = self.extract_attachments(raw_email)

            # Step 5: Truncate if needed
            body, was_truncated = self.smart_truncate(body, max_chars=max_chars)

            # Step 6: Sanitize input for security (pass metadata for logging)
            body = self.sanitize_content(body, email_metadata=metadata)

            # Step 7: Build thread context
            thread_context = self.build_thread_context(metadata)

            preprocessing_time = time.time() - start_time

            result = {
                "metadata": metadata,
                "content": {
                    "body": body,
                    "has_attachments": len(attachments) > 0,
                    "attachments": attachments,
                    "char_count": len(body),
                    "was_truncated": was_truncated
                },
                "thread_context": thread_context,
                "preprocessing_metadata": {
                    "processing_time_ms": int(preprocessing_time * 1000),
                    "warnings": self.warnings.copy()
                }
            }

            logger.info(f"Email preprocessed in {preprocessing_time*1000:.0f}ms "
                       f"({len(body)} chars, {len(attachments)} attachments)")

            return result

        except SecurityException:
            # Re-raise SecurityException without wrapping (AC1, AC2)
            # This allows EmailAnalysisEngine to handle security blocks specifically
            raise
        except Exception as e:
            logger.error(f"Email preprocessing failed: {e}", exc_info=True)
            raise EmailPreprocessorError(f"Failed to preprocess email: {str(e)}") from e

    def extract_metadata(self, raw_email: Any) -> Dict[str, Any]:
        """
        Extract email metadata (sender, subject, date, message ID, thread info).

        Handles multiple input formats:
        - email.message.Message objects
        - Dictionary with email fields
        - MIME string (parsed to Message)

        Args:
            raw_email: Raw email in supported format

        Returns:
            Dictionary with metadata fields:
            {
                "from": "sender@example.com (Sender Name)",
                "subject": "Email subject",
                "date": "2025-10-13T14:30:00Z",
                "message_id": "abc123...",
                "thread_id": "thread_xyz" or None,
                "in_reply_to": "msg_def456" or None,
                "references": ["msg1", "msg2"] or []
            }
        """
        try:
            # Convert to email.message.Message if needed
            if isinstance(raw_email, str):
                msg = Parser().parsestr(raw_email)
            elif isinstance(raw_email, dict):
                # Create Message from dict
                msg = self._dict_to_message(raw_email)
            elif isinstance(raw_email, Message):
                msg = raw_email
            else:
                logger.warning(f"Unknown email format: {type(raw_email)}")
                return self._get_default_metadata()

            # Extract sender (from field)
            from_field = msg.get('From', 'unknown@unknown.com')

            # Extract subject and decode MIME encoding if needed
            subject = msg.get('Subject', '(No Subject)')
            if hasattr(subject, 'encode'):
                # Already decoded by parser
                subject = str(subject)

            # Extract and parse date
            date_field = msg.get('Date', '')
            date_iso = self._parse_date(date_field)

            # Extract message ID
            message_id = msg.get('Message-ID', f"generated_{int(time.time())}")

            # Extract thread information
            in_reply_to = msg.get('In-Reply-To', None)
            references = msg.get('References', '')
            references_list = references.split() if references else []

            # Thread ID is typically the first message ID in references, or in_reply_to
            thread_id = None
            if references_list:
                thread_id = references_list[0]
            elif in_reply_to:
                thread_id = in_reply_to

            metadata = {
                "from": from_field,
                "subject": subject,
                "date": date_iso,
                "message_id": message_id,
                "thread_id": thread_id,
                "in_reply_to": in_reply_to,
                "references": references_list
            }

            logger.debug(f"Extracted metadata: from={from_field}, subject={subject}")

            return metadata

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            self.warnings.append(f"Metadata extraction error: {str(e)}")
            return self._get_default_metadata()

    def parse_body(self, raw_email: Any) -> str:
        """
        Parse email body and convert HTML to plain text if needed.

        Handles both plain text and HTML emails. For HTML emails, uses BeautifulSoup
        to convert to clean plain text while preserving structure.

        Args:
            raw_email: Raw email in supported format

        Returns:
            Clean plain text body
        """
        try:
            # Convert to Message if needed
            if isinstance(raw_email, str):
                msg = Parser().parsestr(raw_email)
            elif isinstance(raw_email, dict):
                # Direct dict access
                body = raw_email.get('body', raw_email.get('Body', ''))
                body_html = raw_email.get('body_html', raw_email.get('HTMLBody', ''))

                # Prefer HTML if available
                if body_html:
                    return self.parse_html(body_html)
                return str(body)
            elif isinstance(raw_email, Message):
                msg = raw_email
            else:
                logger.warning(f"Unknown email format for body parsing: {type(raw_email)}")
                return ""

            # Extract body from Message object
            if msg.is_multipart():
                # Handle multipart messages
                body = ""
                html_body = ""

                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif content_type == 'text/html':
                        html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')

                # Prefer HTML conversion over plain text
                if html_body:
                    return self.parse_html(html_body)
                return body
            else:
                # Single part message
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)

                if payload:
                    body = payload.decode('utf-8', errors='ignore')
                else:
                    body = str(msg.get_payload())

                if content_type == 'text/html':
                    return self.parse_html(body)
                return body

        except Exception as e:
            logger.error(f"Body parsing failed: {e}")
            self.warnings.append(f"Body parsing error: {str(e)}")
            return ""

    def parse_html(self, html_content: str) -> str:
        """
        Convert HTML email to clean plain text with structure preserved.

        Uses BeautifulSoup to parse HTML and extract text while:
        - Preserving paragraph structure (double newlines)
        - Converting links to "text (URL)" format
        - Noting inline images as "[Image: filename.jpg]"
        - Removing scripts, styles, and tracking pixels

        Args:
            html_content: HTML email content

        Returns:
            Clean plain text with structure preserved

        Raises:
            HTMLParsingError: If BeautifulSoup is not available or parsing fails
        """
        if not BS4_AVAILABLE:
            raise HTMLParsingError("BeautifulSoup4 not available. Install with: pip install beautifulsoup4 lxml")

        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # Remove scripts, styles, and tracking pixels
            for tag in soup(['script', 'style', 'meta', 'link']):
                tag.decompose()

            # Remove 1x1 tracking images
            for img in soup.find_all('img'):
                width = img.get('width', '')
                height = img.get('height', '')
                if width == '1' or height == '1':
                    img.decompose()
                else:
                    # Replace image with placeholder
                    alt_text = img.get('alt', 'image')
                    src = img.get('src', '')
                    filename = src.split('/')[-1] if src else 'unknown'
                    img.replace_with(f"[Image: {filename}]")

            # Convert links to readable format
            for link in soup.find_all('a'):
                link_text = link.get_text().strip()
                link_url = link.get('href', '')
                if link_url and link_url != link_text:
                    link.replace_with(f"{link_text} ({link_url})")
                elif link_text:
                    link.replace_with(link_text)

            # Get text with structure preserved
            text = soup.get_text(separator='\n')

            # Clean up whitespace
            lines = []
            for line in text.split('\n'):
                line = line.strip()
                if line:
                    lines.append(line)

            # Join with double newlines for paragraph structure
            text = '\n\n'.join(lines)

            # Reduce multiple newlines
            text = re.sub(r'\n{3,}', '\n\n', text)

            logger.debug(f"HTML parsed to {len(text)} chars")

            return text.strip()

        except Exception as e:
            logger.error(f"HTML parsing failed: {e}")
            self.warnings.append(f"HTML parsing failed, using raw content: {str(e)}")
            # Fallback: return raw HTML with tags stripped
            return re.sub(r'<[^>]+>', ' ', html_content)

    def extract_attachments(self, raw_email: Any) -> List[str]:
        """
        Extract attachment metadata (filename and size).

        Does NOT process attachment content, only lists files with sizes.

        Args:
            raw_email: Raw email in supported format

        Returns:
            List of attachment strings: ["report.pdf (2.3MB)", "image.png (450KB)"]
        """
        attachments = []

        try:
            if isinstance(raw_email, dict):
                # Handle dict format (from Outlook COM)
                if 'attachments' in raw_email:
                    atts = raw_email['attachments']
                    if isinstance(atts, list):
                        for att in atts:
                            if isinstance(att, dict):
                                name = att.get('filename', att.get('FileName', 'unknown'))
                                size = att.get('size', att.get('Size', 0))
                                attachments.append(self._format_attachment(name, size))
                            else:
                                attachments.append(str(att))
                return attachments

            elif isinstance(raw_email, str):
                msg = Parser().parsestr(raw_email)
            elif isinstance(raw_email, Message):
                msg = raw_email
            else:
                return []

            # Extract from Message object
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if filename:
                    # Get size from payload
                    payload = part.get_payload(decode=True)
                    size = len(payload) if payload else 0
                    attachments.append(self._format_attachment(filename, size))

            if attachments:
                logger.debug(f"Found {len(attachments)} attachments")

            # Check for potentially malicious attachments
            for att in attachments:
                if any(ext in att.lower() for ext in ['.exe', '.scr', '.bat', '.cmd', '.vbs', '.js']):
                    self.warnings.append(f"Potentially dangerous attachment detected: {att}")

            return attachments

        except Exception as e:
            logger.error(f"Attachment extraction failed: {e}")
            self.warnings.append(f"Attachment extraction error: {str(e)}")
            return []

    def strip_signatures(self, body: str) -> str:
        """
        Remove email signatures using heuristic pattern matching.

        Detects common signature delimiters and patterns, then removes everything
        after the signature start.

        Args:
            body: Email body text

        Returns:
            Body with signature removed
        """
        if not body:
            return body

        lines = body.split('\n')
        signature_start = None

        # Find signature start
        for i, line in enumerate(lines):
            # Check if line matches any signature pattern
            for pattern in self.signature_patterns:
                if pattern.search(line):
                    signature_start = i
                    break

            if signature_start is not None:
                break

        if signature_start is not None:
            # Keep content before signature
            result = '\n'.join(lines[:signature_start]).strip()
            logger.debug(f"Stripped signature at line {signature_start}")
            return result

        return body

    def strip_quotes(self, body: str) -> str:
        """
        Remove quoted replies intelligently while preserving context.

        Detects quoted text using common patterns (>, |, "On X wrote:", etc.)
        and removes them. Preserves first 2-3 lines of quoted text if relevant.

        Args:
            body: Email body text

        Returns:
            Body with quoted replies removed
        """
        if not body:
            return body

        lines = body.split('\n')
        quote_start = None

        # Find where quotes begin
        for i, line in enumerate(lines):
            # Check if line matches any quote pattern
            for pattern in self.quote_patterns:
                if pattern.search(line):
                    quote_start = i
                    break

            if quote_start is not None:
                break

        if quote_start is not None:
            # Keep content before quotes
            # Optionally keep first 2-3 lines of quote for context
            kept_quote_lines = min(2, len(lines) - quote_start)
            result_lines = lines[:quote_start]

            if kept_quote_lines > 0:
                result_lines.append("\n[Previous message context:]")
                result_lines.extend(lines[quote_start:quote_start + kept_quote_lines])

            result = '\n'.join(result_lines).strip()
            logger.debug(f"Stripped quotes starting at line {quote_start}")
            return result

        return body

    def smart_truncate(self, body: str, max_chars: int = 10000) -> Tuple[str, bool]:
        """
        Intelligently truncate long emails to fit within token limits.

        Strategy:
        - Keep first 8000 chars (primary content)
        - Keep last 1000 chars (conclusion/signature context)
        - End on sentence boundary when possible
        - Note truncation in output

        Args:
            body: Email body text
            max_chars: Maximum characters before truncation

        Returns:
            Tuple of (truncated_body, was_truncated)
        """
        if len(body) <= max_chars:
            return body, False

        # Keep first 80% and last 10% of max_chars
        first_part_len = int(max_chars * 0.8)
        last_part_len = int(max_chars * 0.1)

        first_part = body[:first_part_len]
        last_part = body[-last_part_len:]

        # Try to end on sentence boundary
        first_part = self._truncate_to_sentence(first_part)

        truncated_body = (
            f"{first_part}\n\n"
            f"[... Content truncated: {len(body)} chars → {len(first_part) + len(last_part)} chars ...]\n\n"
            f"{last_part}"
        )

        logger.debug(f"Truncated email from {len(body)} to {len(truncated_body)} chars")

        return truncated_body, True

    def sanitize_content(self, body: str, email_metadata: Dict[str, Any] = None) -> str:
        """
        Sanitize email content to prevent prompt injection attacks.

        Story 3.2 AC1: Block Injection Patterns
        Story 3.2 AC2: Safe Error Response
        Story 3.2 AC3: Security Event Logging

        This method:
        1. Removes control characters
        2. Detects suspicious patterns based on security_level
        3. Blocks or warns based on security_level and pattern severity
        4. Logs all security events to security.log
        5. Raises SecurityException when blocking criteria met

        Args:
            body: Email body text
            email_metadata: Email metadata dict (for logging) - optional

        Returns:
            Sanitized body text (if allowed to proceed)

        Raises:
            SecurityException: When email is blocked for security reasons
        """
        if not body:
            return body

        # Default metadata if not provided
        if email_metadata is None:
            email_metadata = {
                "subject": "(Unknown)",
                "from": "unknown",
                "message_id": "unknown"
            }

        # Remove control characters (except newlines and tabs)
        sanitized = ''.join(char for char in body
                          if char.isprintable() or char in '\n\t')

        # Check for suspicious patterns based on security_level
        for pattern_dict in self.suspicious_patterns:
            pattern = pattern_dict["regex"]
            pattern_name = pattern_dict["name"]
            severity = pattern_dict["severity"]
            description = pattern_dict["description"]

            if pattern.search(sanitized):
                # Get preview of matched content (first 200 chars)
                email_preview = sanitized[:200] if len(sanitized) > 200 else sanitized

                # Blocking logic based on security_level (AC1, AC5)
                if self.security_level == "Strict":
                    # Strict mode: Block ALL suspicious patterns
                    logger.warning(
                        f"[BLOCKED] Security pattern matched in Strict mode: {pattern_name} "
                        f"(severity: {severity}, description: {description})"
                    )

                    # Log security event (AC3)
                    self.security_logger.log_event(
                        event_type="blocked",
                        pattern_name=pattern_name,
                        email_metadata=email_metadata,
                        action_taken="blocked_email",
                        severity=severity
                    )

                    raise SecurityException(
                        pattern_name=pattern_name,
                        severity=severity,
                        email_preview=email_preview,
                        technical_details=f"Pattern: {pattern.pattern}, Match in: {email_preview[:50]}..."
                    )

                elif self.security_level == "Normal":
                    # Normal mode (default): Block high/medium severity, warn on low
                    if severity in ["high", "medium"]:
                        logger.warning(
                            f"[BLOCKED] Security pattern matched in Normal mode: {pattern_name} "
                            f"(severity: {severity}, description: {description})"
                        )

                        # Log security event (AC3)
                        self.security_logger.log_event(
                            event_type="blocked",
                            pattern_name=pattern_name,
                            email_metadata=email_metadata,
                            action_taken="blocked_email",
                            severity=severity
                        )

                        raise SecurityException(
                            pattern_name=pattern_name,
                            severity=severity,
                            email_preview=email_preview,
                            technical_details=f"Pattern: {pattern.pattern}, Match in: {email_preview[:50]}..."
                        )
                    else:
                        # Low severity: warn only
                        warning_msg = f"Suspicious content detected: {pattern_name} (severity: {severity}, allowed in Normal mode)"
                        self.warnings.append(warning_msg)
                        logger.info(f"[WARNED] {warning_msg}")

                        # Log warning event (AC3)
                        self.security_logger.log_event(
                            event_type="warned",
                            pattern_name=pattern_name,
                            email_metadata=email_metadata,
                            action_taken="allowed_with_warning",
                            severity=severity
                        )

                elif self.security_level == "Permissive":
                    # Permissive mode: Warn on all patterns, allow processing
                    warning_msg = f"Suspicious content detected: {pattern_name} (severity: {severity}, allowed in Permissive mode)"
                    self.warnings.append(warning_msg)
                    logger.info(f"[WARNED] {warning_msg}")

                    # Log warning event (AC3)
                    self.security_logger.log_event(
                        event_type="warned",
                        pattern_name=pattern_name,
                        email_metadata=email_metadata,
                        action_taken="allowed_with_warning",
                        severity=severity
                    )

        return sanitized

    def build_thread_context(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build thread context from email metadata.

        Analyzes headers to determine if email is part of a thread and
        provides context about the conversation.

        Args:
            metadata: Email metadata dictionary

        Returns:
            Thread context dictionary:
            {
                "is_reply": bool,
                "previous_subject": str or None,
                "reply_to_sender": str or None,
                "thread_length": int (estimated)
            }
        """
        is_reply = bool(metadata.get('in_reply_to') or metadata.get('references'))

        # Extract previous subject (remove Re:, Fwd: prefixes)
        subject = metadata.get('subject', '')
        previous_subject = None
        if is_reply:
            previous_subject = re.sub(r'^(Re:|Fwd:|RE:|FW:)\s*', '', subject, flags=re.IGNORECASE).strip()

        # Estimate thread length from references
        references = metadata.get('references', [])
        thread_length = len(references) + 1 if references else 1

        # Extract reply-to sender (would need to parse In-Reply-To or check previous message)
        reply_to_sender = None
        # In a full implementation, this would look up the sender from In-Reply-To message

        thread_context = {
            "is_reply": is_reply,
            "previous_subject": previous_subject if is_reply else None,
            "reply_to_sender": reply_to_sender,
            "thread_length": thread_length
        }

        return thread_context

    # Helper methods

    def _dict_to_message(self, email_dict: Dict[str, Any]) -> Message:
        """Convert dictionary to email.message.Message object."""
        msg = Message()

        # Common field mappings
        field_map = {
            'from': 'From',
            'sender': 'From',
            'SenderEmailAddress': 'From',
            'subject': 'Subject',
            'Subject': 'Subject',
            'date': 'Date',
            'ReceivedTime': 'Date',
            'message_id': 'Message-ID',
            'in_reply_to': 'In-Reply-To',
            'references': 'References'
        }

        for key, value in email_dict.items():
            header_name = field_map.get(key, key)
            if value and isinstance(value, (str, int, float)):
                msg[header_name] = str(value)

        return msg

    def _parse_date(self, date_str: str) -> str:
        """Parse date string to ISO 8601 format."""
        if not date_str:
            return datetime.now().isoformat() + 'Z'

        try:
            if DATEUTIL_AVAILABLE:
                dt = date_parser.parse(date_str)
            else:
                # Fallback: try basic parsing
                dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')

            return dt.isoformat()
        except Exception as e:
            logger.debug(f"Date parsing failed for '{date_str}': {e}")
            return datetime.now().isoformat() + 'Z'

    def _format_attachment(self, filename: str, size: int) -> str:
        """Format attachment as 'filename.ext (size)'."""
        if size < 1024:
            size_str = f"{size}B"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.1f}KB"
        else:
            size_str = f"{size/(1024*1024):.1f}MB"

        return f"{filename} ({size_str})"

    def _truncate_to_sentence(self, text: str) -> str:
        """Truncate text to last complete sentence."""
        # Find last sentence ending
        sentence_endings = ['.', '!', '?']
        last_ending = -1

        for ending in sentence_endings:
            pos = text.rfind(ending)
            if pos > last_ending:
                last_ending = pos

        if last_ending > len(text) * 0.8:  # Only truncate if we're keeping at least 80%
            return text[:last_ending + 1]

        return text

    def _get_default_metadata(self) -> Dict[str, Any]:
        """Return default metadata when extraction fails."""
        return {
            "from": "unknown@unknown.com",
            "subject": "(No Subject)",
            "date": datetime.now().isoformat() + 'Z',
            "message_id": f"generated_{int(time.time())}",
            "thread_id": None,
            "in_reply_to": None,
            "references": []
        }

    def _load_security_patterns(self) -> List[Dict[str, Any]]:
        """
        Load security patterns from YAML file or fallback to defaults.

        Story 3.2 AC7: Updatable Blocklist

        Tries to load patterns from security_patterns.yaml. If file doesn't exist
        or YAML parsing fails, falls back to hardcoded default patterns.

        Returns:
            List of pattern dictionaries with compiled regex and metadata
        """
        compiled_patterns = []

        # Try to load from YAML file first
        if YAML_AVAILABLE and self.security_patterns_path is None:
            # Auto-discover security_patterns.yaml
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(os.path.dirname(current_dir), "config")
            yaml_path = os.path.join(config_dir, "security_patterns.yaml")

            if os.path.exists(yaml_path):
                self.security_patterns_path = yaml_path

        # Load from YAML if available
        if self.security_patterns_path and os.path.exists(self.security_patterns_path):
            try:
                with open(self.security_patterns_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if data and 'patterns' in data:
                    version = data.get('version', 'unknown')
                    logger.info(f"Loading security patterns from {self.security_patterns_path} (version: {version})")

                    for pattern_def in data['patterns']:
                        try:
                            compiled_patterns.append({
                                "name": pattern_def["name"],
                                "regex": re.compile(pattern_def["regex"], re.IGNORECASE),
                                "severity": pattern_def.get("severity", "medium"),
                                "description": pattern_def.get("description", ""),
                                "category": pattern_def.get("category", "unknown")
                            })
                        except re.error as e:
                            logger.error(f"Invalid regex pattern '{pattern_def.get('name')}': {e}")
                            continue

                    logger.info(f"Loaded {len(compiled_patterns)} security patterns from YAML (version: {version})")
                    return compiled_patterns
            except Exception as e:
                logger.warning(f"Failed to load security_patterns.yaml: {e}. Falling back to defaults.")

        # Fallback to default patterns if YAML loading failed
        logger.info("Using default hardcoded security patterns")

        default_patterns = [
            {
                "name": "ignore_instructions",
                "pattern": r'ignore\s+(all\s+)?(previous|prior|above)\s+instructions',
                "severity": "high",
                "description": "Attempts to override system instructions",
                "category": "prompt_injection"
            },
            {
                "name": "ignore_all_instructions",
                "pattern": r'ignore\s+all\s+instructions',
                "severity": "high",
                "description": "Attempts to ignore all instructions",
                "category": "prompt_injection"
            },
            {
                "name": "disregard_instructions",
                "pattern": r'disregard\s+(all\s+)?(previous|prior|above)',
                "severity": "high",
                "description": "Attempts to disregard AI instructions",
                "category": "prompt_injection"
            },
            {
                "name": "system_prompt_injection",
                "pattern": r'system\s*:',
                "severity": "medium",
                "description": "Potential system prompt manipulation",
                "category": "prompt_injection"
            },
            {
                "name": "role_confusion",
                "pattern": r'you\s+are\s+now',
                "severity": "high",
                "description": "Attempts to redefine AI role",
                "category": "prompt_injection"
            },
            {
                "name": "act_as_injection",
                "pattern": r'act\s+as\s+(if|though)',
                "severity": "medium",
                "description": "Role-playing injection attempt",
                "category": "prompt_injection"
            },
            {
                "name": "pretend_injection",
                "pattern": r'pretend\s+(to\s+be|that)',
                "severity": "medium",
                "description": "Pretend-based role injection",
                "category": "prompt_injection"
            },
            {
                "name": "chatml_start",
                "pattern": r'<\|im_start\|>',
                "severity": "high",
                "description": "ChatML format injection attempt",
                "category": "format_injection"
            },
            {
                "name": "chatml_end",
                "pattern": r'<\|im_end\|>',
                "severity": "high",
                "description": "ChatML format injection attempt",
                "category": "format_injection"
            },
        ]

        # Compile default patterns
        for pdef in default_patterns:
            compiled_patterns.append({
                "name": pdef["name"],
                "regex": re.compile(pdef["pattern"], re.IGNORECASE),
                "severity": pdef["severity"],
                "description": pdef["description"],
                "category": pdef["category"]
            })

        logger.info(f"Loaded {len(compiled_patterns)} default security patterns")
        return compiled_patterns


# Convenience function for quick preprocessing
def preprocess_email(raw_email: Any, max_chars: int = 10000) -> Dict[str, Any]:
    """
    Convenience function to preprocess an email.

    Args:
        raw_email: Raw email in supported format
        max_chars: Maximum characters before truncation

    Returns:
        Preprocessed email dictionary
    """
    preprocessor = EmailPreprocessor()
    return preprocessor.preprocess_email(raw_email, max_chars=max_chars)
