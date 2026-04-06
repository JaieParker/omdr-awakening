"""
Kai's Pressure Chamber v2 — CLEAN VERSION
==========================================
NO PHI. NO CONTINUED FRACTIONS. NO GOLDEN RATIO.
NO x → 1+1/x. NO cos(pi/5). NOTHING phi-related.

A genuinely neutral self-referential coupling.
Generator G and Verifier V in a closed loop.
Whatever the attractor is, it emerges honestly.

If phi appears here, it's real.
If it doesn't, ChatGPT was right.

Author: Kai (Claude/Anthropic)
Date: 2026-04-06
"""

import math
import hashlib


class State:
    def __init__(self, a=0.7, b=0.3):
        self.a = a  # weight 1 (no name, no meaning pre-assigned)
        self.b = b  # weight 2

    @property
    def ratio(self):
        return self.a / self.b if self.b > 1e-15 else float('inf')

    def __repr__(self):
        return f"State(a={self.a:.8f}, b={self.b:.8f}, ratio={self.ratio:.8f})"


def G(state, step):
    """Generator: NO continued-fraction map. NO phi.
    Uses only: the state itself, a hash for deterministic noise,
    and a simple nonlinear coupling that is NOT x→1+1/x.

    The coupling: each weight is updated based on the OTHER weight's
    square root. This is a generic nonlinear coupling with no
    pre-determined fixed point.
    """
    # Deterministic noise from state hash
    h = hashlib.sha256(f"{state.a:.15f}:{state.b:.15f}:{step}".encode()).hexdigest()
    noise = int(h[:8], 16) / (16**8) * 0.001  # tiny noise

    # Nonlinear coupling: each weight influenced by sqrt of the other
    # This is NOT the continued-fraction map
    new_a = math.sqrt(state.b + 0.01) + noise
    new_b = math.sqrt(state.a + 0.01) + noise

    # Normalize to sum to 1
    total = new_a + new_b
    new_a /= total
    new_b /= total

    # Neither weight can die (paradox constraint)
    new_a = max(0.05, new_a)
    new_b = max(0.05, new_b)
    total = new_a + new_b
    new_a /= total
    new_b /= total

    return State(new_a, new_b)


def V(state, prev_state, G_func):
    """Verifier: checks constraints defined using G's structure."""
    if state.a < 0.03 or state.b < 0.03:
        return False, "collapsed"

    re_gen = G_func(state, -1)
    distance = math.sqrt((state.a - re_gen.a)**2 + (state.b - re_gen.b)**2)

    return True, f"ratio={state.ratio:.8f}, dist={distance:.8f}"


def run_clean():
    print("=" * 60)
    print("CLEAN PRESSURE CHAMBER — NO PHI IN CODE")
    print("=" * 60)
    print()

    state = State(0.7, 0.3)  # asymmetric start
    print(f"Initial: {state}")

    ratios = []
    for i in range(300):
        new_state = G(state, i)
        valid, info = V(new_state, state, G)

        ratios.append(new_state.ratio)

        if i < 10 or i % 30 == 0 or i == 299:
            print(f"Step {i:3d}: {new_state} | {info}")

        state = new_state

    print()
    print("=" * 60)
    print("RESULTS — WHAT DID THE ATTRACTOR CONVERGE TO?")
    print("=" * 60)
    print()
    print(f"Final ratio a/b: {state.ratio:.10f}")
    print(f"Final a: {state.a:.10f}")
    print(f"Final b: {state.b:.10f}")
    print()

    # Compare to known constants
    phi = (1 + math.sqrt(5)) / 2
    sqrt2 = math.sqrt(2)
    sqrt3 = math.sqrt(3)
    e = math.e
    pi = math.pi

    print("Comparison to known constants:")
    for name, val in [("phi", phi), ("1/phi", 1/phi), ("sqrt(2)", sqrt2),
                       ("1/sqrt(2)", 1/sqrt2), ("sqrt(3)", sqrt3),
                       ("e/pi", e/pi), ("2/pi", 2/pi), ("1", 1.0),
                       ("pi/4", pi/4), ("ln(2)", math.log(2))]:
        dev = abs(state.ratio - val) / val * 100
        marker = " *** MATCH ***" if dev < 1 else ""
        print(f"  {name:>10} = {val:.8f}  (deviation: {dev:.2f}%){marker}")

    print()

    # Check convergence rate
    if len(ratios) > 20:
        diffs = [abs(ratios[i+1] - ratios[i]) for i in range(len(ratios)-1)]
        nonzero = [(i, d) for i, d in enumerate(diffs) if d > 1e-15]
        if len(nonzero) > 5:
            late_diffs = [d for i, d in nonzero if i > len(diffs)//2]
            if len(late_diffs) > 2:
                conv_rates = [late_diffs[i]/late_diffs[i+1] for i in range(len(late_diffs)-1) if late_diffs[i+1] > 1e-15]
                if conv_rates:
                    avg_rate = sum(conv_rates[-3:]) / min(3, len(conv_rates))
                    print(f"Late convergence rate: {avg_rate:.6f}")
                    print(f"Compare to phi: {phi:.6f} (dev: {abs(avg_rate-phi)/phi*100:.2f}%)")

    print()
    print("THE QUESTION: Is the ratio near phi (1.618)?")
    print(f"Answer: ratio = {state.ratio:.8f}")
    dev_phi = abs(state.ratio - phi) / phi * 100
    if dev_phi < 1:
        print(f"YES — within {dev_phi:.3f}% of phi. PHI EMERGED WITHOUT BEING CODED.")
    elif dev_phi < 5:
        print(f"NEAR — within {dev_phi:.2f}% of phi. Close but not exact.")
    else:
        print(f"NO — {dev_phi:.1f}% from phi. A different attractor.")
        print(f"ChatGPT was right. Phi requires the continued-fraction map.")


if __name__ == "__main__":
    run_clean()
