# Security Policy

## Scope

Clarity Gate is a verification methodology, not a security tool. However, we take security seriously.

## Reporting a Vulnerability

If you discover a security issue:

1. **Do NOT** open a public issue
2. Email: contact@clarity-gate.org
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
- Prevent prompt injection

## Validator Security

If you're implementing a validator:

1. Use validators from trusted sources (official releases)
2. Verify validator version matches specification version
3. See RFC-004 for parser hardening requirements
4. Implement resource limits (see FORMAT_SPEC §Security)

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.1.x   | ✅ Yes    |
| 2.0.x   | ✅ Yes    |
| < 2.0   | ❌ No     |
