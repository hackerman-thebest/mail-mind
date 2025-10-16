# MailMind - Sovereign AI Email Assistant

**Your AI, Your Data, Your Rules**

MailMind is a privacy-first desktop application that provides AI-powered email intelligence without sending data to the cloud. All AI processing happens locally on your machine using Ollama.

## Current Status

**Phase:** Implementation (Phase 4)
**Current Story:** 3.1 - Database Encryption Implementation ✅ IMPLEMENTED

## Features (Current)

### 🔒 Security Features

#### ✅ Story 3.1: Database Encryption (COMPLETE)

- **256-bit AES Encryption:** SQLCipher database encryption for all email data
- **Windows DPAPI Key Management:** Secure key storage tied to user account + machine
- **PBKDF2 Key Derivation:** 100,000 iterations with SHA-256 for additional security
- **Encryption by Default:** New installations automatically use encrypted databases
- **Migration Tools:** Convert between encrypted and unencrypted databases
- **Settings UI Integration:** Manage encryption from Privacy settings
- **Performance:** <5% overhead (typically 2-3%)
- **Automatic Backup:** Safe migration with automatic rollback on failure

**Encryption Architecture:**
- **Key Storage:** Windows Credential Manager (DPAPI-protected)
- **Key Derivation:** PBKDF2-HMAC-SHA256 with random salt
- **Database:** SQLCipher with 256-bit AES-CBC
- **Platform:** Windows 10/11 (macOS/Linux support planned for v2.0)

**User Control:**
```
Settings → Privacy → Database Encryption
• Encryption Status: Enabled/Disabled indicator
• Enable Encryption: Migrate unencrypted database
• Disable Encryption: Migrate to unencrypted (with warning)
• Progress Tracking: Real-time migration progress
```

**Security Documentation:** See [SECURITY.md](SECURITY.md) for complete encryption architecture

### 🤖 AI Features

### ✅ Story 1.1: Ollama Integration & Model Setup (COMPLETE)

- Ollama Python client integration
- Automatic model verification and fallback
- Support for Llama 3.1 8B and Mistral 7B models
- Configuration management via YAML
- Comprehensive error handling
- Full unit test coverage

### ✅ Story 1.2: Email Preprocessing Pipeline (COMPLETE)

- Email metadata extraction (sender, subject, date, threading)
- HTML to plain text conversion with structure preserved
- Intelligent signature and quote stripping
- Attachment metadata handling
- Smart content truncation for long emails (>10k chars)
- Structured JSON output for LLM consumption
- Thread context preservation
- Input sanitization to prevent prompt injection
- Performance: <200ms preprocessing target

### ✅ Story 1.3: Real-Time Email Analysis Engine (COMPLETE)

- **AI-Powered Analysis:** Priority classification, summarization, tags, sentiment, action items
- **Progressive Disclosure:** Quick priority in <500ms, full analysis in <2s
- **SQLite Caching:** Sub-100ms cache retrieval for analyzed emails
- **Batch Processing:** Analyze multiple emails with progress tracking
- **Performance Monitoring:** Tokens/second, processing time metrics
- **Complete Pipeline:** Preprocessing → LLM → Parsing → Caching
- **Robust Parsing:** JSON response parsing with fallback heuristics
- **Model Version Tracking:** Automatic cache invalidation on model changes

**Output Format:**
```json
{
  "priority": "High",
  "confidence": 0.92,
  "summary": "CFO reports Q4 budget overrun requiring immediate action",
  "tags": ["budget", "urgent", "financial", "deadline"],
  "sentiment": "urgent",
  "action_items": [
    "Review all pending expenses immediately",
    "Submit spending analysis by Friday COB"
  ],
  "processing_time_ms": 1847,
  "tokens_per_second": 52.3,
  "model_version": "llama3.1:8b-instruct-q4_K_M",
  "cache_hit": false
}
```

### ✅ Story 1.4: Priority Classification System (COMPLETE)

- **Enhanced Priority Classification:** Builds on Story 1.3 with user learning capabilities
- **Sender Importance Tracking:** Adaptive scoring (0.0-1.0) based on user behavior
- **User Correction Learning:** System learns from manual priority adjustments
- **VIP Sender Management:** Mark important senders for automatic priority boost
- **Visual Priority Indicators:** Color-coded emoji (🔴 High, 🟡 Medium, 🔵 Low)
- **Classification Accuracy Tracking:** Monitor and report accuracy over time (target: >85%)
- **Adaptive Confidence Scoring:** Confidence increases with correction history
- **Manual Priority Override:** Users can correct and teach the system
- **Performance:** <50ms overhead for enhanced classification

**Enhanced Classification Output:**
```json
{
  "priority": "High",
  "confidence": 0.94,
  "sender_importance": 0.85,
  "base_priority": "Medium",
  "adjustments": {
    "sender_adjustment": +1,
    "correction_adjustment": +0.15
  },
  "visual_indicator": "🔴",
  "classification_source": "enhanced_learning"
}
```

**Learning System:**
- Tracks user corrections in SQLite database
- Updates sender importance incrementally (±0.05 per correction)
- Applies correction patterns to future emails
- Accuracy improves from ~60% to >85% over 30 days
- Weights recent corrections (last 30 days) more heavily

### ✅ Story 1.5: Response Generation Assistant (COMPLETE)

- **AI-Powered Response Generation:** Generate contextual email responses using local LLM
- **Personal Style Learning:** Analyzes 20-50 sent emails to learn your writing patterns
- **Three Response Lengths:** Brief (<50 words), Standard (50-150 words), Detailed (150-300 words)
- **Four Tone Options:** Professional, Friendly, Formal, Casual
- **Eight Scenario Templates:** Meeting acceptance/decline, status updates, thank you, follow-up, etc.
- **Thread Context Awareness:** Incorporates last 5 messages for coherent responses
- **Style Integration:** Uses your greeting style, closing style, formality level, and common phrases
- **Performance Metrics:** Tracks generation time, word count, acceptance rate, edit percentage
- **Response Formatting:** Cleans markdown, removes signatures, formats naturally
- **Performance:** Brief <3s, Standard <5s, Detailed <10s on recommended hardware

**Writing Style Profile:**
```json
{
  "greeting_style": "Hi",
  "closing_style": "Thanks",
  "formality_level": 0.45,
  "common_phrases": ["let me know", "happy to", "looking forward"],
  "tone_markers": {
    "enthusiasm": 0.3,
    "directness": 0.6,
    "politeness": 0.7
  },
  "avg_sentence_length": 12.5
}
```

**Response Output:**
```json
{
  "response_text": "Hi John,\n\nThanks for reaching out about the project...",
  "length": "Standard",
  "tone": "Professional",
  "template": "Meeting Acceptance",
  "word_count": 87,
  "processing_time_ms": 2341,
  "model_version": "llama3.1:8b-instruct-q4_K_M"
}
```

## Prerequisites

### System Requirements

- **OS:** Windows 10/11 (Mac support planned for v2.0)
- **RAM:** 16GB minimum, 32GB recommended
- **Disk Space:** 10GB (including models)
- **GPU:** Optional but recommended for optimal performance

### Required Software

1. **Python 3.10+**
   - Download from https://www.python.org/downloads/

2. **Ollama**
   - Download from https://ollama.com/download
   - Install and ensure service is running

3. **AI Model (one of):**
   - Llama 3.1 8B (recommended): `ollama pull llama3.1:8b-instruct-q4_K_M`
   - Mistral 7B (fallback): `ollama pull mistral:7b-instruct-q4_K_M`

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mail-mind.git
cd mail-mind
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Ollama

Download and install Ollama from https://ollama.com/download

Verify installation:
```bash
ollama --version
```

### 4. Download AI Model

```bash
ollama pull llama3.1:8b-instruct-q4_K_M
```

This will download approximately 5GB of data.

## Usage

### Run the Application

```bash
python main.py
```

Expected output:
```
2025-10-13 - mailmind - INFO - Starting MailMind...
2025-10-13 - mailmind - INFO - Loading configuration...
2025-10-13 - ollama_manager - INFO - Attempting to connect to Ollama service...
2025-10-13 - ollama_manager - INFO - Connected to Ollama service in 0.123s
2025-10-13 - ollama_manager - INFO - Primary model verified: llama3.1:8b-instruct-q4_K_M
2025-10-13 - ollama_manager - INFO - Test inference successful in 2.456s
✓ Ollama initialization successful!
✓ Story 1.1 (Ollama Integration) complete!
```

### Email Preprocessing Demo

```bash
python examples/email_preprocessing_demo.py
```

This demonstrates:
- Simple plain text email preprocessing
- HTML email parsing
- Signature stripping
- Thread context extraction
- Attachment handling
- Long email truncation
- Suspicious content detection
- Complete structured JSON output

### Email Analysis Demo

```bash
python examples/email_analysis_demo.py
```

This comprehensive demo showcases:
1. **Single Email Analysis** - End-to-end pipeline with urgent budget email
2. **Cache Performance** - Demonstrates cache hit speedup (10-50x faster)
3. **Batch Processing** - Process multiple emails with progress tracking
4. **Progressive Disclosure** - Shows quick priority (<500ms) then full analysis
5. **Analysis Statistics** - Database stats and metrics visualization
6. **Complete Pipeline** - Visualizes all pipeline steps

Expected output:
```
======================================================================
DEMO 1: Single Email Analysis
======================================================================

1. Initializing Ollama...
✓ Ollama ready: llama3.1:8b-instruct-q4_K_M

2. Creating Email Analysis Engine...
✓ Engine ready

3. Analyzing email...
   From: alice@company.com (Alice Smith - CFO)
   Subject: URGENT: Q4 Budget Overrun - Action Required

✓ Analysis complete in 1.85s

======================================================================
ANALYSIS RESULTS
======================================================================

🔴 Priority: High (confidence: 0.92)

📊 Sentiment: urgent

📝 Summary:
   CFO reports Q4 budget overrun requiring immediate action

🏷️  Tags: budget, urgent, financial, deadline, action-required

✅ Action Items:
   1. Review all pending expenses immediately
   2. Identify cost reduction opportunities
   3. Schedule emergency budget meeting this week

⚡ Performance:
   Processing time: 1847ms
   Tokens/second: 52.3
   Model: llama3.1:8b-instruct-q4_K_M
   Cache hit: False
```

### Priority Classifier Demo

```bash
python examples/priority_classifier_demo.py
```

This interactive demo showcases the learning system (Story 1.4):
1. **Demo 1: Basic Classification** - New senders with no history
2. **Demo 2: VIP Sender** - Priority boost for VIP senders
3. **Demo 3: Learning from Corrections** - System learns from 5 user corrections
4. **Demo 4: Accuracy Improvement** - 30-day simulation showing accuracy improvement
5. **Demo 5: Real-World Scenarios** - Executive, spam, and mixed-priority senders

Expected output:
```
===================================================================
Demo 3: Learning from User Corrections
===================================================================

Simulating 5 emails from manager@company.com with user corrections...

Email 1:
🟡 From: manager@company.com - Task 1
   Priority: Medium (70% confident)
   Sender Importance: 0.50
   ❌ User corrected to: High

[... 4 more emails with corrections ...]

📊 Sender Importance After 5 Corrections:
   • Importance Score: 0.75
   • Correction Count: 5

Now classifying a NEW email from the same sender:

🔴 From: manager@company.com - New task assignment
   Priority: High (80% confident)
   Sender Importance: 0.75

📊 Observations:
   • After 5 upgrades, sender importance increased
   • System learned this sender is important
   • New emails automatically upgraded to High priority
   • No user correction needed - system learned the pattern!
```

### Response Generator Demo

```bash
python examples/response_generator_demo.py
```

This interactive demo showcases the response generation system (Story 1.5):
1. **Demo 1: Writing Style Analysis** - Analyze 5 sent emails, extract writing patterns
2. **Demo 2: Response Lengths** - Generate Brief/Standard/Detailed responses with performance timing
3. **Demo 3: Tone Variations** - Professional/Friendly/Formal/Casual tone examples
4. **Demo 4: Scenario Templates** - Meeting Acceptance/Status Update/Thank You templates
5. **Demo 5: Thread Context** - Multi-message conversation awareness
6. **Demo 6: Response Metrics** - Performance tracking and statistics

Expected output:
```
======================================================================
DEMO 1: Writing Style Analysis
======================================================================

Analyzing writing style from sent emails...

✓ Writing style profile created from 5 emails

Profile Details:
  Greeting Style: Hi
  Closing Style: Thanks
  Formality Level: 0.45 (0.0=casual, 1.0=formal)
  Avg Sentence Length: 12 words
  Common Phrases: thanks for, let me know, looking forward

Tone Markers:
  Enthusiasm: 0.30
  Directness: 0.60
  Politeness: 0.70

----------------------------------------------------------------------
DEMO 2: Response Lengths (Brief / Standard / Detailed)
----------------------------------------------------------------------

Original Email:
  From: John Smith
  Subject: Team Meeting Next Week

  Body:
  Hi Alice,

  I wanted to schedule a team meeting for next Tuesday at 2pm to
  discuss the Q4 roadmap and upcoming priorities.

  Would you be available?

  Thanks,
  John

----------------------------------------------------------------------
Brief Response
----------------------------------------------------------------------

Generated in 2.45s (2450ms)
Word count: 32

Response:
Hi John,

Thanks for reaching out. Yes, I'm available Tuesday at 2pm.
Looking forward to discussing Q4 priorities.

Thanks,
Alice

✓ Performance: EXCELLENT (under 3s target)
```

### Using the ResponseGenerator

```python
from src.mailmind.core.ollama_manager import OllamaManager
from src.mailmind.core.email_preprocessor import EmailPreprocessor
from src.mailmind.core.writing_style_analyzer import WritingStyleAnalyzer
from src.mailmind.core.response_generator import ResponseGenerator
from src.mailmind.utils.config import load_config, get_ollama_config

# Initialize Ollama
config = load_config()
ollama_config = get_ollama_config(config)
ollama = OllamaManager(ollama_config)
ollama.initialize()

# Analyze writing style from sent emails
sent_emails = [
    {'body': 'Hi John,\n\nThanks for reaching out...', 'subject': 'Re: Project'},
    # ... more sent emails (20-50 recommended)
]

analyzer = WritingStyleAnalyzer(db_path='data/mailmind.db')
profile = analyzer.analyze_sent_emails(sent_emails, profile_name='alice')

print(f"✓ Style profile created: {profile['greeting_style']}, {profile['closing_style']}")

# Generate response to incoming email
preprocessor = EmailPreprocessor()
generator = ResponseGenerator(ollama, db_path='data/mailmind.db')

incoming_email = preprocessor.preprocess_email({
    'from': 'john.smith@company.com',
    'subject': 'Team Meeting Next Week',
    'body': 'Hi Alice,\n\nI wanted to schedule a team meeting for next Tuesday at 2pm...',
    'date': '2025-10-13T10:00:00Z',
    'message_id': 'msg_001'
})

# Generate response with customization
result = generator.generate_response(
    incoming_email,
    length='Standard',        # Brief, Standard, or Detailed
    tone='Professional',      # Professional, Friendly, Formal, or Casual
    template='Meeting Acceptance'  # Optional: use scenario template
)

print(f"Response ({result['word_count']} words, {result['processing_time_ms']}ms):")
print(result['response_text'])

# Generate with thread context
thread = [previous_email_1, previous_email_2, previous_email_3]
result = generator.generate_response(
    incoming_email,
    length='Standard',
    tone='Professional',
    thread_context=thread  # Last 5 messages for context
)

# Get response metrics
metrics = generator.get_response_metrics(days=30)
print(f"Total responses: {metrics['total_generated']}")
print(f"Acceptance rate: {metrics.get('acceptance_rate_percent', 0):.1f}%")
```

### Using the WritingStyleAnalyzer

```python
from src.mailmind.core.writing_style_analyzer import WritingStyleAnalyzer

# Create analyzer
analyzer = WritingStyleAnalyzer(db_path='data/mailmind.db')

# Analyze sent emails
sent_emails = [
    {'body': 'Hi John,\n\nThanks for your email...', 'subject': 'Re: Meeting'},
    # ... 20-50 sent emails for best results
]

profile = analyzer.analyze_sent_emails(sent_emails, profile_name='default')

print(f"Greeting: {profile['greeting_style']}")
print(f"Closing: {profile['closing_style']}")
print(f"Formality: {profile['formality_level']:.2f}")
print(f"Common phrases: {', '.join(profile['common_phrases'][:5])}")

# Load existing profile
profile = analyzer.load_profile('default')

# Record edit feedback for improvement
analyzer.record_edit_feedback(
    message_id='msg_001',
    original_response='Original generated text...',
    edited_response='User-edited text...',
    profile_name='default'
)
```

### Using the EmailAnalysisEngine

```python
from src.mailmind.core.ollama_manager import OllamaManager
from src.mailmind.core.email_analysis_engine import EmailAnalysisEngine
from src.mailmind.utils.config import load_config, get_ollama_config

# Initialize Ollama
config = load_config()
ollama_config = get_ollama_config(config)
ollama = OllamaManager(ollama_config)
ollama.initialize()

# Create analysis engine
engine = EmailAnalysisEngine(ollama, db_path='data/mailmind.db')

# Analyze a single email
email = {
    'from': 'alice@example.com',
    'subject': 'URGENT: Need your review',
    'body': 'Please review the attached document ASAP.',
    'date': '2025-10-13T14:30:00Z',
    'message_id': 'msg_001'
}

analysis = engine.analyze_email(email)

print(f"Priority: {analysis['priority']}")
print(f"Summary: {analysis['summary']}")
print(f"Tags: {', '.join(analysis['tags'])}")
print(f"Action Items: {analysis['action_items']}")

# Analyze multiple emails in batch
emails = [email1, email2, email3]

def progress(current, total, result):
    print(f"[{current}/{total}] Analyzed: {result['priority']}")

results = engine.analyze_batch(emails, callback=progress)

# Get analysis statistics
stats = engine.get_analysis_stats()
print(f"Total analyses: {stats['total_analyses']}")
print(f"Cache hit rate: {stats['cache_hit_rate_percent']:.1f}%")
print(f"Avg processing time: {stats['avg_processing_time_ms']}ms")
```

### Using the EmailPreprocessor

```python
from src.mailmind.core.email_preprocessor import EmailPreprocessor

# Create preprocessor instance
preprocessor = EmailPreprocessor()

# Preprocess an email
email = {
    'from': 'alice@example.com',
    'subject': 'Test Email',
    'body': 'Email content here...',
    'date': '2025-10-13T14:30:00Z'
}

result = preprocessor.preprocess_email(email)

# Access structured output
print(f"From: {result['metadata']['from']}")
print(f"Body: {result['content']['body']}")
print(f"Processing time: {result['preprocessing_metadata']['processing_time_ms']}ms")
```

## Development

### Project Structure

```
mail-mind/
├── src/
│   └── mailmind/
│       ├── core/              # Core business logic
│       │   ├── ollama_manager.py            # Story 1.1: LLM integration
│       │   ├── email_preprocessor.py        # Story 1.2: Email preprocessing
│       │   ├── email_analysis_engine.py     # Story 1.3: AI analysis
│       │   ├── priority_classifier.py       # Story 1.4: Priority learning
│       │   ├── writing_style_analyzer.py    # Story 1.5: Style analysis
│       │   └── response_generator.py        # Story 1.5: Response generation
│       ├── ui/                # User interface (coming in Story 2.3)
│       ├── utils/             # Utilities
│       │   └── config.py
│       └── models/            # Data models
├── tests/
│   ├── unit/                  # Unit tests (140+ tests, >85% coverage)
│   │   ├── test_ollama_manager.py               # Story 1.1 tests
│   │   ├── test_email_preprocessor.py           # Story 1.2 tests
│   │   ├── test_email_analysis_engine.py        # Story 1.3 tests
│   │   ├── test_priority_classifier.py          # Story 1.4 tests (34 tests)
│   │   ├── test_writing_style_analyzer.py       # Story 1.5 tests (46 tests)
│   │   └── test_response_generator.py           # Story 1.5 tests (50 tests)
│   └── integration/           # Integration tests
│       ├── test_email_analysis_integration.py           # Story 1.3 integration
│       ├── test_priority_classifier_integration.py      # Story 1.4 integration
│       └── test_response_generation_integration.py      # Story 1.5 integration
├── examples/
│   ├── email_preprocessing_demo.py              # Story 1.2 demo
│   ├── email_analysis_demo.py                   # Story 1.3 demo (6 scenarios)
│   ├── priority_classifier_demo.py              # Story 1.4 demo (5 scenarios)
│   └── response_generator_demo.py               # Story 1.5 demo (6 scenarios)
├── config/
│   └── default.yaml           # Default configuration
├── data/
│   └── mailmind.db            # SQLite database (created at runtime)
├── docs/
│   ├── stories/               # Story files
│   │   ├── story-1.1.md       # Ollama Integration
│   │   ├── story-1.2.md       # Email Preprocessing
│   │   ├── story-1.3.md       # Email Analysis Engine
│   │   ├── story-1.4.md       # Priority Classification System
│   │   └── story-1.5.md       # Response Generation Assistant
│   ├── epic-stories.md        # Epic breakdown
│   └── project-workflow-status-2025-10-13.md
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
└── pytest.ini                 # Test configuration
```

### Running Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest --cov=src/mailmind --cov-report=html

# Run specific story tests
pytest tests/unit/test_ollama_manager.py                  # Story 1.1 tests
pytest tests/unit/test_email_preprocessor.py              # Story 1.2 tests
pytest tests/unit/test_email_analysis_engine.py           # Story 1.3 tests
pytest tests/unit/test_priority_classifier.py             # Story 1.4 tests (34 tests)
pytest tests/unit/test_writing_style_analyzer.py          # Story 1.5 tests (46 tests)
pytest tests/unit/test_response_generator.py              # Story 1.5 tests (50 tests)

# Run integration tests (requires Ollama running)
pytest tests/integration/test_email_analysis_integration.py -v
pytest tests/integration/test_priority_classifier_integration.py -v
pytest tests/integration/test_response_generation_integration.py -v

# Run specific test class
pytest tests/unit/test_email_analysis_engine.py::TestQuickPriorityHeuristic

# Run performance benchmarks
pytest tests/integration/test_email_analysis_integration.py::TestPerformanceBenchmark -v -s
```

### Configuration

Configuration is managed via YAML files in the `config/` directory.

**config/default.yaml:**
```yaml
ollama:
  primary_model: "llama3.1:8b-instruct-q4_K_M"
  fallback_model: "mistral:7b-instruct-q4_K_M"
  temperature: 0.3
  context_window: 8192
  gpu_acceleration: true
```

## Roadmap

### ✅ Completed (6/12 stories - 46% progress)

- **Story 1.1:** Ollama Integration & Model Setup (5 points) ✅
- **Story 1.2:** Email Preprocessing Pipeline (5 points) ✅
- **Story 1.3:** Real-Time Email Analysis Engine (8 points) ✅
- **Story 1.4:** Priority Classification System (5 points) ✅
- **Story 1.5:** Response Generation Assistant (8 points) ✅
- **Story 3.1:** Database Encryption Implementation (5 points) ✅

### 🔄 Next Up

- **Story 1.6:** Performance Optimization & Caching (5 points)

### Epic 2: Desktop Application

- **Story 2.1:** Outlook Integration (pywin32)
- **Story 2.2:** SQLite Database & Caching Layer
- **Story 2.3:** CustomTkinter UI Framework
- **Story 2.4:** Settings & Configuration System
- **Story 2.5:** Hardware Profiling & Onboarding Wizard
- **Story 2.6:** Error Handling, Logging & Installer

### Epic 3: Security & Privacy

- **Story 3.1:** Database Encryption Implementation (5 points) ✅ **COMPLETE**
- Story 3.2: Privacy-Preserving Analytics
- Story 3.3: Secure Configuration Management

## Error Handling & Logging (Story 2.6)

MailMind features comprehensive error handling and logging for production reliability.

### Automatic Error Recovery

**Ollama Connection (AC2):**
- Automatic retry with exponential backoff (1s → 2s → 4s → 8s → 16s)
- Up to 5 retry attempts for transient failures
- Automatic fallback from Llama 3.1 to Mistral if model unavailable

**Outlook Connection (AC2):**
- Automatic reconnection with retry logic
- Connection state tracking (Connected/Reconnecting/Disconnected)
- User-friendly error messages with actionable next steps

**Database Corruption (AC12):**
- Automatic detection and backup restoration
- Database integrity checking on startup
- Graceful degradation if restoration fails

**Memory Pressure (AC12):**
- Background memory monitoring (every 5 seconds)
- Automatic garbage collection at 85% memory threshold
- Batch size reduction under memory pressure

### Structured Logging (AC4)

**Log Format:**
```
[2025-10-15 14:32:15] INFO [module:function:line] message
```

**Log Rotation:**
- Maximum 10 files of 10MB each
- Automatic rotation when file size limit reached
- Platform-specific log directory:
  - Windows: `%APPDATA%\MailMind\logs\`
  - Mac: `~/Library/Application Support/MailMind/logs/`
  - Linux: `~/.local/share/MailMind/logs/`

**Log Levels:**
- `DEBUG` - Detailed diagnostic information
- `INFO` - Normal operation events
- `WARNING` - Unexpected but handled situations (fallbacks, retries)
- `ERROR` - Operation failures with recovery
- `CRITICAL` - Serious errors requiring attention

**Performance Metrics Logging:**
```python
[2025-10-15 14:32:15] INFO [logger:log_performance_metrics:350] PERFORMANCE: operation=email_analysis | duration_s=2.345 | tokens_per_sec=125.3 | memory_mb=456.7 | cache_hits=12
```

### Issue Reporting (AC6)

**Export Sanitized Logs:**
```python
from mailmind.core.logger import export_logs_to_clipboard

# Copy logs to clipboard for support (automatically sanitized)
success = export_logs_to_clipboard()
```

**Automatic Sanitization:**
- Email addresses → `[EMAIL]`
- Email subjects → `[SUBJECT]`
- Email bodies → `[BODY_REMOVED]`
- API keys → `[API_KEY]`

**UI Integration:**
- "Report Issue" button in Help menu
- One-click log export to clipboard
- Sanitized logs safe to share with support

### Error Messages (AC5)

All error messages follow the format: **"{What happened} {Why} {What to do next}"**

Examples:
- ✅ "MailMind requires Ollama to run AI features. Please download from https://ollama.ai/download and restart the application."
- ✅ "Insufficient memory detected (1.5GB available, 2.0GB recommended). For better performance, please close some applications."
- ✅ "Database corruption detected. Attempting to restore from backup... This may take a few moments."

### Developer Usage

**Error Handling:**
```python
from mailmind.core.error_handler import get_error_handler, retry

handler = get_error_handler()

try:
    risky_operation()
except Exception as e:
    user_message = handler.handle_exception(e, context={'operation': 'email_fetch'})
    show_error_dialog(user_message)

# Retry decorator for automatic recovery
@retry(max_retries=5, initial_delay=1.0, exceptions=(ConnectionError,))
def connect_to_service():
    return service.connect()
```

**Logging:**
```python
from mailmind.core.logger import setup_logging, get_logger, log_performance_metrics

# Setup (application startup)
setup_logging(log_level="INFO")

# Get logger for module
logger = get_logger(__name__)
logger.info("Operation completed successfully")
logger.error("Operation failed", exc_info=True)  # Include stack trace

# Log performance metrics
log_performance_metrics(
    operation="email_analysis",
    duration_seconds=2.5,
    tokens_per_second=125.3,
    memory_mb=512.3
)
```

### Documentation

**For Developers:**
- [Error Handling Patterns](docs/developer-guide/error-handling-patterns.md) - Complete developer guide with examples

**For Users:**
- [Troubleshooting Guide](docs/user-guide/troubleshooting.md) - User-friendly troubleshooting steps

## Troubleshooting

### Ollama Not Found

**Error:** `Failed to connect to Ollama service`

**Solution:**
1. Ensure Ollama is installed: https://ollama.com/download
2. Start Ollama service: `ollama serve`
3. Verify it's running: `ollama list`

**Recovery:** MailMind automatically retries connection up to 5 times with exponential backoff

### Model Not Available

**Error:** `Neither primary model nor fallback model are available`

**Solution:**
Download the model:
```bash
ollama pull llama3.1:8b-instruct-q4_K_M
```

**Recovery:** MailMind automatically falls back to Mistral if Llama unavailable

### Slow Performance

If AI inference is slow:
1. Check if GPU acceleration is working: Look for GPU detection in logs
2. Consider using a smaller model: `mistral:7b-instruct-q4_K_M`
3. Verify system meets minimum requirements (16GB RAM)

**Recovery:** MailMind automatically reduces memory usage under pressure

### Database Encryption Issues

**Error:** `Encryption unavailable (migration tools not found)`

**Solution:**
1. Ensure pysqlcipher3 is installed: `pip install pysqlcipher3`
2. Verify Windows 10/11 (DPAPI required for encryption)
3. Check Settings → Privacy → Database Encryption for status

**Error:** `Failed to unlock encrypted database`

**Solution:**
1. Database may be corrupted - restore from backup
2. Encryption key may be unavailable - check Windows Credential Manager
3. See [SECURITY.md](SECURITY.md) for key management details

**Recovery:** MailMind automatically creates backups before migration

### More Help

For comprehensive troubleshooting:
- **Security Guide:** [SECURITY.md](SECURITY.md) - Encryption architecture and security practices
- **FAQ:** [FAQ.md](FAQ.md) - Frequently asked questions
- **User Guide:** [docs/user-guide/troubleshooting.md](docs/user-guide/troubleshooting.md)
- **Developer Guide:** [docs/developer-guide/error-handling-patterns.md](docs/developer-guide/error-handling-patterns.md)
- **Report Issue:** Help → Report Issue (exports sanitized logs to clipboard)

## License

Copyright © 2025 MailMind Team. All rights reserved.

## Contributing

This project is currently in active development. Contributions will be welcome after v1.0 release.

## Support

For issues and questions:
- Check documentation in `docs/`
- Review story files in `docs/stories/`
- See workflow status in `docs/project-workflow-status-2025-10-13.md`

---

**Project Status:** 46% Complete (Phase 4 - Implementation)
**Stories Completed:** 6/12 (33 story points out of 72 total)
**Current Story:** 3.1 ✅ COMPLETE
**Next Story:** 1.6 - Performance Optimization & Caching

**Security:** 256-bit AES database encryption enabled by default. See [SECURITY.md](SECURITY.md) for details.
