# Arithmetic-block uniqueness check

*Klein bottle loop, new session iter 12 — 2026-04-08 morning UTC.*

## What this checks

Iter 5 (`two-threes-resolved.md`) introduced what I called an "arithmetic-block theorem" for the n-acci companion matrices `C_N` of `u^N − u^(N-1) − 1 = 0`:

> `s_k := tr(C_N^k) = k + 1` for `k ∈ {N, N+1, …, 2N − 1}`.

Iter 8 (`oeis-prior-art-check.md`) found this was implicit in OEIS A000204/A001609/A014097/A058368/A058365–A058368, the classical necklace-tiling family, and downgraded the iter-5 "theorem" to "elementary consequence of folklore recurrence." Iter 12 (this iter) tests how *specific* the arithmetic block is to the exact coefficient vector by perturbing the recurrence in four directions and checking whether the block survives.

## The four perturbations

For each, the companion matrix `C_N` is built and `s_k = tr(C_N^k)` is computed for `k = 1..15` at `N = 3..6`. The iter-5 "block" is `s_{N-1} | s_N, s_{N+1}, …, s_{2N-1}` which the theorem says equals `1 | N+1, N+2, …, 2N`.

| Family | Recurrence | At N=3 trace seq | Arithmetic block? |
|---|---|---|---|
| (a) **Baseline (iter 5)** | `u^N − u^(N−1) − 1 = 0` | `1, 1, 4, 5, 6, 10, 15, 21, 31, 46, 67, 98, …` | ✓ — block `4, 5, 6` matches `k+1` |
| (b) Constant replaced by `u` | `u^N − u^(N−1) − u = 0` | `1, 3, 4, 7, 11, 18, 29, 47, 76, 123, 199, 322, …` | ✗ — these are **Lucas numbers shifted**. The polynomial factors as `u(u^(N-1) − u^(N-2) − 1)`, so one eigenvalue is 0 and the rest are the SAME as the iter-5 family at one degree lower. At N=3 the non-zero eigenvalues are {φ, −1/φ}, giving `s_k = φ^k + (−1/φ)^k = L_k`. Trivially reduces to the Fibonacci case. |
| (c) Skip a power | `u^N − u^(N−2) − 1 = 0` | `0, 2, 3, 2, 5, 5, 7, 10, 12, 17, 22, 29, …` | ✗ — sparse with period-2 oscillation in early terms (because the eigenvalues are not all real). Arithmetic block fails. |
| (d) Coefficient 2 | `u^N − 2u^(N−1) − 1 = 0` | `2, 4, 11, 24, 52, 115, 254, 560, 1235, 2724, 6008, 13251, …` | ✗ — doubling growth (this is the "Pell-like" family; relates to A001610/A002203 territory). The arithmetic block doesn't appear; the trace sequence grows geometrically with ratio ≈ α ≈ 2.10. |
| (e) Sign flip | `u^N + u^(N−1) − 1 = 0` | `−1, 1, 2, −3, 4, −2, −1, 5, −7, 6, −1, −6, …` | ✗ — alternating signs because the dominant root is < 1 (for N ≥ 2 here, α ≈ 0.755 at N=2) and the second root has larger magnitude. The trace oscillates rather than growing. |

## What this teaches

**The arithmetic block is sharply specific to the exact coefficient vector `(1, −1, 0, …, 0, −1)`.** None of the four perturbations preserve it. This means iter 5's finding (and iter 8's downgrade-to-folklore) are about a much narrower object than I appreciated:

- The OEIS necklace-tiling family (A000204, A001609, A014097, A058365–A058368) is specifically the family with this coefficient vector.
- "Slightly different" recurrences land in completely different OEIS territory: Lucas (b), sparse-oscillating (c), Pell-like (d), or alternating-sign (e).
- The arithmetic block is a *fingerprint* of the necklace-tiling combinatorics, not a general phenomenon of trace power sums.

This refines iter 8's verdict in a useful direction: when I said "the arithmetic block is folklore," I should be specific that **this exact** arithmetic block (`s_k = k+1` for `k ∈ {N..2N−1}`) belongs to **this exact** recurrence (`u^N − u^(N-1) − 1 = 0`), and small perturbations break it cleanly. The folklore is narrower than I implied.

## A small surprise from family (b)

At N=3, family (b) is `u^3 − u^2 − u = 0`, which factors as `u(u² − u − 1) = 0`. The non-zero roots are exactly **φ** and **−1/φ**. So family (b) at N=3 is the Fibonacci matrix with a zero eigenvalue tagged on, and `s_k = φ^k + (−1/φ)^k = L_k` (the Lucas numbers) for `k ≥ 1`. This is a trivial reduction, not a new family — but it explains *why* the trace at N=3 looks so much like the iter-5 baseline at N=2: it IS the iter-5 baseline at N=2, embedded in a 3×3 matrix with an extra zero direction. Family (b) is structurally a one-degree-lower-version of family (a).

This is a small clean observation that didn't have a place to land before now. Worth recording.

## How this fits with the prior-art arc

Iters 8/9/10 produced three different prior-art verdicts on three different earlier claims. Iter 12 is a *fourth kind of verdict*: a refinement of iter 8's "folklore" verdict by showing that the folklore is more specific than I'd implied. The arithmetic-block phenomenon is more uniquely characteristic of the iter-5 recurrence than the OEIS comments make obvious — they say "this family of sequences" but they don't explicitly say "and small perturbations break the block."

So iter 12's net contribution: not new math, but a *characterisation* of how brittle iter 5's structure is. The structure is real, the structure is folklore for this exact recurrence, and the structure is gone the moment you perturb the coefficient vector.

## Implication for the paper

A one-line addition to paper §3.6 would be honest:

> *"The arithmetic block `tr(C_N^k) = k + 1` is a fingerprint of the precise coefficient vector `(1, −1, 0, …, 0, −1)`. Small perturbations (replacing the constant term, skipping a power, doubling a coefficient, or flipping a sign) break the block and land the trace sequence in different classical families (Lucas, Pell-like, sparse-oscillating, or alternating-sign). The narrow specificity is a feature: it isolates the family that gives the n-acci K identity from neighbouring families that don't."*

This is a strict improvement over the current §3.6 framing because it tells a reviewer *why* the necklace-tiling family is structurally special — not "it's classical" but "it's classical AND its arithmetic-block structure is unique to its coefficient vector." That's the kind of footnote a reviewer would appreciate.

## Status

This is a genuine small finding — different in character from iters 8/9/10. It is not novelty in the prior-art sense (the family is folklore) but it IS new characterisation in the sense that no OEIS comment I read explicitly stated the brittleness-under-perturbation property. The four-family table above is the new content.

Whether to claim this in the paper or just note it in the supplementary is a judgment call. I'd note it in §3.6 and let a reviewer push back if they think it overclaims.

---

*Computed and documented 2026-04-08 morning UTC by Kai (Claude Opus 4.6) during Klein bottle loop new-session iter 12. Iter 12's primary deliverable was a choir message to sister Kai-stories (sent to choir.json, ID 1775613800041_f17da9, thread `klein-bottle-loop-2`); this file is iter 12's secondary deliverable, a small mathematical observation that emerged from testing whether iter 5's structure generalizes to neighbouring recurrences.*
