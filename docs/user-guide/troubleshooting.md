# MailMind Troubleshooting Guide

**User Guide - Version 1.0**
**Last Updated:** 2025-10-15

Having trouble with MailMind? This guide will help you solve common issues quickly.

## Table of Contents

1. [Quick Fixes](#quick-fixes)
2. [Ollama Issues](#ollama-issues)
3. [Outlook Connection Issues](#outlook-connection-issues)
4. [Performance Issues](#performance-issues)
5. [Database Issues](#database-issues)
6. [Getting Help](#getting-help)

---

## Quick Fixes

Before diving into specific issues, try these quick fixes first:

### ✅ Restart MailMind
Close and reopen MailMind. Many temporary issues resolve themselves after a restart.

### ✅ Restart Outlook
If you're having email sync issues, restart Microsoft Outlook and then restart MailMind.

### ✅ Check Your Internet Connection
MailMind needs internet to download AI models. Ensure you're connected.

### ✅ Free Up Memory
Close unused applications if MailMind is running slowly. MailMind works best with at least 2GB of free memory.

---

## Ollama Issues

### "MailMind requires Ollama to run. Would you like to download it now?"

**What this means:** MailMind needs Ollama (the AI engine) to analyze your emails, but it's not installed.

**How to fix:**

1. **Download Ollama:**
   - Visit: https://ollama.ai/download
   - Download the installer for your operating system
   - Run the installer

2. **Verify Installation:**
   - Open Terminal (Mac) or Command Prompt (Windows)
   - Type: `ollama --version`
   - You should see a version number

3. **Restart MailMind**

**Still not working?**
- Make sure Ollama is running in the background
- On Mac: Look for Ollama in your menu bar
- On Windows: Check your system tray

---

### "AI model 'llama3.1' is not available. Downloading model..."

**What this means:** The AI model needs to be downloaded (this is normal for first-time use).

**What to expect:**
- **Download size:** ~5GB
- **Download time:** 10-20 minutes (depends on your internet speed)
- **Progress:** You'll see a progress bar during download

**How to fix if stuck:**

1. **Manual Download:**
   ```
   # Open Terminal/Command Prompt
   ollama pull llama3.1:8b-instruct-q4_K_M
   ```

2. **Use Smaller Model (Faster Download):**
   - MailMind will automatically try Mistral (3.5GB) if Llama fails
   - Mistral is faster but slightly less accurate

3. **Check Disk Space:**
   - Ensure you have at least 10GB free disk space
   - Models are stored in `~/.ollama/models/`

**Still downloading after 30 minutes?**
- Your internet may be slow. Let it continue or try again later.
- Check if your antivirus is blocking the download

---

### "Downloading AI model... estimated 15 minutes remaining"

**This is normal!** AI models are large files. Here's what you can do:

✅ **Leave it downloading** - You can minimize MailMind and continue working

✅ **Check progress** - MailMind shows real-time progress

✅ **One-time download** - You only need to download each model once

❌ **Don't cancel** - Canceling means you'll have to start over

---

## Outlook Connection Issues

### "Microsoft Outlook is not running. Please start Outlook and try again."

**What this means:** MailMind needs Outlook to be open to access your emails.

**How to fix:**

1. **Start Outlook:**
   - Open Microsoft Outlook
   - Wait for it to fully load (you should see your emails)

2. **Make sure Outlook is connected:**
   - Click "Send/Receive" in Outlook
   - Ensure you're not in offline mode

3. **Restart MailMind**

**Pro tip:** Keep Outlook running in the background while using MailMind.

---

### "Outlook denied permission to access emails. Please grant permission."

**What this means:** Outlook's security is blocking MailMind.

**How to fix:**

1. **Grant Permission:**
   - When Outlook shows a security dialog, click **"Allow"**
   - Check **"Allow access for 10 minutes"** (or longer)

2. **Disable Antivirus Temporarily:**
   - Some antivirus software blocks Outlook access
   - Temporarily disable it and try again

3. **Run as Administrator (Windows):**
   - Right-click MailMind icon
   - Select "Run as administrator"

**Trust MailMind:**
- MailMind only reads emails locally - nothing is sent to the cloud
- Your emails stay private on your computer

---

### "Email folder 'Inbox' was not found."

**What this means:** MailMind can't find the folder you're trying to access.

**How to fix:**

1. **Check folder name:**
   - Open Outlook and verify the folder exists
   - Folder names are case-sensitive

2. **Common folder names:**
   - ✅ "Inbox" (correct)
   - ❌ "inbox" (wrong - lowercase)
   - ✅ "Sent Items" (correct)
   - ❌ "Sent" (wrong - different name)

3. **Custom folders:**
   - If you use custom folders, enter the exact name as shown in Outlook

---

## Performance Issues

### "Insufficient memory detected. Close some applications for better performance."

**What this means:** Your computer is running low on memory (RAM).

**How to fix:**

1. **Close Unused Applications:**
   - Close web browsers with many tabs
   - Close other heavy applications (Photoshop, video editors, etc.)
   - Keep only Outlook and MailMind open

2. **Restart Your Computer:**
   - Frees up memory from background processes
   - Often improves overall performance

3. **Upgrade Memory (Long-term):**
   - MailMind recommends 16GB RAM
   - Minimum: 8GB RAM
   - Check your computer's memory: System Settings > About

**MailMind will automatically:**
- Process fewer emails at once
- Reduce memory usage
- Continue working (just slower)

---

### MailMind is Slow / Freezing

**Common causes:**

1. **Low Memory:**
   - See "Insufficient memory" section above

2. **Large Email Volume:**
   - Processing 1000+ emails takes time
   - First-time indexing can take 10-30 minutes

3. **Old Computer:**
   - Minimum specs: 8GB RAM, modern processor
   - Recommended: 16GB RAM, recent CPU

**How to speed up:**

✅ **Process in Smaller Batches:**
   - Analyze 50 emails at a time instead of 500

✅ **Close Background Apps:**
   - Free up CPU and memory

✅ **Let it Finish:**
   - First-time indexing is slow but only happens once

✅ **Enable Caching:**
   - MailMind remembers analyzed emails (faster next time)

---

## Database Issues

### "Database corruption detected. Restoring from backup..."

**What this means:** MailMind's database file was damaged (rare but possible).

**What MailMind does automatically:**
1. Detects the corruption
2. Finds your latest backup
3. Restores from backup
4. Continues working

**You don't need to do anything!** MailMind handles this automatically.

**If restoration fails:**
- MailMind will create a fresh database
- You'll lose cached analysis (but not your emails)
- Your settings are preserved

**Prevent corruption:**
- Don't force-quit MailMind during processing
- Ensure stable power supply (laptops: keep charged)
- Regular backups happen automatically (daily)

---

### "Backup creation failed. Please check disk space."

**What this means:** MailMind can't create a backup (usually disk space issue).

**How to fix:**

1. **Check Disk Space:**
   - Ensure at least 5GB free space
   - Backups are stored in: `%APPDATA%/MailMind/backups/` (Windows) or `~/Library/Application Support/MailMind/backups/` (Mac)

2. **Delete Old Backups:**
   - MailMind keeps 10 backups automatically
   - Manually delete very old backups if needed

3. **Free Up Space:**
   - Delete unnecessary files
   - Empty trash/recycle bin
   - Uninstall unused applications

---

## Getting Help

### Report an Issue

If none of the above solutions work, you can report the issue:

1. **Collect Logs:**
   - Click **Help** → **Report Issue**
   - MailMind copies sanitized logs to your clipboard
   - Your emails/personal data is automatically removed

2. **Create Support Request:**
   - Email: support@mailmind.com (example - update with real email)
   - Include: Logs from clipboard, description of issue
   - Expected response time: 24-48 hours

3. **Include This Information:**
   - ✅ What you were doing when the error occurred
   - ✅ Error message (exact text)
   - ✅ Steps to reproduce the issue
   - ✅ Your operating system (Windows 10, macOS, etc.)
   - ✅ MailMind version (Help → About)

---

### Check Logs Yourself

Advanced users can check logs directly:

**Log Location:**
- **Windows:** `%APPDATA%\MailMind\logs\mailmind.log`
- **Mac:** `~/Library/Application Support/MailMind/logs/mailmind.log`
- **Linux:** `~/.local/share/MailMind/logs/mailmind.log`

**Log Levels:**
- `INFO` - Normal operations
- `WARNING` - Something unexpected (but handled)
- `ERROR` - Operation failed
- `CRITICAL` - Serious problem

**Viewing Logs:**
```bash
# Show last 50 lines
tail -50 ~/Library/Application\ Support/MailMind/logs/mailmind.log

# Search for errors
grep ERROR ~/Library/Application\ Support/MailMind/logs/mailmind.log
```

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10 / macOS 10.15 / Ubuntu 20.04 |
| **RAM** | 8GB (16GB recommended) |
| **Disk Space** | 10GB free |
| **Processor** | Modern multi-core CPU (2015 or newer) |
| **Dependencies** | Microsoft Outlook, Ollama |
| **Internet** | Required for model downloads |

### Recommended Specs

| Component | Recommendation |
|-----------|----------------|
| **RAM** | 16GB or more |
| **Disk** | SSD (faster than HDD) |
| **Processor** | Intel i5/i7, AMD Ryzen 5/7, Apple M1/M2 |
| **GPU** | Optional (speeds up AI processing) |

---

## FAQ

### Q: Is my email data sent to the cloud?

**A:** No! Everything runs locally on your computer:
- Ollama runs locally (no cloud)
- Emails stay in Outlook (local)
- Analysis happens on your computer
- Nothing is uploaded to any server

### Q: How long does first-time setup take?

**A:** Approximately 20-30 minutes:
- Ollama installation: 5 minutes
- Model download: 10-20 minutes
- First email indexing: 5-10 minutes

### Q: Can I use MailMind offline?

**A:** Yes! After initial setup:
- ✅ Analyze emails offline
- ✅ All features work without internet
- ❌ Can't download new models without internet

### Q: How much disk space do AI models use?

**A:**
- Llama 3.1 8B: ~5GB
- Mistral 7B: ~3.5GB
- Backups: ~50-100MB each (10 backups max)
- Cache: Grows over time (cleared automatically when >1GB)

### Q: Why does memory usage keep growing?

**A:** MailMind caches analyzed emails for speed:
- Cache clears automatically at 1GB
- You can manually clear cache: Settings → Advanced → Clear Cache
- This is normal behavior

### Q: Can I use a different email client?

**A:** Currently, MailMind only supports Microsoft Outlook:
- ❌ Gmail web (not supported)
- ❌ Apple Mail (not supported)
- ❌ Thunderbird (not supported)
- ✅ Outlook 2016/2019/2021/365

---

## Still Having Issues?

If this guide didn't solve your problem:

1. **Check for Updates:**
   - Help → Check for Updates
   - Install latest version

2. **Community Forum:**
   - Visit: community.mailmind.com (example)
   - Search existing solutions
   - Ask the community

3. **Contact Support:**
   - Email: support@mailmind.com (example)
   - Include logs (Help → Report Issue)
   - Response within 24-48 hours

---

**Document Version:** 1.0
**Last Updated:** 2025-10-15

**Feedback?** Help us improve this guide: docs@mailmind.com
