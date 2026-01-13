# Clarity Gate Roadmap

**Version:** 1.4
**Last Updated:** 2026-01-13

---

## Overview

Clarity Gate development follows a phased approach, starting with the highest-value, lowest-complexity capabilities and expanding based on real-world feedback.

---

## Current Status

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | Internal consistency checks (Claude skill) | ✅ Ready |
| **Phase 2** | npm/PyPI validators for CI/CD | 🔜 Planned |
| **Phase 3** | External verification hooks | 🔜 Planned |
| **Phase 4** | Confidence scoring & optimization | 🔜 Planned |

---

## Phase 1: Internal Consistency (Ready)

### What's Included

**Core Capability:** Verify claims within a single document without external systems.

| Component | Status | Description |
|-----------|--------|-------------|
| 9-point verification checklist | ✅ Ready | 4 epistemic + 3 data quality + 2 verification routing checks |
| Temporal coherence detection | ✅ Ready (v1.5) | Date validation, chronology checks |
| Externally verifiable claims | ✅ Ready (v1.5) | Pricing, statistics, competitor claim flagging |
| Two-Round HITL verification | ✅ Ready (v1.6) | Round A (derived data) + Round B (true verification) |
| Claude skill implementation | ✅ Ready (v2.0) | SKILL.md with agentskills.io compliance |
| Internal consistency detection | ✅ Ready | Figure vs. text, abstract vs. body |
| HITL protocol | ✅ Ready | Intelligent routing to human review |
| Output format specification | ✅ Ready | YAML-based findings report |

### Deliverables

- `skills/clarity-gate/SKILL.md` — Claude skill for direct use (v2.0)
- `docs/ARCHITECTURE.md` — Full system documentation
- `docs/PRIOR_ART.md` — Landscape analysis
- `examples/` — Real-world verification examples

### Use Cases

1. **Research papers** — Cross-reference figures, tables, and text claims
2. **Business documents** — Flag unmarked projections and assumptions
3. **Technical specs** — Identify inconsistencies before review
4. **RAG knowledge bases** — Pre-ingestion quality gate

### Limitations

- No external verification (user must manually check external claims)
- No confidence scoring (binary pass/fail/review)
- No integration APIs (Claude skill only)

---

## Phase 2: npm/PyPI Validators (Planned)

### Goal

Provide programmatic validators for CI/CD integration.

### What's Planned

| Component | Status | Description |
|-----------|--------|-------------|
| Unified Format Specification | ✅ v2.0 | Single spec for CGD/SOT |
| Procedures Documentation | ✅ v1.0 | Verification workflows |
| clarity-gate package | 🔜 Planned | Unified validator (npm/PyPI) |
| agentskills.io compliance | ✅ Ready | YAML frontmatter, marketplace.json |

### Specification Suite v2.0 (Ready)

| Document | Purpose |
|----------|---------|
| [CLARITY_GATE_FORMAT_SPEC.md](CLARITY_GATE_FORMAT_SPEC.md) | Unified format specification |
| [CLARITY_GATE_PROCEDURES.md](CLARITY_GATE_PROCEDURES.md) | Verification procedures |

### Planned Package

| Package | npm | PyPI | Purpose |
|---------|-----|------|---------|
| clarity-gate | 🔜 Planned | 🔜 Planned | Unified validator for CGD files |

### Placeholder Packages (Namespace Reserved)

| Package | npm | PyPI | Purpose |
|---------|-----|------|---------|
| cgd-creator | v0.0.1 | v0.0.1 | Future: CGD generation |
| sot-creator | v0.0.1 | v0.0.1 | Future: SOT generation |
| cgd-generator | v0.0.1 | v0.0.1 | Future: Batch generation |
| sot-generator | v0.0.1 | v0.0.1 | Future: Batch generation |
| memory-trail | v0.0.1 | v0.0.1 | Future: Decision tracking |

### agentskills.io Compliance (Ready)

| Component | Status | Location |
|-----------|--------|----------|
| YAML frontmatter | ✅ Ready | `skills/clarity-gate/SKILL.md` |
| marketplace.json | ✅ Ready | `.claude-plugin/marketplace.json` |
| AGENTS.md | ✅ Ready | Repository root |
| Build scripts | ✅ Ready | `scripts/build-skill.sh`, `scripts/build-skill.ps1` |

---

## Phase 3: External Verification Hooks (Planned)

### Goal

Provide interfaces for users to implement their own verification connectors.

### Architecture

```python
class VerificationConnector:
    """Base class for external verification."""
    
    def can_verify(self, claim: Claim) -> bool:
        """Returns True if this connector can verify the claim type."""
        pass
    
    def verify(self, claim: Claim) -> VerificationResult:
        """Verifies claim against external source."""
        pass

class ConnectorRegistry:
    """Manages available verification connectors."""
    
    def register(self, connector: VerificationConnector) -> None:
        pass
    
    def find_connector(self, claim: Claim) -> Optional[VerificationConnector]:
        pass
```

### Example Connectors (Templates)

| Connector | Source | Claims Verified |
|-----------|--------|-----------------|
| `GitHistoryConnector` | Git commits | Deployment dates, version numbers |
| `MetricsConnector` | Monitoring APIs | Performance claims, uptime |
| `FinancialConnector` | Accounting systems | Revenue, costs, margins |
| `CRMConnector` | Customer databases | User counts, customer lists |

### Deliverables

- Connector interface specification
- Template implementations for common sources
- Integration guide for custom connectors
- Example: Git-based verification

### Dependencies

- Real-world user feedback on connector needs
- API design validation
- Security review for external connections

### Timeline

**Target:** Q2-Q3 2026 *(estimated, dependent on Phase 2 completion and feedback)*

---

## Phase 4: Confidence Scoring & HITL Optimization (Planned)

### Goal

Reduce HITL burden through intelligent confidence scoring.

### Capabilities

| Capability | Description |
|------------|-------------|
| Claim confidence scoring | 0-100 score based on multiple signals |
| Adaptive thresholds | Learn from HITL decisions |
| Batch prioritization | Route highest-risk claims first |
| Audit trail | Track all automated and human decisions |

### Confidence Signals

| Signal | Weight | Description |
|--------|--------|-------------|
| Internal consistency | High | Contradictions indicate low confidence |
| Hedging language present | Medium | Markers present = appropriate confidence |
| Source attribution | Medium | Cited claims higher than uncited |
| Claim specificity | Low | Very specific numbers may need verification |
| Historical patterns | Medium | Similar claims that failed before |

### HITL Optimization

```
Current (Phase 1):
  50 claims --> 48 auto-pass, 2 HITL review

Phase 3 Target:
  50 claims --> 48 auto-pass, 1.5 HITL review (confidence-prioritized)
                             + 0.5 auto-handled (learned patterns)
```

### Deliverables

- Confidence scoring algorithm
- Threshold configuration interface
- Learning pipeline for HITL feedback
- Analytics dashboard for verification patterns

### Dependencies

- Sufficient Phase 1 usage data
- HITL decision corpus for training
- Validation of confidence signals

### Timeline

**Target:** Q4 2026 *(estimated, dependent on Phase 3 completion and data collection)*

---

## Integration Roadmap

### Current

| Platform | Status | Notes |
|----------|--------|-------|
| Claude Desktop | ✅ Ready | Via `skills/clarity-gate/SKILL.md` |
| Claude Code | ✅ Ready | Via `skills/clarity-gate/SKILL.md` |
| Manual checklist | ✅ Ready | Via documentation |
| agentskills.io | ✅ Ready | Marketplace-compliant |

### Planned

| Platform | Phase | Notes |
|----------|-------|-------|
| npm | Phase 2 | `npm install clarity-gate` |
| PyPI | Phase 2 | `pip install clarity-gate` |
| LlamaIndex | Phase 3 | Custom retriever/checker component |
| LangChain | Phase 3 | Tool integration |
| REST API | Phase 4 | Standalone service deployment |

### LlamaIndex Integration (Planned)

```python
from llama_index import VectorStoreIndex
from clarity_gate import ClarityGateChecker

# Pre-ingestion verification
checker = ClarityGateChecker()

def ingest_with_verification(document):
    result = checker.verify(document)
    
    if result.status == "PASS":
        index.insert(document)
        return {"status": "ingested"}
    elif result.status == "NEEDS_REVIEW":
        queue_for_review(document, result.findings)
        return {"status": "queued_for_review"}
    else:
        return {"status": "blocked", "issues": result.findings}
```

### LangChain Integration (Planned)

```python
from langchain.tools import Tool
from clarity_gate import verify_document

clarity_gate_tool = Tool(
    name="clarity_gate",
    func=verify_document,
    description="Verify epistemic quality of a document before use"
)
```

---

## Contributing

### Phase 1 Contributions Welcome

- **Prior art discoveries** — Open-source pre-ingestion gates we missed?
- **Verification point feedback** — Are the 9 points the right focus?
- **Real-world examples** — Documents that expose edge cases
- **Documentation improvements** — Clarity and completeness

### Phase 2 Contributions Welcome

- **Connector implementations** — Git, metrics, CRM integrations
- **API design feedback** — Interface usability
- **Security review** — External connection risks

### How to Contribute

1. Open an issue describing the contribution
2. Discuss approach before implementing
3. Submit PR with tests and documentation
4. Expect review within 1 week

---

## Success Metrics

### Phase 1

| Metric | Target *(goal)* | Measurement |
|--------|-----------------|-------------|
| GitHub stars | 100+ *(target)* | GitHub |
| Active users | 50+ *(target)* | Download/usage tracking |
| Issues/feedback | 20+ *(target)* | GitHub issues |
| Real-world examples | 5+ *(target)* | Contributed examples |

### Phase 2

| Metric | Target *(goal)* | Measurement |
|--------|-----------------|-------------|
| npm package published | 1 *(target)* | npm registry |
| PyPI package published | 1 *(target)* | PyPI registry |
| CI/CD example | 1+ *(target)* | GitHub Actions workflow |

### Phase 3

| Metric | Target *(goal)* | Measurement |
|--------|-----------------|-------------|
| Connector implementations | 3+ *(target)* | Community contributions |
| Integration usage | 25+ *(target)* | Package downloads |
| HITL efficiency | >90% auto-pass *(target)* | User reports |

### Phase 4

| Metric | Target *(goal)* | Measurement |
|--------|-----------------|-------------|
| Confidence accuracy | >85% *(target)* | Validated against HITL decisions |
| HITL reduction | >50% vs Phase 1 *(target)* | Before/after comparison |
| Enterprise adoption | 2+ *(target)* | Case studies |

---

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — Full system documentation
- [CLARITY_GATE_FORMAT_SPEC.md](CLARITY_GATE_FORMAT_SPEC.md) — Unified format specification (v2.0)
- [CLARITY_GATE_PROCEDURES.md](CLARITY_GATE_PROCEDURES.md) — Verification procedures
- [PRIOR_ART.md](PRIOR_ART.md) — Landscape of existing systems

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.4 | 2026-01-13 | Renumbered phases: npm/PyPI validators now Phase 2, external hooks Phase 3, confidence scoring Phase 4 |
| 1.3 | 2026-01-12 | Added Phase 1.5 (specs & packages), updated integrations to Current |
| 1.2 | 2025-12-31 | Updated for v1.6 (Two-Round HITL) |
| 1.1 | 2025-12-28 | Updated for v1.5 (9-point system) |
| 1.0 | 2025-12-21 | Initial roadmap |
