# MailMind Privacy Policy

**Effective Date:** October 16, 2025
**Version:** 1.0.0
**Last Updated:** October 16, 2025

## Introduction

MailMind is committed to protecting your privacy through local-first design. This Privacy Policy explains what data we collect, how we protect it, and your rights regarding your information.

**Core Principle:** All email processing happens locally on your machine. Your email content never leaves your device.

---

## 1. Data Collection

### What Data We Process

MailMind processes the following data locally on your machine:

**Email Data (Processed Locally):**
- Email messages retrieved from Microsoft Outlook
- Email metadata (sender, recipient, subject, date, message IDs)
- Email content (body text, HTML)
- Email attachments (metadata only - filenames, sizes, types)
- Thread context and conversation history

**Analysis Results (Stored Locally):**
- AI-generated email summaries
- Priority classifications (High/Medium/Low)
- Suggested tags and categories
- Action item extractions
- Sentiment analysis
- Response drafts

**User Preferences (Stored Locally):**
- Application settings and configurations
- User corrections and feedback for AI learning
- Writing style profiles
- VIP sender lists
- Folder preferences

**Performance Metrics (Stored Locally):**
- AI inference performance (tokens/second, processing time)
- Hardware profiling data (CPU, RAM, GPU specs)
- Cache hit rates
- Application usage statistics

### What Data We Do NOT Collect

- ❌ Your email content is NEVER uploaded to any server
- ❌ No cloud backup of your emails or analysis
- ❌ No third-party analytics or tracking
- ❌ No personally identifiable information sent to MailMind servers
- ❌ No telemetry data transmission (unless explicitly opted in)

---

## 2. Data Encryption

### Encryption at Rest

**Database Encryption (Default):**
- All email analysis data stored in encrypted SQLite database
- **Encryption Standard:** 256-bit AES encryption via SQLCipher
- **Key Management:** Windows Data Protection API (DPAPI)
- **Key Derivation:** PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Platform:** Windows 10/11 (macOS/Linux support planned for v2.0)

**Key Protection:**
- Encryption keys stored in Windows Credential Manager
- Keys protected with Windows DPAPI (tied to user account + machine)
- Keys cannot be extracted to another machine
- Hardware-backed key protection where available

**Performance:**
- Encryption overhead: <5% (typically 2-3%)
- No impact on user experience

### Encryption in Transit

- **No Network Transfer:** Email data never leaves your machine
- **Local AI Processing:** All Ollama LLM inference happens localhost (127.0.0.1:11434)
- **No Cloud APIs:** Zero external API calls for email processing

---

## 3. Data Storage

### Storage Location

All MailMind data is stored locally on your machine:

**Windows:**
- **Database:** `%LOCALAPPDATA%\MailMind\data\mailmind.db` (encrypted)
- **Logs:** `%APPDATA%\MailMind\logs\`
- **Configuration:** `%APPDATA%\MailMind\config\`
- **Models:** `%USERPROFILE%\.ollama\models\` (Ollama storage)

**Data Retention:**
- Email analysis data: Retained indefinitely until you delete it
- Performance metrics: Retained for 90 days (configurable)
- Logs: Rotated after 10 files of 10MB each

### Data Backup

- **Local Backups Only:** Automatic backup before database migration
- **No Cloud Sync:** MailMind does not sync data to any cloud service
- **Manual Export:** You can export your data at any time (Settings → Data Management)

---

## 4. Third-Party Services

**MailMind does NOT use any third-party services for email processing.**

### Data Sharing

- ✅ **Zero data sharing:** Your email content is never shared with anyone
- ✅ **No partnerships:** We do not partner with data brokers or advertisers
- ✅ **No analytics:** No Google Analytics, Mixpanel, or similar services

### External Connections

**The ONLY external connection MailMind makes:**
- **Microsoft Outlook (Local):** Via pywin32 API to read emails from your local Outlook application
  - This is a local connection on your machine
  - No data sent to Microsoft servers beyond what Outlook normally sends

**Optional Crash Reports (Opt-In Only):**
- If you enable crash reporting, sanitized error logs may be sent to MailMind servers
- All email addresses, subjects, and bodies are automatically removed from crash reports
- Crash reporting is DISABLED by default
- You can enable/disable at: Settings → Privacy → Crash Reporting

### AI Model Provider

- **Ollama:** Local LLM inference engine (runs on localhost)
- **Models:** Downloaded once from Ollama registry, stored locally
- **No cloud inference:** All AI processing happens on your hardware
- **Model verification:** SHA256 checksums verified against known-good hashes

---

## 5. Known Limitations & Security Boundaries

**MailMind provides strong security, but we are transparent about what we CAN and CANNOT protect:**

### What IS Protected ✅

- ✅ **Database File:** Encrypted with 256-bit AES (SQLCipher)
- ✅ **Analysis Results:** Stored encrypted, inaccessible without your Windows account
- ✅ **File System Access:** Encrypted database is unreadable by unauthorized users
- ✅ **Data Theft:** Stolen database files cannot be decrypted on another machine

### What IS NOT Protected ❌

- ❌ **Outlook Storage:** Email source data remains in Microsoft Outlook's storage
  - Outlook may or may not encrypt its data store (depends on Outlook version)
  - Outlook storage is outside MailMind's control
  - Recommendation: Use full-disk encryption (Windows BitLocker)

- ❌ **Application Memory:** While MailMind is running:
  - Decrypted email content exists in application memory
  - Advanced attackers could potentially dump memory
  - Mitigation: Keep your operating system and security software up-to-date

- ❌ **Screen Capture:** Email content displayed on screen is visible
  - Malware with screen recording capabilities could capture displayed emails
  - Physical security: Lock your computer when away

- ❌ **Administrator Access:** System administrators can:
  - Extract DPAPI keys from Windows Credential Manager
  - Access decrypted data while application is running
  - Mitigation: Only use MailMind on machines you control

- ❌ **Malware:** MailMind cannot protect against:
  - Keyloggers recording your password
  - Trojans with system-level access
  - Rootkits compromising the operating system
  - Mitigation: Use reputable antivirus software

### Recommendations for Comprehensive Protection

1. **Enable Full-Disk Encryption:** Use Windows BitLocker to encrypt your entire drive
2. **Use Strong Windows Password:** DPAPI security is tied to your user account password
3. **Keep Windows Updated:** Install security patches promptly
4. **Use Antivirus Software:** Protect against malware and keyloggers
5. **Physical Security:** Lock your computer when unattended
6. **Network Security:** Keep your network secure (though MailMind works offline)

---

## 6. Your Rights

You have complete control over your data in MailMind:

### Data Access

- **Full Access:** You can access all your data at any time
- **Export:** Settings → Data Management → Export All Data
- **Location:** All data stored in documented locations (see Section 3)

### Data Deletion

- **Clear Analysis Cache:** Settings → Privacy → Clear Analysis Data
- **Delete Specific Emails:** Remove individual email analysis results
- **Complete Removal:** Uninstall MailMind to delete all application data
- **Secure Deletion:** Database file is securely overwritten during uninstall

### Data Portability

- **Standard Formats:** Analysis data exportable as JSON
- **Database Access:** Direct SQLite database access if needed
- **No Lock-In:** Your data is yours, in open formats

### Encryption Control

- **Enable Encryption:** Settings → Privacy → Enable Database Encryption
- **Disable Encryption:** Settings → Privacy → Disable Encryption (with strong warning)
- **Migration Tools:** Convert between encrypted and unencrypted databases

---

## 7. Policy Updates

### How We Notify You

- **In-App Notification:** Major privacy policy changes displayed on startup
- **Version Changes:** Policy version number incremented
- **Effective Date:** Updated effective date shown at top of policy
- **Review Period:** 30 days notice before significant changes take effect

### Your Options

- **Accept Changes:** Continue using MailMind with new policy
- **Reject Changes:** You may discontinue use; your local data remains yours
- **Export Data:** Export your data before discontinuing use

### Policy History

- **Version 1.0.0 (October 16, 2025):** Initial privacy policy
  - Established local-first privacy principles
  - Documented encryption architecture (Story 3.1)
  - Defined security boundaries and limitations

---

## 8. Contact & Support

### Questions About This Policy

If you have questions about this Privacy Policy:

- **Email:** privacy@mailmind.ai
- **Documentation:** See [SECURITY.md](../SECURITY.md) for technical details
- **FAQ:** See [security-faq.md](security-faq.md) for common questions

### Security Issues

If you discover a security vulnerability:

- **DO NOT** open a public GitHub issue
- **Email:** security@mailmind.ai
- See [SECURITY.md](../SECURITY.md) for responsible disclosure process

### Compliance Inquiries

For compliance or legal inquiries:

- **Email:** legal@mailmind.ai

---

## 9. Legal Framework

### Jurisdiction

MailMind is operated by MailMind, Inc. (United States).

### Compliance

**GDPR Compliance (EU Users):**
- ✅ Data processed locally (no transfer to third parties)
- ✅ Right to access, export, and delete data
- ✅ No consent needed for local processing
- ✅ Data minimization (only process what's necessary)

**CCPA Compliance (California Users):**
- ✅ No sale of personal data (we never collect it)
- ✅ Right to know what data is collected (documented in Section 1)
- ✅ Right to delete data (Section 6)

**HIPAA Considerations:**
- ⚠️ MailMind provides encryption at rest and local processing
- ⚠️ However, users in regulated industries should conduct their own compliance assessment
- ⚠️ MailMind is not a HIPAA-certified Business Associate

---

## 10. Children's Privacy

MailMind is not intended for users under 13 years of age. We do not knowingly collect data from children.

---

## Summary

**MailMind's Privacy Promise:**

1. 🔒 **Local-First:** All AI processing happens on your machine
2. 🔐 **Encrypted by Default:** 256-bit AES database encryption
3. 🛡️ **No Cloud Upload:** Email content never leaves your device
4. 🔑 **You Control Your Data:** Full access, export, and deletion rights
5. 📍 **Transparent Limitations:** Clear about what we CAN and CANNOT protect

**Questions?** Read our [Security FAQ](security-faq.md) for more details.

---

**Last Updated:** October 16, 2025
**Version:** 1.0.0
**Effective Date:** October 16, 2025
