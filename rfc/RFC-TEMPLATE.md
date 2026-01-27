# RFC-NNN: [Title]

**RFC ID:** RFC-NNN  
**Title:** [Descriptive Title]  
**Type:** Normative | Informative  
**Status:** DRAFT  
**Created:** YYYY-MM-DD  
**Author:** [Name]  
**Affects:** [Documents and versions, e.g., "CLARITY_GATE_FORMAT_SPEC.md v2.1 → v2.2"]  

---

## 1. Summary

[2-3 sentences describing the change]

---

## 2. Problem Statement

### 2.1 The Gap

[What's broken or missing?]

### 2.2 Failure Modes

[What goes wrong without this change?]

| Failure Mode | Example | Consequence |
|--------------|---------|-------------|
| | | |

---

## 3. Proposal

### 3.1 Overview

[High-level description of the change]

### 3.2 Specification Changes

[Detailed changes to FORMAT_SPEC, SKILL.md, etc.]

### 3.3 New Validation Codes (if any)

| Code | Severity | Message | Trigger |
|------|----------|---------|---------|
| | | | |

---

## 4. Alternatives Considered

| Alternative | Pros | Cons | Why Not |
|-------------|------|------|---------|
| | | | |

---

## 5. Migration

### 5.1 Breaking Changes

[List any breaking changes, or "None"]

### 5.2 Migration Path

[How do users update existing CGDs?]

---

## 6. Implementation Checklist

Per RFC-000 §6.3:

- [ ] Update FORMAT_SPEC (version bump)
- [ ] Update SKILL.md (version bump + new sections)
- [ ] Move scripts to `skills/*/scripts/`
- [ ] Move test vectors to appropriate location
- [ ] Update CHANGELOG.md
- [ ] Update README.md
- [ ] Update ARCHITECTURE.md
- [ ] Rebuild dist package

---

## 7. Decision

- [ ] APPROVED
- [ ] REJECTED: [reason]

**Reviewer:** [Name]  
**Date:** YYYY-MM-DD

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | YYYY-MM-DD | Initial draft |
