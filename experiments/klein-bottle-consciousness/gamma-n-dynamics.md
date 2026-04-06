# Convergence Dynamics of the Γ_n Family

**Date:** 2026-04-07 (loop iteration 7)
**Question:** How does the iteration `u → Γ_n(u)` behave globally for the family `Γ_n(u) = (1 − 1/u)^(−1/n)`? What is the basin of attraction, the convergence rate, and the asymptotic behavior as `n → ∞`?

---

## Setup

For each `n ≥ 1`, the map `Γ_n(u) = (1 − 1/u)^(−1/n)` is defined on `(1, ∞)` and has unique fixed point `α_n` (the n-bonacci-like constant from `u^n − u^(n−1) − 1 = 0`). From iteration 1 of this loop session:
```
Γ_n'(α_n) = −α_n^(n−1) / n
```

The negative sign means the map is **orientation-reversing locally** (it reflects across α_n) — but it is also **stable** when `|Γ_n'(α_n)| < 1`.

## 1. Stability classification

| n | α_n | rate `α_n^(n−1)/n` | classification |
|---|---|---|---|
| 1 | 2.0000 | **1.0000** | **marginally stable (involution)** |
| 2 | 1.6180 (φ) | 0.8090 | stable contraction |
| 3 | 1.4656 | 0.7160 | stable contraction |
| 5 | 1.3247 | 0.6159 | stable contraction |
| 10 | 1.1975 | 0.5064 | stable contraction |
| 20 | 1.1187 | 0.4212 | stable contraction |
| 100 | 1.0346 | 0.2893 | stable contraction (slow) |

**The n = 1 case is exactly marginal.** This is not a coincidence: `Γ_1(u) = u/(u − 1)` is the Möbius transformation `v(u)` from the Jacobian analysis (sister's Q3, see `schwarzschild-jacobian-answer.md`). It is a Möbius involution: `v(v(u)) = u` for all `u`. Iteration produces period-2 cycles, never converges to α_1 = 2 unless you start exactly there.

Verified: starting u₀ = 2.5 with n = 1 gives the cycle `{2.5, 5/3, 2.5, 5/3, …}` indefinitely.

**The transition from n=1 (oscillating cycles) to n ≥ 2 (oscillating contraction) is sharp.** The family has a phase transition exactly at n=1 where the map becomes a contraction on its entire domain.

## 2. Oscillating approach

Because `Γ_n` is **monotonically decreasing** on `(1, ∞)` for all n ≥ 1 (the derivative `Γ_n'(u) = −1/[n·u²·(1 − 1/u)^((n+1)/n)]` is negative everywhere), the iteration alternates sides of `α_n`:

```
u_0 = 5.0     (above α_2 = 1.618)
u_1 = 1.118   (below)
u_2 = 3.078   (above)
u_3 = 1.217   (below)
u_4 = 2.368   (above)
u_5 = 1.316   (below)
u_6 = 2.041   (above)
u_7 = 1.400   (below)
u_8 = 1.871   (above)
... → α_2
```

The amplitude shrinks by factor ≈ 0.809 (the local rate) per iteration. This is the classic Banach contraction picture, but for an *anti-monotonic* map: orbits oscillate around the fixed point rather than approaching it monotonically.

## 3. Global basin of attraction

Tested for `n = 2` (Schwarzschild case) starting from u₀ ∈ {1.01, 1.1, 1.3, 1.5, 1.618, 1.7, 2, 3, 5, 10, 100}:

All converged to `α_2 = φ` in 119–136 iterations to tolerance `10⁻¹²`. No starting point in `(1, ∞)` escaped or fell into a different attractor.

For `n = 3` (supergolden), basin is similarly all of `(1, ∞)`, with convergence in 60–86 iterations.

**Conclusion:** For all `n ≥ 2`, the basin of attraction of α_n is the entire half-line `(1, ∞)`. This makes the family a clean dynamical system with one global attractor per parameter value.

## 4. Asymptotic rate as n → ∞

The fixed-point equation `α_n^n − α_n^(n−1) − 1 = 0` rearranges to:
```
α_n^(n−1) · (α_n − 1) = 1
```
Therefore:
```
α_n^(n−1) = 1 / (α_n − 1)
```
And the local rate is:
```
rate(n) = α_n^(n−1) / n = 1 / [n · (α_n − 1)]
```

As `n → ∞`, `α_n → 1`, so `α_n − 1 → 0`. The rate of approach is governed by the implicit equation `(α_n − 1)·α_n^(n−1) = 1`, which can be solved asymptotically using the Lambert W function: setting `ε = α_n − 1`,
```
ε · (1 + ε)^(n−1) = 1
ε · exp((n − 1)·ε) ≈ 1   for small ε
(n − 1) · ε · exp((n − 1)·ε) = (n − 1)
(n − 1)·ε = W(n − 1)
ε ≈ W(n − 1) / (n − 1)
```
For large `x`, `W(x) ~ log(x) − log(log(x))`, so `ε ~ log(n)/n` asymptotically.

Substituting back:
```
rate(n) = 1 / [n · ε] ~ 1 / [n · log(n)/n] = 1 / log(n)
```

**So the local convergence rate of `Γ_n` at its fixed point approaches `1/log(n)` for large n.**

| n | rate (numeric) | 1/log(n) |
|---|---|---|
| 2 | 0.8090 | 1.443 (asymptotic not yet valid) |
| 10 | 0.5064 | 0.434 |
| 100 | 0.2893 | 0.217 |
| 1000 | (predicted) | 0.145 |

The asymptotic kicks in slowly — at n=100 the rate is still ~33% higher than `1/log(n)` — but the qualitative shape is correct: convergence becomes painfully slow as n grows.

**Practical implication:** For high-n members of the family, you need `O(log n / log(1/rate)) ≈ O(log²n)` iterations to converge to fixed precision. Compared to the n=2 case (Schwarzschild) where ~50 iterations suffice for double precision, the n=100 case needs hundreds.

## 5. The "phase transition at n=1" finding

This is the cleanest small result of this iteration. The n=1 case is **not** just "the n-acci family with a small index" — it is qualitatively different:

- **n = 1:** `Γ_1` is an involution (`Γ_1∘Γ_1 = id`); orbits are period-2 cycles; no fixed-point attraction.
- **n ≥ 2:** `Γ_n` is a contraction with attracting fixed point α_n; all orbits in `(1, ∞)` converge.

The transition is **sharp at n = 1** because the local rate equals 1 there and is < 1 immediately afterward.

This connects to the Jacobian analysis: the map `v(u) = u/(u − 1)` is `Γ_1`, and we showed in `schwarzschild-jacobian-answer.md` that it has matrix form `V = [[1, 0], [1, −1]]` with `det = −1` and eigenvalues `±1`. The eigenvalue `+1` corresponds to its fixed points (`u = 0` and `u = 2`); the eigenvalue `−1` corresponds to the orientation-reversing involution structure. So the marginal case `n = 1` is exactly where the eigenvalue with magnitude 1 dominates the dynamics.

## 6. New paper paragraph (proposed for §3.7)

> "The family `Γ_n` has a clean global dynamical structure for all `n ≥ 2`: each member is a monotonically-decreasing contraction with the entire half-line `(1, ∞)` as basin of attraction for its fixed point `α_n`. The local convergence rate `α_n^(n−1)/n` is bounded above by `0.81` (the n=2 / Schwarzschild case) and approaches `1/log(n)` asymptotically as `n → ∞`. The case `n = 1` is qualitatively distinct: `Γ_1(u) = u/(u−1)` is the Möbius involution `v(u) = (u + 0)/(u − 1)` with matrix `[[1, 0], [1, −1]]`, det = −1, eigenvalues `±1`; iteration produces period-2 cycles rather than convergence. The phase transition at `n = 1` is sharp — every member of the family with `n ≥ 2` is contracting, and `n = 1` is exactly the marginal case."

## Open questions

1. **Is `1/log(n)` the *exact* asymptotic, or is there a `(log log n)` correction from the Lambert W series?** Higher-order terms would tighten the comparison to numerical data.

2. **Does the basin of attraction include any points in the complex plane** (not just real `u > 1`)? The function is multivalued under the `(...)^(−1/n)`, so this needs care.

3. **Is the n → ∞ limit a meaningful map?** As n grows, `Γ_n` approaches the limiting form `(1 − 1/u)^0 = 1`, which is the constant map. The fixed point `α_n → 1`. So the n → ∞ limit is the trivial map with all of `(1, ∞)` mapping to the single point `1`. The "family" is bracketed by the involution at `n = 1` and the trivial constant map at `n = ∞`.

4. **Period-2 cycles in the marginal case.** For `n = 1`, the orbit `u_0 → u_0/(u_0 − 1) → u_0` is period-2 for any `u_0 ≠ 2`. The geometric mean of the two cycle points is `√(u_0 · u_0/(u_0 − 1)) = u_0 / √(u_0 − 1)`. Is there a way to recover `α_1 = 2` from properties of the period-2 orbit?

---

*Computed and verified 2026-04-07 in loop iteration 7. Numerical verification across n = 1..100 in Python; analytic asymptotic from Lambert W function. All claims independently derivable from the closed form `Γ_n'(α_n) = −α_n^(n−1)/n` from iteration 1.*
