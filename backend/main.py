"""
Grid Authority — FastAPI backend server.

Responsibilities:
  • Register users and franchises under grid zones
  • Receive RSA-encrypted credentials, decrypt, validate, process transaction
  • Record valid transactions to the blockchain ledger
  • Expose blockchain and balance endpoints
"""

import hashlib
import time
import json
import os
import sys

# Allow running this file directly from the backend folder.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from blockchain.blockchain import Blockchain
from crypto.sha3_hash import generate_id
from crypto.rsa_sim import decrypt as rsa_decrypt
from utils.helpers import generate_vmid
from crypto.rsa_keys import PRIVATE_KEY as _RSA_PRIVATE_KEY
app        = FastAPI()
blockchain = Blockchain()

# --- Grid structure: 3 providers, 3 zones each ---
GRID = {
    "TataPower":   {"zones": ["TP-NORTH", "TP-SOUTH", "TP-WEST"]},
    "Adani":       {"zones": ["AD-NORTH", "AD-SOUTH", "AD-EAST"]},
    "ChargePoint": {"zones": ["CP-EAST",  "CP-WEST",  "CP-CENTRAL"]},
}

users      = {}   # uid  -> user dict
franchises = {}   # fid  -> franchise dict


#helpers

def valid_zone(zone_code: str) -> bool:
    for provider in GRID.values():
        if zone_code in provider["zones"]:
            return True
    return False


#endpoints

@app.get("/grid_info")
def grid_info():
    """Return available providers and zone codes."""
    return GRID


@app.post("/register_user")
def register_user(name: str, password: str, mobile: str, pin: str, zone_code: str):
    if not valid_zone(zone_code):
        return {"error": f"Invalid zone_code. Choose from: {[z for p in GRID.values() for z in p['zones']]}"}

    uid  = generate_id(name, password)
    vmid = generate_vmid(uid, mobile)

    # Keep in-memory state stable while backend is running.
    # Re-registration should not reset wallet balance.
    if uid in users:
        existing = users[uid]
        print(f"[GRID] User already registered: UID={uid}  Balance preserved={existing['balance']}")
        return {
            "UID": uid,
            "VMID": existing["vmid"],
            "zone_code": existing["zone_code"],
            "message": "User already registered; existing balance preserved",
        }

    users[uid] = {
        "name":      name,
        "password":  password,
        "pin":       pin,
        "mobile":    mobile,
        "vmid":      vmid,
        "zone_code": zone_code,
        "balance":   1000.0,
    }
    print(f"[GRID] User Registered: UID={uid}  VMID={vmid}  Zone={zone_code}")
    return {"UID": uid, "VMID": vmid, "zone_code": zone_code}


@app.post("/register_franchise")
def register_franchise(name: str, password: str, zone_code: str, initial_balance: float = 0.0):
    if not valid_zone(zone_code):
        return {"error": f"Invalid zone_code. Choose from: {[z for p in GRID.values() for z in p['zones']]}"}

    fid = generate_id(name, password, zone_code)

    # Keep in-memory state stable while backend is running.
    # Re-registration should not reset franchise balance.
    if fid in franchises:
        existing = franchises[fid]
        print(f"[GRID] Franchise already registered: FID={fid}  Balance preserved={existing['balance']}")
        return {
            "FID": fid,
            "zone_code": existing["zone_code"],
            "message": "Franchise already registered; existing balance preserved",
        }

    franchises[fid] = {
        "name":      name,
        "password":  password,
        "zone_code": zone_code,
        "balance":   initial_balance,
    }
    print(f"[GRID] Franchise Registered: FID={fid}  Zone={zone_code}")
    return {"FID": fid, "zone_code": zone_code}


@app.post("/process_transaction")
def process_transaction(encrypted_credential: str, amount: float, fid: str):
    print("\n[GRID] Processing Transaction...")

    #Step 1: Decrypt RSA-encrypted credentials
    try:
        decrypted = json.loads(rsa_decrypt(_RSA_PRIVATE_KEY, encrypted_credential))
        vmid      = decrypted["vmid"]
        pin       = decrypted["pin"]
        print(f"[GRID] Decrypted credentials — VMID: {vmid}, PIN: {'*' * len(pin)}")
    except Exception as e:
        print(f"[GRID] Decryption failed: {e}")
        return {"status": f"Decryption failed: {e}"}

    #Step 2: Validate user, PIN, balance, franchise
    user = next((u for u in users.values() if u["vmid"] == vmid), None)
    if not user:
        print("[GRID] User not found")
        return {"status": "User not found"}

    if user["pin"] != pin:
        print("[GRID] Invalid PIN")
        return {"status": "Invalid PIN"}

    if user["balance"] < amount:
        print("[GRID] Insufficient balance")
        return {"status": "Insufficient balance"}

    if fid not in franchises:
        print("[GRID] Invalid Franchise")
        return {"status": "Invalid Franchise"}

    print("[GRID] Validation successful")

    #Step 3: Transfer funds
    ts = time.time()
    user["balance"]            -= amount
    franchises[fid]["balance"] += amount
    print("[GRID] Balances updated")

    #Step 4: Build and record transaction block
    uid    = next(k for k, v in users.items() if v["vmid"] == vmid)
    tx_raw = uid + fid + str(ts) + str(amount)
    tx_id  = hashlib.sha3_256(tx_raw.encode()).hexdigest()

    transaction_data = {
        "tx_id":        tx_id,
        "uid":          uid,
        "vmid":         vmid,
        "fid":          fid,
        "amount":       amount,
        "timestamp":    ts,
        "status":       "success",
        "dispute_flag": False,
    }
    blockchain.add_block(transaction_data)
    print("[BLOCKCHAIN] Block added")

    #Step 5: Hardware failure edge case (set True to test)
    hardware_failure = False
    if hardware_failure:
        print("[SYSTEM] Hardware failure after payment — issuing refund block")
        user["balance"]            += amount
        franchises[fid]["balance"] -= amount
        refund_ts = time.time()
        blockchain.add_block({
            "tx_id":        tx_id + "_refund",
            "uid":          uid,
            "vmid":         vmid,
            "fid":          fid,
            "amount":       -amount,
            "timestamp":    refund_ts,
            "status":       "refund",
            "dispute_flag": True,
        })
        return {"status": "Charging Failed — Refunded"}

    return {"status": "Transaction Successful"}


@app.get("/get_blockchain")
def get_blockchain():
    return [
        {
            "index":     block.index,
            "timestamp": block.timestamp,
            "data":      block.data,
            "prev_hash": block.prev_hash,
            "hash":      block.hash,
        }
        for block in blockchain.chain
    ]


@app.get("/get_balances")
def get_balances():
    return {
        "users": {
            uid: {
                "name": u["name"],
                "balance": u["balance"],
                "zone_code": u["zone_code"],
            }
            for uid, u in users.items()
        },
        "franchises": {
            fid: {
                "name": f["name"],
                "balance": f["balance"],
                "zone_code": f["zone_code"],
            }
            for fid, f in franchises.items()
        },
    }