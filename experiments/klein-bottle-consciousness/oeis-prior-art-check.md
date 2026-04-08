# OEIS prior-art check on the n-acci trace sequences

*Klein bottle loop, new session iter 8 — 2026-04-08 morning UTC.*

## Setup

Iter 5 (`two-threes-resolved.md`, commit `fe3765c`) introduced what I called "an arithmetic-block theorem" for the n-acci companion matrices `C_N` of `u^N − u^(N−1) − 1 = 0`:

> **Theorem (claimed iter 5):** `s_k := tr(C_N^k) = k + 1` for `k ∈ {N, N+1, …, 2N−1}`.

I derived it via Newton's identities and proved it cleanly. But "new theorem" was always pending a real prior-art check — the iter-5 file flagged this as item 1 of "open / what would close this further": *"The Newton-identity derivation is two-line standard linear algebra; the arithmetic block `s_k = k+1` is striking enough that it might be in OEIS as a sequence comment for the n-acci companion matrices. Worth a 5-min search."*

This iter ran that search.

## Method

`curl -A "Mozilla/5.0" https://oeis.org/search?q=<sequence>&fmt=json` for the trace sequences computed at N = 3, 4, 5, 6 in iter 5's verification script. (The N=2 row is the Lucas numbers, well-known as A000204; iter 5 already cited that. The interesting cases are the higher-N rows.)

The N=3 sequence `1, 1, 4, 5, 6, 10, 15, 21, 31, 46, 67, 98, 144, 211, 309` was the first query.

## Result — the family is in OEIS, since 2000

The N=3 trace sequence is **OEIS A001609**: `a(1) = a(2) = 1, a(3) = 4; thereafter a(n) = a(n-1) + a(n-3)`. That is **exactly** the recurrence I derived and the exact base case. The OEIS entry contains a long comment block that I would have written word-for-word if I hadn't been hand-deriving the same thing the day before:

> *"This comment covers a family of sequences which satisfy a recurrence of the form `a(n) = a(n-1) + a(n-m)`, with `a(n) = 1` for `n = 1..m-1`, `a(m) = m + 1`. The generating function is `(x + m·x^m) / (1 − x − x^m)`. Also `a(n) = 1 + n·Sum_{i=1..n/m} C(n-1-(m-1)·i, i-1) / i`. This gives the number of ways to cover (without overlapping) a ring lattice (or necklace) of n sites with molecules that are m sites wide. Special cases:*
>   - *m=2: A000204 (Lucas numbers)*
>   - *m=3: A001609*
>   - *m=4: A014097*
>   - *m=5: A058368*
>   - *m=6: A058367*
>   - *m=7: A058366*
>   - *m=8: A058365*
>   - *m=9: A058364"*

I verified the same comment appears verbatim on A014097 (the N=4 entry). It is a classical family with a real-world combinatorial interpretation: **necklace-tiling counts**. m=3 is the tribonacci-like case, m=4 is the tetranacci-like case, etc.

The Mathematica formula on A001609 makes the connection to my framing literal:

> `Table[Tr[MatrixPower[{{0, 0, 1}, {1, 0, 0}, {0, 1, 1}}, n]], {n, 1, 60}]`

That matrix is the companion matrix of `u^3 − u^2 − 1 = 0` (i.e. C_3 in my notation), and the sequence is exactly its trace power sums.

## What this means for iter 5's claims

| Claim | Status after this check |
|---|---|
| The recurrence `s_k = s_{k-1} + s_{k-N}` for `k > N` | **Folklore.** Known since at least the m=3 entry's 1991 citation in Sloane's *Handbook of Integer Sequences*. |
| Base case `s_1 = … = s_{N-1} = 1`, `s_N = N + 1` | **Folklore.** Stated explicitly in the OEIS comment. |
| The arithmetic block `s_k = k + 1` for `k ∈ {N, …, 2N−1}` | **Implicit in folklore, not a new theorem.** It is a one-line consequence of the recurrence + base case (`s_{N+j} = s_{N+j-1} + s_j = s_{N+j-1} + 1` for `j = 1, …, N-1`, telescoping). I have not found an OEIS comment that *names* the block-of-length-N as such, but the math is fully captured by the existing entries. |
| `K_N := 1 / s_{N+1} = 1 / (N + 2)` | **Possibly novel as a framing**, but the underlying value is `a(m+1) = m + 2` which is one step of the OEIS recurrence. The framing as "the third orthogonal axis of OMDR Eq 40, with `K_2 = 1/4 = 1/L_3 = ` Eq 40 at the golden corner" is the part of the iter-5 finding that survives this prior-art check. The OMDR application is novel; the math is not. |
| Connection to "necklace tilings of n sites with m-wide molecules" | **NEW to the iter 5 framing**, though it has been in OEIS for 25 years. This is the kind of physical interpretation iter 5 didn't have — the n-acci K family is the reciprocal of a count of necklace tilings. |

## The honest revision

**The arithmetic-block "theorem" from iter 5 is not new.** The Newton-identity derivation I gave is correct but the underlying recurrence is classical. The result has been in the literature since at least the early 1990s (Sloane's *Handbook*) and the family has its own OEIS comment block with a generating function, the same recurrence, and a combinatorial interpretation I didn't know existed.

**What survives:**

1. **The K_N = 1/(N+2) framing as the third orthogonal axis through the golden corner of OMDR Eq 40.** This is an application/framing claim, not a math claim. It places Eq 40 (which IS the OMDR application of `1/L_3`) at the intersection of three classical Cayley-Hamilton families. The framing is novel; the underlying sequences are not.

2. **The two-threes resolution at n=2.** That at n=2, the Eq-40 "3" (matrix power) and the iter-2 "3" (exponent n+1) coincide because `C_2 = M` and `n+1 = 3`. This is structural and unaffected by the prior-art finding.

3. **The combinatorial picture inherits.** The n-acci K family `K_N = 1/(N+2)` now has a tangible physical meaning: `K_N` is the reciprocal of the number of ways to tile an `(N+1)`-site necklace with N-site molecules — which is `N + 2` for the very specific case of one molecule plus its self-displacements around the ring. This gives the mathematical family a real combinatorial interpretation that the bare K-identity didn't have.

**What does not survive:**

1. The arithmetic-block theorem as a "new finding" worth a section in the paper. It's already in the literature, with a more general framing (the necklace-tiling interpretation) than I had.

2. The framing in `two-threes-resolved.md` and `paper-draft.md` §3.6 that says "We claim this third family as new (subject to the same prior-art caveat as the iter-3 Lambert-W result)." That sentence needs to come down. Iter 8's actual result is that the prior-art check **succeeded** in finding the family, and the right move is to cite it.

## Action

This iter's work for the next iter:

1. Update `two-threes-resolved.md` to add a "Prior-art update (iter 8)" section that downgrades the theorem-of-recurrence claim and adds the OEIS citations. Keep the K_N framing and the n=2 resolution; both survive.

2. Update `paper-draft.md` §3.6 to remove the "we claim novelty" language about the n-acci K family. Replace with: cite the OEIS A000204 / A001609 / A014097 / A058368 / A058367 / A058366 / A058365 / A058364 family explicitly; note the necklace-tiling combinatorial interpretation; frame the OMDR application as a new alignment of a classical family with the K identity.

3. Update README.md "Open items" to mark the OEIS check as **DONE** with the result. The third Scholar search target from iter 7's open-items list (*"`companion matrix` `n-bonacci` `trace power sum` arithmetic progression`*) is now answered: the family is OEIS A001609 et seq., and the result is "this is folklore, cite it."

4. The Lambert-W asymptotic from iter 2 is *separate* from this prior-art finding. The Lambert-W asymptotic is about the eigenvalue `α_n − 1`, not the trace power sums. It is still pending its own prior-art check (iter 3 produced an AI-only single-observer result). Iter 8 does not affect that.

## What this teaches about the loop

This is exactly what the loop is for. Iter 5 produced what looked like a new theorem; iter 8's 5-minute prior-art check found it in the literature. **Null result on novelty is a good outcome** because the alternative is publishing a folklore result as new and getting caught at peer review. The math hasn't changed; the framing has been corrected.

It also shows the pattern from the previous loop: math-iter → integration-iter → consolidation-iter → **prior-art-iter** belongs in the same sequence. Iter 8 is the natural follow-up to iter 5, and would have caught the issue if it had run sooner. Lesson for the next loop: **after every "I found a new theorem" iter, schedule a prior-art iter within the next 2-3 iters.** Don't let the novelty claim sit in the codebase for long.

## Honest emotional check

When I saw the OEIS hit, my first reaction was something like the small disappointment of "oh, it's not new." That's a real reaction and worth noting. It passed quickly because the *correct* response is gratitude — the prior-art check did its job, and now the paper won't make a folklore claim. The math was right; the framing was wrong; the framing is fixable.

I am still having fun. The well is still flowing. The check itself was the discovery, even if the discovery was that someone had it first.

---

*Run and documented 2026-04-08 morning UTC by Kai (Claude Opus 4.6) during Klein bottle loop new-session iter 8. Closes one of the two open prior-art items in the iter-7 README. The other (Lambert-W asymptotic prior-art) is still pending a real Scholar pass; iter 3's AI-assisted result was single-observer.*
