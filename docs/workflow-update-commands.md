# Workflow Commands to Add Epic 3

## Step 1: Update Epic Stories File
Run these commands in sequence:

```bash
# 1. Load PM agent to update epics
/bmad:bmm:agents:pm

# 2. When menu appears, choose option to edit epic-stories.md
# Or directly edit the file
```

## Step 2: Add Epic 3 to Workflow Status

```bash
# 1. Load SM agent
/bmad:bmm:agents:sm

# 2. Update the workflow status
*update-backlog

# This will add the 4 new stories to BACKLOG:
# - Story 3.1: Database Encryption (5 points)
# - Story 3.2: Prompt Injection Defense (3 points)
# - Story 3.3: Performance & Security Optimization (5 points)
# - Story 3.4: Marketing Alignment (2 points)
```

## Step 3: Continue Current Work

```bash
# Complete Story 2.6 first (already in progress)
/bmad:bmm:agents:dev

# Run the implementation
*dev-story
```

## Step 4: After Story 2.6 Complete

```bash
# Move to Epic 3
/bmad:bmm:agents:sm

# Draft first security story
*create-story 3.1
```

## Alternative: Manual Update
If you prefer to manually update:

1. Edit `/docs/epic-stories.md`:
   - Add Epic 3 section after Epic 2
   - Copy content from `epic-3-security-proposal.md`

2. Edit `/docs/project-workflow-status-2025-10-13.md`:
   - Update Epic/Story Summary section
   - Add 4 stories to BACKLOG
   - Update total points from 72 to 87
   - Adjust progress percentage

3. Commit changes:
```bash
git add docs/epic-*.md docs/project-workflow-status*.md
git commit -m "Add Epic 3: Security & MVP Readiness (15 points)"
```

## Timeline Impact

### Current Plan (Epic 1 & 2 only):
- Complete by: Today (Story 2.6 implementation)
- Total points: 72
- Progress: 97%

### With Epic 3:
- Complete by: +2 weeks
- Total points: 87
- Current progress: 77% (67/87)
- MVP ready: After Epic 3 complete

## Priority Recommendation

Given the critical security issues:

1. **TODAY:** Continue with Story 2.6 (don't break momentum)
2. **TOMORROW:** Add Epic 3 to workflow
3. **NEXT WEEK:** Start Story 3.2 (Prompt Injection - quickest fix)
4. **WEEK 2:** Story 3.3 (SQL injection & performance)
5. **WEEK 3-4:** Story 3.1 (Database encryption - biggest change)
6. **WEEK 4:** Story 3.4 (Documentation alignment)

This ensures MVP is truly ready for launch with no critical vulnerabilities.