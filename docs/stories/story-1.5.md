# Story 1.5: Response Generation Assistant

**Epic:** Epic 1 - AI-Powered Email Intelligence
**Story ID:** 1.5
**Story Points:** 8
**Priority:** P0 (Critical Path)
**Status:** Ready
**Created:** 2025-10-13
**Approved:** 2025-10-13

---

## Story Description

As a user, I need AI to draft contextual email replies in my writing style so that I can respond faster to routine emails.

## Business Value

This story completes the AI-powered email intelligence loop by adding response generation:
- Reduces time spent writing routine email responses by 60-70%
- AI learns user's writing style from sent items for authentic responses
- Multiple length options (Brief/Standard/Detailed) provide flexibility
- Tone adjustment (Professional/Friendly/Formal/Casual) adapts to context
- Templates for common scenarios (meeting acceptance, status update, thank you, decline)
- All generation happens offline in <5 seconds, maintaining privacy
- Editable drafts give users full control before sending
- Response quality improves over time as system learns from user edits

Without this story, users can analyze emails but must manually compose all responses. This adds intelligent drafting to complete the workflow.

---

## Acceptance Criteria

### AC1: Multiple Response Lengths
- [ ] Generate responses in three lengths:
  - **Brief:** <50 words (quick acknowledgments, simple yes/no)
  - **Standard:** 50-150 words (typical business replies)
  - **Detailed:** 150-300 words (comprehensive responses with context)
- [ ] Length selection available in UI (buttons or dropdown)
- [ ] Generated response matches requested length (±20% tolerance)
- [ ] Brief responses focus on key point only
- [ ] Standard responses include context and key details
- [ ] Detailed responses provide comprehensive coverage with reasoning

### AC2: Thread Context Incorporation
- [ ] Include full email thread in generation prompt
- [ ] Reference previous messages when relevant
- [ ] Maintain conversation continuity across thread
- [ ] Identify and respond to all questions from sender
- [ ] Acknowledge points made in previous emails
- [ ] Thread context limited to last 5 messages for token efficiency

### AC3: Writing Style Analysis & Matching
- [ ] Analyze user's sent items folder on first use
- [ ] Extract writing patterns from 20-50 sent emails:
  - Greeting style (Hi/Hello/Dear)
  - Closing style (Thanks/Best/Regards)
  - Sentence structure (short vs. long sentences)
  - Formality level (contractions, casual language)
  - Tone markers (enthusiasm, directness, politeness)
  - Common phrases and expressions
- [ ] Store writing style profile in user preferences database
- [ ] Apply learned style to all generated responses
- [ ] Update style profile incrementally as user edits responses

### AC4: Common Scenario Templates
- [ ] Provide pre-built templates for common scenarios:
  - **Meeting Acceptance:** Accept meeting invite with confirmation
  - **Meeting Decline:** Politely decline with optional reason
  - **Status Update:** Provide project/task status summary
  - **Thank You:** Express gratitude appropriately
  - **Information Request:** Request additional details
  - **Acknowledgment:** Confirm receipt and next steps
  - **Follow-up:** Check status of previous conversation
  - **Out of Office:** Automatic OOO-style response
- [ ] Template selection via UI dropdown or smart suggestion
- [ ] Templates adapt to user's writing style
- [ ] Smart template suggestion based on email content

### AC5: Tone Adjustment Controls
- [ ] Support four tone options:
  - **Professional:** Formal business language, no contractions
  - **Friendly:** Warm and approachable, some informality
  - **Formal:** Very formal, titles, structured language
  - **Casual:** Relaxed, conversational, contractions
- [ ] Tone selection via UI buttons or dropdown
- [ ] Default tone inferred from original email's tone
- [ ] Tone adjustment preserves core message content
- [ ] Each tone generates distinct language patterns

### AC6: Offline Generation Performance
- [ ] Generate Brief responses in <3 seconds (target)
- [ ] Generate Standard responses in <5 seconds (target)
- [ ] Generate Detailed responses in <10 seconds (acceptable)
- [ ] Display generation progress indicator
- [ ] Show estimated time remaining during generation
- [ ] Allow cancellation of in-progress generation
- [ ] Performance targets based on recommended hardware (mid-GPU)
- [ ] CPU-only performance: 2x longer acceptable

### AC7: Editable Draft in UI
- [ ] Display generated response in editable text area
- [ ] Preserve formatting (paragraphs, spacing)
- [ ] Allow full editing before sending
- [ ] Track edit percentage (chars changed / total chars)
- [ ] "Regenerate" button to create new draft
- [ ] "Accept" button to use draft as-is
- [ ] "Cancel" button to discard draft
- [ ] Save draft automatically every 30 seconds

### AC8: Response Metrics Tracking
- [ ] Track response generation metrics:
  - Generation time (ms)
  - Response length (words, chars)
  - Tone selected
  - Template used (if any)
  - Edit percentage after generation
  - User accepted or discarded
  - Regeneration count
- [ ] Store metrics in performance_metrics table
- [ ] Calculate acceptance rate (accepted / total generated)
- [ ] Calculate average edit percentage
- [ ] Display metrics in settings/statistics panel
- [ ] Weekly/monthly metrics summary

---

## Technical Notes

### Dependencies
- **Story 1.1:** OllamaManager (LLM inference) ✅ COMPLETE
- **Story 1.2:** EmailPreprocessor (email parsing) ✅ COMPLETE
- **Story 1.3:** EmailAnalysisEngine (email analysis) ✅ COMPLETE
- **Story 1.4:** PriorityClassifier (priority info for urgency) ✅ COMPLETE
- **Story 2.1:** Outlook Integration (access to sent items) - can simulate for MVP
- **SQLite:** For storing writing style profile and metrics

### Architecture Overview

```
User initiates response
    ↓
Load email + thread context
    ↓
Retrieve writing style profile from DB
    ↓
Determine tone (from user selection or email analysis)
    ↓
Select template (if applicable)
    ↓
Build response generation prompt
    ↓
OllamaManager.generate() (Story 1.1)
    ↓
Parse and format response
    ↓
Display in editable UI
    ↓
User edits / accepts / regenerates
    ↓
Track metrics
    ↓
Update writing style based on edits
```

### Response Generation Prompt Engineering

**System Prompt:**
```
You are an email response assistant. Generate professional email responses that match the user's writing style and tone. Be concise, clear, and appropriate for business communication.
```

**Response Generation Prompt Template:**
```
Generate an email response based on the following information:

Original Email:
From: {from}
Subject: {subject}
Body: {body}

Thread Context:
{thread_summary}

User's Writing Style:
- Greeting: {greeting_style}
- Closing: {closing_style}
- Formality: {formality_level}
- Common phrases: {common_phrases}

Response Requirements:
- Length: {length} ({word_target} words)
- Tone: {tone}
- Template: {template} (if applicable)

Generate ONLY the email response body. Do not include subject line or email headers.
Maintain the user's writing style and match the requested tone.
Respond to all questions and points raised in the original email.

Response:
```

### Few-Shot Learning from Sent Items

```python
class WritingStyleAnalyzer:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)

    def analyze_sent_emails(self, sent_emails: List[Dict]) -> Dict[str, Any]:
        """
        Analyze sent emails to extract writing style patterns.

        Args:
            sent_emails: List of sent email dictionaries

        Returns:
            Writing style profile dictionary
        """
        # Extract patterns from 20-50 sent emails
        sample_size = min(50, max(20, len(sent_emails)))
        sample = sent_emails[:sample_size]

        # Analyze greeting patterns
        greetings = self._extract_greetings(sample)
        most_common_greeting = max(set(greetings), key=greetings.count)

        # Analyze closing patterns
        closings = self._extract_closings(sample)
        most_common_closing = max(set(closings), key=closings.count)

        # Analyze formality
        formality = self._calculate_formality(sample)

        # Extract common phrases
        common_phrases = self._extract_common_phrases(sample)

        # Analyze sentence structure
        avg_sentence_length = self._calculate_avg_sentence_length(sample)

        # Analyze tone markers
        tone_markers = self._extract_tone_markers(sample)

        profile = {
            'greeting_style': most_common_greeting,
            'closing_style': most_common_closing,
            'formality_level': formality,  # 0.0-1.0 scale
            'common_phrases': common_phrases[:10],  # Top 10
            'avg_sentence_length': avg_sentence_length,
            'tone_markers': tone_markers,
            'sample_size': sample_size,
            'last_updated': datetime.now().isoformat()
        }

        return profile

    def _extract_greetings(self, emails: List[Dict]) -> List[str]:
        """Extract greeting patterns from emails."""
        greetings = []
        patterns = [
            r'^(Hi|Hello|Hey|Dear|Greetings)',
            r'^(Good morning|Good afternoon|Good evening)',
        ]

        for email in emails:
            body = email.get('body', '')
            first_line = body.split('\n')[0] if body else ''

            for pattern in patterns:
                match = re.search(pattern, first_line, re.IGNORECASE)
                if match:
                    greetings.append(match.group(1))
                    break

        return greetings if greetings else ['Hi']

    def _extract_closings(self, emails: List[Dict]) -> List[str]:
        """Extract closing patterns from emails."""
        closings = []
        patterns = [
            r'(Thanks|Thank you|Best regards|Best|Regards|Sincerely|Cheers)',
        ]

        for email in emails:
            body = email.get('body', '')
            last_lines = '\n'.join(body.split('\n')[-3:])  # Last 3 lines

            for pattern in patterns:
                match = re.search(pattern, last_lines, re.IGNORECASE)
                if match:
                    closings.append(match.group(1))
                    break

        return closings if closings else ['Thanks']

    def _calculate_formality(self, emails: List[Dict]) -> float:
        """Calculate formality score 0.0 (casual) to 1.0 (formal)."""
        formality_scores = []

        for email in emails:
            body = email.get('body', '')

            # Indicators of informality
            contractions = len(re.findall(r"n't|'s|'re|'ve|'ll|'d", body))
            exclamations = body.count('!')
            casual_words = len(re.findall(r'\b(hey|yeah|yep|nope|gonna|wanna)\b', body, re.IGNORECASE))

            # Indicators of formality
            formal_greetings = len(re.findall(r'\b(Dear|Greetings|Sincerely)\b', body, re.IGNORECASE))
            formal_words = len(re.findall(r'\b(regarding|furthermore|therefore|accordingly)\b', body, re.IGNORECASE))

            # Calculate score
            informal_score = contractions + exclamations + casual_words
            formal_score = formal_greetings + formal_words

            total = informal_score + formal_score
            if total > 0:
                formality = formal_score / total
            else:
                formality = 0.5  # Neutral

            formality_scores.append(formality)

        return sum(formality_scores) / len(formality_scores) if formality_scores else 0.5
```

### Response Generator Implementation

```python
class ResponseGenerator:
    def __init__(self, ollama_manager: OllamaManager, db_path: str):
        self.ollama = ollama_manager
        self.db = sqlite3.connect(db_path)
        self.style_analyzer = WritingStyleAnalyzer(db_path)
        self.writing_style = self._load_writing_style()

    def _load_writing_style(self) -> Dict[str, Any]:
        """Load user's writing style profile from database."""
        cursor = self.db.execute("""
            SELECT value FROM user_preferences
            WHERE key = 'writing_style_profile'
        """)

        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        else:
            # Default style profile
            return {
                'greeting_style': 'Hi',
                'closing_style': 'Thanks',
                'formality_level': 0.5,
                'common_phrases': [],
                'avg_sentence_length': 15,
                'tone_markers': {}
            }

    def generate_response(
        self,
        email: Dict[str, Any],
        length: str = 'Standard',
        tone: str = 'Professional',
        template: Optional[str] = None,
        thread_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate email response using LLM.

        Args:
            email: Preprocessed email data
            length: Brief|Standard|Detailed
            tone: Professional|Friendly|Formal|Casual
            template: Optional template name
            thread_context: Optional list of previous emails in thread

        Returns:
            Generated response dictionary
        """
        start_time = time.time()

        # Build generation prompt
        prompt = self._build_response_prompt(
            email,
            length,
            tone,
            template,
            thread_context
        )

        # Determine token target based on length
        word_targets = {
            'Brief': 50,
            'Standard': 100,
            'Detailed': 200
        }
        max_tokens = word_targets[length] * 2  # ~2 tokens per word

        # Generate response with LLM
        response_text = self.ollama.generate(
            prompt=prompt,
            temperature=0.7,  # Higher for creativity
            max_tokens=max_tokens
        )

        # Clean and format response
        formatted_response = self._format_response(response_text)

        # Calculate metrics
        processing_time = int((time.time() - start_time) * 1000)
        word_count = len(formatted_response.split())

        result = {
            'response_text': formatted_response,
            'length': length,
            'tone': tone,
            'template': template,
            'word_count': word_count,
            'processing_time_ms': processing_time,
            'model_version': self.ollama.get_model_info()['name']
        }

        # Store metrics
        self._log_response_metrics(result)

        return result

    def _build_response_prompt(
        self,
        email: Dict[str, Any],
        length: str,
        tone: str,
        template: Optional[str],
        thread_context: Optional[List[Dict]]
    ) -> str:
        """Build LLM prompt for response generation."""
        metadata = email.get('metadata', {})
        content = email.get('content', {})

        # Word targets
        word_targets = {
            'Brief': '20-50',
            'Standard': '50-150',
            'Detailed': '150-300'
        }

        # Build thread summary
        thread_summary = ""
        if thread_context:
            thread_summary = self._summarize_thread(thread_context)

        # Get template instructions if specified
        template_instructions = ""
        if template:
            template_instructions = self._get_template_instructions(template)

        # Build style instructions
        style_instructions = f"""
Greeting: Start with "{self.writing_style['greeting_style']}"
Closing: End with "{self.writing_style['closing_style']}"
Formality: {'Formal' if self.writing_style['formality_level'] > 0.7 else 'Casual' if self.writing_style['formality_level'] < 0.3 else 'Balanced'}
"""

        prompt = f"""Generate an email response in the user's writing style.

Original Email:
From: {metadata.get('from', 'Unknown')}
Subject: {metadata.get('subject', 'No subject')}
Body:
{content.get('body', '')}

{f"Thread Context:\n{thread_summary}\n" if thread_summary else ""}

Response Requirements:
- Length: {length} ({word_targets[length]} words)
- Tone: {tone}
{f"- Template: {template}\n{template_instructions}\n" if template else ""}

User's Writing Style:
{style_instructions}

Generate ONLY the email response body. Do not include subject line, salutation if not needed, or signature block.
Match the user's writing style and requested tone.
Address all questions and points from the original email.

Response:
"""

        return prompt

    def _format_response(self, raw_response: str) -> str:
        """Clean and format generated response."""
        # Remove any markdown artifacts
        response = re.sub(r'```[\s\S]*?```', '', raw_response)

        # Remove leading/trailing whitespace
        response = response.strip()

        # Ensure proper paragraph spacing
        response = re.sub(r'\n{3,}', '\n\n', response)

        return response

    def _summarize_thread(self, thread_context: List[Dict]) -> str:
        """Summarize thread context for prompt."""
        # Limit to last 5 messages for token efficiency
        recent_thread = thread_context[-5:]

        summary_lines = []
        for i, msg in enumerate(recent_thread):
            sender = msg.get('metadata', {}).get('from', 'Unknown')
            body_preview = msg.get('content', {}).get('body', '')[:100]
            summary_lines.append(f"{i+1}. {sender}: {body_preview}...")

        return '\n'.join(summary_lines)

    def _get_template_instructions(self, template: str) -> str:
        """Get specific instructions for template type."""
        templates = {
            'Meeting Acceptance': 'Confirm attendance, acknowledge time/date, express enthusiasm',
            'Meeting Decline': 'Politely decline, provide brief reason if appropriate, suggest alternative if possible',
            'Status Update': 'Provide clear status, mention progress, note any blockers, state next steps',
            'Thank You': 'Express genuine gratitude, acknowledge specific action, maintain warmth',
            'Information Request': 'Clearly state what information is needed, explain why, provide deadline if needed',
            'Acknowledgment': 'Confirm receipt, summarize key points, state next action',
            'Follow-up': 'Reference previous conversation, check current status, offer assistance',
            'Out of Office': 'State unavailability period, provide alternative contact, set return expectations'
        }

        return templates.get(template, '')

    def _log_response_metrics(self, result: Dict[str, Any]) -> None:
        """Log response generation metrics to database."""
        self.db.execute("""
            INSERT INTO performance_metrics (
                operation,
                processing_time_ms,
                model_version,
                timestamp
            ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            f'response_generation_{result["length"]}',
            result['processing_time_ms'],
            result['model_version']
        ))

        self.db.commit()

    def update_style_from_edits(
        self,
        original: str,
        edited: str
    ) -> None:
        """
        Update writing style profile based on user edits.

        Args:
            original: Original generated response
            edited: User's edited version
        """
        # Calculate edit distance and patterns
        # This would analyze what changed and update style profile
        # For MVP, this can be simplified or deferred
        pass

    def get_response_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get response generation metrics for time period."""
        cursor = self.db.execute("""
            SELECT
                COUNT(*) as total_generated,
                AVG(processing_time_ms) as avg_time,
                operation
            FROM performance_metrics
            WHERE operation LIKE 'response_generation_%'
            AND timestamp > datetime('now', '-' || ? || ' days')
            GROUP BY operation
        """, (days,))

        metrics = {
            'total_generated': 0,
            'by_length': {},
            'avg_processing_time_ms': 0
        }

        for row in cursor:
            total = row[0]
            avg_time = row[1]
            operation = row[2]
            length = operation.replace('response_generation_', '')

            metrics['total_generated'] += total
            metrics['by_length'][length] = {
                'count': total,
                'avg_time_ms': avg_time
            }

        return metrics
```

---

## Testing Checklist

### Unit Tests
- [ ] Test ResponseGenerator initialization
- [ ] Test writing style analyzer with sample sent emails
- [ ] Test greeting extraction from emails
- [ ] Test closing extraction from emails
- [ ] Test formality calculation
- [ ] Test response prompt building
- [ ] Test response formatting and cleanup
- [ ] Test thread context summarization
- [ ] Test template instruction retrieval
- [ ] Test metrics logging
- [ ] Test edge cases: empty emails, no thread context

### Integration Tests
- [ ] Test full response generation pipeline (email → LLM → formatted response)
- [ ] Test with real Ollama inference (requires Ollama running)
- [ ] Test all three lengths (Brief, Standard, Detailed)
- [ ] Test all four tones (Professional, Friendly, Formal, Casual)
- [ ] Test all templates (Meeting Acceptance, Decline, etc.)
- [ ] Test with thread context (multi-email conversations)
- [ ] Test writing style analysis with sample sent folder
- [ ] Test response metrics tracking and retrieval

### Style Matching Tests
- [ ] Generated responses match user's greeting style
- [ ] Generated responses match user's closing style
- [ ] Formality level matches user's typical formality
- [ ] Common phrases from user's writing appear in responses
- [ ] Sentence structure similar to user's style

### Performance Tests
- [ ] Brief response generation <3 seconds (recommended hardware)
- [ ] Standard response generation <5 seconds (recommended hardware)
- [ ] Detailed response generation <10 seconds (recommended hardware)
- [ ] CPU-only performance within 2x of targets
- [ ] Writing style analysis <2 seconds for 50 emails
- [ ] Metrics retrieval <100ms

### Edge Cases
- [ ] Email with no clear question or request
- [ ] Very long email (>5000 chars)
- [ ] Thread with 10+ previous messages
- [ ] User with no sent items (default style)
- [ ] LLM generates invalid or inappropriate response
- [ ] LLM timeout or error
- [ ] Database write failure
- [ ] User cancels generation mid-process

---

## Performance Targets

| Operation | Target | Acceptable | Critical |
|-----------|--------|------------|----------|
| **Brief Response** | <3s | <5s | <8s |
| **Standard Response** | <5s | <8s | <12s |
| **Detailed Response** | <10s | <15s | <20s |
| **Writing Style Analysis** | <2s | <5s | <10s |
| **Style Profile Load** | <50ms | <100ms | <200ms |
| **Metrics Retrieval** | <100ms | <200ms | <500ms |

**Hardware-based Targets:**
- **Optimal (high-GPU):** Meet target times
- **Recommended (mid-GPU):** Meet acceptable times
- **Minimum (CPU-only):** 2x acceptable times (still usable)

**Quality Targets:**
- Response acceptance rate: >70% (user accepts without major edits)
- Style matching score: >80% (subjective user rating)
- Template appropriateness: >85% (template matches scenario)
- Average edit percentage: <30% (most of response kept)

---

## Definition of Done

- [ ] All acceptance criteria met (AC1-AC8)
- [ ] ResponseGenerator class implemented
- [ ] WritingStyleAnalyzer class implemented
- [ ] Integration with OllamaManager (Story 1.1) complete
- [ ] Integration with EmailPreprocessor (Story 1.2) complete
- [ ] Integration with EmailAnalysisEngine (Story 1.3) for context
- [ ] Response generation for all three lengths working
- [ ] All four tone options implemented
- [ ] All eight templates implemented and tested
- [ ] Writing style analysis from sent items working
- [ ] Database schema for writing style profile created
- [ ] Response metrics tracking implemented
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration tests with real Ollama passing
- [ ] Performance targets met on recommended hardware
- [ ] Error handling for all failure modes
- [ ] Code reviewed and approved
- [ ] Documentation updated:
  - Module docstrings complete
  - API documentation for ResponseGenerator
  - Writing style analysis explanation
  - Template usage examples
- [ ] Demo script showing response generation scenarios
- [ ] UI integration points documented for Story 2.3

---

## Dependencies & Blockers

**Upstream Dependencies:**
- Story 1.1 (Ollama Integration) - COMPLETE ✅
- Story 1.2 (Email Preprocessing) - COMPLETE ✅
- Story 1.3 (Email Analysis Engine) - COMPLETE ✅
- Story 1.4 (Priority Classifier) - COMPLETE ✅

**Downstream Dependencies:**
- Story 2.1 (Outlook Integration) provides access to sent items folder
- Story 2.2 (SQLite Database) provides production database schema
- Story 2.3 (UI) provides response editor interface
- Story 2.4 (Settings) allows writing style customization

**External Dependencies:**
- Ollama service running
- LLM model downloaded (Llama 3.1 8B or Mistral 7B)
- SQLite3 (Python stdlib)

**Potential Blockers:**
- LLM may not match user's style perfectly initially
- Response quality varies with email complexity
- Sent items folder may be inaccessible (Story 2.1 dependency)
- Performance targets challenging for detailed responses on CPU-only

---

## Implementation Plan

### Phase 1: Writing Style Analysis (Day 1-2)
1. Create WritingStyleAnalyzer class
2. Implement greeting/closing extraction
3. Implement formality calculation
4. Implement common phrase extraction
5. Test with sample sent emails
6. Store style profile in database

### Phase 2: Core Response Generation (Day 2-3)
1. Create ResponseGenerator class skeleton
2. Implement response prompt building
3. Integrate OllamaManager for LLM generation
4. Implement response formatting
5. Add length controls (Brief/Standard/Detailed)
6. Test basic generation

### Phase 3: Templates & Tone Controls (Day 3-4)
1. Implement eight response templates
2. Add template selection logic
3. Implement four tone options
4. Test tone variations with same email
5. Add thread context summarization
6. Test with multi-email threads

### Phase 4: Metrics & Polish (Day 4-5)
1. Implement response metrics tracking
2. Add metrics retrieval and reporting
3. Write comprehensive unit tests
4. Write integration tests with real Ollama
5. Performance testing and optimization
6. Documentation and examples

---

## Output Format Example

### Brief Response
```
Hi Alice,

Yes, I can attend the meeting on Friday at 2pm.

Thanks,
[User]
```

### Standard Response
```
Hi Alice,

Thanks for the meeting invite. I can confirm my attendance for Friday at 2pm in Conference Room B.

I've reviewed the agenda and will come prepared to discuss the Q4 budget concerns. Please let me know if you need me to bring any additional materials.

Thanks,
[User]
```

### Detailed Response
```
Hi Alice,

Thank you for organizing this meeting to discuss the Q4 budget overrun. I can confirm my attendance for Friday, October 15th at 2pm in Conference Room B.

I've reviewed the preliminary budget analysis you sent last week and have some insights on potential cost reduction strategies. Specifically, I think we can optimize our vendor contracts and delay some non-critical expenditures to Q1 next year without impacting delivery timelines.

I'll prepare a brief presentation covering three main areas:
1. Current spending analysis by department
2. Immediate cost-saving opportunities ($50-75K)
3. Proposed budget reallocation for remainder of Q4

Please let me know if you'd like me to focus on any specific areas, or if there's additional data you need me to bring. I can also invite the finance team representative if that would be helpful.

Looking forward to the discussion.

Best regards,
[User]
```

### Response Generation Result
```json
{
  "response_text": "Hi Alice,\n\nYes, I can attend...",
  "length": "Brief",
  "tone": "Professional",
  "template": "Meeting Acceptance",
  "word_count": 12,
  "processing_time_ms": 2847,
  "model_version": "llama3.1:8b-instruct-q4_K_M",
  "edit_percentage": 0.15,
  "accepted": true,
  "regeneration_count": 0
}
```

---

## Questions & Decisions

**Q: How many sent emails needed for accurate style analysis?**
**A:** Minimum 20, optimal 50+ emails. System adapts incrementally as more emails are analyzed.

**Q: What if user has no sent items folder?**
**A:** Use default professional style profile. Update profile as user edits generated responses.

**Q: Should we support custom templates?**
**A:** Not in MVP. Eight pre-built templates cover 80% of scenarios. Custom templates in future version.

**Q: How to handle offensive or inappropriate LLM responses?**
**A:** Content filtering layer checks generated response. If flagged, regenerate with stricter prompt. Always show to user for final approval.

**Q: What if LLM generates very poor response?**
**A:** User can regenerate or edit freely. Track regeneration rate as quality metric. Tune prompts if rate >20%.

**Q: Should style profile sync across devices?**
**A:** Not in MVP (local-only). Cloud sync in future version for multi-device users.

---

## Related Documentation

- Story 1.1 (COMPLETE): OllamaManager for LLM inference
- Story 1.2 (COMPLETE): EmailPreprocessor for email parsing
- Story 1.3 (COMPLETE): EmailAnalysisEngine for email understanding
- Story 1.4 (COMPLETE): PriorityClassifier for priority context
- PRD Section 5.3: Response Generation
- PRD Section 5.4: AI Writing Style Learning
- epic-stories.md: Full epic context

---

## Story Lifecycle

**Created:** 2025-10-13 (Moved from BACKLOG to TODO after Story 1.4 completion)
**Started:** [To be filled when implementation begins]
**Completed:** [To be filled when DoD met]

---

_This story completes the AI-powered email intelligence loop by adding response generation capabilities. Users can now analyze emails AND draft contextual responses, all offline with full privacy. The system learns from user's writing style to generate authentic responses that sound like them._

## Dev Agent Record

### Context Reference

- Context File: `docs/stories/story-context-1.5.xml` (Generated: 2025-10-13)

### Agent Model Used

(To be filled by DEV agent)

### Debug Log References

### Completion Notes List

### File List
