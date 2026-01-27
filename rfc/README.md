# Clarity Gate RFCs

Request for Comments (RFCs) for the Clarity Gate specification.

---

## RFC Index

| RFC | Title | Type | Status | Version Impact |
|-----|-------|------|--------|----------------|
| [RFC-000](RFC-000-governance-framework.md) | Governance Framework | Meta | APPROVED | — |
| [RFC-001](RFC-001-format-spec-clarifications.md) | FORMAT_SPEC Clarifications | Normative | IMPLEMENTED | v2.0 → v2.1 ✅ |
| [RFC-002](RFC-002_RAG_Chunk_Safety.md) | RAG Chunk Context Advisory | Normative | APPROVED | v2.1 → v2.2 |
| [RFC-003](RFC-003-community-integration-infrastructure.md) | Community & Integration Infrastructure | Informative | APPROVED | — |
| [RFC-004](RFC-004-parser-hardening.md) | Parser Hardening | Normative | APPROVED | v2.1 → v2.2 |

---

## RFC Types

| Type | Definition | Example |
|------|------------|---------|
| **Meta** | Governance process itself | RFC-000 |
| **Normative** | Changes validation rules or format | RFC-001, RFC-002, RFC-004 |
| **Informative** | Guidance, infrastructure, process | RFC-003 |

---

## Status Definitions

| Status | Meaning |
|--------|---------|
| DRAFT | Under development |
| PROPOSED | Ready for review |
| APPROVED | Accepted, awaiting implementation |
| IMPLEMENTED | Applied to specification |
| REJECTED | Not accepted |
| SUPERSEDED | Replaced by another RFC |

---

## Governance

See [RFC-000](RFC-000-governance-framework.md) for:
- Document hierarchy (FORMAT_SPEC > SKILL.md > everything else)
- Versioning policy (MAJOR.MINOR.PATCH)
- RFC application checklist (§6.3)
- Validator compatibility requirements

---

## Creating a New RFC

1. Copy [RFC-TEMPLATE.md](RFC-TEMPLATE.md)
2. Assign next sequential number
3. Submit as DRAFT
4. After review → APPROVED
5. Apply per §6.3 checklist → IMPLEMENTED

---

## Current Specification Version

| Document | Version |
|----------|---------|
| CLARITY_GATE_FORMAT_SPEC.md | v2.1.0 |
| SKILL.md | v2.1.0 |

**Next planned:** v2.2.0 (RFC-002 + RFC-004)
