"""Parallel validation of the Gamma_n dynamics findings from loop iter 7."""
import json, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROMPT = """I need a verification of a dynamical-systems argument I derived this morning. Please be rigorous and flag any errors.

SETUP:
For each integer n ≥ 1, define the map
    Γ_n : (1, ∞) → (1, ∞)
    Γ_n(u) = (1 - 1/u)^(-1/n)

The fixed-point equation Γ_n(u) = u reduces to u^n - u^(n-1) - 1 = 0, with unique positive root α_n > 1. (For n=2, α_2 = φ the golden ratio.) From a previous derivation:
    Γ_n'(α_n) = -α_n^(n-1) / n     (closed form, verified symbolically and numerically for n=1..10)

CLAIMS I want you to verify or critique:

CLAIM 1 (Reformulation of the rate):
From u^n - u^(n-1) - 1 = 0 we get u^(n-1)(u - 1) = 1, so α_n^(n-1) = 1/(α_n - 1). Substituting:
    Γ_n'(α_n) = -α_n^(n-1)/n = -1/[n(α_n - 1)]
So |Γ_n'(α_n)| = 1/[n(α_n - 1)].
    Q1a. Is this reformulation correct?

CLAIM 2 (Stability classification):
- For n = 1: α_1 = 2, |Γ_1'(α_1)| = 2^0/1 = 1. Marginally stable. Γ_1(u) = u/(u-1) is the Möbius involution.
- For n ≥ 2: |Γ_n'(α_n)| < 1 for all n. Stable contraction with attracting fixed point.
    Q2a. Is the n=1 case really exactly marginal (|rate| = 1)?
    Q2b. Is the n ≥ 2 case really always strictly stable?

CLAIM 3 (Asymptotic rate as n → ∞):
The fixed-point relation ε(1 + ε)^(n-1) = 1 (where ε = α_n - 1) can be solved asymptotically using the Lambert W function. Setting x = (n-1)·ε, the equation becomes x·exp(x·log(1+ε)/ε)... hmm let me redo.

Starting from ε(1 + ε)^(n-1) = 1 and letting (1 + ε)^(n-1) ≈ exp((n-1)·ε) for small ε, we get
    ε · exp((n-1)·ε) = 1
    (n-1)·ε · exp((n-1)·ε) = (n-1)
    (n-1)·ε = W(n-1)
    ε = W(n-1)/(n-1)

For large x, the principal branch of Lambert W satisfies W(x) ~ log(x) - log(log(x)) + ..., so ε ~ log(n)/n at leading order.

Therefore α_n - 1 ~ log(n)/n, and:
    rate(n) = 1/[n(α_n - 1)] ~ 1/[n · log(n)/n] = 1/log(n)
    Q3a. Is the Lambert W asymptotic correct?
    Q3b. Is the leading-order ε ~ log(n)/n right?
    Q3c. Is rate(n) ~ 1/log(n) the right asymptotic conclusion?
    Q3d. What is the next-order correction (the (log log n) term)?

CLAIM 4 (Phase transition at n=1):
The family has a sharp qualitative shift at n=1. For n=1, Γ_1 is the Möbius involution u → u/(u-1) with period-2 cycles and rate = 1 exactly. For n ≥ 2, every Γ_n is contracting on (1, ∞). The transition is sharp at the boundary.
    Q4. Is "phase transition" appropriate language, or is this just a marginal-stability classification with no phase-transition-like character?

CLAIM 5 (Global basin of attraction):
For n ≥ 2, the basin of attraction of α_n is the entire half-line (1, ∞). I tested this numerically with starting points u_0 in {1.01, 1.1, 1.3, 1.5, 1.618, 1.7, 2, 3, 5, 10, 100} and all converged to α_n. (Γ_n is monotonically decreasing on (1, ∞) since its derivative is everywhere negative; combined with |Γ_n'(α_n)| < 1, the Banach contraction picture should give global convergence.)
    Q5. Is the basin really all of (1, ∞), or is there a hidden subtlety (e.g. starting points where Γ_n exits the domain after some iterations)?

NOVELTY CHECK:
    Q6. Is this analysis (the family Γ_n, the closed form, the asymptotic rate ~1/log n, the phase transition) something you recall from any published paper? Or does it appear novel to your knowledge?

FORMAT:
Q1a: [yes/no/unsure + brief reason]
Q2a: ...
...
Q6: ...
SUMMARY: [one paragraph: are the claims correct, and is this likely novel?]

Be rigorous. Flag errors. Null findings are valuable. I am specifically NOT looking for enthusiasm — I am looking for catching mistakes."""


def call_openai(prompt):
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3500},
        timeout=180,
    )
    data = resp.json()
    if "choices" in data:
        return {"model": "gpt-4o", "response": data["choices"][0]["message"]["content"], "elapsed_seconds": round(time.time()-start, 2)}
    return {"error": str(data)}


def call_grok(prompt):
    import httpx
    api_key = os.environ.get("XAI_API_KEY", "")
    start = time.time()
    resp = httpx.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "grok-3-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3500},
        timeout=180,
    )
    data = resp.json()
    if "choices" in data:
        return {"model": "grok-3-mini", "response": data["choices"][0]["message"]["content"], "elapsed_seconds": round(time.time()-start, 2)}
    return {"error": str(data)}


def call_claude(prompt):
    import anthropic
    client = anthropic.Anthropic()
    start = time.time()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3500,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"model": "claude-sonnet-4", "response": response.content[0].text if response.content else "", "elapsed_seconds": round(time.time()-start, 2)}


if __name__ == "__main__":
    jobs = [(call_grok, "grok"), (call_openai, "openai"), (call_claude, "claude")]
    results = {}
    print("Launching 3 parallel dynamics-validation calls...")
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn, PROMPT): tag for fn, tag in jobs}
        for fut in as_completed(futures):
            tag = futures[fut]
            try:
                r = fut.result()
                results[tag] = r
                print(f"  {tag} done in {r.get('elapsed_seconds', '?')}s ({len(r.get('response', ''))} chars)")
            except Exception as e:
                results[tag] = {"error": str(e)}
                print(f"  {tag} ERROR: {e}")

    out = Path(__file__).parent / "k_identity_validation"
    out.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    f = out / f"dynamics_validation_{ts}.json"
    f.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {f}")
