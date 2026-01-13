# Examples

Real-world examples of Clarity Gate verification.

---

## Available Examples

| Example | Type | Document | Result |
|---------|------|----------|--------|
| [Biology Paper](biology-paper-example.md) | Tier 1A: Internal Consistency | Scientific paper (arXiv 2403.00001) | DISCREPANCY FOUND |
| [Self-Verification Report](self-verification-report.md) | Full 9-Point Verification | This repository's documentation | 14/18 PASS, 2 NEEDS REVIEW |

---

## How to Use These Examples

### Learning

Each example shows:
- The document type and problem
- What Clarity Gate found
- How to reproduce the verification
- Resolution options

### Validation

Use the reproducibility instructions to verify our claims yourself:
1. Download the source document
2. Run the provided prompt in Claude/Gemini
3. Compare your results to ours

### Contributing

Have an example to share? See [Contributing](#contributing) below.

---

## Example Structure

Each example follows this format:

```
# Example: [Name]

**Type:** [Tier 1A/1B/2]
**Document:** [Description]
**Result:** [PASS/FAIL/DISCREPANCY]
**Reproducible:** [Yes/No]

## Paper/Document Reference
[How to access the source]

## What Clarity Gate Found
[Detection results]

## How to Reproduce
[Step-by-step instructions]

## Why This Matters
[Failure mode if not caught]

## Resolution Options
[How to fix]
```

---

## Contributing

We're looking for examples that demonstrate:

1. **Different document types**
   - Legal documents
   - Financial reports
   - Technical documentation
   - Medical/clinical papers

2. **Different failure modes**
   - Internal consistency issues
   - Missing uncertainty markers
   - Implicit assumptions
   - Stale data

3. **Edge cases**
   - False positives (flagged but correct)
   - Complex multi-part discrepancies
   - Domain-specific challenges

### How to Contribute

1. Fork the repository
2. Add your example as `examples/[descriptive-name].md`
3. Follow the structure above
4. Include reproducibility instructions
5. Open a PR

**Important:** Do not include copyrighted documents directly. Provide references and instructions for obtaining source materials.

---

## License

Examples are provided under CC BY 4.0 — Use freely with attribution.
