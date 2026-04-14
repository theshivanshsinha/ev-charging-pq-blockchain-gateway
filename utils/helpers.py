def generate_vmid(uid: str, mobile: str) -> str:
    """
    Create Vehicle Mobile ID (VMID) from UID and full mobile number.
    Spec: "Users use their UID and mobile number to create their VMID."
    Using the full mobile (not just last 4 digits) ensures global uniqueness.
    """
    return uid + mobile