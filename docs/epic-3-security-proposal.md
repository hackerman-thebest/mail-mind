# Epic 3: Security & MVP Readiness

## Overview
Critical security fixes and MVP readiness improvements identified from security assessment. These stories address vulnerabilities that must be fixed before MVP launch.

**Epic Points:** 15 story points
**Priority:** P0 - Critical (blocks MVP launch)
**Timeline:** 4-week sprint

## Stories

### Story 3.1: Database Encryption Implementation
**Points:** 5
**Priority:** P0 - Critical
**Dependencies:** Story 2.2 (DatabaseManager exists)

#### Problem
Database stores all emails in plain text despite "Absolute Privacy" marketing claim. The `encryption_key` parameter exists but SQLCipher is not implemented.

#### Acceptance Criteria
- AC1: Implement SQLCipher for database encryption
- AC2: Use Windows DPAPI for key management
- AC3: Migrate existing databases to encrypted format
- AC4: Performance impact <10% (target <5%)
- AC5: Transparent to existing code (no API changes)
- AC6: Add encryption status to settings UI
- AC7: Document encryption in privacy policy

#### Implementation
1. Install pysqlcipher3 package
2. Modify DatabaseManager.__init__ to use SQLCipher
3. Implement key derivation from Windows DPAPI
4. Add migration tool for existing databases
5. Update backup/restore to handle encrypted DBs
6. Add unit tests for encryption verification

---

### Story 3.2: Prompt Injection Defense
**Points:** 3
**Priority:** P0 - Critical
**Dependencies:** Story 1.2 (EmailPreprocessor exists)

#### Problem
EmailPreprocessor only logs warnings for suspicious content but continues processing. Malicious emails could manipulate AI responses.

#### Acceptance Criteria
- AC1: Block emails with prompt injection patterns
- AC2: Return safe error response instead of processing
- AC3: Log security events to separate security.log
- AC4: Add "Report Suspicious Email" feature
- AC5: Configurable security level (Strict/Normal/Permissive)
- AC6: User notification for blocked emails
- AC7: Maintain list of blocked patterns (updatable)

#### Implementation
1. Enhance EmailPreprocessor.sanitize_content()
2. Add SecurityException for blocked content
3. Create security event logger
4. Add UI for security notifications
5. Implement pattern update mechanism
6. Add comprehensive security tests

---

### Story 3.3: Performance & Security Optimization
**Points:** 5
**Priority:** P0 - Critical
**Dependencies:** Story 1.1 (OllamaManager), Story 1.3 (EmailAnalysisEngine)

#### Problem
1. SQL injection vulnerability in database_manager.py line 963
2. No Ollama connection pooling (performance bottleneck)
3. No model checksum verification (supply chain risk)

#### Acceptance Criteria
- AC1: Fix SQL injection vulnerability (parameterized queries)
- AC2: Implement Ollama connection pooling
- AC3: Add model checksum verification
- AC4: Parallel email processing for batch operations
- AC5: Achieve 10-15 emails/minute target
- AC6: Add performance metrics dashboard
- AC7: Document security improvements

#### Implementation
1. Replace f-string SQL with parameterized queries
2. Implement OllamaConnectionPool class
3. Add model_checksums.json with verified hashes
4. Implement ThreadPoolExecutor for batch processing
5. Add performance monitoring to UI
6. Security audit all SQL queries

---

### Story 3.4: Marketing & Documentation Alignment
**Points:** 2
**Priority:** P1 - Important
**Dependencies:** Stories 3.1-3.3 complete

#### Problem
Marketing claims don't match implementation. Need to align messaging with actual security features.

#### Acceptance Criteria
- AC1: Update marketing to "Local-First Privacy"
- AC2: Add security documentation
- AC3: Create privacy policy
- AC4: Update README with security features
- AC5: Add security FAQ
- AC6: Document known limitations
- AC7: Create security roadmap

#### Implementation
1. Review all marketing materials
2. Create SECURITY.md documentation
3. Update product website
4. Create user-facing security guide
5. Document encryption status clearly
6. Add security badges to README

## Implementation Order
1. **Week 1:** Story 3.2 (Prompt Injection) - Quick win, immediate security improvement
2. **Week 2:** Story 3.3 (Performance & SQL fixes) - Critical vulnerabilities
3. **Week 3-4:** Story 3.1 (Database Encryption) - Most complex, highest impact
4. **Week 4:** Story 3.4 (Documentation) - Final alignment

## Testing Strategy
- Security penetration testing after each story
- Performance benchmarking for encryption overhead
- User acceptance testing for security UX
- Automated security scanning in CI/CD

## Success Metrics
- Zero critical security vulnerabilities
- Database encryption enabled by default
- Performance targets met (10-15 emails/minute)
- 100% test coverage for security code
- Clear, honest marketing alignment

## Risks & Mitigation
- **Risk:** Encryption performance impact
  - **Mitigation:** Make optional with clear trade-offs
- **Risk:** Breaking existing functionality
  - **Mitigation:** Comprehensive integration tests
- **Risk:** User experience degradation
  - **Mitigation:** Progressive security (start normal, user can increase)

## Alternative: Integrate into Story 2.6
If you prefer not to create Epic 3, these items could be added to Story 2.6's scope:
- Add AC13-AC16 to Story 2.6 for security fixes
- Increase Story 2.6 points from 8 to 13
- Extend timeline by 1-2 weeks

However, I recommend Epic 3 for better tracking and separation of concerns.