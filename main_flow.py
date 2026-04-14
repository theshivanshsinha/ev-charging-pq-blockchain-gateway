"""
Menu-driven EV charging demo flow.
Run once and operate repeatedly like a kiosk.
"""

import requests
from datetime import datetime
from kiosk.kiosk import create_qr, process_scan
from user.user_app import send_transaction
from crypto.qiskit_shor import simulate_shor_attack

GRID_URL = "http://127.0.0.1:8000"


def divider(char: str = "-", width: int = 72) -> str:
    return char * width


def now_timeline() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fetch_balances() -> dict:
    return requests.get(f"{GRID_URL}/get_balances").json()


def prompt_non_empty(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("[ERROR] Value cannot be empty.")


def prompt_float(label: str, minimum: float = 0.0) -> float:
    while True:
        raw = input(f"{label}: ").strip()
        try:
            value = float(raw)
            if value < minimum:
                print(f"[ERROR] Value must be >= {minimum}.")
                continue
            return value
        except ValueError:
            print("[ERROR] Enter a valid number.")


def prompt_choice(label: str, valid_choices: list[str]) -> str:
    valid_set = set(valid_choices)
    while True:
        choice = input(f"{label}: ").strip()
        if choice in valid_set:
            return choice
        print(f"[ERROR] Choose one of: {', '.join(valid_choices)}")


def zone_balance_snapshot(grid: dict, balances: dict) -> dict:
    zone_totals = {}
    for provider in grid.values():
        for zone in provider["zones"]:
            zone_totals[zone] = {"user_total": 0.0, "franchise_total": 0.0}

    for u in balances.get("users", {}).values():
        zone = u.get("zone_code")
        if zone in zone_totals:
            zone_totals[zone]["user_total"] += float(u.get("balance", 0.0))

    for f in balances.get("franchises", {}).values():
        zone = f.get("zone_code")
        if zone in zone_totals:
            zone_totals[zone]["franchise_total"] += float(f.get("balance", 0.0))
    return zone_totals


def show_grid_info() -> dict:
    grid = requests.get(f"{GRID_URL}/grid_info").json()
    balances = fetch_balances()
    zone_totals = zone_balance_snapshot(grid, balances)
    print(f"\n{divider('=')}")
    print("[GRID] Providers, Zones, and Balance Summary")
    print(divider("="))
    for provider, data in grid.items():
        print(f"\n  {provider}")
        print(f"  {divider('.', 64)}")
        for zone in data["zones"]:
            z = zone_totals.get(zone, {"user_total": 0.0, "franchise_total": 0.0})
            combined = z["user_total"] + z["franchise_total"]
            print(
                f"    {zone:<11} | Users: ₹{z['user_total']:>10.2f} | "
                f"Franchises: ₹{z['franchise_total']:>10.2f} | Total: ₹{combined:>10.2f}"
            )
    return grid


def register_default_users() -> None:
    print("\n[STEP] Registering default users")
    user_inputs = [
        {"name": "Saniya", "pin": "1234", "zone": "TP-NORTH", "mobile": "9876543210"},
        {"name": "Rahul", "pin": "5678", "zone": "AD-SOUTH", "mobile": "9123456780"},
        {"name": "Ananya", "pin": "9999", "zone": "CP-EAST", "mobile": "9988776655"},
    ]
    for u in user_inputs:
        res = requests.post(
            f"{GRID_URL}/register_user",
            params={
                "name": u["name"],
                "password": "pass",
                "mobile": u["mobile"],
                "pin": u["pin"],
                "zone_code": u["zone"],
            },
        ).json()
        suffix = f" ({res['message']})" if "message" in res else ""
        print(f"  {u['name']} -> UID: {res['UID']} | VMID: {res['VMID']} | Zone: {res['zone_code']}{suffix}")


def register_default_franchise() -> str:
    print("\n[STEP] Registering default franchise")
    fr = requests.post(
        f"{GRID_URL}/register_franchise",
        params={
            "name": "Universal_Station",
            "password": "frpass",
            "zone_code": "TP-NORTH",
            "initial_balance": 500.0,
        },
    ).json()
    suffix = f" ({fr['message']})" if "message" in fr else ""
    print(f"  FID: {fr['FID']} | Zone: {fr['zone_code']}{suffix}")
    return fr["FID"]


def register_custom_franchise() -> None:
    print("\n[STEP] Registering custom franchise")
    grid = requests.get(f"{GRID_URL}/grid_info").json()
    valid_zones = [z for provider in grid.values() for z in provider["zones"]]
    print(f"  Valid zones: {', '.join(valid_zones)}")

    name = prompt_non_empty("Franchise name")
    password = prompt_non_empty("Franchise password")
    while True:
        zone_code = prompt_non_empty("Zone code").upper()
        if zone_code in valid_zones:
            break
        print(f"[ERROR] Invalid zone code: {zone_code}")
    initial_balance = prompt_float("Initial balance (e.g. 0)", minimum=0.0)

    fr = requests.post(
        f"{GRID_URL}/register_franchise",
        params={
            "name": name,
            "password": password,
            "zone_code": zone_code,
            "initial_balance": initial_balance,
        },
    ).json()
    if "error" in fr:
        print(f"[ERROR] {fr['error']}")
        return
    suffix = f" ({fr['message']})" if "message" in fr else ""
    print(f"  FID: {fr['FID']} | Zone: {fr['zone_code']}{suffix}")


def choose_franchise_by_zone() -> str | None:
    grid = requests.get(f"{GRID_URL}/grid_info").json()
    balances = fetch_balances()
    franchises = balances.get("franchises", {})
    if not franchises:
        print("[WARN] No franchises registered. Choose menu option 2 or 3 first.")
        return None

    zone_to_frs = {}
    for fid, fr in franchises.items():
        zone = fr.get("zone_code", "UNKNOWN")
        zone_to_frs.setdefault(zone, []).append((fid, fr))

    all_zones = [z for provider in grid.values() for z in provider["zones"]]
    print(f"\n{divider()}")
    print("[TXN] Select Target Zone")
    print(divider())
    for idx, zone in enumerate(all_zones, start=1):
        count = len(zone_to_frs.get(zone, []))
        print(f"  {idx}) {zone} ({count} franchise(s))")
    zone_choice = int(prompt_non_empty("Enter zone number"))
    if zone_choice < 1 or zone_choice > len(all_zones):
        print("[ERROR] Invalid zone selection.")
        return None

    selected_zone = all_zones[zone_choice - 1]
    fr_list = zone_to_frs.get(selected_zone, [])
    if not fr_list:
        print(f"[WARN] No franchise found in zone {selected_zone}.")
        return None

    print(f"\n[TXN] Franchises in {selected_zone}")
    print(f"  {divider('.', 64)}")
    for idx, (fid, fr) in enumerate(fr_list, start=1):
        print(f"  {idx}) {fr['name']} | FID={fid} | Balance=₹{fr['balance']}")

    fr_choice = int(prompt_non_empty("Enter franchise number"))
    if fr_choice < 1 or fr_choice > len(fr_list):
        print("[ERROR] Invalid franchise selection.")
        return None
    return fr_list[fr_choice - 1][0]


def run_transaction() -> None:
    balances = fetch_balances()
    users = list(balances.get("users", {}).values())
    if not users:
        print("\n[WARN] No users registered. Choose menu option 1 first.")
        return

    print(f"\n{divider()}")
    print("[TXN] Enter User Credentials")
    print(divider())
    vmid = prompt_non_empty("VMID")
    pin = prompt_non_empty("PIN")
    amount = prompt_float("Amount", minimum=0.01)
    print("\nSelect payment destination:")
    print("  1) Choose zone -> franchise")
    print("  2) Enter FID manually")
    mode = prompt_choice("Choice", ["1", "2"])
    if mode == "1":
        fid = choose_franchise_by_zone()
        if not fid:
            return
    else:
        fid = prompt_non_empty("Franchise FID")

    encrypted_qr_data = create_qr(fid)
    decoded_fid = process_scan(encrypted_qr_data)
    if not decoded_fid:
        print("[ERROR] QR decode failed.")
        return

    result = send_transaction(vmid, pin, amount, decoded_fid)
    print(f"[TXN] Result: {result.get('status', result)}")


def print_blockchain() -> None:
    bc_res = requests.get(f"{GRID_URL}/get_blockchain").json()
    print("\n[BLOCKCHAIN] Ledger")
    for block in bc_res:
        print("\n  " + "-" * 54)
        print(f"  [{now_timeline()}] Block Index   : {block['index']}")
        print(f"  Timestamp (unix): {block['timestamp']}")
        if block["index"] == 0:
            print(f"  Data            : {block['data']}")
        else:
            d = block["data"]
            print(f"  Transaction ID  : {d['tx_id']}")
            print(f"  UID             : {d['uid']}")
            print(f"  VMID            : {d['vmid']}")
            print(f"  FID             : {d['fid']}")
            print(f"  Amount          : {d['amount']}")
            print(f"  Status          : {d['status']}")
            print(f"  Dispute Flag    : {d['dispute_flag']}")
        print(f"  Previous Hash   : {block['prev_hash']}")
        print(f"  Current Hash    : {block['hash']}")


def print_balances() -> None:
    balances = fetch_balances()
    print(f"\n{divider('=')}")
    print("[BALANCES] Snapshot")
    print(divider("="))
    print(f"  Timeline Snapshot: {now_timeline()}")
    print("  " + "-" * 54)
    print("  USERS")
    print("  " + "-" * 54)
    for idx, (uid, u) in enumerate(balances.get("users", {}).items(), start=1):
        print(
            f"  [{idx:02d}] [{now_timeline()}] UID={uid} | Name={u['name']} | "
            f"Zone={u.get('zone_code', 'NA')} | Balance=₹{u['balance']}"
        )
    print("  " + "-" * 54)
    print("  FRANCHISES")
    print("  " + "-" * 54)
    for idx, (fid, f) in enumerate(balances.get("franchises", {}).items(), start=1):
        print(
            f"  [{idx:02d}] [{now_timeline()}] FID={fid} | Name={f['name']} | "
            f"Zone={f.get('zone_code', 'NA')} | Balance=₹{f['balance']}"
        )
    print("  " + "-" * 54)


def menu() -> None:
    print("\n" + "=" * 72)
    print(" EV Charging Payment Gateway - Interactive Kiosk")
    print("=" * 72)
    print(" 1) Register default users")
    print(" 2) Register default franchise")
    print(" 3) Register custom franchise")
    print(" 4) Make transaction")
    print(" 5) View blockchain")
    print(" 6) View balances")
    print(" 7) Run quantum demo")
    print(" 8) Show grid zones (with zone balances)")
    print(" 0) Exit")


def main() -> None:
    show_grid_info()
    while True:
        menu()
        choice = prompt_choice("Enter choice", ["0", "1", "2", "3", "4", "5", "6", "7", "8"])
        try:
            if choice == "1":
                register_default_users()
            elif choice == "2":
                register_default_franchise()
            elif choice == "3":
                register_custom_franchise()
            elif choice == "4":
                run_transaction()
            elif choice == "5":
                print_blockchain()
            elif choice == "6":
                print_balances()
            elif choice == "7":
                print("\n[STEP] Running Shor's Algorithm demo...")
                simulate_shor_attack(use_qiskit=True)
            elif choice == "8":
                show_grid_info()
            elif choice == "0":
                print("\nExiting kiosk demo.")
                break
        except ValueError:
            print("\nInvalid numeric input. Please try again.")
        except requests.RequestException as exc:
            print(f"\nNetwork/backend error: {exc}")


if __name__ == "__main__":
    main()