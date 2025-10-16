# Frequently Asked Questions (FAQ)

**MailMind - Privacy-First AI Email Assistant**

## Security & Privacy

### Is my data encrypted?

**Yes!** MailMind encrypts your email analysis database by default using industry-standard 256-bit AES encryption.

**What's encrypted:**
- ✅ **Database file:** All email analysis data, priority scores, summaries, action items
- ✅ **User preferences:** Settings and configuration
- ✅ **Writing style profiles:** Your learned writing patterns
- ✅ **Sender importance data:** Priority learning information

**What's NOT encrypted:**
- ❌ **Outlook email storage:** Original emails in Outlook (outside MailMind's control)
- ❌ **Application memory:** Decrypted data while application is running
- ❌ **Screen display:** Email content shown in UI

**Encryption technology:**
- **Algorithm:** SQLCipher with 256-bit AES-CBC
- **Key management:** Windows DPAPI (Data Protection API)
- **Key derivation:** PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Performance:** <5% overhead (typically 2-3%)

**Platform support:**
- **Windows 10/11:** Full encryption support ✅
- **macOS/Linux:** Not yet supported (planned for v2.0) ⏳

**Learn more:** [SECURITY.md](SECURITY.md)

---

### Does MailMind send my emails to the cloud?

**No!** MailMind is a **local-first** application. All AI processing happens on your machine.

**What stays local:**
- ✅ All email content processing
- ✅ AI inference (via Ollama running on your machine)
- ✅ Email analysis and summarization
- ✅ Priority classification and learning
- ✅ Response generation
- ✅ Writing style analysis

**What goes to external servers:**
- ❌ Nothing! MailMind does not connect to any external services.
- ⚠️ **Optional telemetry** (disabled by default): Anonymous usage statistics only (no email content)

**Why local-first?**
- **Privacy:** Your emails never leave your device
- **Security:** No cloud storage or API keys required
- **Control:** You own your data
- **Speed:** No network latency
- **Offline:** Works without internet connection (after initial setup)

---

### How does MailMind protect my privacy?

MailMind is designed with **privacy by default**:

1. **Local AI Processing:** Ollama runs on your machine, not in the cloud
2. **Database Encryption:** 256-bit AES encryption for all stored data
3. **No Cloud Upload:** Email content never sent to external servers
4. **Secure Key Management:** Windows DPAPI protects encryption keys
5. **Optional Telemetry:** Disabled by default, user-controlled
6. **Sanitized Logs:** PII automatically removed from diagnostic logs
7. **Open Source:** Code available for security audit

**Data flows:**
```
Outlook (on your PC)
    ↓
MailMind (on your PC)
    ↓
Ollama AI (on your PC)
    ↓
Encrypted Database (on your PC)
    ↓
[NO CLOUD UPLOAD]
```

**Telemetry (if enabled):**
- Anonymous usage statistics (e.g., "email analysis completed in 2.5s")
- Crash reports (sanitized, no PII)
- NO email content, subjects, senders, or personal information

**Control:** Settings → Privacy → Data Collection

---

### Can I disable encryption?

**Yes**, but it's **NOT RECOMMENDED** for privacy-conscious users.

**To disable encryption:**
1. Open Settings → Privacy → Database Encryption
2. Click "Disable Encryption"
3. Read the warning carefully (double confirmation required)
4. Wait for migration to complete

**⚠️ Warning:** Disabling encryption:
- Removes 256-bit AES protection from your database
- Makes email data vulnerable if someone gains file access
- Stores all email analysis in **unencrypted plain text**

**Why would I disable encryption?**
- Performance testing (encryption has <5% overhead)
- Compatibility with older SQLite tools
- Development/debugging purposes
- **Not recommended for production use**

**Safety:** MailMind creates an automatic backup before disabling encryption. You can re-enable encryption at any time.

---

### How do I enable encryption for an existing database?

**Migration is easy and automatic:**

1. Open Settings → Privacy → Database Encryption
2. Click "Enable Encryption (Migrate Database)"
3. Wait for migration progress (typically 1-5 minutes)
4. Encryption enabled!

**What happens during migration:**
1. ✅ Automatic backup created
2. ✅ New encrypted database created
3. ✅ All data copied with progress tracking
4. ✅ Data integrity verification
5. ✅ Original database replaced
6. ✅ Rollback to backup if any error occurs

**Migration performance:**
- ~1000 emails/second
- Large databases (>500MB) supported
- Progress bar shows real-time status

**Safety:** Your original database is backed up before migration. If migration fails, MailMind automatically restores from backup.

---

### Where are encryption keys stored?

Encryption keys are stored **securely** using Windows DPAPI:

**Key storage location:**
- Windows Credential Manager (target: "MailMind_DatabaseEncryptionKey")
- Keys protected with Windows DPAPI (CryptProtectData)
- Keys tied to your Windows user account + machine

**Key derivation:**
- DPAPI key → PBKDF2 (100,000 iterations) → SQLCipher key
- Random salt stored in database (not secret)
- 64-byte derived keys for SQLCipher

**Security properties:**
- ✅ Keys cannot be extracted to another machine
- ✅ Keys cannot be read by other users
- ✅ No hardcoded keys in code
- ✅ Automatic hardware-backed protection where available

**Access control:**
- Only your Windows user account can access keys
- System administrators CAN access keys (Windows limitation)
- Malware running as your user CAN access keys (OS limitation)

**Best practices:**
1. Use strong Windows password
2. Enable BitLocker for full-disk encryption
3. Keep Windows updated (DPAPI security patches)
4. Don't share your Windows account

**Learn more:** [SECURITY.md](SECURITY.md) - Key Management Flow

---

## Installation & Setup

### What are the system requirements?

**Minimum Requirements:**
- **OS:** Windows 10/11 (Mac support planned for v2.0)
- **RAM:** 16GB minimum
- **Disk:** 10GB free space (including AI models)
- **CPU:** Modern x64 processor

**Recommended Requirements:**
- **RAM:** 32GB
- **GPU:** NVIDIA GPU with CUDA support (optional but recommended)
- **Disk:** SSD for better performance
- **CPU:** Multi-core processor (6+ cores ideal)

**Software Requirements:**
- Python 3.10 or higher
- Ollama AI platform
- AI model (Llama 3.1 8B or Mistral 7B)
- Microsoft Outlook (for email integration)

---

### How do I install MailMind?

See [README.md#Installation](README.md#installation) for step-by-step installation instructions.

**Quick start:**
```bash
# 1. Clone repository
git clone https://github.com/yourusername/mail-mind.git
cd mail-mind

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Ollama
# Download from https://ollama.com/download

# 4. Download AI model
ollama pull llama3.1:8b-instruct-q4_K_M

# 5. Run MailMind
python main.py
```

---

### Which AI model should I use?

**Recommended:**
- **Llama 3.1 8B** (`llama3.1:8b-instruct-q4_K_M`)
  - Best balance of quality and performance
  - ~5GB download
  - Works on 16GB RAM systems

**Fallback:**
- **Mistral 7B** (`mistral:7b-instruct-q4_K_M`)
  - Slightly faster than Llama
  - ~4GB download
  - Good for lower-end hardware

**Advanced (if you have 32GB+ RAM):**
- **Llama 3.1 13B** (`llama3.1:13b-instruct-q4_K_M`)
  - Better quality, slower performance
  - ~8GB download

**MailMind automatically:**
- Tries primary model first (Llama 3.1 8B)
- Falls back to Mistral 7B if primary unavailable
- Provides clear error messages if neither model is available

---

## Features & Usage

### What can MailMind do?

**Current features (v1.0):**
1. **AI-Powered Email Analysis**
   - Priority classification (High/Medium/Low)
   - Email summarization
   - Action item extraction
   - Sentiment analysis
   - Smart tagging

2. **Learning System**
   - Learns from your priority corrections
   - Tracks sender importance
   - Adapts to your email patterns
   - Accuracy improves over time (>85% after 30 days)

3. **Response Generation**
   - AI-powered email responses
   - Learns your writing style
   - Multiple lengths (Brief/Standard/Detailed)
   - Four tone options (Professional/Friendly/Formal/Casual)
   - Thread context awareness

4. **Security & Privacy**
   - 256-bit AES database encryption
   - Local AI processing (no cloud)
   - Secure key management
   - Privacy-first design

5. **Performance**
   - Quick priority: <500ms
   - Full analysis: <2s
   - Cache hit: <100ms
   - Response generation: <5s

**Planned features (v2.0):**
- Desktop UI (CustomTkinter)
- Outlook integration (real-time sync)
- Smart folders and rules
- Email scheduling
- Cross-platform support (Mac/Linux)

---

### Does MailMind work offline?

**Partially:**
- ✅ **After setup:** MailMind works offline for email analysis and response generation
- ✅ **AI inference:** Ollama runs locally, no internet required
- ✅ **Database access:** All data stored locally
- ❌ **Initial setup:** Requires internet to download AI models (~5GB)
- ❌ **Email sync:** Requires connection to fetch new emails from Outlook

**Offline capabilities:**
- Analyze already-downloaded emails
- Generate responses
- Train on existing data
- Access cached analysis results

---

## Troubleshooting

### MailMind is slow. How can I speed it up?

**Performance tips:**

1. **Enable GPU acceleration** (if you have NVIDIA GPU):
   - Ollama automatically uses GPU if available
   - Check logs for "GPU detected" message
   - 5-10x speedup on compatible GPUs

2. **Use recommended model:**
   - Llama 3.1 8B (best balance)
   - Mistral 7B (faster, slightly lower quality)

3. **Reduce batch size:**
   - Settings → Performance → Batch Size
   - Lower batch size = less memory, slightly slower

4. **Close memory-hungry applications:**
   - MailMind needs 2-4GB RAM
   - Ollama needs 4-6GB RAM for models

5. **Use SSD for database:**
   - Settings → Advanced → Database Location
   - SSD significantly faster than HDD

**Performance monitoring:**
- Check logs for processing times
- Look for memory pressure warnings
- See [README.md#Troubleshooting](README.md#troubleshooting) for more tips

---

### Where can I get help?

**Documentation:**
- [README.md](README.md) - Getting started and features
- [SECURITY.md](SECURITY.md) - Security architecture
- [FAQ.md](FAQ.md) - This file!
- [docs/stories/](docs/stories/) - Feature stories and implementation details

**Troubleshooting:**
- [README.md#Troubleshooting](README.md#troubleshooting) - Common issues
- `docs/user-guide/troubleshooting.md` - Detailed troubleshooting guide
- `docs/developer-guide/error-handling-patterns.md` - Developer guide

**Report Issues:**
1. Help → Report Issue (in application)
2. Exports sanitized logs to clipboard
3. Create GitHub issue with logs
4. Or email: support@mailmind.ai

**Community:**
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and community support

---

## Advanced

### Can I contribute to MailMind?

**Not yet.** MailMind is currently in active development. Contributions will be welcome after v1.0 release.

**Future contribution areas:**
- Code contributions (features, bug fixes)
- Documentation improvements
- Translation and localization
- Testing and QA
- Security audits

**Stay tuned:**
- Watch the GitHub repository for updates
- Follow project roadmap in [README.md#Roadmap](README.md#roadmap)

---

### Is MailMind open source?

**Yes!** MailMind is open source for transparency and security auditing.

**License:** See [LICENSE](LICENSE) for details.

**Why open source?**
- **Security:** Allow independent security audits
- **Trust:** Users can verify privacy claims
- **Transparency:** No hidden cloud uploads or data collection
- **Community:** Future community contributions

---

### What about GDPR/CCPA compliance?

**MailMind is designed for privacy compliance:**

**GDPR (European Union):**
- ✅ Local processing (no data transfer)
- ✅ User control over data
- ✅ Right to erasure (delete database)
- ✅ Data minimization (only analyze needed fields)
- ✅ Encryption by default

**CCPA (California):**
- ✅ No personal data sale
- ✅ User control and transparency
- ✅ Right to delete
- ✅ Opt-in telemetry

**HIPAA (Healthcare):**
- ⚠️ Encryption at rest ✅
- ⚠️ Local processing ✅
- ⚠️ Audit trails (planned)
- ⚠️ Conduct your own compliance assessment for healthcare use

**Note:** While MailMind implements strong privacy protections, users in regulated industries should conduct their own compliance assessment and potentially enable additional safeguards (e.g., disable telemetry, use full-disk encryption).

---

## Updates

**Last Updated:** 2025-10-15
**Version:** 1.0.0
**Stories Completed:** 6/12 (46% progress)

**Recent additions:**
- ✅ Database Encryption (Story 3.1)
- ✅ Response Generation (Story 1.5)
- ✅ Priority Learning (Story 1.4)
- ✅ Email Analysis (Story 1.3)
- ✅ Email Preprocessing (Story 1.2)
- ✅ Ollama Integration (Story 1.1)

**Coming soon:**
- 🔄 Performance Optimization (Story 1.6)
- 🔄 Desktop UI (Story 2.3)
- 🔄 Outlook Integration (Story 2.1)
- 🔄 macOS/Linux encryption support (v2.0)
