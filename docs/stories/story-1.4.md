# Story 1.4: Priority Classification System

**Epic:** Epic 1 - AI-Powered Email Intelligence
**Story ID:** 1.4
**Story Points:** 5
**Priority:** P0 (Critical Path)
**Status:** Draft
**Created:** 2025-10-13

---

## Story Description

As a user, I need emails automatically classified by priority (High/Medium/Low) so that I can focus on what matters most.

## Business Value

This story builds upon Story 1.3's basic priority classification to create an intelligent, learning system:
- Accurate priority classification helps users triage 100-200 emails/day efficiently
- Visual priority indicators (🔴🟡🔵) enable instant inbox scanning
- Learning from user corrections improves accuracy over time (target: >85% within 30 days)
- Manual override capability gives users control while improving the system
- Priority-based inbox organization reduces cognitive load and email stress
- Adaptive classification considers sender importance and historical patterns

Without this story, priority classification is static. This adds personalized learning and continuous improvement.

---

## Acceptance Criteria

### AC1: Priority Classification with Confidence
- [ ] Classify all emails as High, Medium, or Low priority
- [ ] Include confidence score (0.0 - 1.0) for each classification
- [ ] High confidence threshold: >0.8 for actionable recommendations
- [ ] Priority determination factors:
  - Urgency keywords (ASAP, urgent, deadline, critical, emergency)
  - Sender importance (executives, direct manager, VIP contacts)
  - Action requirements (please review, need your input, waiting on you)
  - Explicit deadlines and time constraints
  - Thread context (reply to high-priority thread inherits priority)
- [ ] Confidence increases with user correction history for similar patterns

### AC2: High Priority Detection Logic
- [ ] Urgency indicators: "ASAP", "urgent", "critical", "emergency", "immediately"
- [ ] Action-required phrases: "need your approval", "requires your input", "waiting for you"
- [ ] Deadline detection: "by EOD", "due tomorrow", "deadline Friday"
- [ ] Executive senders: Configurable VIP list + organizational hierarchy detection
- [ ] Time sensitivity: Meeting within 24 hours, expiring offers, last call notices
- [ ] High confidence when 2+ indicators present

### AC3: Medium Priority Detection Logic
- [ ] Project updates and team communications
- [ ] Scheduled meetings (>24 hours out)
- [ ] Internal team discussions and collaboration
- [ ] Information requests without urgency
- [ ] Status reports and progress updates
- [ ] Default classification for known senders without urgency signals

### AC4: Low Priority Detection Logic
- [ ] Newsletters and subscription emails
- [ ] Automated notifications (no-reply senders)
- [ ] Marketing and promotional content
- [ ] Social media notifications
- [ ] Bulk mail and distribution lists
- [ ] FYI-only messages with no action required

### AC5: User Correction & Learning System
- [ ] Store user priority corrections in user_corrections table
- [ ] Track correction type: priority_override, sender_importance, category_adjustment
- [ ] Weight recent corrections (last 30 days) more heavily than older ones
- [ ] Update sender importance scores based on correction patterns
- [ ] Learn urgency keyword patterns from user behavior
- [ ] Display correction impact: "Learning from your feedback" toast notification

### AC6: Sender Importance Tracking
- [ ] Calculate sender importance score based on:
  - Email frequency (emails received in last 90 days)
  - User correction history (priority upgrades/downgrades)
  - Reply rate (user replies to this sender)
  - Manual VIP designation by user
- [ ] Store sender_importance in database (0.0 - 1.0 scale)
- [ ] High importance sender (>0.8) → bias toward Higher priority
- [ ] Low importance sender (<0.3) → bias toward Lower priority
- [ ] Recalculate sender scores weekly

### AC7: Visual Priority Indicators
- [ ] Display priority with color-coded emoji indicators:
  - High: 🔴 Red circle
  - Medium: 🟡 Yellow circle
  - Low: 🔵 Blue circle
- [ ] Show confidence score on hover/click: "High (92% confident)"
- [ ] Priority badge visible in email list view
- [ ] Large priority indicator in email detail view
- [ ] Consistent color scheme across all UI components

### AC8: Manual Priority Override
- [ ] Allow user to manually change email priority
- [ ] Override UI: Dropdown or button group (High/Medium/Low)
- [ ] Immediately update display after override
- [ ] Store override in user_corrections table for learning
- [ ] Feedback prompt: "Why did you change this?" (optional)
  - "Wrong sender importance"
  - "Urgency misdetected"
  - "Category incorrect"
  - "Other"
- [ ] Apply learning to future emails from same sender

### AC9: Accuracy Tracking & Improvement
- [ ] Track classification accuracy over time
- [ ] Calculate accuracy: (Total - Corrections) / Total
- [ ] Target accuracy: >85% after 30 days of use
- [ ] Display accuracy trend in settings/statistics panel
- [ ] Log accuracy metrics to performance_metrics table
- [ ] Weekly accuracy reports with improvement suggestions

---

## Technical Notes

### Dependencies
- **Story 1.3:** EmailAnalysisEngine (basic priority classification) ✅ COMPLETE
- **Story 2.2:** SQLite Database (user_corrections table) - can use in-memory for MVP
- **SQLite:** For storing corrections and sender importance data

### Architecture Overview

```
Email Input
    ↓
EmailAnalysisEngine (Story 1.3) - Basic Priority
    ↓
PriorityClassifier (Story 1.4) - Enhanced Priority
    ↓
Check sender_importance database
    ↓
Apply user correction weights
    ↓
Calculate confidence score
    ↓
Return enhanced priority + confidence
    ↓
Store in email_analysis table
    ↓
User Override? → Store in user_corrections
    ↓
Update sender_importance scores
```

### Database Schema Extensions

```sql
-- Extends email_analysis table from Story 1.3
ALTER TABLE email_analysis ADD COLUMN user_override TEXT;
ALTER TABLE email_analysis ADD COLUMN override_reason TEXT;
ALTER TABLE email_analysis ADD COLUMN original_priority TEXT;

-- New table for user corrections
CREATE TABLE IF NOT EXISTS user_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    sender TEXT NOT NULL,

    -- Original classification
    original_priority TEXT CHECK(original_priority IN ('High', 'Medium', 'Low')),
    original_confidence REAL,

    -- User correction
    user_priority TEXT CHECK(user_priority IN ('High', 'Medium', 'Low')),
    correction_reason TEXT,

    -- Learning data
    correction_type TEXT CHECK(correction_type IN (
        'priority_override',
        'sender_importance',
        'category_adjustment',
        'urgency_misdetection'
    )),

    -- Metadata
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    applied_to_model BOOLEAN DEFAULT 0,

    -- Indexes
    INDEX idx_sender (sender),
    INDEX idx_timestamp (timestamp),
    INDEX idx_applied (applied_to_model)
);

-- New table for sender importance
CREATE TABLE IF NOT EXISTS sender_importance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_email TEXT UNIQUE NOT NULL,
    sender_name TEXT,

    -- Importance scoring
    importance_score REAL DEFAULT 0.5, -- 0.0 to 1.0
    email_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    correction_count INTEGER DEFAULT 0,

    -- User flags
    is_vip BOOLEAN DEFAULT 0,
    is_blocked BOOLEAN DEFAULT 0,

    -- Metadata
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_sender_email (sender_email),
    INDEX idx_importance_score (importance_score),
    INDEX idx_is_vip (is_vip)
);
```

### Enhanced Priority Classification Algorithm

```python
class PriorityClassifier:
    """
    Enhanced priority classification with learning from user corrections.
    Builds upon EmailAnalysisEngine (Story 1.3) basic priority classification.
    """

    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self._init_db()

    def classify_priority(
        self,
        email: Dict[str, Any],
        base_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced priority classification with user learning.

        Args:
            email: Preprocessed email data
            base_analysis: Basic analysis from Story 1.3

        Returns:
            Enhanced priority classification with confidence
        """
        # Start with base priority from Story 1.3
        base_priority = base_analysis['priority']
        base_confidence = base_analysis['confidence']

        # Get sender importance
        sender = email['metadata']['from']
        sender_importance = self._get_sender_importance(sender)

        # Apply sender importance adjustment
        adjusted_priority, confidence = self._adjust_for_sender(
            base_priority,
            base_confidence,
            sender_importance
        )

        # Apply user correction patterns
        correction_adjustment = self._get_correction_adjustment(
            sender,
            email['metadata']['subject'],
            email['content']['body']
        )

        final_priority, final_confidence = self._apply_corrections(
            adjusted_priority,
            confidence,
            correction_adjustment
        )

        return {
            'priority': final_priority,
            'confidence': final_confidence,
            'sender_importance': sender_importance['score'],
            'base_priority': base_priority,
            'adjustments': {
                'sender_adjustment': sender_importance['adjustment'],
                'correction_adjustment': correction_adjustment
            }
        }

    def _get_sender_importance(self, sender: str) -> Dict[str, Any]:
        """Get sender importance score from database."""
        cursor = self.db.execute("""
            SELECT importance_score, is_vip, email_count, reply_count
            FROM sender_importance
            WHERE sender_email = ?
        """, (sender,))

        row = cursor.fetchone()

        if row:
            score, is_vip, email_count, reply_count = row
            return {
                'score': score,
                'is_vip': bool(is_vip),
                'email_count': email_count,
                'reply_count': reply_count,
                'adjustment': self._calculate_sender_adjustment(score, is_vip)
            }
        else:
            # New sender - neutral importance
            return {
                'score': 0.5,
                'is_vip': False,
                'email_count': 0,
                'reply_count': 0,
                'adjustment': 0
            }

    def _calculate_sender_adjustment(
        self,
        importance_score: float,
        is_vip: bool
    ) -> int:
        """
        Calculate priority adjustment based on sender importance.

        Returns:
            +1 (upgrade priority), 0 (no change), -1 (downgrade priority)
        """
        if is_vip or importance_score > 0.8:
            return +1  # Upgrade priority
        elif importance_score < 0.3:
            return -1  # Downgrade priority
        else:
            return 0  # No adjustment

    def _get_correction_adjustment(
        self,
        sender: str,
        subject: str,
        body: str
    ) -> float:
        """
        Get priority adjustment based on user correction history.
        Returns confidence adjustment (-0.3 to +0.3).
        """
        # Get recent corrections for this sender (last 30 days)
        cursor = self.db.execute("""
            SELECT original_priority, user_priority, correction_type
            FROM user_corrections
            WHERE sender = ?
            AND timestamp > datetime('now', '-30 days')
            ORDER BY timestamp DESC
            LIMIT 10
        """, (sender,))

        corrections = cursor.fetchall()

        if not corrections:
            return 0.0

        # Calculate adjustment based on correction patterns
        upgrade_count = sum(1 for orig, user, _ in corrections
                           if self._is_upgrade(orig, user))
        downgrade_count = sum(1 for orig, user, _ in corrections
                             if self._is_downgrade(orig, user))

        total = len(corrections)

        if upgrade_count > downgrade_count:
            # User tends to upgrade this sender
            return +0.2 * (upgrade_count / total)
        elif downgrade_count > upgrade_count:
            # User tends to downgrade this sender
            return -0.2 * (downgrade_count / total)
        else:
            return 0.0

    def _adjust_for_sender(
        self,
        priority: str,
        confidence: float,
        sender_importance: Dict[str, Any]
    ) -> Tuple[str, float]:
        """Apply sender importance adjustment to priority."""
        adjustment = sender_importance['adjustment']

        if adjustment == 0:
            return priority, confidence

        priority_levels = ['Low', 'Medium', 'High']
        current_index = priority_levels.index(priority)

        # Adjust priority
        new_index = max(0, min(2, current_index + adjustment))
        new_priority = priority_levels[new_index]

        # Adjust confidence based on sender data
        if sender_importance['email_count'] > 10:
            # More data = more confidence in adjustment
            confidence_boost = 0.1
        else:
            confidence_boost = 0.0

        new_confidence = min(1.0, confidence + confidence_boost)

        return new_priority, new_confidence

    def _apply_corrections(
        self,
        priority: str,
        confidence: float,
        correction_adjustment: float
    ) -> Tuple[str, float]:
        """Apply user correction patterns to final classification."""
        adjusted_confidence = min(1.0, max(0.0, confidence + correction_adjustment))

        # If confidence is very high/low due to corrections, may adjust priority
        if correction_adjustment > 0.2 and priority != 'High':
            priority = self._upgrade_priority(priority)
        elif correction_adjustment < -0.2 and priority != 'Low':
            priority = self._downgrade_priority(priority)

        return priority, adjusted_confidence

    def record_user_override(
        self,
        message_id: str,
        sender: str,
        original_priority: str,
        original_confidence: float,
        user_priority: str,
        reason: Optional[str] = None
    ) -> None:
        """
        Record user priority override for learning.

        Args:
            message_id: Email message ID
            sender: Email sender address
            original_priority: System's original classification
            original_confidence: System's confidence score
            user_priority: User's corrected priority
            reason: Optional reason for correction
        """
        # Determine correction type
        correction_type = self._determine_correction_type(
            original_priority,
            user_priority,
            reason
        )

        # Store correction
        self.db.execute("""
            INSERT INTO user_corrections (
                message_id, sender,
                original_priority, original_confidence,
                user_priority, correction_reason, correction_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id, sender,
            original_priority, original_confidence,
            user_priority, reason, correction_type
        ))

        # Update sender importance
        self._update_sender_importance(sender, original_priority, user_priority)

        self.db.commit()

    def _update_sender_importance(
        self,
        sender: str,
        original_priority: str,
        user_priority: str
    ) -> None:
        """Update sender importance based on correction."""
        # Get current importance
        cursor = self.db.execute("""
            SELECT importance_score, correction_count
            FROM sender_importance
            WHERE sender_email = ?
        """, (sender,))

        row = cursor.fetchone()

        if row:
            current_score, correction_count = row
        else:
            current_score, correction_count = 0.5, 0

        # Calculate adjustment
        if self._is_upgrade(original_priority, user_priority):
            # User upgraded - increase importance
            adjustment = +0.05
        elif self._is_downgrade(original_priority, user_priority):
            # User downgraded - decrease importance
            adjustment = -0.05
        else:
            adjustment = 0.0

        new_score = max(0.0, min(1.0, current_score + adjustment))
        new_correction_count = correction_count + 1

        # Update or insert
        self.db.execute("""
            INSERT INTO sender_importance (
                sender_email, importance_score, correction_count, last_updated
            ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(sender_email) DO UPDATE SET
                importance_score = ?,
                correction_count = ?,
                last_updated = CURRENT_TIMESTAMP
        """, (sender, new_score, new_correction_count, new_score, new_correction_count))

    def get_classification_accuracy(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate classification accuracy over time period.

        Args:
            days: Number of days to analyze

        Returns:
            Accuracy metrics dictionary
        """
        # Count total classifications
        cursor = self.db.execute("""
            SELECT COUNT(*) FROM email_analysis
            WHERE processed_date > datetime('now', ? || ' days')
        """, (f'-{days}',))
        total = cursor.fetchone()[0]

        # Count corrections
        cursor = self.db.execute("""
            SELECT COUNT(*) FROM user_corrections
            WHERE timestamp > datetime('now', ? || ' days')
        """, (f'-{days}',))
        corrections = cursor.fetchone()[0]

        if total == 0:
            accuracy = 0.0
        else:
            accuracy = (total - corrections) / total

        return {
            'accuracy_percentage': accuracy * 100,
            'total_classified': total,
            'user_corrections': corrections,
            'period_days': days,
            'target_met': accuracy >= 0.85
        }

    @staticmethod
    def _is_upgrade(original: str, new: str) -> bool:
        """Check if new priority is higher than original."""
        levels = {'Low': 0, 'Medium': 1, 'High': 2}
        return levels[new] > levels[original]

    @staticmethod
    def _is_downgrade(original: str, new: str) -> bool:
        """Check if new priority is lower than original."""
        levels = {'Low': 0, 'Medium': 1, 'High': 2}
        return levels[new] < levels[original]

    @staticmethod
    def _upgrade_priority(priority: str) -> str:
        """Upgrade priority by one level."""
        if priority == 'Low':
            return 'Medium'
        elif priority == 'Medium':
            return 'High'
        return 'High'

    @staticmethod
    def _downgrade_priority(priority: str) -> str:
        """Downgrade priority by one level."""
        if priority == 'High':
            return 'Medium'
        elif priority == 'Medium':
            return 'Low'
        return 'Low'
```

### Integration with Story 1.3

```python
# Integration example
from mailmind.core.email_analysis_engine import EmailAnalysisEngine
from mailmind.core.priority_classifier import PriorityClassifier

# Initialize components
analysis_engine = EmailAnalysisEngine(ollama_manager, db_path)
priority_classifier = PriorityClassifier(db_path)

# Analyze email with enhanced priority
def analyze_email_with_learning(raw_email):
    # Step 1: Basic analysis (Story 1.3)
    base_analysis = analysis_engine.analyze_email(raw_email)

    # Step 2: Enhanced priority classification (Story 1.4)
    enhanced_priority = priority_classifier.classify_priority(
        raw_email,
        base_analysis
    )

    # Step 3: Merge results
    final_analysis = {
        **base_analysis,
        'priority': enhanced_priority['priority'],
        'confidence': enhanced_priority['confidence'],
        'sender_importance': enhanced_priority['sender_importance'],
        'priority_adjustments': enhanced_priority['adjustments']
    }

    return final_analysis

# User overrides priority
def handle_priority_override(message_id, new_priority, reason=None):
    # Get original analysis
    original = get_original_analysis(message_id)

    # Record correction
    priority_classifier.record_user_override(
        message_id=message_id,
        sender=original['sender'],
        original_priority=original['priority'],
        original_confidence=original['confidence'],
        user_priority=new_priority,
        reason=reason
    )

    # Update display
    update_email_priority_display(message_id, new_priority)

    # Show feedback toast
    show_toast("Learning from your feedback")
```

---

## Testing Checklist

### Unit Tests
- [ ] Test PriorityClassifier initialization
- [ ] Test sender importance scoring calculation
- [ ] Test priority adjustment for VIP senders
- [ ] Test priority adjustment for low-importance senders
- [ ] Test user correction recording
- [ ] Test sender importance updates after corrections
- [ ] Test classification accuracy calculation
- [ ] Test priority upgrade/downgrade logic
- [ ] Test correction adjustment calculations
- [ ] Test database schema creation
- [ ] Test edge cases: new senders, missing data

### Integration Tests
- [ ] Test full pipeline: base analysis → enhanced classification
- [ ] Test with real email database (10+ emails)
- [ ] Test user override flow end-to-end
- [ ] Test sender importance evolution over time (simulated)
- [ ] Test accuracy tracking over 30-day period (simulated)
- [ ] Test database persistence across sessions
- [ ] Test with various sender patterns (VIP, newsletter, spam)

### Learning System Tests
- [ ] Test correction learning: 10 corrections → improved accuracy
- [ ] Test sender importance increase after upgrades
- [ ] Test sender importance decrease after downgrades
- [ ] Test VIP sender always gets high priority
- [ ] Test blocked sender always gets low priority
- [ ] Test correction weight decay (older corrections less impactful)
- [ ] Test accuracy target: >85% after 30 days of corrections

### UI/UX Tests
- [ ] Test priority indicator display (🔴🟡🔵)
- [ ] Test confidence score tooltip display
- [ ] Test manual override dropdown functionality
- [ ] Test override reason selection
- [ ] Test "Learning from feedback" toast notification
- [ ] Test accuracy display in settings panel
- [ ] Test visual consistency across email list and detail views

### Performance Tests
- [ ] Sender importance lookup <10ms
- [ ] Correction adjustment calculation <5ms
- [ ] Total enhanced classification overhead <50ms
- [ ] Database write for correction <20ms
- [ ] Accuracy calculation for 30 days <100ms

### Edge Cases
- [ ] New sender (no history) → neutral importance
- [ ] Sender with 1 email → low confidence adjustment
- [ ] Sender with 100+ emails → high confidence adjustment
- [ ] Conflicting corrections (upgrade then downgrade) → neutral
- [ ] VIP sender with low-priority email content
- [ ] Blocked sender trying to send urgent email
- [ ] Database corruption or missing tables
- [ ] Very old corrections (>90 days) have minimal impact

---

## Performance Targets

| Operation | Target | Acceptable | Critical |
|-----------|--------|------------|----------|
| **Enhanced Classification** | <50ms | <100ms | <200ms |
| **Sender Importance Lookup** | <10ms | <20ms | <50ms |
| **Record User Correction** | <20ms | <50ms | <100ms |
| **Update Sender Importance** | <30ms | <75ms | <150ms |
| **Calculate Accuracy (30 days)** | <100ms | <200ms | <500ms |

**Accuracy Targets:**
- Week 1: >60% accuracy (baseline)
- Week 2: >70% accuracy (improving)
- Week 4: >85% accuracy ✅ (target met)
- Week 8: >90% accuracy (excellent)

**User Correction Rate:**
- Target: <15% of emails require manual override
- Acceptable: <25% of emails require override
- Alert threshold: >30% correction rate (system not learning effectively)

---

## Definition of Done

- [ ] All acceptance criteria met (AC1-AC9)
- [ ] PriorityClassifier class implemented
- [ ] Integration with EmailAnalysisEngine (Story 1.3) complete
- [ ] Database schema extended with user_corrections and sender_importance tables
- [ ] User correction recording and application implemented
- [ ] Sender importance tracking implemented
- [ ] Visual priority indicators implemented (🔴🟡🔵)
- [ ] Manual priority override UI implemented
- [ ] Accuracy tracking and reporting implemented
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration tests with learning system passing
- [ ] Performance targets met for all operations
- [ ] User feedback toast notifications working
- [ ] Error handling for all failure modes
- [ ] Code reviewed and approved
- [ ] Documentation updated:
  - Module docstrings complete
  - API documentation for PriorityClassifier
  - Learning system explanation in README
- [ ] Demo script showing priority learning over time
- [ ] Accuracy metrics dashboard created

---

## Dependencies & Blockers

**Upstream Dependencies:**
- Story 1.3 (Real-Time Analysis Engine) - COMPLETE ✅

**Downstream Dependencies:**
- Story 1.5 (Response Generation) can use priority for response urgency
- Story 2.2 (SQLite Database) provides production database schema
- Story 2.3 (UI) displays priority indicators and override controls
- Story 2.4 (Settings) allows VIP configuration and accuracy viewing

**External Dependencies:**
- SQLite3 (Python stdlib)

**Potential Blockers:**
- User correction rate may be lower than expected (limits learning)
- Sender importance algorithm may need tuning
- Accuracy target (>85%) may require more sophisticated ML

---

## Implementation Plan

### Phase 1: Database Schema & Core Logic (Day 1)
1. Create database schema extensions (user_corrections, sender_importance)
2. Implement PriorityClassifier class skeleton
3. Implement sender importance lookup and scoring
4. Implement basic priority adjustment logic
5. Add unit tests for core functions

### Phase 2: User Correction System (Day 2)
1. Implement user correction recording
2. Implement sender importance updates
3. Implement correction pattern analysis
4. Add correction adjustment to classification
5. Test correction learning with simulated data

### Phase 3: Integration & Accuracy Tracking (Day 3)
1. Integrate PriorityClassifier with EmailAnalysisEngine
2. Implement accuracy tracking calculations
3. Add accuracy reporting functions
4. Test end-to-end learning pipeline
5. Tune adjustment weights for optimal accuracy

### Phase 4: Testing & Documentation (Day 4)
1. Write comprehensive unit tests
2. Write integration tests with learning scenarios
3. Performance testing and optimization
4. Create demo script showing learning over time
5. Update documentation and examples

---

## Output Format Example

### Enhanced Priority Classification
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

### User Override Record
```json
{
  "message_id": "msg_12345",
  "sender": "boss@company.com",
  "original_priority": "Medium",
  "original_confidence": 0.72,
  "user_priority": "High",
  "correction_reason": "Wrong sender importance",
  "correction_type": "sender_importance",
  "timestamp": "2025-10-13T10:30:00Z",
  "applied_to_model": true
}
```

### Accuracy Report
```json
{
  "accuracy_percentage": 87.5,
  "total_classified": 500,
  "user_corrections": 62,
  "period_days": 30,
  "target_met": true,
  "trend": "improving",
  "recommendations": [
    "Accuracy above 85% target",
    "Sender importance learning working well",
    "Continue current learning rate"
  ]
}
```

---

## Questions & Decisions

**Q: How quickly should sender importance scores adapt?**
**A:** Small adjustments (±0.05) per correction to avoid overcorrection. Requires 10-20 corrections to significantly change a sender's importance.

**Q: Should we cap the number of corrections stored per sender?**
**A:** Keep last 100 corrections per sender. Archive older corrections for analytics but don't use for real-time learning.

**Q: What if a user never corrects priorities?**
**A:** System defaults to base classification from Story 1.3. Learning is optional enhancement, not required.

**Q: How to handle VIP senders with low-priority emails?**
**A:** VIP flag provides +1 priority adjustment, but obvious newsletters/FYI emails can still be Medium/Low if content clearly indicates it.

**Q: Should we show accuracy metrics to users?**
**A:** Yes, in settings panel. Shows users the system is learning and improving. Gamification element encourages corrections.

**Q: What about privacy concerns with storing sender data?**
**A:** All data stored locally in SQLite. No cloud sync. User controls data deletion. Sender importance is email address + score only, no content.

---

## Related Documentation

- Story 1.3 (COMPLETE): EmailAnalysisEngine with basic priority classification
- Story 2.2: SQLite Database schema (for production implementation)
- PRD Section 5.2: AI Analysis Pipeline
- PRD Section 6.3: Privacy & Data Handling
- epic-stories.md: Full epic context

---

## Story Lifecycle

**Created:** 2025-10-13 (Moved from BACKLOG to TODO after Story 1.3 completion)
**Started:** [To be filled when implementation begins]
**Completed:** [To be filled when DoD met]

---

_This story enhances Story 1.3's priority classification with user learning, sender importance tracking, and continuous accuracy improvement. It transforms static classification into an adaptive system that gets smarter with use._
