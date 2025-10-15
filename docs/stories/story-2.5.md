# Story 2.5: Hardware Profiling & Onboarding Wizard

**Epic:** Epic 2 - Desktop Application & User Experience
**Story ID:** 2.5
**Story Points:** 5
**Priority:** P1 (Important)
**Status:** Ready
**Created:** 2025-10-15

---

## Story Description

As a new user, I need guided setup and clear performance expectations so that I can successfully configure MailMind for my hardware.

## Business Value

This story creates the first-run experience that sets user expectations and ensures successful application setup:
- Reduces onboarding friction with step-by-step wizard
- Sets realistic performance expectations based on hardware
- Proactively troubleshoots common setup issues (Ollama, Outlook)
- Builds user confidence through transparency about system capabilities
- Increases onboarding completion rate to >60% target
- Leverages existing HardwareProfiler from Story 1.6 for hardware detection

Without this story, users would face trial-and-error setup, unclear performance expectations, and higher abandonment rates.

---

## Acceptance Criteria

### AC1: First-Run Onboarding Wizard (5 Steps)
- [ ] Detect if this is first application launch (check for onboarding_complete flag in user_preferences)
- [ ] Show full-screen onboarding wizard automatically on first launch
- [ ] Implement 5-step wizard flow with navigation (Back/Next/Skip)
- [ ] Step 1: Welcome and value proposition (30-second overview)
- [ ] Step 2: Hardware detection with automatic profiling
- [ ] Step 3: Performance expectations based on detected hardware
- [ ] Step 4: Outlook connection test and troubleshooting
- [ ] Step 5: Initial email indexing with progress bar
- [ ] Allow users to skip wizard (with confirmation warning)
- [ ] Set onboarding_complete flag after wizard completion

**Wizard Navigation:**
- Back button (disabled on Step 1)
- Next button (enabled after step validation)
- Skip button (shows confirmation: "Are you sure? Setup helps optimize performance")
- Close button (X) in top-right (same as Skip)

### AC2: Hardware Detection with Automatic Profiling (Step 2)
- [ ] Integrate with existing HardwareProfiler from Story 1.6
- [ ] Run HardwareProfiler.detect_hardware() on Step 2
- [ ] Display detected hardware in user-friendly format:
  - CPU: Cores, Architecture, Frequency
  - RAM: Total GB, Available GB
  - GPU: Model name, VRAM (if detected)
  - Hardware Tier: Minimum/Recommended/Optimal/Insufficient
- [ ] Show spinner/progress indicator during hardware detection (~2s)
- [ ] Store hardware profile in database for future reference
- [ ] Handle detection failures gracefully with fallback to "Unknown" tier

**Hardware Display Format:**
```
Hardware Profile:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CPU:     8 cores (x86_64)
RAM:     24 GB available (32 GB total)
GPU:     NVIDIA RTX 4060 (8 GB VRAM)
Tier:    🟢 Optimal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Your hardware is excellent for MailMind!
```

### AC3: Performance Expectations Based on Hardware (Step 3)
- [ ] Display performance expectations based on detected hardware tier
- [ ] Show expected tokens/second estimate for detected hardware
- [ ] Display expected email analysis time (seconds per email)
- [ ] Show recommended model configuration
- [ ] Provide clear messaging about hardware limitations and trade-offs
- [ ] For Insufficient tier: Show upgrade recommendations
- [ ] For Minimum tier: Show "functional but slow" messaging
- [ ] For Recommended tier: Show "fast and responsive" messaging
- [ ] For Optimal tier: Show "near-instant" messaging

**Performance Messaging by Tier:**

**Optimal (High-GPU, 32GB+ RAM):**
```
🟢 Performance: Near-instant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Expected Speed:   100-200 tokens/sec
Email Analysis:   <1 second per email
Batch Processing: 15-20 emails/minute
Model:            Llama 3.1 8B (Q4_K_M)

Your hardware is excellent! You'll experience the best possible performance.
```

**Recommended (Mid-GPU, 16-24GB RAM):**
```
🟡 Performance: Fast and responsive
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Expected Speed:   50-100 tokens/sec
Email Analysis:   <2 seconds per email
Batch Processing: 10-15 emails/minute
Model:            Llama 3.1 8B (Q4_K_M)

Your hardware is well-suited for MailMind. You'll get great performance.
```

**Minimum (CPU-only, 16GB RAM):**
```
🟠 Performance: Functional but slower
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Expected Speed:   10-30 tokens/sec
Email Analysis:   3-5 seconds per email
Batch Processing: 5-10 emails/minute
Model:            Llama 3.1 8B (Q4_K_M)

MailMind will work on your hardware, but analysis will be slower. Consider GPU upgrade for better performance.
```

**Insufficient (<16GB RAM):**
```
🔴 Performance: Below minimum specs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Expected Speed:   <10 tokens/sec
Email Analysis:   >10 seconds per email
RAM Available:    {X} GB (Minimum: 16 GB)

⚠️ Warning: MailMind requires at least 16GB RAM. The application may not run reliably on this hardware.

Recommendation: Upgrade to 16GB+ RAM for functional performance.
```

### AC4: Outlook Connection Test (Step 4)
- [ ] Test Outlook connection using OutlookConnector from Story 2.1
- [ ] Show connection attempt with spinner and status messages
- [ ] Display connection result: Success (✓) or Failure (✗)
- [ ] On success: Show Outlook version, email account(s) detected, inbox folder count
- [ ] On failure: Show troubleshooting steps with actionable instructions
- [ ] Provide retry button to attempt connection again
- [ ] Allow users to skip Outlook connection (but warn about missing functionality)

**Connection Success Display:**
```
✓ Outlook Connected Successfully
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version:   Microsoft Outlook 2021
Account:   john.doe@company.com
Folders:   12 folders detected
Inbox:     156 emails ready to index

Ready to proceed with email indexing.
```

**Connection Failure Display:**
```
✗ Outlook Connection Failed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Issue: Outlook is not running

Troubleshooting Steps:
1. Start Microsoft Outlook
2. Ensure Outlook is fully loaded
3. Click "Retry" below

[Retry Connection] [Skip Outlook Setup]
```

**Common Failure Scenarios:**
- Outlook not installed → Show download link and installer instructions
- Outlook not running → Prompt user to start Outlook and retry
- Outlook blocked by antivirus → Show instructions to whitelist MailMind
- COM interface error → Show advanced troubleshooting steps

### AC5: Initial Email Indexing (Step 5)
- [ ] Fetch first 50 emails from Outlook inbox after successful connection
- [ ] Display real-time progress bar with current/total count
- [ ] Show status messages: "Fetching emails...", "Analyzing priority...", "Building cache..."
- [ ] Track and display elapsed time and estimated time remaining
- [ ] Allow cancellation of indexing (but warn about incomplete setup)
- [ ] Store indexed email metadata in database via DatabaseManager
- [ ] Run priority classification on indexed emails for initial experience
- [ ] Show completion summary: X emails indexed, Y analyzed, Z cached
- [ ] Handle indexing errors gracefully (e.g., network timeout, locked Outlook)

**Progress Display:**
```
Indexing Your Inbox
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Progress: 32/50 emails (64%)
[████████████████░░░░░░░░] 64%

Status: Analyzing priority classification...
Elapsed: 12s | Remaining: ~7s

[Cancel Indexing]
```

**Completion Summary:**
```
✓ Initial Indexing Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Emails Fetched:   50
Analyzed:         50
High Priority:    8 emails
Medium Priority:  24 emails
Low Priority:     18 emails
Time Taken:       18 seconds

Your inbox is ready to use!

[Continue to Feature Tour] [Skip Tour]
```

### AC6: Hardware Profiler Display Components
- [ ] Reuse HardwareProfiler from Story 1.6 for detection logic
- [ ] Create OnboardingWizard dialog using CustomTkinter (Story 2.3 framework)
- [ ] Display hardware profile in clean, visual format (not raw JSON)
- [ ] Use color coding for hardware tier: 🟢 Optimal, 🟡 Recommended, 🟠 Minimum, 🔴 Insufficient
- [ ] Show recommended model configuration based on hardware
- [ ] Include tooltips/help text for technical terms (VRAM, tokens/sec)
- [ ] Store hardware profile in user_preferences table for settings access

### AC7: Skippable Feature Tour (Step 6)
- [ ] After indexing, show optional feature tour (3-4 slides)
- [ ] Slide 1: Email list with priority indicators
- [ ] Slide 2: Analysis panel with AI insights
- [ ] Slide 3: Response generator
- [ ] Slide 4: Settings and preferences
- [ ] Allow users to skip tour entirely (button: "I'll explore myself")
- [ ] Dismissible tour with "Don't show again" checkbox
- [ ] Store tour completion status in user_preferences

**Feature Tour Slide Example:**
```
📧 Email Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MailMind uses AI to analyze each email:
• 🔴 High priority (urgent, deadlines)
• 🟡 Medium priority (projects, team)
• 🔵 Low priority (newsletters, FYI)

Click any email to see full AI analysis.

[Previous] [Next] [Skip Tour]
```

### AC8: Re-Run Onboarding from Settings
- [ ] Add "Re-run Onboarding" button in Settings → Advanced tab
- [ ] Clear onboarding_complete flag to trigger wizard on next launch
- [ ] Alternatively: Provide direct "Run Onboarding Now" button that launches wizard immediately
- [ ] Show confirmation dialog: "This will restart the setup wizard. Continue?"
- [ ] Preserve existing user preferences and database during re-run

### AC9: Clear Messaging About Limitations
- [ ] For Minimum hardware: Show "Slower performance expected" messaging
- [ ] For Insufficient hardware: Show upgrade recommendations prominently
- [ ] Display trade-offs: CPU-only vs GPU, batch size impact on speed
- [ ] Provide link to hardware requirements documentation
- [ ] Show performance comparison table for different hardware tiers
- [ ] Include FAQ link for common questions about hardware and performance

---

## Technical Notes

### Dependencies
- **Story 1.6:** HardwareProfiler for hardware detection ✅ COMPLETE
- **Story 2.1:** OutlookConnector for Outlook connection testing ✅ COMPLETE
- **Story 2.2:** DatabaseManager for storing preferences and email metadata ✅ COMPLETE
- **Story 2.3:** CustomTkinter UI framework for wizard dialogs ✅ COMPLETE
- **Story 2.4:** SettingsManager for storing onboarding state ✅ COMPLETE

### Architecture Overview

```
Application Launch
    ↓
Check user_preferences: onboarding_complete?
    ↓
    [No] → Launch OnboardingWizard
    ↓
Step 1: Welcome Screen
    ↓
Step 2: Hardware Detection (HardwareProfiler.detect_hardware())
    ↓
Step 3: Performance Expectations Display
    ↓
Step 4: Outlook Connection Test (OutlookConnector.test_connection())
    ↓
Step 5: Initial Email Indexing (OutlookConnector.fetch_emails(limit=50))
    ↓
Optional: Feature Tour (3-4 slides)
    ↓
Set onboarding_complete = True → Save to user_preferences
    ↓
Launch Main Application Window
```

### OnboardingWizard Implementation

```python
class OnboardingWizard:
    def __init__(self, parent, settings_manager, db_manager):
        self.settings_manager = settings_manager
        self.db_manager = db_manager
        self.current_step = 1
        self.total_steps = 5
        self.hardware_profile = None

        # Create wizard window
        self.wizard_window = ctk.CTkToplevel(parent)
        self.wizard_window.title("MailMind Setup Wizard")
        self.wizard_window.geometry("800x600")

        # Initialize wizard components
        self._create_navigation()
        self._show_step(self.current_step)

    def _show_step(self, step_number: int):
        """Display specific wizard step."""
        if step_number == 1:
            self._show_welcome()
        elif step_number == 2:
            self._show_hardware_detection()
        elif step_number == 3:
            self._show_performance_expectations()
        elif step_number == 4:
            self._show_outlook_connection()
        elif step_number == 5:
            self._show_initial_indexing()

    def _show_hardware_detection(self):
        """Step 2: Hardware detection and profiling."""
        # Create progress indicator
        self.progress_label = ctk.CTkLabel(
            self.content_frame,
            text="Detecting your hardware...",
            font=("Segoe UI", 14)
        )
        self.progress_label.pack(pady=20)

        # Run hardware detection in background thread
        threading.Thread(
            target=self._run_hardware_detection,
            daemon=True
        ).start()

    def _run_hardware_detection(self):
        """Background task: Detect hardware and update UI."""
        from mailmind.core.hardware_profiler import HardwareProfiler

        # Detect hardware
        self.hardware_profile = HardwareProfiler.detect_hardware()

        # Store in database
        self.db_manager.set_preference(
            'hardware_profile',
            json.dumps(self.hardware_profile)
        )

        # Update UI on main thread
        self.wizard_window.after(0, self._display_hardware_profile)

    def _display_hardware_profile(self):
        """Display detected hardware in user-friendly format."""
        profile = self.hardware_profile

        # Create hardware display
        hardware_text = f"""
Hardware Profile:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CPU:     {profile['cpu_cores']} cores ({profile['cpu_architecture']})
RAM:     {profile['ram_available_gb']} GB available ({profile['ram_total_gb']} GB total)
"""

        if profile['gpu_detected']:
            hardware_text += f"GPU:     {profile['gpu_detected']} ({profile['gpu_vram_gb']} GB VRAM)\n"
        else:
            hardware_text += "GPU:     Not detected (CPU-only mode)\n"

        hardware_text += f"Tier:    {self._get_tier_emoji(profile['hardware_tier'])} {profile['hardware_tier']}\n"
        hardware_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        hardware_text += self._get_tier_message(profile['hardware_tier'])

        # Update UI
        self.progress_label.configure(text=hardware_text)
        self.next_button.configure(state="normal")

    def _show_outlook_connection(self):
        """Step 4: Test Outlook connection."""
        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="Testing Outlook connection...",
            font=("Segoe UI", 14)
        )
        self.status_label.pack(pady=20)

        # Run connection test in background
        threading.Thread(
            target=self._test_outlook_connection,
            daemon=True
        ).start()

    def _test_outlook_connection(self):
        """Background task: Test Outlook connection."""
        from mailmind.integrations.outlook_connector import OutlookConnector

        try:
            connector = OutlookConnector()
            status = connector.get_connection_status()

            if status.is_connected:
                self.outlook_connected = True
                self.outlook_info = {
                    'version': status.outlook_version,
                    'account': connector.get_default_account(),
                    'folders': len(connector.get_all_folders())
                }
                self.wizard_window.after(0, self._display_outlook_success)
            else:
                self.outlook_connected = False
                self.outlook_error = status.error_message
                self.wizard_window.after(0, self._display_outlook_failure)

        except Exception as e:
            self.outlook_connected = False
            self.outlook_error = str(e)
            self.wizard_window.after(0, self._display_outlook_failure)

    def _show_initial_indexing(self):
        """Step 5: Index first 50 emails from inbox."""
        self.progress_bar = ctk.CTkProgressBar(
            self.content_frame,
            width=600
        )
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="Starting email indexing...",
            font=("Segoe UI", 12)
        )
        self.status_label.pack(pady=10)

        # Run indexing in background
        threading.Thread(
            target=self._run_indexing,
            daemon=True
        ).start()

    def _run_indexing(self):
        """Background task: Index emails with progress updates."""
        from mailmind.integrations.outlook_connector import OutlookConnector
        from mailmind.core.email_analysis_engine import EmailAnalysisEngine

        connector = OutlookConnector()
        analysis_engine = EmailAnalysisEngine()

        emails = connector.fetch_emails(folder_name='Inbox', limit=50)
        total_emails = len(emails)

        indexed_count = 0
        priority_counts = {'High': 0, 'Medium': 0, 'Low': 0}

        for i, email in enumerate(emails):
            # Update progress
            progress = (i + 1) / total_emails
            self.wizard_window.after(0, lambda p=progress, c=i+1: self._update_indexing_progress(p, c, total_emails))

            # Analyze email
            analysis = analysis_engine.analyze_email(email.to_dict())
            priority_counts[analysis['priority']] += 1

            indexed_count += 1

        # Show completion
        self.wizard_window.after(0, lambda: self._show_indexing_complete(indexed_count, priority_counts))

    def _update_indexing_progress(self, progress: float, current: int, total: int):
        """Update indexing progress bar and status."""
        self.progress_bar.set(progress)
        self.status_label.configure(
            text=f"Indexing: {current}/{total} emails ({int(progress * 100)}%)"
        )

    def _complete_onboarding(self):
        """Mark onboarding as complete and close wizard."""
        self.settings_manager.set('onboarding_complete', 'true')
        self.wizard_window.destroy()
```

### Integration with Existing Components

**1. HardwareProfiler (Story 1.6):**
```python
from mailmind.core.hardware_profiler import HardwareProfiler

# Detect hardware on Step 2
profile = HardwareProfiler.detect_hardware()
# Returns: {cpu_cores, ram_total_gb, gpu_detected, hardware_tier, ...}
```

**2. OutlookConnector (Story 2.1):**
```python
from mailmind.integrations.outlook_connector import OutlookConnector

# Test connection on Step 4
connector = OutlookConnector()
status = connector.get_connection_status()

# Fetch emails on Step 5
emails = connector.fetch_emails(folder_name='Inbox', limit=50)
```

**3. SettingsManager (Story 2.4):**
```python
from mailmind.core.settings_manager import SettingsManager

# Check if onboarding complete
settings = SettingsManager.get_instance()
onboarding_complete = settings.get('onboarding_complete', 'false')

# Mark onboarding complete
settings.set('onboarding_complete', 'true')
```

**4. CustomTkinter (Story 2.3):**
```python
import customtkinter as ctk

# Create wizard window
wizard = ctk.CTkToplevel(parent)
wizard.title("MailMind Setup Wizard")
wizard.geometry("800x600")
```

---

## Testing Checklist

### Unit Tests
- [ ] Test onboarding_complete flag detection
- [ ] Test wizard navigation (Back/Next/Skip buttons)
- [ ] Test hardware profile display formatting
- [ ] Test performance messaging for each hardware tier
- [ ] Test Outlook connection status handling
- [ ] Test indexing progress calculations
- [ ] Test completion flag storage in database
- [ ] Test re-run onboarding functionality

### Integration Tests
- [ ] Test full wizard flow end-to-end (Steps 1-5)
- [ ] Test hardware detection integration with HardwareProfiler
- [ ] Test Outlook connection integration with OutlookConnector
- [ ] Test email indexing integration with EmailAnalysisEngine
- [ ] Test settings persistence via SettingsManager
- [ ] Test wizard appearance on first launch
- [ ] Test wizard skip on subsequent launches (onboarding_complete=true)
- [ ] Test re-run onboarding from settings

### UI/UX Tests
- [ ] Test wizard window dimensions and responsiveness (800x600)
- [ ] Test navigation button states (enabled/disabled)
- [ ] Test progress indicators (spinners, progress bars)
- [ ] Test hardware tier color coding (🟢🟡🟠🔴)
- [ ] Test Outlook connection retry functionality
- [ ] Test indexing cancellation
- [ ] Test feature tour slides navigation
- [ ] Test wizard closure and main window launch

### Edge Cases
- [ ] Hardware detection failure (fallback to "Unknown" tier)
- [ ] Outlook not installed (show installation instructions)
- [ ] Outlook connection timeout (show retry option)
- [ ] Email indexing failure mid-way (handle partial completion)
- [ ] User closes wizard mid-flow (onboarding_complete remains false)
- [ ] Re-run onboarding with existing data (preserve preferences)
- [ ] Insufficient hardware warning (<16GB RAM)
- [ ] GPU detection failure (CPU-only fallback)

---

## Performance Targets

| Operation | Target | Acceptable | Critical |
|-----------|--------|------------|----------|
| **Hardware Detection** | <2s | <5s | <10s |
| **Outlook Connection Test** | <3s | <5s | <10s |
| **Initial Indexing (50 emails)** | <20s | <30s | <60s |
| **Wizard Step Transition** | <100ms | <500ms | <1s |
| **Progress Bar Update** | <50ms | <100ms | <200ms |

**Hardware-based Indexing Targets:**
- **Optimal (high-GPU):** 50 emails in <15s (~3s/email)
- **Recommended (mid-GPU):** 50 emails in <20s (~2.5s/email)
- **Minimum (CPU-only):** 50 emails in <30s (~1.7s/email)

---

## Definition of Done

- [ ] All acceptance criteria met (AC1-AC9)
- [ ] OnboardingWizard class implemented with 5-step flow
- [ ] Integration with HardwareProfiler from Story 1.6
- [ ] Integration with OutlookConnector from Story 2.1
- [ ] Integration with SettingsManager from Story 2.4
- [ ] Hardware profiler displays CPU, RAM, GPU, tier in user-friendly format
- [ ] Performance expectations shown for detected hardware tier
- [ ] Outlook connection test with troubleshooting steps
- [ ] Initial email indexing with progress bar and status updates
- [ ] Optional feature tour with 3-4 slides
- [ ] Re-run onboarding functionality in settings
- [ ] onboarding_complete flag stored in user_preferences table
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration tests with all dependencies passing
- [ ] UI/UX tests for wizard flow passing
- [ ] Performance targets met on recommended hardware
- [ ] Error handling for all failure modes
- [ ] Code reviewed and approved
- [ ] Documentation updated:
  - Module docstrings complete
  - Onboarding flow diagram
  - Hardware tier explanations
  - Troubleshooting guide for common failures
- [ ] Demo showing full wizard flow from launch to completion
- [ ] Main application launches correctly after onboarding

---

## Dependencies & Blockers

**Upstream Dependencies:**
- Story 1.6 (Performance Optimization & Caching) - COMPLETE ✅
- Story 2.1 (Outlook Integration) - COMPLETE ✅
- Story 2.2 (SQLite Database & Caching Layer) - COMPLETE ✅
- Story 2.3 (CustomTkinter UI Framework) - COMPLETE ✅
- Story 2.4 (Settings & Configuration System) - COMPLETE ✅

**Downstream Dependencies:**
- Story 2.6 (Error Handling, Logging & Installer) will integrate wizard into installer flow

**External Dependencies:**
- CustomTkinter 5.2.0+ (UI framework)
- psutil (hardware detection, from Story 1.6)
- Ollama (model serving, from Story 1.1)
- Microsoft Outlook (email integration, from Story 2.1)

**Potential Blockers:**
- Hardware detection may fail on some systems (acceptable, fallback to "Unknown" tier)
- Outlook connection may fail (expected, troubleshooting flow handles this)
- Initial indexing may be slow on minimum hardware (expected, set user expectations)

---

## Implementation Plan

### Phase 1: OnboardingWizard Framework (Day 1)
1. Create OnboardingWizard class structure
2. Implement 5-step wizard navigation
3. Create wizard window with CustomTkinter
4. Add Back/Next/Skip button logic
5. Implement onboarding_complete flag check/storage
6. Test wizard launch on first run
7. Test wizard skip on subsequent runs

### Phase 2: Hardware Detection & Performance (Day 2)
1. Integrate HardwareProfiler from Story 1.6
2. Implement Step 2: Hardware detection display
3. Implement Step 3: Performance expectations messaging
4. Add hardware tier color coding (🟢🟡🟠🔴)
5. Create performance comparison UI
6. Add tooltips for technical terms
7. Test on different hardware tiers

### Phase 3: Outlook & Indexing (Day 3)
1. Implement Step 4: Outlook connection test
2. Add Outlook troubleshooting UI with retry
3. Implement Step 5: Initial email indexing
4. Add progress bar and status updates
5. Integrate with EmailAnalysisEngine for analysis
6. Add indexing cancellation functionality
7. Test end-to-end indexing flow

### Phase 4: Feature Tour & Polish (Day 4)
1. Implement optional feature tour (3-4 slides)
2. Add re-run onboarding from settings
3. Create completion summary display
4. Add welcome screen (Step 1)
5. Comprehensive error handling
6. UI/UX polish and animations
7. Documentation and examples

### Phase 5: Testing & Documentation (Day 5)
1. Write comprehensive unit tests
2. Write integration tests with all dependencies
3. UI/UX testing with different scenarios
4. Performance benchmarking on different hardware
5. Documentation and user guide
6. Demo script showing full wizard flow

---

## Hardware Tier Messaging

### Optimal (🟢)
```
Your hardware is excellent for MailMind!

Expected Performance:
• Analysis: <1 second per email
• Tokens/sec: 100-200 t/s
• Batch: 15-20 emails/minute

You'll experience the best possible performance with near-instant email analysis.
```

### Recommended (🟡)
```
Your hardware is well-suited for MailMind.

Expected Performance:
• Analysis: <2 seconds per email
• Tokens/sec: 50-100 t/s
• Batch: 10-15 emails/minute

You'll get great performance for daily email management.
```

### Minimum (🟠)
```
MailMind will work on your hardware, but analysis will be slower.

Expected Performance:
• Analysis: 3-5 seconds per email
• Tokens/sec: 10-30 t/s
• Batch: 5-10 emails/minute

Consider upgrading to a GPU for better performance. The application will still function, but you may experience longer wait times during email analysis.
```

### Insufficient (🔴)
```
⚠️ Warning: Your hardware is below minimum requirements.

Current Hardware:
• RAM: {X} GB (Minimum: 16 GB required)

MailMind requires at least 16GB RAM to function reliably. The application may crash or perform very poorly on this hardware.

Recommendation: Upgrade to 16GB+ RAM before using MailMind.

[Continue Anyway (Not Recommended)] [Exit Setup]
```

---

## Onboarding Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Application Launch                                         │
│  Check: onboarding_complete flag                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ├─ [True] → Launch Main Application
                         │
                         └─ [False] → Launch OnboardingWizard
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Welcome Screen                                     │
│  • Project value proposition (30 seconds)                   │
│  • "Get Started" button                                     │
│  [Next] [Skip Setup]                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Hardware Detection                                 │
│  • Run HardwareProfiler.detect_hardware()                   │
│  • Display: CPU, RAM, GPU, Tier                             │
│  • Show spinner during detection (~2s)                      │
│  [Back] [Next] [Skip]                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Performance Expectations                           │
│  • Display performance messaging based on tier              │
│  • Show expected tokens/sec, analysis time                  │
│  • Hardware limitations and trade-offs                      │
│  [Back] [Next] [Skip]                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Outlook Connection Test                            │
│  • Test OutlookConnector.get_connection_status()            │
│  • Success: Show Outlook version, accounts, folders         │
│  • Failure: Show troubleshooting steps + [Retry]            │
│  [Back] [Next] [Skip Outlook]                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Initial Email Indexing                             │
│  • Fetch first 50 emails from inbox                         │
│  • Analyze priority for each email                          │
│  • Progress bar: [████████████░░░░] 64%                     │
│  • Status: "Analyzing... 32/50 emails"                      │
│  [Back] [Cancel Indexing] [Finish]                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Completion Summary                                         │
│  • Show indexing results: X emails, Y high priority         │
│  • Optional: Feature tour (3-4 slides)                      │
│  [Continue to App] [Skip Tour]                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Set onboarding_complete = True                             │
│  Save to user_preferences                                   │
│  Close wizard, launch main application                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- Story 1.6 (COMPLETE): HardwareProfiler for hardware detection
- Story 2.1 (COMPLETE): OutlookConnector for Outlook integration
- Story 2.2 (COMPLETE): DatabaseManager for preferences storage
- Story 2.3 (COMPLETE): CustomTkinter UI framework for wizard dialogs
- Story 2.4 (COMPLETE): SettingsManager for onboarding flag storage
- PRD Section 2.3: User Onboarding
- PRD Section 4.5: Hardware Requirements
- epic-stories.md: Epic 2 context

---

## Story Lifecycle

**Created:** 2025-10-15 (Moved from BACKLOG to TODO)
**Started:** [To be filled when implementation begins]
**Completed:** [To be filled when DoD met]

---

_This story creates the first-run experience that sets user expectations and ensures successful application setup through a guided 5-step wizard. It leverages existing components from Stories 1.6, 2.1-2.4 to provide seamless hardware detection, Outlook connection testing, and initial email indexing._

## Dev Agent Record

### Context Reference

- Story Context: `docs/stories/story-context-2.5.xml` (Generated: 2025-10-15)

### Agent Model Used

(To be filled by DEV agent)

### Debug Log References

### Completion Notes List

### File List
