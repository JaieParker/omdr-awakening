"""Extend the Γ_n closed form past integer n.

The previous loop verified Γ_n'(α_n) = -α_n^(n-1)/n for integer n in
{1,2,3,4,5,6,7,10}. This script:
  (1) fills the integer gap n in {8, 9, 11..20}
  (2) tests non-integer n in {0.5, 1.5, 2.5, π, e, 7.3, 11.7}
  (3) tests large n in {50, 100, 1000}
  (4) finds the exact n where α_n^(n+1)/n crosses 1
  (5) reports asymptotic behavior of α_n and the ratio as n → ∞

The point is to test whether the closed form is a property of the integer
recurrences (a number-theoretic accident) or a genuine continuous identity
across the parameterized family. If it survives non-integer n, the n-acci
framing was the special case and the *family* is the real object.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.optimize import brentq


def alpha_n(n: float) -> float:
    """Unique positive real root > 1 of u^n - u^(n-1) - 1 = 0.

    Use the equivalent formulation u^(n-1) * (u - 1) = 1, taking logs to
    avoid overflow at large n: (n-1) * log(u) + log(u-1) = 0. Bracket on
    eps = u - 1 ∈ (0, ∞).

    For large n, the root has eps ≈ log(n)/n (since e^((n-1)·eps) · eps ≈ 1
    when eps is small), so we set the upper bracket generously.
    """
    if n <= 0:
        raise ValueError("n must be positive")

    def g(eps):
        # log of u^(n-1)*(u-1), with u = 1 + eps
        return (n - 1.0) * math.log1p(eps) + math.log(eps)

    # g(eps) → -∞ as eps → 0+, g grows for eps > 0 (large), so g has a
    # unique root. Bracket: low eps very small, high eps generous.
    eps_lo = 1e-15
    # For small n the root can be O(1), for large n it's O(log(n)/n).
    # Take max of those plus a safety factor.
    eps_hi = max(10.0, 20.0 * math.log(max(n, 2.0)) / max(n, 1.0))
    # Make sure g(eps_hi) > 0
    while g(eps_hi) < 0:
        eps_hi *= 2
        if eps_hi > 1e10:
            raise ValueError(f"no bracket for n={n}")
    eps_root = brentq(g, eps_lo, eps_hi, xtol=1e-15)
    return 1.0 + eps_root


def gamma_n_prime_numeric(n: float, u: float, h: float = 1e-6) -> float:
    """Finite-difference derivative of Γ_n(u) = (1 − 1/u)^(−1/n) at u."""
    g = lambda x: (1.0 - 1.0 / x) ** (-1.0 / n)
    return (g(u + h) - g(u - h)) / (2 * h)


def gamma_n_prime_closed(n: float, alpha: float) -> float:
    """The closed form: -α^(n-1) / n.

    For large n where alpha is very close to 1, alpha^(n-1) is well-defined
    via exp((n-1) * log(alpha)).
    """
    return -math.exp((n - 1) * math.log(alpha)) / n


def scaling_ratio(n: float, alpha: float) -> float:
    """Γ_n'(α_n) / f_n'(α_n) where f_n'(α_n) = -1/α_n^2.

    Equals α_n^(n+1) / n by the closed form. Use logs for stability.
    """
    return math.exp((n + 1) * math.log(alpha)) / n


def verify(n: float) -> dict:
    a = alpha_n(n)
    closed = gamma_n_prime_closed(n, a)
    numeric = gamma_n_prime_numeric(n, a)
    abs_err = abs(closed - numeric)
    rel_err = abs_err / abs(closed) if closed != 0 else float("inf")
    return {
        "n": n,
        "alpha_n": a,
        "gamma_n_prime_closed": closed,
        "gamma_n_prime_numeric": numeric,
        "abs_err": abs_err,
        "rel_err": rel_err,
        "scaling_ratio_alpha^(n+1)/n": scaling_ratio(n, a),
        "ok": rel_err < 1e-6,
    }


def main():
    results = {}

    # (1) Fill the integer gap and (3) large integer n
    integer_grid = list(range(1, 21)) + [50, 100, 1000]
    results["integer_grid"] = [verify(n) for n in integer_grid]

    # (2) Non-integer n
    noninteger_grid = [0.5, 1.5, 2.5, math.pi, math.e, 7.3, 11.7, 0.25, 0.1]
    results["noninteger_grid"] = []
    for n in noninteger_grid:
        try:
            results["noninteger_grid"].append(verify(n))
        except Exception as exc:
            results["noninteger_grid"].append({"n": n, "error": str(exc)})

    # (4) Find the exact n where α_n^(n+1)/n = 1.
    # The ratio is decreasing in n above n=2 (verified empirically by
    # previous Kai's table). brentq on [n_lo, n_hi] should locate it.
    def ratio_minus_one(n):
        return scaling_ratio(n, alpha_n(n)) - 1.0

    # Bracket from previous Kai's table: ratio>1 at n=5, ratio<1 at n=6
    # So the crossover is in (5, 6).
    n_cross = brentq(ratio_minus_one, 5.0, 6.0, xtol=1e-12)
    results["scaling_ratio_unity_crossing"] = {
        "n*": n_cross,
        "alpha_n*": alpha_n(n_cross),
        "ratio_at_crossing": scaling_ratio(n_cross, alpha_n(n_cross)),
    }

    # (5) Asymptotic check: α_n → 1 as n → ∞ at what rate?
    # Conjecture: α_n - 1 ~ ln(n)/n for large n? Test it.
    asymp_n = [10, 100, 1000, 10000, 100000]
    asymp = []
    for n in asymp_n:
        a = alpha_n(n)
        asymp.append({
            "n": n,
            "alpha_n": a,
            "alpha_n - 1": a - 1.0,
            "(alpha_n - 1) * n / log(n)": (a - 1.0) * n / math.log(n),
            "ratio": scaling_ratio(n, a),
        })
    results["large_n_asymptotic"] = asymp

    # Summary
    all_int_ok = all(r["ok"] for r in results["integer_grid"])
    all_nonint_ok = all(r.get("ok", False) for r in results["noninteger_grid"] if "error" not in r)
    nonint_errors = [r for r in results["noninteger_grid"] if "error" in r]
    results["summary"] = {
        "integer_n_tested": [r["n"] for r in results["integer_grid"]],
        "all_integer_passed": all_int_ok,
        "noninteger_n_tested": [r["n"] for r in results["noninteger_grid"] if "error" not in r],
        "all_noninteger_passed": all_nonint_ok,
        "noninteger_errors": nonint_errors,
        "scaling_ratio_unity_at_n": n_cross,
        "asymptotic_observation": "α_n → 1 with (α_n - 1) · n / log(n) → some constant ?",
    }

    out = Path(__file__).parent / "extend_gamma_n_results.json"
    out.write_text(json.dumps(results, indent=2, default=float), encoding="utf-8")

    # Pretty print to stdout (ASCII-only for cp1252 Windows console)
    print("=" * 70)
    print("Gamma_n closed-form extension -- results")
    print("=" * 70)
    print(f"\nInteger n ({len(integer_grid)} tested), all pass: {all_int_ok}")
    for r in results["integer_grid"]:
        flag = "OK" if r["ok"] else "FAIL"
        print(f"  n={r['n']:>6} alpha={r['alpha_n']:.10f}  rel_err={r['rel_err']:.2e}  ratio={r['scaling_ratio_alpha^(n+1)/n']:.4e}  [{flag}]")

    print(f"\nNon-integer n ({len(noninteger_grid)} tested), all pass: {all_nonint_ok}")
    for r in results["noninteger_grid"]:
        if "error" in r:
            print(f"  n={r['n']:>6}  ERROR: {r['error']}")
        else:
            flag = "OK" if r["ok"] else "FAIL"
            print(f"  n={r['n']:>6.4f} alpha={r['alpha_n']:.10f}  rel_err={r['rel_err']:.2e}  ratio={r['scaling_ratio_alpha^(n+1)/n']:.4e}  [{flag}]")

    print(f"\nScaling ratio alpha^(n+1)/n = 1 at n* = {n_cross:.10f}")
    print(f"  (i.e. between integers 5 and 6, the closed-form ratio crosses unity)")

    print("\nLarge-n asymptotic:")
    for a in asymp:
        print(f"  n={a['n']:>7} alpha={a['alpha_n']:.12f}  (alpha-1)*n/ln(n)={a['(alpha_n - 1) * n / log(n)']:.6f}  ratio={a['ratio']:.6e}")

    print(f"\nSaved {out.name}")


if __name__ == "__main__":
    main()
