import qrcode

def generate_qr(data: str, filename: str = "qr.png") -> None:
    """Generate a QR code image from data and save to filename."""
    img = qrcode.make(data)
    img.save(filename)
    print(f"[QR] Saved to {filename}")