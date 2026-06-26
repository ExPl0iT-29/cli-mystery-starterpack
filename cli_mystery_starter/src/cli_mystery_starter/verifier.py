"""Format-aware answer hashing and verification.

Two formats are supported:

- `sha256_salted` (default for new scaffolds):
      sha256$<salt-hex>$<digest-hex>
  where `digest = sha256(salt + normalize(answer))`.

- `md5_legacy` (older scaffolds):
      <32 hex chars>
  Verified by hashing the stripped guess with MD5
  (`usedforsecurity=False` so FIPS-mode hosts do not crash).

Players are forgiven trailing/leading whitespace and runs of internal
whitespace collapse to a single space. Case sensitivity is intentional
(authors choose the canonical spelling); document it for the player.
"""

from __future__ import annotations

import hashlib
import re
import secrets

LEGACY_MD5_RE = re.compile(r"^[0-9a-f]{32}$")
SHA256_SALTED_RE = re.compile(r"^sha256\$[0-9a-f]{16,64}\$[0-9a-f]{64}$")

FORMAT_SHA256_SALTED = "sha256_salted"
FORMAT_MD5_LEGACY = "md5_legacy"
KNOWN_FORMATS = (FORMAT_SHA256_SALTED, FORMAT_MD5_LEGACY)


def normalize(answer: str) -> str:
    """Strip and collapse internal whitespace runs. Case-preserving."""
    return " ".join(answer.split())


def hash_answer(answer: str, *, fmt: str = FORMAT_SHA256_SALTED, salt: str | None = None) -> str:
    norm = normalize(answer)
    if fmt == FORMAT_MD5_LEGACY:
        return hashlib.md5(answer.strip().encode("utf-8"), usedforsecurity=False).hexdigest()
    if fmt == FORMAT_SHA256_SALTED:
        s = salt or secrets.token_hex(16)
        digest = hashlib.sha256((s + norm).encode("utf-8")).hexdigest()
        return f"sha256${s}${digest}"
    raise ValueError(f"Unknown answer format: {fmt!r}; expected one of {KNOWN_FORMATS}")


def detect_format(encoded: str) -> str | None:
    encoded = encoded.strip()
    if SHA256_SALTED_RE.match(encoded):
        return FORMAT_SHA256_SALTED
    if LEGACY_MD5_RE.match(encoded):
        return FORMAT_MD5_LEGACY
    return None


def verify(encoded: str, guess: str) -> bool:
    encoded = encoded.strip()
    fmt = detect_format(encoded)
    if fmt == FORMAT_SHA256_SALTED:
        _, salt, digest = encoded.split("$")
        candidate = hashlib.sha256((salt + normalize(guess)).encode("utf-8")).hexdigest()
        return candidate == digest
    if fmt == FORMAT_MD5_LEGACY:
        candidate = hashlib.md5(guess.strip().encode("utf-8"), usedforsecurity=False).hexdigest()
        return candidate == encoded
    return False
