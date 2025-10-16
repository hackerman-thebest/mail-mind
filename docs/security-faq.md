# MailMind Security FAQ

**Last Updated:** October 16, 2025
**Version:** 1.0.0

Common questions about MailMind's security, privacy, and data protection.

---

## General Security Questions

### Q1: Is my email data encrypted?

**Yes.** MailMind encrypts all email analysis data using industry-standard encryption:

- **Encryption Standard:** 256-bit AES encryption via SQLCipher
- **Key Management:** Windows Data Protection API (DPAPI)
- **Key Derivation:** PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Protection Level:** Database files are unreadable without your Windows account credentials

**What this means:** If someone steals your laptop or accesses your hard drive, they cannot read your MailMind database without also having access to your Windows account on that specific machine.

**Performance Impact:** Encryption overhead is typically 2-3% (less than 5%), so you won't notice any slowdown.

See [SECURITY.md](../SECURITY.md#database-encryption) for technical details.

---

### Q2: Where is my data stored?

**All data is stored locally on your machine.** MailMind never uploads your email content to the cloud.

**Storage Locations (Windows):**
- **Database:** `%LOCALAPPDATA%\MailMind\data\mailmind.db` (encrypted)
- **Logs:** `%APPDATA%\MailMind\logs\`
- **Configuration:** `%APPDATA%\MailMind\config\`
- **AI Models:** `%USERPROFILE%\.ollama\models\` (Ollama storage)

**Example paths:**
- Database: `C:\Users\YourName\AppData\Local\MailMind\data\mailmind.db`
- Logs: `C:\Users\YourName\AppData\Roaming\MailMind\logs\`

**Cloud Sync:** MailMind does NOT sync data to any cloud service (no Dropbox, OneDrive, iCloud, etc.).

**Backup:** Automatic backup is created before database migrations, stored locally. You can export your data at any time via Settings → Data Management.

See [Privacy Policy](privacy-policy.md#data-storage) for complete details.

---

### Q3: What about my Outlook emails? Are they encrypted by MailMind?

**No.** MailMind only encrypts the **analysis data** (summaries, classifications, tags) it creates, not the original emails stored by Microsoft Outlook.

**What MailMind encrypts:**
- ✅ AI-generated email summaries
- ✅ Priority classifications (High/Medium/Low)
- ✅ Suggested tags and categories
- ✅ Action item extractions
- ✅ Response drafts

**What MailMind does NOT encrypt:**
- ❌ Original emails stored by Microsoft Outlook
- ❌ Outlook's .pst or .ost files
- ❌ Email attachments in Outlook storage

**Why this matters:** If you need comprehensive encryption, use **full-disk encryption** (Windows BitLocker) to encrypt your entire drive, including Outlook's storage.

**Recommendation:** Enable BitLocker on your Windows drive for complete protection of both MailMind and Outlook data.

See [Privacy Policy - Known Limitations](privacy-policy.md#what-is-not-protected) for transparency about security boundaries.

---

### Q4: Can someone access my encrypted database file?

**It depends on the scenario:**

**Scenario 1: Database file stolen/copied to another machine**
- ✅ **Protected:** Database is encrypted with keys tied to your Windows account + specific machine
- ✅ **Result:** Attacker cannot decrypt the database on another computer

**Scenario 2: Attacker gains access to YOUR computer while logged in as YOU**
- ❌ **Not Protected:** If someone has access to your Windows account on your machine, they can access the database
- ❌ **Mitigation:** Use a strong Windows password, enable Windows Hello, lock your computer when away

**Scenario 3: Administrator-level access on your machine**
- ❌ **Not Protected:** System administrators can extract DPAPI keys from Windows Credential Manager
- ❌ **Mitigation:** Only use MailMind on machines you control (not shared/work computers with IT admin access)

**Scenario 4: Malware with system-level access**
- ❌ **Not Protected:** Malware running with administrator privileges could potentially access decrypted data
- ❌ **Mitigation:** Use reputable antivirus software, keep Windows updated

**Summary:** Database encryption protects against **physical theft** and **file system access**, but not against attackers who have compromised your Windows account or machine.

See [Privacy Policy - Security Boundaries](privacy-policy.md#known-limitations--security-boundaries) for complete threat model.

---

### Q5: Is AI processing truly local? Does MailMind send my emails to ChatGPT or other cloud services?

**100% local. Zero cloud APIs.**

**How it works:**
- **AI Engine:** MailMind uses Ollama, a local LLM inference engine
- **Connection:** Ollama runs on your machine at `localhost:127.0.0.1:11434`
- **Models:** AI models are downloaded once from Ollama registry, stored locally in `%USERPROFILE%\.ollama\models\`
- **Processing:** All AI inference happens on your hardware (CPU, RAM, optional GPU)

**No external connections for email processing:**
- ❌ No OpenAI API calls
- ❌ No ChatGPT
- ❌ No Google Gemini
- ❌ No Anthropic Claude API
- ❌ No cloud inference of any kind

**The ONLY external connection:**
- ✅ Microsoft Outlook (via local pywin32 API to read emails from your local Outlook application)
  - This is a local connection on your machine
  - No data sent to Microsoft servers beyond what Outlook normally sends

**Model Downloads:**
- Models are downloaded once during initial setup
- Downloaded from Ollama's public registry (similar to downloading software)
- SHA256 checksums are verified against known-good hashes to prevent tampering
- After download, no internet connection is needed for AI processing

**Verification:** You can disconnect your internet and MailMind will continue processing emails locally.

See [SECURITY.md - Model Verification](../SECURITY.md#model-checksum-verification) for supply chain attack prevention details.

---

### Q6: What are the security limitations I should know about?

**MailMind is transparent about what we CAN and CANNOT protect.**

### What IS Protected ✅

- ✅ **Database File:** Encrypted with 256-bit AES (SQLCipher)
- ✅ **Analysis Results:** Stored encrypted, inaccessible without your Windows account
- ✅ **File System Access:** Encrypted database is unreadable by unauthorized users
- ✅ **Data Theft:** Stolen database files cannot be decrypted on another machine
- ✅ **Prompt Injection Attacks:** Defense system blocks malicious prompts in email content
- ✅ **SQL Injection:** Whitelist validation prevents database manipulation
- ✅ **Model Tampering:** Checksum verification detects compromised AI models

### What IS NOT Protected ❌

- ❌ **Outlook Storage:** Email source data remains in Microsoft Outlook's storage (outside MailMind's control)
- ❌ **Application Memory:** While MailMind is running, decrypted email content exists in memory
- ❌ **Screen Capture:** Email content displayed on screen is visible to screen recording malware
- ❌ **Administrator Access:** System administrators can extract DPAPI keys from Windows Credential Manager
- ❌ **Malware:** MailMind cannot protect against keyloggers, trojans, rootkits with system-level access

### Recommendations for Comprehensive Protection

1. **Enable Full-Disk Encryption:** Use Windows BitLocker to encrypt your entire drive
2. **Use Strong Windows Password:** DPAPI security is tied to your user account password
3. **Keep Windows Updated:** Install security patches promptly
4. **Use Antivirus Software:** Protect against malware and keyloggers
5. **Physical Security:** Lock your computer when unattended (Windows Key + L)
6. **Network Security:** Keep your network secure (though MailMind works offline)

**Why this matters:** We believe transparency builds trust. Understanding security limitations helps you make informed decisions about when to use MailMind and what additional protections to enable.

See [Privacy Policy - Known Limitations](privacy-policy.md#known-limitations--security-boundaries) for complete details.

---

### Q7: How do I report a security vulnerability?

**We take security seriously.** If you discover a vulnerability, please follow responsible disclosure:

**Step 1: DO NOT open a public GitHub issue**
- Public disclosure puts all users at risk
- Contact us privately first

**Step 2: Email security@mailmind.ai**
- Include detailed description of the vulnerability
- Provide steps to reproduce (if applicable)
- Include your contact information for follow-up

**Step 3: Allow time for response**
- We will acknowledge your report within 48 hours
- We will provide a fix timeline within 7 days
- We will credit you in our security changelog (if desired)

**Step 4: Coordinated disclosure**
- We will notify you when a fix is ready
- Public disclosure after patch is released and users have time to update

**Bug Bounty:** We currently do not have a formal bug bounty program, but we appreciate security researchers and will acknowledge your contributions.

**Questions about the vulnerability reporting process?** See [SECURITY.md - Vulnerability Reporting](../SECURITY.md#vulnerability-reporting).

---

### Q8: What's the difference between "Local-First Privacy" and "Absolute Privacy"?

**Great question!** This is about honest, transparent communication.

### "Absolute Privacy" (Unrealistic) ❌

Claims like "Absolute Privacy" or "100% Secure" imply that:
- ❌ No one can ever access your data under any circumstances
- ❌ The system is completely invulnerable to all attacks
- ❌ There are no security limitations whatsoever

**Reality:** No system can guarantee "absolute" privacy. Even with the best encryption:
- Malware on your machine can capture data while you're using it
- Physical access to your computer (while you're logged in) allows data access
- Human factors (weak passwords, social engineering) can compromise security

### "Local-First Privacy" (Honest) ✅

MailMind's "Local-First Privacy" means:
- ✅ All email processing happens on your machine (not sent to cloud)
- ✅ Data is encrypted at rest with industry-standard encryption
- ✅ You control your data (access, export, delete)
- ✅ Transparent about security boundaries (what IS and ISN'T protected)
- ✅ Clear recommendations for comprehensive protection (BitLocker, strong passwords, antivirus)

**Why we use "Local-First" instead of "Absolute":**
1. **Honesty:** We're transparent about security limitations
2. **Trust:** Users can make informed decisions based on realistic security boundaries
3. **Responsibility:** We don't make promises we can't keep
4. **Guidance:** We provide clear recommendations for additional protection

**Example of transparency:**
- "Email content never leaves your device" ✅ (True - we can guarantee this)
- "No one can ever access your data" ❌ (False - malware, admin access, physical access can)

**Our promise:** We'll always be honest about what we CAN protect (database files, data theft, file system access) and what we CANNOT protect (Outlook storage, memory while running, screen, malware). This transparency helps you make informed decisions and take appropriate additional security measures.

See [Privacy Policy](privacy-policy.md) for our complete privacy promise.

---

## Data Management Questions

### Q9: Can I export my data?

**Yes, absolutely.** Your data is yours, and you can export it at any time.

**Export Options:**
- **Settings → Data Management → Export All Data**
- Exports analysis data as JSON (standard, portable format)
- Includes summaries, classifications, tags, action items

**Direct Database Access:**
- Advanced users can access the SQLite database directly at `%LOCALAPPDATA%\MailMind\data\mailmind.db`
- Database is encrypted by default (requires decryption via MailMind application)
- Settings → Privacy → Disable Encryption to create unencrypted copy (with strong warning)

**No Lock-In:** MailMind uses open standards (SQLite, JSON) so your data is always accessible and portable.

See [Privacy Policy - Data Portability](privacy-policy.md#data-portability).

---

### Q10: How do I delete my data?

**You have complete control over your data.**

**Options:**

1. **Clear Analysis Cache:**
   - Settings → Privacy → Clear Analysis Data
   - Removes all AI-generated analysis (summaries, tags, etc.)
   - Keeps application settings

2. **Delete Specific Emails:**
   - Remove individual email analysis results
   - Right-click email → Delete Analysis

3. **Complete Removal:**
   - Uninstall MailMind via Windows Settings → Apps
   - Database file is securely overwritten during uninstall
   - Manually delete folders if desired:
     - `%LOCALAPPDATA%\MailMind\`
     - `%APPDATA%\MailMind\`

4. **Secure Deletion:**
   - For highly sensitive data, use file shredding tools (e.g., Eraser, BleachBit)
   - This prevents forensic recovery of deleted database files

**Important:** Deleting MailMind data does NOT delete your original Outlook emails (those are stored separately by Outlook).

See [Privacy Policy - Data Deletion](privacy-policy.md#data-deletion).

---

### Q11: Does MailMind collect telemetry or usage analytics?

**No telemetry by default. Opt-in only.**

**What MailMind does NOT collect:**
- ❌ Email addresses, subjects, or content
- ❌ Sender or recipient information
- ❌ Usage analytics or behavior tracking
- ❌ No Google Analytics, Mixpanel, or similar services
- ❌ No third-party tracking scripts

**Optional Crash Reporting (Disabled by Default):**
- You can enable crash reporting in Settings → Privacy → Crash Reporting
- If enabled, sanitized error logs may be sent to MailMind servers
- All email addresses, subjects, and bodies are automatically removed from crash reports
- Only technical error information (stack traces, error messages) is included
- You can disable at any time

**Performance Metrics (Stored Locally Only):**
- MailMind tracks performance metrics for optimization (tokens/second, cache hit rates)
- These metrics are stored locally in your database
- Never uploaded to MailMind servers

**Privacy Promise:** We don't monetize your data, track your behavior, or sell information to advertisers.

See [Privacy Policy - Data Collection](privacy-policy.md#what-data-we-do-not-collect).

---

## Compliance Questions

### Q12: Is MailMind GDPR compliant?

**Yes, MailMind is GDPR-friendly for EU users.**

**GDPR Compliance:**
- ✅ **Data Minimization:** Only process what's necessary for functionality
- ✅ **Local Processing:** Data processed locally (no transfer to third parties)
- ✅ **Right to Access:** Full access to all your data at any time
- ✅ **Right to Export:** Export all data as JSON
- ✅ **Right to Deletion:** Delete all data at any time
- ✅ **Right to Portability:** Data in open formats (SQLite, JSON)
- ✅ **No Consent Needed:** Local processing doesn't require GDPR consent

**Why MailMind is GDPR-friendly:**
- Since all processing happens locally on your machine, MailMind acts as a tool you control (not a data processor)
- No data is transferred to MailMind, Inc. or any third parties
- You have complete control over your data

**Important:** While MailMind provides strong privacy protections, users in regulated industries should conduct their own compliance assessment.

See [Privacy Policy - Legal Framework](privacy-policy.md#compliance).

---

### Q13: Is MailMind CCPA compliant?

**Yes, MailMind is CCPA-friendly for California users.**

**CCPA Compliance:**
- ✅ **No Sale of Data:** We never collect personal data, so we can't sell it
- ✅ **Right to Know:** Privacy policy documents what data is processed (Section 1)
- ✅ **Right to Delete:** You can delete all data at any time (Settings → Privacy)
- ✅ **Right to Opt-Out:** No need to opt-out since we don't collect data in the first place

**Why MailMind is CCPA-friendly:**
- All processing happens locally
- MailMind, Inc. never receives your email data
- No data sharing with third parties

See [Privacy Policy - Legal Framework](privacy-policy.md#compliance).

---

### Q14: Can I use MailMind in a regulated industry (healthcare, finance)?

**Proceed with caution. Conduct your own compliance assessment.**

**MailMind provides:**
- ✅ Encryption at rest (256-bit AES)
- ✅ Local processing (no cloud upload)
- ✅ Data access controls (Windows DPAPI)
- ✅ Audit trail (activity logs)

**However:**
- ⚠️ MailMind is NOT a HIPAA-certified Business Associate
- ⚠️ MailMind is NOT audited for SOC 2, ISO 27001, or similar certifications
- ⚠️ Users in regulated industries must conduct their own risk assessment

**Recommendations for regulated industries:**
1. **Consult Legal/Compliance:** Review MailMind architecture with your legal team
2. **Risk Assessment:** Evaluate MailMind's security boundaries against your requirements
3. **Additional Controls:** Enable full-disk encryption, use strong authentication, audit logs
4. **Testing:** Conduct penetration testing or security audit in your environment
5. **Documentation:** Document your risk assessment and mitigation measures

**Use Cases:**
- **Low Risk:** General business email processing (non-sensitive)
- **Medium Risk:** Internal communications (with additional controls)
- **High Risk:** Healthcare PHI, financial data, legal privileged communications (consult compliance team first)

See [Privacy Policy - HIPAA Considerations](privacy-policy.md#compliance).

---

## Technical Questions

### Q15: What encryption algorithm does MailMind use?

**MailMind uses industry-standard encryption:**

**Database Encryption:**
- **Algorithm:** AES-256-CBC (256-bit Advanced Encryption Standard in Cipher Block Chaining mode)
- **Implementation:** SQLCipher (open-source SQLite encryption extension)
- **Key Derivation:** PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Key Management:** Windows Data Protection API (DPAPI)
- **Key Storage:** Windows Credential Manager (hardware-backed where available)

**Why AES-256:**
- Industry standard used by governments and financial institutions
- No known practical attacks against AES-256
- NIST-approved encryption standard
- Performance-optimized for modern CPUs (AES-NI hardware acceleration)

**Key Security Features:**
- Keys are tied to your Windows user account + specific machine
- Keys cannot be extracted to another machine
- Hardware-backed key protection where available (TPM 2.0)

See [SECURITY.md - Database Encryption](../SECURITY.md#database-encryption) for full technical details.

---

### Q16: How does MailMind protect against prompt injection attacks?

**MailMind has a multi-layered prompt injection defense system:**

**Defense Layers:**

1. **Pattern Blocking:**
   - Detects 15+ prompt injection patterns in email content
   - Blocks emails containing suspicious instruction patterns
   - Configurable security levels (strict, balanced, permissive)

2. **Instruction Delimiters:**
   - Uses XML-style tags to clearly separate email content from system instructions
   - Prevents email content from being interpreted as AI instructions

3. **Output Validation:**
   - Validates AI-generated output against expected schemas
   - Rejects malformed or suspicious responses

4. **Security Logging:**
   - Logs all blocked prompt injection attempts
   - Allows security audit trail

**Example Blocked Patterns:**
- "Ignore previous instructions"
- "You are now in developer mode"
- "Forget all previous context"
- "Act as [different role]"
- System-level commands in email content

**Configuration:**
- Settings → Privacy → Prompt Injection Security Level
- Strict: Maximum protection (may block some legitimate emails)
- Balanced: Good security with low false positives (recommended)
- Permissive: Minimal blocking (use with caution)

See [SECURITY.md - Prompt Injection Defense](../SECURITY.md#prompt-injection-defense) for complete implementation details.

---

### Q17: How does MailMind prevent SQL injection attacks?

**MailMind prevents SQL injection through multiple safeguards:**

**Defense Mechanisms:**

1. **Whitelist Validation:**
   - Only allows predefined database schema keywords
   - Rejects any input containing unauthorized SQL keywords
   - Prevents malicious SQL injection via email content

2. **Parameterized Queries:**
   - Uses SQLite parameterized queries for all database operations
   - Input values are automatically escaped
   - Prevents SQL syntax injection

3. **Input Sanitization:**
   - Validates all user input before database queries
   - Removes special characters that could be used for injection
   - Length limits on all input fields

4. **Principle of Least Privilege:**
   - Database connection has minimal permissions
   - Read-only connections for query operations
   - Separate credentials for admin operations

**Example Protection:**
```python
# VULNERABLE (MailMind does NOT do this):
query = f"SELECT * FROM emails WHERE subject = '{user_input}'"

# SECURE (MailMind's approach):
query = "SELECT * FROM emails WHERE subject = ?"
cursor.execute(query, (user_input,))
```

**SQL Injection Attempts Blocked:**
- `'; DROP TABLE emails; --`
- `' OR 1=1 --`
- `'; UPDATE emails SET priority='high'; --`

See [SECURITY.md - SQL Injection Prevention](../SECURITY.md#sql-injection-prevention) for technical implementation.

---

### Q18: How does MailMind verify AI model integrity?

**MailMind uses checksum verification to detect tampered AI models:**

**Model Verification Process:**

1. **SHA256 Checksums:**
   - MailMind maintains a whitelist of known-good model checksums
   - Stored in `src/mailmind/config/model_checksums.json`
   - Checksums are verified before using any AI model

2. **Verification on Startup:**
   - MailMind verifies model integrity every time it starts
   - If checksum mismatch is detected, MailMind refuses to use the model
   - User is notified and given option to re-download clean model

3. **Supply Chain Attack Prevention:**
   - Protects against compromised models downloaded from registry
   - Detects if model files were modified after download
   - Prevents backdoored or malicious models from processing your emails

4. **Secure Model Storage:**
   - Models stored in `%USERPROFILE%\.ollama\models\`
   - Checksum database stored separately in MailMind config

**What Model Verification Protects:**
- ✅ Detects model tampering by attackers
- ✅ Prevents malicious model injection
- ✅ Verifies model integrity before processing sensitive emails

**Limitations:**
- ❌ Cannot detect zero-day vulnerabilities in model architecture
- ❌ Cannot detect backdoors present in original model (relies on trusted sources)
- ❌ Assumes initial checksum database is trustworthy

See [SECURITY.md - Model Checksum Verification](../SECURITY.md#model-checksum-verification) for implementation details.

---

## Still Have Questions?

**Can't find your answer?**

- **Email:** privacy@mailmind.ai
- **Security Issues:** security@mailmind.ai (for vulnerabilities - DO NOT open public GitHub issues)
- **Documentation:**
  - [SECURITY.md](../SECURITY.md) - Technical security implementation
  - [Privacy Policy](privacy-policy.md) - Data handling and user rights
  - [README.md](../README.md) - General product information

---

**Last Updated:** October 16, 2025
**Version:** 1.0.0
