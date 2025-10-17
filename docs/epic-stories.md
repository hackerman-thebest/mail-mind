# MailMind - Epic Breakdown

**Author:** Dawson
**Date:** 2025-10-13
**Project Level:** 2
**Target Scale:** 5-15 stories, 1-2 epics, focused PRD + solutioning handoff

---

## Epic Overview

MailMind is a Sovereign AI Email Assistant - a privacy-first desktop application that provides AI-powered email intelligence without sending data to the cloud. The MVP consists of four main epics:

0. **Epic 0: Setup & Reliability** - Build bulletproof installation with automatic resource detection, model selection, and self-healing diagnostics (Week 0-1, foundational)
1. **Epic 1: AI-Powered Email Intelligence** - Build the local LLM engine for real-time email analysis, response generation, and smart categorization
2. **Epic 2: Desktop Application & User Experience** - Create the Windows desktop application with Outlook integration, modern UI, and seamless onboarding
3. **Epic 3: Security & MVP Readiness** - Address security vulnerabilities and align marketing with implementation reality

**Development Timeline:** 9 weeks MVP (1 week Epic 0 + 8 weeks main epics)
**Target Users:** Privacy-conscious professionals (developers, executives, journalists, lawyers)
**Key Differentiator:** Absolute privacy through local AI processing with one-time purchase model

---

## Epic Details

### Epic 0: Setup & Reliability

**Epic Goal:** Build a bulletproof installation and diagnostic system that automatically detects system resources, selects appropriate AI models, and provides automated troubleshooting for common issues - ensuring 90%+ of users can successfully set up MailMind without manual intervention.

**Value Proposition:** Ensure users can actually install and run the product before they see the main features - addressing critical real-world blockers discovered during testing.

**Success Criteria:**
- Setup success rate >90% (currently ~30%)
- Model selection accuracy >95% (users get models that work on their systems)
- Diagnostic auto-fix rate >80% (issues resolved without manual steps)
- Time to first success <5 minutes
- Zero Unicode errors in diagnostics

**Key Stories:**
- Story 0.1: System Resource Detection & Model Recommendation (3 pts)
- Story 0.2: Interactive Model Selection in Setup Wizard (5 pts)
- Story 0.3: Unicode Error Fixes & Robust Subprocess Handling (2 pts)
- Story 0.4: Interactive Diagnostic Remediation Menu (5 pts)
- Story 0.5: Dynamic Model Loading & Runtime Switching (3 pts) - Nice to have

**Total Epic Points:** 18 points (excluding 0.5)
**Critical Path Points:** 10 points (Stories 0.1, 0.2, 0.3)

**Why This Epic Exists:**
Real-world testing revealed installation failures on 8GB RAM systems:
- 45-second timeout errors (model too large for system)
- Unicode decode crashes (Windows encoding issues)
- No resource-aware setup (assumes all users have 16GB+ RAM)
- Manual troubleshooting required (poor UX)

Without this epic, 50-70% of users will fail during setup and abandon the product.

**Full Epic Document:** [Epic_0_Setup_Reliability.md](Epic_0_Setup_Reliability.md)

---

### Epic 1: AI-Powered Email Intelligence

**Epic Goal:** Build the core local AI engine that analyzes emails in <2 seconds, generates contextual responses, and provides intelligent categorization - all running entirely offline on user hardware.

**Value Proposition:** Enable users to process 100-200 emails/day with AI assistance while maintaining absolute data privacy and zero ongoing costs.

**Success Criteria:**
- Email analysis completes in <2 seconds (interactive performance)
- Priority classification accuracy >85%
- Response generation completes in <5 seconds for standard replies
- Folder suggestion acceptance rate >75%
- Runs entirely offline with no network calls

**Dependencies:**
- Ollama installed and running locally
- Llama 3.1 8B quantized model (Q4_K_M) downloaded
- Hardware: Minimum 16GB RAM, recommended GPU for optimal performance

---

#### Story 1.1: Ollama Integration & Model Setup

**Story Description:**
As a developer, I need to integrate Ollama for local LLM inference so that the application can run AI models entirely offline on user hardware.

**Acceptance Criteria:**
- Ollama Python client integrated into application
- Automatic detection of Ollama installation on system startup
- Download and setup of Llama 3.1 8B Q4_K_M model if not present
- Fallback to Mistral 7B if Llama fails or insufficient hardware
- Configuration for model parameters (temperature: 0.3, context window: 8192 tokens)
- Graceful error handling if Ollama not installed with clear user instructions
- Model version tracking in database for compatibility

**Technical Notes:**
- Use Ollama Python SDK
- Model storage: ~5GB disk space
- Support CPU-only mode (slower) and GPU acceleration (recommended)

**Story Points:** 5
**Priority:** P0 (Critical Path)

---

#### Story 1.2: Email Preprocessing Pipeline

**Story Description:**
As a system, I need to preprocess raw emails into optimized format for LLM analysis so that inference is fast and token-efficient.

**Acceptance Criteria:**
- Extract email metadata (sender, subject, date, thread context)
- Parse HTML emails to plain text with structure preserved
- Handle attachments references without processing content
- Strip email signatures and quoted replies intelligently
- Truncate emails >10,000 characters with smart summarization
- Create structured prompt format for LLM consumption
- Preserve thread context for multi-email conversations
- Clean and sanitize input to prevent prompt injection

**Technical Notes:**
- Use BeautifulSoup for HTML parsing
- Email signature detection via heuristics
- Thread detection using In-Reply-To and References headers
- Target: Preprocessing in <200ms

**Story Points:** 5
**Priority:** P0 (Critical Path)

---

#### Story 1.3: Real-Time Analysis Engine (<2s)

**Story Description:**
As a user, I need instant AI analysis of each email (priority, summary, categories) in under 2 seconds so that I can quickly triage my inbox.

**Acceptance Criteria:**
- Progressive disclosure: Priority indicator in <500ms, summary in <2s, full analysis in <3s
- Generate priority classification: High/Medium/Low with confidence score
- Create 2-3 sentence email summary
- Extract up to 5 key topics/tags
- Identify sentiment (positive/neutral/negative/urgent)
- Extract action items and deadlines automatically
- Cache results in SQLite to avoid re-processing
- Display processing time and token generation speed in UI
- Queue multiple emails for batch processing with progress indicator

**Output Structure:**
```json
{
  "priority": "High",
  "confidence": 0.92,
  "summary": "Budget overrun alert for Q4 project...",
  "tags": ["budget", "deadline", "urgent", "project-alpha"],
  "sentiment": "urgent",
  "action_items": ["Review budget by Friday", "Schedule meeting with Alice"],
  "processing_time_ms": 1847,
  "tokens_per_second": 52.3
}
```

**Performance Targets:**
- Minimum Hardware (CPU-only): <5s analysis
- Recommended Hardware (mid-GPU): <2s analysis
- Optimal Hardware (high-GPU): <1s analysis

**Story Points:** 8
**Priority:** P0 (Critical Path)

---

#### Story 1.4: Priority Classification System

**Story Description:**
As a user, I need emails automatically classified by priority (High/Medium/Low) so that I can focus on what matters most.

**Acceptance Criteria:**
- Classify emails as High/Medium/Low priority with confidence score
- High priority indicators: urgency keywords, action required, executive senders, deadlines
- Medium priority: project updates, team communications, scheduled meetings
- Low priority: newsletters, automated notifications, marketing
- Learn from user corrections to improve accuracy over time
- Store correction feedback in user_corrections table
- Display priority visually with color coding (🔴🟡🔵)
- Allow manual priority override with feedback loop
- Target accuracy: >85% within 30 days of use

**Classification Logic:**
- Analyze sender importance (frequency, manual corrections)
- Detect urgency signals in subject/body
- Identify deadlines and action verbs
- Consider thread context and previous emails
- Weight recent corrections more heavily

**Story Points:** 5
**Priority:** P0 (Critical Path)

---

#### Story 1.5: Response Generation Assistant

**Story Description:**
As a user, I need AI to draft contextual email replies in my writing style so that I can respond faster to routine emails.

**Acceptance Criteria:**
- Generate responses in three lengths: Brief (<50 words), Standard (50-150 words), Detailed (150-300 words)
- Incorporate full email thread context for coherent replies
- Analyze user's sent items to match writing tone and style
- Provide response templates for common scenarios (meeting acceptance, status update, thank you, decline)
- Allow tone adjustment: Professional, Friendly, Formal, Casual
- Generate responses entirely offline in <5 seconds (standard length)
- Editable draft in UI before sending
- Track response generation metrics (time, acceptance rate, user edits)

**Response Time Targets:**
- Brief response: <3 seconds
- Standard response: <5 seconds
- Detailed response: <10 seconds

**Technical Notes:**
- Use few-shot prompting with sent email examples
- Store user's writing patterns in preferences
- Progressive refinement based on user edits

**Story Points:** 8
**Priority:** P0 (Critical Path)

---

#### Story 1.6: Performance Optimization & Caching

**Story Description:**
As a system, I need intelligent caching and optimization so that repeated operations are near-instant and system resources are managed efficiently.

**Acceptance Criteria:**
- SQLite cache for all email analysis results with message_id key
- Cache hit returns results in <100ms
- Store analysis results with model version for cache invalidation
- Hardware profiling on startup to select optimal model configuration
- Automatic detection of CPU/GPU and memory availability
- Display real-time performance metrics: tokens/sec, memory usage, processing time
- Queue management for batch email processing (10-15 emails/minute target)
- Graceful degradation under memory pressure
- Log performance metrics to database for trend analysis
- Memory usage cap: <8GB RAM with model loaded

**Cache Strategy:**
- Cache all analysis results indefinitely
- Invalidate cache if model version changes
- Provide manual cache clear option in settings

**Hardware Profiler:**
```python
{
  "cpu_cores": 8,
  "ram_available_gb": 24,
  "gpu_detected": "NVIDIA RTX 4060",
  "gpu_vram_gb": 8,
  "recommended_model": "llama3.1:8b-instruct-q4_K_M",
  "expected_tokens_per_second": 85
}
```

**Story Points:** 5
**Priority:** P1 (Important)

---

### Epic 2: Desktop Application & User Experience

**Epic Goal:** Create a polished Windows desktop application with Outlook integration, modern UI, and seamless onboarding that makes AI email management intuitive for non-technical users.

**Value Proposition:** Provide a professional desktop experience that feels native to Windows, integrates seamlessly with Outlook, and requires minimal technical knowledge to set up and use.

**Success Criteria:**
- Application starts in <10 seconds including model loading
- Outlook connection success rate >95%
- Onboarding completion rate >60%
- Settings persist correctly across sessions
- Installer works on clean Windows 10/11 systems
- Error recovery works for common failure modes
- User satisfaction >70% "fast enough" rating

**Dependencies:**
- Windows 10/11 OS
- Microsoft Outlook installed and configured
- Ollama installed separately (installer provides guidance)

---

#### Story 2.1: Outlook Integration (pywin32)

**Story Description:**
As a user, I need the application to connect to my Outlook account so that I can analyze and manage my emails directly from MailMind.

**Acceptance Criteria:**
- Connect to Outlook via pywin32 COM interface
- Fetch inbox emails with pagination support (50-100 at a time)
- Read email properties: subject, sender, body, received date, thread info
- Handle both HTML and plain text email formats
- Support common Outlook actions: Move to folder, Mark as read, Reply, Delete
- Automatic reconnection if Outlook loses connection
- Display connection status in UI (connected/disconnected)
- Graceful handling of Outlook not running or not installed
- Support multiple email accounts configured in Outlook

**Limitations (MVP):**
- pywin32 limitations: Folder pagination may be slow for >1000 emails
- Read-only access to sent items for tone analysis
- No calendar integration in MVP

**Technical Notes:**
- Use win32com.client for COM automation
- Implement retry logic with exponential backoff
- Cache folder structure for performance

**Story Points:** 8
**Priority:** P0 (Critical Path)

---

#### Story 2.2: SQLite Database & Caching Layer

**Story Description:**
As a system, I need a local database to store email analysis, user preferences, and performance metrics so that the application is fast and stateful.

**Acceptance Criteria:**
- SQLite database with schema: email_analysis, performance_metrics, user_preferences, user_corrections
- Optional database encryption for sensitive analysis data
- Fast queries: <100ms for all operations
- Automatic database creation on first run
- Database indexes for common queries (message_id, received_date, priority)
- Backup and restore functionality
- Database migration support for future versions
- Complete data deletion on uninstall
- Database size monitoring with alerts if >1GB

**Database Schema:**
```sql
CREATE TABLE email_analysis (
  id INTEGER PRIMARY KEY,
  message_id TEXT UNIQUE NOT NULL,
  subject TEXT,
  sender TEXT,
  received_date DATETIME,
  analysis_json TEXT,
  priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')),
  suggested_folder TEXT,
  confidence_score REAL,
  processing_time_ms INTEGER,
  model_version TEXT,
  hardware_profile TEXT,
  processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  user_feedback TEXT
);

CREATE TABLE performance_metrics (
  id INTEGER PRIMARY KEY,
  hardware_config TEXT,
  model_version TEXT,
  tokens_per_second REAL,
  memory_usage_mb INTEGER,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_preferences (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  default_value TEXT,
  updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_corrections (
  id INTEGER PRIMARY KEY,
  message_id TEXT,
  original_suggestion TEXT,
  user_choice TEXT,
  correction_type TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Story Points:** 5
**Priority:** P0 (Critical Path)

---

#### Story 2.3: CustomTkinter UI Framework

**Story Description:**
As a user, I need a modern, intuitive desktop interface so that I can easily view email analysis, generate responses, and manage my inbox.

**Acceptance Criteria:**
- Modern UI using CustomTkinter framework with dark/light theme support
- Main window layout: Folder sidebar, Email list, Analysis panel
- Email list view with visual priority indicators (🔴🟡🔵) and timestamps
- Analysis panel: Progressive disclosure (priority → summary → full analysis)
- Response editor with draft generation button and tone controls
- Real-time performance indicators: Token speed, processing time, queue depth
- Status bar: Ollama status, Outlook connection, processing queue count
- Responsive layout with resizable panels
- Keyboard shortcuts for common actions
- Progress indicators for long-running operations
- Toast notifications for completed actions

**UI Components:**
- EmailListView: Scrollable list with virtual rendering for performance
- AnalysisPanel: Expandable sections for progressive disclosure
- ResponseEditor: Text editor with formatting options
- SettingsDialog: Tabbed interface for preferences
- HardwareProfiler: Visual display of detected hardware
- ProgressQueue: Background task indicator

**Story Points:** 8
**Priority:** P0 (Critical Path)

---

#### Story 2.4: Settings & Configuration System

**Story Description:**
As a user, I need a settings interface to customize the application behavior so that it works according to my preferences.

**Acceptance Criteria:**
- Settings dialog with tabs: General, AI Model, Performance, Privacy, Advanced
- General settings: Theme (dark/light), startup behavior, notifications
- AI Model settings: Model selection (Llama/Mistral), temperature, response length defaults
- Performance settings: Batch size, cache size limit, hardware optimization toggles
- Privacy settings: Telemetry opt-in (default: off), crash reports, usage logging
- Advanced settings: Database location, log level, debug mode
- All settings stored in user_preferences table
- Settings changes apply immediately without restart where possible
- Reset to defaults option with confirmation
- YAML config file backup for manual editing if needed

**Default Settings:**
```yaml
general:
  theme: "dark"
  startup_behavior: "minimize_to_tray"

ai_model:
  primary_model: "llama3.1:8b-instruct-q4_K_M"
  fallback_model: "mistral:7b-instruct-q4_K_M"
  temperature: 0.3
  context_window: 8192

performance:
  batch_size: 10
  cache_limit_mb: 500
  gpu_acceleration: "auto"

privacy:
  telemetry: false
  crash_reports: false
  local_logging: true
```

**Story Points:** 5
**Priority:** P1 (Important)

---

#### Story 2.5: Hardware Profiling & Onboarding Wizard

**Story Description:**
As a new user, I need guided setup and clear performance expectations so that I can successfully configure MailMind for my hardware.

**Acceptance Criteria:**
- First-run onboarding wizard with 5 steps
- Step 1: Welcome and value proposition
- Step 2: Hardware detection with automatic profiling
- Step 3: Performance expectations based on detected hardware
- Step 4: Outlook connection test and troubleshooting
- Step 5: Initial email indexing with progress bar
- Hardware profiler displays: CPU, RAM, GPU, VRAM, recommended model
- Performance estimate: Expected tokens/second for detected hardware
- Clear messaging about hardware limitations and trade-offs
- Skippable tutorial of main features after setup
- Ability to re-run onboarding from settings

**Hardware Tiers:**
- Minimum (CPU-only, 16GB RAM): "Functional but slow (5-20 t/s)"
- Recommended (mid-GPU, 16-24GB RAM): "Fast and responsive (50-100 t/s)"
- Optimal (high-GPU, 32GB+ RAM): "Near-instant (100-200+ t/s)"

**Onboarding Flow:**
1. Welcome → 2. Hardware Detection → 3. Expectations → 4. Outlook → 5. Initial Index → 6. Feature Tour

**Story Points:** 5
**Priority:** P1 (Important)

---

#### Story 2.6: Error Handling, Logging & Installer

**Story Description:**
As a user, I need the application to handle errors gracefully and as a developer, I need comprehensive logging so that issues can be diagnosed and the application can be easily installed.

**Acceptance Criteria:**
- Graceful error handling for all failure modes with user-friendly messages
- Automatic recovery from Outlook disconnection
- Model fallback if primary model fails to load
- Comprehensive logging with rotation (max 10 files of 10MB each)
- Error logs include: timestamp, severity, context, stack trace
- User-facing error messages avoid technical jargon
- "Report Issue" button copies logs to clipboard
- Windows installer (.exe) with all dependencies except Ollama
- Installer includes hardware check and warnings for minimum specs
- Code signing certificate for Windows Defender trust
- Clean uninstall with option to preserve or delete database
- Automatic update check (optional, user-controlled)

**Error Scenarios:**
- Ollama not installed → Clear instructions with download link
- Model not downloaded → Automatic download with progress or manual fallback
- Outlook not running → Prompt to start Outlook
- Insufficient memory → Suggest lighter model or close apps
- Database corruption → Automatic backup restoration

**Installer Features:**
- NSIS or Inno Setup installer
- Custom branding and license agreement
- Registry entries for uninstall
- Desktop shortcut creation (optional)
- Startup folder entry (optional)

**Story Points:** 8
**Priority:** P0 (Critical Path)

---

### Epic 3: Security & MVP Readiness

**Epic Goal:** Address critical security vulnerabilities and align marketing with implementation reality to ensure a trustworthy MVP launch that delivers on privacy promises.

**Value Proposition:** Transform the MVP from having critical vulnerabilities to being a secure, production-ready application that genuinely delivers "Local-First Privacy" without compromising user data.

**Success Criteria:**
- Zero critical security vulnerabilities in production code
- Database encryption implemented and enabled by default
- All prompt injection attempts blocked with proper logging
- Performance meets promised 10-15 emails/minute target
- Marketing materials accurately reflect security features
- Security documentation complete and transparent

**Dependencies:**
- Stories 1.1-1.6 and 2.1-2.6 complete
- Windows DPAPI available for key management
- SQLCipher library compatible with Python environment

---

#### Story 3.1: Database Encryption Implementation

**Story Description:**
As a privacy-conscious user, I need my email analysis data encrypted at rest so that my sensitive information is protected even if someone gains access to the database file.

**Acceptance Criteria:**
- Implement SQLCipher for transparent database encryption
- Use Windows DPAPI for secure key management (no hardcoded keys)
- Provide migration tool for existing unencrypted databases
- Performance overhead <10% (target <5%) for all operations
- Encryption transparent to existing code (no API changes required)
- Add encryption status indicator to settings UI
- Document encryption implementation in privacy policy
- Support user choice: encrypted (default) or unencrypted (with warning)

**Technical Notes:**
- Install pysqlcipher3 package
- Modify DatabaseManager.__init__ to check encryption_key parameter
- Key derivation: DPAPI → PBKDF2 → SQLCipher key
- PRAGMA key command after connection
- Test with large databases (>500MB)

**Story Points:** 5
**Priority:** P0 (Critical - Privacy Promise)

---

#### Story 3.2: Prompt Injection Defense

**Story Description:**
As a user, I need protection from malicious emails that try to manipulate AI responses so that the system remains secure and trustworthy.

**Acceptance Criteria:**
- Block emails containing prompt injection patterns (don't just warn)
- Return safe error response: "Email blocked for security reasons"
- Log all security events to dedicated security.log with rotation
- Add "Report Suspicious Email" button in UI for false positives
- Configurable security levels: Strict/Normal/Permissive (default: Normal)
- User notification toast when email is blocked
- Maintain updatable blocklist patterns in security_patterns.yaml
- Provide override option with confirmation for advanced users

**Implementation:**
```python
# Current (vulnerable):
if pattern.search(sanitized):
    self.warnings.append(f"Suspicious content")
    logger.warning(f"Potential prompt injection")
    # CONTINUES PROCESSING!

# Fixed (secure):
if pattern.search(sanitized):
    raise SecurityException(f"Email blocked: suspicious content detected")
    # STOPS PROCESSING
```

**Story Points:** 3
**Priority:** P0 (Critical - Security)

---

#### Story 3.3: Performance & Security Optimization

**Story Description:**
As a developer, I need to fix SQL injection vulnerabilities and implement performance optimizations so that the application is both secure and meets performance promises.

**Acceptance Criteria:**
- Fix SQL injection in database_manager.py line 963 (use parameterized queries)
- Audit all SQL queries for injection vulnerabilities
- Implement OllamaConnectionPool with configurable pool size (2-5 connections)
- Add model checksum verification against known-good hashes
- Implement parallel email processing using ThreadPoolExecutor
- Achieve 10-15 emails/minute batch processing target
- Add performance metrics dashboard to UI
- Document all security improvements in SECURITY.md

**Technical Implementation:**
```python
# SQL Injection Fix:
# BEFORE (vulnerable):
cursor.execute(f"DELETE FROM {table}")

# AFTER (secure):
if table not in ALLOWED_TABLES:
    raise ValueError(f"Invalid table: {table}")
cursor.execute(f"DELETE FROM {table}")

# Connection Pooling:
class OllamaConnectionPool:
    def __init__(self, size=3):
        self.pool = [ollama.Client() for _ in range(size)]
        self.available = queue.Queue()
        for conn in self.pool:
            self.available.put(conn)
```

**Model Checksums:**
```json
{
  "llama3.1:8b-instruct-q4_K_M": "sha256:abc123...",
  "mistral:7b-instruct-q4_K_M": "sha256:def456..."
}
```

**Story Points:** 5
**Priority:** P0 (Critical - Security & Performance)

---

#### Story 3.4: Marketing & Documentation Alignment

**Story Description:**
As a product owner, I need marketing claims aligned with actual security implementation so that we maintain user trust and avoid false advertising.

**Acceptance Criteria:**
- Update marketing from "Absolute Privacy" to "Local-First Privacy"
- Create comprehensive SECURITY.md documentation
- Write privacy policy explaining encryption and data handling
- Update README.md with security features section
- Create security FAQ for common user concerns
- Document known limitations transparently
- Create security roadmap for future improvements
- Add security badges to README (e.g., "SQLCipher Encrypted")

**Documentation Updates:**
- Website: Change hero text to "Your Email AI That Never Leaves Your Computer"
- README: Add "Security Features" section with checkmarks for implemented features
- FAQ: "Is my data encrypted?" → "Yes, using industry-standard SQLCipher with Windows DPAPI"
- Limitations: "Email content remains in Outlook's storage which may not be encrypted"

**Story Points:** 2
**Priority:** P1 (Important - Trust)

---

## Story Summary

**Total Stories:** 21 (including Epic 0)
**Total Story Points:** 105 (including Epic 0)

### Epic 0: Setup & Reliability (5 stories, 18 points)
- Story 0.1: System Resource Detection & Model Recommendation (3 pts) - P0
- Story 0.2: Interactive Model Selection in Setup Wizard (5 pts) - P0
- Story 0.3: Unicode Error Fixes & Robust Subprocess Handling (2 pts) - P0
- Story 0.4: Interactive Diagnostic Remediation Menu (5 pts) - P1
- Story 0.5: Dynamic Model Loading & Runtime Switching (3 pts) - P2

### Epic 1: AI-Powered Email Intelligence (6 stories, 36 points)
- Story 1.1: Ollama Integration & Model Setup (5 pts) - P0
- Story 1.2: Email Preprocessing Pipeline (5 pts) - P0
- Story 1.3: Real-Time Analysis Engine (8 pts) - P0
- Story 1.4: Priority Classification System (5 pts) - P0
- Story 1.5: Response Generation Assistant (8 pts) - P0
- Story 1.6: Performance Optimization & Caching (5 pts) - P1

### Epic 2: Desktop Application & User Experience (6 stories, 36 points)
- Story 2.1: Outlook Integration (8 pts) - P0
- Story 2.2: SQLite Database & Caching Layer (5 pts) - P0
- Story 2.3: CustomTkinter UI Framework (8 pts) - P0
- Story 2.4: Settings & Configuration System (5 pts) - P1
- Story 2.5: Hardware Profiling & Onboarding Wizard (5 pts) - P1
- Story 2.6: Error Handling, Logging & Installer (8 pts) - P0

### Epic 3: Security & MVP Readiness (4 stories, 15 points)
- Story 3.1: Database Encryption Implementation (5 pts) - P0
- Story 3.2: Prompt Injection Defense (3 pts) - P0
- Story 3.3: Performance & Security Optimization (5 pts) - P0
- Story 3.4: Marketing & Documentation Alignment (2 pts) - P1

---

## Implementation Sequence

**Recommended Development Order:**

**Sprint 0 (Week 0-1): Setup & Reliability** ⚡ CRITICAL PATH
1. Story 0.3: Unicode Error Fixes (2 pts) - Quick win, unblocks diagnostics
2. Story 0.1: System Resource Detection (3 pts) - Enables smart model selection
3. Story 0.2: Interactive Model Selection (5 pts) - Improves setup UX
4. Story 0.4: Interactive Remediation (5 pts) - Automated troubleshooting

**Sprint 1 (Weeks 1-2): Foundation**
5. Story 2.2: SQLite Database & Caching Layer
6. Story 1.1: Ollama Integration & Model Setup
7. Story 2.1: Outlook Integration (basic read-only)

**Sprint 2 (Weeks 2-4): Core AI**
8. Story 1.2: Email Preprocessing Pipeline
9. Story 1.3: Real-Time Analysis Engine
10. Story 1.4: Priority Classification System

**Sprint 3 (Weeks 5-6): User Interface**
11. Story 2.3: CustomTkinter UI Framework
12. Story 1.5: Response Generation Assistant
13. Story 2.4: Settings & Configuration System

**Sprint 4 (Weeks 7-9): Polish & Release**
14. Story 1.6: Performance Optimization & Caching
15. Story 2.5: Hardware Profiling & Onboarding Wizard
16. Story 2.6: Error Handling, Logging & Installer
17. Story 3.1-3.4: Security & MVP Readiness (4 stories)

---

## Out of Scope (Future Versions)

**Version 1.1 (Month 3):**
- Microsoft Graph API migration option
- Advanced personalization learning
- Custom prompt templates
- Backup and restore

**Version 1.2 (Months 4-5):**
- Multi-account support
- Calendar integration
- Plugin architecture
- Advanced filing rules

**Version 2.0 (Month 6+):**
- Mac support (Apple Silicon)
- Team features (local network sync)
- Voice control integration
- Custom model fine-tuning

---

## Success Metrics

**MVP Validation (First 30 Days):**
- Onboarding completion rate: >60%
- Performance satisfaction: >70% rate as "fast enough"
- Folder suggestion acceptance: >75%
- Priority classification accuracy: >85%
- Daily active usage: >50% after 30 days

**Business Metrics:**
- Trial → Paid conversion: 15-20%
- Customer Acquisition Cost: <$30
- Refund rate: <5%
- Net Promoter Score: >50

---

_This epic breakdown aligns with the 8-week MVP roadmap from the PRD and structures work for efficient parallel development where possible._
