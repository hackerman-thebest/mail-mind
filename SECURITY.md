# Security

**MailMind Security Architecture and Practices**

## Overview

MailMind is designed with privacy and security as core principles. All email processing happens locally on your machine, and sensitive data is protected with industry-standard encryption.

**Security Principles:**
- 🔒 **Local-First:** All AI processing happens on your machine
- 🔐 **Encryption by Default:** Database encrypted with 256-bit AES
- 🛡️ **No Cloud Upload:** Email content never leaves your device
- 🔑 **Secure Key Management:** Windows DPAPI + PBKDF2 key derivation
- 🔍 **Transparent Implementation:** Open source code for security audit

---

## Database Encryption

**Story 3.1: Database Encryption Implementation** ✅ COMPLETE

MailMind encrypts your email analysis database at rest using SQLCipher with 256-bit AES encryption.

### Encryption Technology Stack

**SQLCipher:**
- Industry-standard database encryption library
- 256-bit AES encryption in CBC mode
- Page-level encryption (encrypts entire database file)
- FIPS 140-2 compliant cryptography
- Performance overhead <5% (typically 2-3%)

**Key Management (Windows DPAPI):**
- Windows Data Protection API (CryptProtectData/CryptUnprotectData)
- Keys tied to user account + machine (cannot be extracted to another machine)
- Automatic hardware-backed encryption where available
- No hardcoded keys - all keys generated randomly

**Key Derivation (PBKDF2):**
- PBKDF2-HMAC-SHA256 with 100,000 iterations
- 64-byte derived keys for SQLCipher
- Random 16-byte salt stored in user_preferences table
- Mitigates brute-force and rainbow table attacks

### Architecture

```
User Machine
├── Windows Credential Manager (DPAPI-protected key)
├── MailMind Database (mailmind.db)
│   ├── Encrypted with SQLCipher (256-bit AES)
│   └── user_preferences.encryption_salt (for PBKDF2)
└── Application
    ├── KeyManager (DPAPI + PBKDF2)
    └── DatabaseManager (SQLCipher integration)
```

### Key Management Flow

**First Run (Key Generation):**
1. Generate random 32-byte key using `os.urandom()`
2. Protect key with Windows DPAPI (CryptProtectData)
3. Store DPAPI-protected key in Windows Credential Manager
4. Generate random 16-byte salt
5. Store salt in database user_preferences table
6. Derive 64-byte SQLCipher key: `PBKDF2(DPAPI_key, salt, 100K iterations)`
7. Open database with `PRAGMA key = '...'`

**Subsequent Runs (Key Retrieval):**
1. Retrieve DPAPI-protected key from Windows Credential Manager
2. Unprotect key with Windows DPAPI (CryptUnprotectData)
3. Retrieve salt from database user_preferences table
4. Derive 64-byte SQLCipher key: `PBKDF2(DPAPI_key, salt, 100K iterations)`
5. Open database with `PRAGMA key = '...'`

### Security Properties

**Threats Mitigated:**
- ✅ **File System Access:** Encrypted database file is unreadable without key
- ✅ **Database File Theft:** Encrypted data cannot be accessed on another machine
- ✅ **Forensic Analysis:** Encrypted data resists forensic recovery tools
- ✅ **Backup Exposure:** Database backups are encrypted (same key)

**Threats NOT Mitigated:**
- ❌ **Memory Dumps:** Keys and decrypted data in application memory
- ❌ **Outlook Storage:** Email source data in Outlook (outside our control)
- ❌ **Screen Capture:** Displayed email content visible on screen
- ❌ **Administrator Access:** System administrators can extract DPAPI keys
- ❌ **Malware:** Keyloggers, screen recorders, memory scrapers

**Security Boundaries:**
- Encryption protects **database file at rest**
- Encryption does NOT protect **application runtime** or **Outlook storage**
- Users should use full-disk encryption (BitLocker) for comprehensive protection

### Platform Support

**Windows 10/11:**
- ✅ Full encryption support via pywin32
- ✅ DPAPI available by default
- ✅ Hardware-backed key protection where available

**macOS/Linux:**
- ⚠️ Encryption unavailable (DPAPI Windows-only)
- ℹ️ Graceful degradation to unencrypted database
- ℹ️ Warning shown in Settings UI

**Future:** Keychain (macOS) and libsecret (Linux) support planned for v2.0

### User Control

**Settings → Privacy → Database Encryption:**
- ✅ Encryption status indicator (Enabled/Disabled)
- ✅ Enable encryption button (with migration)
- ✅ Disable encryption button (with strong warning)
- ✅ Progress tracking during migration
- ✅ Automatic backup before migration

**Default Behavior:**
- New installations: **Encryption ENABLED by default**
- Existing databases: Migrate via Settings UI
- Environment override: `MAILMIND_DISABLE_ENCRYPTION=1` (testing only)

### Performance

**Benchmark Results:**
- INSERT operations: 2-4% overhead (EXCELLENT)
- SELECT operations: 1-3% overhead (EXCELLENT)
- UPDATE operations: 2-4% overhead (EXCELLENT)
- DELETE operations: 1-2% overhead (EXCELLENT)
- **Average overhead: 2-3%** (well under 10% target)

Performance details: `docs/performance-testing-results.md`

### Migration

**Unencrypted → Encrypted:**
1. User clicks "Enable Encryption" in Settings
2. Automatic backup created before migration
3. New encrypted database created with generated key
4. All data copied table-by-table with progress tracking
5. Data integrity verification (row counts, checksums)
6. Original database replaced with encrypted version
7. Rollback to backup on failure

**Encrypted → Unencrypted:**
1. User clicks "Disable Encryption" (⚠️ double confirmation warning)
2. Automatic backup created before migration
3. New unencrypted database created
4. All data copied with decryption
5. Data integrity verification
6. Original database replaced
7. Rollback to backup on failure

**Migration Safety:**
- Automatic backup before conversion
- Automatic rollback on failure
- Data integrity verification
- Progress tracking for large databases (>500MB supported)

---

## Local AI Processing

**No Cloud Upload:**
- All AI inference happens locally via Ollama
- LLM models run on your hardware (CPU or GPU)
- Email content never sent to external servers
- No API keys or cloud credentials required

**Models:**
- Llama 3.1 8B (recommended)
- Mistral 7B (fallback)
- Models stored locally in `~/.ollama/models/`

---

## Privacy Policy

**Data Collection:**
- ✅ **Email content:** Processed locally, never uploaded
- ✅ **Analysis results:** Stored in encrypted local database
- ✅ **User corrections:** Stored locally for learning
- ✅ **Writing style:** Analyzed locally from sent emails

**Telemetry (Optional, Disabled by Default):**
- Anonymous usage statistics (no email content)
- Crash reports (sanitized, no PII)
- User can disable in Settings → Privacy

**Third-Party Services:**
- None. MailMind does not connect to any external services.
- Ollama runs locally (localhost:11434)

---

## Security Best Practices

**For Users:**
1. **Enable database encryption** (Settings → Privacy → Database Encryption)
2. **Use full-disk encryption** (Windows BitLocker) for comprehensive protection
3. **Keep Windows updated** (for latest DPAPI security patches)
4. **Use strong Windows password** (DPAPI security tied to user account)
5. **Enable automatic backups** (Settings → Advanced → Auto Backup)

**For Developers:**
1. **Never hardcode keys** - Use KeyManager for all encryption keys
2. **Always sanitize logs** - Use `export_logs_to_clipboard()` for issue reporting
3. **Validate database integrity** - Check encryption status on startup
4. **Handle key unavailability** - Graceful degradation if DPAPI fails
5. **Test migration paths** - Both encrypted→unencrypted and unencrypted→encrypted

---

## Vulnerability Reporting

If you discover a security vulnerability in MailMind:

1. **DO NOT** open a public GitHub issue
2. **Email:** security@mailmind.ai (with PGP if possible)
3. **Include:**
   - Description of vulnerability
   - Steps to reproduce
   - Impact assessment
   - Suggested fix (if available)

**Response Timeline:**
- Acknowledgment within 24 hours
- Initial assessment within 3 business days
- Security patch within 7 days for critical issues

**Disclosure Policy:**
- Responsible disclosure with 90-day embargo
- Credit given to reporter (unless anonymity requested)
- Security advisories published after patch release

---

## Encryption Implementation Details

**Files:**
- `src/mailmind/core/key_manager.py` - DPAPI + PBKDF2 key management
- `src/mailmind/core/db_migration.py` - Database migration tool
- `src/mailmind/database/database_manager.py` - SQLCipher integration
- `src/mailmind/database/backup_manager.py` - Encryption-aware backups
- `src/mailmind/ui/dialogs/settings_dialog.py` - Encryption UI

**Tests:**
- `tests/unit/test_key_manager.py` - Key management unit tests
- `tests/unit/test_encryption.py` - Encryption integration tests
- `tests/integration/test_encrypted_workflow.py` - End-to-end encryption tests
- `tests/performance/test_encryption_performance.py` - Performance benchmarks

**Documentation:**
- `SECURITY.md` - This file (security architecture)
- `docs/performance-testing-results.md` - Encryption performance metrics
- `docs/stories/story-3.1.md` - Encryption implementation story
- `docs/stories/story-context-3.1.xml` - Detailed implementation context

---

## Security Roadmap

**Completed (v1.0):**
- ✅ Database encryption (SQLCipher 256-bit AES)
- ✅ Windows DPAPI key management
- ✅ PBKDF2 key derivation (100K iterations)
- ✅ Encryption-aware backups
- ✅ Migration tools (encrypted ↔ unencrypted)
- ✅ Settings UI for encryption management

**Planned (v2.0):**
- 🔄 macOS Keychain support
- 🔄 Linux libsecret support
- 🔄 Key rotation capability
- 🔄 Hardware security module (HSM) support
- 🔄 Database rekey command

**Future Considerations:**
- 🔮 Per-email encryption (in addition to database encryption)
- 🔮 Password-based key derivation (optional user password)
- 🔮 Multi-user support with separate keys
- 🔮 Cloud backup with end-to-end encryption

---

## Compliance

**Encryption Standards:**
- AES-256-CBC (FIPS 140-2 validated)
- PBKDF2-HMAC-SHA256 with 100K iterations
- Cryptographically secure random number generation (os.urandom)

**Privacy Regulations:**
- GDPR compliant (local processing, no data transfer)
- CCPA compliant (no personal data sale)
- HIPAA considerations (encryption at rest, local processing)

**Note:** While MailMind implements strong encryption, users in regulated industries should conduct their own compliance assessment.

---

## Additional Resources

- [SQLCipher Documentation](https://www.zetetic.net/sqlcipher/)
- [Windows DPAPI Documentation](https://docs.microsoft.com/en-us/windows/win32/api/dpapi/)
- [PBKDF2 RFC 2898](https://tools.ietf.org/html/rfc2898)
- [Ollama Security](https://ollama.ai/security)

---

**Last Updated:** 2025-10-15
**Story:** 3.1 - Database Encryption Implementation
**Version:** 1.0.0
