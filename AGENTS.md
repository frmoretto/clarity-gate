# AGENTS.md - Clarity Gate

> Universal discovery file for AI agents and coding assistants.

## What This Repository Does

**Clarity Gate** is a pre-ingestion verification system for epistemic quality in RAG systems. It ensures documents are properly qualified (claims marked as projections, hypotheses labeled, assumptions explicit) before they enter knowledge bases.

**Core Question:** "If another LLM reads this document, will it mistake assumptions for facts?"

## Quick Start for Agents

### 1. Load the Skill

The main skill file is at: `skills/clarity-gate/SKILL.md`

```
Read: skills/clarity-gate/SKILL.md
```

### 2. Understand the Specifications

| Document | Purpose | Location |
|----------|---------|----------|
| Format Spec | Unified CGD/SOT specification (v2.1) | `docs/CLARITY_GATE_FORMAT_SPEC.md` |
| Procedures | Verification workflows | `docs/CLARITY_GATE_PROCEDURES.md` |

### 3. Trigger Phrases

Use any of these to activate Clarity Gate:
- "clarity gate"
- "check for hallucination risks"
- "can an LLM read this safely"
- "review for equivocation"
- "verify document clarity"
- "pre-ingestion check"

## Repository Structure

```
clarity-gate/
├── skills/clarity-gate/      # Canonical skill (agentskills.io compliant)
│   └── SKILL.md              # v2.1 skill definition
├── .claude/skills/clarity-gate/  # Claude.ai format (metadata wrapper)
│   └── SKILL.md
├── .codex/skills/clarity-gate/   # OpenAI Codex (agentskills.io format)
│   └── SKILL.md
├── .github/skills/clarity-gate/  # GitHub Copilot (agentskills.io format)
│   └── SKILL.md
├── docs/                     # Specifications (v2.1)
│   ├── CLARITY_GATE_FORMAT_SPEC.md   # Unified format spec
│   ├── CLARITY_GATE_PROCEDURES.md    # Verification procedures
│   ├── ARCHITECTURE.md       # 9-point verification system
│   └── ...                   # Supporting docs
├── examples/                 # Usage examples
├── .claude-plugin/           # Claude Code marketplace
└── AGENTS.md                 # This file
```

## Platform-Specific Locations

| Platform | Skill Location | Format |
|----------|----------------|--------|
| Claude Desktop/Code | `.claude/skills/clarity-gate/` | Minimal (`name`, `description` only) |
| OpenAI Codex | `.codex/skills/clarity-gate/` | agentskills.io (full) |
| GitHub Copilot | `.github/skills/clarity-gate/` | agentskills.io (full) |
| Universal (canonical) | `skills/clarity-gate/` | agentskills.io (full) |

Each platform directory contains a full copy of SKILL.md with platform-appropriate frontmatter.

## Key Concepts

### The 9 Verification Points

1. **Hypothesis vs Fact Labeling** - Are claims marked as validated or hypothetical?
2. **Uncertainty Marker Enforcement** - Do projections have qualifiers?
3. **Assumption Visibility** - Are implicit assumptions explicit?
4. **Authoritative-Looking Unvalidated Data** - Could tables be mistaken for empirical data?
5. **Data Consistency** - Do numbers match across sections?
6. **Implicit Causation** - Are causal claims evidence-backed?
7. **Future State as Present** - Are plans written as achievements?
8. **Temporal Coherence** - Are dates internally consistent?
9. **Externally Verifiable Claims** - Are specific numbers flagged for verification?

### Output Format

| Format | Extension | Purpose |
|--------|-----------|---------|
| CGD | `.cgd.md` | Clarity-Gated Document (unified format) |

> **Note:** v2.1 uses a single `.cgd.md` extension. SOT is now a CGD with an optional `tier:` block in YAML frontmatter.

### Two-Round HITL Verification

- **Round A:** Derived data confirmation (quick scan)
- **Round B:** True HITL verification (actual verification needed)

## For Validator Implementers

If building a validator, read:
1. `docs/CLARITY_GATE_FORMAT_SPEC.md` - Complete format and rule definitions

Validator packages:
- npm: `clarity-gate` v1.0.0 — Validates v1.x spec (validation only); v2.1 update planned
- PyPI: `clarity-gate` v1.0.0 — Validates v1.x spec (validation only); v2.1 update planned

> **Note:** Separate `cgd-validator` and `sot-validator` packages are deprecated in v2.1.

## Related Projects

| Project | Purpose | URL |
|---------|---------|-----|
| Source of Truth Creator | Create epistemically calibrated docs | github.com/frmoretto/source-of-truth-creator |
| Stream Coding | Documentation-first methodology | github.com/frmoretto/stream-coding |
| ArXiParse | Scientific paper verification | arxiparse.org |

## License

CC-BY-4.0

## Author

Francesco Marinoni Moretto
