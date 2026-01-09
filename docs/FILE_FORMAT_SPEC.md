# SOT and CGD File Format Specification

**Version:** 1.0  
**Date:** January 2026  
**Author:** Francesco Marinoni Moretto  
**License:** CC BY 4.0  
**Status:** Public Draft

---

## Abstract

This document specifies two complementary file formats for epistemically calibrated documentation in AI systems:

- **`.sot`** (Source of Truth) - Authoritative reference documents with explicit uncertainty calibration
- **`.cgd`** (Clarity-Gated Document) - Documents verified and annotated for safe LLM ingestion

Both formats address a critical gap in AI infrastructure: ensuring documents communicate appropriate confidence levels to both human readers and AI systems that process them.

---

## 1. Introduction

### 1.1 The Problem

Language models confidently process whatever context they receive. A document stating "Revenue will be $50M" as fact will be treated as fact, even when the author meant it as a projection. This creates downstream hallucinations that originate not from the model but from ambiguous input.

### 1.2 The Solution

Two file formats that make epistemic status explicit:

| Format | Purpose | When Created | Core Question |
|--------|---------|--------------|---------------|
| `.sot` | Authoritative reference | During authoring | "Does the reader have accurate confidence in each claim?" |
| `.cgd` | Verified for LLM ingestion | After verification | "Will an LLM mistake assumptions for facts?" |

### 1.3 Relationship

```
[Any Document] --> Clarity Gate Verification --> [.cgd file]
                          |
                          v
                   Source of Truth Creator --> [.sot file]
```

A `.sot` file that passes Clarity Gate becomes a `.cgd` file. A `.cgd` file that serves as an authoritative reference can be designated a `.sot` file. The formats are complementary, not mutually exclusive.

---

## 2. SOT Format Specification

### 2.1 Definition

A **Source of Truth** (`.sot`) file is a markdown document structured to communicate explicit confidence levels for all claims, enabling readers (human or AI) to calibrate their trust appropriately.

### 2.2 File Extension

- **Extension:** `.sot`
- **MIME Type:** `text/x-sot+markdown` (proposed)
- **Alternative:** `.sot.md` for systems requiring `.md` extension

### 2.3 Required Elements

#### 2.3.1 Header Block (REQUIRED)

```markdown
# [Topic] -- Source of Truth

**Last Updated:** YYYY-MM-DD  
**Owner:** [Name or Team]  
**Status:** VERIFIED (with noted exceptions) | DRAFT | UNVERIFIED  
**Version:** X.Y
```

**Rules:**
- Status MUST be qualified if any claims remain unverified
- Last Updated MUST reflect actual last modification date
- Owner MUST be identifiable (person, team, or system)

#### 2.3.2 Verification Status Table (REQUIRED)

```markdown
## Verification Status

| Category | Status | Confidence | Staleness Risk |
|----------|--------|------------|----------------|
| External claims (stable) | Verified against sources | High | STABLE |
| External claims (volatile) | Verified [date] | High | CHECK BEFORE CITING |
| Internal claims | Verified by owner | High | Low |
| Measurements | [Formal/Informal] | [High/Medium] | Low |
| Gap claims | Systematic search | Medium | Medium |
| Estimates | Marked as such | N/A | N/A |
| Self-assessments | Author judgment | N/A | N/A |
```

**Rules:**
- Every claim type in the document MUST appear in this table
- Confidence levels: High, Medium, Low, N/A
- Staleness markers: STABLE, CHECK BEFORE CITING, VOLATILE, SNAPSHOT

#### 2.3.3 Claim Separation (REQUIRED)

Verified data and unverified claims MUST be in separate sections:

```markdown
## Verified Data

| Claim | Value | Source | Verified | Staleness |
|-------|-------|--------|----------|-----------|
| [claim] | [value] | [source] | [date] | [marker] |

## Estimates (NOT VERIFIED)

| Claim | Value | Basis |
|-------|-------|-------|
| [claim] | ~[value] | [basis] |
```

### 2.4 Staleness Markers

| Marker | Meaning | Typical Shelf Life |
|--------|---------|-------------------|
| `[STABLE]` | Historical facts, published standards | Years |
| `[CHECK BEFORE CITING]` | Company info, product features | Months |
| `[VOLATILE]` | Pricing, API endpoints, URLs | Days to weeks |
| `[SNAPSHOT]` | Point-in-time only | Moment of capture |

### 2.5 Uncertainty Markers

Claims MUST use explicit uncertainty markers:

| Type | Markers |
|------|---------|
| Estimates | `~`, `(est.)`, `(estimated)`, `approximately` |
| Projections | `PROJECTED:`, `projected to`, `expected to` |
| Hypotheses | `HYPOTHESIS:`, `may`, `might`, `could` |
| Untested | `UNTESTED:`, `not validated`, `assumed` |
| Self-assessment | `(author judgment)`, `(self-assessed)` |

### 2.6 Anti-Patterns (MUST NOT)

1. **Verified Header Trap:** Status "VERIFIED" with unverified claims in body
2. **Internal Measurement Trap:** Informal measurements formatted like rigorous data
3. **Self-Assessment Trap:** Self-assigned scores in tables that look like external validation
4. **Absence-as-Proof Trap:** "No prior art found" marked as verified
5. **Illustrative-as-Data Trap:** Examples appearing in data tables
6. **Staleness Trap:** Old verification dates on volatile claims without warning

### 2.7 Minimal Valid SOT

```markdown
# [Topic] -- Source of Truth

**Last Updated:** 2026-01-09  
**Owner:** [Name]  
**Status:** VERIFIED (with noted exceptions)

## Verification Status

| Category | Status | Confidence |
|----------|--------|------------|
| External claims | Verified | High |
| Estimates | Marked | N/A |

## Verified Data

| Claim | Value | Source | Verified |
|-------|-------|--------|----------|
| Example | 100 | Internal test | 2026-01-09 |

## Estimates (NOT VERIFIED)

| Claim | Value | Basis |
|-------|-------|-------|
| Growth | ~20% | Author projection |
```

---

## 3. CGD Format Specification

### 3.1 Definition

A **Clarity-Gated Document** (`.cgd`) is a markdown document that has passed epistemic verification and contains inline annotations ensuring safe interpretation by LLMs.

### 3.2 File Extension

- **Extension:** `.cgd`
- **MIME Type:** `text/x-cgd+markdown` (proposed)
- **Alternative:** `.cgd.md` for systems requiring `.md` extension

### 3.3 Required Elements

#### 3.3.1 Verification Header (REQUIRED)

```markdown
---
clarity-gate-version: 1.6
verified-date: YYYY-MM-DD
verified-by: [human name or "automated"]
hitl-status: CONFIRMED | PENDING | PARTIAL
points-passed: [list of point numbers, e.g., 1,2,3,4,5,6,7,8,9]
---
```

**Rules:**
- `hitl-status` MUST be CONFIRMED for full PASS
- `verified-by` MUST identify the human verifier for HITL claims
- `points-passed` lists which of the 9 verification points passed

#### 3.3.2 Inline Annotations (AS NEEDED)

CGD files contain inline epistemic markers. Standard annotation patterns:

| Pattern | Meaning | Example |
|---------|---------|---------|
| `*(not specified)*` | Information gap | "Several researchers *(exact count not specified)* noted..." |
| `*(projected)*` | Future claim | "Revenue *(projected)* to reach $50M" |
| `*(estimated)*` | Approximate value | "Costs *(estimated)* $500/month" |
| `*(as of YYYY-MM-DD)*` | Time-bound claim | "CEO *(as of 2026-01-09)* is Jane Smith" |
| `*(unverified)*` | Requires fact-check | "Competitor offers X *(unverified)*" |
| `*(author assessment)*` | Subjective judgment | "Quality score: 8/10 *(author assessment)*" |
| `[assuming X]` | Hidden assumption made explicit | "Scales linearly [assuming <1000 users]" |

#### 3.3.3 Verification Summary (REQUIRED at end)

```markdown
---

## Clarity Gate Verification

**Verified:** YYYY-MM-DD  
**Version:** 1.6  
**HITL Status:** CONFIRMED by [Name]

### Points Checked

| Point | Status |
|-------|--------|
| 1. Hypothesis vs Fact | PASS |
| 2. Uncertainty Markers | PASS |
| 3. Assumption Visibility | PASS |
| 4. Authoritative-Looking Data | PASS |
| 5. Data Consistency | PASS |
| 6. Implicit Causation | PASS |
| 7. Future as Present | PASS |
| 8. Temporal Coherence | PASS |
| 9. Externally Verifiable | PASS |

### HITL Confirmations

| Claim | Confirmed By | Date |
|-------|--------------|------|
| [claim requiring human verification] | [Name] | [Date] |
```

### 3.4 Annotation Density Guidance

| Document Type | Annotation Density | Rationale |
|---------------|-------------------|-----------|
| Technical spec | High | Precision critical |
| Research summary | Medium | Balance readability |
| General reference | Low | Only ambiguous claims |
| Creative content | None | Not intended for CGD |

### 3.5 Transformation Rules

When converting a document to CGD format:

1. **Vague quantifiers** become explicit gaps:
   - "Several" → "Several *(exact count not specified)*"
   - "Many" → "Many *(quantity undefined)*"
   - "Most" → "Most *(>50% assumed, not measured)*"

2. **Projections** get uncertainty markers:
   - "will be" → "*(projected to be)*"
   - "will reduce" → "*(expected to reduce)*"

3. **Assumptions** become visible:
   - "scales linearly" → "scales linearly [assuming ideal conditions]"

4. **Time-sensitive claims** get dates:
   - "currently" → "*(as of YYYY-MM-DD)*"
   - "the CEO is" → "*(as of YYYY-MM-DD)* the CEO is"

5. **Specific numbers** get sourcing or uncertainty:
   - "$50M revenue" → "$50M revenue *(source: Q3 report)*" OR "~$50M revenue *(estimated)*"

### 3.6 Minimal Valid CGD

```markdown
---
clarity-gate-version: 1.6
verified-date: 2026-01-09
verified-by: Francesco Marinoni
hitl-status: CONFIRMED
points-passed: 1,2,3,4,5,6,7,8,9
---

# Project Status

The project *(as of 2026-01-09)* has approximately *(estimated)* 500 users.

Revenue is *(projected)* to reach $1M by Q4 [assuming current growth rate continues].

---

## Clarity Gate Verification

**Verified:** 2026-01-09  
**Version:** 1.6  
**HITL Status:** CONFIRMED by Francesco Marinoni

| Point | Status |
|-------|--------|
| 1-9 | PASS |
```

---

## 4. Ecosystem Integration

### 4.1 Tool Chain

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Source of      │     │  Clarity Gate   │     │  RAG System     │
│  Truth Creator  │────▶│  Verification   │────▶│  Ingestion      │
│  (.sot output)  │     │  (.cgd output)  │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 4.2 Conversion

| From | To | Process |
|------|-----|---------|
| `.md` | `.sot` | Apply Source of Truth Creator skill |
| `.md` | `.cgd` | Run Clarity Gate, apply annotations |
| `.sot` | `.cgd` | Run Clarity Gate (often passes with minimal changes) |
| `.cgd` | `.sot` | Add verification status table if serving as authoritative reference |

### 4.3 Validation

A valid `.sot` file:
- [ ] Has required header block
- [ ] Has verification status table
- [ ] Separates verified from unverified claims
- [ ] Uses staleness markers on volatile claims
- [ ] Uses uncertainty markers on estimates

A valid `.cgd` file:
- [ ] Has YAML frontmatter with verification metadata
- [ ] Has inline annotations for all ambiguous claims
- [ ] Has verification summary at end
- [ ] HITL status is CONFIRMED (or explicitly PENDING with reason)

---

## 5. Implementation Notes

### 5.1 File Detection

```python
def detect_format(filepath):
    if filepath.endswith('.sot') or filepath.endswith('.sot.md'):
        return 'sot'
    if filepath.endswith('.cgd') or filepath.endswith('.cgd.md'):
        return 'cgd'
    
    # Content-based detection
    content = read_file(filepath)
    if '-- Source of Truth' in content and '## Verification Status' in content:
        return 'sot'
    if 'clarity-gate-version:' in content:
        return 'cgd'
    
    return 'unknown'
```

### 5.2 Syntax Highlighting

Both formats are markdown-based. Editors can provide enhanced highlighting for:
- Uncertainty markers: `*(text)*`
- Assumption blocks: `[assuming X]`
- Staleness markers: `[STABLE]`, `[VOLATILE]`, etc.
- YAML frontmatter (CGD)

### 5.3 Linting Rules

**SOT Linter:**
1. WARN if "VERIFIED" status without verification table
2. ERROR if estimates in "Verified Data" section
3. WARN if volatile claims lack staleness marker
4. ERROR if Last Updated > current date

**CGD Linter:**
1. ERROR if missing YAML frontmatter
2. WARN if hitl-status != CONFIRMED
3. ERROR if verified-date > current date
4. WARN if document contains "will be" without uncertainty marker

---

## 6. Namespace Claim

### 6.1 Prior Art

| Extension | Existing Uses | Conflict Risk |
|-----------|---------------|---------------|
| `.sot` | CET Designer (active), Tekla Structures (active), ImageMagick, Adventure SOS (obsolete) | Low - different domains |
| `.cgd` | CricketGraph (1996, obsolete), Boeing fluid mechanics (niche) | Near zero |

### 6.2 Differentiation

This specification claims `.sot` and `.cgd` for **epistemically calibrated markdown documents** in the AI/ML and knowledge management domain. The existing uses are:
- Binary formats (CET Designer, Tekla, Boeing)
- Obsolete software (CricketGraph 1996, Adventure SOS)
- Completely different domains (interior design, construction, fluid dynamics)

No namespace conflict exists for plaintext/markdown semantic documents.

---

## 7. References

- [Clarity Gate](https://github.com/frmoretto/clarity-gate) - Verification system
- [Source of Truth Creator](https://github.com/frmoretto/source-of-truth-creator) - Document creation skill
- [Stream Coding](https://github.com/frmoretto/stream-coding) - Parent methodology

---

## 8. Changelog

### v1.0 (2026-01-09)
- Initial public specification
- SOT format defined with 6 anti-patterns
- CGD format defined with 9-point verification
- Namespace claim documented

---

## Document Metadata

| Field | Value |
|-------|-------|
| Specification | SOT and CGD File Formats |
| Version | 1.0 |
| Date | January 2026 |
| Author | Francesco Marinoni Moretto |
| License | CC BY 4.0 |
| Canonical URL | github.com/frmoretto/clarity-gate/docs/FILE_FORMAT_SPEC.md |

---

*End of specification*
