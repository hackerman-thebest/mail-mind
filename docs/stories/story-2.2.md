# Story 2.2: SQLite Database & Caching Layer

**Status:** Draft
**Epic:** 2 - Desktop Application & User Experience
**Story Points:** 5
**Priority:** P0 (Critical Path)
**Created:** 2025-10-14

---

## Story

As a system,
I want a robust local SQLite database to persist email analysis, user preferences, and performance metrics,
so that the application maintains state across restarts, delivers fast queries, and preserves user data securely.

## Context

Story 2.2 implements the foundational data persistence layer for MailMind, consolidating all SQLite database operations into a unified, production-ready system. While Stories 1.3 and 1.6 created initial database schemas for their specific needs, this story establishes the complete database architecture with encryption support, migration capabilities, backup/restore functionality, and comprehensive data management.

**Why This Story Is Critical:**
- Centralizes all database operations to prevent schema conflicts
- Adds production features (encryption, migrations, backups) missing from MVP prototypes
- Enables data portability and user control (backup/restore, complete deletion)
- Provides performance monitoring and storage alerts for proactive management
- Establishes patterns for future schema evolution

**Integration with Completed Stories:**
- **Story 1.3 (EmailAnalysisEngine)**: Uses `email_analysis` and `performance_metrics` tables - this story formalizes and extends those schemas
- **Story 1.6 (CacheManager)**: Currently has inline SQLite code - this story provides centralized database access patterns
- **Story 2.1 (OutlookConnector)**: Will integrate via `email_analysis` table for storing Outlook email metadata

---

## Acceptance Criteria

### AC1: Complete Database Schema Definition
- ✅ Define production-ready schema for 4 core tables:
  - `email_analysis`: Email AI analysis results with full metadata
  - `performance_metrics`: System performance tracking and trends
  - `user_preferences`: Application settings and user choices
  - `user_corrections`: User feedback for ML improvement
- ✅ Add proper indexes for common query patterns (message_id, received_date, priority)
- ✅ Add foreign key constraints where appropriate
- ✅ Include schema version tracking for migrations
- ✅ Add CHECK constraints for data validation

### AC2: Optional Database Encryption
- ✅ Support optional SQLite database encryption using SQLCipher
- ✅ Prompt user during first-run to enable/disable encryption
- ✅ Store encryption key securely (Windows DPAPI)
- ✅ Display encryption status in Settings UI
- ✅ Performance impact: <5% overhead for encrypted database operations
- ✅ Clear warning if encryption cannot be enabled (missing dependencies)

### AC3: Fast Query Performance
- ✅ All database operations complete in <100ms (target: <50ms for common queries)
- ✅ Implement connection pooling for concurrent access
- ✅ Add query logging for performance monitoring (debug mode)
- ✅ Use prepared statements to prevent SQL injection
- ✅ Optimize indexes based on query patterns (EXPLAIN QUERY PLAN)

### AC4: Automatic Database Creation & Initialization
- ✅ Detect if database exists on startup
- ✅ Create database with complete schema if not found
- ✅ Initialize with default user preferences
- ✅ Log database creation with timestamp
- ✅ Handle concurrent initialization gracefully (file locking)

### AC5: Database Migration Support
- ✅ Track current schema version in `schema_version` table
- ✅ Detect schema version mismatch on startup
- ✅ Apply migrations sequentially (version N → N+1 → N+2)
- ✅ Rollback migrations on failure with error logging
- ✅ Backup database before applying migrations
- ✅ Support forward-only migrations (no downgrades in MVP)

### AC6: Backup and Restore Functionality
- ✅ Manual backup: Export database to timestamped file
- ✅ Automatic backups: Daily backup to `backups/` folder (keep last 7 days)
- ✅ Restore from backup: Select and restore from backup file
- ✅ Verify backup integrity before restore (checksum validation)
- ✅ Backup includes schema version for compatibility check
- ✅ Display backup status: last backup date, backup size

### AC7: Complete Data Deletion on Uninstall
- ✅ Provide "Delete All Data" option in Settings
- ✅ Confirmation dialog with explicit warning
- ✅ Delete database file completely (not just clear tables)
- ✅ Delete all backup files
- ✅ Delete encryption key from secure storage
- ✅ Log data deletion event (before deletion, for troubleshooting)

### AC8: Database Size Monitoring
- ✅ Track database file size in real-time
- ✅ Display size in Settings: "Database: 245 MB / 1 GB"
- ✅ Alert user if database exceeds 1 GB (orange warning)
- ✅ Provide "Optimize Database" button (VACUUM command)
- ✅ Show space saved after optimization
- ✅ Log size metrics to performance_metrics table

### AC9: Centralized Database Manager Class
- ✅ Create `DatabaseManager` class as single entry point for all DB operations
- ✅ Provide CRUD methods for each table (create, read, update, delete)
- ✅ Handle connection lifecycle (open, close, context manager)
- ✅ Thread-safe operations (connection per thread or pooling)
- ✅ Comprehensive error handling with specific exceptions
- ✅ Integration interface for CacheManager, EmailAnalysisEngine, OutlookConnector

---

## Tasks / Subtasks

### Task 1: Complete Database Schema Implementation (AC1)
- [ ] Create `src/mailmind/database/schema.py` with complete SQL schema definitions
- [ ] Define `email_analysis` table with all fields from epic-stories.md
- [ ] Define `performance_metrics` table for hardware/model tracking
- [ ] Define `user_preferences` table for settings persistence
- [ ] Define `user_corrections` table for user feedback
- [ ] Add `schema_version` table for migration tracking
- [ ] Create indexes for common queries (message_id, received_date, priority)
- [ ] Add CHECK constraints for enum fields (priority, sentiment)
- [ ] Write unit tests for schema creation

### Task 2: DatabaseManager Core Implementation (AC3, AC4, AC9)
- [ ] Create `src/mailmind/database/database_manager.py`
- [ ] Implement `DatabaseManager` class with connection management
- [ ] Implement automatic database creation on first run
- [ ] Add connection pooling for concurrent access
- [ ] Implement CRUD methods for `email_analysis` table
- [ ] Implement CRUD methods for `performance_metrics` table
- [ ] Implement CRUD methods for `user_preferences` table
- [ ] Implement CRUD methods for `user_corrections` table
- [ ] Add context manager support (`with DatabaseManager() as db:`)
- [ ] Add thread-safety via connection per thread or pooling
- [ ] Implement query performance logging (debug mode)
- [ ] Write unit tests for DatabaseManager operations

### Task 3: Optional Database Encryption (AC2)
- [ ] Add optional SQLCipher dependency (pysqlcipher3)
- [ ] Implement encryption toggle in first-run setup
- [ ] Store encryption key using Windows DPAPI (cryptography library)
- [ ] Detect encryption status on database open
- [ ] Handle encrypted database connections
- [ ] Add encryption status to Settings UI
- [ ] Measure and log encryption performance impact
- [ ] Write unit tests for encrypted database operations
- [ ] Document encryption setup in README

### Task 4: Database Migration System (AC5)
- [ ] Create `src/mailmind/database/migrations/` folder
- [ ] Implement migration framework (`Migration` base class)
- [ ] Create initial migration (v1 → v2) as example
- [ ] Detect schema version mismatch on startup
- [ ] Apply migrations sequentially with logging
- [ ] Backup database before migration
- [ ] Rollback on migration failure
- [ ] Update schema_version after successful migration
- [ ] Write unit tests for migration application
- [ ] Document migration creation process

### Task 5: Backup and Restore (AC6)
- [ ] Implement manual backup: `db.backup(backup_path)`
- [ ] Implement automatic daily backups (background task)
- [ ] Store backups in `{project-root}/backups/` folder
- [ ] Add timestamp to backup filenames: `mailmind-db-2025-10-14.bak`
- [ ] Keep last 7 daily backups, delete older
- [ ] Implement restore: `db.restore(backup_path)`
- [ ] Add checksum validation for backup integrity
- [ ] Display backup status in Settings UI
- [ ] Write unit tests for backup/restore operations
- [ ] Handle backup failures gracefully (disk full, permissions)

### Task 6: Data Deletion and Privacy (AC7)
- [ ] Add "Delete All Data" option in Settings → Privacy
- [ ] Implement confirmation dialog with explicit warning
- [ ] Delete database file completely
- [ ] Delete all backup files in backups/ folder
- [ ] Delete encryption key from Windows DPAPI
- [ ] Log data deletion event before deletion
- [ ] Clear application state after deletion
- [ ] Write unit tests for data deletion
- [ ] Document data deletion in Privacy Policy

### Task 7: Database Size Monitoring (AC8)
- [ ] Implement `db.get_size_mb()` method
- [ ] Display size in Settings UI: "Database: 245 MB / 1 GB"
- [ ] Check size on startup and periodically (every 10 minutes)
- [ ] Show orange warning if size > 1 GB
- [ ] Implement "Optimize Database" button (VACUUM)
- [ ] Show space saved after optimization
- [ ] Log size metrics to performance_metrics table
- [ ] Write unit tests for size monitoring

### Task 8: Integration with Existing Stories (AC9)
- [ ] Refactor Story 1.3 (EmailAnalysisEngine) to use DatabaseManager
- [ ] Refactor Story 1.6 (CacheManager) to use DatabaseManager
- [ ] Update Story 2.1 (OutlookConnector) integration for email metadata storage
- [ ] Create integration examples in `examples/database_integration_demo.py`
- [ ] Write integration tests with EmailAnalysisEngine
- [ ] Write integration tests with CacheManager
- [ ] Verify backward compatibility with existing data

### Task 9: Testing and Documentation
- [ ] Write comprehensive unit tests (target: >85% coverage)
- [ ] Write integration tests with concurrent access
- [ ] Write performance tests (query benchmarks)
- [ ] Create demo script: `examples/database_demo.py`
- [ ] Write database administration guide in docs/
- [ ] Document backup/restore procedures
- [ ] Document migration creation process
- [ ] Update README with database setup instructions
- [ ] Update CHANGELOG with Story 2.2 completion

---

## Dev Notes

### Database Schema

**Complete Production Schema:**

```sql
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Email analysis results (extends Story 1.3 schema)
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
    suggested_folder TEXT,
    confidence_score REAL CHECK(confidence_score >= 0 AND confidence_score <= 1.0),
    sentiment TEXT CHECK(sentiment IN ('positive', 'neutral', 'negative', 'urgent')),

    -- Performance tracking
    processing_time_ms INTEGER,
    model_version TEXT NOT NULL,
    hardware_profile TEXT,

    -- Metadata
    processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_feedback TEXT,  -- For future learning

    -- Indexes
    INDEX idx_message_id (message_id),
    INDEX idx_priority (priority),
    INDEX idx_received_date (received_date),
    INDEX idx_processed_date (processed_date)
);

-- Performance metrics (extends Story 1.6 schema)
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,  -- 'email_analysis', 'batch_processing', 'outlook_fetch', etc.
    hardware_config TEXT NOT NULL,
    model_version TEXT,
    tokens_per_second REAL,
    memory_usage_mb INTEGER,
    processing_time_ms INTEGER,
    database_size_mb INTEGER,  -- For size monitoring
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_operation (operation),
    INDEX idx_timestamp (timestamp)
);

-- User preferences for all settings
CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    default_value TEXT,
    value_type TEXT CHECK(value_type IN ('string', 'int', 'float', 'bool', 'json')),
    category TEXT,  -- 'general', 'ai_model', 'performance', 'privacy', 'advanced'
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_category (category)
);

-- User corrections for learning system (Story 1.4 integration)
CREATE TABLE IF NOT EXISTS user_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    correction_type TEXT NOT NULL,  -- 'priority', 'folder', 'sentiment', etc.
    original_suggestion TEXT,
    user_choice TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES email_analysis(message_id),
    INDEX idx_message_id (message_id),
    INDEX idx_correction_type (correction_type),
    INDEX idx_timestamp (timestamp)
);
```

### Project Structure Notes

**New Files to Create:**
```
src/mailmind/database/
├── __init__.py
├── database_manager.py          # Main DatabaseManager class (600+ lines)
├── schema.py                     # Complete SQL schema definitions (200 lines)
├── migrations/                   # Migration system
│   ├── __init__.py
│   ├── migration_base.py        # Base Migration class (100 lines)
│   └── v001_initial_schema.py   # Example migration (50 lines)
├── backup_manager.py             # Backup/restore functionality (300 lines)
└── encryption.py                 # Optional encryption support (150 lines)

tests/unit/
├── test_database_manager.py     # DatabaseManager unit tests (500+ lines)
├── test_schema.py                # Schema validation tests (200 lines)
├── test_migrations.py            # Migration tests (300 lines)
└── test_backup_manager.py        # Backup/restore tests (250 lines)

examples/
└── database_demo.py              # Database operations demo (400 lines)
```

**Dependencies to Add:**
```
pysqlcipher3>=1.1.0  # Optional: for database encryption
cryptography>=41.0.0 # For Windows DPAPI key storage
```

### Architecture Patterns

**Design Pattern: Repository Pattern**
- `DatabaseManager` provides unified interface to all database operations
- Hides SQL implementation details from business logic
- Makes testing easier (can mock DatabaseManager)
- Enables future database backend changes (though SQLite is sufficient for MVP)

**Connection Management:**
```python
# Context manager pattern
with DatabaseManager() as db:
    db.insert_email_analysis(...)
    db.get_performance_metrics()
# Automatic connection cleanup

# Singleton pattern for shared connection
db = DatabaseManager.get_instance()
```

**Migration Pattern:**
```python
class Migration:
    version: int
    description: str

    def upgrade(self, conn: sqlite3.Connection):
        """Apply migration"""
        pass

    def downgrade(self, conn: sqlite3.Connection):
        """Rollback migration (future)"""
        pass
```

### Performance Considerations

**Query Optimization:**
- Use indexes for all WHERE, ORDER BY, and JOIN clauses
- Batch inserts for multiple records (use executemany)
- Use prepared statements for security and performance
- Avoid SELECT * (specify columns)
- Use EXPLAIN QUERY PLAN for slow queries

**Connection Pooling:**
```python
# One connection per thread approach
import threading

class DatabaseManager:
    _thread_local = threading.local()

    def _get_connection(self):
        if not hasattr(self._thread_local, 'conn'):
            self._thread_local.conn = sqlite3.connect(self.db_path)
        return self._thread_local.conn
```

**Encryption Performance:**
- Encrypted operations: ~5% slower than unencrypted
- Acceptable trade-off for sensitive data
- Test performance on minimum hardware (CPU-only)

### Integration Points

**Story 1.3 (EmailAnalysisEngine) Integration:**
```python
# Before (inline SQLite):
conn = sqlite3.connect('mailmind.db')
cursor = conn.execute("INSERT INTO email_analysis ...")

# After (DatabaseManager):
from mailmind.database import DatabaseManager

db = DatabaseManager.get_instance()
db.insert_email_analysis(
    message_id=message_id,
    analysis_result=analysis_json,
    processing_time_ms=elapsed_ms
)
```

**Story 1.6 (CacheManager) Integration:**
```python
# CacheManager now delegates to DatabaseManager
class CacheManager:
    def __init__(self):
        self.db = DatabaseManager.get_instance()

    def get_cached_analysis(self, message_id: str):
        return self.db.get_email_analysis(message_id)

    def cache_analysis(self, message_id: str, result: dict):
        self.db.insert_email_analysis(message_id, result)
```

**Story 2.1 (OutlookConnector) Integration:**
```python
# OutlookConnector stores email metadata
connector = OutlookConnector()
emails = connector.fetch_emails("Inbox", limit=50)

for email in emails:
    # Store in database for future reference
    db.insert_email_metadata(
        message_id=email.entry_id,
        subject=email.subject,
        sender=email.sender_email,
        received_date=email.received_time
    )
```

### Technical Constraints

**SQLite Limitations:**
1. **Single-writer**: Only one write at a time (readers can be concurrent)
   - Mitigation: Use WAL mode for better concurrency
2. **File size**: Performance degrades >1GB (hence size monitoring)
   - Mitigation: VACUUM periodically, alert user at 1GB
3. **No built-in encryption**: Requires SQLCipher extension
   - Mitigation: Make encryption optional, warn if unavailable
4. **Limited ALTER TABLE**: Cannot modify columns easily
   - Mitigation: Design schema carefully, use migrations for changes

**Windows-Specific Considerations:**
- Use Windows DPAPI for encryption key storage
- Handle file locking on network drives (not supported)
- Test on Windows 10 and Windows 11

### Testing Strategy

**Unit Tests (50+ tests):**
- DatabaseManager initialization and connection management
- CRUD operations for each table
- Query performance (< 100ms for common queries)
- Migration application and rollback
- Backup creation and restoration
- Encryption enable/disable
- Size monitoring and VACUUM

**Integration Tests (20+ tests):**
- Concurrent access from multiple threads
- Integration with EmailAnalysisEngine (Story 1.3)
- Integration with CacheManager (Story 1.6)
- Large dataset tests (10,000+ email analysis records)
- Database file corruption recovery

**Performance Tests:**
- Insert 1,000 email analysis records: <5 seconds
- Query 1,000 records with filters: <100ms
- VACUUM 1GB database: <30 seconds
- Backup 500MB database: <10 seconds
- Encrypted vs unencrypted performance comparison

**Manual Testing Checklist:**
- [ ] Create database on first run
- [ ] Enable encryption during setup
- [ ] Disable encryption and verify data accessible
- [ ] Create manual backup
- [ ] Restore from backup file
- [ ] Verify automatic daily backups
- [ ] Trigger 1GB size warning
- [ ] Optimize database with VACUUM
- [ ] Delete all data completely
- [ ] Apply migration to existing database
- [ ] Test on clean Windows 10 and Windows 11

---

## References

### Primary Sources
- **Epic Breakdown**: `docs/epic-stories.md` - Story 2.2 specification (lines 285-349)
- **Story 1.3**: `docs/stories/story-1.3.md` - Initial email_analysis and performance_metrics schemas
- **Story 1.6**: `docs/stories/story-1.6.md` - CacheManager implementation patterns
- **Story 2.1**: `docs/stories/story-2.1.md` - Outlook email metadata for database storage

### Technical Documentation
- **SQLite Documentation**: https://www.sqlite.org/docs.html
- **SQLCipher**: https://www.zetetic.net/sqlcipher/
- **Windows DPAPI**: https://learn.microsoft.com/en-us/windows/win32/api/dpapi/
- **Python sqlite3**: https://docs.python.org/3/library/sqlite3.html

### Integration Dependencies
- **Story 1.3 (EmailAnalysisEngine)**: Primary consumer of database for analysis caching
- **Story 1.6 (CacheManager)**: Will delegate all DB operations to DatabaseManager
- **Story 2.1 (OutlookConnector)**: Will store email metadata for reference
- **Story 2.4 (Settings System)**: Will use user_preferences table for settings persistence

---

## Dev Agent Record

### Context Reference

*To be filled by story-context workflow*

### Agent Model Used

*To be filled by DEV agent during implementation*

### Completion Notes List

*To be filled by DEV agent during implementation*

### File List

*To be filled by DEV agent during implementation*

---

## Change Log

### 2025-10-14 - SM Agent (create-story workflow)
- **Action**: Created Story 2.2 draft from epic-stories.md, Story 1.3, and Story 1.6
- **Details**:
  - Story extracted from Epic 2 specifications
  - 9 comprehensive acceptance criteria defined (AC1-AC9)
  - 9 implementation tasks with 40+ subtasks
  - Complete production database schema with 5 tables
  - Optional encryption support via SQLCipher
  - Migration system for future schema evolution
  - Backup/restore functionality with integrity checking
  - Database size monitoring with 1GB warning threshold
  - Integration plan with Stories 1.3, 1.6, and 2.1
  - Testing strategy defined (50+ unit tests, 20+ integration tests)
- **Status**: Draft (awaiting review via story-ready workflow)
- **Next**: User should review story and run `story-ready` to approve for development

---

*This story consolidates all database operations for MailMind, building on the foundations laid in Epic 1 and establishing production-ready data persistence for Epic 2.*
