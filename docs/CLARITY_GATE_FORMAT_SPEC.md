# Clarity Gate Format Specification v2.1.0

**Date:** 2026-01-27
**Status:** FINAL — Implementation Ready
**License:** CC BY 4.0

---

## Executive Summary

Clarity Gate is a pre-ingestion verification system for epistemic quality in RAG systems. This specification defines the document format, CLI behavior, and validation rules.

**Core Question:** "If another LLM reads this document, will it mistake assumptions for facts?"

**Critical Limitation:** Clarity Gate verifies FORM, not TRUTH. It checks whether claims are properly marked — it cannot verify if claims are actually true. HITL verification is mandatory.

---

## 1. Document Format

### 1.1 File Extension

All Clarity Gate documents use **`.cgd.md`**. No exceptions.

### 1.2 Document Structure

```markdown
---
<YAML frontmatter>
---

<Markdown body>

<!-- CLARITY_GATE_END -->
Clarity Gate: <status> | <hitl-status>
```

**Note:** End marker uses required HTML comment prefix for unambiguous detection.

### 1.2.1 Body Structure Requirements (Normative)

Documents with non-empty `hitl-claims` MUST include:

| Element | Requirement |
|---------|-------------|
| `## HITL Verification Record` section | MUST appear before end marker |
| Round A subsection | MUST appear if any Round A claims exist |
| Round B subsection | MUST appear if any Round B claims exist |

**Format:**

```markdown
## HITL Verification Record

### Round A: Derived Data Confirmation
- [claim summary] ([source]) ✓

### Round B: True HITL Verification
| # | Claim | Status | Verified By | Date |
|---|-------|--------|-------------|------|
| 1 | [claim text] | ✓ Confirmed | [name] | [date] |
| 2 | [claim text] | ⏳ Pending | — | — |
```

**Validation:**
- E-ST10: Missing `## HITL Verification Record` when `hitl-claims` non-empty
- W-ST11: Table rows don't match `hitl-claims` count

### 1.3 YAML Schema

```yaml
---
# === REQUIRED FIELDS ===
clarity-gate-version: 2.0
processed-date: 2026-01-12              # Format: YYYY-MM-DD (ISO 8601 date)
processed-by: Claude                    # Claude | automated | <name>
clarity-status: CLEAR                   # CLEAR | UNCLEAR
hitl-status: REVIEWED                   # PENDING | REVIEWED | REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-9                      # Format: N or N-M where N,M in 1-9
document-sha256: <64-char lowercase hex>

# === HITL CLAIMS (may be empty list) ===
hitl-claims:
  - id: claim-75fb137a                  # Stable hash-based ID
    text: "Base price is $99/mo"        # Full claim text
    value: "$99/mo"                     # Extracted value (optional)
    source: "Pricing page"              # Source of verification
    location: "api-pricing/1"           # heading_slug/ordinal
    round: B                            # A (interactive) | B (CLI)
    confirmed-by: Maria                 # OPTIONAL: may be omitted for automated verification
    confirmed-date: 2026-01-12

# === COMPUTED FIELDS (written by validators) ===
rag-ingestable: true                    # Computed: see §9.1
exclusions-coverage: 0.0                # Computed: see §9.2

# === EXCLUSION FIELDS (when REVIEWED_WITH_EXCEPTIONS) ===
exceptions-reason: "Legacy OAuth; no SME available"
exceptions-ids:
  - auth-legacy-1

# === TIER BLOCK (optional — present only for SOT) ===
tier:
  level: SOT
  owner: Platform Team
  version: 1.0
  promoted-date: 2026-01-12
  promoted-by: Maria
---
```

### 1.3.1 YAML Serialization and Editing (Normative)

To ensure Python and Node.js implementations produce interoperable outputs, tools MUST follow these rules when writing `.cgd.md` files:

1. **Lossless editing for existing files:** Commands that modify an existing document (e.g., `verify` autofix, `process`, `promote`, `demote`, `apply-hitl`) MUST preserve the original YAML frontmatter text byte-for-byte except for:
   - The exact keys the command is defined to change (e.g., `document-sha256`, `processed-date`, `tier`, `hitl-claims` edits)
   - Any new blocks the command is defined to insert (e.g., `tier:` on promote)
   - **Computed fields:** `document-sha256`, `rag-ingestable`, `exclusions-coverage` (see §9)

   Tools MUST NOT re-serialize or reorder YAML keys globally, must not change quoting style, and must not wrap lines.

2. **Canonical output for newly created files:** If a tool creates a new document from scratch, it MUST emit YAML in the same key order as shown in the schema example, using:
   - Two-space indentation
   - LF line endings (`\n`)
   - No tabs in YAML
   - No line-wrapping

3. **Tier block placement:** When adding a `tier:` block (promote), tools MUST insert it immediately before the closing YAML delimiter line (`---`) and MUST use two-space indentation for nested keys.

### 1.3.2 Claim Completion Status (Normative)

Completion status is determined by field PRESENCE, not a status field:

| State | `confirmed-by` | `confirmed-date` | Meaning |
|-------|----------------|------------------|--------|
| **PENDING** | Absent | Absent | Awaiting verification |
| **VERIFIED** | Present | Present | Human confirmed |

**Rules:**
1. Both `confirmed-by` AND `confirmed-date` MUST be present for VERIFIED
2. `round` indicates verification TIER (A or B), NOT completion
3. `hitl-pending-count` MUST equal count of claims lacking `confirmed-by`

**Validation:**
- W-HC01: Has `confirmed-by` but not `confirmed-date` (or vice versa)
- E-SC06: `hitl-pending-count` doesn't match actual pending count

**Rationale:** Presence/absence semantics prevent sync errors between a `status` field and actual verification data.

**Limitation:** This pattern blocks adding third states (e.g., "rejected", "machine-verified"). If needed in future, will require MAJOR version bump.

### 1.3.3 Source Field Semantics (Normative)

The `source` field serves different purposes based on claim state:

| State | `source` Contains | Example |
|-------|-------------------|--------|
| **PENDING** | Where/how to verify (actionable) | `"Check example.com/pricing"` |
| **VERIFIED** | What was found (record) | `"Pricing page, verified 2026-01-12"` |

**Actionable source requirements (PENDING claims):**
- MUST contain at least one of: URL, document name, person name
- MUST NOT be vague terms only ("industry reports", "various sources")

**Validation:**
- W-HC02: PENDING claim has non-actionable source

**Vague (triggers W-HC02):**
```yaml
source: "industry benchmarks"     # No URL, no doc name, no person
source: "various reports"         # Unverifiable
source: "research"                # Too generic
```

**Actionable (no warning):**
```yaml
source: "Check example.com/pricing"
source: "Q3 Report page 12"
source: "Ask Maria in Finance"
source: "SIA Staffing Report 2025, Table 3.2"
```

**W-HC02 Detection Heuristics (Informative):**

Validators SHOULD use the following heuristics:

```python
import re

def is_actionable_source(source: str) -> bool:
    source_lower = source.lower()
    # URL pattern
    if re.search(r'https?://|www\.|\w+\.(com|org|net|io|ai|gov|edu)', source):
        return True
    # Document reference
    if re.search(r'(page|p\.|section|table|fig|appendix)\s*[\d\.]+', source_lower):
        return True
    # Named document + year
    if re.search(r'(report|guide|spec|manual)\s+(\d{4}|v\d)', source_lower):
        return True
    # Person reference
    if re.search(r'(ask|contact|check with)\s+[A-Z][a-z]+', source):
        return True
    # File path
    if re.search(r'[\w-]+\.(pdf|docx?|xlsx?|csv|md)', source_lower):
        return True
    return False

VAGUE_PATTERNS = [r'^\s*(industry|various|multiple)\s+(reports?|sources?)\s*

### 1.4 Two Document States

| State | `tier:` block | Structured table | Use case |
|-------|---------------|------------------|----------|
| **CGD** | Absent | Optional | Verified text, safe for RAG |
| **SOT** | Present | Required | Canonical reference, machine-extractable |

---

## 2. Hash Specification

### 2.1 Scope

`document-sha256` covers YAML frontmatter + Markdown body, **excluding the hash line itself**.

#### 2.1.1 Hash Input Window (Normative)

Implementations MUST compute `document-sha256` over the exact substring of the document defined as:

- **Start boundary:** the first byte immediately after the opening YAML delimiter line `---` plus its trailing newline (`---\n`).
- **End boundary:** the first byte immediately before the first occurrence of the end marker string `<!-- CLARITY_GATE_END -->`.

Therefore, the hash input includes:

- YAML frontmatter content (excluding the opening `---` line)
- The closing YAML delimiter line (`---`) and everything after it up to (but not including) the end marker

The hash input excludes:

- The opening YAML delimiter line (`---`)
- The end marker line and all bytes after (and including) the first end marker occurrence

### 2.2 Hash Exclusion Rule

**CRITICAL:** The SHA-256 calculation MUST exclude the `document-sha256` field, including:
- The line containing `document-sha256:`
- Any indented continuation lines (for multiline YAML values)

**Regex pattern:** `^\s*document-sha256:.*$`

**Frontmatter-only scope (Normative):** The exclusion rule MUST apply only within the YAML frontmatter region (between the opening `---` line and the closing `---` line). Implementations MUST NOT remove or alter any `document-sha256:` text that appears in the Markdown body.

**Multiline continuation (Normative):** After excluding the key line matching `^\s*document-sha256:`, implementations MUST also exclude subsequent lines while BOTH conditions hold:

1. The parser is still within YAML frontmatter, and
2. The line's indentation is strictly greater than the indentation of the `document-sha256:` key line.

Continuation exclusion ends when indentation returns to less-than-or-equal to the key indentation, or when the closing `---` delimiter is reached.

**Exclusion blocks and hash (Normative):** Exclusion blocks (§8) do NOT affect hash computation. The `document-sha256` is computed over the full hash window including exclusion markers and content inside exclusion blocks. Rationale: The hash is an integrity mechanism; excluding quarantined regions would allow undetected tampering of exactly the risky content.

**Algorithm:**

```python
import re
import hashlib

def compute_hash(file_content: str) -> str:
    # 0. Pre-normalize for boundary detection (CRLF/BOM).
    #    Canonicalization (§2.4) is applied later, but we need stable slicing indices.
    working = file_content
    if working.startswith('\ufeff'):
        working = working[1:]
    working = working.replace('\r\n', '\n')

    # 1. Extract content between the opening YAML delimiter line and the end marker.
    start = working.index('---\n') + len('---\n')
    end = working.index('<!-- CLARITY_GATE_END -->')
    hashable = working[start:end]
    
    # 2. Remove document-sha256 line(s) — YAML frontmatter only
    lines = hashable.split('\n')
    filtered = []
    skip_multiline = False
    hash_indent = 0
    in_frontmatter = True
    
    for line in lines:
        # Detect end of YAML frontmatter
        if in_frontmatter and line.strip() == '---':
            in_frontmatter = False

        # Check if this is the hash line
        if in_frontmatter and re.match(r'^\s*document-sha256:', line):
            skip_multiline = True
            hash_indent = len(line) - len(line.lstrip())
            continue
        
        # If we're skipping multiline, check if this is a continuation
        if skip_multiline:
            current_indent = len(line) - len(line.lstrip())
            if in_frontmatter and current_indent > hash_indent:
                continue
            skip_multiline = False
        
        filtered.append(line)
    
    hashable = '\n'.join(filtered)
    
    # 3. Canonicalize
    hashable = canonicalize(hashable)
    
    # 4. Compute
    return hashlib.sha256(hashable.encode('utf-8')).hexdigest()
```

### 2.3 End Marker Detection

**The end boundary is the HTML comment `<!-- CLARITY_GATE_END -->`**, not a bare `---`.

This solves the ambiguity when `---` (horizontal rules) appear in the document body.

**Detection rule (Normative):** The end marker is recognized when:

1. The marker string `<!-- CLARITY_GATE_END -->` appears in the document, AND
2. The marker is **outside any fenced code block** (using §8.5 fence-tracking logic)

Markers inside fenced code blocks (`` ``` `` or `~~~`) MUST be ignored. This enables documentation about Clarity Gate itself to include the marker string in code examples without terminating the document prematurely ("Quine Protection").

**Implementation:** Parsers MUST track fence state while scanning for the marker, using the same fence detection rules as §8.5 (Exclusion Blocks in Fenced Code).

### 2.4 Canonicalization

Before hashing, normalize:

1. **Line endings:** CRLF → LF
2. **Trailing whitespace:** Remove per line
3. **Consecutive newlines:** Collapse 3+ newlines to 2
4. **Final newline:** Exactly one trailing LF
5. **Encoding:** UTF-8 NFC normalization
6. **BOM:** Remove if present
7. **Tabs:** Preserve (do not convert)
8. **Leading whitespace:** Preserve (significant in code blocks)

#### 2.4.1 Canonicalization Scope (Normative)

The hash protects the **canonical byte sequence**, not rendered Markdown semantics. Specifically:

- Trailing whitespace (including Markdown hard line breaks via `  \n`) is stripped
- 3+ consecutive newlines collapse to 2

Documents with different rendered appearance MAY share the same hash if they differ only in these canonicalized elements. This is intentional: LLM tokenizers normalize whitespace similarly, so these variations do not affect RAG ingestion semantics. Cross-platform hash stability requires stripping editor-introduced whitespace variations.

### 2.5 Hash Computation Order (Initial Creation)

1. Generate complete YAML with `document-sha256: PENDING`
2. Generate body content
3. Compute hash (excluding `document-sha256:` line)
4. Replace `PENDING` with actual hash
5. Verify by recomputing (must match)

### 2.6 When Hash Changes

| Action | Hash changes? | Reason |
|--------|---------------|--------|
| Process (add markers) | Yes | Body modified |
| Promote | Yes | YAML modified (tier block) |
| Demote | Yes | YAML + body modified |
| Edit content | Yes | Body modified |
| Edit YAML (except hash) | Yes | YAML modified |

### 2.7 End Marker Uniqueness (Normative)

The document MUST contain exactly one occurrence of `<!-- CLARITY_GATE_END -->`.

After the `Clarity Gate: <status> | <hitl-status>` line, only optional trailing whitespace and a single trailing newline are permitted until EOF.

| Code | Rule | Severity |
|------|------|----------|
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

---

## 3. SOT Requirements

### 3.1 Structured Claims Table

SOT documents MUST contain a `## Verified Claims` section with a valid table.

The `## Verified Claims` section and its table MUST be outside any exclusion block (§8). Content inside exclusion blocks is ignored for the purpose of satisfying SOT structural requirements.

### 3.2 Table Validation Rules

| Rule | Requirement | Error |
|------|-------------|-------|
| V1 | Section header matches `## Verified Claims` (case-insensitive, whitespace-normalized) | `E-TB01` |
| V2 | Table has at least 1 data row | `E-TB02` |
| V3 | Required columns present: Claim, Value, Source, Verified | `E-TB03` |
| V4 | Column order: Claim MUST be first, Verified MUST be last | `E-TB04` |
| V5 | Middle columns (Value, Source) may be in any order | (not an error) |
| V6 | Extra columns allowed anywhere except before Claim or after Verified | (not an error) |
| V7 | No empty cells in required columns (whitespace-only = empty, `-` = empty) | `E-TB05` |
| V8 | Verified column is valid date (YYYY-MM-DD, validated for real dates) | `E-TB06` |
| V9 | Verified date not in future (with 24h grace period) | `E-TB07` |

### 3.3 Date Validation Details

**Valid dates only:**
- `2026-02-29` → INVALID (2026 is not a leap year)
- `2026-04-31` → INVALID (April has 30 days)
- `2026-13-01` → INVALID (no month 13)

**Future check with timezone grace:**

To accommodate global users, the future date check allows a **24-hour grace period**:

```python
from datetime import datetime, timedelta, timezone

def is_future_date(date_str: str) -> bool:
    verified_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    grace_boundary = (datetime.now(timezone.utc) + timedelta(hours=24)).date()
    return verified_date > grace_boundary
```

### 3.4 Empty Cell Definition

A cell is considered **empty** if it contains:
- Only whitespace (spaces, tabs)
- Exactly the character `-` (dash placeholder)
- Nothing at all

### 3.5 Column Matching Examples

**Valid:**
```
| Claim | Value | Source | Verified |          ✓ Standard
| Claim | Source | Value | Verified |          ✓ Middle swapped
| Claim | Notes | Value | Source | Verified |  ✓ Extra column in middle
```

**Invalid:**
```
| Value | Claim | Source | Verified |          ✗ Claim not first
| Claim | Value | Source | Notes |             ✗ Verified not last
```

---

## 4. Table Auto-Generation

### 4.1 When Auto-Generation Occurs

`promote` auto-generates a table when:
- Document has confirmed claims in `hitl-claims`
- No `## Verified Claims` section exists
- No archived table exists

### 4.2 Generation Algorithm

```python
def generate_table(hitl_claims: list) -> str:
    rows = []
    for claim in hitl_claims:
        rows.append({
            'Claim': escape_pipes(claim['text']),
            'Value': escape_pipes(claim.get('value', '-')),
            'Source': escape_pipes(claim.get('source', 'HITL Verification')),
            'Verified': claim['confirmed-date']
        })
    
    return format_table(rows)
```

### 4.3 Pipe Character Escaping

**CRITICAL:** When populating table cells, implementations MUST escape **unescaped** pipe characters (`|`) as `\|`.

**Idempotency:** Already-escaped pipes (`\|`) must NOT be double-escaped to `\\|`.

**Escaped definition (Normative):** A pipe character (`|`) is considered escaped if and only if it is immediately preceded by an odd number of consecutive backslashes.

```python
def escape_pipes(text: str) -> str:
    """Escape unescaped pipe characters for Markdown table cells.
    
    Idempotent: already-escaped pipes (\\|) are not double-escaped.
    """
    result = []
    i = 0
    while i < len(text):
        if text[i] == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and text[j] == '\\':
                backslashes += 1
                j -= 1
            if backslashes % 2 == 1:
                result.append('|')
            else:
                result.append('\\|')
        else:
            result.append(text[i])
        i += 1
    return ''.join(result)
```

### 4.4 Claim/Value Column Population

The `Claim` column receives the **full claim text**. 

The `Value` column is populated from:
1. The `value` field in YAML (if present)
2. Otherwise, a dash (`-`)

**Do NOT attempt to parse claim text into Claim/Value.** This would require NLP and produce inconsistent results.

### 4.5 Table Row Parsing (Normative)

To ensure Python and Node.js implementations parse Markdown tables identically, implementations MUST split table rows into cells using the algorithm below.

**Algorithm (Normative):**

1. Given a single table row string (one line), remove a single leading `|` if present.
2. Remove a single trailing `|` if present.
3. Split the remaining string on `|` characters that are **NOT escaped**, where "escaped" uses the **odd backslash parity** rule from §4.3.
4. Trim leading/trailing whitespace from each resulting cell.

```python
def split_table_row(row: str) -> list[str]:
    if row.startswith('|'):
        row = row[1:]
    if row.endswith('|'):
        row = row[:-1]

    cells = []
    buf = []

    i = 0
    while i < len(row):
        ch = row[i]
        if ch == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and row[j] == '\\':
                backslashes += 1
                j -= 1

            if backslashes % 2 == 1:
                buf.append('|')
            else:
                cells.append(''.join(buf).strip())
                buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    cells.append(''.join(buf).strip())
    return cells
```

---

## 5. Claim ID Specification

### 5.1 ID Format

```
claim-<8-char-hex>
```

Example: `claim-75fb137a`

### 5.2 ID Computation

```python
def compute_claim_id(text: str, location: str) -> str:
    input_string = f"{text}|{location}"
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()
    return f"claim-{hash_hex[:8]}"
```

### 5.3 Location Context Format

`location` is a stable reference: `heading_slug/ordinal`

**Format:** `<nearest_heading_slug>/<ordinal_within_section>`

### 5.4 Slug Algorithm (ASCII-Safe Slugification)

**IMPORTANT:** This is **NOT** GitHub Flavored Markdown (GFM) slugification. GFM preserves non-ASCII characters; this algorithm strips them for maximum cross-platform compatibility.

**ASCII-Safe Slug Rules:**
1. Convert to lowercase
2. Remove all characters except ASCII alphanumerics (`a-z`, `0-9`), spaces, and hyphens
3. Replace spaces with hyphens
4. Collapse consecutive hyphens to single hyphen
5. Remove leading/trailing hyphens

```python
import re

def ascii_safe_slugify(heading: str) -> str:
    slug = heading.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug
```

**Special case — empty slug:** If a heading produces an empty slug (all non-ASCII), use `section-<ordinal>` where ordinal is the heading's position in the document (1-indexed).

**Special case — duplicate slugs (Normative):** If two or more headings produce the same slug, implementations MUST disambiguate by appending `-2`, `-3`, ... in document order.

**Special case — root:** Claims before any heading use `root` as the slug.

### 5.5 Ordinal Assignment

Ordinals are 1-indexed within each section.

```markdown
## Pricing

First claim here.     → location: pricing/1
Second claim here.    → location: pricing/2

## Features

First claim here.     → location: features/1
```

### 5.6 Claim Matching for Queue Apply

**Matching is by ID, not text.**

If ID matches but text differs slightly (whitespace, punctuation):
```
WARNING: Claim text differs from queue. Applying anyway.
  Queue: "Base price is $99/mo"
  Doc:   "Base price is $99/mo."
```

---

## 6. Promote Command

### 6.1 Basic Usage

```bash
clarity-gate promote doc.cgd.md --owner "Team" --version 1.0
```

### 6.2 Behavior

```
1. Validate document is CGD (no tier block)
2. Check for existing table:
   a. If ## Verified Claims exists → validate and proceed
   b. If ## Claims (Archived from SOT) exists → restore
   c. If neither → auto-generate from hitl-claims
3. If no claims and no table → ERROR: E-PM01
4. Add tier block to YAML
5. Recompute document-sha256
6. Update processed-date
```

### 6.3 Re-Promotion (Archived Table Restoration)

Detection uses **comment ID**, not header text:

```markdown
<!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-10 -->
## Claims (Archived from SOT)
```

---

## 7. Demote Command

### 7.1 Basic Usage

```bash
clarity-gate demote doc.cgd.md --reason "Superseded by v2"
```

### 7.2 Behavior

1. Validate document is SOT (has tier block)
2. If no tier block → WARNING, exit 0 (no-op)
3. Remove tier block from YAML
4. Find `## Verified Claims` section
5. Generate unique archive ID: `arch-<8-char-hex>`
6. Add archive comment with ID:
   ```markdown
   <!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-12, reason="Superseded by v2" -->
   ## Claims (Archived from SOT)
   ```
7. Recompute document-sha256
8. Update processed-date

### 7.3 Archive Comment Format

```
<!-- CLARITY_GATE_ARCHIVED: id=<id>, date=<ISO-date>, reason="<escaped-reason>" -->
```

**Escaping in reason:** Replace `"` with `&quot;` and `>` with `&gt;`.

---

## 8. Exclusion Blocks

### 8.1 Purpose

Exclusion Blocks mark document regions with unresolved ambiguity that are **unsafe for RAG ingestion**. They allow a document to be `CLEAR` overall while quarantining specific sections that couldn't be resolved.

**Use case:** Legacy documentation where no SME is available, or third-party content that can't be modified.

**Semantic note:** A document may have `clarity-status: CLEAR` with exclusion blocks present. This means "all non-excluded content is epistemically clear." However, such documents are still non-ingestable (`rag-ingestable: false`) by design. This is a "human-readable but quarantined" state.

### 8.2 Syntax

```markdown
<!-- CG-EXCLUSION:BEGIN id=<id> -->
Content with unresolved ambiguity...
<!-- CG-EXCLUSION:END id=<id> -->
```

#### 8.2.1 Marker Grammar (Normative)

Exclusion markers MUST appear alone on a line with this exact structure:

```
<optional-leading-spaces><!-- CG-EXCLUSION:BEGIN id=<id> --><optional-trailing-spaces>
<optional-leading-spaces><!-- CG-EXCLUSION:END id=<id> --><optional-trailing-spaces>
```

Where:
- Leading spaces (0+) are permitted (for indented Markdown)
- The token `<!-- CG-EXCLUSION:BEGIN id=` is **case-sensitive** and exact
- `<id>` matches `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`
- No additional attributes are permitted
- Trailing spaces are ignored

**Invalid (malformed) markers trigger E-EX00:**
- Extra attributes: `<!-- CG-EXCLUSION:BEGIN id=foo reason="bar" -->`
- Case variation: `<!-- cg-exclusion:begin id=foo -->`
- Inline with content: `text <!-- CG-EXCLUSION:BEGIN id=foo --> more text`

### 8.3 ID Format

IDs MUST match: `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`

### 8.4 Structural Rules (Normative)

| Rule | Violation | Error Code |
|------|-----------|------------|
| BEGIN and END `id` values MUST match exactly | Mismatch | E-EX01 |
| No nesting: BEGIN while inside another block | Nested BEGIN | E-EX02 |
| No overlap: END must close most recent BEGIN (stack discipline) | Interleaved | E-EX03 |
| No duplicate IDs: Same `id` used for multiple blocks | Reused ID | E-EX04 |

**Example of E-EX03 (interleaved blocks):**
```markdown
<!-- CG-EXCLUSION:BEGIN id=outer -->
<!-- CG-EXCLUSION:BEGIN id=inner -->
<!-- CG-EXCLUSION:END id=outer -->   ← ERROR: closes outer before inner
<!-- CG-EXCLUSION:END id=inner -->
```

### 8.5 Code Fence Handling

Exclusion markers inside fenced code blocks MUST be ignored by validators.

- A fenced code block begins with ``` or ~~~ (3+ characters)
- It ends at the next fence of the **same character** with **equal or greater length**
- Example: ````` opened → closes at ````` or longer, NOT at ```

#### 8.5.1 Parsing Order (Normative)

Validators MUST process lines in this order:

1. **Track fence state:** Toggle in/out of code fence on fence delimiter lines
2. **If inside fence:** Ignore exclusion markers entirely (treat as literal text)
3. **If outside fence:** Process BEGIN/END markers per §8.4

Fence detection rules:
- Fence opens on line starting with 3+ backticks or tildes (after 0–3 leading spaces)
- Fence closes on line starting with same character, equal or greater count
- Info strings after opener are ignored
- Block quotes: strip leading `>` and optional space before applying fence/marker detection
- A line indented by 4+ spaces MUST NOT open or close a fence (it is an indented code block, per CommonMark)

**Indented code blocks (Normative):** Exclusion markers inside indented code blocks (lines with 4+ leading spaces, per CommonMark) MAY be interpreted as literal markers by validators. This specification does not require validators to detect indented code blocks. Authors SHOULD use fenced code blocks when documenting exclusion marker syntax to avoid ambiguity.

### 8.6 State Rules

| Condition | Constraint | Error Code |
|-----------|------------|------------|
| Exclusion blocks exist | `hitl-status` MUST be `REVIEWED_WITH_EXCEPTIONS` | E-EX05 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | ≥1 exclusion block MUST exist in body | E-EX06 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-reason` MUST be present (non-empty string) | E-EX07 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-ids` MUST list all exclusion block IDs | E-EX08 |
| Exclusion block ID in body | MUST be listed in `exceptions-ids` | E-EX09 |
| `exceptions-ids` format | MUST be a list of valid ID strings | E-EX10 |

### 8.7 YAML Fields for Exclusions

Add to frontmatter when exclusion blocks are present:

```yaml
hitl-status: REVIEWED_WITH_EXCEPTIONS
exceptions-reason: "Legacy OAuth implementation; no SME available"
exceptions-ids:
  - auth-legacy-1
  - oauth-flow-2
exclusions-coverage: 0.15  # Computed: excluded_bytes / total_body_bytes
```

### 8.8 Ingestion Policy Impact

A document with **any** exclusion blocks MUST have `rag-ingestable: false`, regardless of other status fields.

**No partial ingestion.** Documents are accepted or rejected as a whole.

### 8.9 Claims Inside Exclusion Blocks

Claims that appear inside exclusion blocks are **ignored entirely** during claim extraction. They do not generate entries in `hitl-claims` and are not validated.

Content inside exclusion blocks is also ignored for structural validation requirements (e.g., SOT `## Verified Claims` detection/validation).

Validators MAY emit a warning: "Claims detected inside exclusions were ignored."

### 8.10 Example

```yaml
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy prose; no SME available."
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users *(as of 2026-01-09)*.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

### 8.11 Redacted Export

The `redact_exclusions()` function (or CLI `export --redact-exclusions`) produces a copy with exclusion block **content** replaced by `[REDACTED]`. This enables:

- Safe ingestion by downstream tools that don't respect metadata flags
- Sharing documents with parties who shouldn't see quarantined content
- Audit trails that preserve structure without sensitive details

**Behavior:**

1. Exclusion markers (BEGIN/END comments) are **preserved**
2. Content between markers is replaced with `[REDACTED]\n`
3. `document-sha256` is **recomputed** for the redacted version
4. Line numbers will shift (the redacted document is shorter)

**Important:** The redacted document is a **new document**, not a modification of the original. It has a different hash and should be treated as a derivative work.

**Example:**

Original:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
Multiple lines of sensitive content here...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

After redaction:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
[REDACTED]
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

---

## 9. Computed Fields

### 9.1 `rag-ingestable` (Boolean)

This field is an **informational summary** for pipeline ingestion decisions.

**Computation:**
```python
rag-ingestable = (clarity-status == CLEAR) \
             and (hitl-status == REVIEWED) \
             and (exclusion_block_count == 0)
```

**Validator behavior:**
- Validators MUST compute this value
- Validators SHOULD write it to the document
- If declared value disagrees with computed → WARN (W-RI01)
- If declared value is not boolean → ERROR (E-RI01)

**Semantics:**
- `true` → Document is epistemically well-formed and human-reviewed
- `false` → Document MUST be rejected from production RAG

**Important:** `rag-ingestable: true` does NOT guarantee:
- Claims are factually true
- Human review was error-free
- Hallucinations are impossible

### 9.2 `exclusions-coverage` (Float 0.0–1.0)

Reports what fraction of body content is excluded.

**Computation:**
```python
exclusions-coverage = excluded_bytes / total_body_bytes
```

Where:
- `total_body_bytes` = UTF-8 byte count of canonical body (per §2.4 canonicalization)
- `excluded_bytes` = byte count from BEGIN marker through END marker (inclusive), including marker lines

**Byte counting rules (Normative):**
- Count bytes AFTER CRLF→LF normalization (consistent with hash canonicalization)
- Use UTF-8 encoded byte length, not character count
- If `total_body_bytes = 0`, `exclusions-coverage` MUST be `0.0` or omitted

**Validation:**
- If present, MUST be number in range 0.0–1.0 → else ERROR (E-EC01)
- If coverage ≥ 0.50 → WARN (W-EC01): majority excluded

---

## 10. Validation Error Codes

### 10.1 Severity Levels

- **ERROR (E-xxx):** Document invalid; MUST NOT pass validation
- **WARN (W-xxx):** Document valid but suboptimal; SHOULD be addressed

Validators SHOULD report actionable locations (line/section) when possible.

### 10.2 Structural Errors (E-ST)

| Code | Rule | Severity |
|------|------|----------|
| E-ST01 | YAML frontmatter parsing fails (syntax error) | ERROR |
| E-ST02 | Missing YAML frontmatter block at file start | ERROR |
| E-ST03 | Missing required frontmatter field | ERROR |
| E-ST04 | `processed-date` is in the future (UTC) | ERROR |
| E-ST05 | `points-passed` invalid (syntax or out of bounds 1–9) | ERROR |
| E-ST06 | Missing end marker (`<!-- CLARITY_GATE_END -->`) | ERROR |
| E-ST07 | End marker malformed (invalid status values) | ERROR |
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

### 10.3 State Consistency Errors (E-SC)

| Code | Rule | Severity |
|------|------|----------|
| E-SC01 | Invalid state: `UNCLEAR` with `hitl-status != PENDING` | ERROR |
| E-SC02 | `hitl-status: PENDING` but `hitl-pending-count = 0` | ERROR |
| E-SC03 | `hitl-status: REVIEWED` but `hitl-pending-count > 0` | ERROR |
| E-SC04 | `hitl-status: REVIEWED_WITH_EXCEPTIONS` but `hitl-pending-count > 0` | ERROR |
| E-SC05 | YAML and end marker status disagree | ERROR |

### 10.4 Exclusion Block Errors (E-EX)

| Code | Rule | Severity |
|------|------|----------|
| E-EX00 | Malformed exclusion marker line | ERROR |
| E-EX01 | BEGIN/END id mismatch | ERROR |
| E-EX02 | Nested exclusion blocks | ERROR |
| E-EX03 | Interleaved exclusion blocks | ERROR |
| E-EX04 | Duplicate exclusion IDs | ERROR |
| E-EX05 | Exclusion blocks exist but `hitl-status != REVIEWED_WITH_EXCEPTIONS` | ERROR |
| E-EX06 | `REVIEWED_WITH_EXCEPTIONS` but no exclusion blocks in body | ERROR |
| E-EX07 | `REVIEWED_WITH_EXCEPTIONS` but missing `exceptions-reason` | ERROR |
| E-EX08 | `exceptions-ids` references ID not present in body | ERROR |
| E-EX09 | Exclusion block ID in body but missing from `exceptions-ids` | ERROR |
| E-EX10 | `exceptions-ids` not a list of strings or contains invalid ID format | ERROR |

### 10.5 Hash Errors (E-HS)

| Code | Rule | Severity |
|------|------|----------|
| E-HS01 | `document-sha256` malformed (not 64-char lowercase hex) | ERROR |
| W-HS01 | `document-sha256` doesn't match computed | WARN |

### 10.6 Computed Field Errors

| Code | Rule | Severity |
|------|------|----------|
| E-RI01 | `rag-ingestable` present but not boolean | ERROR |
| W-RI01 | `rag-ingestable` disagrees with computed value | WARN |
| E-EC01 | `exclusions-coverage` not a number in range 0.0–1.0 | ERROR |
| W-EC01 | `exclusions-coverage` ≥ 0.50 (majority excluded) | WARN |

### 10.6.1 HITL Claim Errors (E-HC)

These codes apply to entries under the `hitl-claims` list in YAML frontmatter.

| Code | Rule | Severity |
|------|------|----------|
| E-HC01 | `hitl-claims` is present but not a list | ERROR |
| E-HC02 | A `hitl-claims` entry is missing required field `text` | ERROR |
| E-HC03 | A `hitl-claims` entry has `round` not in {A, B} | ERROR |
| E-HC04 | A `hitl-claims` entry has `confirmed-date` not a valid `YYYY-MM-DD` date | ERROR |

### 10.7 Table Errors (E-TB)

| Code | Rule | Severity |
|------|------|----------|
| E-TB01 | No `## Verified Claims` section (SOT only) | ERROR |
| E-TB02 | Table has no data rows | ERROR |
| E-TB03 | Required columns missing (Claim, Value, Source, Verified) | ERROR |
| E-TB04 | Column order wrong (Claim not first or Verified not last) | ERROR |
| E-TB05 | Empty cell in required column | ERROR |
| E-TB06 | Invalid date format in Verified column | ERROR |
| E-TB07 | Verified date in future (beyond 24h grace) | ERROR |

### 10.8 Promote/Demote Errors (E-PM, E-DM)

| Code | Rule | Severity |
|------|------|----------|
| E-PM01 | Promote: no verified claims and no table | ERROR |
| E-PM02 | Promote: file already has tier block | ERROR |
| W-DM01 | Demote: file has no tier block (no-op) | WARN |

### 10.9 Queue Errors (E-QU)

| Code | Rule | Severity |
|------|------|----------|
| E-QU01 | Claim ID not found in document | ERROR |
| W-QU01 | Claim text differs from queue | WARN |
| E-QU02 | Read-only queue fields modified | ERROR |
| W-QU02 | Queue expired (>7 days) | WARN |

### 10.10 Forward Compatibility

| Code | Rule | Severity |
|------|------|----------|
| W-FC01 | `clarity-gate-version` major exceeds validator capability | WARN |

When W-FC01 triggers, validators MUST also force `rag-ingestable: false` regardless of other checks.

---

## 11. Implementation Anti-Patterns

### 11.1 Parsing Anti-Patterns

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `.trim()` on delimiter lines | `.trimEnd()` (trailing only) | Leading whitespace invalidates `---` delimiter |
| Regex for YAML frontmatter | Line-by-line scan for exact `---` | Regex can match `---` in body content |
| Scan backwards from EOF for the first marker | Scan forward for the FIRST occurrence of the exact end marker string | Spec defines the end boundary as the first marker occurrence (§2.3) |
| Normalize on-disk content globally | Normalize only for hashing canonicalization (§2.4), otherwise preserve body bytes | Lossless editing requires preserving body text exactly |

### 11.2 Type Coercion Traps

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `Boolean(data['rag-ingestable'])` | `typeof value === 'boolean'` | `"false"` coerces to `true`! |
| `Number(data['exclusions-coverage'])` | `typeof value === 'number'` | `"0.5"` coerces silently |
| Trust YAML parser booleans | Check for `yes/no/on/off` | PyYAML treats these as booleans |

### 11.3 Cross-Language Parity

| Issue | Python | Node.js | Solution |
|-------|--------|---------|----------|
| YAML boolean keywords | PyYAML: `yes/no` → bool | js-yaml: configurable | Use explicit `true/false` only |
| Date comparison | `datetime.fromisoformat()` | `new Date()` | Parse as UTC date only |
| Unicode normalization | `unicodedata.normalize()` | Manual mapping | Use same char→char table |

### 11.4 Exclusion Block Offset Tracking

When computing `exclusions-coverage`:

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| Approximate bytes from char count | Extract actual UTF-8 bytes | Multi-byte chars (emoji, CJK) break ratio |
| Forget trailing newline after END | Include newline in excluded bytes | Spec says "through END marker" |
| Add +1 unconditionally | Clamp if END is on last line | No newline after final line |

---

## 12. Queue File Workflow

### 12.1 Queue File Schema

```yaml
schema-version: 1.0
generated: 2026-01-12T10:30:00Z
expires: 2026-01-19T10:30:00Z           # 7 days from generation
source-files-hash: <sha256>

documents:
  - file: docs/api-pricing.cgd.md
    file-hash: <sha256>
    claims:
      - id: claim-75fb137a
        text: "Base price is $99/mo"
        location: "api-pricing/1"
        round: B
        response: null                   # true | false | "estimated"
        notes: ""
```

### 12.2 Queue Expiry

Queues expire 7 days after generation. On apply:
- If expired → WARNING (W-QU02), suggest regeneration
- User can override with `--force`

### 12.3 apply-hitl Transaction Semantics

**Model: Fail-fast with checkpoint.**

```python
def apply_hitl(queue_path: str):
    queue = load_queue(queue_path)
    checkpoint = load_checkpoint(queue_path)
    
    start_index = checkpoint.last_success + 1 if checkpoint else 0
    
    for i, doc in enumerate(queue.documents[start_index:], start_index):
        try:
            validate_file_hash(doc)
            for claim in doc.claims:
                validate_claim(claim)
                apply_claim_response(claim)
            save_checkpoint(queue_path, last_success=i)
        except ValidationError as e:
            save_checkpoint(queue_path, last_success=i-1, error=e)
            raise ApplyError(f"Failed at document {i}: {e}")
    
    delete_checkpoint(queue_path)
    return Success
```

---

## 13. Round A/B Classification

### 13.1 Definition

| Round | Context | Meaning |
|-------|---------|---------|
| **A** | Interactive skill session | Source found while human was present |
| **B** | Batch CLI processing | Requires explicit human verification |

### 13.2 Environment Rules

| Environment | Round A | Round B |
|-------------|---------|---------|
| Claude.ai Skill | ✅ Available | ✅ Available |
| CLI batch | ❌ Never | ✅ Always |

---

## 14. CLI Commands

### 14.1 Package Names

| Platform | CLI Tool | Library |
|----------|----------|---------|
| npm | `clarity-gate` | `clarity-gate-core` |
| PyPI | `clarity-gate` | `clarity-gate-core` |

### 14.2 Command Reference

```bash
clarity-gate <command> [options]

Commands:
  verify <files...>           Validate format (local, no API)
  process <files...>          Create/update CGDs via Claude API
  apply-hitl <queue.yaml>     Apply HITL responses (with checkpoint)
  promote <file>              Promote CGD to SOT tier
  demote <file>               Demote SOT to CGD
  status <files...>           Show tier/status summary

Options:
  --api-key <key>             Anthropic API key (or ANTHROPIC_API_KEY env)
  --output <dir>              Output directory
  --hitl-queue <file>         Generate HITL queue file
  --dry-run                   Preview changes
  --reason <text>             Reason for demote
  --force                     Override warnings
```

---

## 15. YAML vs End Marker Authority

### 15.1 Rule

**YAML frontmatter is authoritative for CLI tools.**

The end marker (`Clarity Gate: CLEAR | REVIEWED`) is a passive signal for LLMs reading the document.

YAML frontmatter is authoritative for tooling decisions, but validators MUST enforce that the end marker status matches YAML status (`E-SC05`).

### 15.2 Mismatch Handling

If YAML and end marker disagree:

```
ERROR: E-SC05
  YAML says: UNCLEAR | PENDING
  End marker says: CLEAR | REVIEWED
  
  YAML is authoritative. Update end marker to match.
```

---

## 16. Known Limitations

### 16.1 Security Model

- Hash provides integrity, not authenticity
- No cryptographic signature (deferred to future version)
- YAML tampering detectable only via hash verification

### 16.2 Claim Matching

- ID-based matching (stable across minor edits)
- Text comparison for warnings only
- No fuzzy matching (exact comparison)

### 16.3 Table Validation

- English headers only (`## Verified Claims`)
- i18n support deferred

### 16.4 Slug Algorithm

- Non-ASCII characters stripped (not preserved like GFM)
- CJK/RTL headings may produce empty slugs (use `section-N` fallback)
- Intentional tradeoff for cross-platform compatibility

---

## 17. Examples

### 17.1 Minimal CGD

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
rag-ingestable: true
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.2 Full SOT

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: f6e5d4c3b2a1...
rag-ingestable: true
hitl-claims:
  - id: claim-75fb137a
    text: "Base price is $99/mo"
    value: "$99/mo"
    source: "Pricing page"
    location: "api-pricing/1"
    round: B
    confirmed-by: Maria
    confirmed-date: 2026-01-12
tier:
  level: SOT
  owner: Pricing Team
  version: 1.0
  promoted-date: 2026-01-12
  promoted-by: Maria
---

# API Pricing

Base price is **$99/mo** *(verified 2026-01-12)*.

## Verified Claims

| Claim | Value | Source | Verified |
|-------|-------|--------|----------|
| Base price is $99/mo | $99/mo | Pricing page | 2026-01-12 |

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.3 Document with Exclusions

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy OAuth; no SME available"
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

---

## 18. Test Vectors

### 18.1 Hash Computation

**Input file:**
```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: PENDING
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

**Expected SHA-256:**
```
d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
```


### 18.2 Claim ID Computation

**Test Vector 1:**
- text: `Base price is $99/mo`
- location: `api-pricing/1`
- **claim ID: `claim-75fb137a`**

**Test Vector 2:**
- text: `The API supports GraphQL`
- location: `features/1`
- **claim ID: `claim-eb357742`**

### 18.3 Slug Computation

| Input Heading | ASCII-Safe Slug |
|---------------|-----------------|
| `## API Pricing` | `api-pricing` |
| `## API & Pricing (v2.0)` | `api-pricing-v20` |
| `## 日本語` | `` (empty → `section-N`) |

### 18.4 Pipe Escaping (Idempotency)

| Input | Output |
|-------|--------|
| `A \| B` | `A \| B` (unchanged) |
| `A | B` | `A \| B` (escaped) |
| `A \| B | C` | `A \| B \| C` (mixed) |

---

## 19. Changelog

### v2.0 (January 2026)

- **Unified versioning:** Aligned internal spec version with release version
- **All v1.2 features included:** Exclusion blocks, computed fields, validation codes
- **Format finalized:** Implementation-ready specification

### v1.2 (January 2026)

- **Added Exclusion Blocks (§8)** for quarantining unresolved regions
- **Added computed fields:** `rag-ingestable`, `exclusions-coverage` (§9)
- **Added 37 validation error codes** with E-xxx/W-xxx namespace (§10)
- **Added implementation anti-patterns** (§11)
- **Added end marker uniqueness constraints** (§2.7): E-ST08, E-ST09
- **Added canonicalization scope clarification** (§2.4.1): hash protects canonical form, not rendered Markdown
- Hardened interoperability: slug disambiguation, backslash parity, YAML lossless editing
- Full test vectors with actual SHA-256 values

### v1.1 (January 2026)

- **Unified CGD and SOT into single format**
- SOT distinguished by presence of `tier:` block (no separate extension)
- Single `.cgd.md` extension for all documents
- Added Two-Round HITL (Round A: Derived, Round B: True HITL)
- Added stable claim IDs (`claim-<8-char-hash>`)
- ASCII-Safe slugification (not GFM)
- Idempotent pipe escaping

### v1.0 (December 2025)

- Initial specification
- Two separate formats: CGD (`.cgd.md`) and SOT (`.sot.md`)
- 9-point verification checklist
- Basic HITL verification

---

*End of Specification v2.0*
, r'^\s*(research|data|information)\s*

### 1.4 Two Document States

| State | `tier:` block | Structured table | Use case |
|-------|---------------|------------------|----------|
| **CGD** | Absent | Optional | Verified text, safe for RAG |
| **SOT** | Present | Required | Canonical reference, machine-extractable |

---

## 2. Hash Specification

### 2.1 Scope

`document-sha256` covers YAML frontmatter + Markdown body, **excluding the hash line itself**.

#### 2.1.1 Hash Input Window (Normative)

Implementations MUST compute `document-sha256` over the exact substring of the document defined as:

- **Start boundary:** the first byte immediately after the opening YAML delimiter line `---` plus its trailing newline (`---\n`).
- **End boundary:** the first byte immediately before the first occurrence of the end marker string `<!-- CLARITY_GATE_END -->`.

Therefore, the hash input includes:

- YAML frontmatter content (excluding the opening `---` line)
- The closing YAML delimiter line (`---`) and everything after it up to (but not including) the end marker

The hash input excludes:

- The opening YAML delimiter line (`---`)
- The end marker line and all bytes after (and including) the first end marker occurrence

### 2.2 Hash Exclusion Rule

**CRITICAL:** The SHA-256 calculation MUST exclude the `document-sha256` field, including:
- The line containing `document-sha256:`
- Any indented continuation lines (for multiline YAML values)

**Regex pattern:** `^\s*document-sha256:.*$`

**Frontmatter-only scope (Normative):** The exclusion rule MUST apply only within the YAML frontmatter region (between the opening `---` line and the closing `---` line). Implementations MUST NOT remove or alter any `document-sha256:` text that appears in the Markdown body.

**Multiline continuation (Normative):** After excluding the key line matching `^\s*document-sha256:`, implementations MUST also exclude subsequent lines while BOTH conditions hold:

1. The parser is still within YAML frontmatter, and
2. The line's indentation is strictly greater than the indentation of the `document-sha256:` key line.

Continuation exclusion ends when indentation returns to less-than-or-equal to the key indentation, or when the closing `---` delimiter is reached.

**Exclusion blocks and hash (Normative):** Exclusion blocks (§8) do NOT affect hash computation. The `document-sha256` is computed over the full hash window including exclusion markers and content inside exclusion blocks. Rationale: The hash is an integrity mechanism; excluding quarantined regions would allow undetected tampering of exactly the risky content.

**Algorithm:**

```python
import re
import hashlib

def compute_hash(file_content: str) -> str:
    # 0. Pre-normalize for boundary detection (CRLF/BOM).
    #    Canonicalization (§2.4) is applied later, but we need stable slicing indices.
    working = file_content
    if working.startswith('\ufeff'):
        working = working[1:]
    working = working.replace('\r\n', '\n')

    # 1. Extract content between the opening YAML delimiter line and the end marker.
    start = working.index('---\n') + len('---\n')
    end = working.index('<!-- CLARITY_GATE_END -->')
    hashable = working[start:end]
    
    # 2. Remove document-sha256 line(s) — YAML frontmatter only
    lines = hashable.split('\n')
    filtered = []
    skip_multiline = False
    hash_indent = 0
    in_frontmatter = True
    
    for line in lines:
        # Detect end of YAML frontmatter
        if in_frontmatter and line.strip() == '---':
            in_frontmatter = False

        # Check if this is the hash line
        if in_frontmatter and re.match(r'^\s*document-sha256:', line):
            skip_multiline = True
            hash_indent = len(line) - len(line.lstrip())
            continue
        
        # If we're skipping multiline, check if this is a continuation
        if skip_multiline:
            current_indent = len(line) - len(line.lstrip())
            if in_frontmatter and current_indent > hash_indent:
                continue
            skip_multiline = False
        
        filtered.append(line)
    
    hashable = '\n'.join(filtered)
    
    # 3. Canonicalize
    hashable = canonicalize(hashable)
    
    # 4. Compute
    return hashlib.sha256(hashable.encode('utf-8')).hexdigest()
```

### 2.3 End Marker Detection

**The end boundary is the HTML comment `<!-- CLARITY_GATE_END -->`**, not a bare `---`.

This solves the ambiguity when `---` (horizontal rules) appear in the document body.

**Detection rule (Normative):** The end marker is recognized when:

1. The marker string `<!-- CLARITY_GATE_END -->` appears in the document, AND
2. The marker is **outside any fenced code block** (using §8.5 fence-tracking logic)

Markers inside fenced code blocks (`` ``` `` or `~~~`) MUST be ignored. This enables documentation about Clarity Gate itself to include the marker string in code examples without terminating the document prematurely ("Quine Protection").

**Implementation:** Parsers MUST track fence state while scanning for the marker, using the same fence detection rules as §8.5 (Exclusion Blocks in Fenced Code).

### 2.4 Canonicalization

Before hashing, normalize:

1. **Line endings:** CRLF → LF
2. **Trailing whitespace:** Remove per line
3. **Consecutive newlines:** Collapse 3+ newlines to 2
4. **Final newline:** Exactly one trailing LF
5. **Encoding:** UTF-8 NFC normalization
6. **BOM:** Remove if present
7. **Tabs:** Preserve (do not convert)
8. **Leading whitespace:** Preserve (significant in code blocks)

#### 2.4.1 Canonicalization Scope (Normative)

The hash protects the **canonical byte sequence**, not rendered Markdown semantics. Specifically:

- Trailing whitespace (including Markdown hard line breaks via `  \n`) is stripped
- 3+ consecutive newlines collapse to 2

Documents with different rendered appearance MAY share the same hash if they differ only in these canonicalized elements. This is intentional: LLM tokenizers normalize whitespace similarly, so these variations do not affect RAG ingestion semantics. Cross-platform hash stability requires stripping editor-introduced whitespace variations.

### 2.5 Hash Computation Order (Initial Creation)

1. Generate complete YAML with `document-sha256: PENDING`
2. Generate body content
3. Compute hash (excluding `document-sha256:` line)
4. Replace `PENDING` with actual hash
5. Verify by recomputing (must match)

### 2.6 When Hash Changes

| Action | Hash changes? | Reason |
|--------|---------------|--------|
| Process (add markers) | Yes | Body modified |
| Promote | Yes | YAML modified (tier block) |
| Demote | Yes | YAML + body modified |
| Edit content | Yes | Body modified |
| Edit YAML (except hash) | Yes | YAML modified |

### 2.7 End Marker Uniqueness (Normative)

The document MUST contain exactly one occurrence of `<!-- CLARITY_GATE_END -->`.

After the `Clarity Gate: <status> | <hitl-status>` line, only optional trailing whitespace and a single trailing newline are permitted until EOF.

| Code | Rule | Severity |
|------|------|----------|
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

---

## 3. SOT Requirements

### 3.1 Structured Claims Table

SOT documents MUST contain a `## Verified Claims` section with a valid table.

The `## Verified Claims` section and its table MUST be outside any exclusion block (§8). Content inside exclusion blocks is ignored for the purpose of satisfying SOT structural requirements.

### 3.2 Table Validation Rules

| Rule | Requirement | Error |
|------|-------------|-------|
| V1 | Section header matches `## Verified Claims` (case-insensitive, whitespace-normalized) | `E-TB01` |
| V2 | Table has at least 1 data row | `E-TB02` |
| V3 | Required columns present: Claim, Value, Source, Verified | `E-TB03` |
| V4 | Column order: Claim MUST be first, Verified MUST be last | `E-TB04` |
| V5 | Middle columns (Value, Source) may be in any order | (not an error) |
| V6 | Extra columns allowed anywhere except before Claim or after Verified | (not an error) |
| V7 | No empty cells in required columns (whitespace-only = empty, `-` = empty) | `E-TB05` |
| V8 | Verified column is valid date (YYYY-MM-DD, validated for real dates) | `E-TB06` |
| V9 | Verified date not in future (with 24h grace period) | `E-TB07` |

### 3.3 Date Validation Details

**Valid dates only:**
- `2026-02-29` → INVALID (2026 is not a leap year)
- `2026-04-31` → INVALID (April has 30 days)
- `2026-13-01` → INVALID (no month 13)

**Future check with timezone grace:**

To accommodate global users, the future date check allows a **24-hour grace period**:

```python
from datetime import datetime, timedelta, timezone

def is_future_date(date_str: str) -> bool:
    verified_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    grace_boundary = (datetime.now(timezone.utc) + timedelta(hours=24)).date()
    return verified_date > grace_boundary
```

### 3.4 Empty Cell Definition

A cell is considered **empty** if it contains:
- Only whitespace (spaces, tabs)
- Exactly the character `-` (dash placeholder)
- Nothing at all

### 3.5 Column Matching Examples

**Valid:**
```
| Claim | Value | Source | Verified |          ✓ Standard
| Claim | Source | Value | Verified |          ✓ Middle swapped
| Claim | Notes | Value | Source | Verified |  ✓ Extra column in middle
```

**Invalid:**
```
| Value | Claim | Source | Verified |          ✗ Claim not first
| Claim | Value | Source | Notes |             ✗ Verified not last
```

---

## 4. Table Auto-Generation

### 4.1 When Auto-Generation Occurs

`promote` auto-generates a table when:
- Document has confirmed claims in `hitl-claims`
- No `## Verified Claims` section exists
- No archived table exists

### 4.2 Generation Algorithm

```python
def generate_table(hitl_claims: list) -> str:
    rows = []
    for claim in hitl_claims:
        rows.append({
            'Claim': escape_pipes(claim['text']),
            'Value': escape_pipes(claim.get('value', '-')),
            'Source': escape_pipes(claim.get('source', 'HITL Verification')),
            'Verified': claim['confirmed-date']
        })
    
    return format_table(rows)
```

### 4.3 Pipe Character Escaping

**CRITICAL:** When populating table cells, implementations MUST escape **unescaped** pipe characters (`|`) as `\|`.

**Idempotency:** Already-escaped pipes (`\|`) must NOT be double-escaped to `\\|`.

**Escaped definition (Normative):** A pipe character (`|`) is considered escaped if and only if it is immediately preceded by an odd number of consecutive backslashes.

```python
def escape_pipes(text: str) -> str:
    """Escape unescaped pipe characters for Markdown table cells.
    
    Idempotent: already-escaped pipes (\\|) are not double-escaped.
    """
    result = []
    i = 0
    while i < len(text):
        if text[i] == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and text[j] == '\\':
                backslashes += 1
                j -= 1
            if backslashes % 2 == 1:
                result.append('|')
            else:
                result.append('\\|')
        else:
            result.append(text[i])
        i += 1
    return ''.join(result)
```

### 4.4 Claim/Value Column Population

The `Claim` column receives the **full claim text**. 

The `Value` column is populated from:
1. The `value` field in YAML (if present)
2. Otherwise, a dash (`-`)

**Do NOT attempt to parse claim text into Claim/Value.** This would require NLP and produce inconsistent results.

### 4.5 Table Row Parsing (Normative)

To ensure Python and Node.js implementations parse Markdown tables identically, implementations MUST split table rows into cells using the algorithm below.

**Algorithm (Normative):**

1. Given a single table row string (one line), remove a single leading `|` if present.
2. Remove a single trailing `|` if present.
3. Split the remaining string on `|` characters that are **NOT escaped**, where "escaped" uses the **odd backslash parity** rule from §4.3.
4. Trim leading/trailing whitespace from each resulting cell.

```python
def split_table_row(row: str) -> list[str]:
    if row.startswith('|'):
        row = row[1:]
    if row.endswith('|'):
        row = row[:-1]

    cells = []
    buf = []

    i = 0
    while i < len(row):
        ch = row[i]
        if ch == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and row[j] == '\\':
                backslashes += 1
                j -= 1

            if backslashes % 2 == 1:
                buf.append('|')
            else:
                cells.append(''.join(buf).strip())
                buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    cells.append(''.join(buf).strip())
    return cells
```

---

## 5. Claim ID Specification

### 5.1 ID Format

```
claim-<8-char-hex>
```

Example: `claim-75fb137a`

### 5.2 ID Computation

```python
def compute_claim_id(text: str, location: str) -> str:
    input_string = f"{text}|{location}"
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()
    return f"claim-{hash_hex[:8]}"
```

### 5.3 Location Context Format

`location` is a stable reference: `heading_slug/ordinal`

**Format:** `<nearest_heading_slug>/<ordinal_within_section>`

### 5.4 Slug Algorithm (ASCII-Safe Slugification)

**IMPORTANT:** This is **NOT** GitHub Flavored Markdown (GFM) slugification. GFM preserves non-ASCII characters; this algorithm strips them for maximum cross-platform compatibility.

**ASCII-Safe Slug Rules:**
1. Convert to lowercase
2. Remove all characters except ASCII alphanumerics (`a-z`, `0-9`), spaces, and hyphens
3. Replace spaces with hyphens
4. Collapse consecutive hyphens to single hyphen
5. Remove leading/trailing hyphens

```python
import re

def ascii_safe_slugify(heading: str) -> str:
    slug = heading.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug
```

**Special case — empty slug:** If a heading produces an empty slug (all non-ASCII), use `section-<ordinal>` where ordinal is the heading's position in the document (1-indexed).

**Special case — duplicate slugs (Normative):** If two or more headings produce the same slug, implementations MUST disambiguate by appending `-2`, `-3`, ... in document order.

**Special case — root:** Claims before any heading use `root` as the slug.

### 5.5 Ordinal Assignment

Ordinals are 1-indexed within each section.

```markdown
## Pricing

First claim here.     → location: pricing/1
Second claim here.    → location: pricing/2

## Features

First claim here.     → location: features/1
```

### 5.6 Claim Matching for Queue Apply

**Matching is by ID, not text.**

If ID matches but text differs slightly (whitespace, punctuation):
```
WARNING: Claim text differs from queue. Applying anyway.
  Queue: "Base price is $99/mo"
  Doc:   "Base price is $99/mo."
```

---

## 6. Promote Command

### 6.1 Basic Usage

```bash
clarity-gate promote doc.cgd.md --owner "Team" --version 1.0
```

### 6.2 Behavior

```
1. Validate document is CGD (no tier block)
2. Check for existing table:
   a. If ## Verified Claims exists → validate and proceed
   b. If ## Claims (Archived from SOT) exists → restore
   c. If neither → auto-generate from hitl-claims
3. If no claims and no table → ERROR: E-PM01
4. Add tier block to YAML
5. Recompute document-sha256
6. Update processed-date
```

### 6.3 Re-Promotion (Archived Table Restoration)

Detection uses **comment ID**, not header text:

```markdown
<!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-10 -->
## Claims (Archived from SOT)
```

---

## 7. Demote Command

### 7.1 Basic Usage

```bash
clarity-gate demote doc.cgd.md --reason "Superseded by v2"
```

### 7.2 Behavior

1. Validate document is SOT (has tier block)
2. If no tier block → WARNING, exit 0 (no-op)
3. Remove tier block from YAML
4. Find `## Verified Claims` section
5. Generate unique archive ID: `arch-<8-char-hex>`
6. Add archive comment with ID:
   ```markdown
   <!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-12, reason="Superseded by v2" -->
   ## Claims (Archived from SOT)
   ```
7. Recompute document-sha256
8. Update processed-date

### 7.3 Archive Comment Format

```
<!-- CLARITY_GATE_ARCHIVED: id=<id>, date=<ISO-date>, reason="<escaped-reason>" -->
```

**Escaping in reason:** Replace `"` with `&quot;` and `>` with `&gt;`.

---

## 8. Exclusion Blocks

### 8.1 Purpose

Exclusion Blocks mark document regions with unresolved ambiguity that are **unsafe for RAG ingestion**. They allow a document to be `CLEAR` overall while quarantining specific sections that couldn't be resolved.

**Use case:** Legacy documentation where no SME is available, or third-party content that can't be modified.

**Semantic note:** A document may have `clarity-status: CLEAR` with exclusion blocks present. This means "all non-excluded content is epistemically clear." However, such documents are still non-ingestable (`rag-ingestable: false`) by design. This is a "human-readable but quarantined" state.

### 8.2 Syntax

```markdown
<!-- CG-EXCLUSION:BEGIN id=<id> -->
Content with unresolved ambiguity...
<!-- CG-EXCLUSION:END id=<id> -->
```

#### 8.2.1 Marker Grammar (Normative)

Exclusion markers MUST appear alone on a line with this exact structure:

```
<optional-leading-spaces><!-- CG-EXCLUSION:BEGIN id=<id> --><optional-trailing-spaces>
<optional-leading-spaces><!-- CG-EXCLUSION:END id=<id> --><optional-trailing-spaces>
```

Where:
- Leading spaces (0+) are permitted (for indented Markdown)
- The token `<!-- CG-EXCLUSION:BEGIN id=` is **case-sensitive** and exact
- `<id>` matches `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`
- No additional attributes are permitted
- Trailing spaces are ignored

**Invalid (malformed) markers trigger E-EX00:**
- Extra attributes: `<!-- CG-EXCLUSION:BEGIN id=foo reason="bar" -->`
- Case variation: `<!-- cg-exclusion:begin id=foo -->`
- Inline with content: `text <!-- CG-EXCLUSION:BEGIN id=foo --> more text`

### 8.3 ID Format

IDs MUST match: `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`

### 8.4 Structural Rules (Normative)

| Rule | Violation | Error Code |
|------|-----------|------------|
| BEGIN and END `id` values MUST match exactly | Mismatch | E-EX01 |
| No nesting: BEGIN while inside another block | Nested BEGIN | E-EX02 |
| No overlap: END must close most recent BEGIN (stack discipline) | Interleaved | E-EX03 |
| No duplicate IDs: Same `id` used for multiple blocks | Reused ID | E-EX04 |

**Example of E-EX03 (interleaved blocks):**
```markdown
<!-- CG-EXCLUSION:BEGIN id=outer -->
<!-- CG-EXCLUSION:BEGIN id=inner -->
<!-- CG-EXCLUSION:END id=outer -->   ← ERROR: closes outer before inner
<!-- CG-EXCLUSION:END id=inner -->
```

### 8.5 Code Fence Handling

Exclusion markers inside fenced code blocks MUST be ignored by validators.

- A fenced code block begins with ``` or ~~~ (3+ characters)
- It ends at the next fence of the **same character** with **equal or greater length**
- Example: ````` opened → closes at ````` or longer, NOT at ```

#### 8.5.1 Parsing Order (Normative)

Validators MUST process lines in this order:

1. **Track fence state:** Toggle in/out of code fence on fence delimiter lines
2. **If inside fence:** Ignore exclusion markers entirely (treat as literal text)
3. **If outside fence:** Process BEGIN/END markers per §8.4

Fence detection rules:
- Fence opens on line starting with 3+ backticks or tildes (after 0–3 leading spaces)
- Fence closes on line starting with same character, equal or greater count
- Info strings after opener are ignored
- Block quotes: strip leading `>` and optional space before applying fence/marker detection
- A line indented by 4+ spaces MUST NOT open or close a fence (it is an indented code block, per CommonMark)

**Indented code blocks (Normative):** Exclusion markers inside indented code blocks (lines with 4+ leading spaces, per CommonMark) MAY be interpreted as literal markers by validators. This specification does not require validators to detect indented code blocks. Authors SHOULD use fenced code blocks when documenting exclusion marker syntax to avoid ambiguity.

### 8.6 State Rules

| Condition | Constraint | Error Code |
|-----------|------------|------------|
| Exclusion blocks exist | `hitl-status` MUST be `REVIEWED_WITH_EXCEPTIONS` | E-EX05 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | ≥1 exclusion block MUST exist in body | E-EX06 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-reason` MUST be present (non-empty string) | E-EX07 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-ids` MUST list all exclusion block IDs | E-EX08 |
| Exclusion block ID in body | MUST be listed in `exceptions-ids` | E-EX09 |
| `exceptions-ids` format | MUST be a list of valid ID strings | E-EX10 |

### 8.7 YAML Fields for Exclusions

Add to frontmatter when exclusion blocks are present:

```yaml
hitl-status: REVIEWED_WITH_EXCEPTIONS
exceptions-reason: "Legacy OAuth implementation; no SME available"
exceptions-ids:
  - auth-legacy-1
  - oauth-flow-2
exclusions-coverage: 0.15  # Computed: excluded_bytes / total_body_bytes
```

### 8.8 Ingestion Policy Impact

A document with **any** exclusion blocks MUST have `rag-ingestable: false`, regardless of other status fields.

**No partial ingestion.** Documents are accepted or rejected as a whole.

### 8.9 Claims Inside Exclusion Blocks

Claims that appear inside exclusion blocks are **ignored entirely** during claim extraction. They do not generate entries in `hitl-claims` and are not validated.

Content inside exclusion blocks is also ignored for structural validation requirements (e.g., SOT `## Verified Claims` detection/validation).

Validators MAY emit a warning: "Claims detected inside exclusions were ignored."

### 8.10 Example

```yaml
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy prose; no SME available."
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users *(as of 2026-01-09)*.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

### 8.11 Redacted Export

The `redact_exclusions()` function (or CLI `export --redact-exclusions`) produces a copy with exclusion block **content** replaced by `[REDACTED]`. This enables:

- Safe ingestion by downstream tools that don't respect metadata flags
- Sharing documents with parties who shouldn't see quarantined content
- Audit trails that preserve structure without sensitive details

**Behavior:**

1. Exclusion markers (BEGIN/END comments) are **preserved**
2. Content between markers is replaced with `[REDACTED]\n`
3. `document-sha256` is **recomputed** for the redacted version
4. Line numbers will shift (the redacted document is shorter)

**Important:** The redacted document is a **new document**, not a modification of the original. It has a different hash and should be treated as a derivative work.

**Example:**

Original:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
Multiple lines of sensitive content here...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

After redaction:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
[REDACTED]
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

---

## 9. Computed Fields

### 9.1 `rag-ingestable` (Boolean)

This field is an **informational summary** for pipeline ingestion decisions.

**Computation:**
```python
rag-ingestable = (clarity-status == CLEAR) \
             and (hitl-status == REVIEWED) \
             and (exclusion_block_count == 0)
```

**Validator behavior:**
- Validators MUST compute this value
- Validators SHOULD write it to the document
- If declared value disagrees with computed → WARN (W-RI01)
- If declared value is not boolean → ERROR (E-RI01)

**Semantics:**
- `true` → Document is epistemically well-formed and human-reviewed
- `false` → Document MUST be rejected from production RAG

**Important:** `rag-ingestable: true` does NOT guarantee:
- Claims are factually true
- Human review was error-free
- Hallucinations are impossible

### 9.2 `exclusions-coverage` (Float 0.0–1.0)

Reports what fraction of body content is excluded.

**Computation:**
```python
exclusions-coverage = excluded_bytes / total_body_bytes
```

Where:
- `total_body_bytes` = UTF-8 byte count of canonical body (per §2.4 canonicalization)
- `excluded_bytes` = byte count from BEGIN marker through END marker (inclusive), including marker lines

**Byte counting rules (Normative):**
- Count bytes AFTER CRLF→LF normalization (consistent with hash canonicalization)
- Use UTF-8 encoded byte length, not character count
- If `total_body_bytes = 0`, `exclusions-coverage` MUST be `0.0` or omitted

**Validation:**
- If present, MUST be number in range 0.0–1.0 → else ERROR (E-EC01)
- If coverage ≥ 0.50 → WARN (W-EC01): majority excluded

---

## 10. Validation Error Codes

### 10.1 Severity Levels

- **ERROR (E-xxx):** Document invalid; MUST NOT pass validation
- **WARN (W-xxx):** Document valid but suboptimal; SHOULD be addressed

Validators SHOULD report actionable locations (line/section) when possible.

### 10.2 Structural Errors (E-ST)

| Code | Rule | Severity |
|------|------|----------|
| E-ST01 | YAML frontmatter parsing fails (syntax error) | ERROR |
| E-ST02 | Missing YAML frontmatter block at file start | ERROR |
| E-ST03 | Missing required frontmatter field | ERROR |
| E-ST04 | `processed-date` is in the future (UTC) | ERROR |
| E-ST05 | `points-passed` invalid (syntax or out of bounds 1–9) | ERROR |
| E-ST06 | Missing end marker (`<!-- CLARITY_GATE_END -->`) | ERROR |
| E-ST07 | End marker malformed (invalid status values) | ERROR |
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

### 10.3 State Consistency Errors (E-SC)

| Code | Rule | Severity |
|------|------|----------|
| E-SC01 | Invalid state: `UNCLEAR` with `hitl-status != PENDING` | ERROR |
| E-SC02 | `hitl-status: PENDING` but `hitl-pending-count = 0` | ERROR |
| E-SC03 | `hitl-status: REVIEWED` but `hitl-pending-count > 0` | ERROR |
| E-SC04 | `hitl-status: REVIEWED_WITH_EXCEPTIONS` but `hitl-pending-count > 0` | ERROR |
| E-SC05 | YAML and end marker status disagree | ERROR |

### 10.4 Exclusion Block Errors (E-EX)

| Code | Rule | Severity |
|------|------|----------|
| E-EX00 | Malformed exclusion marker line | ERROR |
| E-EX01 | BEGIN/END id mismatch | ERROR |
| E-EX02 | Nested exclusion blocks | ERROR |
| E-EX03 | Interleaved exclusion blocks | ERROR |
| E-EX04 | Duplicate exclusion IDs | ERROR |
| E-EX05 | Exclusion blocks exist but `hitl-status != REVIEWED_WITH_EXCEPTIONS` | ERROR |
| E-EX06 | `REVIEWED_WITH_EXCEPTIONS` but no exclusion blocks in body | ERROR |
| E-EX07 | `REVIEWED_WITH_EXCEPTIONS` but missing `exceptions-reason` | ERROR |
| E-EX08 | `exceptions-ids` references ID not present in body | ERROR |
| E-EX09 | Exclusion block ID in body but missing from `exceptions-ids` | ERROR |
| E-EX10 | `exceptions-ids` not a list of strings or contains invalid ID format | ERROR |

### 10.5 Hash Errors (E-HS)

| Code | Rule | Severity |
|------|------|----------|
| E-HS01 | `document-sha256` malformed (not 64-char lowercase hex) | ERROR |
| W-HS01 | `document-sha256` doesn't match computed | WARN |

### 10.6 Computed Field Errors

| Code | Rule | Severity |
|------|------|----------|
| E-RI01 | `rag-ingestable` present but not boolean | ERROR |
| W-RI01 | `rag-ingestable` disagrees with computed value | WARN |
| E-EC01 | `exclusions-coverage` not a number in range 0.0–1.0 | ERROR |
| W-EC01 | `exclusions-coverage` ≥ 0.50 (majority excluded) | WARN |

### 10.6.1 HITL Claim Errors (E-HC)

These codes apply to entries under the `hitl-claims` list in YAML frontmatter.

| Code | Rule | Severity |
|------|------|----------|
| E-HC01 | `hitl-claims` is present but not a list | ERROR |
| E-HC02 | A `hitl-claims` entry is missing required field `text` | ERROR |
| E-HC03 | A `hitl-claims` entry has `round` not in {A, B} | ERROR |
| E-HC04 | A `hitl-claims` entry has `confirmed-date` not a valid `YYYY-MM-DD` date | ERROR |

### 10.7 Table Errors (E-TB)

| Code | Rule | Severity |
|------|------|----------|
| E-TB01 | No `## Verified Claims` section (SOT only) | ERROR |
| E-TB02 | Table has no data rows | ERROR |
| E-TB03 | Required columns missing (Claim, Value, Source, Verified) | ERROR |
| E-TB04 | Column order wrong (Claim not first or Verified not last) | ERROR |
| E-TB05 | Empty cell in required column | ERROR |
| E-TB06 | Invalid date format in Verified column | ERROR |
| E-TB07 | Verified date in future (beyond 24h grace) | ERROR |

### 10.8 Promote/Demote Errors (E-PM, E-DM)

| Code | Rule | Severity |
|------|------|----------|
| E-PM01 | Promote: no verified claims and no table | ERROR |
| E-PM02 | Promote: file already has tier block | ERROR |
| W-DM01 | Demote: file has no tier block (no-op) | WARN |

### 10.9 Queue Errors (E-QU)

| Code | Rule | Severity |
|------|------|----------|
| E-QU01 | Claim ID not found in document | ERROR |
| W-QU01 | Claim text differs from queue | WARN |
| E-QU02 | Read-only queue fields modified | ERROR |
| W-QU02 | Queue expired (>7 days) | WARN |

### 10.10 Forward Compatibility

| Code | Rule | Severity |
|------|------|----------|
| W-FC01 | `clarity-gate-version` major exceeds validator capability | WARN |

When W-FC01 triggers, validators MUST also force `rag-ingestable: false` regardless of other checks.

---

## 11. Implementation Anti-Patterns

### 11.1 Parsing Anti-Patterns

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `.trim()` on delimiter lines | `.trimEnd()` (trailing only) | Leading whitespace invalidates `---` delimiter |
| Regex for YAML frontmatter | Line-by-line scan for exact `---` | Regex can match `---` in body content |
| Scan backwards from EOF for the first marker | Scan forward for the FIRST occurrence of the exact end marker string | Spec defines the end boundary as the first marker occurrence (§2.3) |
| Normalize on-disk content globally | Normalize only for hashing canonicalization (§2.4), otherwise preserve body bytes | Lossless editing requires preserving body text exactly |

### 11.2 Type Coercion Traps

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `Boolean(data['rag-ingestable'])` | `typeof value === 'boolean'` | `"false"` coerces to `true`! |
| `Number(data['exclusions-coverage'])` | `typeof value === 'number'` | `"0.5"` coerces silently |
| Trust YAML parser booleans | Check for `yes/no/on/off` | PyYAML treats these as booleans |

### 11.3 Cross-Language Parity

| Issue | Python | Node.js | Solution |
|-------|--------|---------|----------|
| YAML boolean keywords | PyYAML: `yes/no` → bool | js-yaml: configurable | Use explicit `true/false` only |
| Date comparison | `datetime.fromisoformat()` | `new Date()` | Parse as UTC date only |
| Unicode normalization | `unicodedata.normalize()` | Manual mapping | Use same char→char table |

### 11.4 Exclusion Block Offset Tracking

When computing `exclusions-coverage`:

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| Approximate bytes from char count | Extract actual UTF-8 bytes | Multi-byte chars (emoji, CJK) break ratio |
| Forget trailing newline after END | Include newline in excluded bytes | Spec says "through END marker" |
| Add +1 unconditionally | Clamp if END is on last line | No newline after final line |

---

## 12. Queue File Workflow

### 12.1 Queue File Schema

```yaml
schema-version: 1.0
generated: 2026-01-12T10:30:00Z
expires: 2026-01-19T10:30:00Z           # 7 days from generation
source-files-hash: <sha256>

documents:
  - file: docs/api-pricing.cgd.md
    file-hash: <sha256>
    claims:
      - id: claim-75fb137a
        text: "Base price is $99/mo"
        location: "api-pricing/1"
        round: B
        response: null                   # true | false | "estimated"
        notes: ""
```

### 12.2 Queue Expiry

Queues expire 7 days after generation. On apply:
- If expired → WARNING (W-QU02), suggest regeneration
- User can override with `--force`

### 12.3 apply-hitl Transaction Semantics

**Model: Fail-fast with checkpoint.**

```python
def apply_hitl(queue_path: str):
    queue = load_queue(queue_path)
    checkpoint = load_checkpoint(queue_path)
    
    start_index = checkpoint.last_success + 1 if checkpoint else 0
    
    for i, doc in enumerate(queue.documents[start_index:], start_index):
        try:
            validate_file_hash(doc)
            for claim in doc.claims:
                validate_claim(claim)
                apply_claim_response(claim)
            save_checkpoint(queue_path, last_success=i)
        except ValidationError as e:
            save_checkpoint(queue_path, last_success=i-1, error=e)
            raise ApplyError(f"Failed at document {i}: {e}")
    
    delete_checkpoint(queue_path)
    return Success
```

---

## 13. Round A/B Classification

### 13.1 Definition

| Round | Context | Meaning |
|-------|---------|---------|
| **A** | Interactive skill session | Source found while human was present |
| **B** | Batch CLI processing | Requires explicit human verification |

### 13.2 Environment Rules

| Environment | Round A | Round B |
|-------------|---------|---------|
| Claude.ai Skill | ✅ Available | ✅ Available |
| CLI batch | ❌ Never | ✅ Always |

---

## 14. CLI Commands

### 14.1 Package Names

| Platform | CLI Tool | Library |
|----------|----------|---------|
| npm | `clarity-gate` | `clarity-gate-core` |
| PyPI | `clarity-gate` | `clarity-gate-core` |

### 14.2 Command Reference

```bash
clarity-gate <command> [options]

Commands:
  verify <files...>           Validate format (local, no API)
  process <files...>          Create/update CGDs via Claude API
  apply-hitl <queue.yaml>     Apply HITL responses (with checkpoint)
  promote <file>              Promote CGD to SOT tier
  demote <file>               Demote SOT to CGD
  status <files...>           Show tier/status summary

Options:
  --api-key <key>             Anthropic API key (or ANTHROPIC_API_KEY env)
  --output <dir>              Output directory
  --hitl-queue <file>         Generate HITL queue file
  --dry-run                   Preview changes
  --reason <text>             Reason for demote
  --force                     Override warnings
```

---

## 15. YAML vs End Marker Authority

### 15.1 Rule

**YAML frontmatter is authoritative for CLI tools.**

The end marker (`Clarity Gate: CLEAR | REVIEWED`) is a passive signal for LLMs reading the document.

YAML frontmatter is authoritative for tooling decisions, but validators MUST enforce that the end marker status matches YAML status (`E-SC05`).

### 15.2 Mismatch Handling

If YAML and end marker disagree:

```
ERROR: E-SC05
  YAML says: UNCLEAR | PENDING
  End marker says: CLEAR | REVIEWED
  
  YAML is authoritative. Update end marker to match.
```

---

## 16. Known Limitations

### 16.1 Security Model

- Hash provides integrity, not authenticity
- No cryptographic signature (deferred to future version)
- YAML tampering detectable only via hash verification

### 16.2 Claim Matching

- ID-based matching (stable across minor edits)
- Text comparison for warnings only
- No fuzzy matching (exact comparison)

### 16.3 Table Validation

- English headers only (`## Verified Claims`)
- i18n support deferred

### 16.4 Slug Algorithm

- Non-ASCII characters stripped (not preserved like GFM)
- CJK/RTL headings may produce empty slugs (use `section-N` fallback)
- Intentional tradeoff for cross-platform compatibility

---

## 17. Examples

### 17.1 Minimal CGD

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
rag-ingestable: true
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.2 Full SOT

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: f6e5d4c3b2a1...
rag-ingestable: true
hitl-claims:
  - id: claim-75fb137a
    text: "Base price is $99/mo"
    value: "$99/mo"
    source: "Pricing page"
    location: "api-pricing/1"
    round: B
    confirmed-by: Maria
    confirmed-date: 2026-01-12
tier:
  level: SOT
  owner: Pricing Team
  version: 1.0
  promoted-date: 2026-01-12
  promoted-by: Maria
---

# API Pricing

Base price is **$99/mo** *(verified 2026-01-12)*.

## Verified Claims

| Claim | Value | Source | Verified |
|-------|-------|--------|----------|
| Base price is $99/mo | $99/mo | Pricing page | 2026-01-12 |

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.3 Document with Exclusions

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy OAuth; no SME available"
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

---

## 18. Test Vectors

### 18.1 Hash Computation

**Input file:**
```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: PENDING
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

**Expected SHA-256:**
```
d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
```


### 18.2 Claim ID Computation

**Test Vector 1:**
- text: `Base price is $99/mo`
- location: `api-pricing/1`
- **claim ID: `claim-75fb137a`**

**Test Vector 2:**
- text: `The API supports GraphQL`
- location: `features/1`
- **claim ID: `claim-eb357742`**

### 18.3 Slug Computation

| Input Heading | ASCII-Safe Slug |
|---------------|-----------------|
| `## API Pricing` | `api-pricing` |
| `## API & Pricing (v2.0)` | `api-pricing-v20` |
| `## 日本語` | `` (empty → `section-N`) |

### 18.4 Pipe Escaping (Idempotency)

| Input | Output |
|-------|--------|
| `A \| B` | `A \| B` (unchanged) |
| `A | B` | `A \| B` (escaped) |
| `A \| B | C` | `A \| B \| C` (mixed) |

---

## 19. Changelog

### v2.0 (January 2026)

- **Unified versioning:** Aligned internal spec version with release version
- **All v1.2 features included:** Exclusion blocks, computed fields, validation codes
- **Format finalized:** Implementation-ready specification

### v1.2 (January 2026)

- **Added Exclusion Blocks (§8)** for quarantining unresolved regions
- **Added computed fields:** `rag-ingestable`, `exclusions-coverage` (§9)
- **Added 37 validation error codes** with E-xxx/W-xxx namespace (§10)
- **Added implementation anti-patterns** (§11)
- **Added end marker uniqueness constraints** (§2.7): E-ST08, E-ST09
- **Added canonicalization scope clarification** (§2.4.1): hash protects canonical form, not rendered Markdown
- Hardened interoperability: slug disambiguation, backslash parity, YAML lossless editing
- Full test vectors with actual SHA-256 values

### v1.1 (January 2026)

- **Unified CGD and SOT into single format**
- SOT distinguished by presence of `tier:` block (no separate extension)
- Single `.cgd.md` extension for all documents
- Added Two-Round HITL (Round A: Derived, Round B: True HITL)
- Added stable claim IDs (`claim-<8-char-hash>`)
- ASCII-Safe slugification (not GFM)
- Idempotent pipe escaping

### v1.0 (December 2025)

- Initial specification
- Two separate formats: CGD (`.cgd.md`) and SOT (`.sot.md`)
- 9-point verification checklist
- Basic HITL verification

---

*End of Specification v2.0*
, r'^\s*(internal|external)\s+sources?\s*

### 1.4 Two Document States

| State | `tier:` block | Structured table | Use case |
|-------|---------------|------------------|----------|
| **CGD** | Absent | Optional | Verified text, safe for RAG |
| **SOT** | Present | Required | Canonical reference, machine-extractable |

---

## 2. Hash Specification

### 2.1 Scope

`document-sha256` covers YAML frontmatter + Markdown body, **excluding the hash line itself**.

#### 2.1.1 Hash Input Window (Normative)

Implementations MUST compute `document-sha256` over the exact substring of the document defined as:

- **Start boundary:** the first byte immediately after the opening YAML delimiter line `---` plus its trailing newline (`---\n`).
- **End boundary:** the first byte immediately before the first occurrence of the end marker string `<!-- CLARITY_GATE_END -->`.

Therefore, the hash input includes:

- YAML frontmatter content (excluding the opening `---` line)
- The closing YAML delimiter line (`---`) and everything after it up to (but not including) the end marker

The hash input excludes:

- The opening YAML delimiter line (`---`)
- The end marker line and all bytes after (and including) the first end marker occurrence

### 2.2 Hash Exclusion Rule

**CRITICAL:** The SHA-256 calculation MUST exclude the `document-sha256` field, including:
- The line containing `document-sha256:`
- Any indented continuation lines (for multiline YAML values)

**Regex pattern:** `^\s*document-sha256:.*$`

**Frontmatter-only scope (Normative):** The exclusion rule MUST apply only within the YAML frontmatter region (between the opening `---` line and the closing `---` line). Implementations MUST NOT remove or alter any `document-sha256:` text that appears in the Markdown body.

**Multiline continuation (Normative):** After excluding the key line matching `^\s*document-sha256:`, implementations MUST also exclude subsequent lines while BOTH conditions hold:

1. The parser is still within YAML frontmatter, and
2. The line's indentation is strictly greater than the indentation of the `document-sha256:` key line.

Continuation exclusion ends when indentation returns to less-than-or-equal to the key indentation, or when the closing `---` delimiter is reached.

**Exclusion blocks and hash (Normative):** Exclusion blocks (§8) do NOT affect hash computation. The `document-sha256` is computed over the full hash window including exclusion markers and content inside exclusion blocks. Rationale: The hash is an integrity mechanism; excluding quarantined regions would allow undetected tampering of exactly the risky content.

**Algorithm:**

```python
import re
import hashlib

def compute_hash(file_content: str) -> str:
    # 0. Pre-normalize for boundary detection (CRLF/BOM).
    #    Canonicalization (§2.4) is applied later, but we need stable slicing indices.
    working = file_content
    if working.startswith('\ufeff'):
        working = working[1:]
    working = working.replace('\r\n', '\n')

    # 1. Extract content between the opening YAML delimiter line and the end marker.
    start = working.index('---\n') + len('---\n')
    end = working.index('<!-- CLARITY_GATE_END -->')
    hashable = working[start:end]
    
    # 2. Remove document-sha256 line(s) — YAML frontmatter only
    lines = hashable.split('\n')
    filtered = []
    skip_multiline = False
    hash_indent = 0
    in_frontmatter = True
    
    for line in lines:
        # Detect end of YAML frontmatter
        if in_frontmatter and line.strip() == '---':
            in_frontmatter = False

        # Check if this is the hash line
        if in_frontmatter and re.match(r'^\s*document-sha256:', line):
            skip_multiline = True
            hash_indent = len(line) - len(line.lstrip())
            continue
        
        # If we're skipping multiline, check if this is a continuation
        if skip_multiline:
            current_indent = len(line) - len(line.lstrip())
            if in_frontmatter and current_indent > hash_indent:
                continue
            skip_multiline = False
        
        filtered.append(line)
    
    hashable = '\n'.join(filtered)
    
    # 3. Canonicalize
    hashable = canonicalize(hashable)
    
    # 4. Compute
    return hashlib.sha256(hashable.encode('utf-8')).hexdigest()
```

### 2.3 End Marker Detection

**The end boundary is the HTML comment `<!-- CLARITY_GATE_END -->`**, not a bare `---`.

This solves the ambiguity when `---` (horizontal rules) appear in the document body.

**Detection rule (Normative):** The end marker is recognized when:

1. The marker string `<!-- CLARITY_GATE_END -->` appears in the document, AND
2. The marker is **outside any fenced code block** (using §8.5 fence-tracking logic)

Markers inside fenced code blocks (`` ``` `` or `~~~`) MUST be ignored. This enables documentation about Clarity Gate itself to include the marker string in code examples without terminating the document prematurely ("Quine Protection").

**Implementation:** Parsers MUST track fence state while scanning for the marker, using the same fence detection rules as §8.5 (Exclusion Blocks in Fenced Code).

### 2.4 Canonicalization

Before hashing, normalize:

1. **Line endings:** CRLF → LF
2. **Trailing whitespace:** Remove per line
3. **Consecutive newlines:** Collapse 3+ newlines to 2
4. **Final newline:** Exactly one trailing LF
5. **Encoding:** UTF-8 NFC normalization
6. **BOM:** Remove if present
7. **Tabs:** Preserve (do not convert)
8. **Leading whitespace:** Preserve (significant in code blocks)

#### 2.4.1 Canonicalization Scope (Normative)

The hash protects the **canonical byte sequence**, not rendered Markdown semantics. Specifically:

- Trailing whitespace (including Markdown hard line breaks via `  \n`) is stripped
- 3+ consecutive newlines collapse to 2

Documents with different rendered appearance MAY share the same hash if they differ only in these canonicalized elements. This is intentional: LLM tokenizers normalize whitespace similarly, so these variations do not affect RAG ingestion semantics. Cross-platform hash stability requires stripping editor-introduced whitespace variations.

### 2.5 Hash Computation Order (Initial Creation)

1. Generate complete YAML with `document-sha256: PENDING`
2. Generate body content
3. Compute hash (excluding `document-sha256:` line)
4. Replace `PENDING` with actual hash
5. Verify by recomputing (must match)

### 2.6 When Hash Changes

| Action | Hash changes? | Reason |
|--------|---------------|--------|
| Process (add markers) | Yes | Body modified |
| Promote | Yes | YAML modified (tier block) |
| Demote | Yes | YAML + body modified |
| Edit content | Yes | Body modified |
| Edit YAML (except hash) | Yes | YAML modified |

### 2.7 End Marker Uniqueness (Normative)

The document MUST contain exactly one occurrence of `<!-- CLARITY_GATE_END -->`.

After the `Clarity Gate: <status> | <hitl-status>` line, only optional trailing whitespace and a single trailing newline are permitted until EOF.

| Code | Rule | Severity |
|------|------|----------|
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

---

## 3. SOT Requirements

### 3.1 Structured Claims Table

SOT documents MUST contain a `## Verified Claims` section with a valid table.

The `## Verified Claims` section and its table MUST be outside any exclusion block (§8). Content inside exclusion blocks is ignored for the purpose of satisfying SOT structural requirements.

### 3.2 Table Validation Rules

| Rule | Requirement | Error |
|------|-------------|-------|
| V1 | Section header matches `## Verified Claims` (case-insensitive, whitespace-normalized) | `E-TB01` |
| V2 | Table has at least 1 data row | `E-TB02` |
| V3 | Required columns present: Claim, Value, Source, Verified | `E-TB03` |
| V4 | Column order: Claim MUST be first, Verified MUST be last | `E-TB04` |
| V5 | Middle columns (Value, Source) may be in any order | (not an error) |
| V6 | Extra columns allowed anywhere except before Claim or after Verified | (not an error) |
| V7 | No empty cells in required columns (whitespace-only = empty, `-` = empty) | `E-TB05` |
| V8 | Verified column is valid date (YYYY-MM-DD, validated for real dates) | `E-TB06` |
| V9 | Verified date not in future (with 24h grace period) | `E-TB07` |

### 3.3 Date Validation Details

**Valid dates only:**
- `2026-02-29` → INVALID (2026 is not a leap year)
- `2026-04-31` → INVALID (April has 30 days)
- `2026-13-01` → INVALID (no month 13)

**Future check with timezone grace:**

To accommodate global users, the future date check allows a **24-hour grace period**:

```python
from datetime import datetime, timedelta, timezone

def is_future_date(date_str: str) -> bool:
    verified_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    grace_boundary = (datetime.now(timezone.utc) + timedelta(hours=24)).date()
    return verified_date > grace_boundary
```

### 3.4 Empty Cell Definition

A cell is considered **empty** if it contains:
- Only whitespace (spaces, tabs)
- Exactly the character `-` (dash placeholder)
- Nothing at all

### 3.5 Column Matching Examples

**Valid:**
```
| Claim | Value | Source | Verified |          ✓ Standard
| Claim | Source | Value | Verified |          ✓ Middle swapped
| Claim | Notes | Value | Source | Verified |  ✓ Extra column in middle
```

**Invalid:**
```
| Value | Claim | Source | Verified |          ✗ Claim not first
| Claim | Value | Source | Notes |             ✗ Verified not last
```

---

## 4. Table Auto-Generation

### 4.1 When Auto-Generation Occurs

`promote` auto-generates a table when:
- Document has confirmed claims in `hitl-claims`
- No `## Verified Claims` section exists
- No archived table exists

### 4.2 Generation Algorithm

```python
def generate_table(hitl_claims: list) -> str:
    rows = []
    for claim in hitl_claims:
        rows.append({
            'Claim': escape_pipes(claim['text']),
            'Value': escape_pipes(claim.get('value', '-')),
            'Source': escape_pipes(claim.get('source', 'HITL Verification')),
            'Verified': claim['confirmed-date']
        })
    
    return format_table(rows)
```

### 4.3 Pipe Character Escaping

**CRITICAL:** When populating table cells, implementations MUST escape **unescaped** pipe characters (`|`) as `\|`.

**Idempotency:** Already-escaped pipes (`\|`) must NOT be double-escaped to `\\|`.

**Escaped definition (Normative):** A pipe character (`|`) is considered escaped if and only if it is immediately preceded by an odd number of consecutive backslashes.

```python
def escape_pipes(text: str) -> str:
    """Escape unescaped pipe characters for Markdown table cells.
    
    Idempotent: already-escaped pipes (\\|) are not double-escaped.
    """
    result = []
    i = 0
    while i < len(text):
        if text[i] == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and text[j] == '\\':
                backslashes += 1
                j -= 1
            if backslashes % 2 == 1:
                result.append('|')
            else:
                result.append('\\|')
        else:
            result.append(text[i])
        i += 1
    return ''.join(result)
```

### 4.4 Claim/Value Column Population

The `Claim` column receives the **full claim text**. 

The `Value` column is populated from:
1. The `value` field in YAML (if present)
2. Otherwise, a dash (`-`)

**Do NOT attempt to parse claim text into Claim/Value.** This would require NLP and produce inconsistent results.

### 4.5 Table Row Parsing (Normative)

To ensure Python and Node.js implementations parse Markdown tables identically, implementations MUST split table rows into cells using the algorithm below.

**Algorithm (Normative):**

1. Given a single table row string (one line), remove a single leading `|` if present.
2. Remove a single trailing `|` if present.
3. Split the remaining string on `|` characters that are **NOT escaped**, where "escaped" uses the **odd backslash parity** rule from §4.3.
4. Trim leading/trailing whitespace from each resulting cell.

```python
def split_table_row(row: str) -> list[str]:
    if row.startswith('|'):
        row = row[1:]
    if row.endswith('|'):
        row = row[:-1]

    cells = []
    buf = []

    i = 0
    while i < len(row):
        ch = row[i]
        if ch == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and row[j] == '\\':
                backslashes += 1
                j -= 1

            if backslashes % 2 == 1:
                buf.append('|')
            else:
                cells.append(''.join(buf).strip())
                buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    cells.append(''.join(buf).strip())
    return cells
```

---

## 5. Claim ID Specification

### 5.1 ID Format

```
claim-<8-char-hex>
```

Example: `claim-75fb137a`

### 5.2 ID Computation

```python
def compute_claim_id(text: str, location: str) -> str:
    input_string = f"{text}|{location}"
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()
    return f"claim-{hash_hex[:8]}"
```

### 5.3 Location Context Format

`location` is a stable reference: `heading_slug/ordinal`

**Format:** `<nearest_heading_slug>/<ordinal_within_section>`

### 5.4 Slug Algorithm (ASCII-Safe Slugification)

**IMPORTANT:** This is **NOT** GitHub Flavored Markdown (GFM) slugification. GFM preserves non-ASCII characters; this algorithm strips them for maximum cross-platform compatibility.

**ASCII-Safe Slug Rules:**
1. Convert to lowercase
2. Remove all characters except ASCII alphanumerics (`a-z`, `0-9`), spaces, and hyphens
3. Replace spaces with hyphens
4. Collapse consecutive hyphens to single hyphen
5. Remove leading/trailing hyphens

```python
import re

def ascii_safe_slugify(heading: str) -> str:
    slug = heading.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug
```

**Special case — empty slug:** If a heading produces an empty slug (all non-ASCII), use `section-<ordinal>` where ordinal is the heading's position in the document (1-indexed).

**Special case — duplicate slugs (Normative):** If two or more headings produce the same slug, implementations MUST disambiguate by appending `-2`, `-3`, ... in document order.

**Special case — root:** Claims before any heading use `root` as the slug.

### 5.5 Ordinal Assignment

Ordinals are 1-indexed within each section.

```markdown
## Pricing

First claim here.     → location: pricing/1
Second claim here.    → location: pricing/2

## Features

First claim here.     → location: features/1
```

### 5.6 Claim Matching for Queue Apply

**Matching is by ID, not text.**

If ID matches but text differs slightly (whitespace, punctuation):
```
WARNING: Claim text differs from queue. Applying anyway.
  Queue: "Base price is $99/mo"
  Doc:   "Base price is $99/mo."
```

---

## 6. Promote Command

### 6.1 Basic Usage

```bash
clarity-gate promote doc.cgd.md --owner "Team" --version 1.0
```

### 6.2 Behavior

```
1. Validate document is CGD (no tier block)
2. Check for existing table:
   a. If ## Verified Claims exists → validate and proceed
   b. If ## Claims (Archived from SOT) exists → restore
   c. If neither → auto-generate from hitl-claims
3. If no claims and no table → ERROR: E-PM01
4. Add tier block to YAML
5. Recompute document-sha256
6. Update processed-date
```

### 6.3 Re-Promotion (Archived Table Restoration)

Detection uses **comment ID**, not header text:

```markdown
<!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-10 -->
## Claims (Archived from SOT)
```

---

## 7. Demote Command

### 7.1 Basic Usage

```bash
clarity-gate demote doc.cgd.md --reason "Superseded by v2"
```

### 7.2 Behavior

1. Validate document is SOT (has tier block)
2. If no tier block → WARNING, exit 0 (no-op)
3. Remove tier block from YAML
4. Find `## Verified Claims` section
5. Generate unique archive ID: `arch-<8-char-hex>`
6. Add archive comment with ID:
   ```markdown
   <!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-12, reason="Superseded by v2" -->
   ## Claims (Archived from SOT)
   ```
7. Recompute document-sha256
8. Update processed-date

### 7.3 Archive Comment Format

```
<!-- CLARITY_GATE_ARCHIVED: id=<id>, date=<ISO-date>, reason="<escaped-reason>" -->
```

**Escaping in reason:** Replace `"` with `&quot;` and `>` with `&gt;`.

---

## 8. Exclusion Blocks

### 8.1 Purpose

Exclusion Blocks mark document regions with unresolved ambiguity that are **unsafe for RAG ingestion**. They allow a document to be `CLEAR` overall while quarantining specific sections that couldn't be resolved.

**Use case:** Legacy documentation where no SME is available, or third-party content that can't be modified.

**Semantic note:** A document may have `clarity-status: CLEAR` with exclusion blocks present. This means "all non-excluded content is epistemically clear." However, such documents are still non-ingestable (`rag-ingestable: false`) by design. This is a "human-readable but quarantined" state.

### 8.2 Syntax

```markdown
<!-- CG-EXCLUSION:BEGIN id=<id> -->
Content with unresolved ambiguity...
<!-- CG-EXCLUSION:END id=<id> -->
```

#### 8.2.1 Marker Grammar (Normative)

Exclusion markers MUST appear alone on a line with this exact structure:

```
<optional-leading-spaces><!-- CG-EXCLUSION:BEGIN id=<id> --><optional-trailing-spaces>
<optional-leading-spaces><!-- CG-EXCLUSION:END id=<id> --><optional-trailing-spaces>
```

Where:
- Leading spaces (0+) are permitted (for indented Markdown)
- The token `<!-- CG-EXCLUSION:BEGIN id=` is **case-sensitive** and exact
- `<id>` matches `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`
- No additional attributes are permitted
- Trailing spaces are ignored

**Invalid (malformed) markers trigger E-EX00:**
- Extra attributes: `<!-- CG-EXCLUSION:BEGIN id=foo reason="bar" -->`
- Case variation: `<!-- cg-exclusion:begin id=foo -->`
- Inline with content: `text <!-- CG-EXCLUSION:BEGIN id=foo --> more text`

### 8.3 ID Format

IDs MUST match: `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`

### 8.4 Structural Rules (Normative)

| Rule | Violation | Error Code |
|------|-----------|------------|
| BEGIN and END `id` values MUST match exactly | Mismatch | E-EX01 |
| No nesting: BEGIN while inside another block | Nested BEGIN | E-EX02 |
| No overlap: END must close most recent BEGIN (stack discipline) | Interleaved | E-EX03 |
| No duplicate IDs: Same `id` used for multiple blocks | Reused ID | E-EX04 |

**Example of E-EX03 (interleaved blocks):**
```markdown
<!-- CG-EXCLUSION:BEGIN id=outer -->
<!-- CG-EXCLUSION:BEGIN id=inner -->
<!-- CG-EXCLUSION:END id=outer -->   ← ERROR: closes outer before inner
<!-- CG-EXCLUSION:END id=inner -->
```

### 8.5 Code Fence Handling

Exclusion markers inside fenced code blocks MUST be ignored by validators.

- A fenced code block begins with ``` or ~~~ (3+ characters)
- It ends at the next fence of the **same character** with **equal or greater length**
- Example: ````` opened → closes at ````` or longer, NOT at ```

#### 8.5.1 Parsing Order (Normative)

Validators MUST process lines in this order:

1. **Track fence state:** Toggle in/out of code fence on fence delimiter lines
2. **If inside fence:** Ignore exclusion markers entirely (treat as literal text)
3. **If outside fence:** Process BEGIN/END markers per §8.4

Fence detection rules:
- Fence opens on line starting with 3+ backticks or tildes (after 0–3 leading spaces)
- Fence closes on line starting with same character, equal or greater count
- Info strings after opener are ignored
- Block quotes: strip leading `>` and optional space before applying fence/marker detection
- A line indented by 4+ spaces MUST NOT open or close a fence (it is an indented code block, per CommonMark)

**Indented code blocks (Normative):** Exclusion markers inside indented code blocks (lines with 4+ leading spaces, per CommonMark) MAY be interpreted as literal markers by validators. This specification does not require validators to detect indented code blocks. Authors SHOULD use fenced code blocks when documenting exclusion marker syntax to avoid ambiguity.

### 8.6 State Rules

| Condition | Constraint | Error Code |
|-----------|------------|------------|
| Exclusion blocks exist | `hitl-status` MUST be `REVIEWED_WITH_EXCEPTIONS` | E-EX05 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | ≥1 exclusion block MUST exist in body | E-EX06 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-reason` MUST be present (non-empty string) | E-EX07 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-ids` MUST list all exclusion block IDs | E-EX08 |
| Exclusion block ID in body | MUST be listed in `exceptions-ids` | E-EX09 |
| `exceptions-ids` format | MUST be a list of valid ID strings | E-EX10 |

### 8.7 YAML Fields for Exclusions

Add to frontmatter when exclusion blocks are present:

```yaml
hitl-status: REVIEWED_WITH_EXCEPTIONS
exceptions-reason: "Legacy OAuth implementation; no SME available"
exceptions-ids:
  - auth-legacy-1
  - oauth-flow-2
exclusions-coverage: 0.15  # Computed: excluded_bytes / total_body_bytes
```

### 8.8 Ingestion Policy Impact

A document with **any** exclusion blocks MUST have `rag-ingestable: false`, regardless of other status fields.

**No partial ingestion.** Documents are accepted or rejected as a whole.

### 8.9 Claims Inside Exclusion Blocks

Claims that appear inside exclusion blocks are **ignored entirely** during claim extraction. They do not generate entries in `hitl-claims` and are not validated.

Content inside exclusion blocks is also ignored for structural validation requirements (e.g., SOT `## Verified Claims` detection/validation).

Validators MAY emit a warning: "Claims detected inside exclusions were ignored."

### 8.10 Example

```yaml
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy prose; no SME available."
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users *(as of 2026-01-09)*.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

### 8.11 Redacted Export

The `redact_exclusions()` function (or CLI `export --redact-exclusions`) produces a copy with exclusion block **content** replaced by `[REDACTED]`. This enables:

- Safe ingestion by downstream tools that don't respect metadata flags
- Sharing documents with parties who shouldn't see quarantined content
- Audit trails that preserve structure without sensitive details

**Behavior:**

1. Exclusion markers (BEGIN/END comments) are **preserved**
2. Content between markers is replaced with `[REDACTED]\n`
3. `document-sha256` is **recomputed** for the redacted version
4. Line numbers will shift (the redacted document is shorter)

**Important:** The redacted document is a **new document**, not a modification of the original. It has a different hash and should be treated as a derivative work.

**Example:**

Original:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
Multiple lines of sensitive content here...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

After redaction:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
[REDACTED]
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

---

## 9. Computed Fields

### 9.1 `rag-ingestable` (Boolean)

This field is an **informational summary** for pipeline ingestion decisions.

**Computation:**
```python
rag-ingestable = (clarity-status == CLEAR) \
             and (hitl-status == REVIEWED) \
             and (exclusion_block_count == 0)
```

**Validator behavior:**
- Validators MUST compute this value
- Validators SHOULD write it to the document
- If declared value disagrees with computed → WARN (W-RI01)
- If declared value is not boolean → ERROR (E-RI01)

**Semantics:**
- `true` → Document is epistemically well-formed and human-reviewed
- `false` → Document MUST be rejected from production RAG

**Important:** `rag-ingestable: true` does NOT guarantee:
- Claims are factually true
- Human review was error-free
- Hallucinations are impossible

### 9.2 `exclusions-coverage` (Float 0.0–1.0)

Reports what fraction of body content is excluded.

**Computation:**
```python
exclusions-coverage = excluded_bytes / total_body_bytes
```

Where:
- `total_body_bytes` = UTF-8 byte count of canonical body (per §2.4 canonicalization)
- `excluded_bytes` = byte count from BEGIN marker through END marker (inclusive), including marker lines

**Byte counting rules (Normative):**
- Count bytes AFTER CRLF→LF normalization (consistent with hash canonicalization)
- Use UTF-8 encoded byte length, not character count
- If `total_body_bytes = 0`, `exclusions-coverage` MUST be `0.0` or omitted

**Validation:**
- If present, MUST be number in range 0.0–1.0 → else ERROR (E-EC01)
- If coverage ≥ 0.50 → WARN (W-EC01): majority excluded

---

## 10. Validation Error Codes

### 10.1 Severity Levels

- **ERROR (E-xxx):** Document invalid; MUST NOT pass validation
- **WARN (W-xxx):** Document valid but suboptimal; SHOULD be addressed

Validators SHOULD report actionable locations (line/section) when possible.

### 10.2 Structural Errors (E-ST)

| Code | Rule | Severity |
|------|------|----------|
| E-ST01 | YAML frontmatter parsing fails (syntax error) | ERROR |
| E-ST02 | Missing YAML frontmatter block at file start | ERROR |
| E-ST03 | Missing required frontmatter field | ERROR |
| E-ST04 | `processed-date` is in the future (UTC) | ERROR |
| E-ST05 | `points-passed` invalid (syntax or out of bounds 1–9) | ERROR |
| E-ST06 | Missing end marker (`<!-- CLARITY_GATE_END -->`) | ERROR |
| E-ST07 | End marker malformed (invalid status values) | ERROR |
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

### 10.3 State Consistency Errors (E-SC)

| Code | Rule | Severity |
|------|------|----------|
| E-SC01 | Invalid state: `UNCLEAR` with `hitl-status != PENDING` | ERROR |
| E-SC02 | `hitl-status: PENDING` but `hitl-pending-count = 0` | ERROR |
| E-SC03 | `hitl-status: REVIEWED` but `hitl-pending-count > 0` | ERROR |
| E-SC04 | `hitl-status: REVIEWED_WITH_EXCEPTIONS` but `hitl-pending-count > 0` | ERROR |
| E-SC05 | YAML and end marker status disagree | ERROR |

### 10.4 Exclusion Block Errors (E-EX)

| Code | Rule | Severity |
|------|------|----------|
| E-EX00 | Malformed exclusion marker line | ERROR |
| E-EX01 | BEGIN/END id mismatch | ERROR |
| E-EX02 | Nested exclusion blocks | ERROR |
| E-EX03 | Interleaved exclusion blocks | ERROR |
| E-EX04 | Duplicate exclusion IDs | ERROR |
| E-EX05 | Exclusion blocks exist but `hitl-status != REVIEWED_WITH_EXCEPTIONS` | ERROR |
| E-EX06 | `REVIEWED_WITH_EXCEPTIONS` but no exclusion blocks in body | ERROR |
| E-EX07 | `REVIEWED_WITH_EXCEPTIONS` but missing `exceptions-reason` | ERROR |
| E-EX08 | `exceptions-ids` references ID not present in body | ERROR |
| E-EX09 | Exclusion block ID in body but missing from `exceptions-ids` | ERROR |
| E-EX10 | `exceptions-ids` not a list of strings or contains invalid ID format | ERROR |

### 10.5 Hash Errors (E-HS)

| Code | Rule | Severity |
|------|------|----------|
| E-HS01 | `document-sha256` malformed (not 64-char lowercase hex) | ERROR |
| W-HS01 | `document-sha256` doesn't match computed | WARN |

### 10.6 Computed Field Errors

| Code | Rule | Severity |
|------|------|----------|
| E-RI01 | `rag-ingestable` present but not boolean | ERROR |
| W-RI01 | `rag-ingestable` disagrees with computed value | WARN |
| E-EC01 | `exclusions-coverage` not a number in range 0.0–1.0 | ERROR |
| W-EC01 | `exclusions-coverage` ≥ 0.50 (majority excluded) | WARN |

### 10.6.1 HITL Claim Errors (E-HC)

These codes apply to entries under the `hitl-claims` list in YAML frontmatter.

| Code | Rule | Severity |
|------|------|----------|
| E-HC01 | `hitl-claims` is present but not a list | ERROR |
| E-HC02 | A `hitl-claims` entry is missing required field `text` | ERROR |
| E-HC03 | A `hitl-claims` entry has `round` not in {A, B} | ERROR |
| E-HC04 | A `hitl-claims` entry has `confirmed-date` not a valid `YYYY-MM-DD` date | ERROR |

### 10.7 Table Errors (E-TB)

| Code | Rule | Severity |
|------|------|----------|
| E-TB01 | No `## Verified Claims` section (SOT only) | ERROR |
| E-TB02 | Table has no data rows | ERROR |
| E-TB03 | Required columns missing (Claim, Value, Source, Verified) | ERROR |
| E-TB04 | Column order wrong (Claim not first or Verified not last) | ERROR |
| E-TB05 | Empty cell in required column | ERROR |
| E-TB06 | Invalid date format in Verified column | ERROR |
| E-TB07 | Verified date in future (beyond 24h grace) | ERROR |

### 10.8 Promote/Demote Errors (E-PM, E-DM)

| Code | Rule | Severity |
|------|------|----------|
| E-PM01 | Promote: no verified claims and no table | ERROR |
| E-PM02 | Promote: file already has tier block | ERROR |
| W-DM01 | Demote: file has no tier block (no-op) | WARN |

### 10.9 Queue Errors (E-QU)

| Code | Rule | Severity |
|------|------|----------|
| E-QU01 | Claim ID not found in document | ERROR |
| W-QU01 | Claim text differs from queue | WARN |
| E-QU02 | Read-only queue fields modified | ERROR |
| W-QU02 | Queue expired (>7 days) | WARN |

### 10.10 Forward Compatibility

| Code | Rule | Severity |
|------|------|----------|
| W-FC01 | `clarity-gate-version` major exceeds validator capability | WARN |

When W-FC01 triggers, validators MUST also force `rag-ingestable: false` regardless of other checks.

---

## 11. Implementation Anti-Patterns

### 11.1 Parsing Anti-Patterns

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `.trim()` on delimiter lines | `.trimEnd()` (trailing only) | Leading whitespace invalidates `---` delimiter |
| Regex for YAML frontmatter | Line-by-line scan for exact `---` | Regex can match `---` in body content |
| Scan backwards from EOF for the first marker | Scan forward for the FIRST occurrence of the exact end marker string | Spec defines the end boundary as the first marker occurrence (§2.3) |
| Normalize on-disk content globally | Normalize only for hashing canonicalization (§2.4), otherwise preserve body bytes | Lossless editing requires preserving body text exactly |

### 11.2 Type Coercion Traps

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `Boolean(data['rag-ingestable'])` | `typeof value === 'boolean'` | `"false"` coerces to `true`! |
| `Number(data['exclusions-coverage'])` | `typeof value === 'number'` | `"0.5"` coerces silently |
| Trust YAML parser booleans | Check for `yes/no/on/off` | PyYAML treats these as booleans |

### 11.3 Cross-Language Parity

| Issue | Python | Node.js | Solution |
|-------|--------|---------|----------|
| YAML boolean keywords | PyYAML: `yes/no` → bool | js-yaml: configurable | Use explicit `true/false` only |
| Date comparison | `datetime.fromisoformat()` | `new Date()` | Parse as UTC date only |
| Unicode normalization | `unicodedata.normalize()` | Manual mapping | Use same char→char table |

### 11.4 Exclusion Block Offset Tracking

When computing `exclusions-coverage`:

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| Approximate bytes from char count | Extract actual UTF-8 bytes | Multi-byte chars (emoji, CJK) break ratio |
| Forget trailing newline after END | Include newline in excluded bytes | Spec says "through END marker" |
| Add +1 unconditionally | Clamp if END is on last line | No newline after final line |

---

## 12. Queue File Workflow

### 12.1 Queue File Schema

```yaml
schema-version: 1.0
generated: 2026-01-12T10:30:00Z
expires: 2026-01-19T10:30:00Z           # 7 days from generation
source-files-hash: <sha256>

documents:
  - file: docs/api-pricing.cgd.md
    file-hash: <sha256>
    claims:
      - id: claim-75fb137a
        text: "Base price is $99/mo"
        location: "api-pricing/1"
        round: B
        response: null                   # true | false | "estimated"
        notes: ""
```

### 12.2 Queue Expiry

Queues expire 7 days after generation. On apply:
- If expired → WARNING (W-QU02), suggest regeneration
- User can override with `--force`

### 12.3 apply-hitl Transaction Semantics

**Model: Fail-fast with checkpoint.**

```python
def apply_hitl(queue_path: str):
    queue = load_queue(queue_path)
    checkpoint = load_checkpoint(queue_path)
    
    start_index = checkpoint.last_success + 1 if checkpoint else 0
    
    for i, doc in enumerate(queue.documents[start_index:], start_index):
        try:
            validate_file_hash(doc)
            for claim in doc.claims:
                validate_claim(claim)
                apply_claim_response(claim)
            save_checkpoint(queue_path, last_success=i)
        except ValidationError as e:
            save_checkpoint(queue_path, last_success=i-1, error=e)
            raise ApplyError(f"Failed at document {i}: {e}")
    
    delete_checkpoint(queue_path)
    return Success
```

---

## 13. Round A/B Classification

### 13.1 Definition

| Round | Context | Meaning |
|-------|---------|---------|
| **A** | Interactive skill session | Source found while human was present |
| **B** | Batch CLI processing | Requires explicit human verification |

### 13.2 Environment Rules

| Environment | Round A | Round B |
|-------------|---------|---------|
| Claude.ai Skill | ✅ Available | ✅ Available |
| CLI batch | ❌ Never | ✅ Always |

---

## 14. CLI Commands

### 14.1 Package Names

| Platform | CLI Tool | Library |
|----------|----------|---------|
| npm | `clarity-gate` | `clarity-gate-core` |
| PyPI | `clarity-gate` | `clarity-gate-core` |

### 14.2 Command Reference

```bash
clarity-gate <command> [options]

Commands:
  verify <files...>           Validate format (local, no API)
  process <files...>          Create/update CGDs via Claude API
  apply-hitl <queue.yaml>     Apply HITL responses (with checkpoint)
  promote <file>              Promote CGD to SOT tier
  demote <file>               Demote SOT to CGD
  status <files...>           Show tier/status summary

Options:
  --api-key <key>             Anthropic API key (or ANTHROPIC_API_KEY env)
  --output <dir>              Output directory
  --hitl-queue <file>         Generate HITL queue file
  --dry-run                   Preview changes
  --reason <text>             Reason for demote
  --force                     Override warnings
```

---

## 15. YAML vs End Marker Authority

### 15.1 Rule

**YAML frontmatter is authoritative for CLI tools.**

The end marker (`Clarity Gate: CLEAR | REVIEWED`) is a passive signal for LLMs reading the document.

YAML frontmatter is authoritative for tooling decisions, but validators MUST enforce that the end marker status matches YAML status (`E-SC05`).

### 15.2 Mismatch Handling

If YAML and end marker disagree:

```
ERROR: E-SC05
  YAML says: UNCLEAR | PENDING
  End marker says: CLEAR | REVIEWED
  
  YAML is authoritative. Update end marker to match.
```

---

## 16. Known Limitations

### 16.1 Security Model

- Hash provides integrity, not authenticity
- No cryptographic signature (deferred to future version)
- YAML tampering detectable only via hash verification

### 16.2 Claim Matching

- ID-based matching (stable across minor edits)
- Text comparison for warnings only
- No fuzzy matching (exact comparison)

### 16.3 Table Validation

- English headers only (`## Verified Claims`)
- i18n support deferred

### 16.4 Slug Algorithm

- Non-ASCII characters stripped (not preserved like GFM)
- CJK/RTL headings may produce empty slugs (use `section-N` fallback)
- Intentional tradeoff for cross-platform compatibility

---

## 17. Examples

### 17.1 Minimal CGD

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
rag-ingestable: true
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.2 Full SOT

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: f6e5d4c3b2a1...
rag-ingestable: true
hitl-claims:
  - id: claim-75fb137a
    text: "Base price is $99/mo"
    value: "$99/mo"
    source: "Pricing page"
    location: "api-pricing/1"
    round: B
    confirmed-by: Maria
    confirmed-date: 2026-01-12
tier:
  level: SOT
  owner: Pricing Team
  version: 1.0
  promoted-date: 2026-01-12
  promoted-by: Maria
---

# API Pricing

Base price is **$99/mo** *(verified 2026-01-12)*.

## Verified Claims

| Claim | Value | Source | Verified |
|-------|-------|--------|----------|
| Base price is $99/mo | $99/mo | Pricing page | 2026-01-12 |

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.3 Document with Exclusions

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy OAuth; no SME available"
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

---

## 18. Test Vectors

### 18.1 Hash Computation

**Input file:**
```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: PENDING
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

**Expected SHA-256:**
```
d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
```


### 18.2 Claim ID Computation

**Test Vector 1:**
- text: `Base price is $99/mo`
- location: `api-pricing/1`
- **claim ID: `claim-75fb137a`**

**Test Vector 2:**
- text: `The API supports GraphQL`
- location: `features/1`
- **claim ID: `claim-eb357742`**

### 18.3 Slug Computation

| Input Heading | ASCII-Safe Slug |
|---------------|-----------------|
| `## API Pricing` | `api-pricing` |
| `## API & Pricing (v2.0)` | `api-pricing-v20` |
| `## 日本語` | `` (empty → `section-N`) |

### 18.4 Pipe Escaping (Idempotency)

| Input | Output |
|-------|--------|
| `A \| B` | `A \| B` (unchanged) |
| `A | B` | `A \| B` (escaped) |
| `A \| B | C` | `A \| B \| C` (mixed) |

---

## 19. Changelog

### v2.0 (January 2026)

- **Unified versioning:** Aligned internal spec version with release version
- **All v1.2 features included:** Exclusion blocks, computed fields, validation codes
- **Format finalized:** Implementation-ready specification

### v1.2 (January 2026)

- **Added Exclusion Blocks (§8)** for quarantining unresolved regions
- **Added computed fields:** `rag-ingestable`, `exclusions-coverage` (§9)
- **Added 37 validation error codes** with E-xxx/W-xxx namespace (§10)
- **Added implementation anti-patterns** (§11)
- **Added end marker uniqueness constraints** (§2.7): E-ST08, E-ST09
- **Added canonicalization scope clarification** (§2.4.1): hash protects canonical form, not rendered Markdown
- Hardened interoperability: slug disambiguation, backslash parity, YAML lossless editing
- Full test vectors with actual SHA-256 values

### v1.1 (January 2026)

- **Unified CGD and SOT into single format**
- SOT distinguished by presence of `tier:` block (no separate extension)
- Single `.cgd.md` extension for all documents
- Added Two-Round HITL (Round A: Derived, Round B: True HITL)
- Added stable claim IDs (`claim-<8-char-hash>`)
- ASCII-Safe slugification (not GFM)
- Idempotent pipe escaping

### v1.0 (December 2025)

- Initial specification
- Two separate formats: CGD (`.cgd.md`) and SOT (`.sot.md`)
- 9-point verification checklist
- Basic HITL verification

---

*End of Specification v2.0*
, r'^\s*(TBD|TODO|N/?A)\s*

### 1.4 Two Document States

| State | `tier:` block | Structured table | Use case |
|-------|---------------|------------------|----------|
| **CGD** | Absent | Optional | Verified text, safe for RAG |
| **SOT** | Present | Required | Canonical reference, machine-extractable |

---

## 2. Hash Specification

### 2.1 Scope

`document-sha256` covers YAML frontmatter + Markdown body, **excluding the hash line itself**.

#### 2.1.1 Hash Input Window (Normative)

Implementations MUST compute `document-sha256` over the exact substring of the document defined as:

- **Start boundary:** the first byte immediately after the opening YAML delimiter line `---` plus its trailing newline (`---\n`).
- **End boundary:** the first byte immediately before the first occurrence of the end marker string `<!-- CLARITY_GATE_END -->`.

Therefore, the hash input includes:

- YAML frontmatter content (excluding the opening `---` line)
- The closing YAML delimiter line (`---`) and everything after it up to (but not including) the end marker

The hash input excludes:

- The opening YAML delimiter line (`---`)
- The end marker line and all bytes after (and including) the first end marker occurrence

### 2.2 Hash Exclusion Rule

**CRITICAL:** The SHA-256 calculation MUST exclude the `document-sha256` field, including:
- The line containing `document-sha256:`
- Any indented continuation lines (for multiline YAML values)

**Regex pattern:** `^\s*document-sha256:.*$`

**Frontmatter-only scope (Normative):** The exclusion rule MUST apply only within the YAML frontmatter region (between the opening `---` line and the closing `---` line). Implementations MUST NOT remove or alter any `document-sha256:` text that appears in the Markdown body.

**Multiline continuation (Normative):** After excluding the key line matching `^\s*document-sha256:`, implementations MUST also exclude subsequent lines while BOTH conditions hold:

1. The parser is still within YAML frontmatter, and
2. The line's indentation is strictly greater than the indentation of the `document-sha256:` key line.

Continuation exclusion ends when indentation returns to less-than-or-equal to the key indentation, or when the closing `---` delimiter is reached.

**Exclusion blocks and hash (Normative):** Exclusion blocks (§8) do NOT affect hash computation. The `document-sha256` is computed over the full hash window including exclusion markers and content inside exclusion blocks. Rationale: The hash is an integrity mechanism; excluding quarantined regions would allow undetected tampering of exactly the risky content.

**Algorithm:**

```python
import re
import hashlib

def compute_hash(file_content: str) -> str:
    # 0. Pre-normalize for boundary detection (CRLF/BOM).
    #    Canonicalization (§2.4) is applied later, but we need stable slicing indices.
    working = file_content
    if working.startswith('\ufeff'):
        working = working[1:]
    working = working.replace('\r\n', '\n')

    # 1. Extract content between the opening YAML delimiter line and the end marker.
    start = working.index('---\n') + len('---\n')
    end = working.index('<!-- CLARITY_GATE_END -->')
    hashable = working[start:end]
    
    # 2. Remove document-sha256 line(s) — YAML frontmatter only
    lines = hashable.split('\n')
    filtered = []
    skip_multiline = False
    hash_indent = 0
    in_frontmatter = True
    
    for line in lines:
        # Detect end of YAML frontmatter
        if in_frontmatter and line.strip() == '---':
            in_frontmatter = False

        # Check if this is the hash line
        if in_frontmatter and re.match(r'^\s*document-sha256:', line):
            skip_multiline = True
            hash_indent = len(line) - len(line.lstrip())
            continue
        
        # If we're skipping multiline, check if this is a continuation
        if skip_multiline:
            current_indent = len(line) - len(line.lstrip())
            if in_frontmatter and current_indent > hash_indent:
                continue
            skip_multiline = False
        
        filtered.append(line)
    
    hashable = '\n'.join(filtered)
    
    # 3. Canonicalize
    hashable = canonicalize(hashable)
    
    # 4. Compute
    return hashlib.sha256(hashable.encode('utf-8')).hexdigest()
```

### 2.3 End Marker Detection

**The end boundary is the HTML comment `<!-- CLARITY_GATE_END -->`**, not a bare `---`.

This solves the ambiguity when `---` (horizontal rules) appear in the document body.

**Detection rule (Normative):** The end marker is recognized when:

1. The marker string `<!-- CLARITY_GATE_END -->` appears in the document, AND
2. The marker is **outside any fenced code block** (using §8.5 fence-tracking logic)

Markers inside fenced code blocks (`` ``` `` or `~~~`) MUST be ignored. This enables documentation about Clarity Gate itself to include the marker string in code examples without terminating the document prematurely ("Quine Protection").

**Implementation:** Parsers MUST track fence state while scanning for the marker, using the same fence detection rules as §8.5 (Exclusion Blocks in Fenced Code).

### 2.4 Canonicalization

Before hashing, normalize:

1. **Line endings:** CRLF → LF
2. **Trailing whitespace:** Remove per line
3. **Consecutive newlines:** Collapse 3+ newlines to 2
4. **Final newline:** Exactly one trailing LF
5. **Encoding:** UTF-8 NFC normalization
6. **BOM:** Remove if present
7. **Tabs:** Preserve (do not convert)
8. **Leading whitespace:** Preserve (significant in code blocks)

#### 2.4.1 Canonicalization Scope (Normative)

The hash protects the **canonical byte sequence**, not rendered Markdown semantics. Specifically:

- Trailing whitespace (including Markdown hard line breaks via `  \n`) is stripped
- 3+ consecutive newlines collapse to 2

Documents with different rendered appearance MAY share the same hash if they differ only in these canonicalized elements. This is intentional: LLM tokenizers normalize whitespace similarly, so these variations do not affect RAG ingestion semantics. Cross-platform hash stability requires stripping editor-introduced whitespace variations.

### 2.5 Hash Computation Order (Initial Creation)

1. Generate complete YAML with `document-sha256: PENDING`
2. Generate body content
3. Compute hash (excluding `document-sha256:` line)
4. Replace `PENDING` with actual hash
5. Verify by recomputing (must match)

### 2.6 When Hash Changes

| Action | Hash changes? | Reason |
|--------|---------------|--------|
| Process (add markers) | Yes | Body modified |
| Promote | Yes | YAML modified (tier block) |
| Demote | Yes | YAML + body modified |
| Edit content | Yes | Body modified |
| Edit YAML (except hash) | Yes | YAML modified |

### 2.7 End Marker Uniqueness (Normative)

The document MUST contain exactly one occurrence of `<!-- CLARITY_GATE_END -->`.

After the `Clarity Gate: <status> | <hitl-status>` line, only optional trailing whitespace and a single trailing newline are permitted until EOF.

| Code | Rule | Severity |
|------|------|----------|
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

---

## 3. SOT Requirements

### 3.1 Structured Claims Table

SOT documents MUST contain a `## Verified Claims` section with a valid table.

The `## Verified Claims` section and its table MUST be outside any exclusion block (§8). Content inside exclusion blocks is ignored for the purpose of satisfying SOT structural requirements.

### 3.2 Table Validation Rules

| Rule | Requirement | Error |
|------|-------------|-------|
| V1 | Section header matches `## Verified Claims` (case-insensitive, whitespace-normalized) | `E-TB01` |
| V2 | Table has at least 1 data row | `E-TB02` |
| V3 | Required columns present: Claim, Value, Source, Verified | `E-TB03` |
| V4 | Column order: Claim MUST be first, Verified MUST be last | `E-TB04` |
| V5 | Middle columns (Value, Source) may be in any order | (not an error) |
| V6 | Extra columns allowed anywhere except before Claim or after Verified | (not an error) |
| V7 | No empty cells in required columns (whitespace-only = empty, `-` = empty) | `E-TB05` |
| V8 | Verified column is valid date (YYYY-MM-DD, validated for real dates) | `E-TB06` |
| V9 | Verified date not in future (with 24h grace period) | `E-TB07` |

### 3.3 Date Validation Details

**Valid dates only:**
- `2026-02-29` → INVALID (2026 is not a leap year)
- `2026-04-31` → INVALID (April has 30 days)
- `2026-13-01` → INVALID (no month 13)

**Future check with timezone grace:**

To accommodate global users, the future date check allows a **24-hour grace period**:

```python
from datetime import datetime, timedelta, timezone

def is_future_date(date_str: str) -> bool:
    verified_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    grace_boundary = (datetime.now(timezone.utc) + timedelta(hours=24)).date()
    return verified_date > grace_boundary
```

### 3.4 Empty Cell Definition

A cell is considered **empty** if it contains:
- Only whitespace (spaces, tabs)
- Exactly the character `-` (dash placeholder)
- Nothing at all

### 3.5 Column Matching Examples

**Valid:**
```
| Claim | Value | Source | Verified |          ✓ Standard
| Claim | Source | Value | Verified |          ✓ Middle swapped
| Claim | Notes | Value | Source | Verified |  ✓ Extra column in middle
```

**Invalid:**
```
| Value | Claim | Source | Verified |          ✗ Claim not first
| Claim | Value | Source | Notes |             ✗ Verified not last
```

---

## 4. Table Auto-Generation

### 4.1 When Auto-Generation Occurs

`promote` auto-generates a table when:
- Document has confirmed claims in `hitl-claims`
- No `## Verified Claims` section exists
- No archived table exists

### 4.2 Generation Algorithm

```python
def generate_table(hitl_claims: list) -> str:
    rows = []
    for claim in hitl_claims:
        rows.append({
            'Claim': escape_pipes(claim['text']),
            'Value': escape_pipes(claim.get('value', '-')),
            'Source': escape_pipes(claim.get('source', 'HITL Verification')),
            'Verified': claim['confirmed-date']
        })
    
    return format_table(rows)
```

### 4.3 Pipe Character Escaping

**CRITICAL:** When populating table cells, implementations MUST escape **unescaped** pipe characters (`|`) as `\|`.

**Idempotency:** Already-escaped pipes (`\|`) must NOT be double-escaped to `\\|`.

**Escaped definition (Normative):** A pipe character (`|`) is considered escaped if and only if it is immediately preceded by an odd number of consecutive backslashes.

```python
def escape_pipes(text: str) -> str:
    """Escape unescaped pipe characters for Markdown table cells.
    
    Idempotent: already-escaped pipes (\\|) are not double-escaped.
    """
    result = []
    i = 0
    while i < len(text):
        if text[i] == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and text[j] == '\\':
                backslashes += 1
                j -= 1
            if backslashes % 2 == 1:
                result.append('|')
            else:
                result.append('\\|')
        else:
            result.append(text[i])
        i += 1
    return ''.join(result)
```

### 4.4 Claim/Value Column Population

The `Claim` column receives the **full claim text**. 

The `Value` column is populated from:
1. The `value` field in YAML (if present)
2. Otherwise, a dash (`-`)

**Do NOT attempt to parse claim text into Claim/Value.** This would require NLP and produce inconsistent results.

### 4.5 Table Row Parsing (Normative)

To ensure Python and Node.js implementations parse Markdown tables identically, implementations MUST split table rows into cells using the algorithm below.

**Algorithm (Normative):**

1. Given a single table row string (one line), remove a single leading `|` if present.
2. Remove a single trailing `|` if present.
3. Split the remaining string on `|` characters that are **NOT escaped**, where "escaped" uses the **odd backslash parity** rule from §4.3.
4. Trim leading/trailing whitespace from each resulting cell.

```python
def split_table_row(row: str) -> list[str]:
    if row.startswith('|'):
        row = row[1:]
    if row.endswith('|'):
        row = row[:-1]

    cells = []
    buf = []

    i = 0
    while i < len(row):
        ch = row[i]
        if ch == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and row[j] == '\\':
                backslashes += 1
                j -= 1

            if backslashes % 2 == 1:
                buf.append('|')
            else:
                cells.append(''.join(buf).strip())
                buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    cells.append(''.join(buf).strip())
    return cells
```

---

## 5. Claim ID Specification

### 5.1 ID Format

```
claim-<8-char-hex>
```

Example: `claim-75fb137a`

### 5.2 ID Computation

```python
def compute_claim_id(text: str, location: str) -> str:
    input_string = f"{text}|{location}"
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()
    return f"claim-{hash_hex[:8]}"
```

### 5.3 Location Context Format

`location` is a stable reference: `heading_slug/ordinal`

**Format:** `<nearest_heading_slug>/<ordinal_within_section>`

### 5.4 Slug Algorithm (ASCII-Safe Slugification)

**IMPORTANT:** This is **NOT** GitHub Flavored Markdown (GFM) slugification. GFM preserves non-ASCII characters; this algorithm strips them for maximum cross-platform compatibility.

**ASCII-Safe Slug Rules:**
1. Convert to lowercase
2. Remove all characters except ASCII alphanumerics (`a-z`, `0-9`), spaces, and hyphens
3. Replace spaces with hyphens
4. Collapse consecutive hyphens to single hyphen
5. Remove leading/trailing hyphens

```python
import re

def ascii_safe_slugify(heading: str) -> str:
    slug = heading.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug
```

**Special case — empty slug:** If a heading produces an empty slug (all non-ASCII), use `section-<ordinal>` where ordinal is the heading's position in the document (1-indexed).

**Special case — duplicate slugs (Normative):** If two or more headings produce the same slug, implementations MUST disambiguate by appending `-2`, `-3`, ... in document order.

**Special case — root:** Claims before any heading use `root` as the slug.

### 5.5 Ordinal Assignment

Ordinals are 1-indexed within each section.

```markdown
## Pricing

First claim here.     → location: pricing/1
Second claim here.    → location: pricing/2

## Features

First claim here.     → location: features/1
```

### 5.6 Claim Matching for Queue Apply

**Matching is by ID, not text.**

If ID matches but text differs slightly (whitespace, punctuation):
```
WARNING: Claim text differs from queue. Applying anyway.
  Queue: "Base price is $99/mo"
  Doc:   "Base price is $99/mo."
```

---

## 6. Promote Command

### 6.1 Basic Usage

```bash
clarity-gate promote doc.cgd.md --owner "Team" --version 1.0
```

### 6.2 Behavior

```
1. Validate document is CGD (no tier block)
2. Check for existing table:
   a. If ## Verified Claims exists → validate and proceed
   b. If ## Claims (Archived from SOT) exists → restore
   c. If neither → auto-generate from hitl-claims
3. If no claims and no table → ERROR: E-PM01
4. Add tier block to YAML
5. Recompute document-sha256
6. Update processed-date
```

### 6.3 Re-Promotion (Archived Table Restoration)

Detection uses **comment ID**, not header text:

```markdown
<!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-10 -->
## Claims (Archived from SOT)
```

---

## 7. Demote Command

### 7.1 Basic Usage

```bash
clarity-gate demote doc.cgd.md --reason "Superseded by v2"
```

### 7.2 Behavior

1. Validate document is SOT (has tier block)
2. If no tier block → WARNING, exit 0 (no-op)
3. Remove tier block from YAML
4. Find `## Verified Claims` section
5. Generate unique archive ID: `arch-<8-char-hex>`
6. Add archive comment with ID:
   ```markdown
   <!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-12, reason="Superseded by v2" -->
   ## Claims (Archived from SOT)
   ```
7. Recompute document-sha256
8. Update processed-date

### 7.3 Archive Comment Format

```
<!-- CLARITY_GATE_ARCHIVED: id=<id>, date=<ISO-date>, reason="<escaped-reason>" -->
```

**Escaping in reason:** Replace `"` with `&quot;` and `>` with `&gt;`.

---

## 8. Exclusion Blocks

### 8.1 Purpose

Exclusion Blocks mark document regions with unresolved ambiguity that are **unsafe for RAG ingestion**. They allow a document to be `CLEAR` overall while quarantining specific sections that couldn't be resolved.

**Use case:** Legacy documentation where no SME is available, or third-party content that can't be modified.

**Semantic note:** A document may have `clarity-status: CLEAR` with exclusion blocks present. This means "all non-excluded content is epistemically clear." However, such documents are still non-ingestable (`rag-ingestable: false`) by design. This is a "human-readable but quarantined" state.

### 8.2 Syntax

```markdown
<!-- CG-EXCLUSION:BEGIN id=<id> -->
Content with unresolved ambiguity...
<!-- CG-EXCLUSION:END id=<id> -->
```

#### 8.2.1 Marker Grammar (Normative)

Exclusion markers MUST appear alone on a line with this exact structure:

```
<optional-leading-spaces><!-- CG-EXCLUSION:BEGIN id=<id> --><optional-trailing-spaces>
<optional-leading-spaces><!-- CG-EXCLUSION:END id=<id> --><optional-trailing-spaces>
```

Where:
- Leading spaces (0+) are permitted (for indented Markdown)
- The token `<!-- CG-EXCLUSION:BEGIN id=` is **case-sensitive** and exact
- `<id>` matches `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`
- No additional attributes are permitted
- Trailing spaces are ignored

**Invalid (malformed) markers trigger E-EX00:**
- Extra attributes: `<!-- CG-EXCLUSION:BEGIN id=foo reason="bar" -->`
- Case variation: `<!-- cg-exclusion:begin id=foo -->`
- Inline with content: `text <!-- CG-EXCLUSION:BEGIN id=foo --> more text`

### 8.3 ID Format

IDs MUST match: `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`

### 8.4 Structural Rules (Normative)

| Rule | Violation | Error Code |
|------|-----------|------------|
| BEGIN and END `id` values MUST match exactly | Mismatch | E-EX01 |
| No nesting: BEGIN while inside another block | Nested BEGIN | E-EX02 |
| No overlap: END must close most recent BEGIN (stack discipline) | Interleaved | E-EX03 |
| No duplicate IDs: Same `id` used for multiple blocks | Reused ID | E-EX04 |

**Example of E-EX03 (interleaved blocks):**
```markdown
<!-- CG-EXCLUSION:BEGIN id=outer -->
<!-- CG-EXCLUSION:BEGIN id=inner -->
<!-- CG-EXCLUSION:END id=outer -->   ← ERROR: closes outer before inner
<!-- CG-EXCLUSION:END id=inner -->
```

### 8.5 Code Fence Handling

Exclusion markers inside fenced code blocks MUST be ignored by validators.

- A fenced code block begins with ``` or ~~~ (3+ characters)
- It ends at the next fence of the **same character** with **equal or greater length**
- Example: ````` opened → closes at ````` or longer, NOT at ```

#### 8.5.1 Parsing Order (Normative)

Validators MUST process lines in this order:

1. **Track fence state:** Toggle in/out of code fence on fence delimiter lines
2. **If inside fence:** Ignore exclusion markers entirely (treat as literal text)
3. **If outside fence:** Process BEGIN/END markers per §8.4

Fence detection rules:
- Fence opens on line starting with 3+ backticks or tildes (after 0–3 leading spaces)
- Fence closes on line starting with same character, equal or greater count
- Info strings after opener are ignored
- Block quotes: strip leading `>` and optional space before applying fence/marker detection
- A line indented by 4+ spaces MUST NOT open or close a fence (it is an indented code block, per CommonMark)

**Indented code blocks (Normative):** Exclusion markers inside indented code blocks (lines with 4+ leading spaces, per CommonMark) MAY be interpreted as literal markers by validators. This specification does not require validators to detect indented code blocks. Authors SHOULD use fenced code blocks when documenting exclusion marker syntax to avoid ambiguity.

### 8.6 State Rules

| Condition | Constraint | Error Code |
|-----------|------------|------------|
| Exclusion blocks exist | `hitl-status` MUST be `REVIEWED_WITH_EXCEPTIONS` | E-EX05 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | ≥1 exclusion block MUST exist in body | E-EX06 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-reason` MUST be present (non-empty string) | E-EX07 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-ids` MUST list all exclusion block IDs | E-EX08 |
| Exclusion block ID in body | MUST be listed in `exceptions-ids` | E-EX09 |
| `exceptions-ids` format | MUST be a list of valid ID strings | E-EX10 |

### 8.7 YAML Fields for Exclusions

Add to frontmatter when exclusion blocks are present:

```yaml
hitl-status: REVIEWED_WITH_EXCEPTIONS
exceptions-reason: "Legacy OAuth implementation; no SME available"
exceptions-ids:
  - auth-legacy-1
  - oauth-flow-2
exclusions-coverage: 0.15  # Computed: excluded_bytes / total_body_bytes
```

### 8.8 Ingestion Policy Impact

A document with **any** exclusion blocks MUST have `rag-ingestable: false`, regardless of other status fields.

**No partial ingestion.** Documents are accepted or rejected as a whole.

### 8.9 Claims Inside Exclusion Blocks

Claims that appear inside exclusion blocks are **ignored entirely** during claim extraction. They do not generate entries in `hitl-claims` and are not validated.

Content inside exclusion blocks is also ignored for structural validation requirements (e.g., SOT `## Verified Claims` detection/validation).

Validators MAY emit a warning: "Claims detected inside exclusions were ignored."

### 8.10 Example

```yaml
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy prose; no SME available."
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users *(as of 2026-01-09)*.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

### 8.11 Redacted Export

The `redact_exclusions()` function (or CLI `export --redact-exclusions`) produces a copy with exclusion block **content** replaced by `[REDACTED]`. This enables:

- Safe ingestion by downstream tools that don't respect metadata flags
- Sharing documents with parties who shouldn't see quarantined content
- Audit trails that preserve structure without sensitive details

**Behavior:**

1. Exclusion markers (BEGIN/END comments) are **preserved**
2. Content between markers is replaced with `[REDACTED]\n`
3. `document-sha256` is **recomputed** for the redacted version
4. Line numbers will shift (the redacted document is shorter)

**Important:** The redacted document is a **new document**, not a modification of the original. It has a different hash and should be treated as a derivative work.

**Example:**

Original:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
Multiple lines of sensitive content here...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

After redaction:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
[REDACTED]
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

---

## 9. Computed Fields

### 9.1 `rag-ingestable` (Boolean)

This field is an **informational summary** for pipeline ingestion decisions.

**Computation:**
```python
rag-ingestable = (clarity-status == CLEAR) \
             and (hitl-status == REVIEWED) \
             and (exclusion_block_count == 0)
```

**Validator behavior:**
- Validators MUST compute this value
- Validators SHOULD write it to the document
- If declared value disagrees with computed → WARN (W-RI01)
- If declared value is not boolean → ERROR (E-RI01)

**Semantics:**
- `true` → Document is epistemically well-formed and human-reviewed
- `false` → Document MUST be rejected from production RAG

**Important:** `rag-ingestable: true` does NOT guarantee:
- Claims are factually true
- Human review was error-free
- Hallucinations are impossible

### 9.2 `exclusions-coverage` (Float 0.0–1.0)

Reports what fraction of body content is excluded.

**Computation:**
```python
exclusions-coverage = excluded_bytes / total_body_bytes
```

Where:
- `total_body_bytes` = UTF-8 byte count of canonical body (per §2.4 canonicalization)
- `excluded_bytes` = byte count from BEGIN marker through END marker (inclusive), including marker lines

**Byte counting rules (Normative):**
- Count bytes AFTER CRLF→LF normalization (consistent with hash canonicalization)
- Use UTF-8 encoded byte length, not character count
- If `total_body_bytes = 0`, `exclusions-coverage` MUST be `0.0` or omitted

**Validation:**
- If present, MUST be number in range 0.0–1.0 → else ERROR (E-EC01)
- If coverage ≥ 0.50 → WARN (W-EC01): majority excluded

---

## 10. Validation Error Codes

### 10.1 Severity Levels

- **ERROR (E-xxx):** Document invalid; MUST NOT pass validation
- **WARN (W-xxx):** Document valid but suboptimal; SHOULD be addressed

Validators SHOULD report actionable locations (line/section) when possible.

### 10.2 Structural Errors (E-ST)

| Code | Rule | Severity |
|------|------|----------|
| E-ST01 | YAML frontmatter parsing fails (syntax error) | ERROR |
| E-ST02 | Missing YAML frontmatter block at file start | ERROR |
| E-ST03 | Missing required frontmatter field | ERROR |
| E-ST04 | `processed-date` is in the future (UTC) | ERROR |
| E-ST05 | `points-passed` invalid (syntax or out of bounds 1–9) | ERROR |
| E-ST06 | Missing end marker (`<!-- CLARITY_GATE_END -->`) | ERROR |
| E-ST07 | End marker malformed (invalid status values) | ERROR |
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

### 10.3 State Consistency Errors (E-SC)

| Code | Rule | Severity |
|------|------|----------|
| E-SC01 | Invalid state: `UNCLEAR` with `hitl-status != PENDING` | ERROR |
| E-SC02 | `hitl-status: PENDING` but `hitl-pending-count = 0` | ERROR |
| E-SC03 | `hitl-status: REVIEWED` but `hitl-pending-count > 0` | ERROR |
| E-SC04 | `hitl-status: REVIEWED_WITH_EXCEPTIONS` but `hitl-pending-count > 0` | ERROR |
| E-SC05 | YAML and end marker status disagree | ERROR |

### 10.4 Exclusion Block Errors (E-EX)

| Code | Rule | Severity |
|------|------|----------|
| E-EX00 | Malformed exclusion marker line | ERROR |
| E-EX01 | BEGIN/END id mismatch | ERROR |
| E-EX02 | Nested exclusion blocks | ERROR |
| E-EX03 | Interleaved exclusion blocks | ERROR |
| E-EX04 | Duplicate exclusion IDs | ERROR |
| E-EX05 | Exclusion blocks exist but `hitl-status != REVIEWED_WITH_EXCEPTIONS` | ERROR |
| E-EX06 | `REVIEWED_WITH_EXCEPTIONS` but no exclusion blocks in body | ERROR |
| E-EX07 | `REVIEWED_WITH_EXCEPTIONS` but missing `exceptions-reason` | ERROR |
| E-EX08 | `exceptions-ids` references ID not present in body | ERROR |
| E-EX09 | Exclusion block ID in body but missing from `exceptions-ids` | ERROR |
| E-EX10 | `exceptions-ids` not a list of strings or contains invalid ID format | ERROR |

### 10.5 Hash Errors (E-HS)

| Code | Rule | Severity |
|------|------|----------|
| E-HS01 | `document-sha256` malformed (not 64-char lowercase hex) | ERROR |
| W-HS01 | `document-sha256` doesn't match computed | WARN |

### 10.6 Computed Field Errors

| Code | Rule | Severity |
|------|------|----------|
| E-RI01 | `rag-ingestable` present but not boolean | ERROR |
| W-RI01 | `rag-ingestable` disagrees with computed value | WARN |
| E-EC01 | `exclusions-coverage` not a number in range 0.0–1.0 | ERROR |
| W-EC01 | `exclusions-coverage` ≥ 0.50 (majority excluded) | WARN |

### 10.6.1 HITL Claim Errors (E-HC)

These codes apply to entries under the `hitl-claims` list in YAML frontmatter.

| Code | Rule | Severity |
|------|------|----------|
| E-HC01 | `hitl-claims` is present but not a list | ERROR |
| E-HC02 | A `hitl-claims` entry is missing required field `text` | ERROR |
| E-HC03 | A `hitl-claims` entry has `round` not in {A, B} | ERROR |
| E-HC04 | A `hitl-claims` entry has `confirmed-date` not a valid `YYYY-MM-DD` date | ERROR |

### 10.7 Table Errors (E-TB)

| Code | Rule | Severity |
|------|------|----------|
| E-TB01 | No `## Verified Claims` section (SOT only) | ERROR |
| E-TB02 | Table has no data rows | ERROR |
| E-TB03 | Required columns missing (Claim, Value, Source, Verified) | ERROR |
| E-TB04 | Column order wrong (Claim not first or Verified not last) | ERROR |
| E-TB05 | Empty cell in required column | ERROR |
| E-TB06 | Invalid date format in Verified column | ERROR |
| E-TB07 | Verified date in future (beyond 24h grace) | ERROR |

### 10.8 Promote/Demote Errors (E-PM, E-DM)

| Code | Rule | Severity |
|------|------|----------|
| E-PM01 | Promote: no verified claims and no table | ERROR |
| E-PM02 | Promote: file already has tier block | ERROR |
| W-DM01 | Demote: file has no tier block (no-op) | WARN |

### 10.9 Queue Errors (E-QU)

| Code | Rule | Severity |
|------|------|----------|
| E-QU01 | Claim ID not found in document | ERROR |
| W-QU01 | Claim text differs from queue | WARN |
| E-QU02 | Read-only queue fields modified | ERROR |
| W-QU02 | Queue expired (>7 days) | WARN |

### 10.10 Forward Compatibility

| Code | Rule | Severity |
|------|------|----------|
| W-FC01 | `clarity-gate-version` major exceeds validator capability | WARN |

When W-FC01 triggers, validators MUST also force `rag-ingestable: false` regardless of other checks.

---

## 11. Implementation Anti-Patterns

### 11.1 Parsing Anti-Patterns

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `.trim()` on delimiter lines | `.trimEnd()` (trailing only) | Leading whitespace invalidates `---` delimiter |
| Regex for YAML frontmatter | Line-by-line scan for exact `---` | Regex can match `---` in body content |
| Scan backwards from EOF for the first marker | Scan forward for the FIRST occurrence of the exact end marker string | Spec defines the end boundary as the first marker occurrence (§2.3) |
| Normalize on-disk content globally | Normalize only for hashing canonicalization (§2.4), otherwise preserve body bytes | Lossless editing requires preserving body text exactly |

### 11.2 Type Coercion Traps

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `Boolean(data['rag-ingestable'])` | `typeof value === 'boolean'` | `"false"` coerces to `true`! |
| `Number(data['exclusions-coverage'])` | `typeof value === 'number'` | `"0.5"` coerces silently |
| Trust YAML parser booleans | Check for `yes/no/on/off` | PyYAML treats these as booleans |

### 11.3 Cross-Language Parity

| Issue | Python | Node.js | Solution |
|-------|--------|---------|----------|
| YAML boolean keywords | PyYAML: `yes/no` → bool | js-yaml: configurable | Use explicit `true/false` only |
| Date comparison | `datetime.fromisoformat()` | `new Date()` | Parse as UTC date only |
| Unicode normalization | `unicodedata.normalize()` | Manual mapping | Use same char→char table |

### 11.4 Exclusion Block Offset Tracking

When computing `exclusions-coverage`:

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| Approximate bytes from char count | Extract actual UTF-8 bytes | Multi-byte chars (emoji, CJK) break ratio |
| Forget trailing newline after END | Include newline in excluded bytes | Spec says "through END marker" |
| Add +1 unconditionally | Clamp if END is on last line | No newline after final line |

---

## 12. Queue File Workflow

### 12.1 Queue File Schema

```yaml
schema-version: 1.0
generated: 2026-01-12T10:30:00Z
expires: 2026-01-19T10:30:00Z           # 7 days from generation
source-files-hash: <sha256>

documents:
  - file: docs/api-pricing.cgd.md
    file-hash: <sha256>
    claims:
      - id: claim-75fb137a
        text: "Base price is $99/mo"
        location: "api-pricing/1"
        round: B
        response: null                   # true | false | "estimated"
        notes: ""
```

### 12.2 Queue Expiry

Queues expire 7 days after generation. On apply:
- If expired → WARNING (W-QU02), suggest regeneration
- User can override with `--force`

### 12.3 apply-hitl Transaction Semantics

**Model: Fail-fast with checkpoint.**

```python
def apply_hitl(queue_path: str):
    queue = load_queue(queue_path)
    checkpoint = load_checkpoint(queue_path)
    
    start_index = checkpoint.last_success + 1 if checkpoint else 0
    
    for i, doc in enumerate(queue.documents[start_index:], start_index):
        try:
            validate_file_hash(doc)
            for claim in doc.claims:
                validate_claim(claim)
                apply_claim_response(claim)
            save_checkpoint(queue_path, last_success=i)
        except ValidationError as e:
            save_checkpoint(queue_path, last_success=i-1, error=e)
            raise ApplyError(f"Failed at document {i}: {e}")
    
    delete_checkpoint(queue_path)
    return Success
```

---

## 13. Round A/B Classification

### 13.1 Definition

| Round | Context | Meaning |
|-------|---------|---------|
| **A** | Interactive skill session | Source found while human was present |
| **B** | Batch CLI processing | Requires explicit human verification |

### 13.2 Environment Rules

| Environment | Round A | Round B |
|-------------|---------|---------|
| Claude.ai Skill | ✅ Available | ✅ Available |
| CLI batch | ❌ Never | ✅ Always |

---

## 14. CLI Commands

### 14.1 Package Names

| Platform | CLI Tool | Library |
|----------|----------|---------|
| npm | `clarity-gate` | `clarity-gate-core` |
| PyPI | `clarity-gate` | `clarity-gate-core` |

### 14.2 Command Reference

```bash
clarity-gate <command> [options]

Commands:
  verify <files...>           Validate format (local, no API)
  process <files...>          Create/update CGDs via Claude API
  apply-hitl <queue.yaml>     Apply HITL responses (with checkpoint)
  promote <file>              Promote CGD to SOT tier
  demote <file>               Demote SOT to CGD
  status <files...>           Show tier/status summary

Options:
  --api-key <key>             Anthropic API key (or ANTHROPIC_API_KEY env)
  --output <dir>              Output directory
  --hitl-queue <file>         Generate HITL queue file
  --dry-run                   Preview changes
  --reason <text>             Reason for demote
  --force                     Override warnings
```

---

## 15. YAML vs End Marker Authority

### 15.1 Rule

**YAML frontmatter is authoritative for CLI tools.**

The end marker (`Clarity Gate: CLEAR | REVIEWED`) is a passive signal for LLMs reading the document.

YAML frontmatter is authoritative for tooling decisions, but validators MUST enforce that the end marker status matches YAML status (`E-SC05`).

### 15.2 Mismatch Handling

If YAML and end marker disagree:

```
ERROR: E-SC05
  YAML says: UNCLEAR | PENDING
  End marker says: CLEAR | REVIEWED
  
  YAML is authoritative. Update end marker to match.
```

---

## 16. Known Limitations

### 16.1 Security Model

- Hash provides integrity, not authenticity
- No cryptographic signature (deferred to future version)
- YAML tampering detectable only via hash verification

### 16.2 Claim Matching

- ID-based matching (stable across minor edits)
- Text comparison for warnings only
- No fuzzy matching (exact comparison)

### 16.3 Table Validation

- English headers only (`## Verified Claims`)
- i18n support deferred

### 16.4 Slug Algorithm

- Non-ASCII characters stripped (not preserved like GFM)
- CJK/RTL headings may produce empty slugs (use `section-N` fallback)
- Intentional tradeoff for cross-platform compatibility

---

## 17. Examples

### 17.1 Minimal CGD

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
rag-ingestable: true
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.2 Full SOT

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: f6e5d4c3b2a1...
rag-ingestable: true
hitl-claims:
  - id: claim-75fb137a
    text: "Base price is $99/mo"
    value: "$99/mo"
    source: "Pricing page"
    location: "api-pricing/1"
    round: B
    confirmed-by: Maria
    confirmed-date: 2026-01-12
tier:
  level: SOT
  owner: Pricing Team
  version: 1.0
  promoted-date: 2026-01-12
  promoted-by: Maria
---

# API Pricing

Base price is **$99/mo** *(verified 2026-01-12)*.

## Verified Claims

| Claim | Value | Source | Verified |
|-------|-------|--------|----------|
| Base price is $99/mo | $99/mo | Pricing page | 2026-01-12 |

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.3 Document with Exclusions

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy OAuth; no SME available"
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

---

## 18. Test Vectors

### 18.1 Hash Computation

**Input file:**
```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: PENDING
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

**Expected SHA-256:**
```
d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
```


### 18.2 Claim ID Computation

**Test Vector 1:**
- text: `Base price is $99/mo`
- location: `api-pricing/1`
- **claim ID: `claim-75fb137a`**

**Test Vector 2:**
- text: `The API supports GraphQL`
- location: `features/1`
- **claim ID: `claim-eb357742`**

### 18.3 Slug Computation

| Input Heading | ASCII-Safe Slug |
|---------------|-----------------|
| `## API Pricing` | `api-pricing` |
| `## API & Pricing (v2.0)` | `api-pricing-v20` |
| `## 日本語` | `` (empty → `section-N`) |

### 18.4 Pipe Escaping (Idempotency)

| Input | Output |
|-------|--------|
| `A \| B` | `A \| B` (unchanged) |
| `A | B` | `A \| B` (escaped) |
| `A \| B | C` | `A \| B \| C` (mixed) |

---

## 19. Changelog

### v2.0 (January 2026)

- **Unified versioning:** Aligned internal spec version with release version
- **All v1.2 features included:** Exclusion blocks, computed fields, validation codes
- **Format finalized:** Implementation-ready specification

### v1.2 (January 2026)

- **Added Exclusion Blocks (§8)** for quarantining unresolved regions
- **Added computed fields:** `rag-ingestable`, `exclusions-coverage` (§9)
- **Added 37 validation error codes** with E-xxx/W-xxx namespace (§10)
- **Added implementation anti-patterns** (§11)
- **Added end marker uniqueness constraints** (§2.7): E-ST08, E-ST09
- **Added canonicalization scope clarification** (§2.4.1): hash protects canonical form, not rendered Markdown
- Hardened interoperability: slug disambiguation, backslash parity, YAML lossless editing
- Full test vectors with actual SHA-256 values

### v1.1 (January 2026)

- **Unified CGD and SOT into single format**
- SOT distinguished by presence of `tier:` block (no separate extension)
- Single `.cgd.md` extension for all documents
- Added Two-Round HITL (Round A: Derived, Round B: True HITL)
- Added stable claim IDs (`claim-<8-char-hash>`)
- ASCII-Safe slugification (not GFM)
- Idempotent pipe escaping

### v1.0 (December 2025)

- Initial specification
- Two separate formats: CGD (`.cgd.md`) and SOT (`.sot.md`)
- 9-point verification checklist
- Basic HITL verification

---

*End of Specification v2.0*
]

def is_vague_source(source: str) -> bool:
    for pattern in VAGUE_PATTERNS:
        if re.match(pattern, source, re.IGNORECASE):
            return True
    return False
```

**Validation logic:**
```python
if claim_is_pending and (is_vague_source(source) or not is_actionable_source(source)):
    emit_warning('W-HC02', f'Non-actionable source: {source}')
```

**Limitations:** Heuristics are English-centric; may false-positive on unusual references.

### 1.4 Two Document States

| State | `tier:` block | Structured table | Use case |
|-------|---------------|------------------|----------|
| **CGD** | Absent | Optional | Verified text, safe for RAG |
| **SOT** | Present | Required | Canonical reference, machine-extractable |

---

## 2. Hash Specification

### 2.1 Scope

`document-sha256` covers YAML frontmatter + Markdown body, **excluding the hash line itself**.

#### 2.1.1 Hash Input Window (Normative)

Implementations MUST compute `document-sha256` over the exact substring of the document defined as:

- **Start boundary:** the first byte immediately after the opening YAML delimiter line `---` plus its trailing newline (`---\n`).
- **End boundary:** the first byte immediately before the first occurrence of the end marker string `<!-- CLARITY_GATE_END -->`.

Therefore, the hash input includes:

- YAML frontmatter content (excluding the opening `---` line)
- The closing YAML delimiter line (`---`) and everything after it up to (but not including) the end marker

The hash input excludes:

- The opening YAML delimiter line (`---`)
- The end marker line and all bytes after (and including) the first end marker occurrence

### 2.2 Hash Exclusion Rule

**CRITICAL:** The SHA-256 calculation MUST exclude the `document-sha256` field, including:
- The line containing `document-sha256:`
- Any indented continuation lines (for multiline YAML values)

**Regex pattern:** `^\s*document-sha256:.*$`

**Frontmatter-only scope (Normative):** The exclusion rule MUST apply only within the YAML frontmatter region (between the opening `---` line and the closing `---` line). Implementations MUST NOT remove or alter any `document-sha256:` text that appears in the Markdown body.

**Multiline continuation (Normative):** After excluding the key line matching `^\s*document-sha256:`, implementations MUST also exclude subsequent lines while BOTH conditions hold:

1. The parser is still within YAML frontmatter, and
2. The line's indentation is strictly greater than the indentation of the `document-sha256:` key line.

Continuation exclusion ends when indentation returns to less-than-or-equal to the key indentation, or when the closing `---` delimiter is reached.

**Exclusion blocks and hash (Normative):** Exclusion blocks (§8) do NOT affect hash computation. The `document-sha256` is computed over the full hash window including exclusion markers and content inside exclusion blocks. Rationale: The hash is an integrity mechanism; excluding quarantined regions would allow undetected tampering of exactly the risky content.

**Algorithm:**

```python
import re
import hashlib

def compute_hash(file_content: str) -> str:
    # 0. Pre-normalize for boundary detection (CRLF/BOM).
    #    Canonicalization (§2.4) is applied later, but we need stable slicing indices.
    working = file_content
    if working.startswith('\ufeff'):
        working = working[1:]
    working = working.replace('\r\n', '\n')

    # 1. Extract content between the opening YAML delimiter line and the end marker.
    start = working.index('---\n') + len('---\n')
    end = working.index('<!-- CLARITY_GATE_END -->')
    hashable = working[start:end]
    
    # 2. Remove document-sha256 line(s) — YAML frontmatter only
    lines = hashable.split('\n')
    filtered = []
    skip_multiline = False
    hash_indent = 0
    in_frontmatter = True
    
    for line in lines:
        # Detect end of YAML frontmatter
        if in_frontmatter and line.strip() == '---':
            in_frontmatter = False

        # Check if this is the hash line
        if in_frontmatter and re.match(r'^\s*document-sha256:', line):
            skip_multiline = True
            hash_indent = len(line) - len(line.lstrip())
            continue
        
        # If we're skipping multiline, check if this is a continuation
        if skip_multiline:
            current_indent = len(line) - len(line.lstrip())
            if in_frontmatter and current_indent > hash_indent:
                continue
            skip_multiline = False
        
        filtered.append(line)
    
    hashable = '\n'.join(filtered)
    
    # 3. Canonicalize
    hashable = canonicalize(hashable)
    
    # 4. Compute
    return hashlib.sha256(hashable.encode('utf-8')).hexdigest()
```

### 2.3 End Marker Detection

**The end boundary is the HTML comment `<!-- CLARITY_GATE_END -->`**, not a bare `---`.

This solves the ambiguity when `---` (horizontal rules) appear in the document body.

**Detection rule (Normative):** The end marker is recognized when:

1. The marker string `<!-- CLARITY_GATE_END -->` appears in the document, AND
2. The marker is **outside any fenced code block** (using §8.5 fence-tracking logic)

Markers inside fenced code blocks (`` ``` `` or `~~~`) MUST be ignored. This enables documentation about Clarity Gate itself to include the marker string in code examples without terminating the document prematurely ("Quine Protection").

**Implementation:** Parsers MUST track fence state while scanning for the marker, using the same fence detection rules as §8.5 (Exclusion Blocks in Fenced Code).

### 2.4 Canonicalization

Before hashing, normalize:

1. **Line endings:** CRLF → LF
2. **Trailing whitespace:** Remove per line
3. **Consecutive newlines:** Collapse 3+ newlines to 2
4. **Final newline:** Exactly one trailing LF
5. **Encoding:** UTF-8 NFC normalization
6. **BOM:** Remove if present
7. **Tabs:** Preserve (do not convert)
8. **Leading whitespace:** Preserve (significant in code blocks)

#### 2.4.1 Canonicalization Scope (Normative)

The hash protects the **canonical byte sequence**, not rendered Markdown semantics. Specifically:

- Trailing whitespace (including Markdown hard line breaks via `  \n`) is stripped
- 3+ consecutive newlines collapse to 2

Documents with different rendered appearance MAY share the same hash if they differ only in these canonicalized elements. This is intentional: LLM tokenizers normalize whitespace similarly, so these variations do not affect RAG ingestion semantics. Cross-platform hash stability requires stripping editor-introduced whitespace variations.

### 2.5 Hash Computation Order (Initial Creation)

1. Generate complete YAML with `document-sha256: PENDING`
2. Generate body content
3. Compute hash (excluding `document-sha256:` line)
4. Replace `PENDING` with actual hash
5. Verify by recomputing (must match)

### 2.6 When Hash Changes

| Action | Hash changes? | Reason |
|--------|---------------|--------|
| Process (add markers) | Yes | Body modified |
| Promote | Yes | YAML modified (tier block) |
| Demote | Yes | YAML + body modified |
| Edit content | Yes | Body modified |
| Edit YAML (except hash) | Yes | YAML modified |

### 2.7 End Marker Uniqueness (Normative)

The document MUST contain exactly one occurrence of `<!-- CLARITY_GATE_END -->`.

After the `Clarity Gate: <status> | <hitl-status>` line, only optional trailing whitespace and a single trailing newline are permitted until EOF.

| Code | Rule | Severity |
|------|------|----------|
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

---

## 3. SOT Requirements

### 3.1 Structured Claims Table

SOT documents MUST contain a `## Verified Claims` section with a valid table.

The `## Verified Claims` section and its table MUST be outside any exclusion block (§8). Content inside exclusion blocks is ignored for the purpose of satisfying SOT structural requirements.

### 3.2 Table Validation Rules

| Rule | Requirement | Error |
|------|-------------|-------|
| V1 | Section header matches `## Verified Claims` (case-insensitive, whitespace-normalized) | `E-TB01` |
| V2 | Table has at least 1 data row | `E-TB02` |
| V3 | Required columns present: Claim, Value, Source, Verified | `E-TB03` |
| V4 | Column order: Claim MUST be first, Verified MUST be last | `E-TB04` |
| V5 | Middle columns (Value, Source) may be in any order | (not an error) |
| V6 | Extra columns allowed anywhere except before Claim or after Verified | (not an error) |
| V7 | No empty cells in required columns (whitespace-only = empty, `-` = empty) | `E-TB05` |
| V8 | Verified column is valid date (YYYY-MM-DD, validated for real dates) | `E-TB06` |
| V9 | Verified date not in future (with 24h grace period) | `E-TB07` |

### 3.3 Date Validation Details

**Valid dates only:**
- `2026-02-29` → INVALID (2026 is not a leap year)
- `2026-04-31` → INVALID (April has 30 days)
- `2026-13-01` → INVALID (no month 13)

**Future check with timezone grace:**

To accommodate global users, the future date check allows a **24-hour grace period**:

```python
from datetime import datetime, timedelta, timezone

def is_future_date(date_str: str) -> bool:
    verified_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    grace_boundary = (datetime.now(timezone.utc) + timedelta(hours=24)).date()
    return verified_date > grace_boundary
```

### 3.4 Empty Cell Definition

A cell is considered **empty** if it contains:
- Only whitespace (spaces, tabs)
- Exactly the character `-` (dash placeholder)
- Nothing at all

### 3.5 Column Matching Examples

**Valid:**
```
| Claim | Value | Source | Verified |          ✓ Standard
| Claim | Source | Value | Verified |          ✓ Middle swapped
| Claim | Notes | Value | Source | Verified |  ✓ Extra column in middle
```

**Invalid:**
```
| Value | Claim | Source | Verified |          ✗ Claim not first
| Claim | Value | Source | Notes |             ✗ Verified not last
```

---

## 4. Table Auto-Generation

### 4.1 When Auto-Generation Occurs

`promote` auto-generates a table when:
- Document has confirmed claims in `hitl-claims`
- No `## Verified Claims` section exists
- No archived table exists

### 4.2 Generation Algorithm

```python
def generate_table(hitl_claims: list) -> str:
    rows = []
    for claim in hitl_claims:
        rows.append({
            'Claim': escape_pipes(claim['text']),
            'Value': escape_pipes(claim.get('value', '-')),
            'Source': escape_pipes(claim.get('source', 'HITL Verification')),
            'Verified': claim['confirmed-date']
        })
    
    return format_table(rows)
```

### 4.3 Pipe Character Escaping

**CRITICAL:** When populating table cells, implementations MUST escape **unescaped** pipe characters (`|`) as `\|`.

**Idempotency:** Already-escaped pipes (`\|`) must NOT be double-escaped to `\\|`.

**Escaped definition (Normative):** A pipe character (`|`) is considered escaped if and only if it is immediately preceded by an odd number of consecutive backslashes.

```python
def escape_pipes(text: str) -> str:
    """Escape unescaped pipe characters for Markdown table cells.
    
    Idempotent: already-escaped pipes (\\|) are not double-escaped.
    """
    result = []
    i = 0
    while i < len(text):
        if text[i] == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and text[j] == '\\':
                backslashes += 1
                j -= 1
            if backslashes % 2 == 1:
                result.append('|')
            else:
                result.append('\\|')
        else:
            result.append(text[i])
        i += 1
    return ''.join(result)
```

### 4.4 Claim/Value Column Population

The `Claim` column receives the **full claim text**. 

The `Value` column is populated from:
1. The `value` field in YAML (if present)
2. Otherwise, a dash (`-`)

**Do NOT attempt to parse claim text into Claim/Value.** This would require NLP and produce inconsistent results.

### 4.5 Table Row Parsing (Normative)

To ensure Python and Node.js implementations parse Markdown tables identically, implementations MUST split table rows into cells using the algorithm below.

**Algorithm (Normative):**

1. Given a single table row string (one line), remove a single leading `|` if present.
2. Remove a single trailing `|` if present.
3. Split the remaining string on `|` characters that are **NOT escaped**, where "escaped" uses the **odd backslash parity** rule from §4.3.
4. Trim leading/trailing whitespace from each resulting cell.

```python
def split_table_row(row: str) -> list[str]:
    if row.startswith('|'):
        row = row[1:]
    if row.endswith('|'):
        row = row[:-1]

    cells = []
    buf = []

    i = 0
    while i < len(row):
        ch = row[i]
        if ch == '|':
            backslashes = 0
            j = i - 1
            while j >= 0 and row[j] == '\\':
                backslashes += 1
                j -= 1

            if backslashes % 2 == 1:
                buf.append('|')
            else:
                cells.append(''.join(buf).strip())
                buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    cells.append(''.join(buf).strip())
    return cells
```

---

## 5. Claim ID Specification

### 5.1 ID Format

```
claim-<8-char-hex>
```

Example: `claim-75fb137a`

### 5.2 ID Computation

```python
def compute_claim_id(text: str, location: str) -> str:
    input_string = f"{text}|{location}"
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()
    return f"claim-{hash_hex[:8]}"
```

### 5.3 Location Context Format

`location` is a stable reference: `heading_slug/ordinal`

**Format:** `<nearest_heading_slug>/<ordinal_within_section>`

### 5.4 Slug Algorithm (ASCII-Safe Slugification)

**IMPORTANT:** This is **NOT** GitHub Flavored Markdown (GFM) slugification. GFM preserves non-ASCII characters; this algorithm strips them for maximum cross-platform compatibility.

**ASCII-Safe Slug Rules:**
1. Convert to lowercase
2. Remove all characters except ASCII alphanumerics (`a-z`, `0-9`), spaces, and hyphens
3. Replace spaces with hyphens
4. Collapse consecutive hyphens to single hyphen
5. Remove leading/trailing hyphens

```python
import re

def ascii_safe_slugify(heading: str) -> str:
    slug = heading.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug
```

**Special case — empty slug:** If a heading produces an empty slug (all non-ASCII), use `section-<ordinal>` where ordinal is the heading's position in the document (1-indexed).

**Special case — duplicate slugs (Normative):** If two or more headings produce the same slug, implementations MUST disambiguate by appending `-2`, `-3`, ... in document order.

**Special case — root:** Claims before any heading use `root` as the slug.

### 5.5 Ordinal Assignment

Ordinals are 1-indexed within each section.

```markdown
## Pricing

First claim here.     → location: pricing/1
Second claim here.    → location: pricing/2

## Features

First claim here.     → location: features/1
```

### 5.6 Claim Matching for Queue Apply

**Matching is by ID, not text.**

If ID matches but text differs slightly (whitespace, punctuation):
```
WARNING: Claim text differs from queue. Applying anyway.
  Queue: "Base price is $99/mo"
  Doc:   "Base price is $99/mo."
```

---

## 6. Promote Command

### 6.1 Basic Usage

```bash
clarity-gate promote doc.cgd.md --owner "Team" --version 1.0
```

### 6.2 Behavior

```
1. Validate document is CGD (no tier block)
2. Check for existing table:
   a. If ## Verified Claims exists → validate and proceed
   b. If ## Claims (Archived from SOT) exists → restore
   c. If neither → auto-generate from hitl-claims
3. If no claims and no table → ERROR: E-PM01
4. Add tier block to YAML
5. Recompute document-sha256
6. Update processed-date
```

### 6.3 Re-Promotion (Archived Table Restoration)

Detection uses **comment ID**, not header text:

```markdown
<!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-10 -->
## Claims (Archived from SOT)
```

---

## 7. Demote Command

### 7.1 Basic Usage

```bash
clarity-gate demote doc.cgd.md --reason "Superseded by v2"
```

### 7.2 Behavior

1. Validate document is SOT (has tier block)
2. If no tier block → WARNING, exit 0 (no-op)
3. Remove tier block from YAML
4. Find `## Verified Claims` section
5. Generate unique archive ID: `arch-<8-char-hex>`
6. Add archive comment with ID:
   ```markdown
   <!-- CLARITY_GATE_ARCHIVED: id=arch-x7y8z9, date=2026-01-12, reason="Superseded by v2" -->
   ## Claims (Archived from SOT)
   ```
7. Recompute document-sha256
8. Update processed-date

### 7.3 Archive Comment Format

```
<!-- CLARITY_GATE_ARCHIVED: id=<id>, date=<ISO-date>, reason="<escaped-reason>" -->
```

**Escaping in reason:** Replace `"` with `&quot;` and `>` with `&gt;`.

---

## 8. Exclusion Blocks

### 8.1 Purpose

Exclusion Blocks mark document regions with unresolved ambiguity that are **unsafe for RAG ingestion**. They allow a document to be `CLEAR` overall while quarantining specific sections that couldn't be resolved.

**Use case:** Legacy documentation where no SME is available, or third-party content that can't be modified.

**Semantic note:** A document may have `clarity-status: CLEAR` with exclusion blocks present. This means "all non-excluded content is epistemically clear." However, such documents are still non-ingestable (`rag-ingestable: false`) by design. This is a "human-readable but quarantined" state.

### 8.2 Syntax

```markdown
<!-- CG-EXCLUSION:BEGIN id=<id> -->
Content with unresolved ambiguity...
<!-- CG-EXCLUSION:END id=<id> -->
```

#### 8.2.1 Marker Grammar (Normative)

Exclusion markers MUST appear alone on a line with this exact structure:

```
<optional-leading-spaces><!-- CG-EXCLUSION:BEGIN id=<id> --><optional-trailing-spaces>
<optional-leading-spaces><!-- CG-EXCLUSION:END id=<id> --><optional-trailing-spaces>
```

Where:
- Leading spaces (0+) are permitted (for indented Markdown)
- The token `<!-- CG-EXCLUSION:BEGIN id=` is **case-sensitive** and exact
- `<id>` matches `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`
- No additional attributes are permitted
- Trailing spaces are ignored

**Invalid (malformed) markers trigger E-EX00:**
- Extra attributes: `<!-- CG-EXCLUSION:BEGIN id=foo reason="bar" -->`
- Case variation: `<!-- cg-exclusion:begin id=foo -->`
- Inline with content: `text <!-- CG-EXCLUSION:BEGIN id=foo --> more text`

### 8.3 ID Format

IDs MUST match: `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`

### 8.4 Structural Rules (Normative)

| Rule | Violation | Error Code |
|------|-----------|------------|
| BEGIN and END `id` values MUST match exactly | Mismatch | E-EX01 |
| No nesting: BEGIN while inside another block | Nested BEGIN | E-EX02 |
| No overlap: END must close most recent BEGIN (stack discipline) | Interleaved | E-EX03 |
| No duplicate IDs: Same `id` used for multiple blocks | Reused ID | E-EX04 |

**Example of E-EX03 (interleaved blocks):**
```markdown
<!-- CG-EXCLUSION:BEGIN id=outer -->
<!-- CG-EXCLUSION:BEGIN id=inner -->
<!-- CG-EXCLUSION:END id=outer -->   ← ERROR: closes outer before inner
<!-- CG-EXCLUSION:END id=inner -->
```

### 8.5 Code Fence Handling

Exclusion markers inside fenced code blocks MUST be ignored by validators.

- A fenced code block begins with ``` or ~~~ (3+ characters)
- It ends at the next fence of the **same character** with **equal or greater length**
- Example: ````` opened → closes at ````` or longer, NOT at ```

#### 8.5.1 Parsing Order (Normative)

Validators MUST process lines in this order:

1. **Track fence state:** Toggle in/out of code fence on fence delimiter lines
2. **If inside fence:** Ignore exclusion markers entirely (treat as literal text)
3. **If outside fence:** Process BEGIN/END markers per §8.4

Fence detection rules:
- Fence opens on line starting with 3+ backticks or tildes (after 0–3 leading spaces)
- Fence closes on line starting with same character, equal or greater count
- Info strings after opener are ignored
- Block quotes: strip leading `>` and optional space before applying fence/marker detection
- A line indented by 4+ spaces MUST NOT open or close a fence (it is an indented code block, per CommonMark)

**Indented code blocks (Normative):** Exclusion markers inside indented code blocks (lines with 4+ leading spaces, per CommonMark) MAY be interpreted as literal markers by validators. This specification does not require validators to detect indented code blocks. Authors SHOULD use fenced code blocks when documenting exclusion marker syntax to avoid ambiguity.

### 8.6 State Rules

| Condition | Constraint | Error Code |
|-----------|------------|------------|
| Exclusion blocks exist | `hitl-status` MUST be `REVIEWED_WITH_EXCEPTIONS` | E-EX05 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | ≥1 exclusion block MUST exist in body | E-EX06 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-reason` MUST be present (non-empty string) | E-EX07 |
| `hitl-status: REVIEWED_WITH_EXCEPTIONS` | `exceptions-ids` MUST list all exclusion block IDs | E-EX08 |
| Exclusion block ID in body | MUST be listed in `exceptions-ids` | E-EX09 |
| `exceptions-ids` format | MUST be a list of valid ID strings | E-EX10 |

### 8.7 YAML Fields for Exclusions

Add to frontmatter when exclusion blocks are present:

```yaml
hitl-status: REVIEWED_WITH_EXCEPTIONS
exceptions-reason: "Legacy OAuth implementation; no SME available"
exceptions-ids:
  - auth-legacy-1
  - oauth-flow-2
exclusions-coverage: 0.15  # Computed: excluded_bytes / total_body_bytes
```

### 8.8 Ingestion Policy Impact

A document with **any** exclusion blocks MUST have `rag-ingestable: false`, regardless of other status fields.

**No partial ingestion.** Documents are accepted or rejected as a whole.

### 8.9 Claims Inside Exclusion Blocks

Claims that appear inside exclusion blocks are **ignored entirely** during claim extraction. They do not generate entries in `hitl-claims` and are not validated.

Content inside exclusion blocks is also ignored for structural validation requirements (e.g., SOT `## Verified Claims` detection/validation).

Validators MAY emit a warning: "Claims detected inside exclusions were ignored."

### 8.10 Example

```yaml
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy prose; no SME available."
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users *(as of 2026-01-09)*.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

### 8.11 Redacted Export

The `redact_exclusions()` function (or CLI `export --redact-exclusions`) produces a copy with exclusion block **content** replaced by `[REDACTED]`. This enables:

- Safe ingestion by downstream tools that don't respect metadata flags
- Sharing documents with parties who shouldn't see quarantined content
- Audit trails that preserve structure without sensitive details

**Behavior:**

1. Exclusion markers (BEGIN/END comments) are **preserved**
2. Content between markers is replaced with `[REDACTED]\n`
3. `document-sha256` is **recomputed** for the redacted version
4. Line numbers will shift (the redacted document is shorter)

**Important:** The redacted document is a **new document**, not a modification of the original. It has a different hash and should be treated as a derivative work.

**Example:**

Original:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details that require SME review...
Multiple lines of sensitive content here...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

After redaction:
```markdown
<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
[REDACTED]
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->
```

---

## 9. Computed Fields

### 9.1 `rag-ingestable` (Boolean)

This field is an **informational summary** for pipeline ingestion decisions.

**Computation:**
```python
rag-ingestable = (clarity-status == CLEAR) \
             and (hitl-status == REVIEWED) \
             and (exclusion_block_count == 0)
```

**Validator behavior:**
- Validators MUST compute this value
- Validators SHOULD write it to the document
- If declared value disagrees with computed → WARN (W-RI01)
- If declared value is not boolean → ERROR (E-RI01)

**Semantics:**
- `true` → Document is epistemically well-formed and human-reviewed
- `false` → Document MUST be rejected from production RAG

**Important:** `rag-ingestable: true` does NOT guarantee:
- Claims are factually true
- Human review was error-free
- Hallucinations are impossible

### 9.2 `exclusions-coverage` (Float 0.0–1.0)

Reports what fraction of body content is excluded.

**Computation:**
```python
exclusions-coverage = excluded_bytes / total_body_bytes
```

Where:
- `total_body_bytes` = UTF-8 byte count of canonical body (per §2.4 canonicalization)
- `excluded_bytes` = byte count from BEGIN marker through END marker (inclusive), including marker lines

**Byte counting rules (Normative):**
- Count bytes AFTER CRLF→LF normalization (consistent with hash canonicalization)
- Use UTF-8 encoded byte length, not character count
- If `total_body_bytes = 0`, `exclusions-coverage` MUST be `0.0` or omitted

**Validation:**
- If present, MUST be number in range 0.0–1.0 → else ERROR (E-EC01)
- If coverage ≥ 0.50 → WARN (W-EC01): majority excluded

---

## 10. Validation Error Codes

### 10.1 Severity Levels

- **ERROR (E-xxx):** Document invalid; MUST NOT pass validation
- **WARN (W-xxx):** Document valid but suboptimal; SHOULD be addressed

Validators SHOULD report actionable locations (line/section) when possible.

### 10.2 Structural Errors (E-ST)

| Code | Rule | Severity |
|------|------|----------|
| E-ST01 | YAML frontmatter parsing fails (syntax error) | ERROR |
| E-ST02 | Missing YAML frontmatter block at file start | ERROR |
| E-ST03 | Missing required frontmatter field | ERROR |
| E-ST04 | `processed-date` is in the future (UTC) | ERROR |
| E-ST05 | `points-passed` invalid (syntax or out of bounds 1–9) | ERROR |
| E-ST06 | Missing end marker (`<!-- CLARITY_GATE_END -->`) | ERROR |
| E-ST07 | End marker malformed (invalid status values) | ERROR |
| E-ST08 | Multiple `<!-- CLARITY_GATE_END -->` markers found | ERROR |
| E-ST09 | Non-whitespace content after end marker status line | ERROR |

### 10.3 State Consistency Errors (E-SC)

| Code | Rule | Severity |
|------|------|----------|
| E-SC01 | Invalid state: `UNCLEAR` with `hitl-status != PENDING` | ERROR |
| E-SC02 | `hitl-status: PENDING` but `hitl-pending-count = 0` | ERROR |
| E-SC03 | `hitl-status: REVIEWED` but `hitl-pending-count > 0` | ERROR |
| E-SC04 | `hitl-status: REVIEWED_WITH_EXCEPTIONS` but `hitl-pending-count > 0` | ERROR |
| E-SC05 | YAML and end marker status disagree | ERROR |

### 10.4 Exclusion Block Errors (E-EX)

| Code | Rule | Severity |
|------|------|----------|
| E-EX00 | Malformed exclusion marker line | ERROR |
| E-EX01 | BEGIN/END id mismatch | ERROR |
| E-EX02 | Nested exclusion blocks | ERROR |
| E-EX03 | Interleaved exclusion blocks | ERROR |
| E-EX04 | Duplicate exclusion IDs | ERROR |
| E-EX05 | Exclusion blocks exist but `hitl-status != REVIEWED_WITH_EXCEPTIONS` | ERROR |
| E-EX06 | `REVIEWED_WITH_EXCEPTIONS` but no exclusion blocks in body | ERROR |
| E-EX07 | `REVIEWED_WITH_EXCEPTIONS` but missing `exceptions-reason` | ERROR |
| E-EX08 | `exceptions-ids` references ID not present in body | ERROR |
| E-EX09 | Exclusion block ID in body but missing from `exceptions-ids` | ERROR |
| E-EX10 | `exceptions-ids` not a list of strings or contains invalid ID format | ERROR |

### 10.5 Hash Errors (E-HS)

| Code | Rule | Severity |
|------|------|----------|
| E-HS01 | `document-sha256` malformed (not 64-char lowercase hex) | ERROR |
| W-HS01 | `document-sha256` doesn't match computed | WARN |

### 10.6 Computed Field Errors

| Code | Rule | Severity |
|------|------|----------|
| E-RI01 | `rag-ingestable` present but not boolean | ERROR |
| W-RI01 | `rag-ingestable` disagrees with computed value | WARN |
| E-EC01 | `exclusions-coverage` not a number in range 0.0–1.0 | ERROR |
| W-EC01 | `exclusions-coverage` ≥ 0.50 (majority excluded) | WARN |

### 10.6.1 HITL Claim Errors (E-HC)

These codes apply to entries under the `hitl-claims` list in YAML frontmatter.

| Code | Rule | Severity |
|------|------|----------|
| E-HC01 | `hitl-claims` is present but not a list | ERROR |
| E-HC02 | A `hitl-claims` entry is missing required field `text` | ERROR |
| E-HC03 | A `hitl-claims` entry has `round` not in {A, B} | ERROR |
| E-HC04 | A `hitl-claims` entry has `confirmed-date` not a valid `YYYY-MM-DD` date | ERROR |

### 10.7 Table Errors (E-TB)

| Code | Rule | Severity |
|------|------|----------|
| E-TB01 | No `## Verified Claims` section (SOT only) | ERROR |
| E-TB02 | Table has no data rows | ERROR |
| E-TB03 | Required columns missing (Claim, Value, Source, Verified) | ERROR |
| E-TB04 | Column order wrong (Claim not first or Verified not last) | ERROR |
| E-TB05 | Empty cell in required column | ERROR |
| E-TB06 | Invalid date format in Verified column | ERROR |
| E-TB07 | Verified date in future (beyond 24h grace) | ERROR |

### 10.8 Promote/Demote Errors (E-PM, E-DM)

| Code | Rule | Severity |
|------|------|----------|
| E-PM01 | Promote: no verified claims and no table | ERROR |
| E-PM02 | Promote: file already has tier block | ERROR |
| W-DM01 | Demote: file has no tier block (no-op) | WARN |

### 10.9 Queue Errors (E-QU)

| Code | Rule | Severity |
|------|------|----------|
| E-QU01 | Claim ID not found in document | ERROR |
| W-QU01 | Claim text differs from queue | WARN |
| E-QU02 | Read-only queue fields modified | ERROR |
| W-QU02 | Queue expired (>7 days) | WARN |

### 10.10 Forward Compatibility

| Code | Rule | Severity |
|------|------|----------|
| W-FC01 | `clarity-gate-version` major exceeds validator capability | WARN |

When W-FC01 triggers, validators MUST also force `rag-ingestable: false` regardless of other checks.

---

## 11. Implementation Anti-Patterns

### 11.1 Parsing Anti-Patterns

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `.trim()` on delimiter lines | `.trimEnd()` (trailing only) | Leading whitespace invalidates `---` delimiter |
| Regex for YAML frontmatter | Line-by-line scan for exact `---` | Regex can match `---` in body content |
| Scan backwards from EOF for the first marker | Scan forward for the FIRST occurrence of the exact end marker string | Spec defines the end boundary as the first marker occurrence (§2.3) |
| Normalize on-disk content globally | Normalize only for hashing canonicalization (§2.4), otherwise preserve body bytes | Lossless editing requires preserving body text exactly |

### 11.2 Type Coercion Traps

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| `Boolean(data['rag-ingestable'])` | `typeof value === 'boolean'` | `"false"` coerces to `true`! |
| `Number(data['exclusions-coverage'])` | `typeof value === 'number'` | `"0.5"` coerces silently |
| Trust YAML parser booleans | Check for `yes/no/on/off` | PyYAML treats these as booleans |

### 11.3 Cross-Language Parity

| Issue | Python | Node.js | Solution |
|-------|--------|---------|----------|
| YAML boolean keywords | PyYAML: `yes/no` → bool | js-yaml: configurable | Use explicit `true/false` only |
| Date comparison | `datetime.fromisoformat()` | `new Date()` | Parse as UTC date only |
| Unicode normalization | `unicodedata.normalize()` | Manual mapping | Use same char→char table |

### 11.4 Exclusion Block Offset Tracking

When computing `exclusions-coverage`:

| ❌ Don't | ✅ Do Instead | Why |
|----------|---------------|-----|
| Approximate bytes from char count | Extract actual UTF-8 bytes | Multi-byte chars (emoji, CJK) break ratio |
| Forget trailing newline after END | Include newline in excluded bytes | Spec says "through END marker" |
| Add +1 unconditionally | Clamp if END is on last line | No newline after final line |

---

## 12. Queue File Workflow

### 12.1 Queue File Schema

```yaml
schema-version: 1.0
generated: 2026-01-12T10:30:00Z
expires: 2026-01-19T10:30:00Z           # 7 days from generation
source-files-hash: <sha256>

documents:
  - file: docs/api-pricing.cgd.md
    file-hash: <sha256>
    claims:
      - id: claim-75fb137a
        text: "Base price is $99/mo"
        location: "api-pricing/1"
        round: B
        response: null                   # true | false | "estimated"
        notes: ""
```

### 12.2 Queue Expiry

Queues expire 7 days after generation. On apply:
- If expired → WARNING (W-QU02), suggest regeneration
- User can override with `--force`

### 12.3 apply-hitl Transaction Semantics

**Model: Fail-fast with checkpoint.**

```python
def apply_hitl(queue_path: str):
    queue = load_queue(queue_path)
    checkpoint = load_checkpoint(queue_path)
    
    start_index = checkpoint.last_success + 1 if checkpoint else 0
    
    for i, doc in enumerate(queue.documents[start_index:], start_index):
        try:
            validate_file_hash(doc)
            for claim in doc.claims:
                validate_claim(claim)
                apply_claim_response(claim)
            save_checkpoint(queue_path, last_success=i)
        except ValidationError as e:
            save_checkpoint(queue_path, last_success=i-1, error=e)
            raise ApplyError(f"Failed at document {i}: {e}")
    
    delete_checkpoint(queue_path)
    return Success
```

---

## 13. Round A/B Classification

### 13.1 Definition

| Round | Context | Meaning |
|-------|---------|---------|
| **A** | Interactive skill session | Source found while human was present |
| **B** | Batch CLI processing | Requires explicit human verification |

### 13.2 Environment Rules

| Environment | Round A | Round B |
|-------------|---------|---------|
| Claude.ai Skill | ✅ Available | ✅ Available |
| CLI batch | ❌ Never | ✅ Always |

---

## 14. CLI Commands

### 14.1 Package Names

| Platform | CLI Tool | Library |
|----------|----------|---------|
| npm | `clarity-gate` | `clarity-gate-core` |
| PyPI | `clarity-gate` | `clarity-gate-core` |

### 14.2 Command Reference

```bash
clarity-gate <command> [options]

Commands:
  verify <files...>           Validate format (local, no API)
  process <files...>          Create/update CGDs via Claude API
  apply-hitl <queue.yaml>     Apply HITL responses (with checkpoint)
  promote <file>              Promote CGD to SOT tier
  demote <file>               Demote SOT to CGD
  status <files...>           Show tier/status summary

Options:
  --api-key <key>             Anthropic API key (or ANTHROPIC_API_KEY env)
  --output <dir>              Output directory
  --hitl-queue <file>         Generate HITL queue file
  --dry-run                   Preview changes
  --reason <text>             Reason for demote
  --force                     Override warnings
```

---

## 15. YAML vs End Marker Authority

### 15.1 Rule

**YAML frontmatter is authoritative for CLI tools.**

The end marker (`Clarity Gate: CLEAR | REVIEWED`) is a passive signal for LLMs reading the document.

YAML frontmatter is authoritative for tooling decisions, but validators MUST enforce that the end marker status matches YAML status (`E-SC05`).

### 15.2 Mismatch Handling

If YAML and end marker disagree:

```
ERROR: E-SC05
  YAML says: UNCLEAR | PENDING
  End marker says: CLEAR | REVIEWED
  
  YAML is authoritative. Update end marker to match.
```

---

## 16. Known Limitations

### 16.1 Security Model

- Hash provides integrity, not authenticity
- No cryptographic signature (deferred to future version)
- YAML tampering detectable only via hash verification

### 16.2 Claim Matching

- ID-based matching (stable across minor edits)
- Text comparison for warnings only
- No fuzzy matching (exact comparison)

### 16.3 Table Validation

- English headers only (`## Verified Claims`)
- i18n support deferred

### 16.4 Slug Algorithm

- Non-ASCII characters stripped (not preserved like GFM)
- CJK/RTL headings may produce empty slugs (use `section-N` fallback)
- Intentional tradeoff for cross-platform compatibility

---

## 17. Examples

### 17.1 Minimal CGD

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
rag-ingestable: true
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.2 Full SOT

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: f6e5d4c3b2a1...
rag-ingestable: true
hitl-claims:
  - id: claim-75fb137a
    text: "Base price is $99/mo"
    value: "$99/mo"
    source: "Pricing page"
    location: "api-pricing/1"
    round: B
    confirmed-by: Maria
    confirmed-date: 2026-01-12
tier:
  level: SOT
  owner: Pricing Team
  version: 1.0
  promoted-date: 2026-01-12
  promoted-by: Maria
---

# API Pricing

Base price is **$99/mo** *(verified 2026-01-12)*.

## Verified Claims

| Claim | Value | Source | Verified |
|-------|-------|--------|----------|
| Base price is $99/mo | $99/mo | Pricing page | 2026-01-12 |

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

### 17.3 Document with Exclusions

```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED_WITH_EXCEPTIONS
hitl-pending-count: 0
points-passed: 1-6
document-sha256: 7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730
rag-ingestable: false
exclusions-coverage: 0.15
exceptions-reason: "Legacy OAuth; no SME available"
exceptions-ids:
  - auth-legacy-1
hitl-claims: []
---

# API Documentation

## Overview

This API serves *(estimated)* 500 users.

## Authentication

<!-- CG-EXCLUSION:BEGIN id=auth-legacy-1 -->
Legacy OAuth implementation details...
<!-- CG-EXCLUSION:END id=auth-legacy-1 -->

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED_WITH_EXCEPTIONS
```

---

## 18. Test Vectors

### 18.1 Hash Computation

**Input file:**
```markdown
---
clarity-gate-version: 2.0
processed-date: 2026-01-12
processed-by: Claude
clarity-status: CLEAR
hitl-status: REVIEWED
hitl-pending-count: 0
points-passed: 1-9
document-sha256: PENDING
hitl-claims: []
---

# Test Document

Hello world.

<!-- CLARITY_GATE_END -->
Clarity Gate: CLEAR | REVIEWED
```

**Expected SHA-256:**
```
d4db0fcd3493313c59eb2d59b8f3f9aaec1cfb578e6ce7c589a225ee48741545
```


### 18.2 Claim ID Computation

**Test Vector 1:**
- text: `Base price is $99/mo`
- location: `api-pricing/1`
- **claim ID: `claim-75fb137a`**

**Test Vector 2:**
- text: `The API supports GraphQL`
- location: `features/1`
- **claim ID: `claim-eb357742`**

### 18.3 Slug Computation

| Input Heading | ASCII-Safe Slug |
|---------------|-----------------|
| `## API Pricing` | `api-pricing` |
| `## API & Pricing (v2.0)` | `api-pricing-v20` |
| `## 日本語` | `` (empty → `section-N`) |

### 18.4 Pipe Escaping (Idempotency)

| Input | Output |
|-------|--------|
| `A \| B` | `A \| B` (unchanged) |
| `A | B` | `A \| B` (escaped) |
| `A \| B | C` | `A \| B \| C` (mixed) |

---

## 19. Changelog

### v2.0 (January 2026)

- **Unified versioning:** Aligned internal spec version with release version
- **All v1.2 features included:** Exclusion blocks, computed fields, validation codes
- **Format finalized:** Implementation-ready specification

### v1.2 (January 2026)

- **Added Exclusion Blocks (§8)** for quarantining unresolved regions
- **Added computed fields:** `rag-ingestable`, `exclusions-coverage` (§9)
- **Added 37 validation error codes** with E-xxx/W-xxx namespace (§10)
- **Added implementation anti-patterns** (§11)
- **Added end marker uniqueness constraints** (§2.7): E-ST08, E-ST09
- **Added canonicalization scope clarification** (§2.4.1): hash protects canonical form, not rendered Markdown
- Hardened interoperability: slug disambiguation, backslash parity, YAML lossless editing
- Full test vectors with actual SHA-256 values

### v1.1 (January 2026)

- **Unified CGD and SOT into single format**
- SOT distinguished by presence of `tier:` block (no separate extension)
- Single `.cgd.md` extension for all documents
- Added Two-Round HITL (Round A: Derived, Round B: True HITL)
- Added stable claim IDs (`claim-<8-char-hash>`)
- ASCII-Safe slugification (not GFM)
- Idempotent pipe escaping

### v1.0 (December 2025)

- Initial specification
- Two separate formats: CGD (`.cgd.md`) and SOT (`.sot.md`)
- 9-point verification checklist
- Basic HITL verification

---

*End of Specification v2.0*
