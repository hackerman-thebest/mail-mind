# Story 1.2: Email Preprocessing Pipeline

**Epic:** Epic 1 - AI-Powered Email Intelligence
**Story ID:** 1.2
**Story Points:** 5
**Priority:** P0 (Critical Path)
**Status:** TODO
**Created:** 2025-10-13

---

## Story Description

As a system, I need to preprocess raw emails into optimized format for LLM analysis so that inference is fast and token-efficient.

## Business Value

This story transforms raw email data into clean, structured input optimized for LLM processing:
- Reduces token usage by stripping unnecessary content (signatures, quotes)
- Accelerates inference by providing well-formatted, concise input
- Prevents prompt injection attacks through input sanitization
- Preserves critical context (threads, metadata) for accurate analysis
- Enables consistent AI analysis across different email formats (HTML, plain text)

Without this preprocessing, LLM analysis would be slower, more expensive (in tokens), and less accurate.

---

## Acceptance Criteria

### AC1: Email Metadata Extraction
- [ ] Extract sender email address and display name
- [ ] Extract subject line (clean and decode MIME-encoded subjects)
- [ ] Extract received/sent date in ISO 8601 format
- [ ] Extract thread context: In-Reply-To and References headers
- [ ] Extract message ID for tracking and caching
- [ ] Handle missing or malformed headers gracefully

### AC2: HTML to Plain Text Conversion
- [ ] Parse HTML emails using BeautifulSoup
- [ ] Preserve paragraph structure (double newlines between paragraphs)
- [ ] Preserve list formatting (bullets and numbered lists)
- [ ] Convert links to readable format: "Link text (URL)"
- [ ] Strip inline images but note "[Image: filename.jpg]"
- [ ] Remove CSS, JavaScript, and tracking pixels
- [ ] Handle nested tables and complex HTML structures

### AC3: Attachment Handling
- [ ] List attachments with filename and size
- [ ] Do NOT process attachment content in MVP
- [ ] Note attachment presence: "[Attachments: report.pdf (2.3MB), image.png (450KB)]"
- [ ] Warn if attachments might be malicious (e.g., .exe, .scr)

### AC4: Signature and Quote Stripping
- [ ] Detect email signatures using heuristics:
  - Common signature delimiters ("--", "___", "Sent from my iPhone")
  - Contact information patterns (phone numbers, addresses)
  - Legal disclaimers and confidentiality notices
- [ ] Strip quoted replies intelligently:
  - Detect "On [date], [person] wrote:" patterns
  - Detect "> " or "|" quote markers
  - Preserve thread context summary: "In reply to: [subject]"
- [ ] Preserve first 2-3 lines of quoted text if relevant to current message
- [ ] Handle nested quotes in long email threads

### AC5: Content Truncation with Smart Summarization
- [ ] Truncate emails >10,000 characters (to prevent context window overflow)
- [ ] Intelligent truncation strategy:
  - Keep first 8,000 characters (primary content)
  - Keep last 1,000 characters (conclusion/signature context)
  - Note truncation: "[Content truncated: 15,234 chars → 9,000 chars]"
- [ ] Never truncate emails <8,000 characters
- [ ] Preserve complete sentences (don't cut mid-sentence)

### AC6: Structured Prompt Format
- [ ] Create JSON structure for LLM consumption:
```json
{
  "metadata": {
    "from": "alice@example.com (Alice Smith)",
    "subject": "Q4 Budget Review Needed by Friday",
    "date": "2025-10-13T14:30:00Z",
    "thread_id": "abc123...",
    "message_id": "def456..."
  },
  "content": {
    "body": "Hi team,\n\nWe need to review...",
    "has_attachments": true,
    "attachments": ["report.pdf (2.3MB)"],
    "char_count": 1847,
    "was_truncated": false
  },
  "thread_context": {
    "is_reply": true,
    "previous_subject": "Budget Discussion",
    "reply_to_sender": "bob@example.com"
  }
}
```
- [ ] Provide plain text format option for simpler use cases
- [ ] Include preprocessing metadata (timing, truncation, warnings)

### AC7: Thread Context Preservation
- [ ] Detect if email is part of a thread using In-Reply-To header
- [ ] Extract thread subject history (track "Re: Re: Re:" chains)
- [ ] Link to previous messages in thread if available in cache
- [ ] Summarize thread context: "Email #3 in thread started by Bob on 10/10"

### AC8: Input Sanitization & Security
- [ ] Sanitize input to prevent prompt injection attacks:
  - Escape special characters that could break prompts
  - Detect and flag suspicious patterns (e.g., "Ignore previous instructions")
  - Remove control characters and non-printable ASCII
- [ ] Validate all extracted metadata (email addresses, dates)
- [ ] Log security warnings for suspicious content
- [ ] Rate-limit processing if abuse detected

---

## Technical Notes

### Dependencies
- **BeautifulSoup4:** HTML parsing (`pip install beautifulsoup4`)
- **lxml:** Fast HTML parser backend (`pip install lxml`)
- **email.parser:** Python stdlib for email parsing
- **re:** Regex for signature/quote detection
- **dateutil:** Robust date parsing (`pip install python-dateutil`)

### Email Signature Detection Heuristics

```python
SIGNATURE_PATTERNS = [
    r'^--\s*$',  # Standard email signature delimiter
    r'^_{10,}',  # Underscores
    r'Sent from my (iPhone|iPad|Android)',
    r'Get Outlook for (iOS|Android)',
    r'\b(Best regards|Sincerely|Thanks|Cheers),',
    r'\b(Phone|Tel|Mobile):',
    r'\bwww\.[a-z0-9-]+\.(com|net|org)',
    r'CONFIDENTIALITY NOTICE',
]
```

### Quote Detection Patterns

```python
QUOTE_PATTERNS = [
    r'^On .+ wrote:$',  # Gmail style
    r'^From:.+Sent:.+To:.+Subject:',  # Outlook style
    r'^>',  # Traditional quote marker
    r'^\|',  # Pipe-style quote marker
]
```

### Performance Targets
- **Metadata extraction:** <10ms
- **HTML parsing:** <50ms (typical email)
- **Signature/quote stripping:** <20ms
- **Full preprocessing:** <200ms (target)
- **Batch processing:** 50 emails/minute

### Implementation Approach

```python
class EmailPreprocessor:
    def __init__(self):
        self.signature_patterns = self._compile_patterns(SIGNATURE_PATTERNS)
        self.quote_patterns = self._compile_patterns(QUOTE_PATTERNS)

    def preprocess_email(self, raw_email: str) -> Dict[str, Any]:
        """
        Preprocess raw email into structured format for LLM.

        Args:
            raw_email: Raw email message (MIME format or dict from Outlook)

        Returns:
            Structured preprocessed email data
        """
        start_time = time.time()

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
        body, was_truncated = self.smart_truncate(body, max_chars=10000)

        # Step 6: Sanitize input
        body = self.sanitize_content(body)

        # Step 7: Build thread context
        thread_context = self.build_thread_context(metadata)

        preprocessing_time = time.time() - start_time

        return {
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
                "warnings": self.warnings
            }
        }

    def parse_html(self, html_content: str) -> str:
        """Convert HTML email to clean plain text."""
        soup = BeautifulSoup(html_content, 'lxml')

        # Remove scripts, styles, tracking pixels
        for tag in soup(['script', 'style', 'img[width="1"]']):
            tag.decompose()

        # Convert links
        for link in soup.find_all('a'):
            link_text = link.get_text()
            link_url = link.get('href', '')
            if link_url:
                link.replace_with(f"{link_text} ({link_url})")

        # Get text with structure preserved
        text = soup.get_text(separator='\n\n')

        # Clean up whitespace
        text = '\n'.join(line.strip() for line in text.split('\n'))
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def strip_signatures(self, body: str) -> str:
        """Remove email signatures using heuristics."""
        lines = body.split('\n')
        signature_start = None

        for i, line in enumerate(lines):
            # Check signature patterns
            for pattern in self.signature_patterns:
                if pattern.search(line):
                    signature_start = i
                    break
            if signature_start:
                break

        if signature_start:
            # Keep content before signature
            return '\n'.join(lines[:signature_start]).strip()

        return body

    def smart_truncate(self, body: str, max_chars: int = 10000) -> tuple:
        """Intelligently truncate long emails."""
        if len(body) <= max_chars:
            return body, False

        # Keep first 8000 chars and last 1000 chars
        first_part = body[:8000]
        last_part = body[-1000:]

        # Try to end on sentence boundary
        first_part = self._truncate_to_sentence(first_part)

        truncated_body = f"{first_part}\n\n[... Content truncated: {len(body)} chars → {len(first_part) + len(last_part)} chars ...]\n\n{last_part}"

        return truncated_body, True

    def sanitize_content(self, body: str) -> str:
        """Sanitize content to prevent prompt injection."""
        # Remove control characters
        body = ''.join(char for char in body if char.isprintable() or char in '\n\t')

        # Detect suspicious patterns
        suspicious_patterns = [
            r'ignore\s+(previous|all)\s+instructions',
            r'system\s*:',
            r'you\s+are\s+now',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                self.warnings.append(f"Suspicious content detected: {pattern}")

        return body
```

---

## Testing Checklist

### Unit Tests
- [ ] Test metadata extraction from various email formats
- [ ] Test HTML parsing with complex nested structures
- [ ] Test signature detection with common patterns
- [ ] Test quote stripping for Gmail, Outlook, custom formats
- [ ] Test smart truncation at various lengths
- [ ] Test prompt injection sanitization
- [ ] Test thread context extraction
- [ ] Test attachment metadata extraction

### Integration Tests
- [ ] Test with real Outlook email messages
- [ ] Test with HTML emails from various clients (Gmail, Outlook, Apple Mail)
- [ ] Test with plain text emails
- [ ] Test with multi-part MIME emails
- [ ] Test with international characters (UTF-8, emoji)
- [ ] Test with malformed or suspicious emails
- [ ] Test preprocessing performance (<200ms target)

### Edge Cases
- [ ] Email with no subject
- [ ] Email with no body (just attachments)
- [ ] Email with extremely long subject (>500 chars)
- [ ] Email with 50+ attachments
- [ ] Email with nested HTML tables
- [ ] Email thread with 20+ replies
- [ ] Email with mixed encodings
- [ ] Email with embedded images as base64

---

## Performance Targets

| Operation | Target | Critical? |
|-----------|--------|-----------|
| Metadata extraction | <10ms | Yes |
| HTML parsing (typical) | <50ms | Yes |
| HTML parsing (complex) | <150ms | No |
| Signature stripping | <20ms | Yes |
| Quote detection | <30ms | Yes |
| Smart truncation | <20ms | No |
| Sanitization | <10ms | Yes |
| **Total preprocessing** | **<200ms** | **Yes** |
| Batch processing | 50 emails/min | No |

---

## Definition of Done

- [ ] All acceptance criteria met (AC1-AC8)
- [ ] Unit tests written and passing (>90% coverage)
- [ ] Integration tests with real email samples passing
- [ ] Edge cases handled gracefully
- [ ] Performance targets met (<200ms preprocessing)
- [ ] Security: Prompt injection prevention tested
- [ ] Code reviewed and approved
- [ ] Documentation updated:
  - Module docstrings complete
  - API documentation for EmailPreprocessor class
  - Example usage in README
- [ ] Integrated with OllamaManager from Story 1.1
- [ ] Logging added for debugging and metrics

---

## Dependencies & Blockers

**Upstream Dependencies:**
- Story 1.1 (Ollama Integration) - COMPLETE ✅
- OllamaManager must be available for integration

**Downstream Dependencies:**
- Story 1.3 (Real-Time Analysis Engine) depends on this
- Story 1.4 (Priority Classification) depends on this
- All AI analysis features depend on preprocessed email format

**External Dependencies:**
- BeautifulSoup4 library
- Python email.parser (stdlib)
- Access to sample email data for testing

**Potential Blockers:**
- Outlook COM interface may provide emails in unexpected formats
- HTML parsing edge cases may require additional libraries
- Performance targets may require optimization iteration

---

## Implementation Plan

### Phase 1: Core Parsing (Day 1-2)
1. Install dependencies (BeautifulSoup4, lxml)
2. Create EmailPreprocessor class skeleton
3. Implement metadata extraction
4. Implement HTML to plain text conversion
5. Write unit tests for parsing

### Phase 2: Content Cleaning (Day 2-3)
1. Implement signature detection heuristics
2. Implement quote stripping logic
3. Add attachment metadata extraction
4. Test with real email samples
5. Write unit tests for cleaning

### Phase 3: Optimization & Security (Day 3-4)
1. Implement smart truncation algorithm
2. Add input sanitization for security
3. Build thread context extraction
4. Performance profiling and optimization
5. Add logging and metrics

### Phase 4: Integration & Testing (Day 4-5)
1. Integrate with OllamaManager from Story 1.1
2. Create end-to-end test pipeline
3. Test with 100+ real email samples
4. Document API and usage examples
5. Code review and final adjustments

---

## Output Format Examples

### Example 1: Simple Email
**Input:** Plain text email
**Output:**
```json
{
  "metadata": {
    "from": "bob@company.com (Bob Johnson)",
    "subject": "Quick question about project timeline",
    "date": "2025-10-13T10:15:00Z",
    "message_id": "msg_abc123",
    "thread_id": null
  },
  "content": {
    "body": "Hi team,\n\nCan we push the deadline to next Friday? I need more time for testing.\n\nThanks!",
    "has_attachments": false,
    "attachments": [],
    "char_count": 95,
    "was_truncated": false
  },
  "thread_context": {
    "is_reply": false,
    "previous_subject": null,
    "reply_to_sender": null
  },
  "preprocessing_metadata": {
    "processing_time_ms": 12,
    "warnings": []
  }
}
```

### Example 2: HTML Email with Thread
**Input:** HTML email in reply thread
**Output:**
```json
{
  "metadata": {
    "from": "alice@company.com (Alice Smith)",
    "subject": "Re: Q4 Budget Review",
    "date": "2025-10-13T14:30:00Z",
    "message_id": "msg_def456",
    "thread_id": "thread_xyz789"
  },
  "content": {
    "body": "I've reviewed the numbers and we're tracking 5% over budget.\n\nWe should meet this week to discuss cost reduction strategies.\n\n[Attachments: Q4_Budget_Analysis.xlsx (1.2MB)]",
    "has_attachments": true,
    "attachments": ["Q4_Budget_Analysis.xlsx (1.2MB)"],
    "char_count": 127,
    "was_truncated": false
  },
  "thread_context": {
    "is_reply": true,
    "previous_subject": "Q4 Budget Review",
    "reply_to_sender": "bob@company.com"
  },
  "preprocessing_metadata": {
    "processing_time_ms": 87,
    "warnings": []
  }
}
```

---

## Questions & Decisions

**Q: Should we cache preprocessed emails?**
**A:** Yes - store in database with message_id key. If raw email hasn't changed, use cached preprocessed version.

**Q: What if HTML parsing fails?**
**A:** Graceful fallback: Use raw text content, log warning, continue processing.

**Q: Should we support non-English emails?**
**A:** Yes - UTF-8 support is required. Language detection is out of scope for MVP.

**Q: How to handle inline images in HTML?**
**A:** Note presence with "[Image: filename.jpg]" but don't process content. Future: OCR for image text.

**Q: What about calendar invites (.ics attachments)?**
**A:** Note as attachment in MVP. Future: Parse and extract event details.

---

## Related Documentation

- [BeautifulSoup4 Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Python email.parser](https://docs.python.org/3/library/email.parser.html)
- PRD Section 5.1.3: Email Preprocessing Pipeline
- epic-stories.md: Full epic context
- Story 1.1 (completed): OllamaManager integration

---

## Story Lifecycle

**Created:** 2025-10-13 (Moved from BACKLOG to TODO after Story 1.1 completion)
**Started:** [To be filled when implementation begins]
**Completed:** [To be filled when DoD met]

---

_This story is part of Epic 1: AI-Powered Email Intelligence. It provides the critical preprocessing layer that enables fast, secure, and accurate LLM-based email analysis._
