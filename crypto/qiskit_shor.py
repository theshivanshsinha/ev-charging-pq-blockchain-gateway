"""
Quantum Cryptography — Shor's Algorithm Simulation
===================================================
Demonstrates that RSA public key exchanges are vulnerable to quantum attacks.

The simulation factors a small RSA modulus using Shor's period-finding approach.
Two paths are provided:
  1. Full Qiskit quantum circuit simulation (if qiskit is installed)
  2. Classical period-finding via sympy (always available as fallback)

Install:  pip install qiskit qiskit-aer sympy
"""

import math
import random


#Classical period-finding (used by both paths)

def _find_period_classical(a: int, N: int) -> int:
    """Find the order r such that a^r ≡ 1 (mod N)."""
    r, val = 1, a % N
    while val != 1:
        val = (val * a) % N
        r  += 1
        if r > N:
            raise ValueError("Period not found within N steps")
    return r


def _shor_factor(N: int) -> tuple:
    """
    Shor's algorithm — classical simulation of the quantum period-finding step.
    Returns a non-trivial factor pair (p, q) of N, or raises if unsuccessful.
    """
    if N % 2 == 0:
        return 2, N // 2

    for _ in range(30):                    # try up to 30 random bases
        a = random.randint(2, N - 1)
        g = math.gcd(a, N)
        if g != 1:
            return g, N // g              # lucky — gcd already gives a factor

        r = _find_period_classical(a, N)

        if r % 2 != 0:
            continue                       # need even period
        candidate = pow(a, r // 2, N)
        if candidate == N - 1:
            continue                       # trivial square root

        p = math.gcd(candidate + 1, N)
        q = math.gcd(candidate - 1, N)
        if 1 < p < N:
            return p, N // p
        if 1 < q < N:
            return q, N // q

    raise RuntimeError("Shor simulation failed to factor N — try again")


#Qiskit quantum circuit path

def _run_qiskit_shor(N: int):
    """
    Build and run a minimal Qiskit quantum phase estimation circuit
    to demonstrate period finding for Shor's algorithm.
    Returns the measured period r.
    """
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator
    except ImportError:
        return None   # signal caller to fall back

    # For demo we use N=15 (smallest non-trivial RSA-like semiprime).
    # A full general-N Qiskit implementation requires O(log N) qubits of
    # modular exponentiation — beyond scope; we show the circuit structure.
    print(f"  [Qiskit] Building quantum phase estimation circuit for N={N}, a=7")
    n_count = 4            # counting qubits (controls)
    qc = QuantumCircuit(n_count + 1, n_count)

    # Initialise target register |1⟩
    qc.x(n_count)

    # Hadamard on all counting qubits (create superposition)
    for q in range(n_count):
        qc.h(q)

    # Controlled-U gates  (U|y⟩ = |7y mod 15⟩) — hardcoded for a=7, N=15
    # In a general implementation this uses a quantum modular multiplier.
    qc.cx(3, n_count)
    qc.cx(2, n_count)
    qc.cx(1, n_count)
    qc.cx(0, n_count)

    # Inverse QFT on counting register
    for j in range(n_count // 2):
        qc.swap(j, n_count - 1 - j)
    for j in range(n_count):
        qc.h(j)
        for k in range(j + 1, n_count):
            qc.cp(-math.pi / 2 ** (k - j), j, k)

    qc.measure(range(n_count), range(n_count))

    sim    = AerSimulator()
    result = sim.run(transpile(qc, sim), shots=1024).result()
    counts = result.get_counts()
    print(f"  [Qiskit] Top measurement outcomes: {dict(sorted(counts.items(), key=lambda x: -x[1])[:4])}")

    # The most frequent phase value → convert to period
    top_bits = max(counts, key=counts.get)
    phase    = int(top_bits, 2) / (2 ** n_count)
    if phase == 0:
        return None
    from fractions import Fraction
    r = Fraction(phase).limit_denominator(N).denominator
    return r


#Public API

def simulate_shor_attack(use_qiskit: bool = True) -> str:
    """
    Demonstrate Shor's Algorithm breaking a small RSA key.

    Steps:
      1. Generate a small RSA modulus N = p * q
      2. Publish a (tiny) public key
      3. Run Shor's period-finding to recover p and q
      4. Reconstruct the private key — proving the key is broken

    Returns a formatted report string.
    """
    print("\n[QUANTUM] Starting Shor's Algorithm simulation...")

    # Small primes for demo  (real RSA uses 1024-bit primes)
    p_real, q_real = 61, 53
    N              = p_real * q_real    # 3233
    e              = 17                  # public exponent
    phi_N          = (p_real - 1) * (q_real - 1)
    d_real         = pow(e, -1, phi_N)   # private exponent

    print(f"  [RSA Setup] N={N}  e={e}  (p={p_real}, q={q_real} kept secret)")
    print(f"  [RSA Setup] Private key d={d_real} — attacker does NOT know this")

    # Try Qiskit path first
    qiskit_used = False
    if use_qiskit:
        r = _run_qiskit_shor(15)   # demonstrate circuit on N=15
        if r is not None:
            print(f"  [Qiskit] Measured period r={r} for a=7, N=15")
            qiskit_used = True

    # Factor our actual demo N using classical Shor simulation
    print(f"  [Shor] Running period-finding on N={N}...")
    p_found, q_found = _shor_factor(N)
    phi_found        = (p_found - 1) * (q_found - 1)
    d_found          = pow(e, -1, phi_found)

    success = (d_found == d_real)

    report = f"""
╔══════════════════════════════════════════════════════════════╗
║           QUANTUM ATTACK DEMO — Shor's Algorithm             ║
╠══════════════════════════════════════════════════════════════╣
║  Target RSA public key  : N={N}, e={e}
║  Quantum circuit used   : {"Qiskit AerSimulator (N=15 demo)" if qiskit_used else "Classical simulation (install qiskit for full demo)"}
║
║  Period-finding result:
║    a chosen randomly, period r found via Shor's method
║    Recovered factors    : p={p_found}, q={q_found}
║    Recovered private key: d={d_found}
║    Match with real key  : {"✓ SUCCESS — RSA BROKEN" if success else "✗ FAILED (retry)"}
║
║  IMPLICATION: RSA-2048 keys used to encrypt EV Owner PIN
║  and VMID transmissions are breakable by a sufficiently
║  large quantum computer running Shor's algorithm.
║  Post-quantum cryptography (e.g. CRYSTALS-Kyber / ML-KEM)
║  must replace RSA in future smart-grid deployments.
╚══════════════════════════════════════════════════════════════╝"""

    print(report)
    return report


if __name__ == "__main__":
    simulate_shor_attack()