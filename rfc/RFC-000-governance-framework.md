# RFC-000: Clarity Gate Governance Framework

**RFC ID:** RFC-000  
**Title:** Governance Framework  
**Type:** Meta  
**Status:** APPROVED  
**Created:** 2026-01-26  
**Revised:** 2026-01-27 (v0.5)  
**Author:** Francesco Marinoni Moretto

---

## 1. Summary

Minimal governance for Clarity Gate:

1. **Document hierarchy** — FORMAT_SPEC > SKILL.md > everything else
2. **Two RFC types** — Normative (changes validation) vs Informative (everything else)
3. **Versioning policy** — MAJOR.MINOR.PATCH with explicit triggers
4. **Validator compatibility** — Wire compatibility within major versions
5. **Threat model** — Operational guidance with honest uncertainty

**Restructuring:** This RFC supersedes and restructures RFC-001 through RFC-004. See §3.3.

---

## 2. Document Hierarchy

### 2.1 Authority Order

```
1. FORMAT_SPEC.md     — Normative (MUST follow)
2. SKILL.md           — Behavioral (SHOULD follow)  
3. Everything else    — Informative (MAY follow)
```

**Conflict rule:** Higher number loses. FORMAT_SPEC always wins.

### 2.2 What Goes Where

| Content | Document | RFC Required? |
|---------|----------|---------------|
| CGD structure, fields, validation codes | FORMAT_SPEC | Yes (Normative) |
| LLM production guidance, checklists | SKILL.md | Yes if adds validation behavior |
| Human workflows, HITL procedures | PROCEDURES | No |
| Examples, integrations, community | docs/, examples/ | No |

---

## 3. RFC Types and Numbering

### 3.1 Two Types Only

| Type | Scope | Approval | Version Impact |
|------|-------|----------|----------------|
| **Normative** | Changes FORMAT_SPEC, adds validation codes | Author + 1 reviewer | MINOR or MAJOR |
| **Informative** | Everything else | Author only (or PR) | None or PATCH |

**Decision rule:** Does it change what validators check? → Normative. Otherwise → Informative.

### 3.2 Reviewer Requirements

**Reviewer pool:** Maintainer (Francesco Marinoni Moretto) + experts listed in MAINTAINERS.md.

| Situation | Resolution |
|-----------|------------|
| Author proposes reviewer | Reviewer must not be author |
| Reviewer doesn't respond in 14 days | Author may request different reviewer |
| Author disagrees with reviewer | Maintainer makes final decision |
| No qualified reviewer available | Defer RFC until reviewer found |

### 3.3 Restructuring (This RFC)

Original RFCs are **superseded and renumbered**:

| Original | New | Status |
|----------|-----|--------|
| RFC-001 (CGD Checklist) | Merged into RFC-001 | SUPERSEDED |
| RFC-002 (FORMAT_SPEC Clarifications) | Merged into RFC-001 | SUPERSEDED |
| RFC-003 (Chunk Context) | Becomes RFC-002 | RENUMBERED |
| RFC-004 (Community) | Becomes RFC-003 | RENUMBERED |

**Conflict resolution for merged RFCs:** Where original RFC-001 and RFC-002 conflict, RFC-002 content wins (it was more normative).

**Next RFC number:** RFC-004.

### 3.4 RFC Lifecycle

```
DRAFT → PROPOSED → APPROVED → IMPLEMENTED → [SUPERSEDED]
                      │
                      └→ REJECTED
```

---

## 4. Versioning Policy

### 4.1 Format

```
MAJOR.MINOR.PATCH

Current: 2.0.0
```

### 4.2 What Triggers Each Level

| Level | Trigger | Examples |
|-------|---------|----------|
| **MAJOR** | Breaking changes — existing valid CGDs may become invalid | Remove required field, change field semantics |
| **MINOR** | New features, backward compatible — new fields OR new validation codes | Add `chunk-context` field, add W-CC* warnings |
| **PATCH** | Clarifications only — no new fields, no new codes | Explain existing semantics, fix typos |

**Explicit rule:** New warning codes (W-*) = MINOR bump. Clarifications without new codes = PATCH.

### 4.3 Version Plan

| RFC | Change Type | Version Bump |
|-----|-------------|--------------|
| RFC-001 (merged) | New validation codes W-HC*, W-ST* | 2.0.0 → 2.1.0 |
| RFC-002 (chunk context) | New field + W-CC* codes | 2.1.0 → 2.2.0 |

*Note: Revised from original plan. Adding validation codes is MINOR, not PATCH.*

### 4.4 Deprecation Policy

| Phase | Action | Timeline |
|-------|--------|----------|
| Deprecate | Mark DEPRECATED, add W-* warning | vX.Y release |
| Grace period | Users migrate | Minimum 3 months OR 2 minor versions |
| Remove | Delete in next MAJOR, provide migration guide | vX+1.0 release |

**Migration guides are REQUIRED for all MAJOR version bumps.**

### 4.5 Validator Compatibility

**Wire compatibility promise:** All v2.x validators are wire-compatible. A v2.0 validator can process v2.9 CGDs (with warnings for unknown features).

| Situation | Validator Behavior |
|-----------|-------------------|
| Unknown field in CGD | IGNORE silently (forward compatibility) |
| Missing optional field | ACCEPT with default value |
| CGD major version > validator major | WARN: "CGD uses newer format, upgrade validator" |
| CGD major version < validator major | ACCEPT with INFO: "CGD uses older format" |
| Unknown validation code in CGD | IGNORE silently |

**Key distinction:**
- Unknown fields → silent ignore (expected in forward compatibility)
- Major version mismatch → warn but continue (not fatal)

---

## 5. Threat Model

### 5.1 What Clarity Gate Does

| Threat | CG Response | Confidence |
|--------|-------------|------------|
| Unmarked projection | Flags for Point 2 | Estimated HIGH (not measured) |
| Implicit assumption | Flags for Point 3 | Estimated MEDIUM (context-dependent) |
| Internal inconsistency | Flags for Point 5 | Estimated HIGH (automated comparison) |
| Stale timestamp | Flags for Point 8 | Estimated HIGH (date comparison) |
| Unverified specific claim | Routes to HITL | N/A (human decides) |

**Honesty note:** Confidence ratings are estimates based on pattern complexity, not empirical measurement. No test coverage data exists yet.

### 5.2 What Clarity Gate Does NOT Do

| Threat | Why Not | Required Control |
|--------|---------|------------------|
| Verify claims are TRUE | CG checks form, not truth | HITL verification |
| Detect fabricated metadata | CG trusts `confirmed-by` | Audit logging, access control |
| Detect malicious content | Out of scope | Security scanning |
| Prevent prompt injection | Out of scope | Input sanitization |

### 5.3 HITL Operational Guidance

**Minimum requirements:**

| Aspect | Requirement |
|--------|-------------|
| Who verifies | Named human with domain knowledge |
| What to check | Source exists, claim matches source, source is current |
| Documentation | `confirmed-by`, `confirmed-date`, source note |
| Escalation | If unsure → flag for additional review, do NOT mark confirmed |

**HITL is NOT:**
- Rubber-stamping a checkbox
- Automated verification
- Trusting the document author

### 5.4 Validator Trust

**Assumption:** Validators are trusted code running in trusted environment.

**If validator is compromised:** All guarantees void. CGD status is meaningless.

**Operator responsibilities:**
- Use validators from trusted sources (official releases)
- Verify validator version
- Audit validator behavior periodically

---

## 6. RFC Process

### 6.1 Minimal Template

```markdown
# RFC-NNN: [Title]

**Type:** Normative | Informative  
**Status:** DRAFT | PROPOSED | APPROVED | IMPLEMENTED  
**Author:** [Name]  
**Affects:** [Documents]

## Summary
[2-3 sentences]

## Problem
[What's broken?]

## Proposal
[What to change?]

## Alternatives
[What else was considered?]

## Decision
- [ ] APPROVED
- [ ] REJECTED: [reason]
```

### 6.2 Process Flow

```
Typo/clarification (no new codes)? → PR directly

Changes validation? → Normative RFC
   1. Write RFC using template
   2. Get 1 reviewer from pool (§3.2)
   3. Address feedback
   4. Mark APPROVED
   5. Implement changes
   6. Mark IMPLEMENTED

Everything else? → Informative RFC or PR
   1. Write RFC or PR
   2. Self-review sufficient
   3. Merge
```

### 6.3 RFC Application Checklist

**When an RFC is APPROVED, apply it completely:**

| Step | Action | Verify |
|------|--------|--------|
| 1 | Update FORMAT_SPEC | Version bump in header |
| 2 | Update SKILL.md | Version bump + new sections |
| 3 | Move scripts to `skills/*/scripts/` | Scripts executable, tests pass |
| 4 | Move test vectors to `skills/*/references/` or `docs/` | Paths updated in spec |
| 5 | Update CHANGELOG.md | New version section |
| 6 | Update README.md | Version banner |
| 7 | Update ARCHITECTURE.md | Version header |
| 8 | Rebuild dist package | `dist/*.skill` current |

**Definition of IMPLEMENTED:** All 8 steps complete. RFC stays APPROVED until then.

**Common mistake:** Updating spec text but forgetting to move reference implementations. Scripts defined in an RFC are deliverables, not development artifacts.

### 6.4 RFC Location

**Canonical location:** `clarity-gate/rfc/`

| Status | Location |
|--------|----------|
| DRAFT | Author's choice (meta repo, gist, PR) |
| PROPOSED → APPROVED | Move to `clarity-gate/rfc/` |
| SUPERSEDED | Move to `clarity-gate/rfc/archive-superseded/` |

**Naming convention:** `RFC-NNN-short-title.md` (e.g., `RFC-001-format-spec-clarifications.md`)

**Rule:** The `clarity-gate/rfc/` directory is the single source of truth. Working drafts may exist elsewhere but are not authoritative.

### 6.5 Urgent Fixes

**Critical bugs or security issues:**

1. Fix via PR immediately (no RFC gate)
2. Document in CHANGELOG with "HOTFIX" tag
3. Create retroactive RFC if change is normative
4. Validator releases follow semver; all v2.x releases are wire-compatible (§4.5)

---

## 7. Deferred Decisions

| Topic | Deferred Until | Rationale |
|-------|----------------|-----------|
| Multi-reviewer model | >3 active contributors | Project too small now |
| Release cadence | First validator release | No releases yet |
| Automated validation | First validator exists | Nothing to automate |
| Formal voting | >5 active contributors | Single maintainer now |
| Threat model test coverage | Benchmark suite complete | No empirical data yet |

---

## 8. Implementation

### 8.1 On Approval

1. Archive original RFC-001, 002, 003, 004 as SUPERSEDED
2. Publish new RFC-001 (merged), RFC-002 (chunk), RFC-003 (community)
3. Create MAINTAINERS.md with reviewer pool
4. Add link to this RFC from README

### 8.2 With v2.1.0 Release

1. Extract §5 to `docs/THREAT_MODEL.md`
2. Add validator compatibility note to FORMAT_SPEC §1
3. Update CONTRIBUTING.md with RFC process from §6

---

## 9. Decision

- [x] APPROVED
- [ ] REJECTED: [reason]

**Reviewer:** Perplexity (adversarial review)  
**Date:** 2026-01-27

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-01-26 | Initial draft |
| 0.2.0 | 2026-01-26 | Fixed bootstrap dependency, simplified RFC types, added deprecation policy |
| 0.3.0 | 2026-01-26 | Added: explicit "new codes = MINOR" rule, reviewer pool definition, wire compatibility promise, RFC restructuring plan, confidence honesty note, 14-day reviewer timeout |
| 0.4.0 | 2026-01-27 | Added: §6.3 RFC Application Checklist (8-step process for APPROVED → IMPLEMENTED) |
| 0.5.0 | 2026-01-27 | Added: §6.4 RFC Location (canonical location policy) |

---

*RFC-000 v0.5 — minimal governance for Clarity Gate*
