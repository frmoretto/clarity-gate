# RFC-003: Community & Integration Infrastructure

**RFC ID:** RFC-003  
**Title:** Community & Integration Infrastructure  
**Type:** Informative  
**Status:** APPROVED  
**Created:** 2026-01-26  
**Updated:** 2026-01-26  
**Author:** Francesco Marinoni Moretto  
**Affects:** Repository structure, community docs  
**Supersedes:** Original RFC-004 (renumbered per RFC-000)

---

## Summary

This RFC proposes infrastructure improvements for Clarity Gate based on analysis of the Semantica framework (422+ stars, active development). The proposals fall into three categories:

1. **Community files** — Standard open-source project infrastructure
2. **Integration architecture** — Semantica pipeline integration
3. **Strategic positioning** — Documentation and outreach

---

## Motivation

Semantica represents the current state-of-the-art in open-source knowledge engineering. Their project structure demonstrates patterns that correlate with community adoption:

- 21+ introduction notebooks (vs our 1 example)
- Comprehensive GitHub templates
- Clear contribution guidelines
- Active Discord community

More importantly, Semantica and Clarity Gate are **complementary tools** that should work together. Formalizing this relationship benefits both projects.

---

## Proposal A: Community Files

### A.1 CONTRIBUTING.md

**Priority:** High  
**Effort:** 30 minutes  
**Impact:** Enables external contributions

```markdown
# Contributing to Clarity Gate

## Ways to Contribute

1. **Prior art** — Open-source pre-ingestion gates for epistemic quality I missed?
2. **Integration** — LlamaIndex, LangChain, Semantica implementations
3. **Verification feedback** — Are the 9 points the right focus?
4. **Real-world examples** — Documents that expose edge cases

## Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test with the Claude skill
5. Submit a Pull Request

## Code Style

- Markdown files: Use ATX headers (`#`), not Setext
- YAML frontmatter: Follow agentskills.io format
- Examples: Include both passing and failing cases

## Reporting Issues

Use the issue templates:
- Bug Report
- Feature Request
- Documentation Improvement

## Questions?

Open a Discussion or reach out on LinkedIn.
```

### A.2 CHANGELOG.md

**Priority:** High  
**Effort:** 15 minutes  
**Impact:** Version tracking, upgrade guidance

```markdown
# Changelog

All notable changes to Clarity Gate will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-13

### Breaking Changes
- Unified CGD/SOT format with single `.cgd.md` extension
- Changed frontmatter schema (see CLARITY_GATE_FORMAT_SPEC.md)

### Added
- Two-Round HITL verification (Round A: Derived, Round B: True HITL)
- Point 8: Temporal Coherence
- Point 9: Externally Verifiable Claims
- Multi-platform skill support (Claude, OpenAI Codex, GitHub Copilot)

### Changed
- Verification hierarchy now routes to appropriate HITL round
- Documentation restructured for clarity

## [1.6.0] - 2025-12-31

### Added
- Two-Round HITL verification concept

## [1.5.0] - 2025-12-28

### Added
- Point 8: Temporal Coherence
- Point 9: Externally Verifiable Claims

## [1.4.0] - 2025-12-23

### Added
- Annotation offer + CGD output mode

## [1.0.0] - 2025-11-XX

### Added
- Initial release with 6-point verification
- Claude skill implementation
- Basic HITL verification
```

### A.3 GitHub Issue Templates

**Priority:** High  
**Effort:** 30 minutes  
**Impact:** Structured issue reporting

#### .github/ISSUE_TEMPLATE/bug_report.md

```markdown
---
name: Bug Report
about: Report a verification issue or skill malfunction
title: '[BUG] '
labels: bug
assignees: ''
---

## Description
A clear description of the bug.

## Document Type
- [ ] Technical specification
- [ ] Research paper
- [ ] Business document
- [ ] Other: ___

## Expected Behavior
What should have happened?

## Actual Behavior
What actually happened?

## Reproduction Steps
1. Upload document
2. Run "clarity gate on this document"
3. See error/unexpected result

## Verification Point Affected
- [ ] Point 1: Hypothesis vs Fact
- [ ] Point 2: Uncertainty Markers
- [ ] Point 3: Assumption Visibility
- [ ] Point 4: Authoritative-Looking Data
- [ ] Point 5: Data Consistency
- [ ] Point 6: Implicit Causation
- [ ] Point 7: Future as Present
- [ ] Point 8: Temporal Coherence
- [ ] Point 9: Externally Verifiable Claims
- [ ] HITL Routing
- [ ] Other

## Environment
- Platform: [Claude.ai / Claude Desktop / Claude Code]
- Skill Version: [e.g., 2.0]

## Additional Context
Any other relevant information.
```

#### .github/ISSUE_TEMPLATE/feature_request.md

```markdown
---
name: Feature Request
about: Suggest a new verification point or capability
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Problem Statement
What epistemic quality issue are you trying to catch?

## Proposed Solution
How should Clarity Gate handle this?

## Example
Provide a concrete example:

**Before (fails):**
```
[Document text that should fail]
```

**After (passes):**
```
[Document text that should pass]
```

## Alternatives Considered
Other approaches you've thought about.

## Integration Impact
- [ ] Requires new verification point
- [ ] Extends existing point
- [ ] HITL routing change
- [ ] Output format change
```

#### .github/ISSUE_TEMPLATE/documentation.md

```markdown
---
name: Documentation Improvement
about: Suggest documentation clarifications or additions
title: '[DOCS] '
labels: documentation
assignees: ''
---

## Document
Which document needs improvement?

## Issue
What's unclear or missing?

## Suggested Improvement
How should it be clarified?
```

### A.4 CODE_OF_CONDUCT.md

**Priority:** Medium  
**Effort:** 10 minutes (use Contributor Covenant template)

### A.5 SECURITY.md

**Priority:** Medium  
**Effort:** 15 minutes

```markdown
# Security Policy

## Scope

Clarity Gate is a verification methodology, not a security tool. However, we take security seriously.

## Reporting a Vulnerability

If you discover a security issue:

1. **Do NOT** open a public issue
2. Email: [security contact]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact

## Response Timeline

- Acknowledgment: 48 hours
- Initial assessment: 7 days
- Resolution target: 30 days

## Known Limitations

Clarity Gate verifies FORM, not TRUTH. It cannot:
- Detect malicious content
- Verify factual accuracy
- Replace security scanning tools
```

---

## Proposal B: Semantica Integration

### B.1 Integration Guide

**Priority:** High  
**Effort:** 2-3 hours  
**Location:** `docs/integrations/SEMANTICA.md`

```markdown
# Using Clarity Gate with Semantica

## Overview

Clarity Gate and Semantica are complementary tools:

| Tool | Stage | Purpose |
|------|-------|---------|
| Clarity Gate | Pre-ingestion | Epistemic quality verification |
| Semantica | Post-extraction | Entity resolution, KG construction |

## Pipeline Architecture

```
Raw Docs → Clarity Gate → CGD → Semantica → KG
```

## Integration Options

### Option 1: Sequential Pipeline

```python
# 1. Run Clarity Gate (via Claude)
# Output: CGD files in /verified/

# 2. Ingest with Semantica
from semantica.ingest import FileIngestor
from semantica.kg import GraphBuilder

ingestor = FileIngestor()
sources = ingestor.ingest("verified/")

builder = GraphBuilder()
kg = builder.build(sources)
```

### Option 2: Custom Ingestor

```python
from semantica.ingest import BaseIngestor
import subprocess

class ClarityGateIngestor(BaseIngestor):
    """Ingestor that validates via Clarity Gate first."""
    
    def ingest(self, source):
        # Run Clarity Gate (CLI or API)
        result = self.run_clarity_gate(source)
        
        if result.status == "BLOCK":
            raise EpistemicQualityError(result.issues)
        
        return super().ingest(result.cgd_path)
```

## Why Both?

Without Clarity Gate:
- Document: "Revenue will be $50M"
- Extracted: `Company.revenue = "$50M"`
- Result: AI reports as fact ❌

With Clarity Gate:
- Document: "Revenue will be $50M"
- CGD: "Revenue is **projected** to be $50M"
- Extracted: with epistemic context
- Result: AI reports as projection ✓
```

### B.2 GitHub Issue on Semantica Repo

**Priority:** Medium  
**Effort:** 30 minutes  
**Action:** Open discussion/issue

```markdown
Title: Pre-ingestion epistemic verification integration?

Hi Semantica team,

I've built Clarity Gate (github.com/frmoretto/clarity-gate), an open-source 
pre-ingestion verification system for epistemic quality.

**The gap it addresses:**

Semantica's conflict detection handles cases where Source A says "Google" 
and Source B says "Google Inc." — which value is correct?

Clarity Gate handles an earlier problem: a single document states 
"Revenue will be $50M" without marking it as a projection. There's no 
conflict to detect, but an AI will treat it as fact.

**Potential integration:**

Clarity Gate could run as a pre-processor before Semantica ingestion:

```
Raw Docs → Clarity Gate → CGD → Semantica → KG
```

This ensures documents are epistemically clean before entity extraction.

**Questions:**

1. Is this a gap you've considered?
2. Would a ClarityGateIngestor plugin be welcome?
3. Interest in joint documentation?

Happy to discuss further or submit a PR.

Francesco
```

### B.3 Comparison Table for README

**Priority:** Medium  
**Effort:** 15 minutes  
**Location:** Add to clarity-gate/README.md

```markdown
## How Clarity Gate Differs from Knowledge Engineering Tools

| Aspect | Semantica / LlamaIndex | Clarity Gate |
|--------|------------------------|--------------|
| **Stage** | Post-extraction | Pre-ingestion |
| **Input** | Structured entities | Raw documents |
| **Problem** | "Which value is correct?" | "Is this claim properly qualified?" |
| **Output** | Resolved KG | Annotated document (CGD) |
| **Conflict** | Multi-source disagreement | Unmarked projections/assumptions |

**They're complementary:** Use Clarity Gate *before* Semantica/LlamaIndex.
```

---

## Proposal C: Enhanced Documentation

### C.1 Cookbook (Jupyter Notebooks)

**Priority:** Medium  
**Effort:** 2-3 hours per notebook  
**Location:** `cookbook/`

Proposed notebooks:

1. **01_Getting_Started.ipynb** — Basic verification walkthrough
2. **02_The_9_Points.ipynb** — Each point with examples
3. **03_HITL_Workflow.ipynb** — Two-Round HITL demonstration
4. **04_CGD_Format.ipynb** — Creating and reading CGDs
5. **05_Integration_Semantica.ipynb** — Full pipeline example

### C.2 Prior Art Update

**Priority:** High  
**Effort:** 30 minutes  
**Location:** `docs/PRIOR_ART.md`

Add Semantica section:

```markdown
## Knowledge Engineering Frameworks

### Semantica

**URL:** github.com/Hawksight-AI/semantica  
**Focus:** Semantic layer, knowledge graph construction  
**Conflict handling:** Multi-source entity resolution

**Relationship to Clarity Gate:**

Semantica addresses conflicts between extracted entities:
- Source A: `employee.name = "John Doe"`
- Source B: `employee.name = "Jonathan Doe"`
- Resolution: Credibility-weighted voting

Clarity Gate addresses epistemic quality of source documents:
- Document states: "Revenue will be $50M"
- Problem: Projection stated as fact
- Fix: "Revenue is **projected** to be $50M"

**Integration:** Clarity Gate runs before Semantica ingestion.
```

---

## Implementation Timeline

### Week 1 (Immediate)

| Task | Effort | File |
|------|--------|------|
| CONTRIBUTING.md | 30 min | clarity-gate/CONTRIBUTING.md |
| CHANGELOG.md | 15 min | clarity-gate/CHANGELOG.md |
| Bug report template | 15 min | .github/ISSUE_TEMPLATE/bug_report.md |
| Feature request template | 15 min | .github/ISSUE_TEMPLATE/feature_request.md |

### Week 2

| Task | Effort | File |
|------|--------|------|
| CODE_OF_CONDUCT.md | 10 min | clarity-gate/CODE_OF_CONDUCT.md |
| SECURITY.md | 15 min | clarity-gate/SECURITY.md |
| Semantica integration guide | 2 hr | docs/integrations/SEMANTICA.md |
| README comparison table | 15 min | clarity-gate/README.md |

### Week 3-4

| Task | Effort | File |
|------|--------|------|
| Open Semantica GitHub issue | 30 min | External |
| Prior art update | 30 min | docs/PRIOR_ART.md |
| Getting Started notebook | 2 hr | cookbook/01_Getting_Started.ipynb |

### Month 2

| Task | Effort | File |
|------|--------|------|
| Additional notebooks | 8-10 hr | cookbook/*.ipynb |
| Semantica plugin POC | 4-6 hr | integrations/semantica/ |

---

## Success Metrics

| Metric | Current | Target (3 months) |
|--------|---------|-------------------|
| GitHub stars | ~10 | 50+ |
| Contributors | 1 | 3+ |
| Issues/PRs from community | 0 | 5+ |
| Integration mentions | 0 | Semantica docs, 1+ blog |

---

## Open Questions

1. Should we create a Discord/Slack for Clarity Gate?
2. Should notebooks be in main repo or separate `clarity-gate-cookbook`?
3. Priority: More verification points or better integration?

---

## References

- [Semantica Competitive Analysis](../clarity-gate-meta/SEMANTICA_COMPETITIVE_ANALYSIS.md)
- [Semantica GitHub](https://github.com/Hawksight-AI/semantica)
- [Keep a Changelog](https://keepachangelog.com/)
- [Contributor Covenant](https://www.contributor-covenant.org/)

---

## Decision

- [x] APPROVED
- [ ] REJECTED: [reason]

**Reviewer:** Perplexity (adversarial review)  
**Date:** 2026-01-27

---

## Document Metadata

| Field | Value |
|-------|-------|
| RFC Number | 003 (renumbered from 004 per RFC-000) |
| Status | APPROVED |
| Created | 2026-01-26 |
| Author | Francesco Marinoni Moretto |

---

*End of RFC*
