# Changelog

All notable changes to Clarity Gate specifications and tools.

Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## Specification Documents

| Document | Current | Description |
|----------|---------|-------------|
| [CLARITY_GATE_FORMAT_SPEC.md](./docs/CLARITY_GATE_FORMAT_SPEC.md) | 2.1 | Unified format specification |
| [CLARITY_GATE_PROCEDURES.md](./docs/CLARITY_GATE_PROCEDURES.md) | 1.0 | Verification procedures |

---

## [2.1.2] - February 2026

### Fixed
- **Documentation Consistency** — Standardized validation code notation from `W-HC01-02` to `W-HC01, W-HC02` across all documentation for 100% alignment with FORMAT_SPEC

---

## [2.1.1] - January 2026

### Fixed
- **Critical:** `document_hash.py` missing canonicalization algorithm (§2.2-2.4)
- **Documentation:** Validation codes updated to match FORMAT_SPEC (W-HC01, W-HC02, E-SC06)
- **Documentation:** Claim ID regex patterns specified per approach (hash/sequential/semantic)

---

## [2.1] - January 2026

**RFC-001 Applied:** Clarifications for HITL claim handling.

### Added
- **Claim Completion Status** — PENDING/VERIFIED determined by field presence (no explicit status field)
- **Source Field Semantics** — Actionable source (PENDING) vs. what-was-found (VERIFIED)
- **Claim ID Format Guidance** — Hash-based IDs preferred with collision analysis
- **Body Structure Requirements** — HITL Verification Record section mandatory when claims exist
- **New Validation Codes** — E-ST10, W-ST11, W-HC01, W-HC02, E-SC06 (FORMAT_SPEC); E-TB01-07 (SOT validation)
- **Bundled Scripts** — `claim_id.py`, `document_hash.py` with full §2.2-2.4 canonicalization
- **Validation Codes Reference** — Comprehensive table added to SKILL.md documenting all error/warning codes

### Updated
- FORMAT_SPEC: v2.0 → v2.1
- SKILL.md: v2.0.0 → v2.1.0

---

## [2.0] - January 2026

**BREAKING CHANGE:** Unified CGD/SOT format.

### Format Unification
- **Single file extension:** `.cgd.md` for everything (`.sot.md` deprecated)
- **SOT = CGD + tier: block:** SOT is now a CGD with optional `tier:` block in YAML frontmatter
- **One validator:** Single `clarity-gate` package handles both formats
- **promote/demote commands:** Add/remove `tier:` block instead of format conversion

### Key Changes
- Unified spec: `CLARITY_GATE_FORMAT_SPEC.md` replaces 4-file suite
- New procedures doc: `CLARITY_GATE_PROCEDURES.md` for workflows
- `tier.queue` and `tier.claims` for systematic claim processing
- Claim IDs enable tracking across verification rounds

### Breaking Changes
- `.sot.md` extension deprecated (use `.cgd.md`)
- Separate validators (`sot-validator`, `cgd-validator`) deprecated
- 4-file spec suite archived (CGD_FORMAT, SOT_FORMAT, VALIDATOR_REFERENCE, VALIDATOR_IMPL_GUIDE)

### Migration
- Rename `.sot.md` files to `.cgd.md`
- Add `tier:` block to YAML frontmatter for SOT behavior
- Use `clarity-gate` package instead of separate validators

> **Note:** v1.1 and v1.2 were internal development iterations (Jan 10-12, 2026) that were never publicly released. See archive for details.

---

## [1.0] - November 2025

- Initial specification as FILE_FORMAT_SPEC.md
- Separate `.cgd.md` and `.sot.md` formats
- Published as npm/PyPI packages v0.1.1
- Basic validation rules

---

## Validator Package

| Package | npm | PyPI | Spec Version |
|---------|-----|------|--------------|
| clarity-gate | [npm](https://www.npmjs.com/package/clarity-gate) | [PyPI](https://pypi.org/project/clarity-gate/) | 2.1 |

> **Deprecated:** `sot-validator`, `cgd-validator`, `sot-verify`, `cgd-verify` are superseded by the unified `clarity-gate` package.

---

## SKILL.md Versions

| Version | Date | Key Changes |
|---------|------|-------------|
| v2.1.2 | Feb 2, 2026 | Documentation consistency (validation code notation) |
| v2.1.1 | Jan 28, 2026 | Critical bugfixes (document_hash.py canonicalization) |
| v2.1.0 | Jan 27, 2026 | RFC-001 clarifications, bundled scripts |
| v2.0.0 | Jan 13, 2026 | Unified format spec v2.0, single `.cgd.md` extension |
| v1.6 | Dec 31, 2025 | Two-Round HITL (Round A + Round B) |
| v1.5 | Dec 28, 2025 | Points 8-9: Temporal Coherence, Externally Verifiable Claims |
| v1.4 | Dec 23, 2025 | Annotation offer + CGD output mode |
| v1.3 | Dec 2025 | Restructured into Epistemic (1-4) + Data Quality (5-7) |
| v1.2 | Dec 2025 | Added Source of Truth Template |
| v1.1 | Dec 2025 | Added HITL Fact Verification (MANDATORY) |
| v1.0 | Nov 2025 | Initial release with 6-point verification |
