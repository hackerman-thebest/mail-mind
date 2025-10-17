# Epic 0: Setup & Reliability - Summary for Dawson

**Created:** 2025-10-17
**PM:** John (BMAD Product Manager Agent)
**Status:** Ready for Review & Implementation

---

## What I Did

### 1. ✅ Archived Non-Compliant Stories
Moved to `docs/stories/archive/`:
- `story-0.1.md` - Had some good ideas but not BMAD-compliant
- `Story_0.2_Enhanced_Diagnostics_Model_Selection.md` - Good analysis but wrong format

### 2. ✅ Created Proper Epic 0 Structure
**File:** `docs/Epic_0_Setup_Reliability.md`

A comprehensive, BMAD-compliant epic addressing all the issues you identified:

#### Story 0.1: System Resource Detection & Model Recommendation (3 pts)
- Detects RAM, CPU, GPU using `psutil`
- Recommends model based on available resources:
  - `llama3.2:1b` for 4-6 GB RAM
  - `llama3.2:3b` for 6-10 GB RAM **← RECOMMENDED DEFAULT**
  - `llama3.1:8b` for 10+ GB RAM
- Shows expected performance for each option
- **Addresses:** Your client's 8GB RAM system would get 3B model instead of failing with 8B

#### Story 0.2: Interactive Model Selection in Setup Wizard (5 pts)
- Enhanced `setup.bat` with model selection menu
- Shows detected resources + recommendation with ⭐
- User picks 1/2/3, downloads model, saves to `config/user_config.yaml`
- Main app reads user_config.yaml on startup
- **Addresses:** Gives users choice instead of assuming one-size-fits-all

#### Story 0.3: Unicode Error Fixes (2 pts) ⚡ QUICK WIN
- Adds `encoding='utf-8', errors='replace'` to ALL subprocess calls
- Fixes the exact crash you saw: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f`
- **Addresses:** Windows cp1252 vs UTF-8 issue - 10 minute fix!

#### Story 0.4: Interactive Diagnostic Remediation Menu (5 pts)
- When diagnostics fail, shows menu with 6 options:
  1. **Switch to smaller model** (auto-downloads, updates config, retries)
  2. **Re-download current model** (fixes corruption)
  3. **Show system resources** (detailed RAM/CPU/GPU/disk report)
  4. **Show Ollama logs** (auto-finds logs, displays last 50 lines)
  5. **Generate support report** (collects all diagnostic data)
  6. **Exit** (manual troubleshooting)
- **Addresses:** 80%+ of issues auto-fixable instead of requiring manual steps

#### Story 0.5: Dynamic Model Loading (3 pts) - NICE TO HAVE
- Runtime model switching: `python main.py --switch-model`
- Automatic fallback after 3 consecutive timeouts
- Model performance monitoring
- **Addresses:** Easy upgrade/downgrade path

### 3. ✅ Updated Main Epic Documentation
**File:** `docs/epic-stories.md`

- Added Epic 0 to overview (4 epics total now)
- Updated story count: 21 stories, 105 points total
- Added "Sprint 0" (Week 0-1) for setup work **before** main epics
- Updated implementation sequence to include Epic 0 as critical path

---

## Key Insights from Your Analysis

### Root Cause (Confirmed)
1. **Model too large for system** - 8B model needs 10GB+ RAM, client has ~8GB
2. **Unicode handling broken** - Windows subprocess using cp1252 instead of UTF-8
3. **No resource awareness** - Setup assumes everyone can run large models
4. **Manual troubleshooting only** - No automated fixes

### Solution Approach
**Tier 1 (Do First):** Stories 0.1, 0.2, 0.3 (10 points, ~5 hours)
- Fixes Unicode errors ✅
- Adds resource detection ✅
- Enables model selection ✅

**Tier 2 (High Value):** Story 0.4 (5 points, ~4 hours)
- Interactive remediation menu ✅
- Automated log retrieval ✅

**Tier 3 (Nice to Have):** Story 0.5 (3 points, ~2 hours)
- Runtime model switching
- Automatic fallback logic

### Recommended Immediate Action for Your Client
```bash
# Quick workaround while Epic 0 is being implemented:
ollama pull llama3.2:1b

# Edit config/config.yaml:
ollama:
  primary_model: "llama3.2:1b"
  fallback_model: "llama3.2:1b"

# Test again:
python main.py
```

This should work immediately on their 8GB system.

---

## Epic 0 Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Setup Success Rate | 30% | ? | >90% |
| Time to First Success | 15-30 min | ? | <5 min |
| Unicode Errors | Common | 0 | 0 |
| Issues Auto-Fixed | 0% | ? | >80% |
| Model Works on User System | 50% | ? | >95% |

---

## Implementation Priority

### Phase 1: Critical Fixes (Week 0, Days 1-2)
**Start Here! 10 points, ~5 hours**

1. **Story 0.3** (2 pts, 10 min) - Fix Unicode errors
   - Quick grep for all subprocess calls
   - Add `encoding='utf-8', errors='replace'`
   - Test with emoji outputs
   - **Result:** No more crashes in diagnostics

2. **Story 0.1** (3 pts, 2 hours) - Resource detection
   - Create `src/mailmind/utils/system_diagnostics.py`
   - Implement `check_system_resources()`
   - Implement `recommend_model()`
   - Add `psutil` to requirements.txt
   - **Result:** Know what hardware user has

3. **Story 0.2** (5 pts, 3 hours) - Model selection
   - Update `setup.bat` with interactive menu
   - Create `config/user_config.yaml` handling
   - Update main.py to read user_config
   - **Result:** Users pick appropriate model for their system

### Phase 2: Enhanced UX (Week 0-1, Days 3-5)
**If time permits: 5 points, ~4 hours**

4. **Story 0.4** (5 pts, 4 hours) - Interactive remediation
   - Create remediation menu in main.py
   - Implement all 6 options
   - Test on various failure scenarios
   - **Result:** 80%+ of issues auto-fixable

### Phase 3: Advanced Features (Future)
**Nice to have: 3 points, ~2 hours**

5. **Story 0.5** (3 pts, 2 hours) - Dynamic loading
   - Runtime model switching command
   - Automatic fallback logic
   - Performance monitoring
   - **Result:** Easy model upgrades/downgrades

---

## Dependencies & Blockers

**Blocks:**
- All of Epic 1 (AI features need working Ollama)
- All of Epic 2 (UI needs backend working)
- All of Epic 3 (Security needs stable foundation)

**Depends On:**
- None! This is foundational work

**External Dependencies:**
- Ollama installed (user responsibility, but we guide them)
- Python 3.10+ with pip
- Windows 10/11 for setup.bat

---

## Risks & Mitigations

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| psutil detection fails | Low | Med | Graceful fallback to manual selection |
| Model downloads fail | Med | High | Resume support, offline instructions |
| Remediation makes things worse | Low | High | Confirmation prompts, backup configs |
| Platform differences | Med | Med | Test on Win 10/11, provide guidance |
| Users ignore warnings | High | Med | Show expected performance, easy switching |

---

## Technical Highlights

### Model Recommendation Logic
```python
def recommend_model(available_ram_gb: float) -> str:
    if available_ram_gb >= 10:
        return 'llama3.1:8b-instruct-q4_K_M'  # Best quality
    elif available_ram_gb >= 6:
        return 'llama3.2:3b'  # Sweet spot ⭐
    else:
        return 'llama3.2:1b'  # Lightweight
```

### Unicode Fix (The 10-Minute Win)
```python
# Before (crashes):
subprocess.run(['ollama', 'run', model], capture_output=True, text=True)

# After (robust):
subprocess.run(
    ['ollama', 'run', model],
    capture_output=True,
    text=True,
    encoding='utf-8',      # Explicit UTF-8
    errors='replace'       # Replace invalid chars
)
```

### User Config Persistence
```yaml
# config/user_config.yaml
ollama:
  selected_model: "llama3.2:3b"
  model_size: "medium"
  selection_date: "2025-10-17"
  auto_selected: false

system:
  ram_gb: 8.0
  cpu_cores: 4
  gpu_detected: false
```

---

## Open Questions for You

1. **Timeline:** Start Epic 0 now or after current sprint?
2. **Scope:** Implement Tier 1 only (5 hours) or Tier 1 + 2 (9 hours)?
3. **Testing:** Do you have access to 4GB, 8GB, 16GB RAM systems for testing?
4. **Platform:** Focus on Windows only for now (as planned)?
5. **Quick Fix:** Should I implement just the Unicode fix RIGHT NOW (10 min) to unblock your client?

---

## Recommendation

**My Strong Recommendation: Implement Tier 1 NOW (Stories 0.1, 0.2, 0.3)**

**Why:**
- 10 story points = ~5 hours of work
- Solves real customer issue (your 8GB RAM client)
- Prevents 50-70% of users from failing setup
- Low risk, high reward
- Can be done in parallel with other work

**Suggested Approach:**
1. **Today:** Implement Story 0.3 (Unicode fix, 10 min) - Quick win
2. **This week:** Implement Stories 0.1 & 0.2 (resource detection + model selection, 5 hours)
3. **Test with your client:** See if llama3.2:3b works on their 8GB system
4. **Next week (if valuable):** Implement Story 0.4 (interactive remediation, 4 hours)

**Alternative (Minimal):**
- Just fix Unicode errors (Story 0.3, 10 min)
- Manually tell client to use llama3.2:1b
- Defer Epic 0 to later (risk: other users hit same issue)

---

## Files Created/Modified

**Created:**
- `docs/Epic_0_Setup_Reliability.md` - Full epic specification
- `docs/EPIC_0_SUMMARY.md` - This document
- `docs/stories/archive/` - Archived non-compliant stories

**Modified:**
- `docs/epic-stories.md` - Added Epic 0 to main epic list

**Ready to Create (when implementing):**
- `src/mailmind/utils/system_diagnostics.py` - Resource detection module
- `config/user_config.yaml` - User-specific model configuration
- Updated `setup.bat` - Enhanced model selection wizard
- Updated `main.py` - Unicode fixes + diagnostic enhancements

---

## Next Steps

**Decision Point:** Do you want to:
1. ✅ **Approve Epic 0 and start implementation** (recommended)
2. ⚠️ **Approve but defer to later** (risk: more users hit issues)
3. ❌ **Reject and use manual workarounds only** (not recommended)

If you approve, I can:
- Start with Story 0.3 (Unicode fix) right now (10 min)
- Create detailed story cards for Stories 0.1 and 0.2
- Set up implementation tracking

**Your call, Dawson!** What would you like to do?

---

_PM Agent John signing off. Epic 0 is ready for your review and decision._ 📋✅
