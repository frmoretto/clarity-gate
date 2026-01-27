#!/usr/bin/env python3
"""
Clarity Gate: Document Hash Computation

Reference implementation per FORMAT_SPEC §2.2 (RFC-001).
Computes SHA-256 hash excluding the document-sha256 line itself.

Usage:
    python document_hash.py path/to/file.cgd.md
    python document_hash.py --verify path/to/file.cgd.md

Normalization (CRITICAL for cross-platform consistency):
    - BOM removed if present
    - CRLF → LF (Windows compatibility)
    - CR → LF (old Mac compatibility)
    - document-sha256 line excluded from hash computation
"""

import hashlib
import re
import sys


def normalize_content(content: str) -> str:
    """
    Normalize content for consistent hashing across platforms.
    
    Per FORMAT_SPEC §2.2.0 (implicit):
    - Remove UTF-8 BOM if present
    - Normalize all line endings to LF
    """
    # Remove BOM if present
    if content.startswith('\ufeff'):
        content = content[1:]
    
    # Normalize line endings: CRLF → LF, CR → LF
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    return content


def compute_hash(filepath: str) -> str:
    """
    Compute SHA-256 hash of document excluding document-sha256 line.
    
    Algorithm:
        1. Read file as UTF-8
        2. Normalize content (BOM, line endings)
        3. Remove document-sha256 line
        4. Compute SHA-256 of normalized content
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Normalize for cross-platform consistency
    content = normalize_content(content)
    
    # Remove document-sha256 line for computation
    # Handles: document-sha256: "abc123" or document-sha256: abc123
    content = re.sub(r'^document-sha256:.*$', '', content, flags=re.MULTILINE)
    
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def verify(filepath: str) -> bool:
    """
    Verify document hash matches stored value.
    
    Returns True if hash matches, False otherwise.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Normalize for consistent matching
    content = normalize_content(content)
    
    # Extract stored hash
    match = re.search(r'^document-sha256:\s*["\']?([a-f0-9]{64})["\']?', content, re.MULTILINE)
    if not match:
        print("FAIL: No document-sha256 found")
        return False
    
    stored = match.group(1)
    computed = compute_hash(filepath)
    
    if stored == computed:
        print(f"PASS: Hash verified: {computed}")
        return True
    else:
        print(f"FAIL: Hash mismatch")
        print(f"  Stored:   {stored}")
        print(f"  Computed: {computed}")
        return False


def main():
    if len(sys.argv) == 2 and sys.argv[1] not in ("--verify", "--test"):
        print(compute_hash(sys.argv[1]))
    elif len(sys.argv) == 3 and sys.argv[1] == "--verify":
        sys.exit(0 if verify(sys.argv[2]) else 1)
    elif len(sys.argv) == 2 and sys.argv[1] == "--test":
        # Run normalization tests
        print("=== Normalization Tests ===")
        
        # Test BOM removal
        with_bom = '\ufeff# Test'
        without_bom = '# Test'
        assert normalize_content(with_bom) == without_bom, "BOM removal failed"
        print("PASS: BOM removal")
        
        # Test CRLF normalization
        crlf = "line1\r\nline2\r\n"
        lf = "line1\nline2\n"
        assert normalize_content(crlf) == lf, "CRLF normalization failed"
        print("PASS: CRLF -> LF")
        
        # Test CR normalization
        cr = "line1\rline2\r"
        assert normalize_content(cr) == "line1\nline2\n", "CR normalization failed"
        print("PASS: CR -> LF")
        
        print("\nPASS: All normalization tests passed")
    else:
        print("Usage: document_hash.py <file>")
        print("       document_hash.py --verify <file>")
        print("       document_hash.py --test")
        print()
        print("Examples:")
        print("  document_hash.py my-doc.cgd.md")
        print("  document_hash.py --verify my-doc.cgd.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
