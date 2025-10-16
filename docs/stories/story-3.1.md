# Story 3.1: Database Encryption Implementation

Status: Ready

## Story

As a privacy-conscious user,
I want my email analysis data encrypted at rest,
so that my sensitive information is protected even if someone gains access to the database file.

## Acceptance Criteria

1. **AC1: SQLCipher Implementation** - Implement SQLCipher for transparent database encryption with PRAGMA key command
2. **AC2: Windows DPAPI Key Management** - Use Windows DPAPI for secure key storage (no hardcoded keys, derived via PBKDF2)
3. **AC3: Database Migration Tool** - Provide migration tool for existing unencrypted databases with progress indication
4. **AC4: Performance Overhead** - Performance overhead <10% (target <5%) for all database operations
5. **AC5: API Transparency** - Encryption transparent to existing code (no API changes required to DatabaseManager)
6. **AC6: Settings UI Indicator** - Add encryption status indicator to settings UI showing enabled/disabled state
7. **AC7: Privacy Policy Documentation** - Document encryption implementation in privacy policy with technical details
8. **AC8: User Choice** - Support user choice: encrypted (default) or unencrypted (with prominent warning)

## Tasks / Subtasks

- [ ] Task 1: Install and Configure SQLCipher (AC: 1)
  - [ ] 1.1: Add pysqlcipher3 to requirements.txt
  - [ ] 1.2: Verify SQLCipher installation works on Windows 10/11
  - [ ] 1.3: Test fallback to standard sqlite3 if SQLCipher unavailable

- [ ] Task 2: Implement DPAPI Key Management (AC: 2)
  - [ ] 2.1: Create KeyManager class using Windows DPAPI (win32crypt)
  - [ ] 2.2: Implement key derivation: DPAPI → PBKDF2 → SQLCipher key (64 bytes)
  - [ ] 2.3: Store derived key securely in Windows credential store
  - [ ] 2.4: Handle key generation on first run
  - [ ] 2.5: Add unit tests for key derivation and storage

- [ ] Task 3: Modify DatabaseManager for Encryption (AC: 1, 5)
  - [ ] 3.1: Update DatabaseManager.__init__ to check encryption_key parameter
  - [ ] 3.2: Execute PRAGMA key command after SQLCipher connection
  - [ ] 3.3: Add encryption_enabled property to DatabaseManager
  - [ ] 3.4: Ensure existing code paths remain unchanged (backwards compatibility)
  - [ ] 3.5: Add fallback to unencrypted mode if key unavailable

- [ ] Task 4: Database Migration Tool (AC: 3)
  - [ ] 4.1: Create migrate_database() function to convert unencrypted → encrypted
  - [ ] 4.2: Implement progress tracking for migration (row counts, percentage)
  - [ ] 4.3: Create backup of original database before migration
  - [ ] 4.4: Test migration with large databases (>500MB, >10K emails)
  - [ ] 4.5: Add rollback capability if migration fails

- [ ] Task 5: Update Backup/Restore for Encryption (AC: 5)
  - [ ] 5.1: Modify backup_database() to handle encrypted databases
  - [ ] 5.2: Modify restore_database() to detect encrypted backups
  - [ ] 5.3: Add encryption status to backup metadata
  - [ ] 5.4: Test backup/restore with both encrypted and unencrypted DBs

- [ ] Task 6: Performance Testing (AC: 4)
  - [ ] 6.1: Benchmark baseline performance (unencrypted operations)
  - [ ] 6.2: Benchmark encrypted performance (same operations)
  - [ ] 6.3: Calculate overhead percentage for: INSERT, SELECT, UPDATE, DELETE
  - [ ] 6.4: Optimize if overhead >10% (target <5%)
  - [ ] 6.5: Document performance metrics in story completion notes

- [ ] Task 7: Settings UI Integration (AC: 6, 8)
  - [ ] 7.1: Add "Encryption Status" section to Privacy settings tab
  - [ ] 7.2: Display current encryption state (Enabled/Disabled)
  - [ ] 7.3: Add toggle to enable/disable encryption (with confirmation)
  - [ ] 7.4: Display warning dialog if user disables encryption
  - [ ] 7.5: Add "Migrate to Encrypted" button if currently unencrypted
  - [ ] 7.6: Show migration progress bar during conversion

- [ ] Task 8: Documentation Updates (AC: 7)
  - [ ] 8.1: Update privacy policy with encryption technical details
  - [ ] 8.2: Add SECURITY.md section on database encryption
  - [ ] 8.3: Update README.md with encryption feature
  - [ ] 8.4: Document key management approach (DPAPI + PBKDF2)
  - [ ] 8.5: Add FAQ entry: "Is my data encrypted?"

- [ ] Task 9: Unit and Integration Testing (AC: 1-8)
  - [ ] 9.1: Unit tests for KeyManager (key generation, derivation)
  - [ ] 9.2: Unit tests for encrypted DatabaseManager operations
  - [ ] 9.3: Unit tests for migration tool (success and failure cases)
  - [ ] 9.4: Integration tests with existing email analysis workflow
  - [ ] 9.5: Test encryption status UI components
  - [ ] 9.6: Test performance overhead is within limits

## Dev Notes

### Problem Statement
Database currently stores all emails in plain text despite "Absolute Privacy" marketing claim. The `encryption_key` parameter exists in DatabaseManager but SQLCipher is not implemented. This is a **critical security gap** that blocks MVP launch.

**Current Vulnerability:**
- Email analysis data stored unencrypted in `~/.local/share/MailMind/mailmind.db`
- Sensitive information: email subjects, bodies, analysis results, sender addresses
- Any user with file system access can read all historical email data

### Technical Architecture

**SQLCipher Integration:**
- Replace `sqlite3` with `pysqlcipher3` for transparent encryption
- Use 256-bit AES encryption via SQLCipher's PRAGMA key command
- Connection setup:
  ```python
  import pysqlcipher3.dbapi2 as sqlite3
  conn = sqlite3.connect(db_path)
  conn.execute(f"PRAGMA key = '{encryption_key}'")
  ```

**Key Management Flow:**
1. **First Run:** Generate random key → Protect with Windows DPAPI → Store in credential manager
2. **Subsequent Runs:** Retrieve DPAPI-protected key → Derive SQLCipher key via PBKDF2 → Open encrypted DB
3. **Key Derivation:** `DPAPI_key → PBKDF2(salt, 100000 iterations) → 64-byte SQLCipher key`

**Migration Strategy:**
- Detect unencrypted database on startup
- Offer one-time migration with progress UI
- Process: Create new encrypted DB → Copy all tables → Verify integrity → Replace original
- Backup original before migration (automatic rollback on failure)

### Source Tree Components

**Files to Modify:**
- `src/mailmind/core/database_manager.py` - Add SQLCipher support to DatabaseManager.__init__
- `src/mailmind/ui/settings_dialog.py` - Add encryption status and migration UI
- `requirements.txt` - Add pysqlcipher3 dependency

**Files to Create:**
- `src/mailmind/core/key_manager.py` - DPAPI key management and derivation
- `src/mailmind/core/db_migration.py` - Database migration utility
- `tests/unit/test_key_manager.py` - Key management tests
- `tests/unit/test_encryption.py` - Encryption integration tests
- `tests/integration/test_encrypted_workflow.py` - End-to-end encryption tests

### Testing Standards

**Test Coverage Requirements:**
- Unit tests for all key management functions (100% coverage)
- Unit tests for database encryption operations (>95% coverage)
- Integration tests for migration tool (all scenarios)
- Performance benchmarks (automated in CI)

**Test Scenarios:**
- Fresh install with encryption enabled (default)
- Migration from unencrypted to encrypted database
- Backup/restore with encrypted databases
- Performance overhead measurement
- Key unavailability handling (graceful degradation)
- Large database migration (>500MB)

**Performance Targets:**
- INSERT operations: <10% overhead (target <5%)
- SELECT operations: <10% overhead (target <5%)
- UPDATE operations: <10% overhead (target <5%)
- DELETE operations: <10% overhead (target <5%)
- Migration speed: >1000 emails/second

### Project Structure Notes

**Dependencies:**
- Story 2.2 (DatabaseManager exists) - ✅ Complete
- Windows DPAPI available via `win32crypt` module
- SQLCipher compatible with existing schema (no schema changes)

**No API Changes Required:**
- Existing code using DatabaseManager continues to work unchanged
- Encryption is transparent to all consumers of DatabaseManager
- Only internal implementation changes to connection setup

**Configuration:**
- Add `encryption_enabled` to user_preferences table (default: True)
- Store encryption status in database metadata
- Support environment variable override for testing: `MAILMIND_DISABLE_ENCRYPTION=1`

### References

- [Source: docs/epic-stories.md#Story 3.1] - Story description and 8 acceptance criteria
- [Source: docs/epic-3-security-proposal.md#Story 3.1] - Detailed problem statement and 7 ACs
- [Source: src/mailmind/core/database_manager.py] - Current DatabaseManager implementation
- [SQLCipher Documentation] - https://www.zetetic.net/sqlcipher/sqlcipher-api/
- [Windows DPAPI] - https://docs.microsoft.com/en-us/windows/win32/api/dpapi/

### Security Considerations

**Threats Mitigated:**
- ✅ Unauthorized file system access to database
- ✅ Database file theft/exfiltration
- ✅ Forensic analysis of unencrypted data

**Threats NOT Mitigated:**
- ❌ Memory dumps while application running (keys in memory)
- ❌ Email content still in Outlook's storage (outside our control)
- ❌ Keyloggers or screen capture malware
- ❌ Administrator-level access (can extract DPAPI keys)

**Security Transparency:**
- Document limitations clearly in privacy policy
- Explain encryption scope: "Database encrypted, Outlook storage not under our control"
- Provide security roadmap for future improvements

## Dev Agent Record

### Context Reference

- **Context File:** `docs/stories/story-context-3.1.xml`
- **Generated:** 2025-10-15
- **Contains:**
  - 8 acceptance criteria with detailed validation steps
  - 9 implementation tasks mapped to ACs
  - 4 documentation artifacts (epic-stories.md, epic-3-security-proposal.md, story-2.2.md, story-2.6.md)
  - 5 code artifacts (database_manager.py, settings_dialog.py, settings_manager.py, schema.py, backup_manager.py)
  - 7 Python dependencies with purposes and status
  - 10 architectural constraints (platform, performance, API, security, etc.)
  - 7 interface specifications with signatures and usage examples
  - 30 test ideas mapped to all 8 acceptance criteria
  - Complete integration guidance for SQLCipher, DPAPI, PBKDF2, migration tool, and settings UI

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes List

### File List
