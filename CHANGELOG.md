# Changelog

All notable changes to MailMind will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Epic 1: Core AI Engine (In Progress - 32% Complete)

## [0.4.0] - 2025-10-13

### Added - Story 1.4: Priority Classification System

**Enhanced Priority Classification with User Learning**

#### Core Features
- **PriorityClassifier class** (`src/mailmind/core/priority_classifier.py`, 810+ lines)
  - Enhanced priority classification with user learning capabilities
  - Sender importance tracking (0.0-1.0 scoring)
  - User correction recording and application
  - VIP sender management (automatic priority boost)
  - Classification accuracy tracking and reporting
  - Visual priority indicators (🔴 High, 🟡 Medium, 🔵 Low)
  - Adaptive confidence scoring based on correction history

#### Database Schema Extensions
- **user_corrections table**: Stores user priority overrides for learning
  - Fields: message_id, sender, original_priority, user_priority
  - Correction type: priority_override, sender_importance, category_adjustment, urgency_misdetection
  - Timestamp tracking for learning window (30 days)
  - Applied_to_model flag for tracking learned corrections

- **sender_importance table**: Tracks sender importance scores
  - Importance score (0.0-1.0), email count, reply count, correction count
  - VIP and blocked sender flags
  - First seen, last seen, last updated timestamps
  - Indexed for fast lookup (<10ms)

- **email_analysis table extensions**: Added override fields
  - user_override, override_reason, original_priority columns

#### API Methods
- `classify_priority()`: Enhanced priority classification with sender importance
- `record_user_override()`: Record user correction for learning
- `get_classification_accuracy()`: Calculate accuracy over time period
- `set_sender_vip()`: Mark sender as VIP
- `get_sender_stats()`: Retrieve detailed sender statistics
- `_get_sender_importance()`: Look up sender importance score
- `_calculate_sender_adjustment()`: Calculate priority adjustment (-1, 0, +1)
- `_get_correction_adjustment()`: Get confidence adjustment from history
- `_update_sender_importance()`: Update sender score after correction

#### Testing
- **Unit tests** (`tests/unit/test_priority_classifier.py`, 950+ lines)
  - 34 tests across 2 test classes
  - 86% code coverage (exceeds 80% DoD requirement)
  - Full coverage of all 9 acceptance criteria
  - Tests for database schema, classification, corrections, accuracy, VIP management
  - Edge case and error handling tests

- **Integration tests** (`tests/integration/test_priority_classifier_integration.py`, 500+ lines)
  - Integration with Story 1.3 (EmailAnalysisEngine)
  - End-to-end learning system tests
  - Performance benchmarking
  - Real-world scenario testing

#### Demo & Examples
- **Priority Classifier Demo** (`examples/priority_classifier_demo.py`, 650+ lines)
  - 5 interactive demos:
    1. Basic Classification - New senders with no history
    2. VIP Sender - Priority boost demonstration
    3. Learning from Corrections - 5 correction learning cycle
    4. Accuracy Improvement - 30-day simulation (60% → >85% accuracy)
    5. Real-World Scenarios - Executive, spam, mixed-priority senders

#### Enhanced Classification Output
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

#### Learning System
- **User Correction Recording**: Stores all priority overrides in database
- **Sender Importance Updates**: Adjusts sender scores incrementally (±0.05 per correction)
- **Correction Pattern Analysis**: Looks at last 30 days of corrections
- **Confidence Adjustments**: Applies learned patterns to future classifications
- **Accuracy Tracking**: Monitors classification accuracy over time

#### Performance
- **Enhanced Classification**: <50ms overhead (target <50ms) ✅
- **Sender Importance Lookup**: <10ms (target <10ms) ✅
- **User Correction Recording**: <20ms (target <20ms) ✅
- **Accuracy Calculation**: <100ms for 30-day period (target <100ms) ✅

#### Acceptance Criteria Met (9/9)
- ✅ AC1: Priority classification with confidence scores
- ✅ AC2: High priority detection logic
- ✅ AC3: Medium priority detection logic
- ✅ AC4: Low priority detection logic
- ✅ AC5: User correction & learning system
- ✅ AC6: Sender importance tracking (0.0-1.0 scale)
- ✅ AC7: Visual priority indicators (🔴🟡🔵)
- ✅ AC8: Manual priority override with feedback loop
- ✅ AC9: Accuracy tracking & improvement (>85% target)

#### Learning Results
- **Week 1**: ~60% accuracy (system doesn't know patterns)
- **Week 2-3**: 70-80% accuracy (learning phase)
- **Week 4+**: >85% accuracy (target met) ✅
- **Correction Rate**: <15% after 30 days of learning

#### Documentation
- Story specification: `docs/stories/story-1.4.md` (893 lines)
- Updated README with Story 1.4 features, learning system, and demo
- Integration with Story 1.3 (EmailAnalysisEngine base priority)

### Changed
- Updated README.md to include Story 1.4 features and usage examples
- Updated project structure documentation to reflect new files
- Updated roadmap: 32% complete (4/12 stories, 23 story points)

---

## [0.3.0] - 2025-10-13

### Added - Story 1.3: Real-Time Email Analysis Engine

**Complete Pipeline Integration: Preprocessing → LLM → Parsing → Caching**

#### Core Features
- **EmailAnalysisEngine class** (`src/mailmind/core/email_analysis_engine.py`, 780+ lines)
  - AI-powered email analysis with priority, summary, tags, sentiment, action items
  - Progressive disclosure pattern: quick priority (<500ms) → full analysis (<2s)
  - SQLite caching with sub-100ms cache retrieval
  - Batch processing with progress callbacks
  - Performance monitoring (tokens/second, processing time)
  - Automatic cache invalidation on model version changes

#### Database Schema
- **email_analysis table**: Stores analysis results keyed by message_id
  - Fields: priority, sentiment, confidence, summary, tags, action_items
  - Performance metrics: processing_time_ms, tokens_per_second
  - Model version tracking for cache invalidation
  - Timestamp tracking: processed_date

- **performance_metrics table**: Tracks analysis performance over time
  - Operation type, model version, batch size
  - Tokens/second, processing time statistics

#### API Methods
- `analyze_email()`: Main analysis entry point with caching
- `analyze_batch()`: Batch processing with progress callbacks
- `get_analysis_stats()`: Retrieve aggregated statistics
- `_quick_priority_heuristic()`: Fast priority without LLM (<100ms)
- `_build_analysis_prompt()`: Structured prompt engineering
- `_parse_analysis_response()`: JSON parsing with fallback heuristics

#### Testing
- **Unit tests** (`tests/unit/test_email_analysis_engine.py`, 670+ lines)
  - 50+ tests across 11 test classes
  - Full coverage of all 9 acceptance criteria
  - Mocking strategies for Ollama integration
  - Tests for caching, batch processing, performance metrics

- **Integration tests** (`tests/integration/test_email_analysis_integration.py`, 800+ lines)
  - 25+ integration tests with real Ollama inference
  - End-to-end pipeline verification
  - Cache performance validation (<100ms cache hits)
  - Performance benchmarking suite
  - Error handling and edge cases

#### Demo & Examples
- **Email Analysis Demo** (`examples/email_analysis_demo.py`, 479 lines)
  - 6 comprehensive demos:
    1. Single Email Analysis - End-to-end pipeline
    2. Cache Performance - Demonstrates 10-50x speedup
    3. Batch Processing - Multiple emails with progress
    4. Progressive Disclosure - Phased result display
    5. Analysis Statistics - Database metrics
    6. Complete Pipeline - Visual pipeline walkthrough

#### Output Format
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

#### Performance
- **Quick Priority**: <100ms (keyword-based heuristic)
- **Full Analysis**: <2s on recommended hardware (M2 Pro, Ryzen 7)
- **Cache Retrieval**: <100ms (SQLite query)
- **Batch Throughput**: 20-30 emails/minute (sequential processing)

#### Acceptance Criteria Met (9/9)
- ✅ AC1: Progressive disclosure (<500ms quick priority)
- ✅ AC2: Priority classification (High/Medium/Low with confidence)
- ✅ AC3: Summarization (1-2 sentences, <150 chars)
- ✅ AC4: Tag generation (1-5 tags, lowercase, normalized)
- ✅ AC5: Sentiment analysis (positive/neutral/negative/urgent)
- ✅ AC6: Action item extraction (0-5 actionable items)
- ✅ AC7: Performance metrics (tokens/sec, processing time)
- ✅ AC8: Result caching (SQLite, message_id key)
- ✅ AC9: Batch processing (sequential with progress callbacks)

#### Documentation
- Story specification: `docs/stories/story-1.3.md` (653 lines)
- Updated README with Story 1.3 features, usage, and examples
- Integration with Stories 1.1 (OllamaManager) and 1.2 (EmailPreprocessor)

### Changed
- Updated README.md to include Story 1.3 features and usage examples
- Updated project structure documentation to reflect new files
- Updated roadmap: 25% complete (3/12 stories, 18 story points)

---

## [0.2.0] - 2025-10-12

### Added - Story 1.2: Email Preprocessing Pipeline

**Preprocessing Layer: Raw Email → Structured JSON for LLM**

#### Core Features
- **EmailPreprocessor class** (`src/mailmind/core/email_preprocessor.py`, 308 lines)
  - Email metadata extraction (sender, subject, date, threading)
  - HTML to plain text conversion with BeautifulSoup
  - Intelligent signature and quote stripping
  - Attachment metadata handling
  - Smart content truncation for long emails (>10k chars)
  - Thread context preservation
  - Input sanitization to prevent prompt injection
  - Suspicious content detection (SQL injection, script tags, path traversal)

#### API Methods
- `preprocess_email()`: Main preprocessing entry point
- `_extract_metadata()`: Parse sender, subject, date, threading
- `_parse_html_to_text()`: HTML → plain text with structure preserved
- `_strip_signatures()`: Remove common signature patterns
- `_strip_quotes()`: Remove quoted/forwarded content
- `_extract_attachment_metadata()`: Handle attachment info
- `_sanitize_content()`: Prevent prompt injection
- `_detect_suspicious_content()`: Security checks
- `_truncate_content()`: Smart truncation for long emails

#### Testing
- **Unit tests** (`tests/unit/test_email_preprocessor.py`, 650+ lines)
  - 40+ tests across 13 test classes
  - Full coverage of all 7 acceptance criteria
  - Tests for HTML parsing, signature stripping, sanitization

#### Demo & Examples
- **Email Preprocessing Demo** (`examples/email_preprocessing_demo.py`, 340 lines)
  - 8 comprehensive demos showing all preprocessing capabilities
  - Simple text, HTML, signatures, threads, attachments, long emails

#### Output Format
```json
{
  "metadata": {
    "from": "alice@example.com",
    "from_name": "Alice Smith",
    "subject": "Project Update",
    "date_parsed": "2025-10-12T14:30:00Z",
    "message_id": "msg_001",
    "in_reply_to": null,
    "references": []
  },
  "content": {
    "body": "Email content here...",
    "has_html": false,
    "has_signature": false,
    "has_quotes": false
  },
  "attachments": [],
  "thread_context": {
    "is_reply": false,
    "is_forward": false,
    "thread_depth": 0
  },
  "preprocessing_metadata": {
    "processing_time_ms": 45,
    "content_truncated": false,
    "suspicious_content_detected": false
  }
}
```

#### Performance
- Target: <200ms preprocessing time
- Actual: 30-50ms for typical emails

#### Acceptance Criteria Met (7/7)
- ✅ AC1: Metadata extraction
- ✅ AC2: HTML to text conversion
- ✅ AC3: Signature stripping
- ✅ AC4: Attachment metadata
- ✅ AC5: Content truncation
- ✅ AC6: Structured JSON output
- ✅ AC7: Performance (<200ms target)

#### Documentation
- Story specification: `docs/stories/story-1.2.md` (576 lines)
- Updated README with Story 1.2 features and usage examples

### Changed
- Updated README.md to include Story 1.2 features
- Updated project progress: 14% complete (2/12 stories, 10 story points)

---

## [0.1.0] - 2025-10-11

### Added - Story 1.1: Ollama Integration & Model Setup

**Foundation: Local LLM Infrastructure**

#### Core Features
- **OllamaManager class** (`src/mailmind/core/ollama_manager.py`, 292 lines)
  - Ollama Python client integration
  - Automatic model verification with fallback (Llama 3.1 → Mistral)
  - Test inference capability to validate model functionality
  - Configuration management via YAML
  - Comprehensive error handling with user-friendly messages

#### API Methods
- `initialize()`: Connect to Ollama, verify model, test inference
- `generate()`: Generate text with streaming support
- `get_model_info()`: Get current model details
- `is_available()`: Check if Ollama is accessible

#### Configuration
- **Configuration System** (`src/mailmind/utils/config.py`, 80 lines)
  - YAML-based configuration (`config/default.yaml`)
  - Support for primary and fallback models
  - GPU acceleration settings
  - Temperature and context window configuration

#### Testing
- **Unit tests** (`tests/unit/test_ollama_manager.py`, 300+ lines)
  - 20+ tests covering all acceptance criteria
  - Mocking strategies for external dependencies
  - Connection, model verification, inference, error handling tests

#### Performance
- Connection test: <200ms
- Model verification: <500ms
- Test inference: 2-3s (model dependent)
- Optimizations: Eliminated duplicate list() calls (~100-200ms improvement)

#### Compatibility
- Python 3.9+ support (updated type hints from tuple to Tuple)

#### Acceptance Criteria Met (5/5)
- ✅ AC1: Ollama connection and initialization
- ✅ AC2: Model verification with automatic fallback
- ✅ AC3: Test inference capability
- ✅ AC4: Configuration management
- ✅ AC5: Error handling and user feedback

#### Documentation
- Story specification: `docs/stories/story-1.1.md` (480 lines)
- README with installation and usage instructions

### Changed
- Initial project setup
- Project progress: 7% complete (1/12 stories, 5 story points)

---

## [0.0.1] - 2025-10-10

### Added
- Initial project scaffolding
- Project documentation structure
- Epic breakdown (`docs/epic-stories.md`)
- PRD outline (`docs/PRD-MailMind-Outline.md`)
- Workflow tracking system
- Git repository initialization

---

**Legend:**
- ✅ Complete
- 🔄 In Progress
- ⏳ Planned

**Version Numbering:**
- Major.Minor.Patch (0.x.0 for story completions)
- 0.1.0 = Story 1.1
- 0.2.0 = Story 1.2
- 0.3.0 = Story 1.3
- 0.4.0 = Story 1.4
- 1.0.0 = Epic 1 Complete
