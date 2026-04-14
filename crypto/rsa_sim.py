"""
RSA simulation used to encrypt EV Owner credentials (VMID + PIN)
before transmission to the Grid Authority.

This is the classical public-key channel that Shor's algorithm can break,
demonstrating the vulnerability highlighted in Section 5 of the spec.

Install: pip install pycryptodome
"""

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64


def generate_keys():
    """Generate a 2048-bit RSA key pair. Returns (public_key, private_key)."""
    key = RSA.generate(2048)
    return key.publickey(), key


def encrypt(public_key, message: str) -> str:
    """Encrypt a UTF-8 message with the RSA public key. Returns base64 string."""
    cipher     = PKCS1_OAEP.new(public_key)
    ciphertext = cipher.encrypt(message.encode())
    return base64.b64encode(ciphertext).decode()


def decrypt(private_key, ciphertext_b64: str) -> str:
    """Decrypt a base64 RSA ciphertext with the private key. Returns plaintext."""
    cipher     = PKCS1_OAEP.new(private_key)
    ciphertext = base64.b64decode(ciphertext_b64)
    return cipher.decrypt(ciphertext).decode()


def export_public_key(public_key) -> str:
    """Export public key as PEM string (for display / logging)."""
    return public_key.export_key().decode()


if __name__ == "__main__":
    pub, priv = generate_keys()
    msg       = "VMID=440786613aea15483210|PIN=1234"
    enc       = encrypt(pub, msg)
    dec       = decrypt(priv, enc)
    print("Original :", msg)
    print("Encrypted:", enc[:60], "...")
    print("Decrypted:", dec)
    print("Match     :", msg == dec)