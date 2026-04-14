"""
Lightweight Cryptography using ASCON-128 (NIST standard, 2023).
Used for encrypting the Franchise ID (FID) / Virtual Franchise ID (VFID)
in the QR code — suitable for resource-constrained IoT / kiosk hardware.

Install: pip install ascon
"""
import os
import base64

try:
    import ascon
    _ASCON_AVAILABLE = True
except ImportError:
    _ASCON_AVAILABLE = False

# 16-byte key (128-bit) — in production, derive this via a proper KDF
# and store securely (env variable / HSM).  Never hardcode in real deployments.
KEY   = b"ev_kiosk_key_128"   # exactly 16 bytes
NONCE = b"ev_kiosk_nonce_1"   # exactly 16 bytes  (static nonce ok for demo;
                               # use os.urandom(16) per message in production)

VARIANT      = "Ascon-128"
ASSOCIATED   = b"EV_CHARGING_GATEWAY"   # authenticated associated data


def encrypt(plaintext: str) -> str:
    """
    Encrypt plaintext string using ASCON-128.
    Returns a base64-encoded string (nonce || ciphertext || tag).
    Falls back to XOR-based stub if ascon package is not installed.
    """
    if _ASCON_AVAILABLE:
        nonce      = os.urandom(16)          # fresh random nonce per message
        ciphertext = ascon.encrypt(
            KEY, nonce, ASSOCIATED, plaintext.encode(), variant=VARIANT
        )
        # Prepend nonce so decrypt can recover it
        return base64.b64encode(nonce + ciphertext).decode()
    else:
        # Fallback stub (clearly labelled — replace with real package)
        print("[WARNING] ascon package not found — using insecure XOR stub. Run: pip install ascon")
        return _xor_encrypt(plaintext)


def decrypt(token: str) -> str:
    """
    Decrypt a base64-encoded ASCON-128 ciphertext produced by encrypt().
    """
    if _ASCON_AVAILABLE:
        raw        = base64.b64decode(token)
        nonce      = raw[:16]
        ciphertext = raw[16:]
        plaintext  = ascon.decrypt(
            KEY, nonce, ASSOCIATED, ciphertext, variant=VARIANT
        )
        if plaintext is None:
            raise ValueError("ASCON decryption failed — authentication tag mismatch")
        return plaintext.decode()
    else:
        print("[WARNING] ascon package not found — using insecure XOR stub.")
        return _xor_decrypt(token)


#XOR stub (fallback only, not ASCON)

_XOR_KEY = "lightweightkey16"   # 16 chars for the stub

def _xor_encrypt(data: str) -> str:
    encrypted = "".join(
        chr(ord(c) ^ ord(_XOR_KEY[i % len(_XOR_KEY)])) for i, c in enumerate(data)
    )
    return base64.b64encode(encrypted.encode("latin-1")).decode()

def _xor_decrypt(data: str) -> str:
    decoded = base64.b64decode(data).decode("latin-1")
    return "".join(
        chr(ord(c) ^ ord(_XOR_KEY[i % len(_XOR_KEY)])) for i, c in enumerate(decoded)
    )