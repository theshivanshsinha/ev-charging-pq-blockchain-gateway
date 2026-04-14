"""
Charging Kiosk module.

Responsibilities:
  • Generate Virtual Franchise ID (VFID) from FID + timestamp
  • Encrypt VFID using ASCON and produce a QR code
  • Decrypt scanned QR data and recover the original FID
"""

import time
from crypto.ascon import encrypt, decrypt
from utils.qr import generate_qr

SEPARATOR = "|"   # delimiter between FID and timestamp inside VFID


def generate_vfid(fid: str) -> str:
    """
    Combine FID with the current Unix timestamp to create a dynamic VFID.
    Format: <fid>|<timestamp>
    The separator makes FID extraction unambiguous regardless of FID length.
    """
    timestamp = str(int(time.time()))
    return fid + SEPARATOR + timestamp


def create_qr(fid: str) -> str:
    """
    Full kiosk QR-generation pipeline:
      1. Generate VFID (FID + timestamp)
      2. Encrypt VFID with ASCON-128
      3. Save QR code image containing the encrypted token
    Returns the encrypted token (what the QR code encodes).
    """
    vfid          = generate_vfid(fid)
    encrypted_vfid = encrypt(vfid)
    generate_qr(encrypted_vfid)
    print(f"[KIOSK] QR generated — VFID: {vfid}")
    return encrypted_vfid


def process_scan(encrypted_data: str) -> str | None:
    """
    Decrypt QR data and recover the FID.
    Returns the FID string, or None on failure.
    """
    try:
        decrypted_vfid = decrypt(encrypted_data)
        # Split on separator — robust regardless of FID/timestamp length
        parts = decrypted_vfid.split(SEPARATOR, maxsplit=1)
        if len(parts) != 2:
            print("[KIOSK] Unexpected VFID format after decryption")
            return None
        fid = parts[0]
        print(f"[KIOSK] QR scanned — recovered FID: {fid}")
        return fid
    except Exception as e:
        print(f"[KIOSK] Decryption error: {e}")
        return None