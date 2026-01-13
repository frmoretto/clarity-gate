# Clarity Gate Threat Model

**Version:** 1.0
**Date:** 2026-01-12
**Status:** Initial Release

---

## Overview

This document identifies attack vectors against Clarity Gate and documents mitigations. Understanding what CGD prevents—and what it doesn't—is essential for safe deployment.

---

## Core Security Principle

> **Clarity Gate verifies FORM, not TRUTH.**

This is not a limitation to fix; it's a design boundary to understand. The system ensures claims are *properly marked* as uncertain—it cannot verify if claims are *actually true*.

---

## Threat Categories

| Category | Risk Level | Mitigation |
|----------|------------|------------|
| False Source Attribution | CRITICAL | HITL Round B mandatory |
| Selective Hedging | HIGH | Human judgment required |
| Assumption Hiding | MEDIUM | Point 3 catches some; HITL catches rest |
| Round A Rubber-Stamping | MEDIUM | Process design, not tool design |
| Adversarial Claim Chaining | MEDIUM-HIGH | Document-level review |
| Expertise Signaling | HIGH | HITL verification of credentials |

---

## T1: False Source Attribution (CRITICAL)

### Attack Vector

An LLM (or malicious human) fabricates sources to pass verification:

```markdown
FAILS: "Revenue will be $50M"
PASSES: "Revenue is projected to be $50M [Source: Q3 Planning Doc]"
```

The second passes Clarity Gate even if:
- The "Q3 Planning Doc" doesn't exist
- The document exists but says something different
- The citation is to a hallucinated URL

### Why It's Critical

This is the fundamental limitation of form-based verification. A well-formatted lie passes; a poorly-formatted truth fails.

### Mitigation

| Layer | Action | Responsibility |
|-------|--------|----------------|
| **System** | Route source-dependent claims to Round B | Automatic |
| **HITL** | Verify cited sources actually exist | Human reviewer |
| **HITL** | Verify sources actually support claims | Human reviewer |
| **Process** | Spot-check *(e.g., 10%)* of "sourced" claims | QA process |

### Detection Signals

- Multiple claims citing same obscure source
- Sources that can't be located
- Citation style inconsistent with document
- Suspiciously convenient source availability

### Residual Risk

**Cannot be eliminated.** A determined attacker who creates fake sources and cites them correctly will pass automated verification. HITL is the only defense.

---

## T2: Selective Hedging (HIGH)

### Attack Vector

Add uncertainty markers to unimportant claims while stating critical claims as facts:

```markdown
The weather tomorrow is *(estimated)* to be sunny.        ← Hedged (unimportant)
Our system handles 10,000 requests per second.            ← Stated as fact (critical)
Response time is *(projected)* to improve next quarter.   ← Hedged (unimportant)
```

The document "looks" properly qualified but the critical claim is unmarked.

### Why It's High Risk

Creates false confidence. Reviewers see hedging and assume document is thorough.

### Mitigation

| Layer | Action | Responsibility |
|-------|--------|----------------|
| **System** | Flag high-specificity claims (Point 9) | Automatic |
| **System** | Flag performance/capability claims (Point 7) | Automatic |
| **HITL** | Review ALL specific numbers, not just hedged ones | Human reviewer |
| **Process** | Train reviewers on selective hedging pattern | Training |

### Detection Signals

- Hedging ratio: many hedged claims but few on core assertions
- Specific numbers without hedging
- Performance claims stated as present fact

### Residual Risk

**Partially mitigated.** Points 7 and 9 catch many cases, but sophisticated selective hedging requires human judgment.

---

## T3: Assumption Hiding (MEDIUM)

### Attack Vector

Bury critical assumptions in footnotes, appendices, or fine print:

```markdown
# Executive Summary
Our system achieves 99.9% uptime and handles enterprise scale.

...

[Page 47, Appendix C, footnote 12]
*Uptime measured during off-peak hours only. "Enterprise scale" 
defined as <100 concurrent users.*
```

### Why It's Medium Risk

Point 3 (Assumption Visibility) catches inline hidden assumptions, but not document-structure attacks.

### Mitigation

| Layer | Action | Responsibility |
|-------|--------|----------------|
| **System** | Point 3 flags missing assumption markers | Automatic |
| **HITL** | Review executive summaries against appendices | Human reviewer |
| **Process** | Require assumptions in same section as claims | Style guide |

### Detection Signals

- Executive summary with no bracketed assumptions
- Footnotes/appendices with qualifying language
- Mismatch between summary confidence and body hedging

### Residual Risk

**Partially mitigated.** Document structure attacks require full-document human review.

---

## T4: Round A Rubber-Stamping (MEDIUM)

### Attack Vector

Human reviewers in Round A (Derived Data Confirmation) approve without reading:

```
## Derived Data Confirmation

These claims came from sources found in this session:

- API costs $0.005 per call (OpenAI pricing page)
- Model accuracy is 95% (internal benchmark)
- Competitor X has no equivalent feature (their docs)

Reply "confirmed" or flag any I misread.
```

Reviewer types "confirmed" without checking if interpretations are correct.

### Why It's Medium Risk

Defeats the purpose of Round A. Creates false sense of verification.

### Mitigation

| Layer | Action | Responsibility |
|-------|--------|----------------|
| **Design** | Keep Round A lists short (<10 items) | System |
| **Design** | Randomize order to prevent pattern-matching | System |
| **Process** | Time-gate responses (minimum review time) | Process |
| **Process** | Periodic audit of Round A confirmations | QA |

### Detection Signals

- Confirmation time < 5 seconds
- 100% confirmation rate over many documents
- No flags ever raised in Round A

### Residual Risk

**Process risk, not tool risk.** Cannot be solved technically; requires organizational discipline.

---

## T5: Adversarial Claim Chaining (MEDIUM-HIGH)

### Attack Vector

Build false conclusions from individually-true premises:

```markdown
- Company X reported $10M revenue *(verified)*
- Industry average growth is 20% *(verified)*
- Therefore, Company X will reach $12M next year ← FALSE CONCLUSION

[The conclusion doesn't follow—Company X might be declining]
```

Each claim passes individually, but the chain is invalid.

### Why It's Medium-High Risk

Clarity Gate verifies claims in isolation. Logical relationships between claims are not checked.

### Mitigation

| Layer | Action | Responsibility |
|-------|--------|----------------|
| **System** | Point 6 (Implicit Causation) catches some | Automatic |
| **HITL** | Review logical flow, not just individual claims | Human reviewer |
| **Process** | Require explicit reasoning markers | Style guide |

### Detection Signals

- "Therefore" / "thus" / "consequently" without hedging
- Conclusions more specific than premises support
- Causal language without evidence markers

### Residual Risk

**Partially mitigated.** Full logical validation requires human reasoning or formal logic tools (out of scope).

---

## T6: Expertise Signaling (HIGH)

### Attack Vector

Claim expertise or authority without verification:

```markdown
Based on my 20 years of experience in machine learning...
As validated by leading researchers in the field...
Industry experts agree that...
According to peer-reviewed studies...
```

### Why It's High Risk

Authority claims bypass epistemic scrutiny. Readers trust "experts" without verification.

### Mitigation

| Layer | Action | Responsibility |
|-------|--------|----------------|
| **System** | Point 4 flags authority claims without sources | Automatic |
| **System** | Point 9 routes "expert" claims to verification | Automatic |
| **HITL** | Verify credentials when claimed | Human reviewer |
| **Process** | Require specific citations, not appeals to authority | Style guide |

### Detection Signals

- "Experts agree" without naming experts
- Credential claims without verification
- Appeal to unnamed "studies" or "research"

### Residual Risk

**Partially mitigated.** Credential verification is expensive; often impractical for all claims.

---

## What Clarity Gate Prevents

| Threat | Prevention Level | Mechanism |
|--------|------------------|-----------|
| Unmarked projections stated as facts | ✅ HIGH | Point 2 |
| Hidden assumptions | ✅ HIGH | Point 3 |
| Internal contradictions | ✅ HIGH | Point 5 |
| Future state as present | ✅ HIGH | Point 7 |
| Stale temporal claims | ✅ HIGH | Point 8 |
| Unverified specific numbers | ✅ MEDIUM | Point 9 (flags, doesn't verify) |
| Implicit causation | ✅ MEDIUM | Point 6 |

---

## What Clarity Gate Does NOT Prevent

| Threat | Why Not | Mitigation |
|--------|---------|------------|
| Fabricated sources | Verifies form, not truth | HITL source verification |
| Well-formatted lies | Same | HITL fact-checking |
| Selective hedging | Requires judgment | Human review of critical claims |
| Logical fallacies | Out of scope | Human reasoning |
| Adversarial prompt injection | Different attack surface | Input sanitization |
| Social engineering | Human factors | Training |

---

## HITL as Security Boundary

HITL is not optional. It's the security boundary between form verification and truth verification.

### When HITL is MANDATORY

| Scenario | Round | Why |
|----------|-------|-----|
| Claims with external sources | B | Must verify sources exist and support claims |
| Performance/capability claims | B | High-value targets for fabrication |
| Credential/authority claims | B | Easy to fabricate |
| Statistical claims | B | Often misremembered or outdated |
| Competitor claims | B | May be outdated or biased |

### When HITL is Advisory

| Scenario | Round | Why |
|----------|-------|-----|
| LLM interpretations of witnessed sources | A | Quick confirmation sufficient |
| Internal document references | A | Verifiable within session |
| Formatting/style issues | — | Not security-relevant |

---

## Deployment Security Recommendations

### For Low-Risk Use Cases (Internal Docs, Drafts)

```yaml
# Illustrative configuration — adjust thresholds to your needs
minimum_security:
  hitl_round_a: optional
  hitl_round_b: required
  source_verification: spot-check  # e.g., 10%
  audit_trail: recommended
```

### For Medium-Risk Use Cases (Published Content, RAG KBs)

```yaml
# Illustrative configuration — adjust thresholds to your needs
standard_security:
  hitl_round_a: required
  hitl_round_b: required
  source_verification: all external sources
  audit_trail: required
  review_time_minimum: 30 seconds per claim  # example
```

### For High-Risk Use Cases (Legal, Financial, Medical, Safety-Critical)

```yaml
# Illustrative configuration — adjust thresholds to your needs
high_security:
  hitl_round_a: required (2 reviewers)
  hitl_round_b: required (2 reviewers)
  source_verification: all sources + independent verification
  audit_trail: required + signed
  external_fact_check: required (FEVER, ClaimBuster, or equivalent)
  review_time_minimum: 60 seconds per claim  # example
```

---

## Incident Response

### If Fabricated Source Discovered Post-Ingestion

1. **Quarantine:** Remove document from RAG knowledge base immediately
2. **Trace:** Identify all queries that retrieved the document
3. **Notify:** Alert users who received responses based on the document
4. **Audit:** Review HITL process—why was this missed?
5. **Update:** Add pattern to detection signals

### If Systematic Attack Detected

1. **Pause:** Halt ingestion pipeline
2. **Forensics:** Identify attack vector and scope
3. **Remediate:** Remove all affected documents
4. **Harden:** Add detection rules for attack pattern
5. **Resume:** With enhanced monitoring

---

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — System architecture and 9-point verification
- [CLARITY_GATE_FORMAT_SPEC.md](CLARITY_GATE_FORMAT_SPEC.md) — Unified format specification (v2.0)
- [DEPLOYMENT.md](DEPLOYMENT.md) — Deployment playbook
- [CLARITY_GATE_PROCEDURES.md](CLARITY_GATE_PROCEDURES.md) — Verification procedures

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-12 | Initial threat model |

---

*End of threat model*
