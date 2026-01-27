# RFC-002: RAG Chunk Context Advisory

**RFC ID:** RFC-002  
**Title:** RAG Chunk Context Advisory  
**Type:** Normative  
**Status:** APPROVED  
**Created:** 2026-01-24  
**Updated:** 2026-01-26  
**Author:** Francesco Marinoni Moretto  
**Affects:** Clarity Gate v2.1.0 → v2.2.0  
**Supersedes:** Original RFC-003 (renumbered per RFC-000)

---

## 1. Problem Statement

### 1.1 The Gap

Clarity Gate's 9 Verification Points verify epistemic quality — whether claims are properly hedged, sourced, and consistent. However, RAG systems chunk documents before ingestion, and individual chunks may be retrieved in isolation.

**Current scope:** Epistemic quality (Points 1-9)  
**Missing:** Structural assessment for chunk retrieval

### 1.2 Failure Modes

A document can pass all 9 points and still produce incorrect LLM outputs when chunked:

| Failure Mode | Example | Consequence |
|--------------|---------|-------------|
| **Orphan Reference** | Section says "See §3.2 for threshold" | Retrieved chunk contains no value |
| **Context Loss** | Glossary defines "Engagement" but term used in §5 without definition | §5 chunk has undefined term |
| **Assumption Scope Loss** | "All targets assume 300 users" in §1, targets in §4 | §4 chunk has targets without context |

### 1.3 The Tension

**Human-readable documents** benefit from:
- Cross-references instead of repetition
- Central definition sections (glossary, parameter tables)
- "See §X.Y" for rationale

**RAG-chunked retrieval** requires:
- Self-contained sections
- Values at point-of-use
- Context carried forward

These goals conflict. Optimizing for human reading breaks chunk retrieval. Optimizing for chunks bloats documents significantly (see §2.3).

### 1.4 Origin of Discovery

Identified during adversarial review of N1AI Platform OS Architecture v0.5.7 (January 2026). External reviewer (Perplexity) recommended "see §X.Y" patterns that would break RAG retrieval.

---

## 2. Design Decision

### 2.1 Clarity Gate's Role: Detect, Don't Fix

Clarity Gate's mission is **epistemic quality verification**, not structural transformation.

| In Scope | Out of Scope |
|----------|--------------|
| Detect chunk-unsafe structures | Mandate document bloat |
| Signal to downstream systems | Prescribe how to fix |
| Compute advisory field | Enforce structural patterns |

**Principle:** Clarity Gate advises; RAG pipeline acts.

### 2.2 Solution: Advisory Field

Add a computed field that signals whether chunk-time context enrichment is advisable:

```yaml
chunk-context: advisable | optional
```

| Value | Meaning |
|-------|---------|
| `advisable` | Document has orphan references or central definitions; RAG pipeline should prepend context when chunking |
| `optional` | Document is self-contained; direct chunking is safe |

**This is informational, not blocking.** Documents with `chunk-context: advisable` can still be `rag-ingestable: true`.

### 2.3 Why Not Mandate Fixes?

Empirical analysis of four documents (January 2026) measured actual orphan reference ratios and bloat required to achieve chunk safety:

| Document Type | Lines | Total Refs | Orphan Refs | Orphan Ratio | Bloat to Fix |
|---------------|-------|------------|-------------|--------------|--------------|
| API Reference *(test doc)* | 384 | 77 | 77 | 100.0% | 46.1% |
| Config Guide *(test doc)* | 328 | 101 | 98 | 97.0% | 59.2% |
| Legal Contract *(test doc)* | 344 | 58 | 58 | 100.0% | 21.2% |
| N1AI Architecture *(real)* | 1650 | 14 | 7 | 50.0% | 0.4% |

**Methodology:** Test documents (~200 lines each) were created to represent typical reference-heavy structures. Orphan references detected via regex pattern `see §X.Y` without co-located numeric value. Bloat estimated at 40 characters per fix.

**Test documents location:** `clarity-gate-meta/RFC/test-docs/` (3 files: example_api_reference.md, example_config_guide.md, example_legal_contract.md)

**Key findings:**
- Reference-heavy documents (API, Config, Legal) have **97-100% orphan ratios** by design
- Fixing them would bloat documents **21-59%**
- Strategic/narrative documents (N1AI) are already mostly chunk-safe with **<1% bloat**

**Conclusion:** Mandating inline values would bloat reference-heavy documents unacceptably. Better to solve at ingestion time.

---

## 3. Format Specification Changes

### 3.1 New Frontmatter Fields

Add to CLARITY_GATE_FORMAT_SPEC.md §1.3 (YAML Schema):

```yaml
# === CHUNK CONTEXT ADVISORY (computed, informational) ===
chunk-context: advisable | optional          # Computed
chunk-context-sections:                       # Present if advisable
  - "## 1.7 Glossary"
  - "## 8. Platform Parameters"
```

### 3.2 Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chunk-context` | enum | Computed | Advisory for RAG pipeline |
| `chunk-context-sections` | list | If advisable | Sections to prepend as context |

### 3.3 Computation Rules

```python
def compute_chunk_context(document):
    orphan_refs = count_orphan_references(document)
    total_refs = count_all_references(document)
    central_sections = detect_central_definition_sections(document)
    
    orphan_ratio = orphan_refs / total_refs if total_refs > 0 else 0
    
    if orphan_ratio > 0.10 or len(central_sections) > 0:
        return {
            'chunk-context': 'advisable',
            'chunk-context-sections': central_sections
        }
    else:
        return {
            'chunk-context': 'optional'
        }
```

**Detection heuristics:**

| Pattern | Detection |
|---------|-----------|
| Orphan reference | `see §X.Y` without value in same sentence |
| Central section | Section referenced by 5+ other sections |
| Glossary | Section named "Glossary", "Definitions", "Terms" |
| Parameter table | Section with tables referenced elsewhere |

**Threshold rationale:** 10% orphan ratio chosen as initial trigger. Central section threshold of 5+ references based on observed patterns in test documents. These are starting values; adjust based on retrieval quality data.

### 3.4 New Validation Rules

| Code | Rule | Severity |
|------|------|----------|
| W-CC01 | `chunk-context: advisable` but `chunk-context-sections` is empty | WARNING |
| W-CC02 | High orphan reference ratio (>30%) detected | WARNING |

**Note:** These are WARNINGS, not ERRORS. Documents are not rejected.

**Threshold rationale:** 30% warning threshold chosen to flag documents where majority of references lack inline values. No empirical basis; adjust after observing retrieval degradation patterns.

---

## 4. Interaction with Existing Fields

### 4.1 Independence from rag-ingestable

| `rag-ingestable` | `chunk-context` | Meaning |
|------------------|-----------------|---------|
| `true` | `optional` | Epistemically sound, chunk directly |
| `true` | `advisable` | Epistemically sound, prepend context when chunking |
| `false` | `optional` | Has epistemic issues, don't ingest |
| `false` | `advisable` | Has epistemic issues AND chunk issues |

**Key:** `chunk-context` is orthogonal to `rag-ingestable`. Both can be any combination.

### 4.2 No Interaction with Points 1-9

Point 10 is NOT added. The 9 points remain focused on epistemic quality. Chunk context is a separate computed advisory, not a verification point.

---

## 5. RAG Pipeline Guidance

### 5.1 Recommended Handling

When ingesting a document with `chunk-context: advisable`:

1. **Extract context sections** listed in `chunk-context-sections`
2. **For each chunk**, prepend relevant context as header:

```markdown
[CONTEXT]
## 1.7 Glossary (excerpt)
- **Engagement**: A contracted placement of an associate with a client
- **Rating Tier**: Categorical status (Platinum/Gold/Silver/Bronze/Blue)

## 8. Platform Parameters (excerpt)  
- Profile completeness threshold: 80%
- Default shortlist size: 5 candidates
[/CONTEXT]

## 3.5 Matching Engine
...actual chunk content...
```

3. **Embed with context** — The context becomes part of the chunk for embedding

### 5.2 Alternative Strategies

RAG pipelines may use other approaches:

| Strategy | Description |
|----------|-------------|
| Context prepending | Add context header to each chunk (recommended) |
| Parent-child retrieval | Retrieve chunk + parent section together |
| Whole-document fallback | For `advisable` docs, embed as single chunk |
| Ignore advisory | Accept degraded retrieval quality |

Clarity Gate does not prescribe which strategy. It signals; pipeline decides.

---

## 6. Examples

### 6.1 Document with optional Chunk Context

```yaml
---
clarity-gate-version: 2.1
processed-date: 2026-01-24
clarity-status: CLEAR
hitl-status: REVIEWED
rag-ingestable: true
chunk-context: optional
document-sha256: abc123...
---

# Simple Document

## Overview
This section is self-contained. All values are inline.
The threshold is 80% for profile completeness.

## Details  
Another self-contained section. No cross-references.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 6.2 Document with advisable Chunk Context

```yaml
---
clarity-gate-version: 2.1
processed-date: 2026-01-24
clarity-status: CLEAR
hitl-status: REVIEWED
rag-ingestable: true
chunk-context: advisable
chunk-context-sections:
  - "## 1.7 Glossary"
  - "## 8. Platform Parameters"
document-sha256: def456...
---

# Complex Document

## 1.7 Glossary
| Term | Definition |
|------|------------|
| Engagement | A contracted placement |
| Rating Tier | Categorical status |

## 8. Platform Parameters
| Parameter | Value |
|-----------|-------|
| Profile threshold | 80% |
| Shortlist size | 5 |

## 3.5 Matching Engine
When an Engagement reaches COMPLETING state (see §1.7), 
the threshold from §8 applies...

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

**Signal to pipeline:** Chunks from §3.5 need context from §1.7 and §8 prepended.

---

## 7. Implementation Notes

### 7.1 For Clarity Gate Validators

1. **Compute `chunk-context`** during processing
2. **Detect central sections** by reference counting
3. **Emit warnings** for high orphan ratios (W-CC02)
4. **Do NOT fail** documents based on chunk context

### 7.2 For Document Authors

No action required. Authors may optionally:
- Structure documents to be self-contained (results in `optional`)
- Accept `advisable` and let pipeline handle context

### 7.3 For RAG Pipeline Operators

1. **Read `chunk-context` field** before chunking
2. **If `advisable`**, implement context prepending
3. **Monitor retrieval quality** and adjust strategy

---

## 8. Backward Compatibility

### 8.1 Existing Documents

- Documents without `chunk-context` are treated as `optional` (conservative default)
- No existing CGD files are invalidated
- Field is computed on next processing

### 8.2 Spec Version

- Clarity Gate v2.1.0 → v2.2.0
- FORMAT_SPEC v2.1.0 → v2.2.0 (adds `chunk-context` fields, W-CC* warnings)

---

## 9. Decision Summary

| Aspect | Decision |
|--------|----------|
| Scope | Advisory field, not verification point |
| Field name | `chunk-context: advisable \| optional` |
| Blocking? | No — informational only |
| Fix responsibility | RAG pipeline, not document author |
| Bloat required? | No — context added at ingestion time |

---

## 10. Decision Requested

**Approve RFC-002 to:**
1. Add `chunk-context` computed field to CGD frontmatter
2. Add `chunk-context-sections` list for context identification
3. Add W-CC01, W-CC02 warnings to FORMAT_SPEC
4. Document RAG pipeline guidance
5. Update spec version to v2.1

---

## Appendix A: Detection Heuristics

**Heuristic Limitations (IMPORTANT):**
- Detects English "see §X.Y" patterns only
- Misses: "refer to §", "as defined in §", "per §", parenthetical "(§X.Y)"
- Non-English documents will always return `chunk-context: optional`
- For documents with different reference patterns, consider author-declared override
- These heuristics are starting points; adjust based on retrieval quality data

```python
import re

def count_orphan_references(document):
    """Count 'see §X.Y' patterns without co-located value."""
    orphan = 0
    for match in re.finditer(r'[Ss]ee\s+(§[\d\.]+)', document):
        start = max(0, match.start() - 80)
        end = min(len(document), match.end() + 40)
        context = document[start:end]
        has_value = bool(re.search(
            r'\d+[%]|\d+\s*(?:hours?|days?|months?|GB|MB|cores?|seconds?|years?)',
            context
        ))
        if not has_value:
            orphan += 1
    return orphan

def detect_central_definition_sections(document):
    """Find sections that other sections reference."""
    sections = extract_h2_sections(document)
    ref_counts = {}
    
    for section in sections:
        refs = re.findall(r'§([\d\.]+)', section.content)
        for ref in refs:
            ref_counts[ref] = ref_counts.get(ref, 0) + 1
    
    central = []
    for section in sections:
        if ref_counts.get(section.number, 0) >= 5:
            central.append(section.header)
        if re.search(r'[Gg]lossary|[Dd]efinitions|[Tt]erms|[Pp]arameters', section.header):
            central.append(section.header)
    
    return list(set(central))
```

---

## Appendix B: Test Documents

Three test documents were created to validate bloat estimates (January 2026):

| Document | Purpose | Location |
|----------|---------|----------|
| `example_api_reference.md` | Heavy schema references (§6.x, §7.x) | clarity-gate-meta/RFC/test-docs/ |
| `example_config_guide.md` | Central parameter table (§8.x) | clarity-gate-meta/RFC/test-docs/ |
| `example_legal_contract.md` | Definitions section (§1.x) | clarity-gate-meta/RFC/test-docs/ |

These documents are intentionally designed to represent worst-case reference patterns.

---

## Appendix C: Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-01-24 | Initial draft (Point 10 as mandatory verification) |
| 0.2.0 | 2026-01-24 | Rewrite: Advisory field instead of verification point |
| 0.3.0 | 2026-01-24 | Updated with empirical data from test documents; added threshold rationales; added test document appendix |

---

## Decision

- [x] APPROVED
- [ ] REJECTED: [reason]

**Reviewer:** Perplexity (adversarial review)  
**Date:** 2026-01-27

---

*RFC-002 (formerly RFC-003) drafted in response to N1AI Platform OS Architecture adversarial review (January 2026). Revised after empirical analysis showed 21-59% document bloat for reference-heavy document types. Renumbered per RFC-000.*
