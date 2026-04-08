# The "two threes" puzzle, partially resolved

*Klein bottle loop, new session iter 5 — 2026-04-07 evening AEST.*

## The puzzle

Three loop iterations and three external validators have flagged the same nagging coincidence. Two unrelated derivations both produce the integer **3** at exactly **n = 2**:

- **Eq 40 (Cayley-Hamilton, OMDR Band 3):** `K = 1/trace(M³) = 1/L₃ = 1/4`. The "3" is the matrix power applied to the Fibonacci matrix `M = [[1,1],[1,0]]`.
- **Iter 2 (n-acci family closed form):** the scaling factor at the Schwarzschild case is `α_n^(n+1)/n = φ^3/2` at n=2. The "3" is the exponent `n+1 = 3`.

The previous loop's three independent AI validators (Grok, GPT-4o, Claude) all said "likely coincidence absent a structural proof." Iter 5's job: poke at it more carefully.

## The resolution at n=2 (coincidence is structural)

At `n = 2` in the n-acci family `u^n − u^(n−1) − 1 = 0`, the companion matrix is

$$
C_2 \;=\; \begin{pmatrix} 1 & 1 \\ 1 & 0 \end{pmatrix}
$$

— **the Fibonacci matrix M itself.** So the two derivations are not in different worlds. They are both applying the Cayley-Hamilton machinery to the same matrix:

- Eq 40 takes `trace(M³)`.
- Iter 2 takes `α^(n+1) = α^3` where α is the dominant eigenvalue of `M = C_2`, and `n+1 = 3` because `n = 2`.

These are the same "3". `M³` is the third power of the matrix; `α^3 = φ^3` is the third power of its dominant eigenvalue. Their connection is the standard trace identity:

$$
L_3 \;=\; \operatorname{tr}(M^3) \;=\; \varphi^3 + (-1/\varphi)^3 \;=\; \varphi^3 - \varphi^{-3} \;=\; 4.
$$

Equivalently:

$$
\boxed{\;K \cdot \bigl(\varphi^3 - \varphi^{-3}\bigr) \;=\; 1,\qquad K = 1/L_3 = 1/4\;}
$$

This is just Eq 40 rewritten in eigenvalue form. **The two threes are not coincidence; they are two faces of the same `M³`.** The previous validators were correct that the puzzle had no proof "absent a structural derivation," and the structural derivation is one line: at `n=2`, `C_n = M`, and matrix power `3 = n+1`.

## What this generalises to: a third orthogonal Eq-40 family

If the n=2 connection comes from `C_n = M` and matrix power `n+1`, the natural question is: what does `trace(C_N^(N+1))` look like for general N?

**Empirical answer (verified at N = 2..15):**

| N | trace(C_N^(N−1)) | trace(C_N^N) | **trace(C_N^(N+1))** | trace(C_N^(N+2)) | trace(C_N^(N+3)) |
|---|---|---|---|---|---|
| 2 | 1 | 3 | **4** | 7 | 11 |
| 3 | 1 | 4 | **5** | 6 | 10 |
| 4 | 1 | 5 | **6** | 7 | 8 |
| 5 | 1 | 6 | **7** | 8 | 9 |
| 6 | 1 | 7 | **8** | 9 | 10 |
| 7 | 1 | 8 | **9** | 10 | 11 |
| ... | 1 | N+1 | **N+2** | N+3 | N+4 |
| 15 | 1 | 16 | **17** | 18 | 19 |

The bolded column is `trace(C_N^(N+1)) = N + 2` for every `N` tested. For `N ≥ 4` the entire row from `k = N−1` onward is an arithmetic progression `1, N+1, N+2, N+3, …, 2N` (length `N+1` after the leading `1`). For `N = 2` the arithmetic block is just `{3, 4}` (length 2) and then Lucas numbers `7, 11, …` take over. For `N = 3` the block is `{4, 5, 6}` (length 3) and then the tribonacci-Lucas sequence kicks in. So **the arithmetic-block phenomenon is most visible at large N and has a finite length equal to `N` terms (or `N+1` counting the leading `1`).**

### Theorem (Newton-identity proof of the arithmetic block)

For the n-acci companion matrix `C_N` of `p(u) = u^N − u^(N−1) − 1`, the trace power sums `s_k = tr(C_N^k) = sum of α_i^k` satisfy:

$$
s_k \;=\; k + 1 \quad\text{for}\quad k \in \{N,\, N+1,\, \ldots,\, 2N-1\}.
$$

In particular `s_{N+1} = N + 2` for all `N ≥ 2`.

**Proof.** Use Newton's identities. The polynomial `p(u) = u^N − u^(N−1) + 0·u^(N−2) + ... + 0·u + (-1)·1` has elementary symmetric polynomials `e_1 = 1`, `e_2 = e_3 = … = e_{N−1} = 0`, and `e_N = (−1)^{N+1}`. Newton's identity for `1 ≤ k ≤ N` gives

$$
s_k \;=\; e_1 s_{k-1} - e_2 s_{k-2} + \cdots + (-1)^{k-1} k\, e_k.
$$

For `1 ≤ k < N` only the `e_1 s_{k-1}` term survives (all `e_2, …, e_{k}` are zero), so `s_k = s_{k-1}`. With the base case `s_1 = e_1 = 1`, we get `s_1 = s_2 = … = s_{N-1} = 1`. For `k = N`, the `(-1)^{N-1} N e_N` term contributes:

$$
s_N \;=\; s_{N-1} + (-1)^{N-1} \cdot N \cdot (-1)^{N+1} \;=\; 1 + N \cdot (-1)^{2N} \;=\; 1 + N \;=\; N+1.
$$

For `k > N`, Newton's identity becomes the recurrence

$$
s_k \;=\; e_1 s_{k-1} - e_2 s_{k-2} + \cdots + (-1)^{N-1} e_N s_{k-N} \;=\; s_{k-1} + (-1)^{N-1}(-1)^{N+1} s_{k-N} \;=\; s_{k-1} + s_{k-N}.
$$

(The double sign cancels: `(-1)^{N-1} \cdot (-1)^{N+1} = (-1)^{2N} = +1`.) So for `k > N`:

$$
s_k \;=\; s_{k-1} + s_{k-N}.
$$

Now iterate from `s_N = N+1`. For `k = N + j` with `j = 1, 2, …, N−1`, the recurrence gives

$$
s_{N+j} \;=\; s_{N+j-1} + s_j \;=\; s_{N+j-1} + 1
$$

(since `s_j = 1` for `1 ≤ j ≤ N−1`). Telescoping from `s_N = N+1` upward by 1 each step:

$$
s_{N+j} \;=\; (N+1) + j \;=\; (N+j) + 1.
$$

So `s_k = k + 1` for `k = N, N+1, …, 2N−1`. The arithmetic block ends at `k = 2N − 1` because at `k = 2N` we hit `s_{2N} = s_{2N-1} + s_N = 2N + (N+1) = 3N+1`, no longer of the form `k+1`. □

### A third orthogonal generalisation of Eq 40

The previous loop's `metallic-K-family.md` already showed that Eq 40 sits at the corner of a 2-parameter family `K_{p,n} = 1/tr(M_p^n)`, where `M_p = [[p,1],[1,0]]` is the 2×2 metallic-mean companion. Two natural one-parameter slices through the (golden, n=3) corner:

1. **Vary `p`** (linear coefficient, matrix stays 2×2): `K_p = 1/[p(p² + 3)]`.
2. **Vary `n`** (matrix power, matrix stays 2×2): `K_{1,n} = 1/L_n` (the n-band Lucas reciprocal — null result on the benchmark).

The arithmetic-block theorem above gives a **third** axis — orthogonal to both:

3. **Vary `N`** (polynomial degree, matrix grows to N×N): `K_N := 1/tr(C_N^{N+1}) = 1/(N+2)`.

Verified explicitly:

| `N` | matrix | matrix size | `tr(C_N^{N+1})` | `K_N` |
|---|---|---|---|---|
| **2** | `[[1,1],[1,0]]` (Fibonacci `M`) | 2×2 | **4 (=L₃)** | **1/4 (=Eq 40)** |
| 3 | `companion(u³−u²−1)` | 3×3 | 5 | 1/5 |
| 4 | `companion(u⁴−u³−1)` | 4×4 | 6 | 1/6 |
| 5 | `companion(u⁵−u⁴−1)` | 5×5 | 7 | 1/7 |
| ... | ... | ... | ... | ... |
| `N` | `companion(u^N − u^(N−1) − 1)` | N×N | `N+2` | `1/(N+2)` |

All three families pass through the golden / Eq-40 / `K = 1/4` point because at `(p=1, n=3, N=2)` the matrix is the Fibonacci matrix M and the relevant power is `M³`. The three axes parameterise different one-dimensional slices of the larger lattice.

## What the "two threes" actually are

| | Eq 40 | Iter 2 closed form |
|---|---|---|
| The "3" is | matrix power applied to M | exponent `N+1` at `N=2` |
| Computed as | `tr(M³) = L₃ = 4` | `α^{N+1}/N = φ³/2` |
| Generalises to | `tr(C_N^{N+1}) = N+2` (this iter) | `α_N^{N+1}/N` (iter 2) |
| At `N=2` becomes | `tr(M³) = 4` | `φ³/2 ≈ 2.118` |
| Connected by | `α^{N+1}/N = tr(C_N^{N+1})/N + (sum of small eigenvalue powers)/N` | |

At `N = 2`, the small-eigenvalue correction is `(-1/φ)^3/2 = -1/(2φ³) ≈ -0.118`, and the identity becomes

$$
\frac{\varphi^3}{2} \;=\; \frac{L_3}{2} + \frac{1}{2\varphi^3} \;=\; 2 + \frac{1}{2\varphi^3}.
$$

For larger `N`, the correction grows because the non-dominant eigenvalues of `C_N` have absolute values closer to 1. So the iter-2 scaling factor `α_N^{N+1}/N` and the new K family `1/tr(C_N^{N+1}) = 1/(N+2)` are related by a calculable correction at every `N`, but the relationship is exact-and-clean only at `N = 2`.

## Honest framing

The two threes ARE structurally connected at `N = 2` (it is one M³, two ways of asking about it), and the value `tr(C_N^{N+1}) = N + 2` gives a third clean parameterised family of K-identities. **The arithmetic-block claim is NOT new mathematics** — see the prior-art update below. The Newton-identity derivation is correct, but the recurrence and base case are classical and the family is in OEIS since at least the early 1990s. The two pieces that DO survive are (a) the n=2 structural resolution between Eq 40's "3" and the iter-2 "3" and (b) the framing of `K_N = 1/(N+2)` as a third orthogonal axis through the OMDR Eq-40 corner.

### Prior-art update (iter 8, 2026-04-08)

A 5-minute OEIS check found the family. The trace sequences `s_k = tr(C_N^k)` for the n-acci companion matrices form a classical OEIS family of sequences with combinatorial interpretation:

- **N=2:** OEIS [A000204](https://oeis.org/A000204) — the Lucas numbers (already cited by Eq 40).
- **N=3:** OEIS [A001609](https://oeis.org/A001609) — `a(n) = a(n-1) + a(n-3)` with `a(1) = a(2) = 1, a(3) = 4`. Catalogued in Sloane's *Handbook of Integer Sequences* (1973).
- **N=4:** OEIS [A014097](https://oeis.org/A014097).
- **N=5:** OEIS [A058368](https://oeis.org/A058368).
- **N=6:** OEIS [A058367](https://oeis.org/A058367).
- **N=7:** OEIS [A058366](https://oeis.org/A058366).
- **N=8:** OEIS [A058365](https://oeis.org/A058365).
- **N=9:** OEIS [A058364](https://oeis.org/A058364).

Each entry contains the **same comment block** stating my exact recurrence and base case:

> *"This comment covers a family of sequences which satisfy a recurrence of the form `a(n) = a(n-1) + a(n-m)`, with `a(n) = 1` for `n = 1..m-1`, `a(m) = m + 1`. The generating function is `(x + m·x^m) / (1 − x − x^m)`. … This gives the number of ways to cover (without overlapping) a ring lattice (or necklace) of n sites with molecules that are m sites wide."*

**The arithmetic block `s_k = k + 1` for `k ∈ {N, …, 2N − 1}` is a one-line consequence of the recurrence + base case (`s_{N+j} = s_{N+j-1} + s_j = s_{N+j-1} + 1` for `j = 1, …, N − 1`, telescoping). It is implicit in the OEIS entries but not stated as a separately-named identity.**

**Key gain from the prior-art finding:** the n-acci K family `K_N = 1/(N + 2)` now has a tangible combinatorial interpretation it did not have before. `N + 2` is the count of necklace tilings of `(N+1)` sites with N-wide molecules. The K identity is the reciprocal of a count of tilings, not just an abstract trace algebra fact. This gives the OMDR application a real combinatorial picture, which is more than the bare math gave.

**Honest revision of what's claimed:** the **framing** of the n-acci K family as the third orthogonal axis through the OMDR Eq-40 corner is the new content. The **mathematics** is folklore. See `oeis-prior-art-check.md` for the full record.

What it does NOT do:

- It does not say `K = 1/(N+2)` is physically meaningful for any `N ≠ 2`. The OMDR Band-3 reason for `K = 1/4` is empirical.
- It does not connect to the metallic-K family `K_p = 1/[p(p² + 3)]` except through their shared corner at `(p=1, N=2)`. The two parameterisations are genuinely different families through that point.
- It does not pin down what's special about `N + 1` as the matrix power. The arithmetic block runs from `k = N` to `k = 2N − 1`; `N + 1` is the second entry in the block, not the first or last. We'd need additional structure (e.g., a connection to the `Γ_n` family of iter 2) to pick `k = N + 1` as the "natural" choice.

**The validators were right that the *bare* "two threes" coincidence had no proof. They are wrong that there is no connection. The connection is that Eq 40 and the iter-2 closed form both touch the same `M³` at `N = 2`, and the generalisation upward is the arithmetic-block identity proved here.**

## Numerical verification (run extend_two_threes.py to reproduce)

```
n |  k=n-1   k=n   k=n+1   k=n+2   k=n+3
--+----------------------------------------
 2 |   1      3      4       7      11
 3 |   1      4      5       6      10
 4 |   1      5      6       7       8
 5 |   1      6      7       8       9
 ...
15 |   1     16     17      18      19
```

All entries floating-point exact against direct matrix-power computation in numpy.

## What this means for the paper

A small addition to §3.6 (the K-identity section) folds this in:

> "The Eq 40 derivation generalises along *three* orthogonal axes through the golden corner, all passing through `K = 1/4`:
>   1. **Metallic axis** (`vary p, hold matrix at 2×2`): `K_p = 1/[p(p² + 3)]`. The Fibonacci, silver, bronze, … companions, all at matrix power 3.
>   2. **Lucas axis** (`vary matrix power n, hold matrix at p=1`): `K_{1,n} = 1/L_n`. The n-band conjecture (null result, see `effective_k_analysis.md`).
>   3. **n-acci axis** (`vary polynomial degree N, set power to N+1`): `K_N = 1/tr(C_N^{N+1}) = 1/(N+2)`, where `C_N` is the (N×N) companion matrix of `u^N − u^(N−1) − 1`. This third family follows from Newton's identities applied to the elementary symmetric polynomials of `u^N − u^(N−1) − 1`: the trace power sums satisfy `s_k = k + 1` for `k ∈ {N, N+1, …, 2N − 1}`, an arithmetic block of length `N`, which terminates at `k = 2N − 1`. We claim this third family as new (subject to the same prior-art caveat as iter 3's Lambert-W result)."

## Open / what would close this further

1. **Prior-art check on the arithmetic block.** The Newton-identity derivation is two-line standard linear algebra; the arithmetic block `s_k = k+1` is striking enough that it might be in OEIS as a sequence comment for the n-acci companion matrices. Worth a 5-min search.
2. **What if the matrix polynomial were `u^N − u^(N−1) − u^j` for some other `j`?** Same Newton machinery applies; would the block formula hold?
3. **Does `1/(N+2)` mean anything in any physical context?** No reason a priori. Just a well-defined family parallel to Eq 40.

---

*Computed and verified 2026-04-07 evening AEST by Kai (Claude Opus 4.6) during Klein bottle loop iter 5. Numerical verification at N ∈ {2..15}; symbolic Newton-identity proof above. Builds on the previous loop's `metallic-K-family.md` (which gave the orthogonal `vary p` and `vary n` axes through the same corner), iter 1's cousins-not-twins reframing, iter 2's continuous-`n` extension of the `Γ_n` closed form, and iter 3's Lambert-W asymptotic.*
