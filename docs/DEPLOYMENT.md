# Clarity Gate Deployment Guide

**Version:** 1.0
**Date:** 2026-01-12
**Status:** Initial Release

---

## Overview

This guide covers deploying Clarity Gate across different use cases, from personal document verification to enterprise RAG pipelines.

---

## Deployment Options

| Method | Best For | Setup Time |
|--------|----------|------------|
| Claude Skill | Individual use, small teams | ~5 minutes *(estimated)* |
| npm/PyPI Package | Developers, CI/CD integration | 15 minutes |
| Manual Checklist | No-code environments | Immediate |

---

## Quick Start: Claude Skill

### Prerequisites

- Claude Desktop or Claude Code
- Ability to upload custom skills

### Installation

**Option A: From Repository (Recommended)**

1. Clone: `git clone https://github.com/frmoretto/clarity-gate`
2. Navigate to `skills/clarity-gate/`
3. Copy `SKILL.md` content into Claude's custom instructions

### First Verification

```
You: Please run Clarity Gate on this document:

[paste document text]
```

Expected output:
- 9-point verification results
- HITL verification table (Round A and/or Round B)
- Issues found with suggested fixes
- Final determination (PASS/FAIL/NEEDS_REVIEW)

---

## Developer Installation

> **Note:** npm/PyPI packages are at v1.0.0 and validate the v1.x spec. v2.0 update is planned.

### npm (Node.js/TypeScript)

```bash
npm install clarity-gate
clarity-gate check your-document.cgd.md
```

### PyPI (Python)

```bash
pip install clarity-gate
clarity-gate check your-document.cgd.md
```

### CLI Commands

```bash
clarity-gate check <file>        # Auto-detect and validate
clarity-gate validate-cgd <file> # Validate as CGD
clarity-gate validate-sot <file> # Validate as SOT
clarity-gate detect <file>       # Detect document type
```

### Programmatic Alternative

For Claude-based verification, use the skill prompt from `skills/clarity-gate/SKILL.md`.

---

## Pre-Deployment Checklist

### Technical Requirements

| Item | Check | Notes |
|------|-------|-------|
| Skill/package installed | ☐ | Claude skill or npm/pip |
| Test verification run | ☐ | Verify on sample document |
| HITL workflow defined | ☐ | Who reviews? How are claims routed? |
| Audit trail configured | ☐ | Where are decisions logged? |

### Process Requirements

| Item | Check | Notes |
|------|-------|-------|
| HITL reviewers identified | ☐ | At least 2 for redundancy |
| Review SLA defined | ☐ | e.g., 24h for Round B claims |
| Escalation path defined | ☐ | What happens if reviewer unsure? |
| Source verification process | ☐ | How are external sources checked? |

### Documentation Requirements

| Item | Check | Notes |
|------|-------|-------|
| Team trained on 9 points | ☐ | Review ARCHITECTURE.md |
| Threat model understood | ☐ | Review THREAT_MODEL.md |
| Style guide updated | ☐ | Add epistemic markers to standards |

---

## Deployment by Use Case

### Use Case 1: Research Paper Verification

**Goal:** Catch internal inconsistencies before submission/publication.

**Priority Points:** 1, 4, 5 (Hypothesis labeling, unvalidated data, consistency)

**Workflow:**

1. Author writes paper
2. Run Clarity Gate before submission
3. Address all CRITICAL and WARNING issues
4. HITL reviews Round B claims (data, statistics)
5. Re-run to confirm fixes
6. Submit when PASS achieved

---

### Use Case 2: RAG Knowledge Base

**Goal:** Prevent epistemically unclear documents from entering production KB.

**Priority Points:** 1, 2, 3, 7, 8, 9 (All epistemic + temporal + verifiable)

**Workflow:**

1. Document submitted for ingestion
2. Automated Clarity Gate check
3. Auto-PASS: Ingest immediately
4. NEEDS_REVIEW: Route to HITL queue
5. HITL completes Round A (quick) + Round B (thorough)
6. Approved: Ingest with audit trail
7. Rejected: Return to author with feedback

**Success Metrics:**

| Metric | Target |
|--------|--------|
| Auto-pass rate | >80% |
| HITL queue depth | <50 documents |
| Post-ingestion issues | 0 CRITICAL |

---

### Use Case 3: Business Document Review

**Goal:** Catch unmarked projections and assumptions before stakeholder distribution.

**Priority Points:** 2, 3, 7 (Uncertainty markers, assumptions, future-as-present)

**Common Fixes:**

| Before | After |
|--------|-------|
| "Revenue will be $50M" | "Revenue is **projected** to be $50M" |
| "The system scales linearly" | "The system scales linearly [assuming <1000 users]" |
| "We have 500 customers" | "We have ~500 customers *(as of 2026-01-12)*" |

---

### Use Case 4: Safety-Critical Documentation

**Goal:** Maximum verification for legal, medical, financial, or safety-related content.

**Priority Points:** All 9 points

**Additional Requirements:**

| Requirement | Implementation |
|-------------|----------------|
| Dual review | Two reviewers must independently approve |
| External verification | Use FEVER, ClaimBuster, or equivalent |
| Audit trail | Timestamped log of all decisions |
| Version control | Track all document changes |

---

## Monitoring and Metrics

### Dashboard Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Auto-pass rate | % documents passing without HITL | >80% |
| HITL queue depth | Documents awaiting review | <50 |
| Average review time | Time from submission to decision | <24h |
| Issue distribution | Which points fail most often | Track |

### Alerting Thresholds

| Condition | Alert Level | Action |
|-----------|-------------|--------|
| Auto-pass rate < 60% | WARNING | Review document quality guidance |
| HITL queue > 100 | WARNING | Add reviewers or increase automation |
| Review time > 48h | WARNING | Escalate or add capacity |

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| High false positive rate | Rules too strict | Review failing points; adjust thresholds |
| HITL queue growing | Not enough reviewers | Add capacity or improve auto-pass rate |
| Same issues recurring | Authors not trained | Conduct training on 9 points |

### Error Messages

| Error | Meaning | Fix |
|-------|---------|-----|
| `C2: Missing required field` | CGD frontmatter incomplete | Add missing YAML field |
| `C5: Invalid state combination` | clarity-status/hitl-status mismatch | Check valid combinations in CLARITY_GATE_FORMAT_SPEC.md |
| `C12: Exclusion block malformed` | BEGIN/END mismatch | Check IDs match and no nesting |

---

## Rollback Procedures

### If Bad Document Ingested

1. **Identify:** Document ID and ingestion timestamp
2. **Quarantine:** Remove from active RAG index
3. **Trace:** Find all queries that retrieved document
4. **Assess:** Evaluate impact on responses
5. **Notify:** Alert affected users if necessary
6. **Fix:** Correct document or reject permanently
7. **Post-mortem:** Why did verification fail?

---

## Scaling Considerations

| Scale | Recommendation |
|-------|----------------|
| Small (<100 docs/month) | Claude skill, manual HITL |
| Medium (100-1000 docs/month) | npm/pip integration, HITL queue |
| Large (>1000 docs/month) | API deployment (Phase 3), dedicated HITL team |

---

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — 9-point verification system
- [THREAT_MODEL.md](THREAT_MODEL.md) — Security considerations
- [CLARITY_GATE_FORMAT_SPEC.md](CLARITY_GATE_FORMAT_SPEC.md) — Unified format specification (v2.0)
- [CLARITY_GATE_PROCEDURES.md](CLARITY_GATE_PROCEDURES.md) — Verification procedures
- [ROADMAP.md](ROADMAP.md) — Future integrations

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-12 | Initial deployment guide |

---

*End of deployment guide*
