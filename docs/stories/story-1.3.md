# Story 1.3: Real-Time Analysis Engine (<2s)

**Epic:** Epic 1 - AI-Powered Email Intelligence
**Story ID:** 1.3
**Story Points:** 8
**Priority:** P0 (Critical Path)
**Status:** TODO
**Created:** 2025-10-13

---

## Story Description

As a user, I need instant AI analysis of each email (priority, summary, categories) in under 2 seconds so that I can quickly triage my inbox.

## Business Value

This story creates the core email intelligence capability that differentiates MailMind:
- Real-time email analysis enables fast inbox triage (100-200 emails/day)
- Priority classification helps users focus on what matters most
- AI-generated summaries save time reading long emails
- Automatic action item extraction ensures nothing falls through cracks
- Sentiment analysis provides emotional context at a glance
- All processing happens locally, maintaining absolute privacy

Without this story, MailMind is just email preprocessing - this adds the intelligence.

---

## Acceptance Criteria

### AC1: Progressive Disclosure for Fast Perception
- [ ] Priority indicator displayed in <500ms (basic classification)
- [ ] Summary generated and displayed in <2s (2-3 sentences)
- [ ] Full analysis completed in <3s (tags, sentiment, action items)
- [ ] Display partial results as they become available
- [ ] Show loading indicators for pending analysis components

### AC2: Priority Classification
- [ ] Generate priority: High, Medium, or Low
- [ ] Include confidence score (0.0 - 1.0)
- [ ] Confidence >0.8 for High priority recommendations
- [ ] Classification based on:
  - Urgency keywords (ASAP, urgent, deadline, critical)
  - Sender importance (executives, direct manager, VIPs)
  - Action requirements (please review, need your input)
  - Deadlines and time constraints
  - Thread context (reply to important thread)

### AC3: Email Summarization
- [ ] Generate 2-3 sentence summary of email content
- [ ] Summary captures key points and main ask/purpose
- [ ] Summary written in clear, concise language
- [ ] Preserve critical details (names, dates, amounts)
- [ ] Handle long emails (>2000 chars) with better summarization

### AC4: Topic/Tag Extraction
- [ ] Extract up to 5 relevant tags/topics
- [ ] Tags are single words or short phrases (1-3 words)
- [ ] Tags cover: project names, departments, action types, subjects
- [ ] Remove generic tags (email, message, update)
- [ ] Tags are lowercase and normalized

### AC5: Sentiment Analysis
- [ ] Identify sentiment: positive, neutral, negative, or urgent
- [ ] "Urgent" for time-sensitive emails regardless of tone
- [ ] "Positive" for appreciation, agreement, good news
- [ ] "Neutral" for standard business communications
- [ ] "Negative" for complaints, concerns, bad news
- [ ] Sentiment helps prioritize response timing

### AC6: Action Item & Deadline Extraction
- [ ] Extract explicit action items from email body
- [ ] Detect imperative verbs: review, approve, send, schedule, etc.
- [ ] Extract mentioned deadlines and dates
- [ ] Format action items as clear, actionable statements
- [ ] Return empty list if no clear actions detected
- [ ] Limit to 5 most important action items

### AC7: Performance Monitoring
- [ ] Log processing time for each analysis
- [ ] Calculate and display tokens per second
- [ ] Track model used for analysis
- [ ] Log hardware profile at analysis time
- [ ] Store metrics in performance_metrics table

### AC8: Result Caching
- [ ] Cache analysis results in SQLite (email_analysis table)
- [ ] Use message_id as cache key
- [ ] Check cache before running LLM analysis
- [ ] Cache hits return results in <100ms
- [ ] Include model version in cache for invalidation
- [ ] Cache persists across application restarts

### AC9: Batch Processing Queue
- [ ] Support queuing multiple emails for analysis
- [ ] Process queue in background with progress tracking
- [ ] Display queue depth and current processing status
- [ ] Allow cancellation of queued analyses
- [ ] Target throughput: 10-15 emails/minute on recommended hardware
- [ ] Throttle to prevent system overload

---

## Technical Notes

### Dependencies
- **Story 1.1:** OllamaManager (LLM inference) ✅ COMPLETE
- **Story 1.2:** EmailPreprocessor (email → structured input) ✅ COMPLETE
- **SQLite:** For caching (table schema provided below)

### Architecture Overview

```
Raw Email
    ↓
EmailPreprocessor (Story 1.2)
    ↓
Structured Email Data (JSON)
    ↓
AnalysisEngine (Story 1.3) ← Check cache first
    ↓
LLM Prompt Construction
    ↓
OllamaManager.generate() (Story 1.1)
    ↓
Parse LLM Response
    ↓
Structured Analysis Result (JSON)
    ↓
Cache in SQLite
    ↓
Return to caller
```

### Prompt Engineering Strategy

**System Prompt:**
```
You are an email analysis assistant. Analyze the email and provide structured output.
Be concise, accurate, and focus on actionable information.
```

**Analysis Prompt Template:**
```
Analyze this email and provide:
1. Priority (High/Medium/Low) with confidence (0.0-1.0)
2. 2-3 sentence summary
3. Up to 5 relevant tags/topics
4. Sentiment (positive/neutral/negative/urgent)
5. Action items with deadlines

Email Metadata:
From: {from}
Subject: {subject}
Date: {date}

Email Body:
{body}

Return ONLY valid JSON:
{
  "priority": "High|Medium|Low",
  "confidence": 0.92,
  "summary": "...",
  "tags": ["tag1", "tag2"],
  "sentiment": "positive|neutral|negative|urgent",
  "action_items": ["Action 1 by Friday", "Action 2"]
}
```

### Progressive Disclosure Implementation

**Phase 1 (< 500ms):** Quick Priority
```python
# Use fast heuristic for instant priority
priority = quick_priority_heuristic(email)
display_priority_indicator(priority)

# Start LLM analysis in background
analysis_future = async_analyze_email(email)
```

**Phase 2 (< 2s):** Summary
```python
# Wait for LLM to generate summary
result = await analysis_future
display_summary(result['summary'])
```

**Phase 3 (< 3s):** Full Analysis
```python
# Display remaining analysis components
display_tags(result['tags'])
display_sentiment(result['sentiment'])
display_action_items(result['action_items'])
```

### Performance Optimization

1. **Prompt Optimization:**
   - Keep prompts concise (<500 tokens)
   - Use structured output format (JSON)
   - Avoid unnecessary context

2. **Model Parameters:**
   - Temperature: 0.3 (deterministic)
   - Max tokens: 500 (analysis is concise)
   - Stop sequences: `}` (end of JSON)

3. **Caching Strategy:**
   - Always check cache first (saves 2s per cached email)
   - Cache indefinitely (disk is cheap)
   - Invalidate cache on model version change

4. **Batch Processing:**
   - Queue emails for background processing
   - Process sequentially to avoid GPU thrashing
   - Display progress with estimated time remaining

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS email_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    subject TEXT,
    sender TEXT,
    received_date DATETIME,

    -- Analysis results (JSON string)
    analysis_json TEXT NOT NULL,

    -- Denormalized fields for fast queries
    priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')),
    sentiment TEXT CHECK(sentiment IN ('positive', 'neutral', 'negative', 'urgent')),
    confidence_score REAL,

    -- Performance tracking
    processing_time_ms INTEGER,
    tokens_per_second REAL,
    model_version TEXT,
    hardware_profile TEXT,

    -- Metadata
    processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    cache_hit BOOLEAN DEFAULT 0,

    -- Indexes
    INDEX idx_message_id (message_id),
    INDEX idx_priority (priority),
    INDEX idx_processed_date (processed_date)
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,  -- 'email_analysis', 'batch_processing', etc.
    hardware_config TEXT,
    model_version TEXT,
    tokens_per_second REAL,
    memory_usage_mb INTEGER,
    processing_time_ms INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Implementation Approach

```python
class EmailAnalysisEngine:
    def __init__(self, ollama_manager: OllamaManager, db_path: str):
        self.ollama = ollama_manager
        self.preprocessor = EmailPreprocessor()
        self.db = sqlite3.connect(db_path)
        self._init_db()

    def analyze_email(self, raw_email: Any,
                     use_cache: bool = True) -> Dict[str, Any]:
        """
        Analyze email with LLM and return structured results.

        Args:
            raw_email: Raw email in any supported format
            use_cache: Check cache before running analysis

        Returns:
            Analysis results dictionary
        """
        start_time = time.time()

        # Step 1: Preprocess email
        preprocessed = self.preprocessor.preprocess_email(raw_email)
        message_id = preprocessed['metadata']['message_id']

        # Step 2: Check cache
        if use_cache:
            cached = self._get_cached_analysis(message_id)
            if cached:
                cached['cache_hit'] = True
                return cached

        # Step 3: Quick priority heuristic (< 500ms target)
        quick_priority = self._quick_priority_heuristic(preprocessed)

        # Step 4: Build LLM prompt
        prompt = self._build_analysis_prompt(preprocessed)

        # Step 5: Generate analysis with LLM
        response = self.ollama.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=500
        )

        # Step 6: Parse LLM response
        analysis = self._parse_analysis_response(response)

        # Step 7: Add metadata
        processing_time = int((time.time() - start_time) * 1000)
        analysis['processing_time_ms'] = processing_time
        analysis['tokens_per_second'] = self._calculate_tokens_per_sec(response)
        analysis['cache_hit'] = False

        # Step 8: Cache results
        self._cache_analysis(message_id, preprocessed, analysis)

        # Step 9: Log performance
        self._log_performance(analysis)

        return analysis

    def _quick_priority_heuristic(self, email: Dict) -> str:
        """Fast priority classification without LLM."""
        body = email['content']['body'].lower()
        subject = email['metadata']['subject'].lower()

        # High priority indicators
        if any(word in body or word in subject for word in
               ['urgent', 'asap', 'critical', 'emergency', 'immediately']):
            return 'High'

        # Check for deadlines
        if any(word in body for word in ['deadline', 'due', 'by end of']):
            return 'High'

        # Medium priority default for replies
        if email['thread_context']['is_reply']:
            return 'Medium'

        # Low priority default
        return 'Low'

    def _build_analysis_prompt(self, email: Dict) -> str:
        """Build LLM prompt from preprocessed email."""
        metadata = email['metadata']
        content = email['content']

        prompt = f"""Analyze this email and provide structured output.

Email Metadata:
From: {metadata['from']}
Subject: {metadata['subject']}
Date: {metadata['date']}

Email Body:
{content['body']}

Provide analysis in JSON format:
{{
  "priority": "High|Medium|Low",
  "confidence": 0.92,
  "summary": "2-3 sentence summary here",
  "tags": ["tag1", "tag2", "tag3"],
  "sentiment": "positive|neutral|negative|urgent",
  "action_items": ["Action 1", "Action 2"]
}}
"""
        return prompt

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response into structured analysis."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
            else:
                # Fallback parsing if no JSON found
                analysis = self._fallback_parse(response)

            # Validate and normalize
            analysis.setdefault('priority', 'Medium')
            analysis.setdefault('confidence', 0.5)
            analysis.setdefault('summary', 'No summary available')
            analysis.setdefault('tags', [])
            analysis.setdefault('sentiment', 'neutral')
            analysis.setdefault('action_items', [])

            return analysis

        except Exception as e:
            logger.error(f"Failed to parse analysis: {e}")
            return self._default_analysis()

    def analyze_batch(self, emails: List[Any],
                     callback: Optional[Callable] = None) -> List[Dict]:
        """
        Analyze multiple emails in batch.

        Args:
            emails: List of raw emails
            callback: Optional progress callback(current, total, result)

        Returns:
            List of analysis results
        """
        results = []
        total = len(emails)

        for i, email in enumerate(emails):
            result = self.analyze_email(email)
            results.append(result)

            if callback:
                callback(i + 1, total, result)

        return results
```

---

## Testing Checklist

### Unit Tests
- [ ] Test EmailAnalysisEngine initialization
- [ ] Test quick priority heuristic logic
- [ ] Test prompt building from preprocessed email
- [ ] Test LLM response parsing (valid JSON)
- [ ] Test LLM response parsing (invalid JSON fallback)
- [ ] Test cache check logic
- [ ] Test cache storage
- [ ] Test performance metric logging
- [ ] Test batch processing
- [ ] Test error handling for failed LLM calls

### Integration Tests
- [ ] Test full analysis pipeline (preprocessing → LLM → caching)
- [ ] Test with real Ollama inference (requires Ollama running)
- [ ] Test with various email types (short, long, HTML, threads)
- [ ] Test cache hits (2nd analysis should be <100ms)
- [ ] Test batch processing with 10+ emails
- [ ] Test with different hardware configurations
- [ ] Test memory usage during batch processing

### Performance Tests
- [ ] Simple email analysis <2s (recommended hardware)
- [ ] Complex email analysis <3s (recommended hardware)
- [ ] CPU-only analysis <5s (minimum hardware)
- [ ] Cache hits <100ms
- [ ] Batch processing 10-15 emails/minute
- [ ] Memory usage <8GB with model loaded

### Edge Cases
- [ ] Email with no clear priority indicators
- [ ] Email with no action items
- [ ] Very long email (>10k chars, already truncated by preprocessor)
- [ ] Email thread with 20+ previous messages
- [ ] Malformed LLM response (invalid JSON)
- [ ] LLM timeout or error
- [ ] Database write failure
- [ ] Concurrent analysis requests

---

## Performance Targets

| Hardware Tier | Target Time | Acceptable Time | Critical Time |
|--------------|-------------|-----------------|---------------|
| **Optimal** (high-GPU) | <1s | <2s | <3s |
| **Recommended** (mid-GPU) | <2s | <3s | <5s |
| **Minimum** (CPU-only) | <5s | <8s | <10s |

**Cache Performance:**
- Cache hit: <100ms ✅ (must be fast)
- Cache miss: Follow hardware tier targets

**Batch Processing:**
- Optimal: 20-30 emails/minute
- Recommended: 10-15 emails/minute
- Minimum: 5-10 emails/minute

---

## Definition of Done

- [ ] All acceptance criteria met (AC1-AC9)
- [ ] EmailAnalysisEngine class implemented
- [ ] Integration with OllamaManager (Story 1.1) complete
- [ ] Integration with EmailPreprocessor (Story 1.2) complete
- [ ] Database schema created and tested
- [ ] Caching logic implemented and tested
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration tests with real Ollama passing
- [ ] Performance targets met on recommended hardware
- [ ] Batch processing implemented and tested
- [ ] Error handling for all failure modes
- [ ] Code reviewed and approved
- [ ] Documentation updated:
  - Module docstrings complete
  - API documentation for EmailAnalysisEngine
  - Example usage in README
- [ ] Demo script created showing analysis pipeline
- [ ] Performance metrics logged and verified

---

## Dependencies & Blockers

**Upstream Dependencies:**
- Story 1.1 (Ollama Integration) - COMPLETE ✅
- Story 1.2 (Email Preprocessing) - COMPLETE ✅

**Downstream Dependencies:**
- Story 1.4 (Priority Classification) can enhance priority logic
- Story 1.5 (Response Generation) will use analysis results
- Story 1.6 (Performance Optimization) will optimize this engine
- Story 2.2 (SQLite Database) provides production database schema
- Story 2.3 (UI) will display analysis results

**External Dependencies:**
- Ollama service running
- LLM model downloaded (Llama 3.1 8B or Mistral 7B)
- SQLite3 (Python stdlib)

**Potential Blockers:**
- LLM response quality varies - may need prompt tuning
- Performance targets challenging on CPU-only hardware
- JSON parsing may fail if LLM response is malformed

---

## Implementation Plan

### Phase 1: Core Analysis Engine (Day 1-2)
1. Create EmailAnalysisEngine class skeleton
2. Implement prompt building logic
3. Integrate OllamaManager for LLM inference
4. Implement response parsing (JSON → structured analysis)
5. Add basic error handling
6. Create database schema

### Phase 2: Caching & Performance (Day 2-3)
1. Implement SQLite caching logic
2. Add cache check before analysis
3. Store analysis results in database
4. Implement quick priority heuristic
5. Add performance metric logging
6. Test cache hit performance (<100ms)

### Phase 3: Progressive Disclosure & Batch (Day 3-4)
1. Implement progressive disclosure pattern
2. Add async analysis support
3. Implement batch processing queue
4. Add progress tracking for batches
5. Test throughput targets

### Phase 4: Testing & Polish (Day 4-5)
1. Write comprehensive unit tests
2. Write integration tests with real Ollama
3. Performance testing on different hardware
4. Prompt tuning for better results
5. Error handling improvements
6. Documentation and examples

---

## Output Format Example

### Successful Analysis
```json
{
  "priority": "High",
  "confidence": 0.92,
  "summary": "Budget overrun alert for Q4 project. Team lead requests immediate review of spending and meeting to discuss cost reduction strategies.",
  "tags": ["budget", "q4", "urgent", "project-alpha", "cost-reduction"],
  "sentiment": "urgent",
  "action_items": [
    "Review budget by Friday",
    "Schedule meeting with Alice to discuss cost reduction"
  ],
  "processing_time_ms": 1847,
  "tokens_per_second": 52.3,
  "model_version": "llama3.1:8b-instruct-q4_K_M",
  "cache_hit": false
}
```

### Cached Analysis (Fast Path)
```json
{
  "priority": "Medium",
  "confidence": 0.78,
  "summary": "Project status update. On track for Q4 delivery with minor adjustments needed.",
  "tags": ["project-update", "q4", "status", "on-track"],
  "sentiment": "neutral",
  "action_items": [],
  "processing_time_ms": 45,
  "tokens_per_second": null,
  "model_version": "llama3.1:8b-instruct-q4_K_M",
  "cache_hit": true
}
```

---

## Questions & Decisions

**Q: What if LLM returns invalid JSON?**
**A:** Implement fallback parsing with heuristics. Log warning and use default analysis structure.

**Q: Should we support streaming responses for progressive disclosure?**
**A:** Not in MVP. Streaming adds complexity. Use quick heuristic + full LLM analysis approach.

**Q: How to handle very slow hardware (>10s per email)?**
**A:** Display warning during onboarding. Suggest lighter model or hardware upgrade.

**Q: Should we cache failed analyses?**
**A:** No. Only cache successful analyses. Failures should be retryable.

**Q: How to validate LLM output quality?**
**A:** Manual review during development. Future: user feedback loop in Story 1.4.

---

## Related Documentation

- [Ollama Python Client Documentation](https://github.com/ollama/ollama-python)
- Story 1.1 (COMPLETE): OllamaManager implementation
- Story 1.2 (COMPLETE): EmailPreprocessor implementation
- PRD Section 5.2: AI Analysis Pipeline
- epic-stories.md: Full epic context

---

## Story Lifecycle

**Created:** 2025-10-13 (Moved from BACKLOG to TODO after Story 1.2 completion)
**Started:** [To be filled when implementation begins]
**Completed:** [To be filled when DoD met]

---

_This story is part of Epic 1: AI-Powered Email Intelligence. It integrates Stories 1.1 and 1.2 to create the core AI analysis capability that makes MailMind intelligent._
