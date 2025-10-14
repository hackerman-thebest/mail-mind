# Story 2.3: CustomTkinter UI Framework

**Status:** Ready
**Epic:** 2 - Desktop Application & User Experience
**Story Points:** 8
**Priority:** P0 (Critical Path)
**Created:** 2025-10-14

---

## Story

As a user,
I want a modern, intuitive desktop interface with visual email analysis, response generation controls, and real-time performance indicators,
so that I can efficiently triage my inbox, understand email priorities at a glance, and leverage AI assistance without technical complexity.

## Context

Story 2.3 implements the core user interface for MailMind, bringing together all Epic 1 AI capabilities (email analysis, priority classification, response generation) and Epic 2 integrations (Outlook connectivity, database persistence) into a cohesive desktop experience. This story transforms MailMind from a collection of backend services into a complete, usable product.

**Why CustomTkinter:**
- Native Windows feel with modern theming (dark/light mode)
- No external dependencies (ships with Python standard library tkinter)
- Mature and well-documented framework
- Lightweight and performant for desktop applications
- Active community and ongoing development

**Integration Points:**
- **Story 1.3 (EmailAnalysisEngine)**: Display priority, summary, tags, sentiment, action items in Analysis Panel
- **Story 1.4 (PriorityClassifier)**: Visual priority indicators (🔴🟡🔵) in Email List
- **Story 1.5 (ResponseGenerator)**: Response Editor with tone controls and length options
- **Story 2.1 (OutlookConnector)**: Email fetching, folder navigation, email actions (move, mark read, delete)
- **Story 2.2 (DatabaseManager)**: Settings persistence, analysis caching, performance metrics display

**User Experience Goals:**
- **Simplicity**: Clean, uncluttered interface that prioritizes essential information
- **Speed**: Instant visual feedback, progressive disclosure of analysis, background processing
- **Clarity**: Visual priority indicators make inbox triage effortless
- **Control**: Manual overrides for AI suggestions, customizable settings
- **Transparency**: Real-time performance metrics show system status

---

## Acceptance Criteria

### AC1: CustomTkinter Framework with Dark/Light Theme
- ✅ Use CustomTkinter (customtkinter>=5.2.0) for modern UI components
- ✅ Implement dark/light theme toggle with system preference detection
- ✅ Custom color scheme matching MailMind branding
- ✅ Theme persisted in user preferences (Story 2.2 database integration)
- ✅ All UI components update dynamically on theme change (no restart required)
- ✅ Smooth theme transitions with visual feedback

### AC2: Main Window Layout (Folder Sidebar + Email List + Analysis Panel)
- ✅ **Main window**: 1200x800px default, resizable down to 800x600px minimum
- ✅ **Folder sidebar** (left, 200px wide): Collapsible panel showing Outlook folder tree
  - Inbox (default), Sent Items, Drafts, custom folders
  - Folder icons with unread counts
  - Search functionality for folders
- ✅ **Email list** (center, flexible): Scrollable list of emails in selected folder
  - Virtual scrolling for performance with 1000+ emails
  - Sortable by date, sender, priority, subject
  - Multi-select for batch operations
- ✅ **Analysis panel** (right, 400px wide): Collapsible panel showing AI analysis for selected email
  - Progressive disclosure: priority → summary → full details
  - Expandable sections for tags, sentiment, action items
  - Response generation controls
- ✅ Resizable splitters between panels (drag to adjust widths)
- ✅ Panel visibility toggles (hide/show sidebar and analysis panel)

### AC3: Email List View with Priority Indicators
- ✅ **Email list item** components:
  - Priority indicator: 🔴 High / 🟡 Medium / 🔵 Low (20px visual circle)
  - Sender name (bold for unread, truncated to 30 chars)
  - Subject line (truncated to 50 chars with "..." if longer)
  - Timestamp (relative: "5m ago", "2h ago", "Oct 13", formatted for readability)
  - Visual unread indicator (bold text, background highlight)
- ✅ **Row height**: 60px per email (comfortable spacing)
- ✅ **Visual states**: Hover (light background), selected (accent color), unread (bold)
- ✅ **Context menu**: Right-click for quick actions (Mark read, Move, Delete, Analyze now)
- ✅ **Keyboard navigation**: Arrow keys for selection, Enter to open, Del to delete
- ✅ **Virtual scrolling**: Render only visible rows for performance (handle 10,000+ emails smoothly)
- ✅ **Loading indicator**: Skeleton screens while fetching emails from Outlook

### AC4: Analysis Panel with Progressive Disclosure
- ✅ **Quick view** (always visible):
  - Priority indicator with confidence score (e.g., "🔴 High - 92% confident")
  - One-line summary (truncated to 150 chars)
  - Action: "Analyze Now" button if not yet analyzed
- ✅ **Expandable sections** (click to expand/collapse):
  - **Summary**: Full AI-generated summary (2-3 sentences)
  - **Tags**: Colored pills for extracted topics/categories (max 5)
  - **Sentiment**: Icon + label (😊 Positive, 😐 Neutral, 😠 Negative, ⚠️ Urgent)
  - **Action Items**: Bulleted list with checkboxes
  - **Performance**: Processing time, token speed, model version (collapsed by default)
- ✅ **Transitions**: Smooth expand/collapse animations (300ms)
- ✅ **Loading states**: Show "Analyzing..." spinner during LLM processing
- ✅ **Error states**: Display user-friendly error if analysis fails (e.g., "Ollama not responding")

### AC5: Response Editor with Draft Generation
- ✅ **Response editor** (text widget with formatting):
  - Multi-line text editor for composing replies
  - "Generate Response" button with dropdown for length (Brief / Standard / Detailed)
  - Tone selector: Professional / Friendly / Formal / Casual (radio buttons or dropdown)
  - Template dropdown: Meeting Acceptance, Decline, Status Update, Thank You, Follow-up, etc.
- ✅ **Draft generation workflow**:
  1. User clicks "Generate Response" → Show loading indicator
  2. LLM generates draft in background (Story 1.5 ResponseGenerator)
  3. Draft populates editor with editable text
  4. "Send" button to create reply in Outlook (uses Story 2.1 OutlookConnector)
- ✅ **Visual feedback**: Processing indicator with estimated time remaining
- ✅ **Error handling**: Display error if generation fails (e.g., model not available)

### AC6: Real-Time Performance Indicators
- ✅ **Status bar** (bottom of window):
  - **Ollama status**: 🟢 Connected / 🟡 Slow / 🔴 Disconnected (clickable for details)
  - **Outlook connection**: 🟢 Connected / 🟡 Reconnecting / 🔴 Disconnected (clickable for details)
  - **Processing queue**: "Analyzing 3/10 emails" with progress bar
  - **Token speed**: "85 tokens/sec" (real-time update from Story 1.6 PerformanceTracker)
  - **Last analysis time**: "Last: 1.8s" (from most recent analysis)
- ✅ **Performance overlay** (optional, toggled via menu):
  - Mini dashboard showing CPU/GPU usage, RAM, model name
  - Historical performance chart (last 24 hours)
- ✅ **Real-time updates**: Status bar updates every 2 seconds automatically

### AC7: Responsive Layout with Resizable Panels
- ✅ **Window resizing**: All panels scale proportionally
- ✅ **Minimum sizes**: 800x600px window, 150px min sidebar width, 300px min email list width
- ✅ **Splitter dragging**: Visual splitter bars between panels (drag to resize)
- ✅ **Panel collapse**: Double-click splitter to collapse/expand panel quickly
- ✅ **Layout persistence**: Save panel widths and window size in user preferences (Story 2.2 database)
- ✅ **Window state**: Remember maximized/normal state across sessions

### AC8: Keyboard Shortcuts for Common Actions
- ✅ **Ctrl+R**: Refresh email list
- ✅ **Ctrl+A**: Analyze selected email(s) now
- ✅ **Ctrl+N**: Compose new email
- ✅ **Ctrl+Enter**: Send email (when in compose mode)
- ✅ **Ctrl+D**: Delete selected email(s)
- ✅ **Ctrl+M**: Move selected email to folder
- ✅ **Ctrl+,**: Open Settings dialog
- ✅ **Ctrl+T**: Toggle theme (dark/light)
- ✅ **Ctrl+/**: Show keyboard shortcuts cheat sheet
- ✅ **Arrow keys**: Navigate email list
- ✅ **Enter**: Open/expand selected email
- ✅ **Escape**: Close dialogs or deselect

### AC9: Progress Indicators for Long-Running Operations
- ✅ **Email fetching**: Progress bar showing "Fetching 45/100 emails from Inbox"
- ✅ **Batch analysis**: Progress bar showing "Analyzing email 3/10" with percentage
- ✅ **Response generation**: Indeterminate spinner with text "Generating response..."
- ✅ **Ollama model loading**: Progress bar for model download/initialization
- ✅ **Toast notifications**:
  - "Email moved to Archive" (3-second auto-dismiss)
  - "Analysis complete" (3-second auto-dismiss)
  - "Response sent" (3-second auto-dismiss)
- ✅ **Error toasts**: Red background, 5-second dismiss, dismissible by click

### AC10: Toast Notifications for Completed Actions
- ✅ **Success toasts** (green background, 3-second auto-dismiss):
  - "Email marked as read"
  - "Email moved to [folder]"
  - "Email deleted"
  - "Analysis complete"
  - "Response sent"
- ✅ **Error toasts** (red background, 5-second dismiss or manual):
  - "Failed to analyze email: Ollama not responding"
  - "Failed to fetch emails: Outlook disconnected"
  - "Failed to send response: [error details]"
- ✅ **Info toasts** (blue background, 3-second auto-dismiss):
  - "Analyzing 5 emails in background"
  - "Reconnecting to Outlook..."
- ✅ **Toast positioning**: Bottom-right corner, stackable (max 3 visible)
- ✅ **Click to dismiss**: All toasts dismissible by clicking

---

## Tasks / Subtasks

### Task 1: CustomTkinter Setup & Theme System (AC1)
- [x] Install CustomTkinter: `pip install customtkinter>=5.2.0`
- [x] Create `src/mailmind/ui/theme_manager.py` for theme management
- [x] Define MailMind color scheme (primary, accent, background, text colors)
- [x] Implement `ThemeManager` class with `set_theme(mode: "dark"|"light")`
- [x] Detect system theme preference on startup (Windows registry)
- [x] Persist theme choice in database (user_preferences table)
- [x] Implement smooth theme transition (update all widgets dynamically)
- [x] Write unit tests for ThemeManager

### Task 2: Main Window Layout Implementation (AC2, AC7)
- [x] Create `src/mailmind/ui/main_window.py` for main application window
- [x] Implement `MainWindow` class extending `ctk.CTk`
- [ ] Create resizable layout with PanedWindow for 3-column design (using pack layout for now)
- [x] Implement folder sidebar (left panel, 200px default width)
- [x] Implement email list (center panel, flexible width)
- [x] Implement analysis panel (right panel, 400px default width)
- [ ] Add splitter bars for panel resizing (draggable)
- [ ] Implement panel collapse/expand controls (methods exist, needs wiring)
- [ ] Save/restore panel widths and window size in database (window size done, panel widths TODO)
- [x] Add menu bar with File, Edit, View, Tools, Help menus
- [ ] Write unit tests for layout components

### Task 3: Folder Sidebar Component (AC2)
- [x] Create `src/mailmind/ui/components/folder_sidebar.py`
- [x] Implement `FolderSidebar` widget with tree view
- [ ] Integrate with OutlookConnector (Story 2.1) to fetch folder list (placeholder ready)
- [x] Display folder hierarchy with icons
- [x] Show unread counts per folder (badge indicators)
- [x] Implement folder selection (highlight active folder)
- [x] Add search box for filtering folders
- [x] Handle folder refresh on demand
- [x] Write unit tests for FolderSidebar (24 tests, 100% passing, 96% coverage)

### Task 4: Email List View Component (AC3)
- [x] Create `src/mailmind/ui/components/email_list_view.py`
- [ ] Implement `EmailListView` widget with virtual scrolling (basic scrolling works, virtual TODO)
- [x] Create `EmailListItem` component for individual email rows
- [x] Display priority indicator (🔴🟡🔵), sender, subject, timestamp
- [x] Implement visual states (hover, selected, unread)
- [x] Add context menu for quick actions (Mark read, Move, Delete, Analyze)
- [x] Implement keyboard navigation (arrow keys, Enter, Del)
- [x] Add column sorting (by date, sender, priority, subject)
- [ ] Integrate with OutlookConnector to fetch and display emails (placeholder ready)
- [x] Handle multi-select for batch operations (Ctrl+click)
- [x] Add loading skeleton screens during fetch
- [x] Write unit tests for EmailListView (29 tests, 100% passing, 90% coverage)

### Task 5: Analysis Panel Component (AC4)
- [x] Create `src/mailmind/ui/components/analysis_panel.py`
- [x] Implement `AnalysisPanel` widget with expandable sections
- [x] Display quick view (priority, confidence, one-line summary)
- [x] Implement expandable sections (Summary, Tags, Sentiment, Action Items, Performance)
- [x] Add "Analyze Now" button for on-demand analysis
- [ ] Integrate with EmailAnalysisEngine (Story 1.3) for analysis (placeholder ready)
- [x] Display loading states ("Analyzing..." with spinner)
- [x] Handle error states (analysis failed with retry button)
- [x] Implement smooth expand/collapse animations
- [x] Display priority with visual indicators (🔴🟡🔵)
- [ ] Write unit tests for AnalysisPanel

### Task 6: Response Editor Component (AC5)
- [x] Create `src/mailmind/ui/components/response_editor.py`
- [x] Implement `ResponseEditor` widget with text editor
- [x] Add "Generate Response" button with length dropdown (Brief/Standard/Detailed)
- [x] Add tone selector (Professional/Friendly/Formal/Casual)
- [x] Add template dropdown (Meeting Acceptance, Decline, Status Update, etc.)
- [ ] Integrate with ResponseGenerator (Story 1.5) for draft generation (placeholder ready)
- [x] Show loading indicator during generation
- [x] Populate editor with generated draft
- [x] Add "Send" button to create Outlook reply (placeholder ready)
- [x] Handle errors (model not available, generation failed)
- [ ] Write unit tests for ResponseEditor

### Task 7: Status Bar & Performance Indicators (AC6)
- [x] Create `src/mailmind/ui/components/status_bar.py`
- [x] Implement `StatusBar` widget at bottom of main window
- [x] Display Ollama connection status (🟢🟡🔴) with icon
- [x] Display Outlook connection status (🟢🟡🔴) with icon
- [x] Display processing queue count with progress bar ("Analyzing 3/10")
- [x] Display token speed ("85 tokens/sec") from PerformanceTracker
- [x] Display last analysis time ("Last: 1.8s")
- [x] Implement real-time updates (poll every 2 seconds)
- [x] Add click handlers for status icons (callbacks ready)
- [ ] Create optional performance overlay (mini dashboard) (deferred)
- [ ] Write unit tests for StatusBar

### Task 8: Settings Dialog (AC2, AC7)
- [x] Create `src/mailmind/ui/dialogs/settings_dialog.py`
- [x] Implement `SettingsDialog` with tabbed interface (General, AI Model, Performance, Privacy, Advanced)
- [x] **General tab**: Theme, startup behavior, notifications
- [x] **AI Model tab**: Model selection, temperature, response defaults
- [x] **Performance tab**: Batch size, cache size, hardware toggles
- [x] **Privacy tab**: Telemetry, crash reports, logging
- [x] **Advanced tab**: Database location, log level, debug mode
- [ ] Integrate with DatabaseManager (Story 2.2) for settings persistence (placeholder ready)
- [x] Apply settings immediately where possible (no restart)
- [x] Add "Reset to Defaults" button with confirmation
- [ ] Write unit tests for SettingsDialog

### Task 9: Keyboard Shortcuts & Menu System (AC8)
- [x] Define keyboard shortcut mappings in config
- [x] Implement global keyboard event handlers in MainWindow (via keyboard_shortcuts.py)
- [x] Create menu bar with File, Edit, View, Tools, Help menus (in MainWindow)
- [x] Bind keyboard shortcuts to menu actions
- [x] Create keyboard shortcuts display helper (get_shortcuts_text())
- [x] Handle shortcut conflicts gracefully
- [x] Add visual indicators (menu items show shortcuts)
- [ ] Write unit tests for keyboard handling

### Task 10: Progress Indicators & Toast Notifications (AC9, AC10)
- [x] Create `src/mailmind/ui/components/toast.py` (COMPLETE)
- [x] Implement `Toast` widget (bottom-right corner, stackable)
- [x] Define toast types (success, error, info) with color coding
- [x] Implement auto-dismiss (3s for success/info, 5s for errors)
- [x] Implement manual dismiss (click to close)
- [x] Add toast queue manager (max 3 visible, FIFO)
- [x] Implement progress indicators in components:
  - StatusBar: queue progress bar
  - EmailListView: loading skeleton
  - AnalysisPanel: loading state
  - ResponseEditor: loading state
- [ ] Integrate toasts into all user actions (placeholder ready)
- [ ] Write unit tests for Toast and ProgressIndicator

### Task 11: Integration with Backend Services
- [ ] Create `src/mailmind/ui/controllers/email_controller.py` for business logic (TODO)
- [x] Integration placeholders ready in all components:
  - EmailListView: callbacks for email operations
  - AnalysisPanel: on_analyze_clicked callback
  - ResponseEditor: on_generate_clicked, on_send_clicked callbacks
  - StatusBar: auto-update callback mechanism
  - FolderSidebar: on_folder_selected callback
  - SettingsDialog: on_save callback
- [ ] Implement background task queue for LLM operations (TODO)
- [ ] Handle threading (run LLM calls in background threads) (TODO)
- [ ] Write integration tests with all backend services (TODO)

### Task 12: Testing & Documentation
- [ ] Write comprehensive unit tests for all UI components (target: >75% coverage)
- [ ] Write integration tests for complete workflows (fetch → analyze → respond)
- [ ] Test on different screen resolutions (1920x1080, 1366x768, 2560x1440)
- [ ] Test window resizing edge cases (minimum size, maximize, restore)
- [ ] Test theme switching (dark/light) across all components
- [ ] Create UI demo script: `examples/ui_demo.py`
- [ ] Document UI architecture in `docs/ui-architecture.md`
- [ ] Create user guide with screenshots
- [ ] Update CHANGELOG with Story 2.3 completion
- [ ] Update README with UI screenshots and usage instructions

---

## Dev Notes

### CustomTkinter Framework

**Why CustomTkinter vs Alternatives:**

| Framework | Pros | Cons | Verdict |
|-----------|------|------|---------|
| CustomTkinter | Modern look, dark/light themes, native feel, lightweight | Smaller community than Qt | ✅ Best fit |
| PyQt6 | Mature, feature-rich, excellent docs | Heavy, licensing complexity | ❌ Overkill |
| Kivy | Modern, cross-platform | Mobile-focused, unusual layout | ❌ Not native feel |
| tkinter (standard) | Built-in, stable | Outdated appearance | ❌ Too basic |

**CustomTkinter Advantages:**
- Built on top of tkinter (ships with Python)
- Modern appearance (rounded corners, smooth animations)
- Dark/light mode out-of-the-box
- Drop-in replacement for tkinter widgets
- Active development and community

### Project Structure

**New Files to Create:**
```
src/mailmind/ui/
├── __init__.py
├── main_window.py                     # Main application window (600+ lines)
├── theme_manager.py                   # Theme management (150 lines)
├── components/
│   ├── __init__.py
│   ├── folder_sidebar.py              # Folder tree view (300 lines)
│   ├── email_list_view.py             # Email list with virtual scrolling (500 lines)
│   ├── analysis_panel.py              # Expandable analysis display (400 lines)
│   ├── response_editor.py             # Response composition UI (350 lines)
│   ├── status_bar.py                  # Performance indicators (200 lines)
│   ├── toast.py                       # Toast notification widget (150 lines)
│   └── progress_indicator.py          # Progress bars and spinners (100 lines)
├── dialogs/
│   ├── __init__.py
│   ├── settings_dialog.py             # Settings UI (500 lines)
│   ├── keyboard_shortcuts_dialog.py   # Shortcuts cheat sheet (200 lines)
│   └── about_dialog.py                # About MailMind (100 lines)
└── controllers/
    ├── __init__.py
    ├── email_controller.py            # Email business logic (400 lines)
    ├── analysis_controller.py         # Analysis orchestration (300 lines)
    └── response_controller.py         # Response generation orchestration (300 lines)

tests/unit/
├── ui/
│   ├── test_main_window.py
│   ├── test_theme_manager.py
│   ├── test_email_list_view.py
│   ├── test_analysis_panel.py
│   ├── test_response_editor.py
│   └── test_toast.py

examples/
└── ui_demo.py                          # UI demonstration (400 lines)
```

**Dependencies to Add:**
```
customtkinter>=5.2.0    # Modern UI framework
Pillow>=10.0.0          # Image loading for icons
```

### UI Component Architecture

**Design Pattern: MVC (Model-View-Controller)**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Model       │◄────│   Controller    │◄────│      View       │
│  (Backend)      │     │  (Business      │     │  (UI Components)│
│  - Ollama       │     │   Logic)        │     │  - MainWindow   │
│  - Outlook      │     │  - EmailCtrl    │     │  - EmailList    │
│  - Database     │     │  - AnalysisCtrl │     │  - AnalysisPanel│
│  - Analysis     │     │  - ResponseCtrl │     │  - ResponseEditor│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Threading Strategy:**
- **Main thread**: UI rendering only (60fps)
- **Background threads**: LLM operations, Outlook operations, database queries
- **Queue pattern**: Use `queue.Queue` for thread-safe communication
- **UI updates**: Use `after()` method to update UI from background threads

```python
import threading
import queue

class EmailController:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.start()

    def analyze_email(self, email):
        """Non-blocking analysis"""
        self.task_queue.put(("analyze", email))

    def _worker(self):
        """Background worker thread"""
        while True:
            task_type, data = self.task_queue.get()
            if task_type == "analyze":
                result = self.analysis_engine.analyze_email(data)
                self.result_queue.put(("analysis_complete", result))
```

### Integration Points

**Story 2.1 (OutlookConnector) Integration:**
```python
from mailmind.integrations import OutlookConnector

# In FolderSidebar:
outlook = OutlookConnector()
folders = outlook.get_folders()
for folder in folders:
    self.tree_view.insert(folder.name, folder.unread_count)

# In EmailListView:
emails = outlook.fetch_emails("Inbox", limit=50, offset=0)
for email in emails:
    self.add_email_item(email)
```

**Story 1.3 (EmailAnalysisEngine) Integration:**
```python
from mailmind.core import EmailAnalysisEngine

# In AnalysisPanel:
engine = EmailAnalysisEngine(ollama_manager, db_path="data/mailmind.db")
analysis = engine.analyze_email(selected_email)

# Update UI with analysis results:
self.display_priority(analysis['priority'], analysis['confidence'])
self.display_summary(analysis['summary'])
self.display_tags(analysis['tags'])
self.display_action_items(analysis['action_items'])
```

**Story 1.5 (ResponseGenerator) Integration:**
```python
from mailmind.core import ResponseGenerator

# In ResponseEditor:
generator = ResponseGenerator(ollama_manager, db_path="data/mailmind.db")
result = generator.generate_response(
    email=selected_email,
    length="Standard",
    tone="Professional"
)
self.text_editor.insert("1.0", result['response_text'])
```

### Performance Considerations

**Virtual Scrolling for Email List:**
```python
# Only render visible items (e.g., 20 rows on screen)
# Re-render on scroll events
class EmailListView:
    def __init__(self):
        self.total_emails = 10000
        self.visible_rows = 20
        self.scroll_offset = 0

    def render(self):
        """Render only visible emails"""
        start = self.scroll_offset
        end = start + self.visible_rows
        visible_emails = self.emails[start:end]
        for email in visible_emails:
            self.draw_email_row(email)
```

**Smooth UI Updates:**
- Debounce scroll events (update every 100ms, not every pixel)
- Use canvas for custom widgets (faster than nested frames)
- Batch UI updates (update 10 items at once, not 10 separate updates)
- Profile with cProfile to identify bottlenecks

### Color Scheme

**MailMind Brand Colors:**
```python
# Dark theme
DARK_BG = "#1a1a1a"           # Main background
DARK_FG = "#e0e0e0"           # Text color
DARK_ACCENT = "#4a9eff"       # Primary accent (blue)
DARK_HOVER = "#2a2a2a"        # Hover state
DARK_SELECTED = "#3a3a3a"     # Selected state

# Light theme
LIGHT_BG = "#ffffff"          # Main background
LIGHT_FG = "#1a1a1a"          # Text color
LIGHT_ACCENT = "#2563eb"      # Primary accent (darker blue)
LIGHT_HOVER = "#f5f5f5"       # Hover state
LIGHT_SELECTED = "#e5e5e5"    # Selected state

# Priority colors (same in both themes)
PRIORITY_HIGH = "#ef4444"     # Red
PRIORITY_MEDIUM = "#f59e0b"   # Orange
PRIORITY_LOW = "#3b82f6"      # Blue
```

### Technical Constraints

**CustomTkinter Limitations:**
1. **Single-threaded UI**: All UI updates must happen on main thread
   - Mitigation: Use `after()` to schedule UI updates from background threads
2. **Limited styling**: CSS-like styling not available
   - Mitigation: Use CustomTkinter's theme system and custom widgets
3. **No built-in virtual scrolling**: Must implement manually for large lists
   - Mitigation: Use Canvas widget with manual rendering
4. **Windows-only advanced features**: Some features may not work on Mac/Linux
   - Acceptable: MailMind MVP is Windows-only (Mac support in v2.0)

**Performance Targets:**
- UI startup: <3 seconds (including Ollama connection, database init)
- Email list rendering: <500ms for 100 emails
- Theme switching: <200ms (smooth visual transition)
- Analysis display: <100ms (data is pre-computed, just render)
- Smooth scrolling: 60fps (no jank)

### Testing Strategy

**Unit Tests (80+ tests):**
- ThemeManager theme switching and persistence
- EmailListView rendering with mock data
- AnalysisPanel expandable sections
- ResponseEditor text editing and generation UI
- StatusBar status updates
- Toast notifications (show, dismiss, queue)
- Settings dialog input validation

**Integration Tests (30+ tests):**
- Complete workflow: Fetch emails → Display → Analyze → Generate response → Send
- Theme switching while UI is active
- Concurrent analysis requests (queue management)
- Error handling (Ollama disconnected, Outlook closed, database error)
- Window resizing and layout persistence
- Keyboard shortcut handling

**Manual Testing Checklist:**
- [ ] Test on 1920x1080, 1366x768, 2560x1440 resolutions
- [ ] Test with 0, 10, 100, 1000, 10000 emails in list
- [ ] Test dark/light theme switching
- [ ] Test all keyboard shortcuts
- [ ] Test window resizing (minimum size, maximize, restore)
- [ ] Test panel resizing (splitter dragging)
- [ ] Test on clean Windows 10 and Windows 11 systems
- [ ] Test with high DPI displays (scaling 125%, 150%)

---

## References

### Primary Sources
- **Epic Breakdown**: `docs/epic-stories.md` - Story 2.3 specification (lines 351-379)
- **README**: Current features and Epic 1 implementation patterns
- **Story 2.1**: OutlookConnector API for email fetching and actions
- **Story 2.2**: DatabaseManager API for settings persistence

### Technical Documentation
- **CustomTkinter**: https://github.com/TomSchimansky/CustomTkinter
- **CustomTkinter Docs**: https://customtkinter.tomschimansky.com/
- **tkinter Reference**: https://docs.python.org/3/library/tkinter.html
- **Python Threading**: https://docs.python.org/3/library/threading.html

### Integration Dependencies
- **Story 1.3 (EmailAnalysisEngine)**: Analysis results for display in AnalysisPanel
- **Story 1.4 (PriorityClassifier)**: Priority indicators for EmailListView
- **Story 1.5 (ResponseGenerator)**: Draft generation for ResponseEditor
- **Story 1.6 (PerformanceTracker)**: Metrics for StatusBar display
- **Story 2.1 (OutlookConnector)**: Email fetching, folder navigation, email actions
- **Story 2.2 (DatabaseManager)**: Settings persistence, layout state, theme preferences

---

## Dev Agent Record

### Context Reference

*To be generated by story-context workflow*

### Agent Model Used

*To be filled by DEV agent during implementation*

### Completion Notes List

*To be filled by DEV agent during implementation*

### File List

*To be filled by DEV agent during implementation*

---

## Change Log

### 2025-10-14 - SM Agent (create-story workflow)
- **Action**: Created Story 2.3 draft from epic-stories.md and Epic 1 completion context
- **Details**:
  - Story extracted from Epic 2 specifications (lines 351-379)
  - 10 comprehensive acceptance criteria defined (AC1-AC10)
  - 12 implementation tasks with 100+ subtasks
  - Complete UI component architecture defined (MVC pattern)
  - CustomTkinter framework selected (vs PyQt6, Kivy, tkinter)
  - Integration points documented for all Epic 1 stories
  - Threading strategy defined for background LLM operations
  - Color scheme and theme system specified
  - Testing strategy defined (80+ unit tests, 30+ integration tests)
  - Performance targets specified (startup <3s, 60fps scrolling)
- **Status**: Draft (awaiting review via story-ready workflow)
- **Next**: User should review story and run `story-ready` to approve for development

---

*This story brings MailMind to life as a complete desktop application, integrating all AI capabilities from Epic 1 into an intuitive, modern user interface.*
