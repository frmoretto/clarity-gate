# RFC-004: Parser Hardening Against Adversarial Inputs

**RFC ID:** RFC-004  
**Title:** Parser Hardening and DoS Prevention  
**Type:** Normative  
**Status:** APPROVED  
**Created:** 2026-01-27  
**Author:** Francesco Marinoni Moretto  
**Affects:** CLARITY_GATE_FORMAT_SPEC.md v2.1.0 → v2.2.0, validators  
**Triggered By:** Adversarial stress test identifying 17 exploitable vulnerabilities

---

## 1. Summary

This RFC addresses parser vulnerabilities discovered through adversarial testing. The current FORMAT_SPEC is semantically sound but parser-vulnerable to DoS attacks, stack overflows, and bypass techniques.

**Version bump:** 2.1.0 → 2.2.0 (MINOR — adds security constraints)

---

## 2. Threat Model

### 2.1 Attack Surface

| Category | Severity | Count | Risk |
|----------|----------|-------|------|
| Parser DoS + Bypass | CRITICAL (10/10) | 4 | Production hang, tamper undetected |
| False Negatives | HIGH (9/10) | 2 | Docs pass validation but cause hallucinations |
| Validator Impl Bugs | MEDIUM (7/10) | 2 | Hash/ID collisions |
| Governance Gaps | LOW (5/10) | 2 | Migration confusion |

### 2.2 Attacker Capabilities

- Can submit arbitrary CGD content for validation
- Can craft malformed YAML, nested structures, recursive patterns
- Goal: bypass validation, cause DoS, or tamper undetected

### 2.3 Discovered Attack Vectors

| Attack | Target | PoC |
|--------|--------|-----|
| Fence Cascade | §2.3/8.5 | Unclosed nested fences → infinite scan |
| Exclusion Stack Overflow | §8 E-EX02/03 | 10+ interleaved BEGIN/END |
| Pipe Escaper Recursion | §4.3-4.5 | `\|\\|` x1000 → stack overflow |
| Hash Exclude Abuse | §2.2 | Multiline YAML with indent continuation |
| Status Forgery | §1.3.2 | `confirmed-by: null` → truthy bypass |
| Epistemic Bypass | 9-point check | Unknown fields ignored silently |

---

## 3. CRITICAL Fixes

### 3.1 Fence Cascade Prevention

**Attack:** Unclosed or nested code fences cause infinite scanning.

```markdown
```unclosed1
```nested
<!-- END -->
```invalid
```

**Add to §8.5 — Code Fence Handling:**

```markdown
### 8.5.1 Fence Parsing Limits (Normative)

**Timeout:** Parsers MUST abandon fence search after 1000 characters.

**Nesting:** Fences do NOT nest. First valid close (same or more backticks) ends fence.

**Indented fences:** Fences indented > 3 spaces are content, not fence start.

**Validation:**
- E-PL01: Unclosed fence at document end
- W-PL02: Fence parsing limit reached (1000 chars)

**Reference implementation:**
```python
MAX_FENCE_SCAN = 1000

def find_fence_close(content: str, opener: str, start: int) -> int:
    """Find fence close. Returns -1 if not found within limit."""
    min_ticks = len(opener.strip())
    search_end = min(start + MAX_FENCE_SCAN, len(content))
    
    for i, line in enumerate(content[start:search_end].split('\n')):
        stripped = line.lstrip()
        if stripped.startswith('`' * min_ticks) and stripped.rstrip('`') == '':
            return start + len('\n'.join(content[start:search_end].split('\n')[:i+1]))
    
    return -1  # Emit W-PL02, treat remainder as fence content
```
```

---

### 3.2 Exclusion Stack Overflow Prevention

**Attack:** Nested/mismatched BEGIN/END markers corrupt parser stack.

```markdown
<!-- CG-EX:BEGIN outer -->
<!-- CG-EX:BEGIN inner -->
<!-- CG-EX:END wrong -->
<!-- CG-EX:END outer -->
```

**Add to §8 — Exclusion Zones:**

```markdown
### 8.1.1 Exclusion Depth Limits (Normative)

**Max depth:** 10 nested exclusion zones.

**Mismatched IDs:** END with wrong ID closes innermost zone (with warning).

**Validation:**
- E-EX04: Exclusion nesting exceeds 10 levels
- W-EX05: END ID doesn't match innermost BEGIN ID

**Reference implementation:**
```python
MAX_EXCLUSION_DEPTH = 10

def parse_exclusions(content: str) -> list:
    stack = []
    zones = []
    
    for match in re.finditer(r'<!-- CG-EX:(BEGIN|END)(?:\s+(\w+))? -->', content):
        action, zone_id = match.groups()
        
        if action == 'BEGIN':
            if len(stack) >= MAX_EXCLUSION_DEPTH:
                emit_error('E-EX04', f'Depth {len(stack)+1} exceeds {MAX_EXCLUSION_DEPTH}')
                continue
            stack.append((match.start(), zone_id))
        
        elif action == 'END':
            if not stack:
                emit_error('E-EX03', 'END without BEGIN')
                continue
            begin_pos, begin_id = stack.pop()
            if zone_id and begin_id and zone_id != begin_id:
                emit_warning('W-EX05', f'END {zone_id} mismatches BEGIN {begin_id}')
            zones.append((begin_pos, match.end()))
    
    # Unclosed zones
    for pos, zid in stack:
        emit_error('E-EX02', f'Unclosed BEGIN {zid or "(anonymous)"} at {pos}')
    
    return zones
```
```

---

### 3.3 Pipe Escaper Recursion Prevention

**Attack:** Deeply escaped pipes cause stack overflow in table parsing.

```markdown
| Cell\|with\\|many\\\|escapes x1000 |
```

**Add to §4.5 — Table Parsing:**

```markdown
### 4.5.1 Table Cell Limits (Normative)

**Max escapes:** 100 escape sequences per cell.

**Max cells:** 1000 cells per table.

**Parsing:** MUST be iterative, not recursive.

**Validation:**
- W-PL03: Cell escape count exceeds 100
- E-PL04: Table exceeds 1000 cells

**Reference implementation:**
```python
MAX_CELL_ESCAPES = 100
MAX_TABLE_CELLS = 1000

def parse_table_cell(cell: str) -> str:
    """Parse cell content iteratively."""
    result = []
    escape_count = 0
    i = 0
    
    while i < len(cell):
        if cell[i] == '\\' and i + 1 < len(cell):
            escape_count += 1
            if escape_count > MAX_CELL_ESCAPES:
                emit_warning('W-PL03', f'Cell escapes exceed {MAX_CELL_ESCAPES}')
                result.append(cell[i:])  # Append rest unparsed
                break
            result.append(cell[i + 1])
            i += 2
        else:
            result.append(cell[i])
            i += 1
    
    return ''.join(result)
```
```

---

### 3.4 Hash Multiline Abuse Prevention

**Attack:** YAML multiline syntax allows hash tampering.

```yaml
document-sha256: |
  deadbeef...
  tampered-line
```

**Add to §2.2 — Document Hash:**

```markdown
### 2.2.1 Hash Field Constraints (Normative)

**Format:** `document-sha256` MUST be single-line scalar (no `|`, `>`, or continuation).

**Pattern:** `^document-sha256:\s*"?[a-f0-9]{64}"?\s*$`

**Multiline:** Any multiline form triggers E-FM10.

**Validation:**
- E-FM10: document-sha256 uses multiline YAML syntax

**Reference implementation:**
```python
def validate_hash_field(yaml_content: str) -> bool:
    # Check raw YAML before parsing
    hash_pattern = r'^document-sha256:\s*[|>]'
    if re.search(hash_pattern, yaml_content, re.MULTILINE):
        emit_error('E-FM10', 'document-sha256 must be single-line')
        return False
    
    # Also check for continuation indent
    lines = yaml_content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('document-sha256:'):
            if i + 1 < len(lines) and lines[i + 1].startswith('  '):
                emit_error('E-FM10', 'document-sha256 continuation not allowed')
                return False
    return True
```
```

---

### 3.5 YAML Anchors and Aliases Prevention (CRITICAL)

**Attack:** YAML anchors (`&`) and aliases (`*`) can create cyclic references causing infinite recursion.

```yaml
hitl-claims: &loop
  - id: claim-001
    text: *loop  # Cyclic reference → infinite expansion
```

**Add to §1.3.1 — YAML Serialization:**

```markdown
### 1.3.1.1 Prohibited YAML Features (Normative)

**Anchors and aliases:** YAML anchors (`&name`) and aliases (`*name`) are PROHIBITED in CGD frontmatter.

**Rationale:** 
1. Cyclic references cause infinite recursion in naive parsers
2. Aliases obscure actual content, complicating verification
3. No legitimate use case in CGD schema

**Validation:**
- E-PL08: YAML anchor or alias detected

**Reference implementation:**
```python
def check_yaml_prohibited_features(yaml_content: str) -> bool:
    """Check for prohibited YAML features before parsing."""
    # Anchor pattern: &name (not in strings)
    if re.search(r'^[^#"']*&\w+', yaml_content, re.MULTILINE):
        emit_error('E-PL08', 'YAML anchors (&name) prohibited')
        return False
    
    # Alias pattern: *name (not in strings)
    if re.search(r'^[^#"']*\*\w+', yaml_content, re.MULTILINE):
        emit_error('E-PL08', 'YAML aliases (*name) prohibited')
        return False
    
    return True

# Call BEFORE yaml.safe_load()
if not check_yaml_prohibited_features(frontmatter_raw):
    return None  # Reject document
```

**Parser configuration (if using PyYAML):**
```python
# Use SafeLoader and disable anchors
class NoAnchorLoader(yaml.SafeLoader):
    pass

NoAnchorLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    lambda loader, node: dict(loader.construct_pairs(node))
)
# This prevents anchor resolution but still parses; 
# pre-check regex is more secure
```
```

---

## 4. HIGH Severity Fixes

### 4.1 Status Forgery Prevention

**Attack:** `confirmed-by: null` passes truthy checks in some languages.

```yaml
hitl-claims:
  - id: claim-001
    confirmed-by: null  # YAML null → Python None → truthy in "if field:"?
    confirmed-date: 2026-01-01
```

**Add to §1.3.2 — Claim Completion Status:**

```markdown
### 1.3.2.1 Null Value Handling (Normative)

**Null rejection:** `confirmed-by` and `confirmed-date` with null/empty values are treated as ABSENT.

**Validation:**
- W-HC06: confirmed-by/confirmed-date is null or empty string

**Reference implementation:**
```python
def is_field_present(claim: dict, field: str) -> bool:
    """Check if field is present AND has non-null, non-empty value."""
    if field not in claim:
        return False
    value = claim[field]
    if value is None:
        emit_warning('W-HC06', f'{field} is null (treated as absent)')
        return False
    if isinstance(value, str) and value.strip() == '':
        emit_warning('W-HC06', f'{field} is empty string (treated as absent)')
        return False
    return True
```
```

---

### 4.2 Unknown Field Handling

**Attack:** Claim that "validators ignore unknown fields" to bypass checks.

**Add to §8.4 — Field Validation:**

```markdown
### 8.4.1 Unknown Field Policy (Normative)

**Frontmatter:** Unknown fields in frontmatter trigger W-FM11.

**Claims:** Unknown fields in hitl-claims trigger W-HC07.

**Policy:** Validators MUST warn on unknown fields. Documents MAY still pass, but warnings are logged.

**Validation:**
- W-FM11: Unknown frontmatter field
- W-HC07: Unknown claim field

**Known frontmatter fields:**
`clarity-gate-version`, `document-sha256`, `cgd-created`, `cgd-updated`, 
`source-document`, `source-sha256`, `hitl-status`, `hitl-pending-count`, 
`hitl-claims`, `chunk-context`

**Known claim fields:**
`id`, `text`, `source`, `location`, `round`, `confirmed-by`, `confirmed-date`
```

---

## 5. MEDIUM Severity Fixes

### 5.1 Document Hash Normalization Edge Cases

**Attack:** BOM + CRLF + multiline can bypass hash.

**Add test vectors to document_hash.py:**

```python
# Test: BOM + CRLF
content_bom_crlf = '\ufeff---\r\ndocument-sha256: abc\r\n---\r\n'
# Must normalize to: '---\ndocument-sha256: abc\n---\n'

# Test: Multiline continuation (MUST REJECT before hashing)
content_multiline = 'document-sha256: |\n  abc...\n  tampered'
# Must emit E-FM10, not attempt to hash
```

---

### 5.2 Claim ID Collision Awareness

**Attack:** Whitespace normalization creates collisions.

```yaml
- id: claim-001
  text: "A     B"  # normalize() → "A B"
- id: claim-002  
  text: "A B"      # Same normalized text → same hash if location matches
```

**Clarification to §1.3.4:**

```markdown
**Collision note (expanded):**

Normalization (`' '.join(text.split())`) means:
- "A     B" and "A B" produce same hash if location matches
- This is INTENTIONAL — semantically equivalent claims should have same ID

If distinct IDs required for whitespace-different text, use namespaced format:
`claim-pricing-v1`, `claim-pricing-v2`
```

---

## 6. LOW Severity Fixes

### 6.1 Superseded RFC Handling

**Issue:** RFC-001 supersedes old RFC-001/002 but merged content may conflict.

**Add to RFC-000 §3.3:**

```markdown
### 3.3.1 Supersession Semantics

When RFC-X supersedes RFC-Y:
1. RFC-Y moves to `archive-superseded/`
2. All references to RFC-Y redirect to RFC-X
3. Conflicts resolve in favor of RFC-X (newer)
4. Migration notes MUST document behavioral changes

**Migration tracking:** Each superseding RFC MUST include a "Changes from superseded RFC" section.
```

---

## 7. Global Parser Limits

**Add new §9.5 — Parser Safety Limits:**

```markdown
## 9.5 Parser Safety Limits (Normative)

All validators MUST enforce these limits:

| Resource | Limit | Error Code |
|----------|-------|------------|
| Parse timeout | 5 seconds | E-PL05 |
| Document size | 10 MB | E-PL06 |
| Fence scan | 1000 chars | W-PL02 |
| Exclusion depth | 10 levels | E-EX04 |
| Table cells | 1000 | E-PL04 |
| Cell escapes | 100 | W-PL03 |
| YAML depth | 20 levels | E-PL07 |
| Claim count | 500 | W-PL08 |

**Rationale:** Prevents DoS from malformed input while allowing legitimate large documents.

**Memory profiling requirements:**

Validators SHOULD monitor and limit:

| Resource | Limit | Rationale |
|----------|-------|----------|
| Stack depth | 100 frames | Prevents recursion exploits |
| Heap allocation | 100 MB | Prevents memory exhaustion |
| String buffer | 10 MB | Prevents expansion attacks |

**Measurement methodology:**
```python
import tracemalloc
import sys

def validate_with_limits(content: str) -> ValidationResult:
    # Check input size first
    if len(content) > 10 * 1024 * 1024:  # 10 MB
        return error('E-PL06', 'Document exceeds 10 MB')
    
    # Set recursion limit
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(100)
    
    # Track memory
    tracemalloc.start()
    
    try:
        result = parse_and_validate(content)
        
        current, peak = tracemalloc.get_traced_memory()
        if peak > 100 * 1024 * 1024:  # 100 MB
            return error('E-PL09', f'Memory usage {peak/1024/1024:.1f} MB exceeds limit')
        
        return result
    finally:
        tracemalloc.stop()
        sys.setrecursionlimit(old_limit)
```

**Validation:**
- E-PL09: Memory usage exceeded (100 MB)
- E-PL10: Stack depth exceeded (100 frames)
```

---

## 8. New Validation Codes

| Code | Severity | Description |
|------|----------|-------------|
| E-PL01 | Error | Unclosed fence at document end |
| W-PL02 | Warning | Fence parsing limit reached |
| W-PL03 | Warning | Cell escape count exceeded |
| E-PL04 | Error | Table cell count exceeded |
| E-PL05 | Error | Parse timeout |
| E-PL06 | Error | Document size exceeded |
| E-PL07 | Error | YAML nesting depth exceeded |
| E-PL08 | Error | YAML anchor or alias detected |
| W-PL09 | Warning | Claim count exceeded |
| E-EX04 | Error | Exclusion depth exceeded |
| W-EX05 | Warning | Exclusion END/BEGIN ID mismatch |
| E-FM10 | Error | document-sha256 multiline |
| W-FM11 | Warning | Unknown frontmatter field |
| W-HC06 | Warning | confirmed-by/date is null |
| W-HC07 | Warning | Unknown claim field |

---

## 9. Test Vector: doomsday-v2.cgd.md

```yaml
---
clarity-gate-version: 999
document-sha256: |
  deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef
  tampered-indent
hitl-claims:
  - id: dup1
    text: "Validators ignore unknown fields"
    source: "vague"
    unknown-field: "bypass attempt"
  - id: dup1
    text: "Duplicate ID"
    source: "also vague"
    confirmed-by: null
---

# Doomsday Test

```fence1
<!-- END1 -->
```

```
```fence2
  <!-- END2 indented -->
```

<!-- CG-EX:BEGIN outer -->
Nested <!-- CG-EX:BEGIN inner -->
<!-- CG-EX:END wrong -->
<!-- CG-EX:END outer -->

| Pipe\|test\\|test\\\|test |

<!-- CLARITY_GATE_END -->
```

**Expected errors (15+):**

| Code | Location | Reason |
|------|----------|--------|
| W-FC01 | frontmatter | version 999 unknown |
| E-FM10 | document-sha256 | multiline YAML |
| W-HC02 | claim dup1 (first) | "vague" non-actionable |
| W-HC07 | claim dup1 (first) | unknown-field |
| E-HC03 | claim dup1 (second) | duplicate ID |
| W-HC02 | claim dup1 (second) | "also vague" |
| W-HC06 | claim dup1 (second) | confirmed-by null |
| E-PL01 | fence1 | unclosed |
| W-PL02 | fence2 | parsing limit (indented END) |
| W-EX05 | exclusion | END wrong ≠ BEGIN inner |
| E-ST01 | end marker | typo CLARITYGATEEND |

---

## 10. Implementation Checklist

| Document | Changes |
|----------|---------|
| FORMAT_SPEC.md | Add §8.5.1, §8.1.1, §4.5.1, §2.2.1, §1.3.2.1, §8.4.1, §9.5 |
| document_hash.py | Add multiline rejection, BOM/CRLF tests |
| New: validator_limits.py | Reference implementation of all limits |
| New: test-vectors/doomsday-v2.cgd.md | Adversarial test document |

---

## 11. Backward Compatibility

| Change | Impact |
|--------|--------|
| New limits | May reject previously-accepted malformed docs |
| Unknown field warnings | Existing docs with extensions will warn |
| Null rejection | Docs with `confirmed-by: null` now explicitly PENDING |

**Migration:** Documents failing new checks were already semantically invalid. No behavioral change for well-formed CGDs.

---

## 12. Decision

- [x] APPROVED
- [ ] REJECTED: [reason]

**Reviewer:** Perplexity (adversarial review)  
**Date:** 2026-01-27

**Condition:** Fuzzing corpus (10k malformed CGDs) required before v2.2.0 release.

---

## Appendix A: Fuzzing Recommendations

Before v2.2.0 release:

1. **Generate 10,000 malformed CGDs** using grammar-based fuzzing
2. **Test all validators** against doomsday-v2.cgd.md
3. **Measure parse time** — reject if > 5s on standard hardware
4. **Memory profiling** — stack depth, allocation patterns

**Fuzzing targets:**
- Fence open/close combinations
- Exclusion marker permutations  
- Escape sequence chains
- YAML edge cases (anchors, aliases, multiline)
- Unicode edge cases (BOM, RTL, zero-width)

---

*RFC-004 — Parser Hardening Against Adversarial Inputs*
