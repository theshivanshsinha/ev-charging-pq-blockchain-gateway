"""
SHA-3 / Keccak-256 hashing for UID and FID generation.

NOTE on SHA3 vs Keccak-256:
  The spec says "Keccak-256" (the original submission to NIST).
  Python's hashlib.sha3_256 implements NIST FIPS 202 SHA3-256, which differs
  from the original Keccak-256 in its padding (domain separation byte).
  For true Keccak-256 (as used in Ethereum), use pycryptodome:
      from Crypto.Hash import keccak
      k = keccak.new(digest_bits=256)
  Both options are provided below; NIST SHA3-256 is the default.
"""

import hashlib
import time


def generate_id(name: str, password: str, zone_code: str = "") -> str:
    """
    Generate a 16-character hex ID (UID or FID).

    Hash input: name + zone_code + password + current_timestamp
    Algorithm : SHA3-256 (NIST FIPS 202)
    Output    : first 16 hex characters of the digest
    """
    timestamp = str(time.time())
    raw_data  = name + zone_code + password + timestamp
    digest    = hashlib.sha3_256(raw_data.encode()).hexdigest()
    return digest[:16]


def generate_id_keccak(name: str, password: str, zone_code: str = "") -> str:
    """
    Same as generate_id but uses true Keccak-256 (original, pre-NIST padding).
    Requires: pip install pycryptodome
    """
    try:
        from Crypto.Hash import keccak
        timestamp = str(time.time())
        raw_data  = name + zone_code + password + timestamp
        k         = keccak.new(digest_bits=256)
        k.update(raw_data.encode())
        return k.hexdigest()[:16]
    except ImportError:
        print("[WARNING] pycryptodome not installed — falling back to NIST SHA3-256")
        return generate_id(name, password, zone_code)


def sha3_hash(data: str) -> str:
    """General-purpose SHA3-256 hash of any string. Returns full hex digest."""
    return hashlib.sha3_256(data.encode()).hexdigest()