# Clarity Gate Prior Art

**Version:** 1.2  
**Last Updated:** 2026-01-27

---

## Overview

Clarity Gate builds on proven patterns. This document maps the landscape of existing systems and identifies the specific gap Clarity Gate addresses.

**Key principle:** We're not claiming to invent pre-ingestion gates. We're applying proven patterns to epistemic quality, open-source.

**Verification note:** Tool landscape validated via Perplexity Deep Research (January 2026). See changelog for details.

---

## The Gap Matrix

| Stage | Privacy/Security | Accuracy/Compliance | Epistemic Quality |
|-------|------------------|---------------------|-------------------|
| **Pre-ingestion** | ✅ Protecto.ai, OWASP | ✅ Adlib, Pharma QMS | ❌ **Gap** |
| **Detection** | — | — | ✅ UnScientify, HedgeHunter (academic) |
| **Post-retrieval** | — | — | ✅ RAGAS, TruLens, LOKI, RagChecker |
| **Runtime** | — | — | ✅ Self-RAG |

**The gap:** To the best of our knowledge, no open-source system enforces epistemic quality at pre-ingestion.

---

## Enterprise Pre-Ingestion Gates (Proprietary)

### Adlib Software

**Product:** Transform 2025.2 (released November 18, 2025)

**Capabilities:**
- Multi-LLM voting for accuracy verification
- Accuracy Score with configurable thresholds
- Exception rate reduction: 40-60% (claimed)
- Cycle time acceleration: 30-50% (claimed)

**Customers:** Pfizer, Swiss Re, IAG, JP Morgan (Fortune 500)

**Certifications:** SOC 2 Type II, HIPAA (October 2025)

**Focus:** Accuracy and compliance, not epistemic quality

**Reference:** adlibsoftware.com [CHECK BEFORE CITING - features may change]

---

### Pharmaceutical QMS

**Systems:** SimplerQMS, Dot Compliance, Picomto, Ideagen

**Regulatory basis:** FDA 21 CFR Part 11 (established 1997)

**Core requirements:**
- Electronic signatures with name, date/time, meaning
- Audit trails tracking who did what when
- Periodic re-validation schedules
- "If it's not documented, it didn't happen"

**Maturity:** 20+ years of regulatory enforcement

**Focus:** Compliance and traceability, not epistemic quality

---

### What Enterprise Gates Catch vs. Don't Catch

| What They Catch | What They Don't Catch |
|-----------------|----------------------|
| "Revenue was $47M" when records show $49M | "Revenue will be $50M" stated as fact |
| Missing required signature | "Our approach outperforms X" with no evidence |
| Wrong date format | "Users prefer Y" with no methodology |
| Conflicting dates across documents | Unmarked projections |

**The distinction:** Accuracy (does it match the source?) vs. Epistemic quality (is it properly qualified?)

---

## Epistemic Detection Tools (Open-Source)

### UnScientify

**Paper:** Ningrum et al., 2023 (arXiv:2307.14236)

**Capabilities:**
- Detects multiple scientific uncertainty pattern groups
- Rule-based + ML hybrid approach
- Accuracy: ~0.8 on research articles (approximate; see paper for exact metrics)

**What it does:** Identifies uncertainty markers that ARE present in text

**What it doesn't do:** Enforce markers that SHOULD be present but aren't

**Status:** Open-source, academic

---

### HedgeHunter (2010)

**Paper:** Clausen, CoNLL-2010 Shared Task (W10-3017)

**Author:** David Clausen, Stanford University

**Capabilities:**
- Two-stage hedge detection: (1) Hedge cue detection, (2) Uncertainty classification
- Training data: Wikipedia + biomedical abstracts
- High precision hedge detection for downstream IE tasks

**What it does:** Token-level hedge cue detection and scope classification

**What it doesn't do:** Determine if hedging is missing where needed

**Status:** Academic research tool, not maintained, no downloadable package

**Note on "HedgeHog" naming confusion:** Multiple unrelated projects use similar names:
- HedgeHog (wearable sensor platform) — motion tracking hardware
- hedgehog-qa (Haskell testing library) — property-based testing
- HedgePeer (2022 dataset) — benchmark corpus, not a tool
- Various DeFi/trading bots

None of these are NLP uncertainty detection tools. HedgeHunter (2010) is the primary academic system for hedge detection.

---

### FactBank

**Type:** Veridicality corpus

**Purpose:** Training data for factuality classification

**What it provides:** Annotated examples of factual vs. uncertain claims

**What it doesn't do:** Runtime verification

**Status:** Open-source, academic resource

---

### BioScope

**Paper:** Vincze et al., 2008

**Type:** Biomedical uncertainty corpus

**Purpose:** Training data for uncertainty detection in scientific text

**Status:** Open-source, academic resource

---

### HedgePeer Dataset (2022)

**Paper:** Ghosal et al., ACM SIGMOD 2022

**Type:** Hedge detection benchmark corpus

**Size:** 5x larger than previous hedge detection datasets

**Purpose:** Enable domain adaptation across scientific domains

**Status:** Dataset for training/evaluation, not a deployable tool (22+ citations)

---

## Detection vs. Enforcement

| Tool Type | Question Answered |
|-----------|-------------------|
| **Detection** (UnScientify, HedgeHunter) | "Is uncertainty expressed?" |
| **Enforcement** (Clarity Gate) | "Should uncertainty be expressed but isn't?" |

This distinction is the core of Clarity Gate's contribution.

---

## Modern Fact-Checking Tools (2024-2025)

These tools exist but operate **post-ingestion** or **post-retrieval**, not at the pre-ingestion gate:

### LOKI (COLING 2025)

**Focus:** Fact verification with checkworthiness assessment

**Stage:** Post-retrieval evaluation

**Limitation:** Evaluates claims after they're in the system

---

### FIRE (arXiv:2411.00784)

**Focus:** Iterative fact-checking framework

**Stage:** Post-retrieval, iterative refinement

**Limitation:** Operates on generated outputs, not source documents

---

### RagChecker (arXiv:2408.08067)

**Focus:** Diagnostic framework for RAG pipeline issues

**Stage:** Post-retrieval evaluation

**Limitation:** Diagnoses problems after retrieval, doesn't prevent them

---

### Veracity (arXiv:2506.15794)

**Focus:** Open-source fact-checking system

**Stage:** Claim verification against external sources

**Limitation:** Requires external evidence corpus, post-hoc verification

---

### Gap Confirmation

These modern tools validate the gap Clarity Gate addresses:

| Tool | Pre-ingestion? | Epistemic enforcement? |
|------|----------------|------------------------|
| LOKI | ❌ | ❌ (fact-checking) |
| FIRE | ❌ | ❌ (fact-checking) |
| RagChecker | ❌ | ❌ (diagnostic) |
| Veracity | ❌ | ❌ (fact-checking) |
| **Clarity Gate** | ✅ | ✅ |

---

## Automated Fact-Checking (Academic)

### FEVER

**Paper:** Thorne et al., 2018

**Pipeline:**
1. Claim extraction
2. Evidence retrieval
3. Verification against evidence

**Dataset:** 185,000 claims with Wikipedia evidence

**Focus:** Verifying claims against external knowledge

**Limitation:** Requires pre-existing evidence corpus

**Reference:** fever.ai [STABLE - academic]

---

### ClaimBuster

**Capabilities:**
- Claim extraction from news and documents
- Claim-worthiness scoring
- Integration with fact-checking workflows

**Focus:** Identifying claims worth checking, not epistemic quality

**Reference:** claimbuster.org [CHECK BEFORE CITING]

---

## Post-Retrieval & Runtime Systems

### Self-RAG

**Paper:** Asai et al., 2023 (arXiv:2310.11511)

**Innovation:** Reflection tokens (ISREL, ISSUP, ISUSE)
- ISREL: Is retrieved content relevant?
- ISSUP: Is generation supported by retrieval?
- ISUSE: Is response useful?

**Stage:** Runtime (after retrieval, during generation)

**Limitation:** Doesn't prevent problematic content from entering knowledge base

---

### RAGAS

**Type:** RAG evaluation framework

**Metrics:**
- Faithfulness
- Answer relevancy
- Context precision
- Context recall

**Stage:** Post-retrieval evaluation

**Limitation:** Evaluates after the fact, doesn't gate ingestion

**Reference:** github.com/explodinggradients/ragas [CHECK BEFORE CITING]

---

### TruLens

**Type:** LLM application evaluation

**Capabilities:**
- Groundedness scoring
- Answer relevance
- Context relevance

**Stage:** Post-retrieval evaluation

**Limitation:** Same as RAGAS -- evaluation, not prevention

---

## Knowledge Engineering Frameworks

### Semantica

**URL:** github.com/Hawksight-AI/semantica  
**Focus:** Semantic layer, knowledge graph construction  
**Stage:** Post-extraction

**Capabilities:**
- Entity extraction and resolution
- Multi-source conflict resolution
- Knowledge graph construction
- Credibility-weighted voting for conflicting values

**Conflict handling example:**
- Source A: `employee.name = "John Doe"`
- Source B: `employee.name = "Jonathan Doe"`
- Resolution: Credibility-weighted voting

**Relationship to Clarity Gate:**

Semantica addresses conflicts *between* extracted entities. Clarity Gate addresses epistemic quality *within* source documents:

| Tool | Question | Example |
|------|----------|---------|
| Semantica | "Which value is correct?" | John vs Jonathan |
| Clarity Gate | "Is this claim properly qualified?" | "Revenue will be $50M" (unmarked projection) |

**Integration:** Clarity Gate runs *before* Semantica ingestion:

```
Raw Docs → Clarity Gate → CGD → Semantica → Knowledge Graph
```

**Status:** Open-source, active development (422+ stars as of Jan 2026)

---

## Privacy & Security Pre-Ingestion

### Protecto.ai

**Focus:** PII/PHI detection and redaction

**Stage:** Pre-ingestion

**Relevance:** Proves pre-ingestion gates work; different focus

---

### OWASP LLM Security

**Focus:** Prompt injection, data leakage

**Stage:** Various

**Relevance:** Security-focused, not epistemic

---

## Validation & Guardrails

### Guardrails AI

**Focus:** Output validation (schema, format)

**Stage:** Post-generation

**Relevance:** Structure validation, not epistemic quality

---

### NeMo Guardrails

**Focus:** Dialog safety, topic boundaries

**Stage:** Runtime

**Relevance:** Behavioral guardrails, not epistemic verification

---

## The Safety Stack Position

```
Layer 4: Human Strategic Oversight
Layer 3: AI Behavior Verification (PETRI, BLOOM, red-teaming)
Layer 2: Input/Context Verification  <-- Clarity Gate
Layer 1: Deterministic Boundaries (rate limits, guardrails)
Layer 0: AI Execution
```

**Layer 3 Tools:**
- [PETRI](https://anthropic.com/research/petri-open-source-auditing) — Anthropic's open-source auditing tool for exploring model behaviors via multi-turn conversations
- [BLOOM](https://anthropic.com/research/bloom) — Anthropic's automated behavioral evaluation framework for frontier models

**Key insight:** A perfectly aligned model (Layer 3) can confidently produce unsafe outputs from unsafe context (Layer 2). Alignment doesn't inoculate against misleading information.

---

## Summary: What's New

| Component | Status |
|-----------|--------|
| Pre-ingestion gate pattern | ✅ Proven (Adlib, pharma QMS) |
| Epistemic detection | ✅ Proven (UnScientify, HedgeHunter — academic only) |
| Fact-checking pipelines | ✅ Proven (FEVER, ClaimBuster, LOKI, FIRE) |
| Post-retrieval evaluation | ✅ Proven (RAGAS, TruLens, RagChecker, Self-RAG) |
| **Pre-ingestion epistemic enforcement** | ❌ Gap |
| **Open-source accessibility** | ❌ Gap |

**Clarity Gate contribution:** Applying proven gate patterns to epistemic quality, open-source.

---

## References

### Enterprise (Volatile - verify before citing)

- Adlib Software: adlibsoftware.com
- SimplerQMS: simplerqms.com
- Dot Compliance: dotcompliance.com

### Academic (Stable)

- UnScientify: arXiv:2307.14236 (Ningrum et al., 2023)
- HedgeHunter: CoNLL-2010 W10-3017 (Clausen, 2010)
- HedgePeer: ACM SIGMOD 2022 (Ghosal et al., 2022)
- FEVER: fever.ai (Thorne et al., 2018)
- Self-RAG: arXiv:2310.11511 (Asai et al., 2023)
- BioScope: Vincze et al., 2008
- FactBank: Sauri & Pustejovsky, 2009
- LOKI: COLING 2025
- FIRE: arXiv:2411.00784
- RagChecker: arXiv:2408.08067
- Veracity: arXiv:2506.15794

### Standards (Stable)

- FDA 21 CFR Part 11 (established 1997)
- ISO/IEC 5259-1:2024 and 5259-2:2024 (AI data quality for analytics and ML)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-21 | Initial prior art landscape |
| 1.1 | 2026-01-05 | HedgeHog → HedgeHunter (corrected). Added modern fact-checking tools (LOKI, FIRE, RagChecker, Veracity). Added HedgePeer dataset. |
| 1.2 | 2026-01-27 | Added Semantica (Knowledge Engineering Frameworks section) per RFC-003. |
