"""
EV Owner (User) application.

Security flow per spec §5 (Quantum Cryptography):
  • VMID and PIN are encrypted with the Grid's RSA public key before transmission.
  • The Grid decrypts with its private key — plaintext credentials never travel over the network.
  • Shor's algorithm demo shows this RSA channel can be broken by a quantum computer.
"""

import requests
import json
from crypto.rsa_sim import encrypt as rsa_encrypt
from crypto.rsa_keys import PUBLIC_KEY

GRID_URL = "http://127.0.0.1:8000"


def get_user_input():
    vmid   = input("Enter VMID  : ")
    pin    = input("Enter PIN   : ")
    amount = float(input("Enter amount: "))
    return vmid, pin, amount


def send_transaction(vmid: str, pin: str, amount: float, fid: str) -> dict:
    """
    Encrypt VMID + PIN with RSA public key and send ciphertext to Grid.
    Plaintext credentials never leave the user device unencrypted.
    """
    credential           = json.dumps({"vmid": vmid, "pin": pin})
    encrypted_credential = rsa_encrypt(PUBLIC_KEY, credential)

    print(f"\n[USER] Credentials encrypted with RSA public key.")
    print(f"[USER] Encrypted (first 60 chars): {encrypted_credential[:60]}...")

    response = requests.post(
        f"{GRID_URL}/process_transaction",
        params={
            "encrypted_credential": encrypted_credential,
            "amount":               amount,
            "fid":                  fid,
        }
    )
    return response.json()