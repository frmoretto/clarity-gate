# Clarity Gate v1.6

> **⚠️ NEW RELEASE:** Version 1.6 released (2025-12-31). Download the new [`clarity-gate.zip`](clarity-gate.zip) for Two-Round HITL verification — separating quick confirmation from real verification.

**Open-source pre-ingestion verification for epistemic quality in RAG systems.**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

> *"Detection finds what is; enforcement ensures what should be. In practice: find the missing uncertainty markers before they become confident hallucinations."*

---

## The Problem

If you feed a well-aligned model a document that states "Revenue will reach $50M by Q4" as fact (when it's actually a projection), the model will confidently report this as fact.

The model isn't hallucinating. It's faithfully representing what it was told.

**The failure happened before the model saw the input.**

| Document Says | Accuracy Check | Epistemic Check |
|---------------|----------------|-----------------|
| "Revenue will be $50M" (unmarked projection) | ✅ PASS | ❌ FAIL — projection stated as fact |
| "Our approach outperforms X" (no evidence) | ✅ PASS | ❌ FAIL — ungrounded assertion |
| "Users prefer feature Y" (no methodology) | ✅ PASS | ❌ FAIL — missing epistemic basis |

**Accuracy verification asks:** "Does this match the source?"  
**Epistemic verification asks:** "Is this claim properly qualified?"

Both matter. Accuracy verification has mature open-source tools. Epistemic verification has excellent detection systems (UnScientify, HedgeHog, BioScope), but, as far as I know, no open-source enforcement layer.

Clarity Gate is a proposal for that layer.

---

## What Is Clarity Gate?

Clarity Gate is an **open-source pre-ingestion verification system** for epistemic quality.

- **Clarity** — Making explicit what's fact, what's projection, what's hypothesis
- **Gate** — Documents don't enter the knowledge base until they pass verification

### The Gap It Addresses

| Component | Status |
|-----------|--------|
| Pre-ingestion gate pattern | ✅ Proven (Adlib, pharma QMS) |
| Epistemic detection | ✅ Proven (UnScientify, HedgeHog) |
| **Pre-ingestion epistemic enforcement** | ❌ Gap (to my knowledge) |
| **Open-source accessibility** | ❌ Gap |

| Dimension | Enterprise (Adlib) | Clarity Gate |
|-----------|-------------------|--------------|
| **License** | Proprietary | Open source (CC BY 4.0) |
| **Focus** | Accuracy, compliance | Epistemic quality |
| **Target** | Fortune 500 | Founders, researchers, small teams |
| **Cost** | Enterprise pricing | Free |

---

## Quick Start

### Option 1: claude.ai / Claude Desktop

1. Download [`clarity-gate.zip`](clarity-gate.zip)
2. Go to Settings → Features → Skills → Add
3. Upload the zip file
4. Ask Claude: *"Run clarity gate on this document"*

### Option 2: Claude Code

1. Copy `SKILL.md` to your project's skills folder
2. Claude Code will automatically detect and use it
3. Ask Claude: *"Run clarity gate on this document"*

### Option 3: Claude Projects

Add [`SKILL.md`](SKILL.md) to project knowledge. Claude will search it when needed, though Skills provide better integration.

### Option 4: Manual / Other LLMs

Use the [9-point verification](docs/ARCHITECTURE.md#the-9-verification-points) as a manual review process.

For Cursor, Windsurf, or other AI tools, extract the 9 verification points into your `.cursorrules`. The methodology is tool-agnostic—only SKILL.md is Claude-optimized.

---

## Validators (npm / PyPI)

Validate `.sot` and `.cgd` files programmatically or in CI/CD pipelines:

**npm:**
```bash
# Install
npm install -g sot-validator cgd-validator

# Or use directly
npx sot-validator document.sot
npx cgd-validator document.cgd

# CI/CD (quick pass/fail)
npx sot-verify docs/*.sot
npx cgd-verify docs/*.cgd
```

**PyPI:**
```bash
# Install
pip install sot-validator cgd-validator

# Validate
sot-validator document.sot
cgd-validator document.cgd

# CI/CD (quick pass/fail)
sot-verify docs/*.sot
cgd-verify docs/*.cgd
```

**Packages:**

| Package | npm | PyPI | Purpose |
|---------|-----|------|--------|
| sot-validator | [npm](https://www.npmjs.com/package/sot-validator) | [PyPI](https://pypi.org/project/sot-validator/) | Detailed validation with warnings |
| sot-verify | [npm](https://www.npmjs.com/package/sot-verify) | [PyPI](https://pypi.org/project/sot-verify/) | Quick pass/fail for CI/CD |
| cgd-validator | [npm](https://www.npmjs.com/package/cgd-validator) | [PyPI](https://pypi.org/project/cgd-validator/) | Detailed validation with warnings |
| cgd-verify | [npm](https://www.npmjs.com/package/cgd-verify) | [PyPI](https://pypi.org/project/cgd-verify/) | Quick pass/fail for CI/CD |

See [FILE_FORMAT_SPEC.md](docs/FILE_FORMAT_SPEC.md) for the complete `.sot` and `.cgd` format specification.

---

## Two Modes

**Verify Mode (default):**
```
"Run clarity gate on this document"
→ Issues report + Two-Round HITL verification
```

**Annotate Mode:**
```
"Run clarity gate and annotate this document"
→ Complete document with fixes applied inline (CGD)
```

The annotated output is a **Clarity-Gated Document (CGD)**—research shows mid-tier LLMs handle CGDs with better abstention on ambiguous claims.

---

## The 9 Verification Points

### Epistemic Checks (Core Focus)

1. **Hypothesis vs. Fact Labeling** — Claims marked as validated or hypothetical
2. **Uncertainty Marker Enforcement** — Forward-looking statements require qualifiers
3. **Assumption Visibility** — Implicit assumptions made explicit
4. **Authoritative-Looking Unvalidated Data** — Tables with percentages flagged if unvalidated

### Data Quality Checks (Complementary)

5. **Data Consistency** — Conflicting numbers within document
6. **Implicit Causation** — Claims implying causation without evidence
7. **Future State as Present** — Planned outcomes described as achieved

### Verification Routing (v1.5+)

8. **Temporal Coherence** — Dates consistent with each other and with present
9. **Externally Verifiable Claims** — Pricing, statistics, competitor claims flagged for verification

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for full details and examples.

---

## Two-Round HITL Verification (New in v1.6)

Different claims need different types of verification:

| Claim Type | What Human Checks | Cognitive Load |
|------------|-------------------|----------------|
| LLM found source, human witnessed | "Did I interpret correctly?" | Low (quick scan) |
| Human's own data | "Is this actually true?" | High (real verification) |
| No source found | "Is this actually true?" | High (real verification) |

**v1.6 separates these into two rounds:**

### Round A: Derived Data Confirmation

Quick scan of claims from sources found in the current session:

```
## Derived Data Confirmation

These claims came from sources found in this session:

- o3 prices cut 80% June 2025 (OpenAI blog)
- Opus 4.5 is $5/$25 (Anthropic pricing page)

Reply "confirmed" or flag any I misread.
```

### Round B: True HITL Verification

Full verification of claims needing actual checking:

```
## HITL Verification Required

| # | Claim | Why HITL Needed | Human Confirms |
|---|-------|-----------------|----------------|
| 1 | Benchmark scores (100%, 75%→100%) | Your experiment data | [ ] True / [ ] False |
```

**Result:** Human attention focused on claims that actually need it.

---

## Verification Hierarchy

```
Claim Extracted --> Source of Truth Exists?
                           |
           +---------------+---------------+
           YES                             NO
           |                               |
     Tier 1: Automated              Tier 2: HITL
     Verification                   Two-Round Verification
           |                               |
     +-----+-----+                   Round A → Round B
     |           |                         |
   Tier 1A    Tier 1B               APPROVE/REJECT
   Internal   External
     |           |
   PASS/BLOCK  PASS/BLOCK
```

### Tier 1A: Internal Consistency (Ready Now)

Checks for contradictions *within* a document — no external systems required.

| Check Type | Example |
|------------|---------|
| Figure vs. Text | Figure shows β=0.33, text claims β=0.73 |
| Abstract vs. Body | Abstract claims "40% improvement," body shows 28% |
| Table vs. Prose | Table lists 5 features, text references 7 |

See [biology paper example](examples/biology-paper-example.md) for a real case where Clarity Gate detected a Δ=0.40 discrepancy. Try it yourself at [arxiparse.org](https://arxiparse.org).

### Tier 1B: External Verification (Extension Interface)

For claims verifiable against structured sources. **Users provide connectors.**

### Tier 2: Two-Round HITL (Intelligent Routing)

The system detects *which* specific claims need human review AND *what kind of review* each needs.

*Example: A 50-claim document might have 48 pass automated checks, with the remaining 2 split between Round A (quick confirmation) and Round B (real verification). (Illustrative example, not measured.)*

---

## Where This Fits

```
Layer 4: Human Strategic Oversight
Layer 3: AI Behavior Verification (PETRI, BLOOM, behavioral evals)
Layer 2: Input/Context Verification  <-- Clarity Gate
Layer 1: Deterministic Boundaries (rate limits, guardrails)
Layer 0: AI Execution
```

A perfectly aligned model (Layer 3) can confidently produce unsafe outputs from unsafe context (Layer 2). Alignment doesn't inoculate against misleading information.

---

## Prior Art

Clarity Gate builds on proven patterns. See [PRIOR_ART.md](docs/PRIOR_ART.md) for the full landscape.

**Enterprise Gates:** Adlib Software, Pharmaceutical QMS  
**Epistemic Detection:** UnScientify, HedgeHog, FactBank  
**Fact-Checking:** FEVER, ClaimBuster  
**Post-Retrieval:** Self-RAG, RAGAS, TruLens

**The opportunity:** Existing detection tools (UnScientify, HedgeHog, BioScope) excel at identifying uncertainty markers. Clarity Gate proposes a complementary enforcement layer that routes ambiguous claims to human review or marks them automatically. I believe these could work together. Community input on integration is welcome.

---

## Critical Limitation

> **Clarity Gate verifies FORM, not TRUTH.**

This system checks whether claims are properly marked as uncertain — it cannot verify if claims are actually true.

**Risk:** An LLM can hallucinate facts INTO a document, then "pass" Clarity Gate by adding source markers to false claims.

**Mitigation:** Two-Round HITL verification is **mandatory** before declaring PASS. See [SKILL.md](SKILL.md) for the full protocol.

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Ready | Internal consistency checks + Two-Round HITL + annotation (Claude skill) |
| **Phase 2** | 🔜 Planned | External verification hooks (user connectors) |
| **Phase 3** | 🔜 Planned | Confidence scoring for HITL optimization |

See [ROADMAP.md](docs/ROADMAP.md) for details and timeline.

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full 9-point system, verification hierarchy, output format |
| [PRIOR_ART.md](docs/PRIOR_ART.md) | Landscape of existing systems |
| [ROADMAP.md](docs/ROADMAP.md) | Phase 1/2/3 development plan |
| [SKILL.md](SKILL.md) | Claude skill implementation |
| [examples/](examples/) | Real-world verification examples |
| [docs/research/](docs/research/) | Project research documentation |

---

## Related

**arxiparse.org** — Live implementation for scientific papers  
[arxiparse.org](https://arxiparse.org)

**Source of Truth Creator** — Create epistemically calibrated documents (use before verification)  
[github.com/frmoretto/source-of-truth-creator](https://github.com/frmoretto/source-of-truth-creator)

**Stream Coding** — Documentation-first methodology where Clarity Gate originated  
[github.com/frmoretto/stream-coding](https://github.com/frmoretto/stream-coding)

---

## License

CC BY 4.0 — Use freely with attribution.

---

## Author

**Francesco Marinoni Moretto**
- GitHub: [@frmoretto](https://github.com/frmoretto)
- LinkedIn: [francesco-moretto](https://www.linkedin.com/in/francesco-moretto/)

---

## Contributing

Looking for:

1. **Prior art** — Open-source pre-ingestion gates for epistemic quality I missed?
2. **Integration** — LlamaIndex, LangChain implementations
3. **Verification feedback** — Are the 9 points the right focus?
4. **Real-world examples** — Documents that expose edge cases

Open an issue or PR.
