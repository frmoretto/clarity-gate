# RFC-001: FORMAT_SPEC and SKILL.md Clarifications

**RFC ID:** RFC-001
**Title:** Implicit Rule Clarifications and Production Checklist
**Type:** Normative
**Status:** IMPLEMENTED
**Created:** 2026-01-26
**Implemented:** 2026-01-27
**Author:** Francesco Marinoni Moretto
**Affects:** CLARITY_GATE_FORMAT_SPEC.md v2.0 → v2.1.0, SKILL.md v2.0 → v2.1.0
**Supersedes:** Original RFC-001 (CGD Checklist), Original RFC-002 (FORMAT_SPEC Clarifications)

---

## 1. Summary

This RFC consolidates two related changes:

1. **FORMAT_SPEC clarifications** — Explicit rules for claim completion status, source field semantics, claim ID formats, and body structure requirements
2. **SKILL.md production checklist** — Guidance for LLMs producing CGDs

Both address the same root cause: implicit rules that LLMs and humans misinterpret.

**Version bump:** 2.0.0 → 2.1.0 (MINOR — adds validation codes)

---

## 2. Problem Statement

### 2.1 Observed Failures

An LLM producing a CGD made these errors despite having FORMAT_SPEC access:

| Error | Root Cause |
|-------|------------|
| Invented `status: "pending"` field | Spec doesn't state that absence of `confirmed-*` indicates pending |
| Invented `source-instruction` / `verified-source` fields | Spec doesn't clarify `source` dual semantics |
| Omitted `## HITL Verification Record` section | Spec shows in examples but doesn't require |
| Used non-standard claim IDs | Spec shows hash-based but doesn't state if manual allowed |
| Wrong `hitl-pending-count` | No enforcement semantics defined |

### 2.2 Why This Matters

- **LLMs** follow explicit rules, not examples
- **Validators** need unambiguous rules
- **Humans** infer rules from examples, causing interpretation drift

---

## 3. FORMAT_SPEC Changes

### 3.1 Add §1.2.1 — Body Structure Requirements

**Location:** After §1.2 (Document Structure)

```markdown
### 1.2.1 Body Structure Requirements (Normative)

Documents with non-empty `hitl-claims` MUST include:

| Element | Requirement |
|---------|-------------|
| `## HITL Verification Record` section | MUST appear before end marker |
| Round A subsection | MUST appear if any Round A claims exist |
| Round B subsection | MUST appear if any Round B claims exist |

**Format:**

```markdown
## HITL Verification Record

### Round A: Derived Data Confirmation
- [claim summary] ([source]) ✓

### Round B: True HITL Verification
| # | Claim | Status | Verified By | Date |
|---|-------|--------|-------------|------|
| 1 | [claim text] | ✓ Confirmed | [name] | [date] |
| 2 | [claim text] | ⏳ Pending | — | — |
```

**Validation:**
- E-ST10: Missing `## HITL Verification Record` when `hitl-claims` non-empty
- W-ST11: Table rows don't match `hitl-claims` count
```

---

### 3.2 Add §1.3.2 — Claim Completion Status

**Location:** After §1.3.1 (YAML Serialization)

```markdown
### 1.3.2 Claim Completion Status (Normative)

Completion status is determined by field PRESENCE, not a status field:

| State | `confirmed-by` | `confirmed-date` | Meaning |
|-------|----------------|------------------|---------|
| **PENDING** | Absent | Absent | Awaiting verification |
| **VERIFIED** | Present | Present | Human confirmed |

**Rules:**
1. Both `confirmed-by` AND `confirmed-date` MUST be present for VERIFIED
2. `round` indicates verification TIER (A or B), NOT completion
3. `hitl-pending-count` MUST equal count of claims lacking `confirmed-by`

**Validation:**
- W-HC01: Has `confirmed-by` but not `confirmed-date` (or vice versa)
- E-SC06: `hitl-pending-count` doesn't match actual pending count

**Example — Pending:**
```yaml
hitl-claims:
  - id: claim-75fb137a
    text: "Base price is $99/mo"
    source: "Check pricing page at example.com/pricing"
    location: "api-pricing/1"
    round: B
    # No confirmed-by or confirmed-date = PENDING
```

**Example — Verified:**
```yaml
hitl-claims:
  - id: claim-75fb137a
    text: "Base price is $99/mo"
    source: "Pricing page, verified 2026-01-12"
    location: "api-pricing/1"
    round: B
    confirmed-by: Maria
    confirmed-date: 2026-01-12
```

**Rationale:** Presence/absence semantics prevent sync errors between a `status` field and actual verification data.

**Limitation:** This pattern blocks adding third states (e.g., "rejected", "machine-verified"). If needed in future, will require MAJOR version bump with migration guide.
```

---

### 3.3 Add §1.3.3 — Source Field Semantics

**Location:** After §1.3.2

```markdown
### 1.3.3 Source Field Semantics (Normative)

The `source` field serves different purposes based on claim state:

| State | `source` Contains | Example |
|-------|-------------------|---------|
| **PENDING** | Where/how to verify (actionable) | `"Check example.com/pricing"` |
| **VERIFIED** | What was found (record) | `"Pricing page, verified 2026-01-12"` |

**Actionable source requirements (PENDING claims):**
- MUST contain at least one of: URL, document name, person name
- MUST NOT be vague terms only ("industry reports", "various sources")

**Validation:**
- W-HC02: PENDING claim has non-actionable source

**Vague (triggers W-HC02):**
```yaml
source: "industry benchmarks"     # No URL, no doc name, no person
source: "various reports"         # Unverifiable
source: "research"                # Too generic
```

**Actionable (no warning):**
```yaml
source: "Check example.com/pricing"
source: "Q3 Report page 12"
source: "Ask Maria in Finance"
source: "SIA Staffing Report 2025, Table 3.2"
```

**W-HC02 Detection Heuristics (Informative):**

Validators SHOULD use the following heuristics:
```python
import re

def is_actionable_source(source: str) -> bool:
    source_lower = source.lower()
    # URL pattern
    if re.search(r'https?://|www\.|\w+\.(com|org|net|io|ai|gov|edu)', source):
        return True
    # Document reference
    if re.search(r'(page|p\.|section|table|fig|appendix)\s*[\d\.]+', source_lower):
        return True
    # Named document + year
    if re.search(r'(report|guide|spec|manual)\s+(\d{4}|v\d)', source_lower):
        return True
    # Person reference
    if re.search(r'(ask|contact|check with)\s+[A-Z][a-z]+', source):
        return True
    # File path
    if re.search(r'[\w-]+\.(pdf|docx?|xlsx?|csv|md)', source_lower):
        return True
    return False

VAGUE_PATTERNS = [r'^\s*(industry|various|multiple)\s+(reports?|sources?)\s*$', r'^\s*(research|data|information)\s*$', r'^\s*(internal|external)\s+sources?\s*$', r'^\s*(TBD|TODO|N/?A)\s*$']

def is_vague_source(source: str) -> bool:
    for pattern in VAGUE_PATTERNS:
        if re.match(pattern, source, re.IGNORECASE):
            return True
    return False
```

**Validation logic:**
```python
if claim_is_pending and (is_vague_source(source) or not is_actionable_source(source)):
    emit_warning('W-HC02', f'Non-actionable source: {source}')
```

**Limitations:** Heuristics are English-centric; may false-positive on unusual references.
```

---

### 3.4 Add §1.3.4 — Claim ID Formats

**Location:** After §1.3.3

```markdown
### 1.3.4 Claim ID Formats (Normative)

Claim IDs MUST match pattern: `claim-[a-z0-9-]+`

**Allowed formats:**

| Format | Example | Use Case |
|--------|---------|----------|
| Hash-based (preferred) | `claim-75fb137a` | Stable across edits |
| Sequential | `claim-001` | Simple, manual |
| Namespaced | `claim-pricing-1` | Human-readable |

**Hash computation (preferred):**
```python
import hashlib

def claim_id(text: str, location: str) -> str:
    # Normalize inputs
    text = ' '.join(text.strip().split())
    location = location.strip()

    payload = f"{text}|{location}"
    hash_hex = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    return f"claim-{hash_hex[:8]}"
```

**Validation:**
- E-HC03: Duplicate claim ID within document
- W-HC04: Non-hash claim ID (style warning)

**Collision note:** 8 hex chars = 16^8 = 4,294,967,296 combinations.

**Birthday Problem Analysis:**

For n claims sharing the same hash space H, collision probability approximates:

```
P(collision) ≈ 1 - e^(-n² / 2H)

For small P: P ≈ n² / 2H
```

| Claims (n) | P(collision) | Risk Level |
|------------|--------------|------------|
| 100 | ~0.0001% | Negligible |
| 500 | ~0.003% | Very Low |
| 1,000 | ~0.012% | Low |
| 5,000 | ~0.3% | Moderate |
| 10,000 | ~1.2% | Elevated |

**Calculation for n=1000:**
```
H = 2^32 = 4,294,967,296
n = 1000

P ≈ n² / 2H
P ≈ 1,000,000 / 8,589,934,592
P ≈ 0.000116
P ≈ 0.012%
```

**Recommendation:** For documents exceeding 1,000 claims, consider increasing hash prefix to 12 hex chars (collision P < 0.00001% at 10k claims).
```

---

### 3.5 Add §1.3.5 — Round Assignment Rules

**Location:** After §1.3.4

```markdown
### 1.3.5 Round Assignment Rules (Normative)

Claims are assigned to Round A or Round B based on verification requirements:

| Round | Criteria | Human Action | Example |
|-------|----------|--------------|--------|
| **A** | Source found AND human witnessed discovery | Confirm interpretation | Web search result human saw in session |
| **B** | Source not found OR human's own data OR conflicting sources | Verify truth | Benchmark data, pricing claims, statistics |

**Assignment Decision Tree:**

```
Was source found in THIS session?
    │
    ├─ YES ─→ Was human present/active during discovery?
    │              │
    │         ├─ YES ─→ ROUND A (Derived Data Confirmation)
    │         │
    │         └─ NO/UNCLEAR ─→ ROUND B (True HITL)
    │
    └─ NO ─→ Is this human's own data/experiment?
                   │
              ├─ YES ─→ ROUND B with note "your data"
              │
              └─ NO ─→ ROUND B with note "no source found"
```

**Default behavior:** When uncertain, assign to Round B (safer).

**Rationale:** Round A claims only need interpretation confirmation ("Did I read this right?"). Round B claims need truth verification ("Is this actually true?"). Separating them reduces checkbox fatigue and focuses human attention.
```

---

### 3.6 Add Validation Codes to §10

**Location:** §10 (Validation Error Codes)

```markdown
| Code | Severity | Description |
|------|----------|-------------|
| E-ST10 | Error | Missing `## HITL Verification Record` when `hitl-claims` non-empty |
| W-ST11 | Warning | HITL Record table rows don't match `hitl-claims` count |
| W-HC01 | Warning | Claim has `confirmed-by` but not `confirmed-date` (or vice versa) |
| W-HC02 | Warning | PENDING claim has non-actionable source |
| E-HC03 | Error | Duplicate claim ID within document |
| W-HC04 | Warning | Non-hash claim ID (style) |
| E-SC06 | Error | `hitl-pending-count` doesn't match actual pending claims |
```

---

### 3.7 Update Changelog §19

```markdown
### v2.1.0 (2026-01-XX)

**Added:**
- §1.2.1 Body Structure Requirements — HITL Verification Record section required
- §1.3.2 Claim Completion Status — presence/absence semantics
- §1.3.3 Source Field Semantics — actionable vs vague sources
- §1.3.4 Claim ID Formats — hash-based preferred, pattern defined
- §1.3.5 Round Assignment Rules — Round A vs Round B criteria
- Validation codes: E-ST10, W-ST11, W-HC01, W-HC02, E-HC03, W-HC04, E-SC06

**Clarified:**
- `round` field indicates tier, not completion status
- `hitl-pending-count` enforcement semantics
- Round A = interpretation confirmation, Round B = truth verification
```

---

## 4. SKILL.md Changes

### 4.1 Add Production Checklist Section

**Location:** After "CGD Output Format Template"

```markdown
## CGD Production Checklist

Before declaring a CGD complete, verify ALL of the following:

### Structural Completeness

| # | Check | Error If Missing |
|---|-------|------------------|
| 1 | YAML frontmatter with `---` delimiters | Parse failure |
| 2 | All required fields present | E-FM* |
| 3 | `hitl-claims` list present (may be `[]`) | E-FM* |
| 4 | `<!-- CLARITY_GATE_END -->` marker | E-ST* |
| 5 | `## HITL Verification Record` section (if claims exist) | E-ST10 |
| 6 | Status line after end marker matches frontmatter | E-SC05 |

### State Consistency

| Condition | Required |
|-----------|----------|
| `hitl-status: PENDING` | Some claims lack `confirmed-by` |
| `hitl-status: REVIEWED` | All claims have `confirmed-by` + `confirmed-date` |
| `hitl-pending-count: N` | Exactly N claims without `confirmed-by` |

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Invented `status` field | Spec uses presence/absence | Remove; check for `confirmed-*` fields |
| `round: B` read as "completed" | `round` = tier, not status | Check `confirmed-by` presence |
| Vague source | "industry reports" unverifiable | Add URL, doc name, or person |
| Missing HITL Record section | Only in examples | Add `## HITL Verification Record` |
```

---

### 4.2 Add Utility Usage Section

**Location:** After checklist

```markdown
## Utility Files

Reference implementations for hash computation:

**Compute document hash:**
```bash
python utils/document_hash.py path/to/file.cgd.md
# Output: af9c07dcc0025299a6bba9863e0ba3bb0989e2104df58309206b4b1d0121ff78
```

**Generate claim ID:**
```bash
python utils/claim_id.py "Base price is $99/mo" "api-pricing/1"
# Output: claim-75fb137a
```

**If utilities unavailable:** Use inline algorithm from FORMAT_SPEC §1.3.4 and §2.2.

### Workflow Patterns

**Pattern A: Embedded CGD** (source document gets frontmatter)
1. Add frontmatter with `document-sha256: "PENDING"`
2. Run `document_hash.py`, replace PENDING with output
3. Verify with `document_hash.py --verify`

**Pattern B: Separate CGD** (source is read-only)
1. Create `source.cgd.md`
2. Add frontmatter + HITL claims referencing source
3. Compute and insert hash

**When to use which:**
- Source editable AND can add YAML? → Pattern A
- Source read-only OR external? → Pattern B
```

---

### 4.3 Update SKILL.md Changelog

```markdown
### v2.1.0 (2026-01-XX)

**Added:**
- CGD Production Checklist (structural completeness, state consistency)
- Common errors table with fixes
- Utility file usage instructions
- Workflow patterns (embedded vs separate CGD)

**Clarified:**
- HITL claim completion semantics (presence/absence of `confirmed-*`)
- Source field dual semantics
```

---

## 5. Test Vectors

### 5.1 Claim Completion Status

**Input (PENDING):**
```yaml
hitl-claims:
  - id: claim-001
    text: "Price is $99"
    source: "Pricing page"
    location: "pricing/1"
    round: B
```
**Expected:** PENDING (no `confirmed-*` fields)

**Input (VERIFIED):**
```yaml
hitl-claims:
  - id: claim-001
    text: "Price is $99"
    source: "Pricing page"
    location: "pricing/1"
    round: B
    confirmed-by: Maria
    confirmed-date: 2026-01-12
```
**Expected:** VERIFIED

### 5.2 Malformed Claim (W-HC01)

**Input:**
```yaml
hitl-claims:
  - id: claim-001
    text: "Price is $99"
    source: "Pricing page"
    location: "pricing/1"
    round: B
    confirmed-by: Maria
    # Missing confirmed-date
```
**Expected:** W-HC01

### 5.3 Non-Actionable Source (W-HC02)

**Input (PENDING claim):**
```yaml
hitl-claims:
  - id: claim-001
    text: "Industry average is 80%"
    source: "industry reports"
    location: "benchmarks/1"
    round: B
```
**Expected:** W-HC02

### 5.4 Duplicate ID (E-HC03)

**Input:**
```yaml
hitl-claims:
  - id: claim-001
    text: "Price is $99"
    location: "a"
  - id: claim-001
    text: "Users: 1000"
    location: "b"
```
**Expected:** E-HC03

### 5.5 Claim ID Hash

**Input:**
```
text: "Base price is $99/mo"
location: "api-pricing/1"
```
**Expected:** `claim-75fb137a`

---

## 6. Backward Compatibility

| Aspect | Impact |
|--------|--------|
| Existing valid CGDs | Remain valid |
| Missing HITL Record section | Now E-ST10 (was implicit) |
| Vague sources | Now W-HC02 (was allowed) |
| Non-hash claim IDs | Now W-HC04 (style warning) |

**Summary:** Existing documents may show new warnings but remain valid. No migration required.

---

## 7. Alternatives Considered

### 7.1 Add Explicit `status` Field

```yaml
hitl-claims:
  - id: claim-001
    status: pending  # or "verified"
```

**Rejected:** Creates sync risk with `confirmed-*` fields. Presence/absence is single source of truth.

### 7.2 Split Source Into Two Fields

```yaml
source-instruction: "Where to look"
verified-source: "What was found"
```

**Rejected:** Over-engineers schema. Completion status (§1.3.2) already disambiguates.

### 7.3 Make HITL Record Optional

**Rejected:** Without body section, no human-readable audit trail.

---

## 8. Implementation Checklist

| Document | Changes |
|----------|---------|
| FORMAT_SPEC.md | Add §1.2.1, §1.3.2, §1.3.3, §1.3.4; update §10, §19 |
| SKILL.md | Add Production Checklist, Utility Usage sections |
| utils/claim_id.py | Create (reference implementation) |
| utils/document_hash.py | Create (reference implementation) |

---

## 9. Decision

- [x] APPROVED
- [ ] REJECTED: [reason]

**Reviewer:** Perplexity (adversarial review)
**Date:** 2026-01-27

---

## Appendix A: Utility Reference Implementations

### claim_id.py

```python
#!/usr/bin/env python3
"""Generate Clarity Gate claim IDs."""

import hashlib
import sys

def normalize(text: str) -> str:
    """Normalize text for hashing."""
    return ' '.join(text.strip().split())

def claim_id(text: str, location: str) -> str:
    """Generate claim ID from text and location."""
    payload = f"{normalize(text)}|{location.strip()}"
    hash_hex = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    return f"claim-{hash_hex[:8]}"

def test():
    """Run test vectors."""
    assert claim_id("Base price is $99/mo", "api-pricing/1") == "claim-75fb137a"
    print("✓ All tests passed")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        test()
    elif len(sys.argv) == 3:
        print(claim_id(sys.argv[1], sys.argv[2]))
    else:
        print("Usage: claim_id.py <text> <location>")
        print("       claim_id.py --test")
        sys.exit(1)
```

### document_hash.py

```python
#!/usr/bin/env python3
"""Compute Clarity Gate document hashes.

CRITICAL: Normalizes line endings for cross-platform consistency.
Same document on Windows (CRLF) and Unix (LF) produces identical hash.
"""

import hashlib
import re
import sys

def normalize_content(content: str) -> str:
    """Normalize for cross-platform consistency."""
    # Remove BOM if present
    if content.startswith('\ufeff'):
        content = content[1:]
    # Normalize line endings: CRLF to LF, CR to LF
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    return content

def compute_hash(filepath: str) -> str:
    """Compute SHA-256 excluding document-sha256 line."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Normalize for cross-platform consistency
    content = normalize_content(content)

    # Remove document-sha256 line for computation
    # Pattern: ^document-sha256:.*$ (entire line)
    content = re.sub(r'^document-sha256:.*$', '', content, flags=re.MULTILINE)

    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def verify(filepath: str) -> bool:
    """Verify document hash matches."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = normalize_content(content)

    # Extract stored hash from frontmatter
    match = re.search(r'^document-sha256:\s*["\']?([a-f0-9]{64})["\']?', content, re.MULTILINE)
    if not match:
        print("ERROR: No document-sha256 found")
        return False

    stored = match.group(1)
    computed = compute_hash(filepath)

    if stored == computed:
        print(f"OK: Hash verified: {computed}")
        return True
    else:
        print(f"FAIL: Hash mismatch")
        print(f"  Stored:   {stored}")
        print(f"  Computed: {computed}")
        return False

if __name__ == "__main__":
    if len(sys.argv) == 2:
        print(compute_hash(sys.argv[1]))
    elif len(sys.argv) == 3 and sys.argv[1] == "--verify":
        sys.exit(0 if verify(sys.argv[2]) else 1)
    else:
        print("Usage: document_hash.py <file>")
        print("       document_hash.py --verify <file>")
        sys.exit(1)
```

---

*RFC-001 — Merged from original RFC-001 (CGD Checklist) and RFC-002 (FORMAT_SPEC Clarifications)*
