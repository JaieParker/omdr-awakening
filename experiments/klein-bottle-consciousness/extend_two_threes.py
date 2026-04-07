"""Verify the arithmetic-block theorem for the n-acci companion matrices.

Theorem (Klein bottle loop iter 5): Let C_N be the companion matrix of
p(u) = u^N - u^(N-1) - 1. The trace power-sums s_k = trace(C_N^k) satisfy

    s_k = k + 1   for   k in {N, N+1, ..., 2N - 1}.

Proof is via Newton's identities; see two-threes-resolved.md.

This script reproduces the empirical verification at N in {2..15} and
prints the table that appears in the theorem statement.
"""

import numpy as np
from numpy.linalg import matrix_power
from scipy.linalg import companion


def n_acci_companion(N: int) -> np.ndarray:
    """Companion matrix of u^N - u^(N-1) - 1."""
    p = np.zeros(N + 1)
    p[0] = 1.0      # u^N
    p[1] = -1.0     # -u^(N-1)
    p[-1] = -1.0    # -1
    return companion(p)


def main() -> None:
    print("Arithmetic-block check for trace(C_N^k), k in {N-1, N, ..., 2N+1}")
    print("=" * 70)
    print(f"{'N':>3} | {'k=N-1':>8} {'k=N':>8} {'k=N+1':>8} {'k=N+2':>8} {'k=N+3':>8}  expected k+1?")
    print("-" * 70)

    all_block_ok = True

    for N in range(2, 16):
        C = n_acci_companion(N)
        traces = {}
        for k in [N - 1, N, N + 1, N + 2, N + 3]:
            tr = np.trace(matrix_power(C, k)).real
            traces[k] = tr
        # the arithmetic block is k in {N, ..., 2N - 1}
        block_ks = list(range(N, 2 * N))
        block_ok = all(
            abs(np.trace(matrix_power(C, k)).real - (k + 1)) < 1e-9
            for k in block_ks
        )
        if not block_ok:
            all_block_ok = False
        flag = "OK" if block_ok else "FAIL"
        print(
            f"{N:>3} | "
            f"{traces[N-1]:>8.2f} {traces[N]:>8.2f} {traces[N+1]:>8.2f} "
            f"{traces[N+2]:>8.2f} {traces[N+3]:>8.2f}  block {block_ks[0]}..{block_ks[-1]} {flag}"
        )

    print()
    print(f"All arithmetic blocks check OK: {all_block_ok}")
    print()
    print("Extracted: trace(C_N^(N+1)) for N in 2..15")
    print(f"{'N':>3} | {'trace(C_N^(N+1))':>20} | {'expected N+2':>14} | match")
    print("-" * 60)
    for N in range(2, 16):
        C = n_acci_companion(N)
        tr = np.trace(matrix_power(C, N + 1)).real
        match = abs(tr - (N + 2)) < 1e-9
        print(f"{N:>3} | {tr:>20.6f} | {N + 2:>14d} | {'YES' if match else 'NO'}")

    print()
    print("=> K_N := 1 / trace(C_N^(N+1)) = 1 / (N+2)")
    print("   At N=2 this is 1/4 = Eq 40.")


if __name__ == "__main__":
    main()
