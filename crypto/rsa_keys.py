from Crypto.PublicKey import RSA
import os

PUBLIC_KEY_FILE = "public.pem"
PRIVATE_KEY_FILE = "private.pem"

def load_or_generate_keys():
    # If keys already exist → load them
    if os.path.exists(PUBLIC_KEY_FILE) and os.path.exists(PRIVATE_KEY_FILE):
        with open(PUBLIC_KEY_FILE, "rb") as f:
            public_key = RSA.import_key(f.read())

        with open(PRIVATE_KEY_FILE, "rb") as f:
            private_key = RSA.import_key(f.read())

        return public_key, private_key

    # Else → generate and save
    key = RSA.generate(2048)
    public_key = key.publickey()
    private_key = key

    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(public_key.export_key())

    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(private_key.export_key())

    print("[RSA] New key pair generated and saved.")

    return public_key, private_key


# Load keys globally (same for all imports)
PUBLIC_KEY, PRIVATE_KEY = load_or_generate_keys()