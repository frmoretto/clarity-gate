# Clarity Gate Architecture

**Version:** 2.1
**Last Updated:** 2026-01-27

---

## Overview

Clarity Gate is a pre-ingestion verification system for epistemic quality. This document details the verification architecture, including the 9-point checklist and tiered verification hierarchy.

---

## The 9 Verification Points

### Epistemic Checks (Core Focus)

These four checks address the primary mission: ensuring claims are properly qualified.

#### 1. Hypothesis vs. Fact Labeling

**Question:** Is this claim marked as validated or hypothetical?

| Fails | Passes |
|-------|--------|
| "Our architecture outperforms competitors" | "Our architecture outperforms competitors [benchmark data in Table 3]" |
| "The model achieves 40% improvement" | "The model achieves 40% improvement [measured on dataset X]" |
| "Users prefer this approach" | "Users prefer this approach [n=50 survey, p<0.05]" |

**Why it matters:** Ungrounded assertions look like facts to downstream systems.

---

#### 2. Uncertainty Marker Enforcement

**Question:** Do forward-looking statements have appropriate qualifiers?

| Fails | Passes |
|-------|--------|
| "Revenue will be $50M by Q4" | "Revenue is **projected** to be $50M by Q4" |
| "The feature will reduce churn" | "The feature is **expected** to reduce churn" |
| "We will achieve product-market fit" | "We **aim** to achieve product-market fit" |

**Keywords to enforce:** projected, expected, estimated, anticipated, planned, aimed, targeted

**Why it matters:** Future states stated as present facts become "verified" hallucinations.

---

#### 3. Assumption Visibility

**Question:** Are implicit assumptions made explicit?

| Fails | Passes |
|-------|--------|
| "The system scales linearly" | "The system scales linearly [assuming <1000 concurrent users]" |
| "Response time is 50ms" | "Response time is 50ms [under standard load conditions]" |
| "Cost per user is $0.02" | "Cost per user is $0.02 [at current AWS pricing, us-east-1]" |

**Why it matters:** Hidden assumptions break when conditions change.

---

#### 4. Authoritative-Looking Unvalidated Data

**Question:** Do tables/charts with specific numbers have validation sources?

| Red Flags | Resolution |
|-----------|------------|
| Table with percentages, no source | Add [source] or mark [PROJECTED] |
| Chart with trend lines, no methodology | Add methodology note |
| Comparison matrix with checkmarks | Clarify if measured or claimed |

**Why it matters:** Formatted data triggers authority heuristics. Tables "look" more credible than prose.

---

### Data Quality Checks (Complementary)

These three checks support epistemic quality by catching data issues.

#### 5. Data Consistency

**Question:** Are there conflicting numbers, dates, or facts within the document?

| Check Type | Example Discrepancy |
|------------|---------------------|
| Figure vs. Text | Figure shows beta=0.33, text claims beta=0.73 |
| Abstract vs. Body | Abstract claims "40% improvement," body shows 28% |
| Table vs. Prose | Table lists 5 features, text references 7 |
| Repeated values | Revenue stated as $47M in one section, $49M in another |

**Why it matters:** Internal contradictions indicate unreliable content.

---

#### 6. Implicit Causation

**Question:** Does the claim imply causation without evidence?

| Fails | Passes |
|-------|--------|
| "Feature X increased retention" | "Feature X **correlated with** increased retention" |
| "The change reduced errors" | "Errors decreased **after** the change [causal link not established]" |
| "Training improved performance" | "Performance improved **following** training [controlled study pending]" |

**Why it matters:** Correlation stated as causation misleads decision-making.

---

#### 7. Future State as Present

**Question:** Are planned outcomes described as if already achieved?

| Fails | Passes |
|-------|--------|
| "The system handles 10K requests/second" | "The system **is designed to** handle 10K requests/second" |
| "We have enterprise customers" | "We **are targeting** enterprise customers" |
| "The API supports GraphQL" | "The API **will support** GraphQL [Q2 roadmap]" |

**Why it matters:** Aspirations presented as reality create false expectations.

---

### Verification Routing (Points 8-9)

These two checks improve detection and routing for claims that need external verification.

#### 8. Temporal Coherence

**Question:** Are dates coherent with each other and with the present?

| Fails | Passes |
|-------|--------|
| "Last Updated: December 2024" (current date is December 2025) | "Last Updated: December 2025" |
| v1.0.0 dated 2024-12-23, v1.1.0 dated 2024-12-20 (out of order) | Versions in chronological order |
| "Deployed in Q3 2025" in a doc from Q1 2025 | "PLANNED: Q3 2025" |
| "Current CEO is X" (when X left 2 years ago) | "As of Dec 2025, CEO is Y" |

**Sub-checks:**
1. **Document date vs current date**: Is "Last Updated" in the future or suspiciously stale (>6 months)?
2. **Internal chronology**: Are version numbers, event dates in logical sequence?
3. **Reference freshness**: Do "current", "now", "today" claims need staleness markers?

**Why it matters:** A document claiming "December 2024" when consumed in December 2025 misleads any LLM that ingests it about temporal context.

**Scope boundaries:**
- ✅ IN: Wrong years, chronological inconsistencies, stale markers
- ❌ OUT: Judging if timelines are "reasonable" (subjective), verifying events happened on stated dates (HITL)

---

#### 9. Externally Verifiable Claims

**Question:** Does the document contain specific claims that could be fact-checked but aren't sourced?

| Type | Example | Risk |
|------|---------|------|
| Pricing | "Costs ~$0.005 per call" | API pricing changes; may be outdated or wrong |
| Statistics | "Papers average 15-30 equations" | Sounds plausible but may be wildly off |
| Rates/ratios | "40% of researchers use X" | Specific % needs citation |
| Competitor claims | "No competitor offers Y" | May be outdated or incorrect |
| Industry facts | "The standard is X" | Standards evolve |

**Why it matters:** These claims are dangerous because they:
1. Look authoritative (specific numbers)
2. Sound plausible (common-sense estimates)
3. Are verifiable (unlike opinions)
4. Are often wrong (pricing changes, statistics misremembered)

**Fix options:**
1. Add source: "~$0.005 (Gemini pricing, Dec 2025)"
2. Add uncertainty: "~$0.005 (estimated, verify current pricing)"
3. Route to verification: Flag for HITL or external search
4. Generalize: "low cost per call" instead of specific number

**Why it matters:** An LLM ingesting "costs ~$0.005" will confidently repeat this—even if actual cost is 10x different. This is a "confident plausible falsehood."

---

## Verification Hierarchy

```
Claim Extracted --> Does Source of Truth Exist?
                           |
           +---------------+---------------+
           YES                             NO
           |                               |
     Tier 1: Automated              Tier 2: HITL
     Verification                   (Last Resort)
           |                               |
     +-----+-----+                   Human reviews:
     |           |                   - Add markers
   Tier 1A    Tier 1B               - Provide source
   Internal   External              - Reject claim
           |           |                   |
     PASS/BLOCK   PASS/BLOCK        APPROVE/REJECT
```

---

## Tier 1A: Internal Consistency (Ready Now)

Checks for contradictions *within* a document. No external systems required.

### Capabilities

| Check | Description | Status |
|-------|-------------|--------|
| Figure vs. Text | Cross-reference numerical claims | Ready |
| Abstract vs. Body | Verify summary matches content | Ready |
| Table vs. Prose | Ensure counts/lists are consistent | Ready |
| Duplicate values | Flag conflicting repeated claims | Ready |

### Implementation

The Claude skill implementation handles Tier 1A checks through:
1. Extracting claims from document
2. Cross-referencing numerical values
3. Flagging discrepancies with specific locations

### Example Output

```yaml
check: internal_consistency
status: DISCREPANCY_FOUND

findings:
  - type: figure_vs_text
    figure_location: Figure 3, panel B
    figure_value: "beta = 1/3 = 0.33"
    text_location: Section 4.2, paragraph 3
    text_value: "beta = 11/15 = 0.73"
    delta: 0.40
    severity: HIGH

action: BLOCK - Resolve discrepancy before ingestion
```

---

## Tier 1B: External Verification (Extension Interface)

For claims verifiable against structured sources. **Users implement connectors.**

### Interface Design

```python
class VerificationConnector:
    """Base class for external verification."""
    
    def can_verify(self, claim: Claim) -> bool:
        """Returns True if this connector can verify the claim type."""
        pass
    
    def verify(self, claim: Claim) -> VerificationResult:
        """Verifies claim against external source."""
        pass
```

### Example Connectors (User-Implemented)

| Claim Type | Source | Connector |
|------------|--------|-----------|
| "Q3 revenue was $47M" | Financial system | `FinancialDataConnector` |
| "Feature deployed Oct 15" | Git commits | `GitHistoryConnector` |
| "Customer count is 1,247" | CRM | `CRMConnector` |
| "API latency is 50ms" | Monitoring | `MetricsConnector` |

### Honest Limitation

External verification requires bespoke integration for each data source. This is **not out-of-the-box functionality**. Clarity Gate provides the interface; users provide implementations.

---

## Tier 2: Two-Round HITL Verification (v1.6)

When automated verification cannot resolve a claim, it routes to human review.

### The Value Proposition

The value isn't having humans review data -- every team does that.

The value is **intelligent routing**: the system detects *which specific claims* need human review, AND *what kind of review* each needs.

### Why Two Rounds?

Different claims need different types of verification:

| Claim Type | What Human Checks | Cognitive Load |
|------------|-------------------|----------------|
| LLM found source, human witnessed | "Did I interpret correctly?" | Low (quick scan) |
| Human's own data | "Is this actually true?" | High (real verification) |
| No source found | "Is this actually true?" | High (real verification) |

Mixing these in one table creates checkbox fatigue—human rubber-stamps everything instead of focusing attention where it matters.

### Round A: Derived Data Confirmation

Claims where LLM found a source AND human was present in the session.

**Purpose:** Confirm interpretation, not truth. Human already saw the source.

**Format:** Simple list (lighter visual weight for quick scan)

```
## Derived Data Confirmation

These claims came from sources found in this session:

- o3 prices cut 80% June 2025 (OpenAI blog)
- Opus 4.5 is $5/$25 (Anthropic pricing page)

Reply "confirmed" or flag any I misread.
```

### Round B: True HITL Verification

Claims where:
- No source was found
- Source is human's own data/experiment
- LLM is extrapolating or inferring
- Conflicting sources found

**Purpose:** Verify truth. Human may NOT have seen this or it may not exist.

**Format:** Full table with True/False confirmation

```
## HITL Verification Required

| # | Claim | Why HITL Needed | Human Confirms |
|---|-------|-----------------|----------------|
| 1 | Benchmark scores (100%, 75%→100%) | Your experiment data | [ ] True / [ ] False |
```

### Classification Logic

```
Claim Extracted
      │
      ▼
Was source found in THIS session?
      │
      ├─── YES ────► Was human present/active?
      │                    │
      │              ├─ YES ──► ROUND A (Derived)
      │              │
      │              └─ NO/UNCLEAR ──► ROUND B (True HITL)
      │
      └─── NO ─────► Is this human's own data?
                           │
                     ├─ YES ──► ROUND B with note "your data"
                     │
                     └─ NO ──► ROUND B with note "no source found"
```

**Default behavior:** When uncertain, assign to Round B.

### Efficiency Example

*A 50-claim document might have 48 pass automated checks, with the remaining 2 split between Round A (quick confirmation) and Round B (real verification). Human attention is focused on claims that actually need it. (Illustrative example, not measured.)*

### Human Review Options

When a claim is routed to Round B, the human must:

1. **Provide Source of Truth** -- Point to authoritative source that was missed
2. **Add Epistemic Markers** -- Mark as [PROJECTION], [HYPOTHESIS], [UNVERIFIED]
3. **Reject Claim** -- Remove or rewrite the claim entirely

### HITL Protocol

```yaml
claim: "Our system achieves 99.9% uptime"
automated_result: CANNOT_VERIFY
reason: No source of truth for uptime metrics
round: B

human_action_required:
  options:
    - provide_source: "Link to monitoring dashboard or SLA report"
    - add_marker: "Mark as [TARGET] or [PROJECTED]"
    - reject: "Remove claim or rewrite with evidence"
  
  deadline: Before document enters knowledge base
```

---

## Output Format

### Summary Block

```yaml
verification_result:
  status: PASS | FAIL | NEEDS_REVIEW
  document: "[filename]"
  timestamp: "[ISO-8601]"
  
  summary:
    total_claims: [n]
    passed: [n]
    failed: [n]
    needs_review: [n]
```

### Detailed Findings

```yaml
findings:
  - id: 1
    claim: "[exact text]"
    location: "[section/paragraph]"
    check: "[which of 9 checks]"
    result: PASS | FAIL | NEEDS_REVIEW
    severity: CRITICAL | WARNING | TEMPORAL | VERIFIABLE
    reason: "[explanation]"
    suggested_fix: "[how to resolve]"
```

### Severity Levels

| Level | Description | Example |
|-------|-------------|---------|
| CRITICAL | Will cause hallucination | Projection stated as fact |
| WARNING | Could cause equivocation | Missing assumption markers |
| TEMPORAL | Date/time inconsistency | "Last Updated: December 2024" when current is 2025 |
| VERIFIABLE | Specific claim needing fact-check | "Costs ~$0.005 per call" without source |

### Externally Verifiable Claims

```yaml
verifiable_claims:
  - id: 1
    claim: "[exact text]"
    type: PRICING | STATISTIC | RATE | COMPETITOR | INDUSTRY_FACT
    suggested_verification: "[where to check]"
    status: PENDING | VERIFIED | INCORRECT
```

### Final Determination

```yaml
determination:
  action: APPROVE | BLOCK | ROUTE_TO_HITL
  blocking_issues: [list if any]
  hitl_required: [list if any]
  verifiable_claims: [count]
```

---

## Critical Limitation

> **Clarity Gate verifies FORM, not TRUTH.**

This system checks whether claims are properly marked as uncertain -- it cannot verify if claims are actually true.

### The Risk

An LLM can hallucinate facts INTO a document, then "pass" Clarity Gate by adding source markers to false claims.

Example:
```
FAIL: "Revenue will be $50M"
PASS: "Revenue is projected to be $50M [source: Q3 planning doc]"
```

The second passes Clarity Gate even if the "Q3 planning doc" doesn't exist or says something different.

### The Mitigation

HITL Fact Verification is **MANDATORY** before declaring PASS. The human must:
1. Spot-check that cited sources actually exist
2. Verify cited sources actually support the claims
3. Flag any suspicious attribution patterns

---

## Integration Points

### As Claude Skill

Primary implementation. See [SKILL.md](../skills/clarity-gate/SKILL.md).

### As LlamaIndex Component (Planned)

```python
from clarity_gate import ClarityGateChecker

checker = ClarityGateChecker()
result = checker.verify(document)

if result.status == "PASS":
    index.insert(document)
else:
    route_to_review(document, result.findings)
```

### As LangChain Tool (Planned)

```python
from langchain.tools import ClarityGateTool

tools = [ClarityGateTool()]
agent = create_agent(tools=tools)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.6 | 2025-12-31 | Added Two-Round HITL verification (Round A: Derived, Round B: True HITL) |
| 1.5 | 2025-12-28 | Added Points 8-9 (Temporal Coherence, Externally Verifiable Claims), new severity levels |
| 1.0 | 2025-12-21 | Initial architecture document |

---

## Related Documents

- [SKILL.md](../skills/clarity-gate/SKILL.md) — Claude skill implementation (v2.0)
- [CLARITY_GATE_FORMAT_SPEC.md](CLARITY_GATE_FORMAT_SPEC.md) — Unified format specification (v2.0)
- [CLARITY_GATE_PROCEDURES.md](CLARITY_GATE_PROCEDURES.md) — Verification procedures
- [PRIOR_ART.md](PRIOR_ART.md) — Landscape of existing systems
- [ROADMAP.md](ROADMAP.md) — Development phases

## Reference Implementation

| Package | npm | PyPI | Status |
|---------|-----|------|--------|
| clarity-gate | [npm](https://www.npmjs.com/package/clarity-gate) | [PyPI](https://pypi.org/project/clarity-gate/) | v1.0.0 — validates v1.x spec; v2.0 update planned |
